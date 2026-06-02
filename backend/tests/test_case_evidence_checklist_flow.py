import uuid

from app.core.settings import settings
from app.api.v1.routes import cases as cases_routes


def _auth_headers(client, monkeypatch):
    def _skip_plan_limits(*args, **kwargs):
        return None

    monkeypatch.setattr(cases_routes, "enforce_plan_limits", _skip_plan_limits)
    monkeypatch.setattr(settings, "ALLOW_SEED_ADMIN", True)
    monkeypatch.setattr(settings, "ADMIN_SEED_TOKEN", "test-seed-token")

    seed_payload = {
        "username": f"admin_evidence_{uuid.uuid4().hex[:8]}@example.com",
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


def test_case_evidence_checklist_authenticated_flow(client, monkeypatch, tmp_path):
    monkeypatch.setattr(
        settings,
        "CASE_ATTACHMENT_STORAGE_DIR",
        str(tmp_path / "case_attachments"),
    )
    headers = _auth_headers(client, monkeypatch)

    r_case = client.post(
        "/api/v1/cases",
        json={
            "case_number": f"EVIDENCE-{uuid.uuid4().hex[:8]}",
            "title": "Caso de teste do checklist de provas",
            "description": "Validação de pendências/provas por caso.",
            "legal_area": "trabalhista",
            "action_type": "Petição Inicial Trabalhista",
            "status": "draft",
        },
        headers=headers,
    )
    assert r_case.status_code == 200
    case_id = r_case.json()["id"]

    r_create = client.post(
        f"/api/v1/cases/{case_id}/evidence-checklist",
        json={
            "title": "Solicitar comprovante de residência",
            "category": "documento_pessoal",
            "status": "pending",
            "priority": "high",
            "requested_from": "cliente",
            "due_date": "2026-06-10",
            "notes": "Pedir pelo WhatsApp antes de montar a peça.",
            "metadata": {
                "source": "case_evidence_checklist_v1",
            },
        },
        headers=headers,
    )
    assert r_create.status_code == 200
    created = r_create.json()
    assert created["case_id"] == case_id
    assert created["title"] == "Solicitar comprovante de residência"
    assert created["status"] == "pending"
    assert created["priority"] == "high"
    assert created["checklist_metadata"]["source"] == "case_evidence_checklist_v1"

    item_id = created["id"]

    r_list = client.get(f"/api/v1/cases/{case_id}/evidence-checklist", headers=headers)
    assert r_list.status_code == 200
    assert len(r_list.json()) == 1

    r_upload = client.post(
        f"/api/v1/cases/{case_id}/attachments",
        headers=headers,
        data={
            "category": "documento_pessoal",
            "description": "Comprovante de residência recebido.",
            "event_date": "2026-06-02",
        },
        files={"file": ("comprovante.pdf", b"%PDF-1.4\n%%EOF\n", "application/pdf")},
    )
    assert r_upload.status_code == 200
    attachment_id = r_upload.json()["id"]

    r_update = client.patch(
        f"/api/v1/cases/{case_id}/evidence-checklist/{item_id}",
        json={
            "status": "validated",
            "priority": "normal",
            "attachment_id": attachment_id,
            "notes": "Documento recebido e validado operacionalmente.",
            "metadata": {
                "validated_by": "test",
            },
        },
        headers=headers,
    )
    assert r_update.status_code == 200
    updated = r_update.json()
    assert updated["status"] == "validated"
    assert updated["priority"] == "normal"
    assert updated["attachment_id"] == attachment_id
    assert updated["checklist_metadata"]["source"] == "case_evidence_checklist_v1"
    assert updated["checklist_metadata"]["validated_by"] == "test"

    r_delete = client.delete(
        f"/api/v1/cases/{case_id}/evidence-checklist/{item_id}",
        headers=headers,
    )
    assert r_delete.status_code == 204

    r_list_after_delete = client.get(f"/api/v1/cases/{case_id}/evidence-checklist", headers=headers)
    assert r_list_after_delete.status_code == 200
    assert r_list_after_delete.json() == []
