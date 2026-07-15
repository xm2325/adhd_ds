from adhd_ops.attendance import CATEGORICAL, NUMERIC


def test_no_post_appointment_features_are_used():
    forbidden = {"appointment_status", "cancelled_at", "cancellation_reason", "target_dna"}
    assert forbidden.isdisjoint(set(NUMERIC + CATEGORICAL))


def test_model_registry_has_champion_and_challenger(tables):
    from adhd_ops.attendance import train_attendance_models

    result = train_attendance_models(tables["appointments"])
    assert set(result["model_registry"]["status"]) == {"champion", "challenger"}
    assert result["scored_models"]["model"].nunique() == 2
