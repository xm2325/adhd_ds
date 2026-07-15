from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

ASSET_DIR = Path(__file__).with_name("assets")


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    clean = frame.where(pd.notna(frame), None)
    return clean.to_dict(orient="records")


def _asset(name: str) -> str:
    return (ASSET_DIR / name).read_text(encoding="utf-8")


def augment_evidence_dashboard(
    path: str | Path,
    *,
    evidence_registry: pd.DataFrame,
    external_data_registry: pd.DataFrame,
    evidence_coverage: pd.DataFrame,
    evidence_gaps: pd.DataFrame,
    method_matrix: pd.DataFrame,
    kpi_uncertainty: pd.DataFrame,
    subgroup_reliability: pd.DataFrame,
    question_catalog: pd.DataFrame,
) -> None:
    target = Path(path)
    html = target.read_text(encoding="utf-8")
    nav = '<button class="nav-btn" data-view="evidence"><span class="nav-icon">§</span>Evidence & methods</button>'
    if nav not in html:
        html = html.replace(
            '<button class="nav-btn" data-view="scenario"><span class="nav-icon">?</span>DS scenario lab</button>',
            '<button class="nav-btn" data-view="scenario"><span class="nav-icon">?</span>DS scenario lab</button>\n  ' + nav,
        )
    html = html.replace("</style>", _asset("evidence_lab.css") + "\n</style>", 1)
    html = html.replace("</main>", _asset("evidence_lab.html") + "\n</main>", 1)
    payload = {
        "registry": _records(evidence_registry),
        "external_data": _records(external_data_registry),
        "coverage": _records(evidence_coverage),
        "gaps": _records(evidence_gaps),
        "methods": _records(method_matrix),
        "uncertainty": _records(kpi_uncertainty),
        "subgroups": _records(subgroup_reliability),
        "questions": _records(question_catalog[["id", "category", "question", "claim_type", "decision_readiness", "literature_source_count", "available_data_outputs"]]),
    }
    safe_json = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")
    script = _asset("evidence_lab.js").replace("__EVIDENCE_DATA__", safe_json)
    html = html.replace("</body>", script + "\n</body>", 1)
    target.write_text(html, encoding="utf-8")
