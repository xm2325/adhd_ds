from __future__ import annotations

from statistics import NormalDist

import numpy as np
import pandas as pd


def _two_proportion_sample_size(
    baseline_rate: float,
    treatment_rate: float,
    alpha: float,
    power: float,
) -> int:
    if not (0 < treatment_rate < 1 and 0 < baseline_rate < 1):
        raise ValueError("rates must be between zero and one")
    difference = abs(baseline_rate - treatment_rate)
    if difference == 0:
        return 0
    z_alpha = NormalDist().inv_cdf(1 - alpha / 2)
    z_power = NormalDist().inv_cdf(power)
    pooled = (baseline_rate + treatment_rate) / 2
    numerator = (
        z_alpha * np.sqrt(2 * pooled * (1 - pooled))
        + z_power
        * np.sqrt(
            baseline_rate * (1 - baseline_rate)
            + treatment_rate * (1 - treatment_rate)
        )
    ) ** 2
    return int(np.ceil(numerator / difference**2))


def build_experiment_design(
    scored_appointments: pd.DataFrame,
    operations_config: dict,
) -> pd.DataFrame:
    """Build sample-size scenarios for a reminder pilot.

    The calculation is a planning approximation for a two-arm comparison of
    proportions. It does not establish that the configured effect is achievable.
    """
    cfg = operations_config["experimentation"]
    baseline_rate = float(scored_appointments["observed_dna"].mean())
    weekly_capacity = max(int(cfg["weekly_recruitment_capacity"]), 1)
    rows = []
    for relative_reduction in cfg["relative_dna_reductions"]:
        treatment_rate = baseline_rate * (1 - float(relative_reduction))
        per_arm = _two_proportion_sample_size(
            baseline_rate,
            treatment_rate,
            float(cfg["alpha"]),
            float(cfg["power"]),
        )
        total = per_arm * 2
        rows.append(
            {
                "baseline_dna_rate": baseline_rate,
                "assumed_relative_reduction": float(relative_reduction),
                "assumed_treatment_dna_rate": treatment_rate,
                "absolute_reduction": baseline_rate - treatment_rate,
                "alpha": float(cfg["alpha"]),
                "power": float(cfg["power"]),
                "n_per_arm": per_arm,
                "total_sample_size": total,
                "weeks_at_recruitment_capacity": max(
                    int(cfg["minimum_pilot_weeks"]),
                    int(np.ceil(total / weekly_capacity)),
                ),
                "synthetic": True,
            }
        )
    return pd.DataFrame(rows)


def build_experiment_guardrails(operations_config: dict) -> pd.DataFrame:
    rows = []
    for guardrail in operations_config["experimentation"]["guardrails"]:
        rows.append(
            {
                "metric": guardrail["metric"],
                "direction": guardrail["direction"],
                "purpose": guardrail["purpose"],
                "decision_rule": "Define before pilot and review by subgroup where appropriate",
                "synthetic": True,
            }
        )
    return pd.DataFrame(rows)
