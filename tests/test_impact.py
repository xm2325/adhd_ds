from pathlib import Path

import pandas as pd

from adhd_ops.config import load_yaml
from adhd_ops.impact import build_outreach_impact, build_scenario_impact

ROOT = Path(__file__).resolve().parents[1]


def test_scenario_impact_uses_declared_cost_proxies():
    capacity = pd.DataFrame([
        {"scenario": "baseline", "week_start": "2026-01-05", "available_minutes": 600, "backlog_patients": 100, "wait_days_proxy": 20},
        {"scenario": "extra", "week_start": "2026-01-05", "available_minutes": 660, "backlog_patients": 90, "wait_days_proxy": 18},
    ])
    result = build_scenario_impact(capacity, load_yaml(ROOT / "config/operations.yaml")).set_index("scenario")
    assert result.loc["extra", "backlog_patients_avoided"] == 10
    assert result.loc["extra", "horizon_cost_proxy_gbp"] > 0
    assert result["synthetic"].all()


def test_outreach_impact_is_capacity_limited():
    scored = pd.DataFrame({"predicted_dna_probability": [0.8, 0.6, 0.2]})
    result = build_outreach_impact(scored, load_yaml(ROOT / "config/operations.yaml"), capacities=(1, 2, 10))
    assert result["outreach_capacity"].tolist() == [1, 2, 3]
    assert result["expected_dna_without_support"].is_monotonic_increasing
