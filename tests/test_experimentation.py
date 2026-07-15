from pathlib import Path

from adhd_ops.attendance import train_attendance_models
from adhd_ops.config import load_yaml
from adhd_ops.experimentation import build_experiment_design, build_experiment_guardrails

ROOT = Path(__file__).resolve().parents[1]


def test_larger_effect_requires_smaller_sample(tables):
    attendance = train_attendance_models(tables["appointments"])
    result = build_experiment_design(
        attendance["scored_test"], load_yaml(ROOT / "config/operations.yaml")
    ).sort_values("assumed_relative_reduction")
    assert result["total_sample_size"].is_monotonic_decreasing
    assert (result["total_sample_size"] > 0).all()


def test_experiment_guardrails_are_declared():
    result = build_experiment_guardrails(load_yaml(ROOT / "config/operations.yaml"))
    assert {"complaint_rate", "opt_out_rate"}.issubset(set(result["metric"]))
    assert result["synthetic"].all()
