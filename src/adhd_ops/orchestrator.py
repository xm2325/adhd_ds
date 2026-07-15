from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import pandas as pd

from adhd_ops.audit import build_data_lineage, build_incident_register, create_run_context, finalise_manifest
from adhd_ops.audit_dashboard import augment_dashboard
from adhd_ops.config import load_yaml
from adhd_ops.contracts import assert_contracts, build_source_profiles, validate_data_contracts
from adhd_ops.pipeline import run as run_core
from adhd_ops.queue_policy import simulate_queue_policies
from adhd_ops.synthetic import generate_synthetic_data


def _append_once(path: Path, marker: str, content: str) -> None:
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    if marker not in existing:
        path.write_text(existing.rstrip() + "\n\n" + content.strip() + "\n", encoding="utf-8")


def run(root: str | Path) -> dict:
    root = Path(root).resolve()
    for directory in ["data/synthetic", "results", "reports", "tableau/exports"]:
        (root / directory).mkdir(parents=True, exist_ok=True)

    config_paths = [
        root / "config/synthetic_data.yaml",
        root / "config/scenarios.yaml",
        root / "config/operations.yaml",
        root / "config/data_contracts.yaml",
    ]
    synthetic_config = load_yaml(config_paths[0])
    operations_config = load_yaml(config_paths[2])
    contract_config = load_yaml(config_paths[3])
    run_context = create_run_context(root, int(synthetic_config["seed"]), config_paths)

    tables = generate_synthetic_data(synthetic_config, root / "data/synthetic")
    contract_status = validate_data_contracts(tables, contract_config)
    source_profiles = build_source_profiles(tables)
    contract_status.to_csv(root / "results/data_contract_status.csv", index=False)
    source_profiles.to_csv(root / "results/source_profiles.csv", index=False)
    assert_contracts(contract_status)

    summary = run_core(root)

    patient_pathway = pd.read_csv(root / "results/patient_pathway.csv")
    queue_comparison, queue_assignments = simulate_queue_policies(patient_pathway, operations_config)
    queue_comparison.to_csv(root / "results/queue_policy_comparison.csv", index=False)
    queue_assignments.to_csv(root / "results/queue_policy_assignments.csv", index=False)

    validation = pd.read_csv(root / "results/data_quality_rules.csv")
    service_levels = pd.read_csv(root / "results/service_level_status.csv")
    weekly_anomalies = pd.read_csv(root / "results/weekly_anomalies.csv")
    data_lineage = build_data_lineage()
    data_lineage.to_csv(root / "results/data_lineage.csv", index=False)
    incident_register = build_incident_register(
        service_levels, weekly_anomalies, contract_status, validation, run_context["run_id"]
    )
    incident_register.to_csv(root / "results/incident_register.csv", index=False)

    summary.update(
        {
            "run_id": run_context["run_id"],
            "contract_rules_passed": int(contract_status["failure_count"].eq(0).sum()),
            "contract_rules_failed": int(contract_status["failure_count"].gt(0).sum()),
            "open_incidents": int(incident_register["status"].isin(["open", "triage"]).sum()),
            "queue_policy_lowest_max_wait": str(
                queue_comparison.sort_values(["max_wait_remaining", "funding_route_selection_gap"]).iloc[0]["policy"]
            ),
        }
    )
    (root / "results/run_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    for filename in [
        "data_contract_status.csv",
        "source_profiles.csv",
        "queue_policy_comparison.csv",
        "queue_policy_assignments.csv",
        "incident_register.csv",
        "data_lineage.csv",
    ]:
        shutil.copyfile(root / "results" / filename, root / "tableau/exports" / filename)

    dashboard_kwargs = {
        "contract_status": contract_status,
        "source_profiles": source_profiles,
        "queue_policy_comparison": queue_comparison,
        "incident_register": incident_register,
        "data_lineage": data_lineage,
        "run_context": run_context,
    }
    for output in [
        root / "reports/operations_dashboard.html",
        root / "reports/executive_dashboard.html",
        root / "docs/index.html",
    ]:
        augment_dashboard(output, **dashboard_kwargs)

    _append_once(
        root / "reports/weekly_operational_brief.md",
        "## Audit and publication evidence",
        f"""## Audit and publication evidence

Run **{summary['run_id']}** passed **{summary['contract_rules_passed']} contract rules** before metric calculation. The run has **{summary['open_incidents']} open or triage incident records**. The queue-policy comparison identifies **{summary['queue_policy_lowest_max_wait'].replace('_', ' ')}** as the lowest maximum-remaining-wait policy in this synthetic queue; this is operational allocation, not clinical prioritisation.""",
    )
    _append_once(
        root / "reports/monthly_control_pack.md",
        "## Run manifest and replay",
        f"""## Run manifest and replay

Run **{summary['run_id']}** records configuration hashes, source fingerprints, output hashes and a replay command. The contract and coded quality gates passed. Incident records and queue-policy evidence are linked to the same run ID.""",
    )

    output_paths = sorted((root / "results").glob("*")) + sorted((root / "reports").glob("*")) + [root / "docs/index.html"]
    finalise_manifest(root, run_context, source_profiles, contract_status, validation, output_paths)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=Path.cwd())
    args = parser.parse_args()
    print(json.dumps(run(args.root), indent=2))


if __name__ == "__main__":
    main()
