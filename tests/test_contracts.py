from adhd_ops.config import load_yaml
from adhd_ops.contracts import build_source_profiles, validate_data_contracts
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_data_contracts_pass_for_generated_tables(tables):
    status = validate_data_contracts(tables, load_yaml(ROOT / "config/data_contracts.yaml"))
    assert not status["failure_count"].gt(0).any()
    assert status["rule"].str.startswith("primary_key_unique").any()


def test_source_profiles_have_stable_fingerprints(tables):
    first = build_source_profiles(tables)
    second = build_source_profiles(tables)
    assert first["sha256_fingerprint"].tolist() == second["sha256_fingerprint"].tolist()
    assert first["sha256_fingerprint"].str.len().eq(64).all()
