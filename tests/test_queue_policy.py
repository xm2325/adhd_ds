from adhd_ops.config import load_yaml
from adhd_ops.queue_policy import simulate_queue_policies
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_queue_policy_uses_same_declared_capacity(pathway):
    comparison, assignments = simulate_queue_policies(
        pathway["patient_pathway"], load_yaml(ROOT / "config/operations.yaml")
    )
    assert comparison["selected_count"].nunique() == 1
    assert comparison["selected_count"].iloc[0] == 120
    assert set(comparison["policy"]) == {
        "oldest_first",
        "stage_readiness",
        "balanced_funding_route",
        "balanced_service_group",
    }
    assert assignments.groupby("policy")["rank"].max().eq(120).all()


def test_oldest_first_minimises_maximum_remaining_wait(pathway):
    comparison, _ = simulate_queue_policies(
        pathway["patient_pathway"], load_yaml(ROOT / "config/operations.yaml")
    )
    oldest = comparison.set_index("policy").loc["oldest_first", "max_wait_remaining"]
    assert oldest <= comparison["max_wait_remaining"].min() + 1e-9
