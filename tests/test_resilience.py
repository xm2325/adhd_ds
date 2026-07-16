import pandas as pd


def test_resilience_exercises_are_complete_and_human_gated(built_project):
    target, summary = built_project
    incidents = pd.read_csv(target / "results/incident_simulation_results.csv")
    scorecard = pd.read_csv(target / "results/resilience_scorecard.csv")
    evidence = pd.read_csv(target / "results/evidence_registry.csv")
    timeline = pd.read_csv(target / "results/incident_timeline.csv")

    assert len(incidents) == summary["incident_exercises"] == 12
    assert summary["p0_p1_incident_exercises"] >= 8
    assert incidents["detected"].all()
    assert incidents["human_approval_required"].all()
    assert incidents["rollback_or_fallback"].str.len().gt(20).all()
    assert incidents["evidence_boundary"].str.len().gt(30).all()
    assert incidents["evidence_source_ids"].str.contains(";").all()
    known_sources = set(evidence["id"])
    cited_sources = {source for value in incidents["evidence_source_ids"] for source in str(value).split(";")}
    assert cited_sources.issubset(known_sources)
    assert set(timeline["stage"]) == {"detected", "acknowledged", "contained", "target_resolved"}
    assert len(timeline) == 4 * len(incidents)
    assert scorecard["status"].eq("pass").all()
    assert summary["resilience_controls_passed"] == summary["resilience_controls_total"] == len(scorecard)


def test_stress_test_is_reproducible_and_exposes_tail_risk(built_project):
    target, summary = built_project
    stress = pd.read_csv(target / "results/stress_test_summary.csv")
    samples = pd.read_csv(target / "results/stress_test_samples.csv")

    assert len(stress) == 5
    assert len(samples) == 5 * summary["stress_test_simulations_per_policy"]
    assert summary["stress_test_simulations_per_policy"] == 1000
    assert stress["risk_rank"].tolist() == list(range(1, 6))
    assert (stress["cvar95_end_backlog"] >= stress["p90_end_backlog"]).all()
    assert stress["probability_backlog_red"].between(0, 1).all()
    no_action = stress.loc[stress["policy"].eq("no_action")].iloc[0]
    surge = stress.loc[stress["policy"].eq("surge_protocol")].iloc[0]
    assert surge["mean_end_backlog"] < no_action["mean_end_backlog"]
    assert surge["horizon_cost_proxy_gbp"] > no_action["horizon_cost_proxy_gbp"]


def test_early_warning_detects_injected_shift(built_project):
    target, _ = built_project
    warning = pd.read_csv(target / "results/early_warning_signals.csv")
    red = warning[warning["signal"].eq("red")]
    assert len(warning) == 12
    assert warning["injected_shift"].any()
    assert not red.empty
    assert int(red.iloc[0]["week_number"]) >= 5
    assert (red["ewma_referrals"] > red["upper_control_limit"]).all()
