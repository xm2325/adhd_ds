from pathlib import Path

from adhd_ops.config import load_yaml
from adhd_ops.optimisation import (
    build_backlog_driver_decomposition,
    build_resource_optimisation,
)

ROOT = Path(__file__).resolve().parents[1]


def test_resource_optimisation_respects_budget_and_pareto(capacity, synthetic_config):
    grid, recommendations = build_resource_optimisation(
        capacity,
        load_yaml(ROOT / "config/operations.yaml"),
        float(synthetic_config["assessment_duration_minutes"]),
    )
    assert not grid.empty
    assert grid["pareto_efficient"].any()
    assert (recommendations["horizon_cost_proxy_gbp"] <= recommendations["budget_gbp"]).all()
    ordered = recommendations.sort_values("budget_gbp")
    assert ordered["end_backlog"].is_monotonic_decreasing


def test_backlog_driver_decomposition_has_both_directions(capacity):
    result = build_backlog_driver_decomposition(capacity)
    assert "reduces_backlog" in set(result["direction"])
    assert "increases_backlog" in set(result["direction"])
