from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

ASSET_DIR = Path(__file__).with_name("assets")


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    clean = frame.copy()
    for column in clean.columns:
        if pd.api.types.is_datetime64_any_dtype(clean[column]):
            clean[column] = clean[column].dt.strftime("%Y-%m-%dT%H:%M:%S")
    clean = clean.where(pd.notna(clean), None)
    return clean.to_dict(orient="records")


def _asset(name: str) -> str:
    return (ASSET_DIR / name).read_text(encoding="utf-8")


def augment_scenario_dashboard(
    path: str | Path,
    *,
    questions: pd.DataFrame,
    root_causes: pd.DataFrame,
    stage_duration: pd.DataFrame,
    dna_decomposition: pd.DataFrame,
    threshold_grid: pd.DataFrame,
    feature_effects: pd.DataFrame,
    metric_sensitivity: pd.DataFrame,
    period_comparison: pd.DataFrame,
    default_capacity: int,
) -> None:
    target = Path(path)
    html = target.read_text(encoding="utf-8")
    nav = '<button class="nav-btn" data-view="scenario"><span class="nav-icon">?</span>DS scenario lab</button>'
    if nav not in html:
        html = html.replace(
            '<button class="nav-btn" data-view="audit"><span class="nav-icon">⌘</span>Audit & service API</button>',
            '<button class="nav-btn" data-view="audit"><span class="nav-icon">⌘</span>Audit & service API</button>\n  ' + nav,
        )
    html = html.replace("</style>", _asset("scenario_lab.css") + "\n</style>", 1)
    html = html.replace("</main>", _asset("scenario_lab.html") + "\n</main>", 1)
    payload = {
        "questions": _records(questions),
        "root_causes": _records(root_causes),
        "stage_duration": _records(stage_duration),
        "dna_decomposition": _records(dna_decomposition),
        "threshold_grid": _records(threshold_grid),
        "feature_effects": _records(feature_effects),
        "metric_sensitivity": _records(metric_sensitivity),
        "period_comparison": _records(period_comparison),
        "default_capacity": int(default_capacity),
    }
    safe_json = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")
    script = _asset("scenario_lab.js").replace("__SCENARIO_DATA__", safe_json)
    html = html.replace("</body>", script + "\n</body>", 1)
    target.write_text(html, encoding="utf-8")
