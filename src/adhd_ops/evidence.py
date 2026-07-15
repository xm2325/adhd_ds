from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from adhd_ops.config import load_yaml


CLAIM_READINESS = {
    "descriptive": ("descriptive_ready", "Validated definitions and uncertainty are still required."),
    "inferential": ("uncertainty_review", "Decision should consider interval width, multiplicity and assumptions."),
    "predictive": ("external_validation_required", "Prediction needs temporal/external validation, calibration and workflow testing."),
    "scenario": ("assumption_dependent", "Scenario results are conditional projections, not forecasts of realised policy impact."),
    "causal": ("causal_design_required", "Causal claim requires randomisation or a defensible identification strategy."),
    "safety": ("safety_review_required", "Clinical safety, human factors and subgroup evidence require accountable review."),
    "operational": ("production_controls_required", "Production use requires SLOs, monitoring, incident response and rollback."),
    "governance": ("governance_approval_required", "Information governance, security and clinical safety approval are required."),
    "decision": ("stage_gate_required", "Decision needs cost, adoption, safety, effect and implementation evidence."),
}


def load_evidence_registry(path: str | Path) -> list[dict[str, Any]]:
    return list(load_yaml(path).get("sources", []))


def _split_topics(value: Any) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, list):
        return {str(x) for x in value}
    return {x.strip() for x in str(value).split(",") if x.strip()}


def enrich_question_catalog(
    catalog: pd.DataFrame,
    *,
    registry_path: str | Path,
    policy_path: str | Path,
    external_registry_path: str | Path,
    root: str | Path,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    root = Path(root)
    sources = load_evidence_registry(registry_path)
    source_by_id = {str(x["id"]): x for x in sources}
    policy = load_yaml(policy_path)
    defaults = policy["category_defaults"]
    external_sources = list(load_yaml(external_registry_path).get("datasets", []))
    external_by_id = {str(x["id"]): x for x in external_sources}
    enriched_rows: list[dict[str, Any]] = []

    for _, raw in catalog.iterrows():
        row = raw.to_dict()
        category = str(row["category"])
        default = defaults[category]
        claim_type = str(row.get("claim_type") or default["claim_type"])
        topics = set(default.get("topics", [])) | _split_topics(row.get("evidence_topics"))
        explicit_ids = _split_topics(row.get("evidence_ids"))
        candidates = [s for s in sources if explicit_ids and s["id"] in explicit_ids]
        if not candidates:
            candidates = [s for s in sources if topics.intersection(set(s.get("topics", [])))]
        candidates = sorted(
            candidates,
            key=lambda s: (
                0 if s["source_type"] in {"official_guidance", "official_standard", "reporting_guideline"} else 1,
                -int(s["year"]),
                str(s["id"]),
            ),
        )[:6]
        evidence_ids = [str(s["id"]) for s in candidates]
        data_outputs = row.get("data_outputs") or default.get("data_outputs", [])
        if isinstance(data_outputs, str):
            data_outputs = [x.strip() for x in data_outputs.split(",") if x.strip()]
        availability = [bool((root / p).exists()) for p in data_outputs]
        external_ids = [str(x) for x in (row.get("external_data_ids") or default.get("external_data_ids", []))]
        external_rows = [external_by_id[x] for x in external_ids if x in external_by_id]
        readiness, boundary = CLAIM_READINESS.get(claim_type, CLAIM_READINESS["descriptive"])
        row.update({
            "claim_type": claim_type,
            "evidence_topics": "; ".join(sorted(topics)),
            "evidence_ids": "; ".join(evidence_ids),
            "literature_support": " | ".join(f"{s['id']}: {s['title']} ({s['year']})" for s in candidates),
            "literature_urls": " | ".join(str(s["url"]) for s in candidates),
            "literature_source_count": len(candidates),
            "data_outputs": "; ".join(data_outputs),
            "available_data_outputs": int(sum(availability)),
            "required_data_outputs": len(data_outputs),
            "data_support_status": "available" if availability and all(availability) else "partial_or_missing",
            "external_data_ids": "; ".join(external_ids),
            "external_data_support": " | ".join(f"{x['id']}: {x['name']}" for x in external_rows),
            "external_data_urls": " | ".join(str(x["url"]) for x in external_rows),
            "decision_readiness": readiness,
            "evidence_boundary": boundary,
        })
        enriched_rows.append(row)

    enriched = pd.DataFrame(enriched_rows)
    coverage = (
        enriched.groupby("category", sort=False)
        .agg(
            questions=("id", "count"),
            questions_with_literature=("literature_source_count", lambda s: int((s >= 1).sum())),
            questions_with_data=("available_data_outputs", lambda s: int((s >= 1).sum())),
            mean_literature_sources=("literature_source_count", "mean"),
            mean_data_outputs=("available_data_outputs", "mean"),
        )
        .reset_index()
    )
    coverage["literature_coverage_rate"] = coverage["questions_with_literature"] / coverage["questions"]
    coverage["data_coverage_rate"] = coverage["questions_with_data"] / coverage["questions"]

    gap_rows = []
    for _, row in enriched.iterrows():
        if row["claim_type"] == "causal":
            gap = "Requires randomised or defensible quasi-experimental evidence before an intervention-effect claim."
        elif row["claim_type"] == "predictive":
            gap = "Requires temporal/external validation and prospective workflow evaluation before scaled use."
        elif row["claim_type"] in {"safety", "governance"}:
            gap = "Requires accountable clinical safety, information-governance or equality review."
        elif row["data_support_status"] != "available":
            gap = "One or more required project data products are unavailable in this build."
        else:
            gap = "No blocking evidence gap for synthetic descriptive demonstration; real provider validation remains required."
        gap_rows.append({
            "question_id": row["id"],
            "category": row["category"],
            "claim_type": row["claim_type"],
            "decision_readiness": row["decision_readiness"],
            "evidence_gap": gap,
            "next_action": row["next_action"],
        })
    gaps = pd.DataFrame(gap_rows)

    registry_frame = pd.DataFrame(sources)
    registry_frame["topics"] = registry_frame["topics"].map(lambda x: "; ".join(x))
    external_frame = pd.DataFrame(external_sources)
    return enriched, coverage, gaps, registry_frame, external_frame


def validate_evidence_coverage(catalog: pd.DataFrame, registry: pd.DataFrame) -> None:
    if catalog.empty:
        raise ValueError("Question catalog is empty")
    if (catalog["literature_source_count"] < 1).any():
        missing = catalog.loc[catalog["literature_source_count"] < 1, "id"].tolist()
        raise ValueError(f"Questions missing literature support: {missing}")
    if (catalog["available_data_outputs"] < 1).any():
        missing = catalog.loc[catalog["available_data_outputs"] < 1, "id"].tolist()
        raise ValueError(f"Questions missing project data support: {missing}")
    known = set(registry["id"].astype(str))
    referenced = set()
    for value in catalog["evidence_ids"].fillna(""):
        referenced.update(x.strip() for x in str(value).split(";") if x.strip())
    unknown = sorted(referenced - known)
    if unknown:
        raise ValueError(f"Unknown evidence IDs: {unknown}")


def build_method_selection_matrix() -> pd.DataFrame:
    rows = [
        ("Current level or distribution", "Descriptive statistics with uncertainty", "Stable definition and representative records", "Metric, interval and distribution", "Do not use a model when a direct measure answers the decision", "KAHN_DQ_2016;KAPLAN_MEIER_1958"),
        ("Recent change", "Run chart / regression / interrupted time series", "Comparable periods and no unreviewed concurrent change", "Level, slope, uncertainty and contextual events", "Do not call a before-after difference causal", "BERNAL_ITS_2017;SQUIRE_2016"),
        ("Individual risk", "Temporally validated probability model", "Predictors available at decision time and stable outcome definition", "Calibration, PR-AUC, utility and subgroup performance", "Do not use accuracy alone for imbalanced outcomes", "TRIPOD_AI_2024;PROBAST_2019;SAITO_PR_2015"),
        ("Threshold or workload policy", "Decision curve / capacity-constrained policy grid", "Defensible error consequences and real team capacity", "Net benefit or workload/precision/recall trade-off", "Do not default to 0.5", "VICKERS_DCA_2006;VAN_CALSTER_CALIBRATION_2019"),
        ("Intervention effect", "Randomised trial or target-trial emulation", "Aligned eligibility, assignment, time zero and outcomes", "Causal estimand with assumptions and sensitivity analysis", "Do not infer effect from feature importance or raw pre/post change", "HERNAN_TARGET_TRIAL_2016;CONSORT_AI_2020;SPIRIT_AI_2020"),
        ("Waiting time with incomplete follow-up", "Survival / competing-risk analysis", "Recorded entry, outcome, censoring and competing events", "Time-to-event curve and fixed-horizon probability", "Do not treat immature cohorts as failures", "KAPLAN_MEIER_1958;FINE_GRAY_1999"),
        ("Forecast and capacity", "Baseline-comparative probabilistic forecast plus queue scenarios", "Stable time grain, backtesting and capacity assumptions", "Forecast intervals, WAPE and scenario envelope", "Do not treat scenarios as causal impact", "HYNDMAN_MASE_2006;GNEITING_SCORING_2007;LITTLE_LAW_1961"),
        ("Fairness and safety", "Subgroup reliability, harm analysis and human-factors evaluation", "Meaningful groups, sufficient samples and defined harms", "Group metrics, uncertainty, overrides and guardrails", "Do not optimize one parity metric without a harm model", "OBERMEYER_BIAS_2019;DECIDE_AI_2022;WHO_AI_ETHICS_2021"),
        ("Economic or scale decision", "Incremental cost-effectiveness and implementation evaluation", "Credible effect, costs, perspective and adoption evidence", "Scenario distribution and stage-gate decision", "Do not monetise an assumed effect as realised savings", "CHEERS_2022;NICE_ESF_2022;SQUIRE_2016"),
    ]
    return pd.DataFrame(rows, columns=["question_family", "recommended_method", "key_assumptions", "required_output", "avoid", "evidence_ids"])


def write_evidence_handbook(
    catalog: pd.DataFrame,
    registry: pd.DataFrame,
    coverage: pd.DataFrame,
    gaps: pd.DataFrame,
    method_matrix: pd.DataFrame,
    external_registry: pd.DataFrame,
    output_path: str | Path,
) -> None:
    lines = [
        "# Evidence-backed data science operating handbook",
        "",
        "> All project numbers are synthetic. Literature supports the analytical method or governance principle; it does not validate provider-specific effects.",
        "",
        "## Coverage",
        "",
        f"- Questions: {len(catalog)}",
        f"- Categories: {catalog['category'].nunique()}",
        f"- Literature sources: {len(registry)}",
        f"- External public data sources: {len(external_registry)}",
        f"- Questions with literature support: {int((catalog['literature_source_count'] >= 1).sum())}/{len(catalog)}",
        f"- Questions with project data support: {int((catalog['available_data_outputs'] >= 1).sum())}/{len(catalog)}",
        "",
        "## Method selection matrix",
        "",
    ]
    for _, row in method_matrix.iterrows():
        lines.extend([
            f"### {row['question_family']}",
            "",
            f"**Recommended method:** {row['recommended_method']}",
            "",
            f"**Key assumptions:** {row['key_assumptions']}",
            "",
            f"**Required output:** {row['required_output']}",
            "",
            f"**Avoid:** {row['avoid']}",
            "",
            f"**Evidence:** {row['evidence_ids']}",
            "",
        ])
    lines.extend(["## Evidence registry", ""])
    for _, row in registry.sort_values(["year", "id"], ascending=[False, True]).iterrows():
        lines.extend([
            f"### {row['id']} — {row['title']} ({int(row['year'])})",
            "",
            f"**Type:** {row['source_type']} · **Venue:** {row['venue']}",
            "",
            f"**Project use:** {row['use_in_project']}",
            "",
            f"**Limitation:** {row['limitations']}",
            "",
            f"**URL:** {row['url']}",
            "",
        ])
    lines.extend(["## External public-data registry", ""])
    for _, row in external_registry.iterrows():
        lines.extend([f"### {row['id']} — {row['name']}", "", f"**Publisher:** {row['publisher']}", "", f"**Project use:** {row['project_use']}", "", f"**Limitation:** {row['limitations']}", "", f"**URL:** {row['url']}", ""])
    lines.extend(["## Evidence-gap policy", "", "Causal, predictive, safety and governance questions remain gated even when the synthetic analysis runs successfully. The evidence-gap register states what must happen before a real-world decision is treated as ready.", ""])
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")
