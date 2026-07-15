import json
import pandas as pd


def test_manifest_and_incidents_link_to_run(built_project):
    target, summary = built_project
    manifest = json.loads((target / "results/run_manifest.json").read_text())
    incidents = pd.read_csv(target / "results/incident_register.csv")
    assert manifest["run_id"] == summary["run_id"]
    assert manifest["contract_gate"] == "pass"
    assert manifest["quality_gate"] == "pass"
    assert len(manifest["output_sha256"]) >= 20
    assert manifest["replay_command"] == "python -m adhd_ops.orchestrator --root ."
    assert incidents["run_id"].eq(summary["run_id"]).all()
