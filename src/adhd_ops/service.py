from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Annotated

import pandas as pd
from fastapi import FastAPI, Header, HTTPException, Query

PATIENT_LEVEL_ROLES = {"operations", "patient_support"}


def _records(path: Path) -> list[dict]:
    if not path.exists():
        return []
    frame = pd.read_csv(path)
    return frame.where(pd.notna(frame), None).to_dict(orient="records")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def create_app(root: str | Path | None = None) -> FastAPI:
    project_root = Path(root or os.getenv("ADHD_DS_ROOT", ".")).resolve()
    results = project_root / "results"
    app = FastAPI(title="ADHD DS synthetic operations API", version="0.8.0")

    @app.get("/health")
    def health() -> dict:
        manifest = _read_json(results / "run_manifest.json")
        return {"status": "ok" if manifest else "not_built", "synthetic": True, "run_id": manifest.get("run_id"), "contract_gate": manifest.get("contract_gate"), "quality_gate": manifest.get("quality_gate")}

    @app.get("/v1/summary")
    def summary() -> dict:
        payload = _read_json(results / "run_summary.json")
        if not payload:
            raise HTTPException(status_code=503, detail="Pipeline outputs are not available")
        return payload

    @app.get("/v1/contracts")
    def contracts() -> list[dict]:
        return _records(results / "data_contract_status.csv")

    @app.get("/v1/service-levels")
    def service_levels() -> list[dict]:
        return _records(results / "service_level_status.csv")

    @app.get("/v1/actions")
    def actions(status: str | None = None) -> list[dict]:
        rows = _records(results / "operational_action_queue.csv")
        return [row for row in rows if status is None or row.get("status") == status]

    @app.get("/v1/budget-recommendation")
    def budget_recommendation(budget_gbp: float = Query(10000, ge=0)) -> dict:
        frame = pd.read_csv(results / "budget_recommendations.csv")
        eligible = frame[frame["budget_gbp"].le(budget_gbp)]
        row = (eligible.iloc[-1] if not eligible.empty else frame.iloc[0]).where(pd.notna, None)
        return row.to_dict()

    @app.get("/v1/queue-policies")
    def queue_policies() -> list[dict]:
        return _records(results / "queue_policy_comparison.csv")

    @app.get("/v1/ds-questions")
    def ds_questions(category: str | None = None) -> list[dict]:
        rows = _records(results / "ds_question_catalog.csv")
        return [row for row in rows if category is None or row.get("category") == category]

    @app.get("/v1/diagnostics/root-causes")
    def diagnostic_root_causes() -> list[dict]:
        return _records(results / "root_cause_scorecard.csv")

    @app.get("/v1/diagnostics/threshold-policy")
    def diagnostic_threshold_policy(
        weekly_capacity: int | None = Query(None, ge=1, le=500),
    ) -> list[dict]:
        rows = _records(results / "threshold_policy_grid.csv")
        return [
            row for row in rows
            if weekly_capacity is None or int(row.get("weekly_capacity", -1)) == weekly_capacity
        ]

    @app.get("/v1/diagnostics/metric-sensitivity")
    def diagnostic_metric_sensitivity() -> list[dict]:
        return _records(results / "metric_definition_sensitivity.csv")

    @app.get("/v1/evidence")
    def evidence_registry(topic: str | None = None) -> list[dict]:
        rows = _records(results / "evidence_registry.csv")
        return [row for row in rows if topic is None or topic in str(row.get("topics", ""))]

    @app.get("/v1/evidence/coverage")
    def evidence_coverage() -> list[dict]:
        return _records(results / "evidence_coverage.csv")

    @app.get("/v1/evidence/gaps")
    def evidence_gaps(claim_type: str | None = None) -> list[dict]:
        rows = _records(results / "evidence_gap_register.csv")
        return [row for row in rows if claim_type is None or row.get("claim_type") == claim_type]

    @app.get("/v1/statistics/kpi-uncertainty")
    def kpi_uncertainty() -> list[dict]:
        return _records(results / "kpi_uncertainty.csv")

    @app.get("/v1/statistics/subgroup-reliability")
    def subgroup_reliability(status: str | None = None) -> list[dict]:
        rows = _records(results / "subgroup_reliability.csv")
        return [row for row in rows if status is None or row.get("reliability_status") == status]

    @app.get("/v1/resilience/incidents")
    def resilience_incidents(severity: str | None = None) -> list[dict]:
        rows = _records(results / "incident_simulation_results.csv")
        return [row for row in rows if severity is None or row.get("severity") == severity]

    @app.get("/v1/resilience/stress-tests")
    def resilience_stress_tests(policy: str | None = None) -> list[dict]:
        rows = _records(results / "stress_test_summary.csv")
        return [row for row in rows if policy is None or row.get("policy") == policy]

    @app.get("/v1/resilience/early-warning")
    def resilience_early_warning(signal: str | None = None) -> list[dict]:
        rows = _records(results / "early_warning_signals.csv")
        return [row for row in rows if signal is None or row.get("signal") == signal]

    @app.get("/v1/resilience/scorecard")
    def resilience_scorecard(status: str | None = None) -> list[dict]:
        rows = _records(results / "resilience_scorecard.csv")
        return [row for row in rows if status is None or row.get("status") == status]

    @app.get("/v1/appointment-support")
    def appointment_support(
        x_role: Annotated[str, Header(alias="X-Role")] = "executive",
        limit: int = Query(20, ge=1, le=200),
    ) -> list[dict]:
        if x_role not in PATIENT_LEVEL_ROLES:
            raise HTTPException(status_code=403, detail="Patient-level queue requires an authorised operational role")
        frame = pd.read_csv(results / "appointment_support_queue.csv").head(limit)
        allowed = ["appointment_id", "scheduled_start", "funding_route", "service_group", "appointment_type", "predicted_dna_probability", "support_priority_band", "recommended_action"]
        selected = frame[[column for column in allowed if column in frame.columns]]
        return selected.where(pd.notna(selected), None).to_dict(orient="records")

    @app.get("/v1/audit/manifest")
    def audit_manifest() -> dict:
        return _read_json(results / "run_manifest.json")

    @app.get("/v1/audit/incidents")
    def audit_incidents() -> list[dict]:
        return _records(results / "incident_register.csv")

    @app.get("/v1/audit/lineage")
    def audit_lineage() -> list[dict]:
        return _records(results / "data_lineage.csv")

    return app


app = create_app()


def main() -> None:
    import uvicorn

    uvicorn.run("adhd_ops.service:app", host="127.0.0.1", port=8000, reload=False)
