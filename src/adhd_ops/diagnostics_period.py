from __future__ import annotations

import numpy as np
import pandas as pd

from adhd_ops.diagnostics_common import PERIOD_WEEKS, _datetime, _safe_relative_change


def build_period_comparison(
    tables: dict[str, pd.DataFrame],
    *,
    assessment_duration_minutes: float,
    period_weeks: int = PERIOD_WEEKS,
) -> pd.DataFrame:
    referrals = _datetime(
        tables["referrals"],
        ["referral_received_at", "accepted_at", "first_contact_at"],
    )
    appointments = _datetime(
        tables["appointments"],
        ["booked_at", "scheduled_start", "cancelled_at"],
    )
    assessments = _datetime(
        tables["assessments"],
        ["assessment_started_at", "assessment_completed_at"],
    )
    capacity = _datetime(tables["clinician_capacity"], ["week_start"])

    coverage_ends = [
        referrals["referral_received_at"].max() + pd.Timedelta(days=1),
        appointments["scheduled_start"].max() + pd.Timedelta(days=1),
        assessments["assessment_completed_at"].max() + pd.Timedelta(days=1),
        capacity["week_start"].max() + pd.Timedelta(days=7),
    ]
    period_end = min(value for value in coverage_ends if pd.notna(value))
    recent_start = period_end - pd.Timedelta(weeks=period_weeks)
    previous_start = recent_start - pd.Timedelta(weeks=period_weeks)

    def period_mask(series: pd.Series, start: pd.Timestamp, end: pd.Timestamp) -> pd.Series:
        return series.ge(start) & series.lt(end)

    def metrics(start: pd.Timestamp, end: pd.Timestamp) -> dict[str, float]:
        referral_group = referrals[period_mask(referrals["referral_received_at"], start, end)].copy()
        scheduled = appointments[period_mask(appointments["scheduled_start"], start, end)].copy()
        assessment_appointments = scheduled[scheduled["appointment_type"].eq("assessment")].copy()
        eligible = scheduled[scheduled["appointment_status"].isin(["attended", "did_not_attend"])]
        completed = assessments[period_mask(assessments["assessment_completed_at"], start, end)]
        assessment_capacity = capacity[
            period_mask(capacity["week_start"], start, end)
            & capacity["service_type"].eq("assessment")
        ]
        effective_minutes = (
            assessment_capacity["available_minutes"] - assessment_capacity["absence_minutes"]
        ).clip(lower=0)
        contact_days = (
            referral_group["first_contact_at"] - referral_group["referral_received_at"]
        ).dt.total_seconds() / 86400
        lead_days = (
            scheduled["scheduled_start"] - scheduled["booked_at"]
        ).dt.total_seconds() / 86400
        return {
            "referrals_received": float(len(referral_group)),
            "referral_acceptance_rate": float(referral_group["accepted_at"].notna().mean()) if len(referral_group) else np.nan,
            "median_referral_to_contact_days": float(contact_days.median()),
            "assessments_completed": float(len(completed)),
            "assessment_appointments_scheduled": float(len(assessment_appointments)),
            "appointment_dna_rate": float(eligible["appointment_status"].eq("did_not_attend").mean()) if len(eligible) else np.nan,
            "appointment_cancellation_rate": float(scheduled["appointment_status"].str.startswith("cancelled").mean()) if len(scheduled) else np.nan,
            "median_booking_lead_days": float(lead_days.median()),
            "assessment_capacity_minutes": float(effective_minutes.sum()),
            "assessment_slot_equivalent": float(effective_minutes.sum() / assessment_duration_minutes),
            "assessment_capacity_per_referral": float(
                (effective_minutes.sum() / assessment_duration_minutes) / max(len(referral_group), 1)
            ),
        }

    previous = metrics(previous_start, recent_start)
    recent = metrics(recent_start, period_end)
    units = {
        "referrals_received": "count",
        "referral_acceptance_rate": "rate",
        "median_referral_to_contact_days": "days",
        "assessments_completed": "count",
        "assessment_appointments_scheduled": "count",
        "appointment_dna_rate": "rate",
        "appointment_cancellation_rate": "rate",
        "median_booking_lead_days": "days",
        "assessment_capacity_minutes": "minutes",
        "assessment_slot_equivalent": "appointments",
        "assessment_capacity_per_referral": "ratio",
    }
    rows = []
    for metric, previous_value in previous.items():
        recent_value = recent[metric]
        rows.append(
            {
                "metric": metric,
                "unit": units[metric],
                "previous_period_start": previous_start,
                "previous_period_end": recent_start,
                "recent_period_start": recent_start,
                "recent_period_end": period_end,
                "previous_value": previous_value,
                "recent_value": recent_value,
                "absolute_change": float(recent_value - previous_value),
                "relative_change": _safe_relative_change(previous_value, recent_value),
                "interpretation_boundary": "Operational period comparison; recent referral outcomes may be right-censored.",
            }
        )
    return pd.DataFrame(rows)
