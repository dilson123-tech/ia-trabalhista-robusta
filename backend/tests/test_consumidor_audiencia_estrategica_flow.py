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
        "username": f"admin_cons_aud_{uuid.uuid4().hex[:8]}@example.com",
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


def test_consumidor_audiencia_estrategica_generates_approves_and_exports_pdf(monkeypatch, tmp_path):
    monkeypatch.setattr(
        settings,
        "CASE_ATTACHMENT_STORAGE_DIR",
        str(tmp_path / "case_attachments"),
    )

    headers = _auth_headers(monkeypatch)

    create_case_payload = {
        "case_number": f"CONS-AUDIENCIA-QA-{uuid.uuid4().hex[:8]}",
        "title": "QA Consumidor — Audiência estratégica de cobrança indevida e negativação",
        "description": (
            "Área jurídica: Consumidor. "
            "Consumidor ajuíza ação contra banco/fornecedor por cobrança indevida, negativação e falha de atendimento. "
            "O caso envolve contrato contestado, faturas, protocolos de SAC, reclamação em ouvidoria, prints de aplicativo, "
            "comprovantes de pagamento, inscrição em cadastro restritivo e pedido de baixa da negativação. "
            "O advogado deverá revisar relação de consumo, origem da dívida, regularidade da contratação, comunicação prévia, "
            "tentativa administrativa de solução, dano material, dano moral e documentos que comprovem a falha do fornecedor."
        ),
        "legal_area": "consumidor",
        "action_type": "cobranca_indevida_negativacao",
        "status": "draft",
    }

    r_case = client.post("/api/v1/cases", json=create_case_payload, headers=headers)
    assert r_case.status_code == 200
    case_id = r_case.json()["id"]

    create_party_state_payload = {
        "case_id": case_id,
        "area": "consumidor",
        "parties": [
            {
                "key": "consumer_1",
                "name": "Cliente Consumidor QA",
                "role": "consumidor autor",
                "party_type": "person",
                "status": "active",
                "is_original_party": True,
                "metadata": {"description": "consumidor que contesta cobrança e negativação"},
            },
            {
                "key": "supplier_1",
                "name": "Banco Alfa QA",
                "role": "fornecedor réu",
                "party_type": "company",
                "status": "active",
                "is_original_party": True,
                "metadata": {"description": "instituição financeira responsável pela cobrança"},
            },
            {
                "key": "support_agent_1",
                "name": "Atendente SAC QA",
                "role": "atendente",
                "party_type": "person",
                "status": "active",
                "is_original_party": True,
                "metadata": {"description": "atendente que registrou protocolo administrativo"},
            },
        ],
        "metadata": {
            "source": "test_consumidor_audiencia_estrategica_flow",
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
            "source_party_key": "consumer_1",
            "target_party_key": "supplier_1",
            "relationship_type": "relacao_de_consumo_bancaria",
            "status": "active",
            "metadata": {"description": "relação de consumo discutida por cobrança e negativação."},
        },
        headers=headers,
    )
    assert r_relationship.status_code == 200

    r_upload = client.post(
        f"/api/v1/cases/{case_id}/attachments",
        headers=headers,
        data={
            "category": "pdf",
            "description": "Comprovante de negativação e protocolos de atendimento do consumidor.",
            "event_date": "2026-05-29",
        },
        files={
            "file": (
                "protocolo_sac_negativacao_consumidor.pdf",
                b"%PDF-1.4\n% consumidor fake\n%%EOF\n",
                "application/pdf",
            )
        },
    )
    assert r_upload.status_code == 200

    r_analysis = client.get(
        f"/api/v1/cases/{case_id}/analysis?force=true",
        headers=headers,
    )
    assert r_analysis.status_code == 200
    technical = r_analysis.json()["analysis"]["technical"]
    assert technical["legal_area"] == "consumidor"

    create_document_payload = {
        "case_id": case_id,
        "area": "consumidor",
        "document_type": "audiencia_estrategica",
        "title": "Roteiro de Audiência Estratégica Consumidor — QA",
        "notes": "Documento criado para QA funcional da audiência estratégica consumidor.",
        "metadata": {
            "source": "test_consumidor_audiencia_estrategica_flow",
            "display_title": "Roteiro de Audiência Estratégica Consumidor — QA",
            "case_comarca": "JOINVILLE/SC",
            "lawyer_name": "Advogado Responsável",
            "lawyer_oab": "00000",
            "lawyer_uf": "SC",
            "signature_local": "Joinville/SC",
            "signature_date": "29/05/2026",
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
    assert generated["area"] == "consumidor"
    assert generated["document_type"] == "audiencia_estrategica"
    assert generated["current_version_number"] == 2
    assert generated["status"] == "draft"

    generated_version = max(generated["versions"], key=lambda item: item["version_number"])
    assert generated_version["version_number"] == 2
    assert generated_version["approved"] is False

    sections = generated_version["sections"]
    section_keys = {section.get("key") for section in sections}

    assert "sintese_tese_audiencia" in section_keys
    assert "pontos_provar" in section_keys
    assert "perguntas_pessoas_identificadas" in section_keys
    assert "perguntas_repetitivas_perigosas" in section_keys
    assert "perguntas_condicionais" in section_keys
    assert "versao_curta" in section_keys
    assert "pontos_confirmar_advogado" in section_keys

    combined_text = "\n".join(
        (section.get("content") or "")
        for section in sections
    ).lower()

    required_terms = [
        "consumidor / autor",
        "fornecedor / empresa ré",
        "atendente / suporte / sac / ouvidoria",
        "representante comercial / vendedor / loja",
        "testemunha do consumidor",
        "testemunha do fornecedor",
        "responsável financeiro / cobrança / negativação",
        "técnico / assistência / perito do produto ou serviço",
        "cobrança indevida",
        "negativação",
        "protocolo",
        "relação de consumo",
        "contexto estruturado adicional identificado no caso",
        "cliente consumidor qa",
        "banco alfa qa",
        "atendente sac qa",
        "relacao_de_consumo_bancaria",
        "protocolo_sac_negativacao_consumidor.pdf",
        "comprovante de negativação e protocolos de atendimento do consumidor",
        "material de apoio estratégico",
        "revisão e decisão final do advogado",
    ]

    for term in required_terms:
        assert term in combined_text

    forbidden_terms = [
        "reclamante / empregado",
        "preposto / representante da reclamada",
        "vítima / ofendido",
        "policial militar / agente da abordagem",
        "delegado / autoridade policial",
        "acusado / réu",
        "representante da pratic sider",
        "edson estevão",
        "rosangela de lourdes siqueira",
        "locação da carreta",
    ]

    for term in forbidden_terms:
        assert term not in combined_text

    approve_payload = {
        "approved": True,
        "notes": "Versão QA aprovada para exportação do roteiro de audiência estratégica consumidor.",
        "metadata": {
            "source": "test_consumidor_audiencia_estrategica_flow",
            "based_on_version_number": generated_version["version_number"],
            "qa_checkpoint": "QA_CONSUMIDOR_AUDIENCIA_ESTRATEGICA_FLOW_OK",
        },
        "sections": sections,
    }

    r_approve = client.post(
        f"/api/v1/editable-documents/{document_id}/versions",
        json=approve_payload,
        headers=headers,
    )
    assert r_approve.status_code == 200
    approved_version = r_approve.json()

    assert approved_version["approved"] is True
    assert approved_version["version_number"] == 3

    r_detail = client.get(
        f"/api/v1/editable-documents/{document_id}",
        headers=headers,
    )
    assert r_detail.status_code == 200
    detail = r_detail.json()

    assert detail["status"] == "approved"
    assert detail["current_version_number"] == 3

    r_pdf = client.get(
        f"/api/v1/editable-documents/{document_id}/export/pdf",
        headers=headers,
    )
    assert r_pdf.status_code == 200
    assert r_pdf.headers["content-type"] == "application/pdf"
    assert r_pdf.content.startswith(b"%PDF")
    assert len(r_pdf.content) > 1000
