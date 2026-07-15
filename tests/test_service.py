from fastapi.testclient import TestClient

from adhd_ops.service import create_app


def test_api_exposes_aggregate_controls_and_manifest(built_project):
    target, summary = built_project
    client = TestClient(create_app(target))
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["run_id"] == summary["run_id"]
    assert client.get("/v1/contracts").status_code == 200
    assert client.get("/v1/queue-policies").status_code == 200
    assert client.get("/v1/audit/manifest").json()["contract_gate"] == "pass"


def test_patient_queue_requires_operational_role(built_project):
    target, _ = built_project
    client = TestClient(create_app(target))
    assert client.get("/v1/appointment-support").status_code == 403
    response = client.get(
        "/v1/appointment-support?limit=3", headers={"X-Role": "patient_support"}
    )
    assert response.status_code == 200
    assert len(response.json()) == 3
    assert "patient_id" not in response.json()[0]


def test_api_exposes_ds_questions_and_diagnostics(built_project):
    target, _ = built_project
    client = TestClient(create_app(target))
    questions = client.get("/v1/ds-questions?category=appointment_and_model")
    assert questions.status_code == 200
    assert len(questions.json()) >= 8
    assert "current_synthetic_answer" in questions.json()[0]
    roots = client.get("/v1/diagnostics/root-causes")
    assert roots.status_code == 200
    assert any(row["hypothesis"] == "capacity_pressure" for row in roots.json())
    policies = client.get("/v1/diagnostics/threshold-policy?weekly_capacity=100")
    assert policies.status_code == 200
    assert all(row["weekly_capacity"] == 100 for row in policies.json())
