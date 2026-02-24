from fastapi.testclient import TestClient
import uuid

from app.main import app
from app.core.settings import settings

client = TestClient(app)


def _auth_headers():
    seed_payload = {
        "username": f"admin_pdf_{uuid.uuid4().hex[:8]}@example.com",
        "password": f"admin_pdf_pass_{uuid.uuid4().hex[:8]}",
        "role": "admin",
    }

    # seed admin
    r_seed = client.post(
        "/api/v1/auth/seed-admin",
        json=seed_payload,
        headers={"x-seed-token": settings.ADMIN_SEED_TOKEN},
    )
    assert r_seed.status_code == 200
    assert r_seed.json()["ok"] is True

    # login
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


def test_executive_pdf_requires_auth():
    response = client.get("/api/v1/cases/1/executive-pdf")
    assert response.status_code in (401, 403)


def test_executive_pdf_authenticated_flow():
    headers = _auth_headers()

    # cria case
    create_payload = {
        "case_number": "9999999-99.2025.5.12.0001",
        "title": "Teste PDF Executivo",
        "description": "Descrição para geração de PDF executivo.",
        "status": "draft",
    }

    r_create = client.post("/api/v1/cases", json=create_payload, headers=headers)
    assert r_create.status_code == 200
    created = r_create.json()
    case_id = created["id"]

    # gera PDF
    r_pdf = client.get(f"/api/v1/cases/{case_id}/executive-pdf", headers=headers)

    assert r_pdf.status_code == 200
    assert r_pdf.headers["content-type"].startswith("application/pdf")
    assert len(r_pdf.content) > 100  # garante que não é JSON pequeno
