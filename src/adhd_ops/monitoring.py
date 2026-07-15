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


def build_champion_challenger_monitoring(
    scored_models: pd.DataFrame,
    model_registry: pd.DataFrame,
    operations_config: dict,
) -> pd.DataFrame:
    """Compare champion and challenger models by month on later-time data."""
    from sklearn.metrics import average_precision_score

    data = scored_models.copy()
    data["scheduled_start"] = pd.to_datetime(data["scheduled_start"], errors="coerce")
    data["monitoring_month"] = data["scheduled_start"].dt.to_period("M").astype(str)
    status = model_registry.set_index("model")["status"].to_dict()
    rows = []
    for (model, month), group in data.groupby(["model", "monitoring_month"], sort=True):
        observed = group["observed_dna"]
        probability = group["predicted_dna_probability"]
        pr_auc = (
            float(average_precision_score(observed, probability))
            if observed.nunique() > 1
            else float("nan")
        )
        rows.append(
            {
                "model": model,
                "model_status": status.get(model, "candidate"),
                "monitoring_month": month,
                "n": int(len(group)),
                "observed_dna_rate": float(observed.mean()),
                "mean_predicted_probability": float(probability.mean()),
                "brier_score": float(brier_score_loss(observed, probability)),
                "pr_auc": pr_auc,
            }
        )
    frame = pd.DataFrame(rows)
    cfg = operations_config["model_governance"]
    champion = model_registry.loc[model_registry["status"].eq("champion"), "model"].iloc[0]
    challenger = model_registry.loc[model_registry["status"].eq("challenger"), "model"].iloc[0]
    latest_months = sorted(frame["monitoring_month"].unique())[-3:]
    recent = frame[frame["monitoring_month"].isin(latest_months)]
    recent_summary = recent.groupby("model", as_index=False).agg(
        recent_mean_brier=("brier_score", "mean"),
        recent_mean_pr_auc=("pr_auc", "mean"),
    )
    lookup = recent_summary.set_index("model")
    promotion_candidate = False
    if champion in lookup.index and challenger in lookup.index:
        brier_improvement = float(
            lookup.loc[champion, "recent_mean_brier"]
            - lookup.loc[challenger, "recent_mean_brier"]
        )
        pr_auc_drop = float(
            lookup.loc[champion, "recent_mean_pr_auc"]
            - lookup.loc[challenger, "recent_mean_pr_auc"]
        )
        promotion_candidate = (
            brier_improvement
            >= float(cfg["challenger_brier_improvement_required"])
            and pr_auc_drop <= float(cfg["challenger_pr_auc_drop_tolerance"])
        )
    frame["challenger_promotion_candidate"] = bool(promotion_candidate)
    frame["synthetic"] = True
    return frame
