import shutil
from pathlib import Path

from adhd_ops.attendance import CATEGORICAL, NUMERIC
from adhd_ops.capacity import simulate_capacity
from adhd_ops.config import load_yaml
from adhd_ops.forecasting import forecast_referrals
from adhd_ops.operations import build_operational_action_queue
from adhd_ops.pathway import analyse_pathway
from adhd_ops.pipeline import run
from adhd_ops.synthetic import generate_synthetic_data
from adhd_ops.validation import validate_tables

ROOT = Path(__file__).resolve().parents[1]


def test_generation_is_reproducible():
    config = load_yaml(ROOT / "config/synthetic_data.yaml")
    first = generate_synthetic_data(config)
    second = generate_synthetic_data(config)
    assert first["patients"].equals(second["patients"])
    assert first["appointments"].equals(second["appointments"])


def test_generated_data_passes_all_rules():
    tables = generate_synthetic_data(load_yaml(ROOT / "config/synthetic_data.yaml"))
    assert validate_tables(tables)["failure_count"].sum() == 0


def test_pathway_counts_are_monotone():
    tables = generate_synthetic_data(load_yaml(ROOT / "config/synthetic_data.yaml"))
    counts = analyse_pathway(tables)["stage_summary"]["patient_count"].tolist()
    assert all(first >= second for first, second in zip(counts, counts[1:]))


def test_no_post_appointment_features_are_used():
    forbidden = {"appointment_status", "cancelled_at", "cancellation_reason", "target_dna"}
    assert forbidden.isdisjoint(set(NUMERIC + CATEGORICAL))


def test_action_queue_uses_explicit_config():
    config = load_yaml(ROOT / "config/synthetic_data.yaml")
    tables = generate_synthetic_data(config)
    pathway = analyse_pathway(tables)
    forecast = forecast_referrals(tables["referrals"], int(config["forecast_horizon_weeks"]))
    capacity = simulate_capacity(
        tables,
        pathway["patient_pathway"],
        forecast["forecast"],
        load_yaml(ROOT / "config/scenarios.yaml"),
        float(config["assessment_duration_minutes"]),
    )
    queue = build_operational_action_queue(
        pathway["patient_pathway"],
        capacity,
        validate_tables(tables),
        load_yaml(ROOT / "config/operations.yaml"),
    )
    assert not queue.empty
    assert queue["synthetic"].all()
    assert set(queue["status"]).issubset({"open", "recorded"})
    assert "data_quality_gate_passed" in set(queue["signal"])


def test_full_pipeline_builds_interactive_workspace(tmp_path):
    shutil.copytree(ROOT / "config", tmp_path / "config")
    summary = run(tmp_path)
    dashboard = tmp_path / "reports" / "operations_dashboard.html"
    pages_version = tmp_path / "docs" / "index.html"
    action_queue = tmp_path / "results" / "operational_action_queue.csv"
    assert summary["synthetic_referrals"] > 1000
    assert dashboard.exists() and pages_version.exists() and action_queue.exists()
    html = dashboard.read_text(encoding="utf-8")
    for marker in [
        "Operations command centre",
        "Interactive scenario planner",
        "Appointment support workflow",
        "Data and model controls",
        "window.DASHBOARD_DATA=",
        "getElementById('planExtra')",
        "exportSupport",
    ]:
        assert marker in html
    assert "No real patient or company data are used" in html
