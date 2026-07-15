from __future__ import annotations

import numpy as np
import pandas as pd

PERIOD_WEEKS = 12


def _datetime(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    result = frame.copy()
    for column in columns:
        if column in result.columns:
            result[column] = pd.to_datetime(result[column], errors="coerce")
    return result


def _safe_relative_change(previous: float, recent: float) -> float:
    if pd.isna(previous) or previous == 0:
        return np.nan
    return float((recent - previous) / abs(previous))


def _selection_gap(frame: pd.DataFrame, selected_mask: pd.Series, column: str) -> float:
    rates = []
    for _, group in frame.groupby(column, dropna=False):
        if len(group):
            rates.append(float(selected_mask.loc[group.index].mean()))
    return float(max(rates) - min(rates)) if len(rates) >= 2 else 0.0
