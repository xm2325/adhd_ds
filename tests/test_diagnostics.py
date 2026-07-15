import numpy as np
import pandas as pd

from adhd_ops.diagnostics import (
    build_dna_change_decomposition,
    build_metric_definition_sensitivity,
    build_period_comparison,
    build_stage_duration_decomposition,
)


def test_period_comparison_uses_common_operating_coverage(tables, synthetic_config):
    result = build_period_comparison(
        tables,
        assessment_duration_minutes=float(synthetic_config["assessment_duration_minutes"]),
    )
    referral = result[result["metric"].eq("referrals_received")].iloc[0]
    assert referral["previous_value"] > 0
    assert referral["recent_value"] > 0
    assert pd.Timestamp(referral["previous_period_end"]) == pd.Timestamp(referral["recent_period_start"])


def test_stage_decomposition_and_metric_sensitivity(pathway):
    stages = build_stage_duration_decomposition(pathway["patient_pathway"])
    sensitivity = build_metric_definition_sensitivity(pathway["patient_pathway"])
    assert stages.iloc[0]["stage_key"] == "appointment_queue"
    assert np.isclose(stages["share_of_complete_pathway_mean"].sum(), 1.0, atol=1e-6)
    patient_wait = sensitivity[sensitivity["definition"].eq("patient_experience_wait")].iloc[0]
    accepted_wait = sensitivity[sensitivity["definition"].eq("accepted_pathway_wait")].iloc[0]
    assert patient_wait["median_days"] > accepted_wait["median_days"]


def test_dna_decomposition_reconciles_by_dimension(tables):
    result = build_dna_change_decomposition(tables["appointments"])
    for _, group in result.groupby("dimension"):
        assert np.isclose(group["total_contribution"].sum(), group["overall_change"].iloc[0], atol=1e-10)
        assert group["n_previous"].sum() > 0
        assert group["n_recent"].sum() > 0


def test_threshold_grid_respects_capacity(built_project):
    target, _ = built_project
    grid = pd.read_csv(target / "results/threshold_policy_grid.csv")
    assert grid["selected_count"].le(grid["weekly_capacity"]).all()
    assert grid["precision"].dropna().between(0, 1).all()
    assert grid["recall"].between(0, 1).all()
    assert grid["expected_appointments_recovered"].ge(0).all()
