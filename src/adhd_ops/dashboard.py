from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from plotly.offline import get_plotlyjs


STAGE_ORDER = [
    "referral_received",
    "referral_accepted",
    "first_contact",
    "assessment_booked",
    "assessment_attended",
    "assessment_completed",
    "treatment_started",
]

STAGE_LABELS = {
    "referral_received": "Referral received",
    "referral_accepted": "Referral accepted",
    "first_contact": "First contact",
    "assessment_booked": "Assessment booked",
    "assessment_attended": "Assessment attended",
    "assessment_completed": "Assessment completed",
    "treatment_started": "Treatment started",
}


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    clean = frame.copy()
    for column in clean.columns:
        if pd.api.types.is_datetime64_any_dtype(clean[column]):
            clean[column] = clean[column].dt.strftime("%Y-%m-%dT%H:%M:%S")
        elif isinstance(clean[column].dtype, pd.PeriodDtype):
            clean[column] = clean[column].astype(str)
    clean = clean.replace({np.nan: None, pd.NaT: None})
    return clean.to_dict(orient="records")


def _prepare_cases(pathway: pd.DataFrame) -> pd.DataFrame:
    cases = pathway.copy()
    date_columns = [
        "referral_received_at",
        "accepted_at",
        "first_contact_at",
        "scheduled_start",
        "assessment_completed_at",
        "treatment_started_at",
    ]
    for column in date_columns:
        cases[column] = pd.to_datetime(cases[column], errors="coerce")

    observed_end = max(
        value
        for value in [
            cases["referral_received_at"].max(),
            cases["scheduled_start"].max(),
            cases["assessment_completed_at"].max(),
            cases["treatment_started_at"].max(),
        ]
        if pd.notna(value)
    )
    cases["referral_week"] = cases["referral_received_at"].dt.to_period("W-MON").dt.start_time
    cases["referral_month"] = cases["referral_received_at"].dt.to_period("M").astype(str)
    cases["accepted"] = cases["accepted_at"].notna()
    cases["contacted"] = cases["first_contact_at"].notna()
    cases["booked"] = cases["scheduled_start"].notna()
    cases["attended"] = cases["appointment_status"].eq("attended")
    cases["completed"] = cases["assessment_completed_at"].notna()
    cases["treatment"] = cases["treatment_started_at"].notna()
    cases["days_to_contact"] = (
        cases["first_contact_at"] - cases["referral_received_at"]
    ).dt.total_seconds() / 86400
    cases["days_to_assessment"] = (
        cases["assessment_completed_at"] - cases["referral_received_at"]
    ).dt.total_seconds() / 86400
    cases["days_to_treatment"] = (
        cases["treatment_started_at"] - cases["referral_received_at"]
    ).dt.total_seconds() / 86400
    cases["days_open"] = (
        observed_end - cases["referral_received_at"]
    ).dt.total_seconds() / 86400

    conditions = [
        cases["treatment"],
        cases["completed"],
        cases["attended"],
        cases["booked"],
        cases["contacted"],
        cases["accepted"],
    ]
    choices = [
        "treatment_started",
        "assessment_completed",
        "assessment_attended",
        "assessment_booked",
        "first_contact",
        "referral_accepted",
    ]
    cases["current_stage"] = np.select(conditions, choices, default="referral_received")
    cases.loc[cases["referral_status"].eq("rejected"), "current_stage"] = "referral_rejected"

    keep = [
        "referral_id",
        "referral_week",
        "referral_month",
        "funding_route",
        "service_group",
        "accepted",
        "contacted",
        "booked",
        "attended",
        "completed",
        "treatment",
        "days_to_assessment",
        "days_open",
        "current_stage",
    ]
    return cases[keep]


def _prepare_appointments(appointments: pd.DataFrame) -> pd.DataFrame:
    appts = appointments.copy()
    appts["scheduled_start"] = pd.to_datetime(appts["scheduled_start"], errors="coerce")
    appts["scheduled_week"] = appts["scheduled_start"].dt.to_period("W-MON").dt.start_time
    appts["scheduled_month"] = appts["scheduled_start"].dt.to_period("M").astype(str)
    summary = (
        appts.groupby(
            [
                "scheduled_week",
                "scheduled_month",
                "appointment_type",
                "appointment_status",
                "service_group",
                "funding_route",
            ],
            dropna=False,
        )
        .size()
        .rename("appointment_count")
        .reset_index()
    )
    return summary


def _payload(
    *,
    pathway: pd.DataFrame,
    appointments: pd.DataFrame,
    waiting_summary: pd.DataFrame,
    group_summary: pd.DataFrame,
    weekly_actuals: pd.DataFrame,
    forecast: pd.DataFrame,
    forecast_performance: pd.DataFrame,
    capacity_scenarios: pd.DataFrame,
    model_metrics: pd.DataFrame,
    support_queue: pd.DataFrame,
    calibration: pd.DataFrame,
    subgroup_audit: pd.DataFrame,
    validation: pd.DataFrame,
    assessment_duration_minutes: float,
    operations_config: dict,
    action_queue: pd.DataFrame,
) -> dict[str, Any]:
    cases = _prepare_cases(pathway)
    appts = _prepare_appointments(appointments)
    weekly = weekly_actuals.copy()
    weekly["week_start"] = pd.to_datetime(weekly["week_start"], errors="coerce")
    future = forecast.copy()
    future["week_start"] = pd.to_datetime(future["week_start"], errors="coerce")
    capacity = capacity_scenarios.copy()
    capacity["week_start"] = pd.to_datetime(capacity["week_start"], errors="coerce")
    queue = support_queue.copy()
    queue["scheduled_start"] = pd.to_datetime(queue["scheduled_start"], errors="coerce")

    baseline = capacity[capacity["scenario"].eq("baseline")].sort_values("week_start")
    first = baseline.iloc[0]
    initial_backlog = float(
        first["backlog_patients"]
        - first["new_assessment_demand"]
        + first["effective_throughput_patients"]
    )
    assessment_conversion = float(first["new_assessment_demand"] / max(first["predicted_referrals"], 1))

    return {
        "meta": {
            "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "synthetic": True,
            "observed_end": str(cases["referral_month"].max()),
            "assessment_duration_minutes": float(assessment_duration_minutes),
            "initial_backlog": initial_backlog,
            "assessment_conversion": assessment_conversion,
            "base_available_minutes": float(first["available_minutes"]),
            "base_dna_rate": float(first["assumed_dna_rate"]),
            "thresholds": operations_config["thresholds"],
            "default_outreach_capacity": int(
                operations_config["appointment_support"]["default_weekly_outreach_capacity"]
            ),
        },
        "cases": _records(cases),
        "appointments": _records(appts),
        "waiting_summary": _records(waiting_summary),
        "group_summary": _records(group_summary),
        "weekly_actuals": _records(weekly),
        "forecast": _records(future),
        "forecast_performance": _records(forecast_performance),
        "capacity_scenarios": _records(capacity),
        "model_metrics": _records(model_metrics),
        "support_queue": _records(queue),
        "calibration": _records(calibration),
        "subgroup_audit": _records(subgroup_audit),
        "validation": _records(validation),
        "action_queue": _records(action_queue),
        "stage_order": STAGE_ORDER,
        "stage_labels": STAGE_LABELS,
    }


ASSET_DIR = Path(__file__).with_name("assets")


def _html(payload: dict[str, Any], plotly_mode: str) -> str:
    template = (ASSET_DIR / "dashboard.html").read_text(encoding="utf-8")
    css = (ASSET_DIR / "dashboard.css").read_text(encoding="utf-8")
    javascript = (ASSET_DIR / "dashboard.js").read_text(encoding="utf-8")
    safe_json = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")
    if plotly_mode == "inline":
        plotly_tag = f"<script>{get_plotlyjs()}</script>"
    elif plotly_mode == "cdn":
        plotly_tag = '<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>'
    else:
        raise ValueError("plotly_mode must be 'inline' or 'cdn'")
    return (
        template.replace("{{CSS}}", css)
        .replace("{{PLOTLY_TAG}}", plotly_tag)
        .replace("{{DATA_JSON}}", safe_json)
        .replace("{{DASHBOARD_JS}}", javascript)
    )


def build_dashboard(
    *,
    pathway: pd.DataFrame,
    appointments: pd.DataFrame,
    waiting_summary: pd.DataFrame,
    group_summary: pd.DataFrame,
    weekly_actuals: pd.DataFrame,
    forecast: pd.DataFrame,
    forecast_performance: pd.DataFrame,
    capacity_scenarios: pd.DataFrame,
    model_metrics: pd.DataFrame,
    support_queue: pd.DataFrame,
    calibration: pd.DataFrame,
    subgroup_audit: pd.DataFrame,
    validation: pd.DataFrame,
    assessment_duration_minutes: float,
    operations_config: dict,
    action_queue: pd.DataFrame,
    output_path: str | Path,
    plotly_mode: str = "inline",
) -> None:
    """Build an interactive static dashboard from synthetic analytical outputs."""
    payload = _payload(
        pathway=pathway,
        appointments=appointments,
        waiting_summary=waiting_summary,
        group_summary=group_summary,
        weekly_actuals=weekly_actuals,
        forecast=forecast,
        forecast_performance=forecast_performance,
        capacity_scenarios=capacity_scenarios,
        model_metrics=model_metrics,
        support_queue=support_queue,
        calibration=calibration,
        subgroup_audit=subgroup_audit,
        validation=validation,
        assessment_duration_minutes=assessment_duration_minutes,
        operations_config=operations_config,
        action_queue=action_queue,
    )
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_html(payload, plotly_mode), encoding="utf-8")
