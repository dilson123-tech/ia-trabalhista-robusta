from fastapi.testclient import TestClient
import uuid

from app.main import app
from app.core.settings import settings

client = TestClient(app)


def _auth_headers(monkeypatch):
    from app.api.v1.routes import cases as cases_routes

    monkeypatch.setattr(settings, "ALLOW_SEED_ADMIN", True)
    monkeypatch.setattr(settings, "ADMIN_SEED_TOKEN", "test-seed-token")
    monkeypatch.setattr(settings, "LLM_ANALYSIS_ENABLED", False)
    monkeypatch.setattr(cases_routes, "enforce_plan_limits", lambda *args, **kwargs: None)

    seed_payload = {
        "username": f"admin_aud_ctx_{uuid.uuid4().hex[:8]}@example.com",
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


def test_audiencia_estrategica_uses_party_state_and_attachment_context(monkeypatch, tmp_path):
    monkeypatch.setattr(
        settings,
        "CASE_ATTACHMENT_STORAGE_DIR",
        str(tmp_path / "case_attachments"),
    )

    headers = _auth_headers(monkeypatch)

    create_case_payload = {
        "case_number": f"AUD-CTX-{uuid.uuid4().hex[:8]}",
        "title": "Audiência cível com partes e anexos estruturados",
        "description": (
            "Caso cível de responsabilidade por desaparecimento de carreta. "
            "A descrição inicial não lista todas as testemunhas, para validar o contexto estruturado."
        ),
        "legal_area": "civel",
        "action_type": "Roteiro de audiência",
        "status": "draft",
    }

    r_case = client.post("/api/v1/cases", json=create_case_payload, headers=headers)
    assert r_case.status_code == 200
    case_id = r_case.json()["id"]

    create_party_state_payload = {
        "case_id": case_id,
        "area": "civel",
        "parties": [
            {
                "key": "author_1",
                "name": "PRATIC SIDER",
                "role": "parte autora",
                "party_type": "company",
                "status": "active",
                "is_original_party": True,
                "metadata": {"description": "empresa locadora da carreta"},
            },
            {
                "key": "defendant_1",
                "name": "Dilson Pereira",
                "role": "parte ré",
                "party_type": "person",
                "status": "active",
                "is_original_party": True,
                "metadata": {"description": "responsável formal pela locação"},
            },
            {
                "key": "witness_edson",
                "name": "Edson Estevão",
                "role": "testemunha",
                "party_type": "person",
                "status": "active",
                "is_original_party": True,
                "metadata": {"witness_type": "usuário prático da carreta"},
            },
            {
                "key": "witness_rosangela",
                "name": "Rosangela de Lourdes Siqueira",
                "role": "testemunha",
                "party_type": "person",
                "status": "active",
                "is_original_party": True,
                "metadata": {"witness_type": "testemunha sobre tratativas"},
            },
        ],
        "metadata": {
            "source": "test_audiencia_context_snapshot_v2",
            "case_comarca": "Joinville/SC",
        },
    }

    r_party_state = client.post(
        "/api/v1/case-party-states",
        json=create_party_state_payload,
        headers=headers,
    )
    assert r_party_state.status_code == 200
    state_id = r_party_state.json()["id"]

    r_relationship = client.post(
        f"/api/v1/case-party-states/{state_id}/relationships",
        json={
            "source_party_key": "defendant_1",
            "target_party_key": "witness_edson",
            "relationship_type": "locacao_em_interesse_de_terceiro",
            "status": "active",
            "metadata": {"description": "Dilson teria formalizado locação a pedido de Edson."},
        },
        headers=headers,
    )
    assert r_relationship.status_code == 200

    r_upload = client.post(
        f"/api/v1/cases/{case_id}/attachments",
        headers=headers,
        data={
            "category": "pdf",
            "description": "Boletim de ocorrência sobre furto/desaparecimento da carreta.",
            "event_date": "2026-05-19",
        },
        files={
            "file": (
                "boletim_ocorrencia_furto_carreta.pdf",
                b"%PDF-1.4\n% boletim fake\n%%EOF\n",
                "application/pdf",
            )
        },
    )
    assert r_upload.status_code == 200

    create_document_payload = {
        "case_id": case_id,
        "area": "civel",
        "document_type": "audiencia_estrategica",
        "title": "Roteiro de Audiência Estratégica — Contexto V2",
        "notes": "Documento criado para validar uso de partes e anexos no contexto da audiência.",
        "metadata": {
            "source": "test_audiencia_context_snapshot_v2",
            "display_title": "Roteiro de Audiência Estratégica — Contexto V2",
        },
        "sections": [
            {
                "key": "placeholder",
                "title": "Rascunho inicial",
                "content": "",
                "source": "manual",
                "status": "draft",
                "metadata": {},
            },
        ],
    }

    r_create_doc = client.post(
        "/api/v1/editable-documents",
        json=create_document_payload,
        headers=headers,
    )
    assert r_create_doc.status_code == 200
    document_id = r_create_doc.json()["id"]

    r_generate = client.post(
        f"/api/v1/editable-documents/{document_id}/generate-assisted-draft",
        headers=headers,
    )
    assert r_generate.status_code == 200

    generated = r_generate.json()
    latest_version = max(generated["versions"], key=lambda item: item["version_number"])
    combined_text = "\n".join(
        (section.get("content") or "")
        for section in latest_version["sections"]
    ).lower()

    required_terms = [
        "contexto estruturado adicional identificado no caso",
        "partes/pessoas ativas cadastradas no caso",
        "pratic sider",
        "dilson pereira",
        "edson estevão",
        "rosangela de lourdes siqueira",
        "relações entre partes/pessoas",
        "locacao_em_interesse_de_terceiro",
        "anexos/provas cadastrados no caso",
        "boletim_ocorrencia_furto_carreta.pdf",
        "boletim de ocorrência sobre furto/desaparecimento da carreta",
        "rosangela de lourdes siqueira:",
    ]

    for term in required_terms:
        assert term in combined_text

    assert "policial militar / agente da abordagem:" not in combined_text
    assert "reclamante / empregado:" not in combined_text
