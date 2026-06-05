from fastapi.testclient import TestClient
from datetime import datetime, timezone
import uuid

from app.main import app
from app.core.settings import settings
from app.core.security import pwd_context
from app.models.tenant import Tenant
from app.models.tenant_member import TenantMember
from app.models.user import User
from app.models.subscription import Subscription

client = TestClient(app)


def _auth_headers(monkeypatch, prefix="contact_log"):
    from app.api.v1.routes import cases as cases_routes

    monkeypatch.setattr(settings, "ALLOW_SEED_ADMIN", True)
    monkeypatch.setattr(settings, "ADMIN_SEED_TOKEN", "test-seed-token")
    monkeypatch.setattr(cases_routes, "enforce_plan_limits", lambda *args, **kwargs: None)

    seed_payload = {
        "username": f"admin_{prefix}_{uuid.uuid4().hex[:8]}@example.com",
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


def _create_case(headers):
    create_payload = {
        "case_number": f"CONTACT-LOG-QA-{uuid.uuid4().hex[:8]}",
        "title": "QA Registro manual de contato WhatsApp",
        "description": "Caso para validar auditoria manual de contato com cliente.",
        "legal_area": "trabalhista",
        "action_type": "comunicacao_cliente",
        "client_name": "Cliente Contato QA",
        "client_whatsapp": "5547999999999",
        "client_whatsapp_consent": True,
        "status": "draft",
    }

    r_create = client.post("/api/v1/cases", json=create_payload, headers=headers)
    assert r_create.status_code == 200
    return r_create.json()["id"]


def test_case_contact_logs_create_and_list(monkeypatch):
    headers = _auth_headers(monkeypatch)
    case_id = _create_case(headers)

    payload = {
        "contact_type": "whatsapp",
        "direction": "outgoing",
        "summary": "Solicitados documentos pelo WhatsApp",
        "note": "Advogado pediu RG, comprovante de residência e prints da conversa.",
    }

    r_create = client.post(
        f"/api/v1/cases/{case_id}/contact-logs",
        json=payload,
        headers=headers,
    )
    assert r_create.status_code == 200
    created = r_create.json()

    assert created["case_id"] == case_id
    assert created["contact_type"] == "whatsapp"
    assert created["direction"] == "outgoing"
    assert created["summary"] == payload["summary"]
    assert created["note"] == payload["note"]
    assert created["occurred_at"]
    assert created["created_at"]
    assert created["updated_at"]

    r_list = client.get(
        f"/api/v1/cases/{case_id}/contact-logs",
        headers=headers,
    )
    assert r_list.status_code == 200
    items = r_list.json()

    assert len(items) == 1
    assert items[0]["id"] == created["id"]
    assert items[0]["summary"] == "Solicitados documentos pelo WhatsApp"

    r_delete = client.delete(
        f"/api/v1/cases/{case_id}/contact-logs/{created['id']}",
        headers=headers,
    )
    assert r_delete.status_code == 204

    r_list_after_delete = client.get(
        f"/api/v1/cases/{case_id}/contact-logs",
        headers=headers,
    )
    assert r_list_after_delete.status_code == 200
    assert r_list_after_delete.json() == []


def test_case_contact_logs_reject_missing_case(monkeypatch):
    headers = _auth_headers(monkeypatch, prefix="missing_case")
    missing_id = 999999999

    r_create = client.post(
        f"/api/v1/cases/{missing_id}/contact-logs",
        json={
            "contact_type": "whatsapp",
            "direction": "outgoing",
            "summary": "Tentativa inválida",
        },
        headers=headers,
    )
    assert r_create.status_code == 404

    r_list = client.get(
        f"/api/v1/cases/{missing_id}/contact-logs",
        headers=headers,
    )
    assert r_list.status_code == 404

    r_delete = client.delete(
        f"/api/v1/cases/{missing_id}/contact-logs/1",
        headers=headers,
    )
    assert r_delete.status_code == 404


