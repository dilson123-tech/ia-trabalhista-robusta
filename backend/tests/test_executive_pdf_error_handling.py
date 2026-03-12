from fastapi.testclient import TestClient
import uuid

from app.main import app
from app.core.settings import settings

client = TestClient(app, raise_server_exceptions=False)


def _auth_headers(monkeypatch):
    monkeypatch.setattr(settings, "ALLOW_SEED_ADMIN", True)
    monkeypatch.setattr(settings, "ADMIN_SEED_TOKEN", "test-seed-token")

    seed_payload = {
        "username": f"admin_pdf_err_{uuid.uuid4().hex[:8]}@example.com",
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


def test_executive_pdf_internal_error_returns_500(monkeypatch):
    headers = _auth_headers(monkeypatch)

    create_payload = {
        "case_number": "8888888-88.2025.5.12.0001",
        "title": "Teste erro PDF Executivo",
        "description": "Descrição para simular erro interno na geração de PDF.",
        "status": "draft",
    }

    r_create = client.post("/api/v1/cases", json=create_payload, headers=headers)
    assert r_create.status_code == 200
    case_id = r_create.json()["id"]

    def _boom(*args, **kwargs):
        raise RuntimeError("pdf engine exploded on purpose")

    monkeypatch.setattr("app.api.v1.routes.cases.generate_executive_pdf", _boom)

    response = client.get(f"/api/v1/cases/{case_id}/executive-pdf", headers=headers)

    assert response.status_code == 500
