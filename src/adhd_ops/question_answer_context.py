from __future__ import annotations
from typing import Any
import numpy as np
import pandas as pd
from adhd_ops.question_casebook_helpers import _fmt, _pct, _row


def build_answer_context(*, summary: dict[str, Any], contract_status: pd.DataFrame, quality_status: pd.DataFrame, source_freshness: pd.DataFrame, missingness: pd.DataFrame, period_comparison: pd.DataFrame, stage_duration: pd.DataFrame, metric_sensitivity: pd.DataFrame, dna_decomposition: pd.DataFrame, threshold_grid: pd.DataFrame, feature_effects: pd.DataFrame, root_causes: pd.DataFrame, group_summary: pd.DataFrame, stage_summary: pd.DataFrame, queue_policy: pd.DataFrame, scenario_impact: pd.DataFrame, model_registry: pd.DataFrame, subgroup_audit: pd.DataFrame, attendance_monitoring: pd.DataFrame, champion_challenger: pd.DataFrame, forecast: pd.DataFrame, forecast_performance: pd.DataFrame, weekly_anomalies: pd.DataFrame, budget_recommendations: pd.DataFrame, experiment_design: pd.DataFrame, experiment_guardrails: pd.DataFrame, incident_register: pd.DataFrame, data_lineage: pd.DataFrame, operations_config: dict[str, Any]) -> dict[str, Any]:
    contract_failures = int(contract_status['failure_count'].gt(0).sum())
    quality_failures = int(quality_status['failure_count'].gt(0).sum())
    publication = 'pass' if contract_failures == 0 and quality_failures == 0 else 'block'
    wait_patient = _row(metric_sensitivity, 'definition', 'patient_experience_wait')
    wait_accepted = _row(metric_sensitivity, 'definition', 'accepted_pathway_wait')
    top_stage = stage_duration.iloc[0]
    top_group = group_summary.sort_values('p90_referral_to_assessment_days', ascending=False).iloc[0]
    top_root = root_causes.sort_values('signal_strength', key=lambda x: x.map({'strong_signal': 0, 'moderate_signal': 1, 'weak_or_no_signal': 2})).iloc[0]
    top_dna = dna_decomposition.iloc[0]
    overall_dna_previous = float(top_dna['overall_dna_rate_previous'])
    overall_dna_recent = float(top_dna['overall_dna_rate_recent'])
    top_feature = feature_effects.iloc[0] if len(feature_effects) else None
    best_model = model_registry.sort_values('selection_score', ascending=False).iloc[0]
    baseline_model = model_registry.sort_values('selection_score', ascending=False).iloc[-1]
    latest_monitoring = attendance_monitoring.sort_values('monitoring_month').iloc[-1]
    subgroup_gap = float(subgroup_audit['brier_score'].max() - subgroup_audit['brier_score'].min())
    default_capacity = int(operations_config['appointment_support']['default_weekly_outreach_capacity'])
    capacity_rows = threshold_grid[threshold_grid['weekly_capacity'].eq(default_capacity)].copy()
    feasible = capacity_rows[capacity_rows['funding_route_selection_gap'].le(0.15) & capacity_rows['service_group_selection_gap'].le(0.15)]
    threshold_choice = feasible.sort_values(['expected_appointments_recovered', 'precision'], ascending=False).iloc[0] if len(feasible) else capacity_rows.sort_values(['funding_route_selection_gap', 'service_group_selection_gap']).iloc[0]
    selected_forecast = str(forecast['selected_model'].iloc[0])
    selected_performance = forecast_performance[forecast_performance['model'].eq(selected_forecast)].iloc[0]
    forecast_total = float(forecast['predicted_referrals'].sum())
    forecast_low = float(forecast['p10_referrals'].sum())
    forecast_high = float(forecast['p90_referrals'].sum())
    anomaly_count = int(weekly_anomalies['status'].isin(['amber', 'red']).sum())
    budget_10k = budget_recommendations.iloc[(budget_recommendations['budget_gbp'] - 10000).abs().argsort()[:1]].iloc[0]
    baseline_scenario = scenario_impact[scenario_impact['scenario'].eq('baseline')].iloc[0]
    extra_clinic = scenario_impact[scenario_impact['scenario'].eq('add_one_assessment_clinic')].iloc[0]
    demand_up = scenario_impact[scenario_impact['scenario'].eq('demand_up_10pct')].iloc[0]
    absence = scenario_impact[scenario_impact['scenario'].eq('clinician_absence_10pct')].iloc[0]
    default_effect = float(operations_config['experimentation']['default_relative_dna_reduction'])
    pilot = experiment_design.iloc[(experiment_design['assumed_relative_reduction'] - default_effect).abs().argsort()[:1]].iloc[0]
    reliable_challenger = bool(champion_challenger['challenger_promotion_candidate'].any())
    stale_source = source_freshness.sort_values('coverage_lag_vs_referral_cutoff_days', ascending=False).iloc[0]
    unexpected_missing = missingness[missingness['status'].eq('fail')]
    expected_nullable = missingness[missingness['status'].eq('expected_nullable')].sort_values('missing_rate', ascending=False)
    action_open = int(summary.get('open_actions', 0))
    incidents_open = int(incident_register['status'].isin(['open', 'triage']).sum())
    period = period_comparison.set_index('metric')
    referrals_change = float(period.loc['referrals_received', 'relative_change'])
    capacity_change = float(period.loc['assessment_slot_equivalent', 'relative_change'])
    contact_change = float(period.loc['median_referral_to_contact_days', 'relative_change'])
    largest_period = period_comparison.assign(abs_rel=lambda x: x['relative_change'].abs()).sort_values('abs_rel', ascending=False).iloc[0]
    stages = stage_summary.set_index('stage')
    accepted = float(stages.loc['referral_accepted', 'patient_count'])
    completed = float(stages.loc['assessment_completed', 'patient_count'])
    completion = completed / max(accepted, 1)
    open_cases = int(float(stages.loc['referral_received', 'patient_count']) - float(stages.loc['treatment_started', 'patient_count']))
    nonnullable_missing_answer = 'No non-nullable contract field is missing in the current synthetic run.' if unexpected_missing.empty else f'{len(unexpected_missing)} non-nullable fields fail their missingness contract and publication should stop.'
    nullable_example = f"The highest structurally nullable field is {expected_nullable.iloc[0]['table']}.{expected_nullable.iloc[0]['column']} at {_pct(expected_nullable.iloc[0]['missing_rate'])}." if len(expected_nullable) else 'No nullable field profile is available.'
    top_stage_owner = {'referral_processing': 'referral operations', 'initial_contact': 'intake / patient support', 'booking_process': 'scheduling operations', 'appointment_queue': 'clinical operations and rostering', 'assessment_delivery': 'clinical delivery', 'treatment_transition': 'clinical pathway team'}.get(str(top_stage['stage_key']), 'pathway owner')
    context = locals()
    context.update({'_fmt': _fmt, '_pct': _pct, '_row': _row})
    return context
