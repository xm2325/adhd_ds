from adhd_ops.synthetic import generate_synthetic_data


def test_generation_is_reproducible(synthetic_config):
    small = {
        **synthetic_config,
        "weeks": 8,
        "base_weekly_referrals": 8,
        "forecast_horizon_weeks": 2,
    }
    first = generate_synthetic_data(small)
    second = generate_synthetic_data(small)
    assert first["patients"].equals(second["patients"])
    assert first["appointments"].equals(second["appointments"])
