from __future__ import annotations
from pathlib import Path
from typing import Any
import pandas as pd
from adhd_ops.config import load_yaml
from adhd_ops.question_answer_context import build_answer_context
from adhd_ops.question_answers_data_and_metrics import build_answers as build_data_and_metrics_answers
from adhd_ops.question_answers_patient_pathway import build_answers as build_patient_pathway_answers
from adhd_ops.question_answers_appointment_and_model import build_answers as build_appointment_and_model_answers
from adhd_ops.question_answers_forecast_and_capacity import build_answers as build_forecast_and_capacity_answers
from adhd_ops.question_answers_experimentation import build_answers as build_experimentation_answers
from adhd_ops.question_answers_governance_and_communication import build_answers as build_governance_and_communication_answers
from adhd_ops.question_answers_extended import build_answers as build_extended_answers

def build_answer_map(*, summary: dict[str, Any], contract_status: pd.DataFrame, quality_status: pd.DataFrame, source_freshness: pd.DataFrame, missingness: pd.DataFrame, period_comparison: pd.DataFrame, stage_duration: pd.DataFrame, metric_sensitivity: pd.DataFrame, dna_decomposition: pd.DataFrame, threshold_grid: pd.DataFrame, feature_effects: pd.DataFrame, root_causes: pd.DataFrame, group_summary: pd.DataFrame, stage_summary: pd.DataFrame, queue_policy: pd.DataFrame, scenario_impact: pd.DataFrame, model_registry: pd.DataFrame, subgroup_audit: pd.DataFrame, attendance_monitoring: pd.DataFrame, champion_challenger: pd.DataFrame, forecast: pd.DataFrame, forecast_performance: pd.DataFrame, weekly_anomalies: pd.DataFrame, budget_recommendations: pd.DataFrame, experiment_design: pd.DataFrame, experiment_guardrails: pd.DataFrame, incident_register: pd.DataFrame, data_lineage: pd.DataFrame, operations_config: dict[str, Any], config_root: str | Path, kpi_uncertainty: pd.DataFrame, subgroup_reliability: pd.DataFrame) -> dict[str, str]:
    ctx = build_answer_context(summary=summary, contract_status=contract_status, quality_status=quality_status, source_freshness=source_freshness, missingness=missingness, period_comparison=period_comparison, stage_duration=stage_duration, metric_sensitivity=metric_sensitivity, dna_decomposition=dna_decomposition, threshold_grid=threshold_grid, feature_effects=feature_effects, root_causes=root_causes, group_summary=group_summary, stage_summary=stage_summary, queue_policy=queue_policy, scenario_impact=scenario_impact, model_registry=model_registry, subgroup_audit=subgroup_audit, attendance_monitoring=attendance_monitoring, champion_challenger=champion_challenger, forecast=forecast, forecast_performance=forecast_performance, weekly_anomalies=weekly_anomalies, budget_recommendations=budget_recommendations, experiment_design=experiment_design, experiment_guardrails=experiment_guardrails, incident_register=incident_register, data_lineage=data_lineage, operations_config=operations_config)
    answers = {}
    answers.update(build_data_and_metrics_answers(ctx))
    answers.update(build_patient_pathway_answers(ctx))
    answers.update(build_appointment_and_model_answers(ctx))
    answers.update(build_forecast_and_capacity_answers(ctx))
    answers.update(build_experimentation_answers(ctx))
    answers.update(build_governance_and_communication_answers(ctx))
    answers.update(build_extended_answers(
        config_root=config_root, summary=summary, kpi_uncertainty=kpi_uncertainty,
        subgroup_reliability=subgroup_reliability, period_comparison=period_comparison,
        experiment_design=experiment_design, model_registry=model_registry,
        attendance_monitoring=attendance_monitoring, threshold_grid=threshold_grid,
        queue_policy=queue_policy, incident_register=incident_register,
        data_lineage=data_lineage, budget_recommendations=budget_recommendations,
    ))
    return answers

def _load_question_items(config_path: str | Path) -> list[dict[str, Any]]:
    path = Path(config_path)
    config = load_yaml(path)
    if 'questions' in config:
        return list(config.get('questions', []))
    items: list[dict[str, Any]] = []
    for relative in config.get('includes', []):
        included = load_yaml(path.parent / relative)
        items.extend(included.get('questions', []))
    return items

def build_question_catalog(config_path: str | Path, answers: dict[str, str]) -> pd.DataFrame:
    rows = []
    for item in _load_question_items(config_path):
        row = dict(item)
        row['current_synthetic_answer'] = answers.get(str(item.get('answer_key')), 'No run-specific answer is available; use the documented method and inputs.')
        row['evidence_class'] = 'synthetic operational demonstration'
        rows.append(row)
    return pd.DataFrame(rows)

def write_casebook(question_catalog: pd.DataFrame, output_path: str | Path) -> None:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        '# Evidence-backed data scientist scenario casebook — synthetic ADHD service',
        '',
        '> Every numerical answer is generated from synthetic data. Literature supports methods and governance principles; it does not establish provider-specific effects.',
        '',
        '## How to use this casebook',
        '',
        'For each question, start with the decision, state the current evidence, explain the method, name assumptions and the risk if wrong, and finish with the next action. Descriptive, inferential, predictive, scenario, causal, safety and governance claims are kept separate.',
        '',
    ]
    for category, group in question_catalog.groupby('category', sort=False):
        lines.extend([f"## {category.replace('_', ' ').title()}", ''])
        for _, row in group.iterrows():
            lines.extend([
                f"### {row['id']} — {row['question']}", '',
                f"**Asked by:** {row['stakeholder']}", '',
                f"**Claim type:** {row.get('claim_type', 'descriptive')}", '',
                f"**Why it is asked:** {row['why_asked']}", '',
                f"**Current synthetic answer:** {row['current_synthetic_answer']}", '',
                f"**How to solve it:** {row['method']}", '',
                f"**Inputs:** {row['required_inputs']}", '',
                f"**Project data support:** {row.get('data_outputs', '')}", '',
                f"**Literature support:** {row.get('literature_support', '')}", '',
                f"**External public data support:** {row.get('external_data_support', '')}", '',
                f"**Evidence boundary:** {row.get('evidence_boundary', '')}", '',
                f"**Decision readiness:** {row.get('decision_readiness', '')}", '',
                f"**Output:** {row['deliverable']}", '',
                f"**Risk if wrong:** {row['risk_if_wrong']}", '',
                f"**Next action:** {row['next_action']}", '',
            ])
    output.write_text('\n'.join(lines), encoding='utf-8')
