from __future__ import annotations

import numpy as np
import pandas as pd

from adhd_ops.diagnostics_common import _datetime


def build_stage_duration_decomposition(pathway: pd.DataFrame) -> pd.DataFrame:
    data = _datetime(
        pathway,
        [
            "referral_received_at",
            "accepted_at",
            "first_contact_at",
            "booked_at",
            "scheduled_start",
            "assessment_completed_at",
            "treatment_started_at",
        ],
    )
    specs = [
        ("referral_processing", "referral_received_at", "accepted_at", "Referral received → accepted"),
        ("initial_contact", "accepted_at", "first_contact_at", "Accepted → first contact"),
        ("booking_process", "first_contact_at", "booked_at", "First contact → booking created"),
        ("appointment_queue", "booked_at", "scheduled_start", "Booking created → assessment slot"),
        ("assessment_delivery", "scheduled_start", "assessment_completed_at", "Assessment start → completed"),
        ("treatment_transition", "assessment_completed_at", "treatment_started_at", "Assessment completed → treatment"),
    ]
    duration_columns: list[str] = []
    labels: dict[str, str] = {}
    for key, start, end, label in specs:
        column = f"duration_{key}_days"
        duration_columns.append(column)
        labels[key] = label
        data[column] = (data[end] - data[start]).dt.total_seconds() / 86400
        data.loc[data[column].lt(0), column] = np.nan

    complete = data.dropna(subset=duration_columns).copy()
    complete_total_mean = float(complete[duration_columns].sum(axis=1).mean()) if len(complete) else np.nan
    rows = []
    for key, _, _, _ in specs:
        column = f"duration_{key}_days"
        series = data[column]
        complete_mean = float(complete[column].mean()) if len(complete) else np.nan
        rows.append(
            {
                "stage_key": key,
                "stage_label": labels[key],
                "n_observed": int(series.notna().sum()),
                "median_days": float(series.median()),
                "p90_days": float(series.quantile(0.9)),
                "mean_days": float(series.mean()),
                "complete_pathway_n": int(len(complete)),
                "complete_pathway_mean_days": complete_mean,
                "share_of_complete_pathway_mean": float(complete_mean / complete_total_mean) if complete_total_mean else np.nan,
                "interpretation_boundary": "Descriptive stage duration; not a causal attribution of delay.",
            }
        )
    return pd.DataFrame(rows).sort_values("share_of_complete_pathway_mean", ascending=False).reset_index(drop=True)


def build_metric_definition_sensitivity(pathway: pd.DataFrame) -> pd.DataFrame:
    data = _datetime(
        pathway,
        ["referral_received_at", "accepted_at", "first_contact_at", "booked_at", "assessment_completed_at"],
    )
    definitions = [
        ("patient_experience_wait", "referral_received_at", "Referral received → completed assessment"),
        ("accepted_pathway_wait", "accepted_at", "Referral accepted → completed assessment"),
        ("post_contact_wait", "first_contact_at", "First contact → completed assessment"),
        ("booking_queue_wait", "booked_at", "Booking created → completed assessment"),
    ]
    rows = []
    baseline_median = None
    for key, start, label in definitions:
        duration = (data["assessment_completed_at"] - data[start]).dt.total_seconds() / 86400
        duration = duration.where(duration.ge(0))
        median = float(duration.median())
        if baseline_median is None:
            baseline_median = median
        rows.append(
            {
                "definition": key,
                "label": label,
                "n": int(duration.notna().sum()),
                "median_days": median,
                "p90_days": float(duration.quantile(0.9)),
                "missing_start_or_end": int(duration.isna().sum()),
                "median_difference_vs_patient_experience": float(median - baseline_median),
                "decision_use": {
                    "patient_experience_wait": "End-to-end patient experience and access reporting",
                    "accepted_pathway_wait": "Operational performance after referral acceptance",
                    "post_contact_wait": "Scheduling and clinical-capacity review",
                    "booking_queue_wait": "Appointment-queue management",
                }[key],
            }
        )
    return pd.DataFrame(rows)
