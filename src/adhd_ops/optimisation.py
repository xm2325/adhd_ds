from __future__ import annotations

import numpy as np
import pandas as pd


def build_resource_optimisation(
    capacity_scenarios: pd.DataFrame,
    operations_config: dict,
    assessment_duration_minutes: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Enumerate cost-constrained assessment-capacity and outreach plans.

    The calculation uses synthetic planning assumptions. It is a transparent
    decision aid rather than a mathematical claim about a real service.
    """
    cfg = operations_config["resource_optimisation"]
    proxy = operations_config["planning_cost_proxies"]
    baseline = (
        capacity_scenarios[capacity_scenarios["scenario"].eq("baseline")]
        .sort_values("week_start")
        .reset_index(drop=True)
    )
    if baseline.empty:
        raise ValueError("baseline capacity scenario is required")

    first = baseline.iloc[0]
    initial_backlog = float(
        first["backlog_patients"]
        - first["new_assessment_demand"]
        + first["effective_throughput_patients"]
    )
    base_available = float(first["available_minutes"])
    base_dna = float(first["assumed_dna_rate"])
    horizon = len(baseline)
    targetable = max(float(cfg["targetable_appointments_per_week"]), 1.0)
    max_relative_reduction = float(proxy["outreach_relative_dna_reduction"])
    clinician_hour_cost = float(proxy["clinician_hour_gbp"])
    contact_cost = float(proxy["patient_support_contact_gbp"])
    baseline_end = float(baseline.iloc[-1]["backlog_patients"])

    rows: list[dict] = []
    plan_number = 0
    for extra_minutes in cfg["extra_assessment_minutes_options"]:
        for outreach_capacity in cfg["outreach_capacity_options"]:
            plan_number += 1
            coverage = min(float(outreach_capacity) / targetable, 1.0)
            relative_dna_reduction = max_relative_reduction * coverage
            effective_dna = base_dna * (1 - relative_dna_reduction)
            available = base_available + float(extra_minutes)
            throughput = (available / assessment_duration_minutes) * (1 - effective_dna)
            backlog = initial_backlog
            for _, week in baseline.iterrows():
                backlog = max(0.0, backlog + float(week["new_assessment_demand"]) - throughput)
            wait_proxy = 7 * backlog / max(throughput, 1.0)
            horizon_cost = horizon * (
                float(extra_minutes) / 60 * clinician_hour_cost
                + float(outreach_capacity) * contact_cost
            )
            avoided = max(0.0, baseline_end - backlog)
            rows.append(
                {
                    "plan_id": f"PLAN-{plan_number:03d}",
                    "extra_assessment_minutes_per_week": int(extra_minutes),
                    "outreach_contacts_per_week": int(outreach_capacity),
                    "outreach_coverage_ratio": coverage,
                    "assumed_relative_dna_reduction": relative_dna_reduction,
                    "effective_weekly_throughput": throughput,
                    "end_backlog": backlog,
                    "end_wait_days_proxy": wait_proxy,
                    "horizon_cost_proxy_gbp": horizon_cost,
                    "backlog_patients_avoided": avoided,
                    "cost_per_backlog_patient_avoided_gbp": (
                        horizon_cost / avoided if avoided > 0 else np.nan
                    ),
                    "synthetic": True,
                }
            )

    grid = pd.DataFrame(rows)
    pareto = []
    for idx, row in grid.iterrows():
        dominated = (
            (grid["horizon_cost_proxy_gbp"] <= row["horizon_cost_proxy_gbp"])
            & (grid["end_backlog"] <= row["end_backlog"])
            & (
                (grid["horizon_cost_proxy_gbp"] < row["horizon_cost_proxy_gbp"])
                | (grid["end_backlog"] < row["end_backlog"])
            )
        ).any()
        pareto.append(not bool(dominated))
    grid["pareto_efficient"] = pareto
    grid = grid.sort_values(
        ["horizon_cost_proxy_gbp", "end_backlog", "outreach_contacts_per_week"]
    ).reset_index(drop=True)

    recommendations: list[dict] = []
    for budget in cfg["budgets_gbp"]:
        feasible = grid[grid["horizon_cost_proxy_gbp"].le(float(budget))]
        if feasible.empty:
            continue
        best = feasible.sort_values(
            ["end_backlog", "horizon_cost_proxy_gbp", "outreach_contacts_per_week"]
        ).iloc[0]
        recommendations.append(
            {
                "budget_gbp": float(budget),
                "plan_id": best["plan_id"],
                "extra_assessment_minutes_per_week": int(
                    best["extra_assessment_minutes_per_week"]
                ),
                "outreach_contacts_per_week": int(best["outreach_contacts_per_week"]),
                "end_backlog": float(best["end_backlog"]),
                "end_wait_days_proxy": float(best["end_wait_days_proxy"]),
                "horizon_cost_proxy_gbp": float(best["horizon_cost_proxy_gbp"]),
                "backlog_patients_avoided": float(best["backlog_patients_avoided"]),
                "synthetic": True,
            }
        )
    return grid, pd.DataFrame(recommendations)


def build_backlog_driver_decomposition(capacity_scenarios: pd.DataFrame) -> pd.DataFrame:
    """Summarise scenario differences from baseline as planning sensitivities.

    These values are not causal attribution because each stored scenario changes
    a declared assumption rather than reproducing a controlled intervention.
    """
    end = (
        capacity_scenarios.sort_values("week_start")
        .groupby("scenario", as_index=False)
        .tail(1)
        .copy()
    )
    baseline = float(end.loc[end["scenario"].eq("baseline"), "backlog_patients"].iloc[0])
    labels = {
        "add_one_assessment_clinic": "Additional assessment capacity",
        "demand_up_10pct": "Higher referral demand",
        "reduce_dna_20pct": "Lower DNA assumption",
        "clinician_absence_10pct": "Reduced clinician availability",
        "baseline": "Baseline",
    }
    end["driver"] = end["scenario"].map(labels).fillna(end["scenario"])
    end["backlog_difference_vs_baseline"] = end["backlog_patients"] - baseline
    end["direction"] = np.select(
        [
            end["backlog_difference_vs_baseline"].gt(0),
            end["backlog_difference_vs_baseline"].lt(0),
        ],
        ["increases_backlog", "reduces_backlog"],
        default="baseline",
    )
    end["synthetic"] = True
    return end[
        [
            "scenario",
            "driver",
            "backlog_patients",
            "backlog_difference_vs_baseline",
            "direction",
            "synthetic",
        ]
    ].sort_values("backlog_difference_vs_baseline")
