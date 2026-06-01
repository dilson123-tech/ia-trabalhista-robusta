from fastapi.testclient import TestClient
import uuid

from app.main import app
from app.core.settings import settings

client = TestClient(app)


def _auth_headers(monkeypatch):
    from app.api.v1.routes import cases as cases_routes

    monkeypatch.setattr(settings, "ALLOW_SEED_ADMIN", True)
    monkeypatch.setattr(settings, "ADMIN_SEED_TOKEN", "test-seed-token")
    monkeypatch.setattr(cases_routes, "enforce_plan_limits", lambda *args, **kwargs: None)

    seed_payload = {
        "username": f"admin_case_whatsapp_{uuid.uuid4().hex[:8]}@example.com",
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


def test_case_create_list_and_detail_include_client_whatsapp_fields(monkeypatch):
    headers = _auth_headers(monkeypatch)

    create_payload = {
        "case_number": f"WHATSAPP-QA-{uuid.uuid4().hex[:8]}",
        "title": "QA WhatsApp — comunicação com cliente",
        "description": "Caso para validar campos de contato WhatsApp do cliente.",
        "legal_area": "trabalhista",
        "action_type": "comunicacao_cliente",
        "client_name": "Cliente WhatsApp QA",
        "client_whatsapp": "5547999999999",
        "client_whatsapp_consent": True,
        "status": "draft",
    }

    r_create = client.post("/api/v1/cases", json=create_payload, headers=headers)
    assert r_create.status_code == 200
    created = r_create.json()

    assert created["case_number"] == create_payload["case_number"]
    assert created["client_name"] == "Cliente WhatsApp QA"
    assert created["client_whatsapp"] == "5547999999999"
    assert created["client_whatsapp_consent"] is True
    assert created["client_whatsapp_consent_at"]

    case_id = created["id"]

    r_detail = client.get(f"/api/v1/cases/{case_id}", headers=headers)
    assert r_detail.status_code == 200
    detail = r_detail.json()

    assert detail["client_name"] == "Cliente WhatsApp QA"
    assert detail["client_whatsapp"] == "5547999999999"
    assert detail["client_whatsapp_consent"] is True
    assert detail["client_whatsapp_consent_at"]

    r_list = client.get("/api/v1/cases", headers=headers)
    assert r_list.status_code == 200
    matching = [
        item for item in r_list.json()
        if item["case_number"] == create_payload["case_number"]
    ]
    assert len(matching) == 1
    assert matching[0]["client_name"] == "Cliente WhatsApp QA"
    assert matching[0]["client_whatsapp"] == "5547999999999"
    assert matching[0]["client_whatsapp_consent"] is True


def test_case_create_without_whatsapp_keeps_fields_empty(monkeypatch):
    headers = _auth_headers(monkeypatch)

    create_payload = {
        "case_number": f"NO-WHATSAPP-QA-{uuid.uuid4().hex[:8]}",
        "title": "QA Caso sem WhatsApp",
        "description": "Caso sem contato WhatsApp informado.",
        "legal_area": "cível",
        "action_type": "sem_contato",
        "status": "draft",
    }

    r_create = client.post("/api/v1/cases", json=create_payload, headers=headers)
    assert r_create.status_code == 200
    created = r_create.json()

    assert created["client_name"] is None
    assert created["client_whatsapp"] is None
    assert created["client_whatsapp_consent"] is False
    assert created["client_whatsapp_consent_at"] is None
