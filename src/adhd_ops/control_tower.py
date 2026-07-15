from __future__ import annotations

import numpy as np
import pandas as pd


def _higher_bad(value: float, amber: float, red: float) -> str:
    if value >= red:
        return "red"
    if value >= amber:
        return "amber"
    return "green"


def _lower_bad(value: float, amber: float, red: float) -> str:
    if value <= red:
        return "red"
    if value <= amber:
        return "amber"
    return "green"


def build_service_level_status(
    patient_pathway: pd.DataFrame,
    capacity_scenarios: pd.DataFrame,
    validation: pd.DataFrame,
    attendance_monitoring: pd.DataFrame,
    forecast_monitoring: pd.DataFrame,
    selected_forecast_model: str,
    operations_config: dict,
) -> pd.DataFrame:
    """Create a compact service-level and analytical-control scorecard."""
    thresholds = operations_config["thresholds"]
    pathway = patient_pathway.copy()
    for column in ["referral_received_at", "assessment_completed_at", "accepted_at"]:
        pathway[column] = pd.to_datetime(pathway[column], errors="coerce")
    waits = (
        pathway["assessment_completed_at"] - pathway["referral_received_at"]
    ).dt.total_seconds() / 86400
    p90_wait = float(waits.quantile(0.9))
    accepted = int(pathway["accepted_at"].notna().sum())
    completion_rate = float(pathway["assessment_completed_at"].notna().sum() / max(accepted, 1))
    baseline = (
        capacity_scenarios[capacity_scenarios["scenario"].eq("baseline")]
        .sort_values("week_start")
        .iloc[-1]
    )
    quality_failures = int(
        validation[
            validation["severity"].eq("error") & validation["failure_count"].gt(0)
        ].shape[0]
    )
    minimum_n = int(thresholds["minimum_monitoring_n"])
    reliable = attendance_monitoring[attendance_monitoring["n"].ge(minimum_n)]
    calibration_gap = (
        float(reliable.sort_values("monitoring_month").iloc[-1]["absolute_calibration_gap"])
        if not reliable.empty
        else np.nan
    )
    selected = forecast_monitoring[forecast_monitoring["model"].eq(selected_forecast_model)]
    forecast_wape = (
        float(selected.sort_values("origin_week").iloc[-1]["wape"])
        if not selected.empty
        else np.nan
    )

    rows = [
        {
            "control_id": "SLO-001",
            "category": "Patient access",
            "control": "P90 referral-to-assessment wait",
            "value": p90_wait,
            "display_unit": "days",
            "status": _higher_bad(
                p90_wait,
                float(thresholds["p90_assessment_wait_amber_days"]),
                float(thresholds["p90_assessment_wait_days"]),
            ),
            "owner_role": "Operations lead",
            "response": "Review longest open cases and assessment capacity",
        },
        {
            "control_id": "SLO-002",
            "category": "Service flow",
            "control": "Baseline end backlog",
            "value": float(baseline["backlog_patients"]),
            "display_unit": "patients",
            "status": _higher_bad(
                float(baseline["backlog_patients"]),
                float(thresholds["backlog_amber_patients"]),
                float(thresholds["backlog_review_patients"]),
            ),
            "owner_role": "Clinical operations",
            "response": "Review budget-constrained resource plans",
        },
        {
            "control_id": "SLO-003",
            "category": "Pathway",
            "control": "Completed assessments per accepted referral",
            "value": completion_rate,
            "display_unit": "rate",
            "status": _lower_bad(
                completion_rate,
                float(thresholds["completed_per_accepted_amber_rate"]),
                float(thresholds["completed_per_accepted_review_rate"]),
            ),
            "owner_role": "Pathway manager",
            "response": "Separate booking, attendance and open-case drivers",
        },
        {
            "control_id": "SLO-004",
            "category": "Data",
            "control": "Error-level data-quality failures",
            "value": float(quality_failures),
            "display_unit": "rules",
            "status": "green" if quality_failures == 0 else "red",
            "owner_role": "Data engineering",
            "response": "Stop publication on any error-level failure",
        },
        {
            "control_id": "SLO-005",
            "category": "Appointment model",
            "control": "Latest absolute calibration gap",
            "value": calibration_gap,
            "display_unit": "rate",
            "status": (
                _higher_bad(
                    calibration_gap,
                    float(thresholds["attendance_calibration_gap_amber"]),
                    float(thresholds["attendance_calibration_gap"]),
                )
                if np.isfinite(calibration_gap)
                else "unknown"
            ),
            "owner_role": "Model owner",
            "response": "Review calibration and promotion status",
        },
        {
            "control_id": "SLO-006",
            "category": "Demand model",
            "control": "Latest rolling-origin WAPE",
            "value": forecast_wape,
            "display_unit": "rate",
            "status": (
                _higher_bad(
                    forecast_wape,
                    float(thresholds["forecast_wape_amber"]),
                    float(thresholds["forecast_wape_review"]),
                )
                if np.isfinite(forecast_wape)
                else "unknown"
            ),
            "owner_role": "Forecast owner",
            "response": "Review demand shift and interval width",
        },
    ]
    frame = pd.DataFrame(rows)
    frame["synthetic"] = True
    return frame


def _robust_series_anomalies(
    dates: pd.Series,
    values: pd.Series,
    series_name: str,
    operations_config: dict,
    window: int = 12,
) -> list[dict]:
    amber = float(operations_config["thresholds"]["anomaly_robust_z_amber"])
    red = float(operations_config["thresholds"]["anomaly_robust_z_red"])
    rows: list[dict] = []
    values = values.astype(float).reset_index(drop=True)
    dates = pd.to_datetime(dates).reset_index(drop=True)
    for idx in range(window, len(values)):
        history = values.iloc[idx - window : idx]
        expected = float(history.median())
        mad = float((history - expected).abs().median())
        robust_z = 0.0 if mad == 0 else float(0.6745 * (values.iloc[idx] - expected) / mad)
        magnitude = abs(robust_z)
        status = "red" if magnitude >= red else "amber" if magnitude >= amber else "normal"
        rows.append(
            {
                "series": series_name,
                "period_start": dates.iloc[idx],
                "observed_value": float(values.iloc[idx]),
                "expected_rolling_median": expected,
                "robust_z": robust_z,
                "direction": "above" if robust_z > 0 else "below" if robust_z < 0 else "at_expected",
                "status": status,
                "synthetic": True,
            }
        )
    return rows


def build_weekly_anomalies(
    weekly_actuals: pd.DataFrame,
    appointments: pd.DataFrame,
    operations_config: dict,
) -> pd.DataFrame:
    """Detect robust weekly anomalies in referral volume and DNA rate."""
    rows = _robust_series_anomalies(
        weekly_actuals["week_start"],
        weekly_actuals["referrals"],
        "weekly_referrals",
        operations_config,
    )
    appts = appointments[
        appointments["appointment_status"].isin(["attended", "did_not_attend"])
    ].copy()
    appts["week_start"] = pd.to_datetime(appts["scheduled_start"]).dt.to_period("W-SUN").dt.start_time
    appts["dna"] = appts["appointment_status"].eq("did_not_attend").astype(int)
    weekly_dna = (
        appts.groupby("week_start", as_index=False)
        .agg(dna_rate=("dna", "mean"), n=("dna", "size"))
        .sort_values("week_start")
    )
    rows.extend(
        _robust_series_anomalies(
            weekly_dna["week_start"],
            weekly_dna["dna_rate"],
            "weekly_dna_rate",
            operations_config,
        )
    )
    return pd.DataFrame(rows).sort_values(["period_start", "series"]).reset_index(drop=True)
