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
        "username": f"admin_prev_aud_{uuid.uuid4().hex[:8]}@example.com",
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


def test_previdenciario_bpc_loas_audiencia_estrategica_generates_approves_and_exports_pdf(monkeypatch, tmp_path):
    monkeypatch.setattr(
        settings,
        "CASE_ATTACHMENT_STORAGE_DIR",
        str(tmp_path / "case_attachments"),
    )

    headers = _auth_headers(monkeypatch)

    create_case_payload = {
        "case_number": f"PREV-BPC-QA-{uuid.uuid4().hex[:8]}",
        "title": "QA Previdenciário — Audiência estratégica BPC/LOAS",
        "description": (
            "Área jurídica: Previdenciário/BPC-LOAS. "
            "Caso envolve requerente em situação de vulnerabilidade, deficiência ou impedimento de longo prazo, "
            "renda familiar baixa, CadÚnico, NIS, laudos médicos, receitas, exames, gastos com remédios, "
            "familiar cuidador, avaliação social, perícia médica e indeferimento administrativo do INSS. "
            "O advogado deverá revisar grupo familiar, renda per capita, barreiras sociais, incapacidade funcional, "
            "documentos médicos, estudo social, rotina diária, dependência de terceiros e prova testemunhal."
        ),
        "legal_area": "previdenciário",
        "action_type": "bpc_loas",
        "status": "draft",
    }

    r_case = client.post("/api/v1/cases", json=create_case_payload, headers=headers)
    assert r_case.status_code == 200
    case_id = r_case.json()["id"]

    create_party_state_payload = {
        "case_id": case_id,
        "area": "previdenciário",
        "parties": [
            {
                "key": "claimant_1",
                "name": "Ana Requerente QA",
                "role": "requerente segurada",
                "party_type": "person",
                "status": "active",
                "is_original_party": True,
                "metadata": {"description": "requerente de BPC/LOAS com vulnerabilidade social"},
            },
            {
                "key": "caregiver_1",
                "name": "Carlos Cuidador QA",
                "role": "familiar cuidador",
                "party_type": "person",
                "status": "active",
                "is_original_party": True,
                "metadata": {"description": "familiar que acompanha rotina, consultas e medicação"},
            },
            {
                "key": "doctor_1",
                "name": "Dra. Médica Assistente QA",
                "role": "médico assistente",
                "party_type": "person",
                "status": "active",
                "is_original_party": True,
                "metadata": {"description": "profissional que emitiu laudo médico"},
            },
            {
                "key": "inss_1",
                "name": "INSS QA",
                "role": "autarquia previdenciária",
                "party_type": "public_entity",
                "status": "active",
                "is_original_party": True,
                "metadata": {"description": "responsável pelo indeferimento administrativo"},
            },
        ],
        "metadata": {
            "source": "test_previdenciario_bpc_loas_audiencia_estrategica_flow",
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
            "source_party_key": "caregiver_1",
            "target_party_key": "claimant_1",
            "relationship_type": "cuidado_diario_e_dependencia_funcional",
            "status": "active",
            "metadata": {"description": "familiar afirma acompanhar medicação, consultas e rotina diária."},
        },
        headers=headers,
    )
    assert r_relationship.status_code == 200

    r_upload = client.post(
        f"/api/v1/cases/{case_id}/attachments",
        headers=headers,
        data={
            "category": "pdf",
            "description": "Laudo médico, CadÚnico e comprovantes de renda familiar para BPC/LOAS.",
            "event_date": "2026-05-30",
        },
        files={
            "file": (
                "laudo_medico_cadunico_renda_bpc_loas.pdf",
                b"%PDF-1.4\n% previdenciario fake\n%%EOF\n",
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
    assert technical["legal_area"] in {"previdenciário", "previdenciario"}

    create_document_payload = {
        "case_id": case_id,
        "area": "previdenciário",
        "document_type": "audiencia_estrategica",
        "title": "Roteiro de Audiência Estratégica Previdenciário/BPC-LOAS — QA",
        "notes": "Documento criado para QA funcional da audiência estratégica previdenciária.",
        "metadata": {
            "source": "test_previdenciario_bpc_loas_audiencia_estrategica_flow",
            "display_title": "Roteiro de Audiência Estratégica Previdenciário/BPC-LOAS — QA",
            "case_comarca": "JOINVILLE/SC",
            "lawyer_name": "Advogado Responsável",
            "lawyer_oab": "00000",
            "lawyer_uf": "SC",
            "signature_local": "Joinville/SC",
            "signature_date": "30/05/2026",
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
    assert generated["area"] == "previdenciário"
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
        "requerente / segurado",
        "familiar cuidador / responsável pela rotina",
        "representante legal / procurador",
        "médico assistente / profissional de saúde",
        "perito médico",
        "assistente social / avaliador social",
        "servidor / representante do inss",
        "testemunha sobre rotina, incapacidade e vulnerabilidade",
        "bpc/loas",
        "cadúnico",
        "renda familiar",
        "laudos médicos",
        "perícia médica",
        "avaliação social",
        "benefício assistencial",
        "contexto estruturado adicional identificado no caso",
        "ana requerente qa",
        "carlos cuidador qa",
        "dra. médica assistente qa",
        "inss qa",
        "cuidado_diario_e_dependencia_funcional",
        "laudo_medico_cadunico_renda_bpc_loas.pdf",
        "laudo médico, cadúnico e comprovantes de renda familiar para bpc/loas",
        "material de apoio estratégico",
        "revisão e decisão final do advogado",
    ]

    for term in required_terms:
        assert term in combined_text

    forbidden_terms = [
        "genitor / requerente",
        "consumidor / autor",
        "fornecedor / empresa ré",
        "reclamante / empregado",
        "preposto / representante da reclamada",
        "vítima / ofendido",
        "policial militar / agente da abordagem",
        "representante da pratic sider",
        "edson estevão",
        "locação da carreta",
    ]

    for term in forbidden_terms:
        assert term not in combined_text

    approve_payload = {
        "approved": True,
        "notes": "Versão QA aprovada para exportação do roteiro de audiência estratégica previdenciária.",
        "metadata": {
            "source": "test_previdenciario_bpc_loas_audiencia_estrategica_flow",
            "based_on_version_number": generated_version["version_number"],
            "qa_checkpoint": "QA_PREVIDENCIARIO_BPC_LOAS_AUDIENCIA_ESTRATEGICA_FLOW_OK",
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
