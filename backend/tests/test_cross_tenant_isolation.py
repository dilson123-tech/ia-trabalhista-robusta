import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.core.settings import settings

client = TestClient(app)


def seed_and_login(username: str):
    payload = {
        "username": username,
        "password": "devpass123",
        "role": "admin",
    }

    client.post(
        "/api/v1/auth/seed-admin",
        json=payload,
        headers={"x-seed-token": settings.ADMIN_SEED_TOKEN},
    )

    r = client.post(
        "/api/v1/auth/login",
        json={"username": payload["username"], "password": payload["password"]},
    )

    assert r.status_code == 200
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_cross_tenant_isolation():
    # Tenant A
    headers_a = seed_and_login(f"userA_{uuid.uuid4().hex[:6]}@test.com")

    # Tenant B
    headers_b = seed_and_login(f"userB_{uuid.uuid4().hex[:6]}@test.com")

    # A cria case
    r_create = client.post(
        "/api/v1/cases",
        json={
            "case_number": f"CASE-{uuid.uuid4().hex[:6]}",
            "title": "Teste isolamento",
            "description": "Descrição",
        },
        headers=headers_a,
    )
    assert r_create.status_code == 200
    case_id = r_create.json()["id"]

    # B não deve ver na listagem
    r_list = client.get("/api/v1/cases", headers=headers_b)
    assert r_list.status_code == 200
    assert all(c["id"] != case_id for c in r_list.json())

    # B não deve acessar via ID
    r_get = client.get(f"/api/v1/cases/{case_id}", headers=headers_b)
    assert r_get.status_code == 404
