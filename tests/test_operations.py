from pathlib import Path

from adhd_ops.config import load_yaml
from adhd_ops.operations import build_operational_action_queue

ROOT = Path(__file__).resolve().parents[1]


def test_action_queue_uses_explicit_config(pathway, capacity, validation):
    queue = build_operational_action_queue(
        pathway["patient_pathway"],
        capacity,
        validation,
        load_yaml(ROOT / "config/operations.yaml"),
    )
    assert not queue.empty
    assert queue["synthetic"].all()
    assert set(queue["status"]).issubset({"open", "recorded"})
    assert "data_quality_gate_passed" in set(queue["signal"])
    assert {"created_on", "due_on", "source_metric", "escalation_route"}.issubset(queue.columns)
