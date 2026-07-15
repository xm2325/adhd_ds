def test_full_pipeline(built_project):
    target, summary = built_project
    assert summary["synthetic_referrals"] > 1000
    assert summary["open_actions"] >= 1
    assert (target / "reports/executive_dashboard.html").exists()
    assert (target / "reports/monthly_control_pack.md").exists()
    assert (target / "results/scenario_impact.csv").exists()
    assert (target / "results/resource_optimisation.csv").exists()
    assert (target / "results/experiment_design.csv").exists()
    assert (target / "results/service_level_status.csv").exists()
    assert summary["pareto_resource_plans"] >= 1
