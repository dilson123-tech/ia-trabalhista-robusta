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
        "username": f"admin_civamb_aud_{uuid.uuid4().hex[:8]}@example.com",
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


def test_civil_ambiental_audiencia_estrategica_generates_approves_and_exports_pdf(monkeypatch, tmp_path):
    monkeypatch.setattr(
        settings,
        "CASE_ATTACHMENT_STORAGE_DIR",
        str(tmp_path / "case_attachments"),
    )

    headers = _auth_headers(monkeypatch)

    create_case_payload = {
        "case_number": f"CIV-AMB-AUDIENCIA-QA-{uuid.uuid4().hex[:8]}",
        "title": "QA Civil/Ambiental — Audiência estratégica de dano de vizinhança e dano ambiental",
        "description": (
            "Área jurídica: Civil/Ambiental. "
            "Caso envolve responsabilidade civil ambiental, dano de vizinhança, ruído excessivo, fumaça, odor, "
            "infiltração, descarte irregular e possível dano ambiental causado por empresa vizinha. "
            "Há fotos, vídeos, laudo técnico, auto de fiscalização, reclamações de moradores e registros de órgão público. "
            "O advogado deverá revisar nexo causal, extensão do dano, prova técnica, testemunhas, obrigação de fazer, "
            "obrigação de não fazer, reparação, indenização e medidas para cessar o dano."
        ),
        "legal_area": "civil_ambiental",
        "action_type": "responsabilidade_civil_ambiental_dano_vizinhanca",
        "status": "draft",
    }

    r_case = client.post("/api/v1/cases", json=create_case_payload, headers=headers)
    assert r_case.status_code == 200
    case_id = r_case.json()["id"]

    create_party_state_payload = {
        "case_id": case_id,
        "area": "civil_ambiental",
        "parties": [
            {
                "key": "author_1",
                "name": "Moradora Prejudicada QA",
                "role": "autora prejudicada",
                "party_type": "person",
                "status": "active",
                "is_original_party": True,
                "metadata": {"description": "moradora afetada por ruído, fumaça, odor e infiltração"},
            },
            {
                "key": "company_1",
                "name": "Empresa Vizinha QA",
                "role": "ré causadora alegada do dano",
                "party_type": "company",
                "status": "active",
                "is_original_party": True,
                "metadata": {"description": "empresa apontada como origem do dano ambiental e de vizinhança"},
            },
            {
                "key": "neighbor_1",
                "name": "Vizinho Testemunha QA",
                "role": "vizinho comunidade afetada",
                "party_type": "person",
                "status": "active",
                "is_original_party": True,
                "metadata": {"description": "vizinho que presenciou ruído, fumaça e odor recorrentes"},
            },
            {
                "key": "expert_1",
                "name": "Engenheiro Ambiental QA",
                "role": "perito técnico ambiental",
                "party_type": "person",
                "status": "active",
                "is_original_party": True,
                "metadata": {"description": "técnico responsável por laudo ambiental e de engenharia"},
            },
            {
                "key": "inspection_1",
                "name": "Fiscalização Ambiental QA",
                "role": "órgão público fiscalização",
                "party_type": "public_entity",
                "status": "active",
                "is_original_party": True,
                "metadata": {"description": "órgão público que lavrou auto de fiscalização"},
            },
        ],
        "metadata": {
            "source": "test_civil_ambiental_audiencia_estrategica_flow",
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
            "source_party_key": "company_1",
            "target_party_key": "author_1",
            "relationship_type": "origem_alegada_do_dano_ambiental_e_vizinhanca",
            "status": "active",
            "metadata": {
                "description": "autora afirma que empresa vizinha gera ruído, fumaça, odor e infiltração recorrentes."
            },
        },
        headers=headers,
    )
    assert r_relationship.status_code == 200

    r_upload = client.post(
        f"/api/v1/cases/{case_id}/attachments",
        headers=headers,
        data={
            "category": "pdf",
            "description": "Laudo técnico, fotos, vídeos e auto de fiscalização sobre ruído, fumaça, odor e infiltração.",
            "event_date": "2026-05-31",
        },
        files={
            "file": (
                "auto_fiscalizacao_laudo_ruido_fumaca.pdf",
                b"%PDF-1.4\n% civil ambiental fake\n%%EOF\n",
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
    assert technical["legal_area"] in {"civil_ambiental", "ambiental", "cível", "civel"}

    create_document_payload = {
        "case_id": case_id,
        "area": "civil_ambiental",
        "document_type": "audiencia_estrategica",
        "title": "Roteiro de Audiência Estratégica Civil/Ambiental — QA",
        "notes": "Documento criado para QA funcional da audiência estratégica civil/ambiental.",
        "metadata": {
            "source": "test_civil_ambiental_audiencia_estrategica_flow",
            "display_title": "Roteiro de Audiência Estratégica Civil/Ambiental — QA",
            "case_comarca": "JOINVILLE/SC",
            "lawyer_name": "Advogado Responsável",
            "lawyer_oab": "00000",
            "lawyer_uf": "SC",
            "signature_local": "Joinville/SC",
            "signature_date": "31/05/2026",
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
    assert generated["area"] == "civil_ambiental"
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
        "autor / prejudicado",
        "réu / causador alegado do dano",
        "testemunha do autor",
        "testemunha da defesa",
        "perito / técnico ambiental ou de engenharia",
        "fiscalização / órgão público",
        "vizinho / comunidade afetada",
        "responsável por documentos, fotos, vídeos ou laudos",
        "responsabilidade civil",
        "dano ambiental",
        "dano de vizinhança",
        "nexo causal",
        "fiscalização",
        "perícia",
        "laudo",
        "obrigação de fazer",
        "não fazer",
        "contexto estruturado adicional identificado no caso",
        "moradora prejudicada qa",
        "empresa vizinha qa",
        "vizinho testemunha qa",
        "engenheiro ambiental qa",
        "fiscalização ambiental qa",
        "origem_alegada_do_dano_ambiental_e_vizinhanca",
        "auto_fiscalizacao_laudo_ruido_fumaca.pdf",
        "laudo técnico, fotos, vídeos e auto de fiscalização sobre ruído, fumaça, odor e infiltração",
        "material de apoio estratégico",
        "revisão e decisão final do advogado",
    ]

    for term in required_terms:
        assert term in combined_text

    forbidden_terms = [
        "requerente / segurado",
        "familiar cuidador / responsável pela rotina",
        "genitor / requerente",
        "genitor / requerido",
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
        "notes": "Versão QA aprovada para exportação do roteiro de audiência estratégica civil/ambiental.",
        "metadata": {
            "source": "test_civil_ambiental_audiencia_estrategica_flow",
            "based_on_version_number": generated_version["version_number"],
            "qa_checkpoint": "QA_CIVIL_AMBIENTAL_AUDIENCIA_ESTRATEGICA_FLOW_OK",
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
