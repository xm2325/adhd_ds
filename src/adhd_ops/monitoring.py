from __future__ import annotations

import pandas as pd
from sklearn.metrics import brier_score_loss


def build_attendance_monitoring(scored: pd.DataFrame) -> pd.DataFrame:
    """Summarise probability calibration over calendar months in later-time data."""
    data = scored.copy()
    data["scheduled_start"] = pd.to_datetime(data["scheduled_start"], errors="coerce")
    data["monitoring_month"] = data["scheduled_start"].dt.to_period("M").astype(str)
    rows = []
    for month, group in data.groupby("monitoring_month", sort=True):
        observed = float(group["observed_dna"].mean())
        predicted = float(group["predicted_dna_probability"].mean())
        rows.append({
            "monitoring_month": month,
            "n": int(len(group)),
            "observed_dna_rate": observed,
            "mean_predicted_probability": predicted,
            "calibration_gap": predicted - observed,
            "absolute_calibration_gap": abs(predicted - observed),
            "brier_score": float(brier_score_loss(group["observed_dna"], group["predicted_dna_probability"])),
        })
    return pd.DataFrame(rows)


def build_forecast_monitoring(backtest: pd.DataFrame, weekly_actuals: pd.DataFrame) -> pd.DataFrame:
    """Attach dates to rolling-origin forecast checks for monitoring charts."""
    dates = weekly_actuals["week_start"].reset_index(drop=True)
    frame = backtest.copy()
    frame["origin_week"] = frame["origin_index"].map(
        lambda index: dates.iloc[int(index)] if int(index) < len(dates) else pd.NaT
    )
    return frame.sort_values(["origin_week", "model"]).reset_index(drop=True)
