from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error


def weekly_referral_series(referrals: pd.DataFrame) -> pd.DataFrame:
    data = referrals.copy()
    data["week_start"] = data["referral_received_at"].dt.to_period("W-SUN").dt.start_time
    weekly = data.groupby("week_start").size().rename("referrals").reset_index()
    full = pd.DataFrame({"week_start": pd.date_range(weekly["week_start"].min(), weekly["week_start"].max(), freq="W-MON")})
    return full.merge(weekly, on="week_start", how="left").fillna({"referrals": 0})


def _features(history: list[float], index: int) -> list[float]:
    return [
        index,
        np.sin(2 * np.pi * index / 52),
        np.cos(2 * np.pi * index / 52),
        history[-1],
        float(np.mean(history[-4:])),
    ]


def _fit_ridge(values: np.ndarray) -> Ridge:
    history = values.astype(float).tolist()
    x, y = [], []
    for index in range(4, len(history)):
        x.append(_features(history[:index], index))
        y.append(history[index])
    return Ridge(alpha=8.0).fit(np.asarray(x), np.asarray(y))


def _predict(values: np.ndarray, horizon: int, model_name: str) -> np.ndarray:
    history = values.astype(float).tolist()
    model = _fit_ridge(values) if model_name == "ridge" else None
    output = []
    for _ in range(horizon):
        if model_name == "naive_last":
            prediction = history[-1]
        elif model_name == "rolling4":
            prediction = float(np.mean(history[-4:]))
        elif model_name == "ridge":
            prediction = float(model.predict(np.asarray([_features(history, len(history))]))[0])
        else:
            raise ValueError(model_name)
        prediction = max(0.0, prediction)
        history.append(prediction)
        output.append(prediction)
    return np.asarray(output)


def forecast_referrals(referrals: pd.DataFrame, horizon: int = 12) -> dict:
    weekly = weekly_referral_series(referrals)
    values = weekly["referrals"].to_numpy(dtype=float)
    models = ["naive_last", "rolling4", "ridge"]
    rows, residuals = [], {model: [] for model in models}
    for model_name in models:
        for origin in range(max(52, len(values) // 2), len(values) - 3, 4):
            actual = values[origin : origin + 4]
            predicted = _predict(values[:origin], len(actual), model_name)
            residuals[model_name].extend((actual - predicted).tolist())
            rows.append({
                "model": model_name,
                "origin_index": origin,
                "horizon_weeks": len(actual),
                "mae": mean_absolute_error(actual, predicted),
                "wape": float(np.abs(actual - predicted).sum() / max(actual.sum(), 1)),
                "underforecast_rate": float((predicted < actual).mean()),
            })
    backtest = pd.DataFrame(rows)
    performance = (
        backtest.groupby("model", as_index=False)
        .agg(
            mean_mae=("mae", "mean"),
            mean_wape=("wape", "mean"),
            mean_underforecast_rate=("underforecast_rate", "mean"),
        )
        .sort_values("mean_wape")
    )
    selected = str(performance.iloc[0]["model"])
    point = _predict(values, horizon, selected)
    errors = np.asarray(residuals[selected])
    lower_error, upper_error = np.quantile(errors, [0.1, 0.9])
    future = pd.date_range(weekly["week_start"].max() + pd.Timedelta(days=7), periods=horizon, freq="W-MON")
    forecast = pd.DataFrame({
        "week_start": future,
        "predicted_referrals": point,
        "p10_referrals": np.maximum(0, point + lower_error),
        "p90_referrals": np.maximum(0, point + upper_error),
        "selected_model": selected,
    })
    return {
        "weekly_actuals": weekly,
        "backtest": backtest,
        "performance": performance,
        "forecast": forecast,
        "selected_model": selected,
    }
