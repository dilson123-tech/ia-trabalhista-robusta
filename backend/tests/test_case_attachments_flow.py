import uuid
from pathlib import Path

from app.core.settings import settings


def _auth_headers(client, monkeypatch):
    monkeypatch.setattr(settings, "ALLOW_SEED_ADMIN", True)
    monkeypatch.setattr(settings, "ADMIN_SEED_TOKEN", "test-seed-token")

    seed_payload = {
        "username": f"admin_attach_{uuid.uuid4().hex[:8]}@example.com",
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


def test_case_attachments_authenticated_flow(client, monkeypatch, tmp_path):
    monkeypatch.setattr(
        settings,
        "CASE_ATTACHMENT_STORAGE_DIR",
        str(tmp_path / "case_attachments"),
    )

    headers = _auth_headers(client, monkeypatch)

    create_case_payload = {
        "case_number": f"ATTACH-{uuid.uuid4().hex[:8]}",
        "title": "Caso real trabalhista com prova documental",
        "description": "Caso usado para validar upload de provas e anexos.",
        "legal_area": "trabalhista",
        "action_type": "Petição Inicial Trabalhista",
        "status": "draft",
    }

    r_case = client.post("/api/v1/cases", json=create_case_payload, headers=headers)
    assert r_case.status_code == 200
    case_id = r_case.json()["id"]

    pdf_bytes = b"%PDF-1.4\n% prova trabalhista fake\n%%EOF\n"

    r_upload = client.post(
        f"/api/v1/cases/{case_id}/attachments",
        headers=headers,
        data={
            "category": "pdf",
            "description": "PDF trabalhista real para análise do advogado",
            "event_date": "2026-05-19",
        },
        files={
            "file": (
                "prova_trabalhista.pdf",
                pdf_bytes,
                "application/pdf",
            )
        },
    )

    assert r_upload.status_code == 200
    uploaded = r_upload.json()

    assert uploaded["case_id"] == case_id
    assert uploaded["original_filename"] == "prova_trabalhista.pdf"
    assert uploaded["mime_type"] == "application/pdf"
    assert uploaded["file_size_bytes"] == len(pdf_bytes)
    assert uploaded["category"] == "pdf"
    assert uploaded["description"] == "PDF trabalhista real para análise do advogado"
    assert uploaded["event_date"] == "2026-05-19"

    attachment_id = uploaded["id"]

    stored_files = list(Path(settings.CASE_ATTACHMENT_STORAGE_DIR).rglob("*.pdf"))
    assert len(stored_files) == 1
    assert stored_files[0].read_bytes() == pdf_bytes

    r_list = client.get(
        f"/api/v1/cases/{case_id}/attachments",
        headers=headers,
    )
    assert r_list.status_code == 200
    items = r_list.json()
    assert len(items) == 1
    assert items[0]["id"] == attachment_id

    r_patch = client.patch(
        f"/api/v1/cases/{case_id}/attachments/{attachment_id}",
        headers=headers,
        json={
            "category": "notificacao",
            "description": "Documento reclassificado para teste",
            "event_date": "2026-05-20",
        },
    )
    assert r_patch.status_code == 200
    patched = r_patch.json()
    assert patched["category"] == "notificacao"
    assert patched["description"] == "Documento reclassificado para teste"
    assert patched["event_date"] == "2026-05-20"

    r_download = client.get(
        f"/api/v1/cases/{case_id}/attachments/{attachment_id}/download",
        headers=headers,
    )
    assert r_download.status_code == 200
    assert r_download.content == pdf_bytes
    assert "prova_trabalhista.pdf" in r_download.headers.get("content-disposition", "")

    r_delete = client.delete(
        f"/api/v1/cases/{case_id}/attachments/{attachment_id}",
        headers=headers,
    )
    assert r_delete.status_code == 204

    r_list_after_delete = client.get(
        f"/api/v1/cases/{case_id}/attachments",
        headers=headers,
    )
    assert r_list_after_delete.status_code == 200
    assert r_list_after_delete.json() == []

    assert list(Path(settings.CASE_ATTACHMENT_STORAGE_DIR).rglob("*.pdf")) == []


def test_case_attachment_rejects_invalid_category(client, monkeypatch, tmp_path):
    monkeypatch.setattr(
        settings,
        "CASE_ATTACHMENT_STORAGE_DIR",
        str(tmp_path / "case_attachments"),
    )

    headers = _auth_headers(client, monkeypatch)

    r_case = client.post(
        "/api/v1/cases",
        json={
            "case_number": f"ATTACH-BAD-{uuid.uuid4().hex[:8]}",
            "title": "Caso para categoria inválida",
            "description": "Validação de categoria de anexo.",
            "legal_area": "trabalhista",
            "action_type": "Petição Inicial Trabalhista",
            "status": "draft",
        },
        headers=headers,
    )
    assert r_case.status_code == 200
    case_id = r_case.json()["id"]

    r_upload = client.post(
        f"/api/v1/cases/{case_id}/attachments",
        headers=headers,
        data={"category": "categoria_inexistente"},
        files={"file": ("teste.pdf", b"fake", "application/pdf")},
    )

    assert r_upload.status_code == 422
    assert "Invalid attachment category" in r_upload.text
