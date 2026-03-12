from fastapi.testclient import TestClient
import uuid

from app.main import app
from app.core.settings import settings

client = TestClient(app)


def _auth_headers(monkeypatch):
    monkeypatch.setattr(settings, "ALLOW_SEED_ADMIN", True)
    monkeypatch.setattr(settings, "ADMIN_SEED_TOKEN", "test-seed-token")

    seed_payload = {
        "username": f"admin_d07_{uuid.uuid4().hex[:8]}@example.com",
        "password": "dev",
        "role": "admin",
    }

    r_seed = client.post(
        "/api/v1/auth/seed-admin",
        json=seed_payload,
        headers={"x-seed-token": "test-seed-token"},
    )
    assert r_seed.status_code == 200
    body_seed = r_seed.json()
    assert body_seed["ok"] is True

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


def test_create_and_get_case_flow(monkeypatch):
    headers = _auth_headers(monkeypatch)

    create_payload = {
        "case_number": "0001234-56.2025.5.12.0001",
        "title": "Reclamação trabalhista por verbas rescisórias",
        "description": "Reclamante alega não recebimento de férias, 13º e FGTS.",
        "status": "draft",
    }
    r_create = client.post("/api/v1/cases", json=create_payload, headers=headers)
    assert r_create.status_code == 200
    created = r_create.json()
    assert created["case_number"] == create_payload["case_number"]
    assert created["title"] == create_payload["title"]
    assert created["status"] == create_payload["status"]
    assert "id" in created

    case_id = created["id"]

    r_list = client.get("/api/v1/cases", headers=headers)
    assert r_list.status_code == 200
    items = r_list.json()
    assert any(item["id"] == case_id for item in items)

    r_detail = client.get(f"/api/v1/cases/{case_id}", headers=headers)
    assert r_detail.status_code == 200
    detail = r_detail.json()
    assert detail["id"] == case_id
    assert detail["case_number"] == create_payload["case_number"]
