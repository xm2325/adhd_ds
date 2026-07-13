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
from adhd_ops.operations import build_operational_action_queue
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
    action_queue.to_csv(root / "results/operational_action_queue.csv", index=False)

    attendance = train_attendance_models(tables["appointments"], root / "models/attendance_model.joblib")
    attendance["metrics"].to_csv(root / "results/attendance_model_metrics.csv", index=False)
    attendance["support_queue"].to_csv(root / "results/appointment_support_queue.csv", index=False)
    attendance["calibration"].to_csv(root / "results/attendance_calibration.csv", index=False)
    attendance["subgroup_audit"].to_csv(root / "results/attendance_subgroup_audit.csv", index=False)

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
    }
    (root / "results/run_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    brief = f"""# Weekly operational brief — synthetic demonstration

## Headline

Under the baseline synthetic scenario, assessment demand remains above effective throughput and the simulated backlog ends at **{summary['baseline_backlog_end']:.0f} patients** after the 12-week horizon.

## Evidence

The generated dataset contains **{summary['synthetic_referrals']:,} referrals** and **{summary['synthetic_appointments']:,} appointments**. Median referral-to-completed-assessment time is **{summary['median_referral_to_assessment_days']:.1f} days** and the 90th percentile is **{summary['p90_referral_to_assessment_days']:.1f} days**. The selected demand model is **{summary['forecast_model']}**.

The selected appointment-support model is **{summary['attendance_model']}**, with PR-AUC **{summary['attendance_pr_auc']:.3f}** and Brier score **{summary['attendance_brier']:.3f}** on a later-time test set.

## Operational meaning

The simulation indicates that reminders alone are unlikely to remove the assessment backlog when assessment capacity is below demand. Capacity action should be assessed before expanding model-led outreach.

## Recommendation

Compare the baseline with the extra-clinic scenario, confirm the operational cost of adding 540 assessment minutes per week, and agree the owner of the referral-to-assessment metric.

## Decision required

1. Confirm whether referral receipt or referral acceptance is the primary waiting-time start point.
2. Confirm whether an extra assessment clinic is feasible.
3. Confirm how many appointments can receive additional contact each week.

## Limitations

All data, parameters, and results are synthetic and must not be interpreted as estimates for a real provider.
"""
    (root / "reports/weekly_operational_brief.md").write_text(brief, encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=Path.cwd())
    args = parser.parse_args()
    print(json.dumps(run(args.root), indent=2))


if __name__ == "__main__":
    main()
