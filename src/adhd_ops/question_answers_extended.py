from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from adhd_ops.config import load_yaml


def _items(config_root: str | Path) -> list[dict[str, Any]]:
    root = Path(config_root)
    items: list[dict[str, Any]] = []
    for path in sorted((root / "ds_questions").glob("*.yaml")):
        if path.name[:2].isdigit() and int(path.name[:2]) >= 7:
            items.extend(load_yaml(path).get("questions", []))
    return items


def build_answers(
    *,
    config_root: str | Path,
    summary: dict[str, Any],
    kpi_uncertainty: pd.DataFrame,
    subgroup_reliability: pd.DataFrame,
    period_comparison: pd.DataFrame,
    experiment_design: pd.DataFrame,
    model_registry: pd.DataFrame,
    attendance_monitoring: pd.DataFrame,
    threshold_grid: pd.DataFrame,
    queue_policy: pd.DataFrame,
    incident_register: pd.DataFrame,
    data_lineage: pd.DataFrame,
    budget_recommendations: pd.DataFrame,
) -> dict[str, str]:
    wait = kpi_uncertainty[kpi_uncertainty["metric"].eq("median_referral_to_assessment_days")].iloc[0]
    dna = kpi_uncertainty[kpi_uncertainty["metric"].eq("appointment_dna_rate")].iloc[0]
    insufficient = int(subgroup_reliability["reliability_status"].eq("insufficient").sum())
    review = int(subgroup_reliability["reliability_status"].eq("review").sum())
    largest = period_comparison.assign(abs_change=lambda x: x["relative_change"].abs()).sort_values("abs_change", ascending=False).iloc[0]
    pilot = experiment_design.sort_values("total_sample_size").iloc[0]
    champion = model_registry[model_registry["status"].eq("champion")].iloc[0]
    latest_monitor = attendance_monitoring.sort_values("monitoring_month").iloc[-1]
    capacity = int(summary.get("default_outreach_capacity", 100))
    policy_rows = threshold_grid[threshold_grid["weekly_capacity"].eq(capacity)]
    policy = policy_rows.sort_values(["expected_appointments_recovered", "precision"], ascending=False).iloc[0]
    queue_best = queue_policy.sort_values(["max_wait_remaining", "funding_route_selection_gap"]).iloc[0]
    incidents = int(incident_register["status"].isin(["open", "triage"]).sum())
    budget = budget_recommendations.iloc[(budget_recommendations["budget_gbp"] - 10000).abs().argsort()[:1]].iloc[0]

    base = {
        "statistical_inference_and_uncertainty": (
            f"The synthetic median wait is {wait['estimate']:.1f} days with a bootstrap 95% interval of "
            f"{wait['lower_95']:.1f}–{wait['upper_95']:.1f}; the observed DNA rate is {dna['estimate']:.1%} "
            f"({dna['lower_95']:.1%}–{dna['upper_95']:.1%}). {insufficient} subgroup rows are marked insufficient "
            f"and {review} require review, so point estimates alone are not decision-ready."
        ),
        "causal_inference_and_policy_evaluation": (
            f"The current build contains descriptive changes and a planning trial, not an identified provider effect. "
            f"The largest relative period movement is {largest['metric'].replace('_', ' ')} ({largest['relative_change']:.1%}); "
            f"the smallest configured reminder scenario still requires about {int(pilot['total_sample_size']):,} appointments. "
            "A causal claim remains gated behind randomisation or a reviewed quasi-experimental design."
        ),
        "model_development_and_validation": (
            f"The registered champion is {champion['model']} with PR-AUC {champion['pr_auc']:.3f} and Brier "
            f"{champion['brier_score']:.3f} on later synthetic data. The latest monthly calibration gap is "
            f"{latest_monitor['calibration_gap']:.1%}; deployment still requires external validation, feature-availability checks "
            "and prospective workflow evaluation."
        ),
        "fairness_safety_and_human_factors": (
            f"At the default weekly capacity of {capacity}, the best synthetic policy row selects {int(policy['selected_count'])} "
            f"appointments with precision {policy['precision']:.1%}, recall {policy['recall']:.1%}, funding-route selection gap "
            f"{policy['funding_route_selection_gap']:.1%} and service-group gap {policy['service_group_selection_gap']:.1%}. "
            f"{insufficient + review} subgroup rows are not fully reliable, so parity or safety claims are not ready."
        ),
        "production_ml_and_monitoring": (
            f"The run is reproducible through manifest {summary.get('run_id', 'not available')} and currently has {incidents} "
            f"open/triage synthetic incidents. The champion remains {champion['model']}; production readiness additionally "
            "requires monitored latency, training-serving reconciliation, rollback testing and named response owners."
        ),
        "privacy_security_and_information_governance": (
            f"The synthetic build records {len(data_lineage)} lineage links and restricts the patient-level API to declared "
            "operational roles with a minimised response schema. This demonstrates least privilege, but real use still requires "
            "managed identity, database permissions, DPIA/IG review, retention controls and immutable audit logging."
        ),
        "product_economics_and_implementation": (
            f"Under the synthetic £10,000 planning budget the selected grid plan adds {int(budget['extra_assessment_minutes_per_week'])} "
            f"assessment minutes per week and {int(budget['outreach_contacts_per_week'])} outreach contacts; "
            f"{queue_best['policy']} minimises maximum remaining wait among the tested queue policies. These are conditional "
            "scenario results, not realised savings or impact."
        ),
    }
    answers: dict[str, str] = {}
    for item in _items(config_root):
        answers[str(item["answer_key"])] = base[str(item["category"])]
    return answers
