from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

NUMERIC = [
    "lead_days",
    "previous_attended_count",
    "previous_dna_count",
    "previous_cancel_count",
    "reschedule_count",
    "appointment_hour",
]
CATEGORICAL = [
    "appointment_type",
    "day_of_week",
    "service_group",
    "funding_route",
    "age_band",
    "region_group",
    "reminder_7d_delivered",
    "reminder_1d_delivered",
]


def prepare_attendance_data(appointments: pd.DataFrame) -> pd.DataFrame:
    data = appointments[appointments["appointment_status"].isin(["attended", "did_not_attend"])].copy()
    data["lead_days"] = (data["scheduled_start"] - data["booked_at"]).dt.total_seconds() / 86400
    data["day_of_week"] = data["scheduled_start"].dt.day_name()
    data["appointment_hour"] = data["scheduled_start"].dt.hour
    data["target_dna"] = data["appointment_status"].eq("did_not_attend").astype(int)
    return data.sort_values("scheduled_start").reset_index(drop=True)


def _preprocessor() -> ColumnTransformer:
    numeric = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
    ])
    categorical = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])
    return ColumnTransformer([("numeric", numeric, NUMERIC), ("categorical", categorical, CATEGORICAL)])


def train_attendance_models(appointments: pd.DataFrame, model_path: str | Path | None = None) -> dict:
    data = prepare_attendance_data(appointments)
    split = int(len(data) * 0.80)
    train, test = data.iloc[:split], data.iloc[split:]
    x_train, y_train = train[NUMERIC + CATEGORICAL], train["target_dna"]
    x_test, y_test = test[NUMERIC + CATEGORICAL], test["target_dna"]

    estimators = {
        "logistic_regression": LogisticRegression(max_iter=1000, random_state=42),
        "random_forest": RandomForestClassifier(
            n_estimators=220, min_samples_leaf=12, class_weight="balanced", random_state=42, n_jobs=1
        ),
    }
    fitted, predictions, metric_rows = {}, {}, []
    for name, estimator in estimators.items():
        model = Pipeline([("preprocess", _preprocessor()), ("model", estimator)])
        model.fit(x_train, y_train)
        probability = model.predict_proba(x_test)[:, 1]
        top_k = min(100, len(test))
        top_index = np.argsort(-probability)[:top_k]
        metric_rows.append({
            "model": name,
            "test_n": len(test),
            "dna_prevalence": float(y_test.mean()),
            "roc_auc": float(roc_auc_score(y_test, probability)),
            "pr_auc": float(average_precision_score(y_test, probability)),
            "brier_score": float(brier_score_loss(y_test, probability)),
            "top_k": top_k,
            "precision_at_k": float(y_test.iloc[top_index].mean()),
            "recall_at_k": float(y_test.iloc[top_index].sum() / max(y_test.sum(), 1)),
        })
        fitted[name] = model
        predictions[name] = probability

    metrics = pd.DataFrame(metric_rows)
    metrics["selection_score"] = metrics["pr_auc"] - 0.35 * metrics["brier_score"]
    metrics = metrics.sort_values(["selection_score", "pr_auc"], ascending=[False, False])
    selected = str(metrics.iloc[0]["model"])
    model, probability = fitted[selected], predictions[selected]

    scored = test[[
        "appointment_id", "patient_id", "scheduled_start", "appointment_type", "service_group", "funding_route"
    ]].copy()
    scored["observed_dna"] = y_test.to_numpy()
    scored["predicted_dna_probability"] = probability
    scored["support_priority_band"] = pd.cut(
        probability, [-0.001, 0.25, 0.50, 0.75, 1], labels=["routine", "review", "high", "very_high"]
    )
    scored["recommended_action"] = np.select(
        [probability >= 0.75, probability >= 0.50, probability >= 0.25],
        ["confirm_and_offer_easy_reschedule", "extra_reminder", "standard_reminder"],
        default="routine_process",
    )
    scored = scored.sort_values("predicted_dna_probability", ascending=False).reset_index(drop=True)
    support_queue = scored.head(200).copy()

    calibration_frame = pd.DataFrame({"probability": probability, "outcome": y_test.to_numpy()})
    calibration_frame["bin"] = pd.qcut(calibration_frame["probability"], q=10, duplicates="drop")
    calibration = (
        calibration_frame.groupby("bin", observed=True)
        .agg(
            mean_predicted_probability=("probability", "mean"),
            observed_dna_rate=("outcome", "mean"),
            n=("outcome", "size"),
        )
        .reset_index()
    )
    calibration["bin"] = calibration["bin"].astype(str)

    audit_frame = test.copy()
    audit_frame["probability"] = probability
    subgroup_rows = []
    for variable in ["funding_route", "service_group"]:
        for value, group in audit_frame.groupby(variable):
            subgroup_rows.append({
                "group_variable": variable,
                "group_value": value,
                "n": len(group),
                "observed_dna_rate": float(group["target_dna"].mean()),
                "mean_predicted_probability": float(group["probability"].mean()),
                "brier_score": float(brier_score_loss(group["target_dna"], group["probability"])),
            })
    subgroup_audit = pd.DataFrame(subgroup_rows)

    if model_path is not None:
        path = Path(model_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, path)
    return {
        "metrics": metrics,
        "selected_model": selected,
        "support_queue": support_queue,
        "scored_test": scored,
        "calibration": calibration,
        "subgroup_audit": subgroup_audit,
        "model": model,
    }
