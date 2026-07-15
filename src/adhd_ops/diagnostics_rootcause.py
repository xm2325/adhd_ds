from __future__ import annotations

import numpy as np
import pandas as pd

from adhd_ops.diagnostics_common import PERIOD_WEEKS


def build_root_cause_scorecard(
    period_comparison: pd.DataFrame,
    stage_duration: pd.DataFrame,
    dna_decomposition: pd.DataFrame,
    contract_status: pd.DataFrame,
    quality_status: pd.DataFrame,
    capacity_scenarios: pd.DataFrame,
) -> pd.DataFrame:
    metric = period_comparison.set_index("metric")

    def values(name: str) -> tuple[float, float, float]:
        row = metric.loc[name]
        return float(row["previous_value"]), float(row["recent_value"]), float(row["relative_change"])

    referral_prev, referral_recent, referral_change = values("referrals_received")
    capacity_prev, capacity_recent, capacity_change = values("assessment_slot_equivalent")
    contact_prev, contact_recent, contact_change = values("median_referral_to_contact_days")
    dna_prev, dna_recent, dna_change = values("appointment_dna_rate")

    baseline = capacity_scenarios[capacity_scenarios["scenario"].eq("baseline")]
    backlog_end = float(baseline.sort_values("week_start").iloc[-1]["backlog_patients"]) if len(baseline) else np.nan
    top_stage = stage_duration.iloc[0]
    top_dna = dna_decomposition.iloc[0] if len(dna_decomposition) else None
    contract_failures = int(contract_status["failure_count"].gt(0).sum())
    quality_failures = int(quality_status["failure_count"].gt(0).sum())

    def strength(change: float, moderate: float, strong: float, reverse: bool = False) -> str:
        value = -change if reverse else change
        if value >= strong:
            return "strong_signal"
        if value >= moderate:
            return "moderate_signal"
        return "weak_or_no_signal"

    rows = [
        {
            "hypothesis": "demand_pressure",
            "signal_strength": strength(referral_change, 0.05, 0.10),
            "previous_value": referral_prev,
            "recent_value": referral_recent,
            "evidence": f"Referrals changed by {referral_change:.1%} between adjacent {PERIOD_WEEKS}-week periods.",
            "next_analysis": "Check referral source, funding route, service group and one-off ingestion changes.",
            "owner": "Operations analytics",
        },
        {
            "hypothesis": "capacity_pressure",
            "signal_strength": "strong_signal" if backlog_end > 1000 or capacity_change < -0.05 else ("moderate_signal" if backlog_end > 500 else "weak_or_no_signal"),
            "previous_value": capacity_prev,
            "recent_value": capacity_recent,
            "evidence": f"Assessment slot-equivalent capacity changed by {capacity_change:.1%}; baseline horizon backlog is {backlog_end:.0f}.",
            "next_analysis": "Validate roster assumptions, appointment duration, absence and effective throughput.",
            "owner": "Clinical operations",
        },
        {
            "hypothesis": "administrative_processing_delay",
            "signal_strength": strength(contact_change, 0.10, 0.25),
            "previous_value": contact_prev,
            "recent_value": contact_recent,
            "evidence": f"Median referral-to-contact time changed from {contact_prev:.1f} to {contact_recent:.1f} days.",
            "next_analysis": "Review referral completeness, hand-offs, duplicate records and staffing by intake day.",
            "owner": "Pathway manager",
        },
        {
            "hypothesis": "appointment_attendance_loss",
            "signal_strength": strength(dna_change, 0.10, 0.25),
            "previous_value": dna_prev,
            "recent_value": dna_recent,
            "evidence": f"DNA rate changed from {dna_prev:.1%} to {dna_recent:.1%}; largest observed contribution is {top_dna['dimension']}={top_dna['segment']}" if top_dna is not None else f"DNA rate changed from {dna_prev:.1%} to {dna_recent:.1%}.",
            "next_analysis": "Separate case-mix change from within-segment rate change; test interventions before claiming cause.",
            "owner": "Patient support and model owner",
        },
        {
            "hypothesis": "pathway_stage_bottleneck",
            "signal_strength": "strong_signal" if float(top_stage["share_of_complete_pathway_mean"]) >= 0.40 else "moderate_signal",
            "previous_value": np.nan,
            "recent_value": float(top_stage["share_of_complete_pathway_mean"]),
            "evidence": f"{top_stage['stage_label']} contributes {float(top_stage['share_of_complete_pathway_mean']):.1%} of mean complete-pathway time.",
            "next_analysis": "Validate event semantics, examine weekly queues and test feasible process or capacity changes.",
            "owner": "Operations and clinical service lead",
        },
        {
            "hypothesis": "data_reliability_issue",
            "signal_strength": "strong_signal" if contract_failures or quality_failures else "weak_or_no_signal",
            "previous_value": np.nan,
            "recent_value": float(contract_failures + quality_failures),
            "evidence": f"Contract failures={contract_failures}; coded quality failures={quality_failures}.",
            "next_analysis": "Stop publication for blocking failures; reconcile source, transformation and metric owner decisions.",
            "owner": "Data engineering and metric owner",
        },
    ]
    result = pd.DataFrame(rows)
    result["causal_status"] = "Diagnostic hypothesis only; further validation or experiment required."
    return result
