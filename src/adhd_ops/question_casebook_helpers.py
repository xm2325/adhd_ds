from __future__ import annotations
from typing import Any
import pandas as pd


def _fmt(value: float | int | None, digits: int=1) -> str:
    if value is None or pd.isna(value):
        return 'not available'
    return f'{float(value):,.{digits}f}'


def _pct(value: float | None, digits: int=1) -> str:
    if value is None or pd.isna(value):
        return 'not available'
    return f'{float(value):.{digits}%}'


def _row(frame: pd.DataFrame, column: str, value: Any) -> pd.Series | None:
    match = frame[frame[column].eq(value)]
    return match.iloc[0] if len(match) else None
