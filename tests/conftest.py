from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from adhd_ops.capacity import simulate_capacity
from adhd_ops.config import load_yaml
from adhd_ops.forecasting import forecast_referrals
from adhd_ops.pathway import analyse_pathway
from adhd_ops.pipeline import run
from adhd_ops.synthetic import generate_synthetic_data
from adhd_ops.validation import validate_tables

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def synthetic_config():
    return load_yaml(ROOT / "config/synthetic_data.yaml")


@pytest.fixture(scope="session")
def tables(synthetic_config):
    return generate_synthetic_data(synthetic_config)


@pytest.fixture(scope="session")
def pathway(tables):
    return analyse_pathway(tables)


@pytest.fixture(scope="session")
def forecast(tables, synthetic_config):
    return forecast_referrals(tables["referrals"], int(synthetic_config["forecast_horizon_weeks"]))


@pytest.fixture(scope="session")
def capacity(tables, pathway, forecast, synthetic_config):
    return simulate_capacity(
        tables,
        pathway["patient_pathway"],
        forecast["forecast"],
        load_yaml(ROOT / "config/scenarios.yaml"),
        float(synthetic_config["assessment_duration_minutes"]),
    )


@pytest.fixture(scope="session")
def validation(tables):
    return validate_tables(tables)


@pytest.fixture(scope="session")
def built_project(tmp_path_factory):
    target = tmp_path_factory.mktemp("built_project")
    shutil.copytree(ROOT / "config", target / "config")
    summary = run(target)
    return target, summary
