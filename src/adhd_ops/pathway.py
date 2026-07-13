from __future__ import annotations

import numpy as np
import pandas as pd


def analyse_pathway(tables: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    referrals = tables["referrals"].copy()
    appointments = tables["appointments"].copy()
    assessments = tables["assessments"].copy()
    treatments = tables["treatment_events"].copy()

    first_assessment = (
        appointments[appointments["appointment_type"].eq("assessment")]
        .sort_values("scheduled_start")
        .drop_duplicates("referral_id")
    )
    pathway = referrals.merge(
        first_assessment[["referral_id", "appointment_id", "booked_at", "scheduled_start", "appointment_status"]],
        on="referral_id",
        how="left",
    )
    pathway = pathway.merge(
        assessments[["appointment_id", "assessment_completed_at"]], on="appointment_id", how="left"
    )
    first_treatment = treatments.sort_values("event_at").drop_duplicates("referral_id")
    pathway = pathway.merge(
        first_treatment[["referral_id", "event_at"]].rename(columns={"event_at": "treatment_started_at"}),
        on="referral_id",
        how="left",
    )

    stages = [
        ("referral_received", pathway["referral_received_at"].notna()),
        ("referral_accepted", pathway["accepted_at"].notna()),
        ("first_contact", pathway["first_contact_at"].notna()),
        ("assessment_booked", pathway["scheduled_start"].notna()),
        ("assessment_attended", pathway["appointment_status"].eq("attended")),
        ("assessment_completed", pathway["assessment_completed_at"].notna()),
        ("treatment_started", pathway["treatment_started_at"].notna()),
    ]
    stage_rows, previous = [], None
    for stage, mask in stages:
        count = int(mask.sum())
        stage_rows.append({
            "stage": stage,
            "patient_count": count,
            "conversion_from_previous": np.nan if previous in (None, 0) else count / previous,
            "conversion_from_referral": count / len(pathway),
        })
        previous = count
    stage_summary = pd.DataFrame(stage_rows)

    metrics = {
        "referral_to_contact_days": (pathway["first_contact_at"] - pathway["referral_received_at"]).dt.total_seconds() / 86400,
        "referral_to_assessment_days": (pathway["assessment_completed_at"] - pathway["referral_received_at"]).dt.total_seconds() / 86400,
        "acceptance_to_assessment_days": (pathway["assessment_completed_at"] - pathway["accepted_at"]).dt.total_seconds() / 86400,
        "assessment_to_treatment_days": (pathway["treatment_started_at"] - pathway["assessment_completed_at"]).dt.total_seconds() / 86400,
    }
    waiting_summary = pd.DataFrame([
        {
            "metric": name,
            "n": int(series.notna().sum()),
            "median_days": float(series.median()),
            "p90_days": float(series.quantile(0.9)),
            "mean_days": float(series.mean()),
        }
        for name, series in metrics.items()
    ])

    pathway["referral_month"] = pathway["referral_received_at"].dt.to_period("M").astype(str)
    cohort_rows = []
    for month, group in pathway.groupby("referral_month"):
        for horizon in (30, 60, 90):
            deadline = group["referral_received_at"] + pd.to_timedelta(horizon, unit="D")
            cohort_rows.append({
                "referral_month": month,
                "horizon_days": horizon,
                "referrals": len(group),
                "assessment_completed_rate": float(
                    (group["assessment_completed_at"].notna() & (group["assessment_completed_at"] <= deadline)).mean()
                ),
                "treatment_started_rate": float(
                    (group["treatment_started_at"].notna() & (group["treatment_started_at"] <= deadline)).mean()
                ),
            })
    cohort_progression = pd.DataFrame(cohort_rows)

    pathway["referral_to_assessment_days"] = (
        pathway["assessment_completed_at"] - pathway["referral_received_at"]
    ).dt.total_seconds() / 86400
    group_summary = (
        pathway.groupby(["funding_route", "service_group"], dropna=False)
        .agg(
            referrals=("referral_id", "size"),
            assessments_completed=("assessment_completed_at", lambda s: s.notna().sum()),
            treatment_started=("treatment_started_at", lambda s: s.notna().sum()),
            median_referral_to_assessment_days=("referral_to_assessment_days", "median"),
            p90_referral_to_assessment_days=("referral_to_assessment_days", lambda s: s.quantile(0.9)),
        )
        .reset_index()
    )
    return {
        "patient_pathway": pathway,
        "stage_summary": stage_summary,
        "waiting_summary": waiting_summary,
        "cohort_progression": cohort_progression,
        "group_summary": group_summary,
    }
