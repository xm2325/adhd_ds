from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

ASSET_DIR = Path(__file__).with_name("assets")


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    return frame.where(pd.notna(frame), None).to_dict(orient="records")


def _asset(name: str) -> str:
    return (ASSET_DIR / name).read_text(encoding="utf-8")


def augment_resilience_dashboard(
    path: str | Path,
    *,
    incident_results: pd.DataFrame,
    incident_timeline: pd.DataFrame,
    stress_summary: pd.DataFrame,
    early_warning: pd.DataFrame,
    response_matrix: pd.DataFrame,
    resilience_scorecard: pd.DataFrame,
) -> None:
    target = Path(path)
    html = target.read_text(encoding="utf-8")
    nav = '<button class="nav-btn" data-view="resilience"><span class="nav-icon">⚠</span>Resilience lab</button>'
    if nav not in html:
        html = html.replace(
            '<button class="nav-btn" data-view="evidence"><span class="nav-icon">§</span>Evidence & methods</button>',
            '<button class="nav-btn" data-view="evidence"><span class="nav-icon">§</span>Evidence & methods</button>\n  ' + nav,
        )
    html = html.replace("</style>", _asset("resilience_lab.css") + "\n</style>", 1)
    html = html.replace("</main>", _asset("resilience_lab.html") + "\n</main>", 1)
    payload = {
        "incidents": _records(incident_results),
        "timeline": _records(incident_timeline),
        "stress": _records(stress_summary),
        "warning": _records(early_warning),
        "responses": _records(response_matrix),
        "scorecard": _records(resilience_scorecard),
    }
    safe_json = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")
    script = _asset("resilience_lab.js").replace("__RESILIENCE_DATA__", safe_json)
    html = html.replace("</body>", script + "\n</body>", 1)
    target.write_text(html, encoding="utf-8")
