from __future__ import annotations

import pandas as pd


def simulate_capacity(
    tables: dict[str, pd.DataFrame],
    pathway: pd.DataFrame,
    forecast: pd.DataFrame,
    scenarios_config: dict,
    assessment_duration_minutes: float = 90,
) -> pd.DataFrame:
    referrals = tables["referrals"]
    appointments = tables["appointments"]
    capacity = tables["clinician_capacity"]
    accepted_rate = referrals["accepted_at"].notna().mean()
    completion_rate = pathway["assessment_completed_at"].notna().sum() / max(pathway["accepted_at"].notna().sum(), 1)
    eligible = appointments[
        appointments["appointment_type"].eq("assessment")
        & appointments["appointment_status"].isin(["attended", "did_not_attend"])
    ]
    dna_rate = eligible["appointment_status"].eq("did_not_attend").mean()
    backlog_start = int((pathway["accepted_at"].notna() & pathway["assessment_completed_at"].isna()).sum())
    observed_end = referrals["referral_received_at"].max()
    recent_capacity = capacity[
        (capacity["service_type"] == "assessment") & (capacity["week_start"] <= observed_end)
    ].sort_values("week_start").tail(12)
    base_capacity = float(recent_capacity["available_minutes"].mean())

    rows = []
    for scenario in scenarios_config["scenarios"]:
        backlog = float(backlog_start)
        for _, week in forecast.iterrows():
            expected_referrals = float(week["predicted_referrals"]) * float(scenario["demand_multiplier"])
            arrivals = expected_referrals * accepted_rate * completion_rate
            available = base_capacity * float(scenario["capacity_multiplier"]) + float(scenario["extra_assessment_minutes"])
            effective_dna = dna_rate * (1 - float(scenario["dna_relative_reduction"]))
            throughput = (available / assessment_duration_minutes) * (1 - effective_dna)
            backlog = max(0, backlog + arrivals - throughput)
            rows.append({
                "scenario": scenario["name"],
                "week_start": week["week_start"],
                "predicted_referrals": expected_referrals,
                "new_assessment_demand": arrivals,
                "available_minutes": available,
                "effective_throughput_patients": throughput,
                "backlog_patients": backlog,
                "wait_days_proxy": 7 * backlog / max(throughput, 1),
                "assumed_dna_rate": effective_dna,
            })
    return pd.DataFrame(rows)
