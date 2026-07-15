from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import pandas as pd

from adhd_ops.attendance import train_attendance_models
from adhd_ops.capacity import simulate_capacity
from adhd_ops.config import load_yaml
from adhd_ops.dashboard import build_dashboard
from adhd_ops.forecasting import forecast_referrals
from adhd_ops.control_tower import build_service_level_status, build_weekly_anomalies
from adhd_ops.experimentation import build_experiment_design, build_experiment_guardrails
from adhd_ops.optimisation import build_backlog_driver_decomposition, build_resource_optimisation
from adhd_ops.impact import build_outreach_impact, build_scenario_impact
from adhd_ops.monitoring import (
    build_attendance_monitoring,
    build_champion_challenger_monitoring,
    build_forecast_monitoring,
)
from adhd_ops.operations import append_monitoring_actions, build_operational_action_queue
from adhd_ops.pathway import analyse_pathway
from adhd_ops.synthetic import generate_synthetic_data
from adhd_ops.validation import assert_valid, validate_tables, write_validation_report


def _write_frames(frames: dict[str, pd.DataFrame], directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for name, frame in frames.items():
        frame.to_csv(directory / f"{name}.csv", index=False)


def run(root: str | Path) -> dict:
    root = Path(root).resolve()
    for directory in ["data/synthetic", "results", "models", "reports", "tableau/exports"]:
        (root / directory).mkdir(parents=True, exist_ok=True)

    config = load_yaml(root / "config/synthetic_data.yaml")
    scenarios = load_yaml(root / "config/scenarios.yaml")
    operations_config = load_yaml(root / "config/operations.yaml")
    tables = generate_synthetic_data(config, root / "data/synthetic")

    validation = validate_tables(tables)
    validation.to_csv(root / "results/data_quality_rules.csv", index=False)
    write_validation_report(validation, root / "reports/data_quality_report.html")
    assert_valid(validation)

    pathway = analyse_pathway(tables)
    _write_frames(pathway, root / "results")

    forecast = forecast_referrals(tables["referrals"], int(config["forecast_horizon_weeks"]))
    _write_frames(
        {name: frame for name, frame in forecast.items() if isinstance(frame, pd.DataFrame)},
        root / "results",
    )

    capacity = simulate_capacity(
        tables,
        pathway["patient_pathway"],
        forecast["forecast"],
        scenarios,
        float(config["assessment_duration_minutes"]),
    )
    capacity.to_csv(root / "results/capacity_scenarios.csv", index=False)

    action_queue = build_operational_action_queue(
        pathway["patient_pathway"], capacity, validation, operations_config
    )
    attendance = train_attendance_models(tables["appointments"], root / "models/attendance_model.joblib")
    attendance["metrics"].to_csv(root / "results/attendance_model_metrics.csv", index=False)
    attendance["support_queue"].to_csv(root / "results/appointment_support_queue.csv", index=False)
    attendance["calibration"].to_csv(root / "results/attendance_calibration.csv", index=False)
    attendance["subgroup_audit"].to_csv(root / "results/attendance_subgroup_audit.csv", index=False)
    attendance["scored_test"].to_csv(root / "results/attendance_scored_test.csv", index=False)
    attendance["scored_models"].to_csv(root / "results/attendance_scored_models.csv", index=False)
    attendance["model_registry"].to_csv(root / "results/model_registry.csv", index=False)

    scenario_impact = build_scenario_impact(capacity, operations_config)
    scenario_impact.to_csv(root / "results/scenario_impact.csv", index=False)
    outreach_impact = build_outreach_impact(attendance["scored_test"], operations_config)
    outreach_impact.to_csv(root / "results/outreach_impact.csv", index=False)
    attendance_monitoring = build_attendance_monitoring(attendance["scored_test"])
    attendance_monitoring.to_csv(root / "results/attendance_monitoring.csv", index=False)
    forecast_monitoring = build_forecast_monitoring(forecast["backtest"], forecast["weekly_actuals"])
    forecast_monitoring.to_csv(root / "results/forecast_monitoring.csv", index=False)
    champion_challenger = build_champion_challenger_monitoring(
        attendance["scored_models"], attendance["model_registry"], operations_config
    )
    champion_challenger.to_csv(root / "results/champion_challenger_monitoring.csv", index=False)
    resource_grid, budget_recommendations = build_resource_optimisation(
        capacity, operations_config, float(config["assessment_duration_minutes"])
    )
    resource_grid.to_csv(root / "results/resource_optimisation.csv", index=False)
    budget_recommendations.to_csv(root / "results/budget_recommendations.csv", index=False)
    backlog_drivers = build_backlog_driver_decomposition(capacity)
    backlog_drivers.to_csv(root / "results/backlog_driver_decomposition.csv", index=False)
    experiment_design = build_experiment_design(attendance["scored_test"], operations_config)
    experiment_design.to_csv(root / "results/experiment_design.csv", index=False)
    experiment_guardrails = build_experiment_guardrails(operations_config)
    experiment_guardrails.to_csv(root / "results/experiment_guardrails.csv", index=False)
    service_levels = build_service_level_status(
        pathway["patient_pathway"],
        capacity,
        validation,
        attendance_monitoring,
        forecast_monitoring,
        str(forecast["selected_model"]),
        operations_config,
    )
    service_levels.to_csv(root / "results/service_level_status.csv", index=False)
    weekly_anomalies = build_weekly_anomalies(
        forecast["weekly_actuals"], tables["appointments"], operations_config
    )
    weekly_anomalies.to_csv(root / "results/weekly_anomalies.csv", index=False)
    action_queue = append_monitoring_actions(
        action_queue,
        attendance_monitoring,
        forecast_monitoring,
        str(forecast["selected_model"]),
        operations_config,
    )
    action_queue.to_csv(root / "results/operational_action_queue.csv", index=False)

    dashboard_inputs = {
        "pathway": pathway["patient_pathway"],
        "appointments": tables["appointments"],
        "waiting_summary": pathway["waiting_summary"],
        "group_summary": pathway["group_summary"],
        "weekly_actuals": forecast["weekly_actuals"],
        "forecast": forecast["forecast"],
        "forecast_performance": forecast["performance"],
        "capacity_scenarios": capacity,
        "model_metrics": attendance["metrics"],
        "support_queue": attendance["support_queue"],
        "calibration": attendance["calibration"],
        "subgroup_audit": attendance["subgroup_audit"],
        "validation": validation,
        "assessment_duration_minutes": float(config["assessment_duration_minutes"]),
        "operations_config": operations_config,
        "action_queue": action_queue,
        "scenario_impact": scenario_impact,
        "outreach_impact": outreach_impact,
        "attendance_monitoring": attendance_monitoring,
        "forecast_monitoring": forecast_monitoring,
        "model_registry": attendance["model_registry"],
        "champion_challenger": champion_challenger,
        "resource_optimisation": resource_grid,
        "budget_recommendations": budget_recommendations,
        "backlog_drivers": backlog_drivers,
        "experiment_design": experiment_design,
        "experiment_guardrails": experiment_guardrails,
        "service_levels": service_levels,
        "weekly_anomalies": weekly_anomalies,
    }
    build_dashboard(
        **dashboard_inputs,
        output_path=root / "reports/operations_dashboard.html",
        plotly_mode="inline",
    )
    build_dashboard(
        **dashboard_inputs,
        output_path=root / "docs/index.html",
        plotly_mode="cdn",
    )
    shutil.copyfile(
        root / "reports/operations_dashboard.html",
        root / "reports/executive_dashboard.html",
    )

    for filename in [
        "stage_summary.csv",
        "waiting_summary.csv",
        "cohort_progression.csv",
        "group_summary.csv",
        "weekly_actuals.csv",
        "forecast.csv",
        "performance.csv",
        "capacity_scenarios.csv",
        "attendance_model_metrics.csv",
        "attendance_calibration.csv",
        "attendance_subgroup_audit.csv",
        "operational_action_queue.csv",
        "scenario_impact.csv",
        "outreach_impact.csv",
        "attendance_monitoring.csv",
        "forecast_monitoring.csv",
        "model_registry.csv",
        "champion_challenger_monitoring.csv",
        "resource_optimisation.csv",
        "budget_recommendations.csv",
        "backlog_driver_decomposition.csv",
        "experiment_design.csv",
        "experiment_guardrails.csv",
        "service_level_status.csv",
        "weekly_anomalies.csv",
    ]:
        shutil.copyfile(root / "results" / filename, root / "tableau/exports" / filename)

    wait = pathway["waiting_summary"].set_index("metric")
    baseline = capacity[capacity["scenario"].eq("baseline")].iloc[-1]
    best = attendance["metrics"].iloc[0]
    summary = {
        "synthetic_patients": int(len(tables["patients"])),
        "synthetic_referrals": int(len(tables["referrals"])),
        "synthetic_appointments": int(len(tables["appointments"])),
        "median_referral_to_assessment_days": round(float(wait.loc["referral_to_assessment_days", "median_days"]), 2),
        "p90_referral_to_assessment_days": round(float(wait.loc["referral_to_assessment_days", "p90_days"]), 2),
        "forecast_model": forecast["selected_model"],
        "baseline_backlog_end": round(float(baseline["backlog_patients"]), 1),
        "attendance_model": attendance["selected_model"],
        "attendance_pr_auc": round(float(best["pr_auc"]), 4),
        "attendance_brier": round(float(best["brier_score"]), 4),
        "open_actions": int(action_queue["status"].eq("open").sum()),
        "best_scenario": str(scenario_impact.sort_values("end_backlog").iloc[0]["scenario"]),
        "red_service_controls": int(service_levels["status"].eq("red").sum()),
        "anomaly_alerts": int(weekly_anomalies["status"].isin(["amber", "red"]).sum()),
        "pareto_resource_plans": int(resource_grid["pareto_efficient"].sum()),
        "experiment_default_total_n": int(
            experiment_design.iloc[(experiment_design["assumed_relative_reduction"] - float(operations_config["experimentation"]["default_relative_dna_reduction"])).abs().argsort()[:1]]["total_sample_size"].iloc[0]
        ),
    }
    (root / "results/run_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    budget_10k = budget_recommendations.iloc[(budget_recommendations["budget_gbp"] - 10000).abs().argsort()[:1]].iloc[0]
    default_experiment = experiment_design.iloc[(experiment_design["assumed_relative_reduction"] - float(operations_config["experimentation"]["default_relative_dna_reduction"])).abs().argsort()[:1]].iloc[0]

    brief = f"""# Weekly operational brief — synthetic demonstration

## Headline

Under the baseline synthetic scenario, assessment demand remains above effective throughput and the simulated backlog ends at **{summary['baseline_backlog_end']:.0f} patients** after the 12-week horizon.

## Evidence

The generated dataset contains **{summary['synthetic_referrals']:,} referrals** and **{summary['synthetic_appointments']:,} appointments**. Median referral-to-completed-assessment time is **{summary['median_referral_to_assessment_days']:.1f} days** and the 90th percentile is **{summary['p90_referral_to_assessment_days']:.1f} days**. The selected demand model is **{summary['forecast_model']}**.

The selected appointment-support model is **{summary['attendance_model']}**, with PR-AUC **{summary['attendance_pr_auc']:.3f}** and Brier score **{summary['attendance_brier']:.3f}** on a later-time test set.

The control tower contains **{summary['red_service_controls']} red service or analytical controls** and **{summary['anomaly_alerts']} amber/red weekly anomaly flags**. These flags indicate where investigation is required; they do not assign cause.

Within a synthetic **£10,000** 12-week planning budget, the enumerated recommendation is **{budget_10k['plan_id']}**: **{int(budget_10k['extra_assessment_minutes_per_week'])} extra assessment minutes per week** and **{int(budget_10k['outreach_contacts_per_week'])} outreach contacts per week**, ending at **{budget_10k['end_backlog']:.0f} backlog patients**.

## Operational meaning

The simulation indicates that reminders alone are unlikely to remove the assessment backlog when assessment capacity is below demand. Capacity action should be assessed before expanding model-led outreach.

## Recommendation

Compare the baseline with the stored alternatives and the budget-constrained Pareto frontier, confirm whether the synthetic resource assumptions are suitable for planning, and record the selected action, owner, due date and rationale in the decision register.

Do not treat the configured outreach effect as evidence. At the default assumed **{default_experiment['assumed_relative_reduction']:.0%} relative DNA reduction**, a conventional two-arm pilot would require about **{int(default_experiment['total_sample_size']):,} appointments** under the current sample-size approximation.

## Decision required

1. Confirm whether referral receipt or referral acceptance is the primary waiting-time start point.
2. Confirm whether an extra assessment clinic is feasible.
3. Confirm how many appointments can receive additional contact each week.

## Limitations

All data, parameters, and results are synthetic and must not be interpreted as estimates for a real provider.
"""
    (root / "reports/weekly_operational_brief.md").write_text(brief, encoding="utf-8")

    minimum_n = int(operations_config["thresholds"]["minimum_monitoring_n"])
    reliable_monitoring = attendance_monitoring[attendance_monitoring["n"].ge(minimum_n)].sort_values("monitoring_month")
    latest_attendance = reliable_monitoring.iloc[-1]
    selected_forecast_checks = forecast_monitoring[forecast_monitoring["model"].eq(str(forecast["selected_model"]))].sort_values("origin_week")
    latest_forecast = selected_forecast_checks.iloc[-1]
    impact_best = scenario_impact.sort_values("end_backlog").iloc[0]
    control_pack = f"""# Monthly control pack — synthetic demonstration

## Publication gate

All automated error-level data-quality rules passed. This confirms the generated tables satisfy the coded checks; it does not approve metric meaning or source completeness.

## Service pressure

- P90 referral-to-assessment time: **{summary['p90_referral_to_assessment_days']:.1f} days**.
- Baseline 12-week backlog: **{summary['baseline_backlog_end']:.0f} patients**.
- Lowest stored scenario backlog: **{impact_best['scenario'].replace('_', ' ')}**, ending at **{impact_best['end_backlog']:.0f} patients**.
- Scenario resource proxy over the horizon: **£{impact_best['horizon_cost_proxy_gbp']:,.0f}**.

## Appointment-model control

The latest reliable monitoring month is **{latest_attendance['monitoring_month']}** with **n={int(latest_attendance['n'])}**. The observed synthetic DNA rate is **{latest_attendance['observed_dna_rate']:.1%}**, mean predicted probability is **{latest_attendance['mean_predicted_probability']:.1%}**, and the absolute calibration gap is **{latest_attendance['absolute_calibration_gap']:.1%}**.

The configured review level is **{float(operations_config['thresholds']['attendance_calibration_gap']):.1%}**. Crossing this level creates an owned model-review action; it does not automatically retrain or suspend the model.

## Forecast control

The latest rolling-origin check for **{forecast['selected_model']}** has WAPE **{latest_forecast['wape']:.1%}** and under-forecast rate **{latest_forecast['underforecast_rate']:.1%}**. The configured WAPE review level is **{float(operations_config['thresholds']['forecast_wape_review']):.1%}**.

## Champion–challenger control

The registered champion is **{attendance['selected_model']}**. The current challenger promotion flag is **{bool(champion_challenger['challenger_promotion_candidate'].iloc[0])}** under the declared recent-Brier and PR-AUC guardrails. Promotion still requires review, reproducibility checks and workflow validation.

## Resource optimisation and pilot feasibility

The synthetic £10,000 budget recommendation is **{budget_10k['plan_id']}**, with **{int(budget_10k['extra_assessment_minutes_per_week'])} extra assessment minutes per week** and **{int(budget_10k['outreach_contacts_per_week'])} outreach contacts per week**. The default reminder-effect assumption would require **{int(default_experiment['total_sample_size']):,} appointments**, or **{int(default_experiment['weeks_at_recruitment_capacity'])} weeks** at the configured recruitment capacity. This indicates that a smaller pilot may estimate process feasibility but may be underpowered for the assumed outcome effect.

## Open controls

The action register contains **{int(action_queue['status'].eq('open').sum())} open actions** and **{int(action_queue['status'].eq('recorded').sum())} recorded control**. Owners, due dates and rationale should be maintained in an authenticated decision system in production.

## Boundary

All data, costs, effects, thresholds and outcomes are synthetic. The pack demonstrates a control process and does not state provider performance or intervention effectiveness.
"""
    (root / "reports/monthly_control_pack.md").write_text(control_pack, encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=Path.cwd())
    args = parser.parse_args()
    print(json.dumps(run(args.root), indent=2))


if __name__ == "__main__":
    main()
