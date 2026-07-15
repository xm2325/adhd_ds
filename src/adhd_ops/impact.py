from __future__ import annotations

import numpy as np
import pandas as pd


def build_scenario_impact(
    capacity_scenarios: pd.DataFrame,
    operations_config: dict,
) -> pd.DataFrame:
    """Create a synthetic resource and cost-proxy comparison for stored scenarios.

    Cost fields are planning assumptions from config, not observed provider costs.
    """
    proxy = operations_config["planning_cost_proxies"]
    horizon = int(proxy["horizon_weeks"])
    clinician_hour_cost = float(proxy["clinician_hour_gbp"])

    ordered = capacity_scenarios.sort_values(["scenario", "week_start"]).copy()
    baseline_rows = ordered[ordered["scenario"].eq("baseline")]
    baseline_end = baseline_rows.iloc[-1]
    baseline_minutes = float(baseline_rows["available_minutes"].mean())

    rows: list[dict] = []
    for scenario, group in ordered.groupby("scenario", sort=False):
        end = group.iloc[-1]
        weekly_minutes_delta = float(group["available_minutes"].mean() - baseline_minutes)
        weekly_cost_proxy = weekly_minutes_delta / 60 * clinician_hour_cost
        backlog_reduction = float(baseline_end["backlog_patients"] - end["backlog_patients"])
        horizon_cost = weekly_cost_proxy * horizon
        cost_per_avoided = (
            horizon_cost / backlog_reduction if backlog_reduction > 0 and horizon_cost > 0 else np.nan
        )
        rows.append({
            "scenario": scenario,
            "end_backlog": float(end["backlog_patients"]),
            "end_wait_days_proxy": float(end["wait_days_proxy"]),
            "backlog_change_vs_baseline": float(end["backlog_patients"] - baseline_end["backlog_patients"]),
            "wait_change_vs_baseline": float(end["wait_days_proxy"] - baseline_end["wait_days_proxy"]),
            "weekly_clinical_minutes_change": weekly_minutes_delta,
            "weekly_cost_proxy_gbp": weekly_cost_proxy,
            "horizon_cost_proxy_gbp": horizon_cost,
            "backlog_patients_avoided": max(backlog_reduction, 0.0),
            "cost_per_backlog_patient_avoided_gbp": cost_per_avoided,
            "synthetic": True,
        })
    return pd.DataFrame(rows)


def build_outreach_impact(
    scored_appointments: pd.DataFrame,
    operations_config: dict,
    capacities: tuple[int, ...] = (25, 50, 100, 150, 200),
) -> pd.DataFrame:
    """Build a capacity-limited outreach impact calculator using declared assumptions."""
    proxy = operations_config["planning_cost_proxies"]
    contact_cost = float(proxy["patient_support_contact_gbp"])
    unused_slot_proxy = float(proxy["unused_assessment_slot_gbp"])
    relative_reduction = float(proxy["outreach_relative_dna_reduction"])
    ranked = scored_appointments.sort_values("predicted_dna_probability", ascending=False)

    rows = []
    for capacity in capacities:
        selected = ranked.head(min(capacity, len(ranked)))
        expected_dna = float(selected["predicted_dna_probability"].sum())
        expected_appointments_recovered = expected_dna * relative_reduction
        outreach_cost = len(selected) * contact_cost
        avoided_slot_proxy = expected_appointments_recovered * unused_slot_proxy
        rows.append({
            "outreach_capacity": int(len(selected)),
            "expected_dna_without_support": expected_dna,
            "assumed_relative_dna_reduction": relative_reduction,
            "expected_appointments_recovered": expected_appointments_recovered,
            "outreach_cost_proxy_gbp": outreach_cost,
            "avoided_unused_slot_proxy_gbp": avoided_slot_proxy,
            "net_value_proxy_gbp": avoided_slot_proxy - outreach_cost,
            "synthetic": True,
        })
    return pd.DataFrame(rows)
