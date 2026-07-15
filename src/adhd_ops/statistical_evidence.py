from __future__ import annotations

from math import sqrt
from typing import Any

import numpy as np
import pandas as pd


def _wilson(events: int, n: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if n <= 0:
        return (float("nan"), float("nan"))
    p = events / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    margin = z * sqrt((p * (1 - p) + z * z / (4 * n)) / n) / denom
    return max(0.0, centre - margin), min(1.0, centre + margin)


def _bootstrap_interval(values: np.ndarray, statistic: str, seed: int, draws: int = 800) -> tuple[float, float]:
    clean = values[np.isfinite(values)]
    if len(clean) == 0:
        return (float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    estimates = np.empty(draws, dtype=float)
    for i in range(draws):
        sample = rng.choice(clean, size=len(clean), replace=True)
        estimates[i] = np.median(sample) if statistic == "median" else np.quantile(sample, 0.90)
    return float(np.quantile(estimates, 0.025)), float(np.quantile(estimates, 0.975))


def build_kpi_uncertainty(
    tables: dict[str, pd.DataFrame], patient_pathway: pd.DataFrame, *, seed: int = 20260715
) -> pd.DataFrame:
    appointments = tables["appointments"].copy()
    waits = pd.to_numeric(patient_pathway["referral_to_assessment_days"], errors="coerce").dropna().to_numpy()
    accepted = patient_pathway["referral_status"].eq("accepted")
    completed = patient_pathway["assessment_completed_at"].notna() & accepted

    rows: list[dict[str, Any]] = []
    dna_n = int(appointments["appointment_status"].isin(["attended", "dna"]).sum())
    dna_events = int(appointments["appointment_status"].eq("dna").sum())
    dna_low, dna_high = _wilson(dna_events, dna_n)
    rows.append({
        "metric": "appointment_dna_rate",
        "estimate": dna_events / max(dna_n, 1),
        "lower_95": dna_low,
        "upper_95": dna_high,
        "unit": "proportion",
        "n": dna_n,
        "events": dna_events,
        "method": "Wilson score interval",
        "decision_use": "Quantifies uncertainty around the observed synthetic DNA rate.",
    })

    completion_n = int(accepted.sum())
    completion_events = int(completed.sum())
    comp_low, comp_high = _wilson(completion_events, completion_n)
    rows.append({
        "metric": "accepted_to_completed_rate",
        "estimate": completion_events / max(completion_n, 1),
        "lower_95": comp_low,
        "upper_95": comp_high,
        "unit": "proportion",
        "n": completion_n,
        "events": completion_events,
        "method": "Wilson score interval",
        "decision_use": "Shows precision of pathway completion among accepted referrals.",
    })

    for idx, (metric, stat) in enumerate([
        ("median_referral_to_assessment_days", "median"),
        ("p90_referral_to_assessment_days", "p90"),
    ]):
        estimate = float(np.median(waits) if stat == "median" else np.quantile(waits, 0.90))
        low, high = _bootstrap_interval(waits, stat, seed + idx)
        rows.append({
            "metric": metric,
            "estimate": estimate,
            "lower_95": low,
            "upper_95": high,
            "unit": "days",
            "n": int(len(waits)),
            "events": int(len(waits)),
            "method": "Patient-level percentile bootstrap",
            "decision_use": "Separates estimated waiting-time level from sampling uncertainty.",
        })

    referrals = tables["referrals"].copy()
    referrals["week"] = pd.to_datetime(referrals["referral_received_at"]).dt.to_period("W-MON").dt.start_time
    weekly = referrals.groupby("week").size().to_numpy(dtype=float)
    rng = np.random.default_rng(seed + 99)
    boot_means = np.array([rng.choice(weekly, size=len(weekly), replace=True).mean() for _ in range(800)])
    rows.append({
        "metric": "mean_weekly_referrals",
        "estimate": float(weekly.mean()),
        "lower_95": float(np.quantile(boot_means, 0.025)),
        "upper_95": float(np.quantile(boot_means, 0.975)),
        "unit": "referrals_per_week",
        "n": int(len(weekly)),
        "events": int(referrals.shape[0]),
        "method": "Week-level bootstrap",
        "decision_use": "Quantifies historical weekly-demand uncertainty without treating referrals as independent days.",
    })
    return pd.DataFrame(rows)


def build_subgroup_reliability(scored_test: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for dimension in ["service_group", "funding_route", "appointment_type"]:
        for segment, group in scored_test.groupby(dimension, dropna=False):
            n = int(len(group))
            events = int(group["observed_dna"].sum())
            low, high = _wilson(events, n)
            predicted = float(group["predicted_dna_probability"].mean())
            observed = events / max(n, 1)
            status = "adequate" if n >= 200 and events >= 20 else "review" if n >= 80 and events >= 8 else "insufficient"
            rows.append({
                "dimension": dimension,
                "segment": str(segment),
                "n": n,
                "events": events,
                "observed_rate": observed,
                "lower_95": low,
                "upper_95": high,
                "mean_predicted_probability": predicted,
                "calibration_gap": predicted - observed,
                "reliability_status": status,
                "minimum_action": (
                    "Report with interval" if status == "adequate" else
                    "Pool periods or use partial pooling" if status == "review" else
                    "Do not make a standalone group decision"
                ),
            })
    return pd.DataFrame(rows)
