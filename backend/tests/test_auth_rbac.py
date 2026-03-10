import uuid

from app.core.settings import settings


def _seed_and_login(client, monkeypatch, role: str):
    monkeypatch.setattr(settings, "ALLOW_SEED_ADMIN", True)
    monkeypatch.setattr(settings, "ADMIN_SEED_TOKEN", "test-seed-token")

    username = f"{role}_{uuid.uuid4().hex[:8]}@example.com"
    password = "dev"

    seed_payload = {
        "username": username,
        "password": password,
        "role": role,
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
        json={"username": username, "password": password},
    )
    assert r_login.status_code == 200
    return r_login.json()["access_token"]


def test_admin_only_admin_ok(client, monkeypatch):
    token = _seed_and_login(client, monkeypatch, "admin")

    r = client.get(
        "/api/v1/auth/admin-only",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200


def test_admin_only_adv_forbidden(client, monkeypatch):
    token = _seed_and_login(client, monkeypatch, "advogado")

    r = client.get(
        "/api/v1/auth/admin-only",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403
