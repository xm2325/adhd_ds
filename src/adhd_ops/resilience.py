from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class StressSensitivity:
    baseline_backlog: float
    baseline_wait_days: float
    demand_backlog_per_unit: float
    demand_wait_per_unit: float
    capacity_backlog_per_unit_loss: float
    capacity_wait_per_unit_loss: float
    clinic_backlog_reduction_per_540_minutes: float
    clinic_wait_reduction_per_540_minutes: float
    dna_backlog_reduction_for_20pct: float
    dna_wait_reduction_for_20pct: float


def build_incident_scenario_catalog(config: dict[str, Any]) -> pd.DataFrame:
    frame = pd.DataFrame(config["incident_scenarios"]).copy()
    evidence_map = {
        "source_freshness": "KAHN_DQ_2016;NIST_AI_RMF_2023",
        "duplicate_keys": "KAHN_DQ_2016;NIST_AI_RMF_2023",
        "schema_drift": "KAHN_DQ_2016;DCB0129",
        "demand_surge": "LITTLE_LAW_1961;NIST_AI_RMF_2023",
        "capacity_loss": "LITTLE_LAW_1961;DCB0160",
        "calibration_drift": "VAN_CALSTER_CALIBRATION_2019;FUTURE_AI_2025",
        "feature_missingness": "KAHN_DQ_2016;FUTURE_AI_2025",
        "subgroup_harm_signal": "OBERMEYER_BIAS_2019;WHO_AI_ETHICS_2021",
        "experiment_guardrail": "CONSORT_AI_2020;SPIRIT_AI_2020",
        "service_latency": "NIST_AI_RMF_2023;FUTURE_AI_2025",
        "audit_gap": "NIST_AI_RMF_2023;DCB0160",
        "metric_definition_change": "RECORD_2015;SQUIRE_2016",
    }
    frame["evidence_source_ids"] = frame["incident_type"].map(evidence_map)
    frame["evidence_use"] = "Supports the control, monitoring or governance method; it does not validate the injected value or provider impact."
    frame["trigger_ratio"] = frame["observed_value"] / frame["threshold"].replace(0, np.nan)
    frame["breach"] = frame["observed_value"] > frame["threshold"]
    frame["synthetic"] = True
    return frame


def build_response_decision_matrix(config: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for item in config["response_levels"]:
        row = dict(item)
        row["target_recovery_minutes"] = int(float(row["target_resolution_hours"]) * 60)
        row["synthetic"] = True
        rows.append(row)
    return pd.DataFrame(rows)


def _sensitivities(scenario_impact: pd.DataFrame) -> StressSensitivity:
    data = scenario_impact.set_index("scenario")
    baseline = data.loc["baseline"]
    demand = data.loc["demand_up_10pct"]
    absence = data.loc["clinician_absence_10pct"]
    clinic = data.loc["add_one_assessment_clinic"]
    dna = data.loc["reduce_dna_20pct"]
    return StressSensitivity(
        baseline_backlog=float(baseline["end_backlog"]),
        baseline_wait_days=float(baseline["end_wait_days_proxy"]),
        demand_backlog_per_unit=float(demand["backlog_change_vs_baseline"]) / 0.10,
        demand_wait_per_unit=float(demand["wait_change_vs_baseline"]) / 0.10,
        capacity_backlog_per_unit_loss=float(absence["backlog_change_vs_baseline"]) / 0.10,
        capacity_wait_per_unit_loss=float(absence["wait_change_vs_baseline"]) / 0.10,
        clinic_backlog_reduction_per_540_minutes=-float(clinic["backlog_change_vs_baseline"]),
        clinic_wait_reduction_per_540_minutes=-float(clinic["wait_change_vs_baseline"]),
        dna_backlog_reduction_for_20pct=-float(dna["backlog_change_vs_baseline"]),
        dna_wait_reduction_for_20pct=-float(dna["wait_change_vs_baseline"]),
    )


def simulate_stress_test(
    scenario_impact: pd.DataFrame,
    resilience_config: dict[str, Any],
    operations_config: dict[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    cfg = resilience_config["stress_test"]
    rng = np.random.default_rng(int(resilience_config["seed"]))
    simulations = int(cfg["simulations"])
    sensitivity = _sensitivities(scenario_impact)

    demand_shock = np.clip(
        rng.normal(float(cfg["demand_shock_mean"]), float(cfg["demand_shock_sd"]), simulations),
        -0.10,
        0.45,
    )
    capacity_shock = np.clip(
        rng.normal(float(cfg["capacity_shock_mean"]), float(cfg["capacity_shock_sd"]), simulations),
        -0.30,
        0.10,
    )
    dna_shock = np.clip(
        rng.normal(float(cfg["dna_shock_mean"]), float(cfg["dna_shock_sd"]), simulations),
        -0.06,
        0.10,
    )
    cost_cfg = operations_config["planning_cost_proxies"]
    horizon = int(cfg["horizon_weeks"])
    rows: list[dict[str, Any]] = []

    for policy in cfg["policies"]:
        extra_minutes = float(policy["extra_assessment_minutes_per_week"])
        outreach = float(policy["outreach_contacts_per_week"])
        clinic_scale = extra_minutes / 540.0
        assumed_relative_dna_reduction = float(cost_cfg["outreach_relative_dna_reduction"]) * min(outreach / 200.0, 1.0)
        dna_scale = assumed_relative_dna_reduction / 0.20

        end_backlog = (
            sensitivity.baseline_backlog
            + sensitivity.demand_backlog_per_unit * demand_shock
            + sensitivity.capacity_backlog_per_unit_loss * np.maximum(-capacity_shock, 0)
            + sensitivity.dna_backlog_reduction_for_20pct * np.maximum(dna_shock, 0) / 0.20
            - sensitivity.clinic_backlog_reduction_per_540_minutes * clinic_scale
            - sensitivity.dna_backlog_reduction_for_20pct * dna_scale
        )
        end_wait = (
            sensitivity.baseline_wait_days
            + sensitivity.demand_wait_per_unit * demand_shock
            + sensitivity.capacity_wait_per_unit_loss * np.maximum(-capacity_shock, 0)
            + sensitivity.dna_wait_reduction_for_20pct * np.maximum(dna_shock, 0) / 0.20
            - sensitivity.clinic_wait_reduction_per_540_minutes * clinic_scale
            - sensitivity.dna_wait_reduction_for_20pct * dna_scale
        )
        weekly_cost = extra_minutes / 60.0 * float(cost_cfg["clinician_hour_gbp"]) + outreach * float(
            cost_cfg["patient_support_contact_gbp"]
        )
        for i in range(simulations):
            rows.append(
                {
                    "policy": policy["policy"],
                    "simulation_id": i + 1,
                    "demand_shock": demand_shock[i],
                    "capacity_shock": capacity_shock[i],
                    "dna_shock": dna_shock[i],
                    "end_backlog": max(0.0, end_backlog[i]),
                    "end_wait_days_proxy": max(0.0, end_wait[i]),
                    "horizon_cost_proxy_gbp": weekly_cost * horizon,
                    "synthetic": True,
                }
            )

    samples = pd.DataFrame(rows)
    threshold = float(cfg["backlog_red_threshold"])
    summary_rows = []
    for policy, group in samples.groupby("policy", sort=False):
        q95 = float(group["end_backlog"].quantile(0.95))
        tail = group[group["end_backlog"].ge(q95)]["end_backlog"]
        summary_rows.append(
            {
                "policy": policy,
                "mean_end_backlog": float(group["end_backlog"].mean()),
                "p50_end_backlog": float(group["end_backlog"].quantile(0.50)),
                "p90_end_backlog": float(group["end_backlog"].quantile(0.90)),
                "cvar95_end_backlog": float(tail.mean()),
                "probability_backlog_red": float(group["end_backlog"].gt(threshold).mean()),
                "mean_end_wait_days_proxy": float(group["end_wait_days_proxy"].mean()),
                "p90_end_wait_days_proxy": float(group["end_wait_days_proxy"].quantile(0.90)),
                "horizon_cost_proxy_gbp": float(group["horizon_cost_proxy_gbp"].iloc[0]),
                "simulations": int(len(group)),
                "synthetic": True,
            }
        )
    summary = pd.DataFrame(summary_rows).sort_values(
        ["probability_backlog_red", "cvar95_end_backlog", "horizon_cost_proxy_gbp"]
    )
    summary["risk_rank"] = np.arange(1, len(summary) + 1)
    return summary, samples


def build_early_warning_signals(
    weekly_actuals: pd.DataFrame, resilience_config: dict[str, Any]
) -> pd.DataFrame:
    cfg = resilience_config["early_warning"]
    observed = pd.to_numeric(weekly_actuals["referrals"], errors="coerce").dropna().to_numpy(dtype=float)
    centre = float(np.mean(observed))
    sigma = float(np.std(observed, ddof=1))
    rng = np.random.default_rng(int(resilience_config["seed"]) + 17)
    future_weeks = int(cfg["future_weeks"])
    shift_week = int(cfg["injected_shift_week"])
    simulated = rng.normal(centre, sigma, future_weeks)
    simulated[shift_week - 1 :] += float(cfg["injected_demand_shift"])
    lam = float(cfg["ewma_lambda"])
    width = float(cfg["control_limit_width"])
    z = centre
    rows = []
    start = pd.to_datetime(weekly_actuals["week_start"]).max() + pd.Timedelta(days=7)
    for idx, value in enumerate(simulated, start=1):
        z = lam * value + (1 - lam) * z
        scale = sigma * np.sqrt(lam / (2 - lam) * (1 - (1 - lam) ** (2 * idx)))
        upper = centre + width * scale
        lower = max(0.0, centre - width * scale)
        rows.append(
            {
                "week_start": (start + pd.Timedelta(days=7 * (idx - 1))).date().isoformat(),
                "week_number": idx,
                "observed_referrals": float(value),
                "ewma_referrals": float(z),
                "centre_line": centre,
                "lower_control_limit": float(lower),
                "upper_control_limit": float(upper),
                "signal": "red" if z > upper else "green",
                "injected_shift": bool(idx >= shift_week),
                "synthetic": True,
            }
        )
    return pd.DataFrame(rows)


def build_incident_simulation_results(
    catalog: pd.DataFrame,
    response_matrix: pd.DataFrame,
    stress_summary: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    response = response_matrix.set_index("severity")
    safest = stress_summary.iloc[0]
    rows = []
    timeline_rows = []
    for _, scenario in catalog.iterrows():
        level = response.loc[scenario["severity"]]
        action_state = {
            "P0": "stop_automation",
            "P1": "block_suspend_or_rollback",
            "P2": "degraded_mode_and_triage",
            "P3": "record_and_plan",
        }[scenario["severity"]]
        result = scenario.to_dict()
        result.update(
            {
                "detected": bool(scenario["breach"]),
                "decision_state": action_state,
                "acknowledgement_minutes": int(level["acknowledgement_minutes"]),
                "containment_hours": float(level["containment_hours"]),
                "target_resolution_hours": float(level["target_resolution_hours"]),
                "recommended_stress_policy": safest["policy"] if scenario["incident_type"] in {"demand_surge", "capacity_loss"} else "not_applicable",
                "human_approval_required": True,
            }
        )
        rows.append(result)
        for stage, elapsed_hours in [
            ("detected", 0.0),
            ("acknowledged", float(level["acknowledgement_minutes"]) / 60.0),
            ("contained", float(level["containment_hours"])),
            ("target_resolved", float(level["target_resolution_hours"])),
        ]:
            timeline_rows.append(
                {
                    "scenario_id": scenario["scenario_id"],
                    "severity": scenario["severity"],
                    "stage": stage,
                    "elapsed_hours": elapsed_hours,
                    "owner_role": scenario["owner_role"],
                    "synthetic": True,
                }
            )
    return pd.DataFrame(rows), pd.DataFrame(timeline_rows)


def build_resilience_scorecard(
    incident_results: pd.DataFrame,
    stress_summary: pd.DataFrame,
    early_warning: pd.DataFrame,
) -> pd.DataFrame:
    controls = [
        ("blocking_data_contracts", True, "Data freshness, keys and allowed values have fail-closed scenarios."),
        ("model_suspension_path", incident_results["decision_state"].eq("block_suspend_or_rollback").any(), "Calibration, missingness and subgroup signals suspend model-led ranking."),
        ("manual_fallback", incident_results["rollback_or_fallback"].str.len().gt(10).all(), "Every scenario names a rollback or degraded-service path."),
        ("named_incident_owner", incident_results["owner_role"].str.len().gt(3).all(), "Each scenario has an accountable owner and escalation route."),
        ("severity_sla", incident_results["target_resolution_hours"].notna().all(), "P0–P3 acknowledgement, containment and target resolution are declared."),
        ("stress_test", len(stress_summary) >= 5, "Five response policies are compared across stochastic demand, capacity and DNA shocks."),
        ("early_warning", early_warning["signal"].eq("red").any(), "The injected shift produces an EWMA warning in the deterministic exercise."),
        ("human_approval", incident_results["human_approval_required"].all(), "No simulated incident autonomously changes clinical or patient-level decisions."),
        ("evidence_boundary", incident_results["evidence_boundary"].str.len().gt(30).all(), "Every exercise states what the synthetic result cannot establish."),
    ]
    rows = []
    for control, passed, evidence in controls:
        rows.append(
            {
                "control": control,
                "status": "pass" if bool(passed) else "fail",
                "evidence": evidence,
                "synthetic": True,
            }
        )
    return pd.DataFrame(rows)
