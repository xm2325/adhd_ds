import json

import pandas as pd


def test_every_question_has_literature_and_data_support(built_project):
    target, summary = built_project
    catalog = pd.read_csv(target / "results/ds_question_catalog.csv")
    assert len(catalog) == 106
    assert summary["questions_with_literature_support"] == 106
    assert summary["questions_with_data_support"] == 106
    assert catalog["literature_source_count"].ge(1).all()
    assert catalog["available_data_outputs"].ge(1).all()
    assert catalog["evidence_boundary"].str.len().gt(20).all()
    assert catalog["decision_readiness"].notna().all()


def test_evidence_registry_and_external_data_are_valid(built_project):
    target, summary = built_project
    registry = pd.read_csv(target / "results/evidence_registry.csv")
    external = pd.read_csv(target / "results/external_data_registry.csv")
    coverage = pd.read_csv(target / "results/evidence_coverage.csv")
    assert len(registry) == summary["literature_sources"] == 35
    assert len(external) == summary["external_public_data_sources"] == 7
    assert registry["url"].str.startswith("http").all()
    assert registry["limitations"].str.len().gt(20).all()
    assert coverage["literature_coverage_rate"].eq(1).all()
    assert coverage["data_coverage_rate"].eq(1).all()


def test_uncertainty_and_subgroup_reliability_outputs(built_project):
    target, _ = built_project
    uncertainty = pd.read_csv(target / "results/kpi_uncertainty.csv")
    subgroups = pd.read_csv(target / "results/subgroup_reliability.csv")
    assert len(uncertainty) >= 5
    assert (uncertainty["lower_95"] <= uncertainty["estimate"]).all()
    assert (uncertainty["estimate"] <= uncertainty["upper_95"]).all()

    appointments = pd.read_csv(target / "data/synthetic/appointments.csv")
    eligible = appointments["appointment_status"].isin(["attended", "did_not_attend"])
    expected_events = int(appointments["appointment_status"].eq("did_not_attend").sum())
    expected_n = int(eligible.sum())
    dna_row = uncertainty.loc[uncertainty["metric"].eq("appointment_dna_rate")].iloc[0]
    assert int(dna_row["events"]) == expected_events
    assert int(dna_row["n"]) == expected_n
    assert abs(float(dna_row["estimate"]) - expected_events / expected_n) < 1e-12
    assert set(subgroups["reliability_status"]).issubset({"adequate", "review", "insufficient"})
    assert (subgroups["lower_95"] <= subgroups["observed_rate"]).all()
    assert (subgroups["observed_rate"] <= subgroups["upper_95"]).all()


def test_manifest_tracks_evidence_products(built_project):
    target, _ = built_project
    manifest = json.loads((target / "results/run_manifest.json").read_text())
    assert manifest["replay_command"] == "python -m adhd_ops.orchestrator --root ."
    outputs = " ".join(manifest["output_sha256"].keys())
    assert "evidence_registry.csv" in outputs
    assert "evidence_coverage.csv" in outputs
    assert "evidence_backed_ds_handbook.md" in outputs
