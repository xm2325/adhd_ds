from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from adhd_ops.diagnostics_common import PERIOD_WEEKS, _datetime, _selection_gap


def build_dna_change_decomposition(
    appointments: pd.DataFrame,
    *,
    period_weeks: int = PERIOD_WEEKS,
) -> pd.DataFrame:
    data = _datetime(appointments, ["booked_at", "scheduled_start"])
    data = data[data["appointment_status"].isin(["attended", "did_not_attend"])].copy()
    data["target_dna"] = data["appointment_status"].eq("did_not_attend").astype(int)
    data["lead_days"] = (data["scheduled_start"] - data["booked_at"]).dt.total_seconds() / 86400
    data["lead_time_band"] = pd.cut(
        data["lead_days"],
        [-np.inf, 7, 14, 28, 56, np.inf],
        labels=["≤7d", "8–14d", "15–28d", "29–56d", ">56d"],
    ).astype(str)
    data["day_of_week"] = data["scheduled_start"].dt.day_name()
    both = data["reminder_7d_delivered"].astype(bool) & data["reminder_1d_delivered"].astype(bool)
    only_7d = data["reminder_7d_delivered"].astype(bool) & ~data["reminder_1d_delivered"].astype(bool)
    only_1d = ~data["reminder_7d_delivered"].astype(bool) & data["reminder_1d_delivered"].astype(bool)
    data["reminder_pattern"] = np.select(
        [both, only_7d, only_1d], ["both", "7d_only", "1d_only"], default="none"
    )

    maximum = data["scheduled_start"].max() + pd.Timedelta(days=1)
    minimum_period_n = min(300, max(50, len(data) // 20))
    candidate_ends = pd.date_range(
        data["scheduled_start"].min() + pd.Timedelta(weeks=2 * period_weeks),
        maximum,
        freq="7D",
    )
    period_end = maximum
    for candidate in reversed(candidate_ends):
        recent_start_candidate = candidate - pd.Timedelta(weeks=period_weeks)
        previous_start_candidate = recent_start_candidate - pd.Timedelta(weeks=period_weeks)
        recent_n = int(data["scheduled_start"].between(recent_start_candidate, candidate, inclusive="left").sum())
        previous_n = int(data["scheduled_start"].between(previous_start_candidate, recent_start_candidate, inclusive="left").sum())
        if recent_n >= minimum_period_n and previous_n >= minimum_period_n:
            period_end = candidate
            break
    recent_start = period_end - pd.Timedelta(weeks=period_weeks)
    previous_start = recent_start - pd.Timedelta(weeks=period_weeks)
    previous = data[data["scheduled_start"].between(previous_start, recent_start, inclusive="left")].copy()
    recent = data[data["scheduled_start"].between(recent_start, period_end, inclusive="left")].copy()
    previous_overall = float(previous["target_dna"].mean())
    recent_overall = float(recent["target_dna"].mean())
    overall_change = recent_overall - previous_overall

    dimensions = [
        "appointment_type",
        "funding_route",
        "service_group",
        "lead_time_band",
        "reminder_pattern",
        "day_of_week",
    ]
    rows = []
    for dimension in dimensions:
        values = sorted(set(previous[dimension].dropna().astype(str)) | set(recent[dimension].dropna().astype(str)))
        for value in values:
            prev_group = previous[previous[dimension].astype(str).eq(value)]
            recent_group = recent[recent[dimension].astype(str).eq(value)]
            prev_share = len(prev_group) / max(len(previous), 1)
            recent_share = len(recent_group) / max(len(recent), 1)
            prev_rate = float(prev_group["target_dna"].mean()) if len(prev_group) else 0.0
            recent_rate = float(recent_group["target_dna"].mean()) if len(recent_group) else 0.0
            composition_effect = (recent_share - prev_share) * (prev_rate + recent_rate) / 2
            within_rate_effect = (recent_rate - prev_rate) * (prev_share + recent_share) / 2
            rows.append(
                {
                    "dimension": dimension,
                    "segment": value,
                    "n_previous": int(len(prev_group)),
                    "n_recent": int(len(recent_group)),
                    "share_previous": prev_share,
                    "share_recent": recent_share,
                    "dna_rate_previous": prev_rate,
                    "dna_rate_recent": recent_rate,
                    "composition_effect": composition_effect,
                    "within_segment_rate_effect": within_rate_effect,
                    "total_contribution": composition_effect + within_rate_effect,
                    "overall_dna_rate_previous": previous_overall,
                    "overall_dna_rate_recent": recent_overall,
                    "overall_change": overall_change,
                    "interpretation_boundary": "Observed rate decomposition; it does not identify a causal effect.",
                }
            )
    result = pd.DataFrame(rows)
    result["absolute_contribution"] = result["total_contribution"].abs()
    return result.sort_values("absolute_contribution", ascending=False).reset_index(drop=True)


def build_threshold_policy_grid(
    scored: pd.DataFrame,
    operations_config: dict[str, Any],
) -> pd.DataFrame:
    data = scored.copy().reset_index(drop=True)
    data["predicted_dna_probability"] = pd.to_numeric(data["predicted_dna_probability"], errors="coerce")
    data["observed_dna"] = pd.to_numeric(data["observed_dna"], errors="coerce").fillna(0).astype(int)
    data = data.sort_values("predicted_dna_probability", ascending=False)
    capacities = operations_config.get("appointment_support", {}).get(
        "policy_capacities", [25, 50, 100, 150, 200]
    )
    thresholds = operations_config.get("appointment_support", {}).get(
        "policy_thresholds", [0.05, 0.10, 0.15, 0.20, 0.25]
    )
    assumed_effect = float(
        operations_config.get("planning_cost_proxies", {}).get("outreach_relative_dna_reduction", 0.0)
    )
    total_dna = max(int(data["observed_dna"].sum()), 1)
    rows = []
    for capacity in capacities:
        for threshold in thresholds:
            eligible = data[data["predicted_dna_probability"].ge(float(threshold))]
            selected = eligible.head(int(capacity))
            selected_mask = pd.Series(False, index=data.index)
            selected_mask.loc[selected.index] = True
            observed = int(selected["observed_dna"].sum())
            expected_dna = float(selected["predicted_dna_probability"].sum())
            rows.append(
                {
                    "weekly_capacity": int(capacity),
                    "minimum_probability": float(threshold),
                    "eligible_count": int(len(eligible)),
                    "selected_count": int(len(selected)),
                    "observed_dna_selected": observed,
                    "precision": float(observed / len(selected)) if len(selected) else np.nan,
                    "recall": float(observed / total_dna),
                    "mean_predicted_probability": float(selected["predicted_dna_probability"].mean()) if len(selected) else np.nan,
                    "expected_dna_selected": expected_dna,
                    "expected_appointments_recovered": expected_dna * assumed_effect,
                    "funding_route_selection_gap": _selection_gap(data, selected_mask, "funding_route"),
                    "service_group_selection_gap": _selection_gap(data, selected_mask, "service_group"),
                    "interpretation_boundary": "Capacity and threshold trade-off on synthetic test data; not intervention effectiveness.",
                }
            )
    return pd.DataFrame(rows)


def build_model_feature_effects(model_path: str | Path) -> pd.DataFrame:
    model = joblib.load(model_path)
    preprocess = model.named_steps["preprocess"]
    estimator = model.named_steps["model"]
    names = preprocess.get_feature_names_out()
    if hasattr(estimator, "coef_"):
        values = np.asarray(estimator.coef_[0], dtype=float)
        method = "logistic_coefficient"
        direction = np.where(values >= 0, "higher_predicted_risk", "lower_predicted_risk")
    elif hasattr(estimator, "feature_importances_"):
        values = np.asarray(estimator.feature_importances_, dtype=float)
        method = "feature_importance"
        direction = np.repeat("importance_without_direction", len(values))
    else:
        return pd.DataFrame(columns=["feature", "value", "absolute_value", "direction", "method"])
    result = pd.DataFrame(
        {
            "feature": names,
            "value": values,
            "absolute_value": np.abs(values),
            "direction": direction,
            "method": method,
            "interpretation_boundary": "Predictive association in the fitted model; not a causal explanation of attendance.",
        }
    )
    return result.sort_values("absolute_value", ascending=False).reset_index(drop=True)
