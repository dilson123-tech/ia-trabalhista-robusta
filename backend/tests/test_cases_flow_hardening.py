from fastapi.testclient import TestClient
import uuid

from app.main import app
from app.core.settings import settings

client = TestClient(app)


def _auth_headers(monkeypatch):
    monkeypatch.setattr(settings, "ALLOW_SEED_ADMIN", True)
    monkeypatch.setattr(settings, "ADMIN_SEED_TOKEN", "test-seed-token")

    seed_payload = {
        "username": f"admin_case_hard_{uuid.uuid4().hex[:8]}@example.com",
        "password": "dev",
        "role": "admin",
    }

    r_seed = client.post(
        "/api/v1/auth/seed-admin",
        json=seed_payload,
        headers={"x-seed-token": "test-seed-token"},
    )
    assert r_seed.status_code == 200
    assert r_seed.json()["ok"] is True

    r_login = client.post(
        "/api/v1/auth/login",
        json={
            "username": seed_payload["username"],
            "password": seed_payload["password"],
        },
    )
    assert r_login.status_code == 200

    token = r_login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_cases_flow_idempotent_analysis_and_report(monkeypatch):
    headers = _auth_headers(monkeypatch)

    create_payload = {
        "case_number": f"FLOW-{uuid.uuid4()}",
        "title": "Caso de fluxo endurecido",
        "description": "Teste de idempotência, análise e relatório.",
        "status": "draft",
    }

    first_create = client.post("/api/v1/cases", json=create_payload, headers=headers)
    assert first_create.status_code == 200
    first_case = first_create.json()
    case_id = first_case["id"]

    second_create = client.post("/api/v1/cases", json=create_payload, headers=headers)
    assert second_create.status_code == 200
    second_case = second_create.json()

    assert second_case["id"] == case_id
    assert second_case["case_number"] == create_payload["case_number"]

    list_resp = client.get("/api/v1/cases", headers=headers)
    assert list_resp.status_code == 200
    items = [item for item in list_resp.json() if item["case_number"] == create_payload["case_number"]]
    assert len(items) == 1

    first_analysis = client.get(f"/api/v1/cases/{case_id}/analysis", headers=headers)
    assert first_analysis.status_code == 200
    first_analysis_body = first_analysis.json()
    assert first_analysis_body["case_id"] == case_id
    assert "analysis_id" in first_analysis_body
    assert "analysis" in first_analysis_body

    second_analysis = client.get(f"/api/v1/cases/{case_id}/analysis", headers=headers)
    assert second_analysis.status_code == 200
    second_analysis_body = second_analysis.json()

    assert second_analysis_body["case_id"] == case_id
    assert second_analysis_body["analysis_id"] == first_analysis_body["analysis_id"]

    report_resp = client.get(f"/api/v1/cases/{case_id}/report", headers=headers)
    assert report_resp.status_code == 200
    report_body = report_resp.json()
    assert "report_html" in report_body
    assert isinstance(report_body["report_html"], str)
    assert len(report_body["report_html"]) > 50


def test_cases_endpoints_return_404_for_missing_case(monkeypatch):
    headers = _auth_headers(monkeypatch)
    missing_id = 999999

    detail = client.get(f"/api/v1/cases/{missing_id}", headers=headers)
    assert detail.status_code == 404

    analysis = client.get(f"/api/v1/cases/{missing_id}/analysis", headers=headers)
    assert analysis.status_code == 404

    report = client.get(f"/api/v1/cases/{missing_id}/report", headers=headers)
    assert report.status_code == 404
