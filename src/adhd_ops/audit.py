from __future__ import annotations

import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

import pandas as pd


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def create_run_context(root: Path, seed: int, config_paths: list[Path]) -> dict[str, Any]:
    try:
        package_version = version("adhd-ds")
    except PackageNotFoundError:
        package_version = "development"
    return {
        "run_id": f"RUN-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}",
        "started_at_utc": utc_now(),
        "package_version": package_version,
        "git_sha": os.getenv("GITHUB_SHA") or os.getenv("GIT_COMMIT") or "local-unavailable",
        "synthetic_seed": int(seed),
        "config_files": {str(path.relative_to(root)): sha256_file(path) for path in config_paths},
        "synthetic": True,
    }


def build_data_lineage() -> pd.DataFrame:
    rows = [
        ("referrals", "patient_pathway", "stage_summary; waiting_summary; action_queue"),
        ("appointments", "attendance_scored_test", "appointment_support_queue; calibration; model_registry"),
        ("clinician_capacity", "capacity_scenarios", "resource_optimisation; budget_recommendations"),
        ("communications", "attendance_features", "appointment_support_model"),
        ("all source tables", "contract and quality gates", "publication decision"),
        ("all analytical products", "dashboard payload", "interactive operating workspace and API"),
    ]
    return pd.DataFrame(rows, columns=["source", "transformation", "downstream_products"]).assign(synthetic=True)


def build_incident_register(
    service_levels: pd.DataFrame,
    weekly_anomalies: pd.DataFrame,
    contract_status: pd.DataFrame,
    validation: pd.DataFrame,
    run_id: str,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    detected_at = utc_now()
    for row in service_levels[service_levels["status"].eq("red")].itertuples():
        rows.append({"incident_id": f"INC-SLO-{row.control_id}", "severity": "high", "signal_type": "service_control", "signal": row.control, "owner_role": row.owner_role, "playbook": row.response, "rollback_trigger": "Suspend automated publication or decision use if the control reflects invalid data.", "status": "open", "detected_at_utc": detected_at, "run_id": run_id, "synthetic": True})
    for index, row in weekly_anomalies[weekly_anomalies["status"].eq("red")].tail(5).reset_index(drop=True).iterrows():
        rows.append({"incident_id": f"INC-ANOM-{index+1:03d}", "severity": "medium", "signal_type": "weekly_anomaly", "signal": f"{row['series']} {row['direction']} expected", "owner_role": "Operations analytics", "playbook": "Reconcile source refresh, duplicates, policy changes and operational events before assigning cause.", "rollback_trigger": "Remove the affected period from automated decisions if source reconciliation fails.", "status": "triage", "detected_at_utc": detected_at, "run_id": run_id, "synthetic": True})
    contract_failures = int(contract_status["failure_count"].gt(0).sum())
    quality_failures = int(validation["failure_count"].gt(0).sum())
    if contract_failures or quality_failures:
        rows.append({"incident_id": "INC-DATA-001", "severity": "critical", "signal_type": "publication_gate", "signal": f"{contract_failures} contract and {quality_failures} quality failures", "owner_role": "Data engineering", "playbook": "Stop publication, identify the first failing source, correct or formally waive, then rerun from source ingestion.", "rollback_trigger": "Revert to the most recent manifest with passing gates.", "status": "open", "detected_at_utc": detected_at, "run_id": run_id, "synthetic": True})
    columns = ["incident_id", "severity", "signal_type", "signal", "owner_role", "playbook", "rollback_trigger", "status", "detected_at_utc", "run_id", "synthetic"]
    return pd.DataFrame(rows, columns=columns)


def finalise_manifest(
    root: Path,
    context: dict[str, Any],
    source_profiles: pd.DataFrame,
    contract_status: pd.DataFrame,
    validation: pd.DataFrame,
    output_paths: list[Path],
) -> dict[str, Any]:
    output_hashes = {}
    for path in output_paths:
        if path.exists() and path.is_file():
            output_hashes[str(path.relative_to(root))] = sha256_file(path)
    manifest = {
        **context,
        "completed_at_utc": utc_now(),
        "contract_gate": "pass" if not contract_status["failure_count"].gt(0).any() else "fail",
        "quality_gate": "pass" if not validation["failure_count"].gt(0).any() else "fail",
        "source_profiles": source_profiles.to_dict(orient="records"),
        "output_sha256": output_hashes,
        "replay_command": "python -m adhd_ops.pipeline --root .",
    }
    (root / "results/run_manifest.json").write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    return manifest
