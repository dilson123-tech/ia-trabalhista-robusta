from fastapi.testclient import TestClient
import uuid

from app.main import app
from app.core.settings import settings

client = TestClient(app)


def _seed_and_login(role: str):
    username = f"{role}_{uuid.uuid4().hex[:8]}@example.com"
    password = "dev"

    seed_payload = {
        "username": username,
        "password": password,
        "role": role,
    }

    # seed admin endpoint é protegido por token
    r_seed = client.post(
        "/api/v1/auth/seed-admin",
        json=seed_payload,
        headers={"x-seed-token": settings.ADMIN_SEED_TOKEN},
    )
    assert r_seed.status_code == 200
    assert r_seed.json()["ok"] is True

    r_login = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert r_login.status_code == 200
    return r_login.json()["access_token"]


def test_admin_only_admin_ok():
    token = _seed_and_login("admin")

    r = client.get(
        "/api/v1/auth/admin-only",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200


def test_admin_only_adv_forbidden():
    token = _seed_and_login("advogado")

    r = client.get(
        "/api/v1/auth/admin-only",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403
