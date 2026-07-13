from __future__ import annotations

import pandas as pd


def build_operational_action_queue(
    patient_pathway: pd.DataFrame,
    capacity_scenarios: pd.DataFrame,
    validation: pd.DataFrame,
    operations_config: dict,
) -> pd.DataFrame:
    """Create a service-wide action queue from explicit synthetic thresholds.

    The output is a structured hand-off for an operations meeting. It does not
    prescribe clinical action and all thresholds come from ``config/operations.yaml``.
    """
    thresholds = operations_config["thresholds"]
    pathway = patient_pathway.copy()
    pathway["referral_received_at"] = pd.to_datetime(pathway["referral_received_at"], errors="coerce")
    pathway["assessment_completed_at"] = pd.to_datetime(pathway["assessment_completed_at"], errors="coerce")
    waits = (
        pathway["assessment_completed_at"] - pathway["referral_received_at"]
    ).dt.total_seconds() / 86400
    accepted = int(pathway["accepted_at"].notna().sum())
    completed = int(pathway["assessment_completed_at"].notna().sum())
    completion_rate = completed / max(accepted, 1)
    p90_wait = float(waits.quantile(0.9))
    baseline = (
        capacity_scenarios[capacity_scenarios["scenario"].eq("baseline")]
        .sort_values("week_start")
        .iloc[-1]
    )
    failed_errors = int(
        validation[
            validation["severity"].eq("error") & validation["failure_count"].gt(0)
        ].shape[0]
    )

    rows: list[dict] = []
    counter = 0

    def add(priority: str, signal: str, evidence: str, owner: str, decision: str, cadence: str, status: str = "open") -> None:
        nonlocal counter
        counter += 1
        rows.append(
            {
                "action_id": f"ACT-{counter:03d}",
                "priority": priority,
                "signal": signal,
                "evidence": evidence,
                "owner_role": owner,
                "decision_required": decision,
                "review_cadence": cadence,
                "status": status,
                "synthetic": True,
            }
        )

    if p90_wait > float(thresholds["p90_assessment_wait_days"]):
        add(
            "high",
            "p90_wait_above_portfolio_review_threshold",
            f"P90 referral-to-assessment wait is {p90_wait:.1f} days.",
            "Operations lead",
            "Confirm the metric threshold and assign review of the longest open cases.",
            "Weekly pathway review",
        )
    if float(baseline["backlog_patients"]) > float(thresholds["backlog_review_patients"]):
        add(
            "high",
            "baseline_backlog_above_portfolio_review_threshold",
            f"Synthetic baseline backlog ends at {baseline['backlog_patients']:.0f} patients.",
            "Clinical operations",
            "Compare clinic, demand and absence scenarios before roster approval.",
            "Weekly capacity review",
        )
    if completion_rate < float(thresholds["completed_per_accepted_review_rate"]):
        add(
            "medium",
            "completed_per_accepted_below_portfolio_review_rate",
            f"Completed assessments are {completion_rate:.1%} of accepted referrals.",
            "Pathway manager",
            "Separate booking, attendance and still-open cases before choosing an action.",
            "Daily operations huddle",
        )
    if failed_errors > int(thresholds["data_quality_error_tolerance"]):
        add(
            "high",
            "data_quality_gate_failed",
            f"{failed_errors} error-level rules failed.",
            "Data engineering",
            "Stop dashboard publication and correct or formally waive the failed rules.",
            "Every data refresh",
        )
    else:
        add(
            "recorded",
            "data_quality_gate_passed",
            "All automated error-level data checks passed.",
            "Data team",
            "Record the successful gate; metric ownership and source checks remain separate controls.",
            "Every data refresh",
            status="recorded",
        )
    return pd.DataFrame(rows)
