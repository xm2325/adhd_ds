import pandas as pd

from adhd_ops.monitoring import build_attendance_monitoring, build_forecast_monitoring


def test_attendance_monitoring_keeps_monthly_calibration_fields():
    scored = pd.DataFrame({
        "scheduled_start": pd.to_datetime(["2026-01-02", "2026-01-10", "2026-02-04"]),
        "observed_dna": [0, 1, 1],
        "predicted_dna_probability": [0.2, 0.7, 0.8],
    })
    result = build_attendance_monitoring(scored)
    assert set(result["monitoring_month"]) == {"2026-01", "2026-02"}
    assert {"calibration_gap", "brier_score"}.issubset(result.columns)


def test_forecast_monitoring_attaches_origin_dates():
    weekly = pd.DataFrame({"week_start": pd.date_range("2026-01-05", periods=8, freq="W-MON")})
    backtest = pd.DataFrame({"model": ["naive_last"], "origin_index": [4], "wape": [0.1], "underforecast_rate": [0.5]})
    result = build_forecast_monitoring(backtest, weekly)
    assert result.loc[0, "origin_week"] == weekly.loc[4, "week_start"]
