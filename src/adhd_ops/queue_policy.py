from __future__ import annotations

import itertools

import numpy as np
import pandas as pd


def _current_stage(row: pd.Series) -> str:
    if pd.notna(row.get("assessment_completed_at")):
        return "assessment_completed"
    if row.get("appointment_status") == "attended":
        return "assessment_attended"
    if pd.notna(row.get("scheduled_start")):
        return "assessment_booked"
    if pd.notna(row.get("first_contact_at")):
        return "first_contact"
    if pd.notna(row.get("accepted_at")):
        return "referral_accepted"
    return "referral_received"


def _round_robin(groups: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    iterators = {key: iter(frame.to_dict("records")) for key, frame in groups.items()}
    for key in itertools.cycle(sorted(iterators)):
        if not iterators:
            break
        iterator = iterators.get(key)
        if iterator is None:
            continue
        try:
            rows.append(next(iterator))
        except StopIteration:
            del iterators[key]
    return pd.DataFrame(rows)


def simulate_queue_policies(patient_pathway: pd.DataFrame, operations_config: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    cfg = operations_config.get("queue_policy", {})
    capacity = int(cfg.get("weekly_capacity", 120))
    overdue_days = float(cfg.get("overdue_days", 90))
    pathway = patient_pathway.copy()
    for column in ["referral_received_at", "accepted_at", "first_contact_at", "scheduled_start", "assessment_completed_at"]:
        pathway[column] = pd.to_datetime(pathway[column], errors="coerce")
    observed_end = max(
        value for value in [pathway["referral_received_at"].max(), pathway["scheduled_start"].max(), pathway["assessment_completed_at"].max()] if pd.notna(value)
    )
    queue = pathway[pathway["accepted_at"].notna() & pathway["assessment_completed_at"].isna()].copy()
    queue["days_waiting"] = (observed_end - queue["referral_received_at"]).dt.total_seconds() / 86400
    queue["current_stage"] = queue.apply(_current_stage, axis=1)
    stage_weight = {"assessment_attended": 4, "assessment_booked": 3, "first_contact": 2, "referral_accepted": 1, "referral_received": 0}
    queue["readiness_score"] = queue["current_stage"].map(stage_weight).fillna(0) * 1000 + queue["days_waiting"]

    ordered: dict[str, pd.DataFrame] = {
        "oldest_first": queue.sort_values(["days_waiting", "referral_id"], ascending=[False, True]),
        "stage_readiness": queue.sort_values(["readiness_score", "days_waiting"], ascending=[False, False]),
        "balanced_funding_route": _round_robin({key: group.sort_values("days_waiting", ascending=False) for key, group in queue.groupby("funding_route")}),
        "balanced_service_group": _round_robin({key: group.sort_values("days_waiting", ascending=False) for key, group in queue.groupby("service_group")}),
    }
    comparisons, assignments = [], []
    for policy, ordered_queue in ordered.items():
        selected = ordered_queue.head(capacity).copy()
        remaining = ordered_queue.iloc[capacity:].copy()
        selected["policy"] = policy
        selected["rank"] = np.arange(1, len(selected) + 1)
        assignments.append(selected[["policy", "rank", "referral_id", "funding_route", "service_group", "current_stage", "days_waiting"]])
        group_rates = []
        for column in ["funding_route", "service_group"]:
            totals = queue[column].value_counts()
            picked = selected[column].value_counts()
            rates = (picked / totals).fillna(0)
            group_rates.append(float(rates.max() - rates.min()) if len(rates) > 1 else 0.0)
        comparisons.append(
            {
                "policy": policy,
                "weekly_capacity": capacity,
                "selected_count": int(len(selected)),
                "mean_wait_selected": float(selected["days_waiting"].mean()),
                "p90_wait_selected": float(selected["days_waiting"].quantile(0.9)),
                "overdue_cases_cleared": int(selected["days_waiting"].ge(overdue_days).sum()),
                "max_wait_remaining": float(remaining["days_waiting"].max()) if not remaining.empty else 0.0,
                "funding_route_selection_gap": group_rates[0],
                "service_group_selection_gap": group_rates[1],
                "synthetic": True,
            }
        )
    return pd.DataFrame(comparisons), pd.concat(assignments, ignore_index=True)
