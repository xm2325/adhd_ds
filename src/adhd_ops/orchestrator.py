from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import pandas as pd

from adhd_ops.audit import build_data_lineage, build_incident_register, create_run_context, finalise_manifest
from adhd_ops.audit_dashboard import augment_dashboard
from adhd_ops.diagnostics import (
    build_dna_change_decomposition,
    build_metric_definition_sensitivity,
    build_missingness_audit,
    build_model_feature_effects,
    build_period_comparison,
    build_root_cause_scorecard,
    build_source_freshness,
    build_stage_duration_decomposition,
    build_threshold_policy_grid,
)
from adhd_ops.question_casebook import build_answer_map, build_question_catalog, write_casebook
from adhd_ops.scenario_dashboard import augment_scenario_dashboard
from adhd_ops.config import load_yaml
from adhd_ops.contracts import assert_contracts, build_source_profiles, validate_data_contracts
from adhd_ops.pipeline import run as run_core
from adhd_ops.queue_policy import simulate_queue_policies
from adhd_ops.synthetic import generate_synthetic_data


def _append_once(path: Path, marker: str, content: str) -> None:
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    if marker not in existing:
        path.write_text(existing.rstrip() + "\n\n" + content.strip() + "\n", encoding="utf-8")


def run(root: str | Path) -> dict:
    root = Path(root).resolve()
    for directory in ["data/synthetic", "results", "reports", "tableau/exports"]:
        (root / directory).mkdir(parents=True, exist_ok=True)

    config_paths = [
        root / "config/synthetic_data.yaml",
        root / "config/scenarios.yaml",
        root / "config/operations.yaml",
        root / "config/data_contracts.yaml",
        root / "config/ds_questions.yaml",
        *sorted((root / "config/ds_questions").glob("*.yaml")),
    ]
    synthetic_config = load_yaml(config_paths[0])
    operations_config = load_yaml(config_paths[2])
    contract_config = load_yaml(config_paths[3])
    run_context = create_run_context(root, int(synthetic_config["seed"]), config_paths)

    tables = generate_synthetic_data(synthetic_config, root / "data/synthetic")
    contract_status = validate_data_contracts(tables, contract_config)
    source_profiles = build_source_profiles(tables)
    contract_status.to_csv(root / "results/data_contract_status.csv", index=False)
    source_profiles.to_csv(root / "results/source_profiles.csv", index=False)
    assert_contracts(contract_status)

    summary = run_core(root)

    patient_pathway = pd.read_csv(root / "results/patient_pathway.csv")
    queue_comparison, queue_assignments = simulate_queue_policies(patient_pathway, operations_config)
    queue_comparison.to_csv(root / "results/queue_policy_comparison.csv", index=False)
    queue_assignments.to_csv(root / "results/queue_policy_assignments.csv", index=False)

    validation = pd.read_csv(root / "results/data_quality_rules.csv")
    service_levels = pd.read_csv(root / "results/service_level_status.csv")
    weekly_anomalies = pd.read_csv(root / "results/weekly_anomalies.csv")
    data_lineage = build_data_lineage()
    data_lineage.to_csv(root / "results/data_lineage.csv", index=False)
    incident_register = build_incident_register(
        service_levels, weekly_anomalies, contract_status, validation, run_context["run_id"]
    )
    incident_register.to_csv(root / "results/incident_register.csv", index=False)

    pathway = pd.read_csv(root / "results/patient_pathway.csv")
    stage_summary = pd.read_csv(root / "results/stage_summary.csv")
    group_summary = pd.read_csv(root / "results/group_summary.csv")
    scenario_impact = pd.read_csv(root / "results/scenario_impact.csv")
    capacity_scenarios = pd.read_csv(root / "results/capacity_scenarios.csv")
    scored_test = pd.read_csv(root / "results/attendance_scored_test.csv")
    model_registry = pd.read_csv(root / "results/model_registry.csv")
    subgroup_audit = pd.read_csv(root / "results/attendance_subgroup_audit.csv")
    attendance_monitoring = pd.read_csv(root / "results/attendance_monitoring.csv")
    champion_challenger = pd.read_csv(root / "results/champion_challenger_monitoring.csv")
    forecast_frame = pd.read_csv(root / "results/forecast.csv")
    forecast_performance = pd.read_csv(root / "results/performance.csv")
    budget_recommendations = pd.read_csv(root / "results/budget_recommendations.csv")
    experiment_design = pd.read_csv(root / "results/experiment_design.csv")
    experiment_guardrails = pd.read_csv(root / "results/experiment_guardrails.csv")
    action_queue = pd.read_csv(root / "results/operational_action_queue.csv")

    period_comparison = build_period_comparison(
        tables, assessment_duration_minutes=float(synthetic_config["assessment_duration_minutes"])
    )
    stage_duration = build_stage_duration_decomposition(pathway)
    metric_sensitivity = build_metric_definition_sensitivity(pathway)
    dna_decomposition = build_dna_change_decomposition(tables["appointments"])
    threshold_grid = build_threshold_policy_grid(scored_test, operations_config)
    feature_effects = build_model_feature_effects(root / "models/attendance_model.joblib")
    source_freshness = build_source_freshness(tables)
    missingness_audit = build_missingness_audit(tables, contract_config)
    root_causes = build_root_cause_scorecard(
        period_comparison,
        stage_duration,
        dna_decomposition,
        contract_status,
        validation,
        capacity_scenarios,
    )
    diagnostic_outputs = {
        "period_comparison": period_comparison,
        "stage_duration_decomposition": stage_duration,
        "metric_definition_sensitivity": metric_sensitivity,
        "dna_change_decomposition": dna_decomposition,
        "threshold_policy_grid": threshold_grid,
        "model_feature_effects": feature_effects,
        "source_freshness": source_freshness,
        "missingness_audit": missingness_audit,
        "root_cause_scorecard": root_causes,
    }
    for name, frame in diagnostic_outputs.items():
        frame.to_csv(root / f"results/{name}.csv", index=False)

    summary.update(
        {
            "run_id": run_context["run_id"],
            "contract_rules_passed": int(contract_status["failure_count"].eq(0).sum()),
            "contract_rules_failed": int(contract_status["failure_count"].gt(0).sum()),
            "open_incidents": int(incident_register["status"].isin(["open", "triage"]).sum()),
            "queue_policy_lowest_max_wait": str(
                queue_comparison.sort_values(["max_wait_remaining", "funding_route_selection_gap"]).iloc[0]["policy"]
            ),
        }
    )
    answers = build_answer_map(
        summary=summary,
        contract_status=contract_status,
        quality_status=validation,
        source_freshness=source_freshness,
        missingness=missingness_audit,
        period_comparison=period_comparison,
        stage_duration=stage_duration,
        metric_sensitivity=metric_sensitivity,
        dna_decomposition=dna_decomposition,
        threshold_grid=threshold_grid,
        feature_effects=feature_effects,
        root_causes=root_causes,
        group_summary=group_summary,
        stage_summary=stage_summary,
        queue_policy=queue_comparison,
        scenario_impact=scenario_impact,
        model_registry=model_registry,
        subgroup_audit=subgroup_audit,
        attendance_monitoring=attendance_monitoring,
        champion_challenger=champion_challenger,
        forecast=forecast_frame,
        forecast_performance=forecast_performance,
        weekly_anomalies=weekly_anomalies,
        budget_recommendations=budget_recommendations,
        experiment_design=experiment_design,
        experiment_guardrails=experiment_guardrails,
        incident_register=incident_register,
        data_lineage=data_lineage,
        operations_config=operations_config,
    )
    question_catalog = build_question_catalog(root / "config/ds_questions.yaml", answers)
    question_catalog.to_csv(root / "results/ds_question_catalog.csv", index=False)
    write_casebook(question_catalog, root / "reports/ds_question_casebook.md")

    summary.update(
        {
            "ds_questions_covered": int(len(question_catalog)),
            "strongest_diagnostic_signal": str(
                root_causes.sort_values(
                    "signal_strength",
                    key=lambda x: x.map({"strong_signal": 0, "moderate_signal": 1, "weak_or_no_signal": 2}),
                ).iloc[0]["hypothesis"]
            ),
            "largest_pathway_stage": str(stage_duration.iloc[0]["stage_key"]),
        }
    )
    (root / "results/run_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    for filename in [
        "data_contract_status.csv",
        "source_profiles.csv",
        "queue_policy_comparison.csv",
        "queue_policy_assignments.csv",
        "incident_register.csv",
        "data_lineage.csv",
        "period_comparison.csv",
        "stage_duration_decomposition.csv",
        "metric_definition_sensitivity.csv",
        "dna_change_decomposition.csv",
        "threshold_policy_grid.csv",
        "model_feature_effects.csv",
        "source_freshness.csv",
        "missingness_audit.csv",
        "root_cause_scorecard.csv",
        "ds_question_catalog.csv",
    ]:
        shutil.copyfile(root / "results" / filename, root / "tableau/exports" / filename)

    dashboard_kwargs = {
        "contract_status": contract_status,
        "source_profiles": source_profiles,
        "queue_policy_comparison": queue_comparison,
        "incident_register": incident_register,
        "data_lineage": data_lineage,
        "run_context": run_context,
    }
    for output in [
        root / "reports/operations_dashboard.html",
        root / "reports/executive_dashboard.html",
        root / "docs/index.html",
    ]:
        augment_dashboard(output, **dashboard_kwargs)
        augment_scenario_dashboard(
            output,
            questions=question_catalog,
            root_causes=root_causes,
            stage_duration=stage_duration,
            dna_decomposition=dna_decomposition,
            threshold_grid=threshold_grid,
            feature_effects=feature_effects,
            metric_sensitivity=metric_sensitivity,
            period_comparison=period_comparison,
            default_capacity=int(operations_config["appointment_support"]["default_weekly_outreach_capacity"]),
        )

    _append_once(
        root / "reports/weekly_operational_brief.md",
        "## Audit and publication evidence",
        f"""## Audit and publication evidence

Run **{summary['run_id']}** passed **{summary['contract_rules_passed']} contract rules** before metric calculation. The run has **{summary['open_incidents']} open or triage incident records**. The queue-policy comparison identifies **{summary['queue_policy_lowest_max_wait'].replace('_', ' ')}** as the lowest maximum-remaining-wait policy in this synthetic queue; this is operational allocation, not clinical prioritisation.""",
    )
    _append_once(
        root / "reports/monthly_control_pack.md",
        "## Run manifest and replay",
        f"""## Run manifest and replay

Run **{summary['run_id']}** records configuration hashes, source fingerprints, output hashes and a replay command. The contract and coded quality gates passed. Incident records and queue-policy evidence are linked to the same run ID.""",
    )
    _append_once(
        root / "reports/weekly_operational_brief.md",
        "## Data scientist scenario diagnosis",
        f"""## Data scientist scenario diagnosis

The v0.6 workbench covers **{summary['ds_questions_covered']} stakeholder questions**. The strongest current diagnostic signal is **{summary['strongest_diagnostic_signal'].replace('_', ' ')}**, while the largest descriptive pathway stage is **{summary['largest_pathway_stage'].replace('_', ' ')}**. These are triage findings rather than causal conclusions; the linked casebook states the method, inputs, failure mode and next action for every question.""",
    )
    _append_once(
        root / "reports/monthly_control_pack.md",
        "## Diagnostic and question coverage",
        f"""## Diagnostic and question coverage

The run generated a period comparison, pathway-stage decomposition, wait-definition sensitivity, DNA change decomposition, threshold/workload grid, predictive feature explanation and **{summary['ds_questions_covered']}** question-specific answers. Reviewers should preserve the distinction between descriptive, predictive, scenario and causal evidence.""",
    )

    output_paths = sorted((root / "results").glob("*")) + sorted((root / "reports").glob("*")) + [root / "docs/index.html"]
    finalise_manifest(root, run_context, source_profiles, contract_status, validation, output_paths)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=Path.cwd())
    args = parser.parse_args()
    print(json.dumps(run(args.root), indent=2))


if __name__ == "__main__":
    main()
