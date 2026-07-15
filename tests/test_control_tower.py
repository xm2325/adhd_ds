from pathlib import Path

from adhd_ops.attendance import train_attendance_models
from adhd_ops.config import load_yaml
from adhd_ops.control_tower import build_service_level_status, build_weekly_anomalies
from adhd_ops.monitoring import build_attendance_monitoring, build_forecast_monitoring

ROOT = Path(__file__).resolve().parents[1]


def test_control_tower_outputs_owned_statuses(
    tables, pathway, capacity, validation, forecast
):
    operations = load_yaml(ROOT / "config/operations.yaml")
    attendance = train_attendance_models(tables["appointments"])
    attendance_monitoring = build_attendance_monitoring(attendance["scored_test"])
    forecast_monitoring = build_forecast_monitoring(
        forecast["backtest"], forecast["weekly_actuals"]
    )
    result = build_service_level_status(
        pathway["patient_pathway"],
        capacity,
        validation,
        attendance_monitoring,
        forecast_monitoring,
        str(forecast["selected_model"]),
        operations,
    )
    assert len(result) == 6
    assert set(result["status"]).issubset({"green", "amber", "red", "unknown"})
    assert result["owner_role"].notna().all()


def test_weekly_anomaly_detector_returns_expected_fields(tables, forecast):
    result = build_weekly_anomalies(
        forecast["weekly_actuals"],
        tables["appointments"],
        load_yaml(ROOT / "config/operations.yaml"),
    )
    assert {"series", "robust_z", "status", "expected_rolling_median"}.issubset(
        result.columns
    )
    assert set(result["series"]) == {"weekly_referrals", "weekly_dna_rate"}
