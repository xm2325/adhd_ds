from __future__ import annotations

import pandas as pd


def build_operational_action_queue(
    patient_pathway: pd.DataFrame,
    capacity_scenarios: pd.DataFrame,
    validation: pd.DataFrame,
    operations_config: dict,
) -> pd.DataFrame:
    """Create a deterministic service-wide action register from explicit thresholds.

    The register supports an operating meeting. It does not prescribe clinical action.
    All thresholds, due-date rules and costs come from configuration.
    """
    thresholds = operations_config["thresholds"]
    due_days = operations_config["workflow"]["action_due_days"]
    pathway = patient_pathway.copy()
    for column in ["referral_received_at", "assessment_completed_at", "scheduled_start"]:
        pathway[column] = pd.to_datetime(pathway[column], errors="coerce")
    waits = (pathway["assessment_completed_at"] - pathway["referral_received_at"]).dt.total_seconds() / 86400
    accepted = int(pathway["accepted_at"].notna().sum())
    completed = int(pathway["assessment_completed_at"].notna().sum())
    completion_rate = completed / max(accepted, 1)
    p90_wait = float(waits.quantile(0.9))
    baseline = capacity_scenarios[capacity_scenarios["scenario"].eq("baseline")].sort_values("week_start").iloc[-1]
    failed_errors = int(validation[validation["severity"].eq("error") & validation["failure_count"].gt(0)].shape[0])
    anchor = max(
        timestamp for timestamp in [pathway["referral_received_at"].max(), pathway["scheduled_start"].max()] if pd.notna(timestamp)
    ).normalize()

    rows: list[dict] = []
    counter = 0

    def add(
        priority: str,
        signal: str,
        evidence: str,
        owner: str,
        decision: str,
        cadence: str,
        source_metric: str,
        escalation: str,
        status: str = "open",
    ) -> None:
        nonlocal counter
        counter += 1
        due_on = anchor + pd.Timedelta(days=int(due_days[priority]))
        rows.append({
            "action_id": f"ACT-{counter:03d}",
            "priority": priority,
            "signal": signal,
            "source_metric": source_metric,
            "evidence": evidence,
            "owner_role": owner,
            "decision_required": decision,
            "review_cadence": cadence,
            "created_on": anchor.date().isoformat(),
            "due_on": due_on.date().isoformat(),
            "sla_status": "recorded" if status == "recorded" else "due",
            "escalation_route": escalation,
            "status": status,
            "decision_note": "",
            "synthetic": True,
        })

    if p90_wait > float(thresholds["p90_assessment_wait_days"]):
        add("high", "p90_wait_above_portfolio_review_threshold", f"P90 referral-to-assessment wait is {p90_wait:.1f} days.", "Operations lead", "Confirm the metric threshold and assign review of the longest open cases.", "Weekly pathway review", "p90_referral_to_assessment_days", "Chief operating officer")
    if float(baseline["backlog_patients"]) > float(thresholds["backlog_review_patients"]):
        add("high", "baseline_backlog_above_portfolio_review_threshold", f"Synthetic baseline backlog ends at {baseline['backlog_patients']:.0f} patients.", "Clinical operations", "Compare clinic, demand and absence scenarios before roster approval.", "Weekly capacity review", "baseline_backlog_end", "Clinical director")
    if completion_rate < float(thresholds["completed_per_accepted_review_rate"]):
        add("medium", "completed_per_accepted_below_portfolio_review_rate", f"Completed assessments are {completion_rate:.1%} of accepted referrals.", "Pathway manager", "Separate booking, attendance and still-open cases before choosing an action.", "Daily operations huddle", "completed_per_accepted", "Operations lead")
    if failed_errors > int(thresholds["data_quality_error_tolerance"]):
        add("high", "data_quality_gate_failed", f"{failed_errors} error-level rules failed.", "Data engineering", "Stop dashboard publication and correct or formally waive the failed rules.", "Every data refresh", "error_level_quality_failures", "Head of data")
    else:
        add("recorded", "data_quality_gate_passed", "All automated error-level data checks passed.", "Data team", "Record the successful gate; metric ownership and source checks remain separate controls.", "Every data refresh", "error_level_quality_failures", "Head of data", status="recorded")
    return pd.DataFrame(rows)


def append_monitoring_actions(
    action_queue: pd.DataFrame,
    attendance_monitoring: pd.DataFrame,
    forecast_monitoring: pd.DataFrame,
    selected_forecast_model: str,
    operations_config: dict,
) -> pd.DataFrame:
    """Append model-control actions using declared review levels.

    Small monitoring groups are excluded from alert generation but remain visible
    in the monitoring table and chart.
    """
    rows = action_queue.copy()
    thresholds = operations_config["thresholds"]
    minimum_n = int(thresholds["minimum_monitoring_n"])
    anchor = pd.to_datetime(rows["created_on"].max())
    due_days = operations_config["workflow"]["action_due_days"]
    next_id = len(rows) + 1

    def append(
        priority: str,
        signal: str,
        source_metric: str,
        evidence: str,
        owner: str,
        decision: str,
        cadence: str,
        escalation: str,
    ) -> None:
        nonlocal rows, next_id
        due_on = anchor + pd.Timedelta(days=int(due_days[priority]))
        record = pd.DataFrame([{
            "action_id": f"ACT-{next_id:03d}",
            "priority": priority,
            "signal": signal,
            "source_metric": source_metric,
            "evidence": evidence,
            "owner_role": owner,
            "decision_required": decision,
            "review_cadence": cadence,
            "created_on": anchor.date().isoformat(),
            "due_on": due_on.date().isoformat(),
            "sla_status": "due",
            "escalation_route": escalation,
            "status": "open",
            "decision_note": "",
            "synthetic": True,
        }])
        rows = pd.concat([rows, record], ignore_index=True)
        next_id += 1

    reliable = attendance_monitoring[attendance_monitoring["n"].ge(minimum_n)]
    if not reliable.empty:
        latest = reliable.sort_values("monitoring_month").iloc[-1]
        gap = float(latest["absolute_calibration_gap"])
        if gap > float(thresholds["attendance_calibration_gap"]):
            append(
                "medium",
                "attendance_calibration_gap_above_review_level",
                "absolute_calibration_gap",
                f"Latest reliable synthetic month ({latest['monitoring_month']}, n={int(latest['n'])}) has an absolute calibration gap of {gap:.1%}.",
                "Model owner",
                "Review probability calibration, workflow changes and whether the model should be recalibrated or suspended.",
                "Monthly model review",
                "Head of data science",
            )

    selected = forecast_monitoring[forecast_monitoring["model"].eq(selected_forecast_model)]
    if not selected.empty:
        latest = selected.sort_values("origin_week").iloc[-1]
        wape = float(latest["wape"])
        if wape > float(thresholds["forecast_wape_review"]):
            append(
                "medium",
                "forecast_wape_above_review_level",
                "forecast_wape",
                f"Latest rolling-origin WAPE for {selected_forecast_model} is {wape:.1%}.",
                "Forecast owner",
                "Review recent demand shifts and decide whether to change the planning model or widen the planning interval.",
                "Weekly capacity review",
                "Head of data science",
            )
    return rows
