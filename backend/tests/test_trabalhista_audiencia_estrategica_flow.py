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
        "username": f"admin_lab_aud_{uuid.uuid4().hex[:8]}@example.com",
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


def test_trabalhista_audiencia_estrategica_generates_approves_and_exports_pdf(monkeypatch):
    headers = _auth_headers(monkeypatch)

    create_case_payload = {
        "case_number": f"TRAB-AUDIENCIA-QA-{uuid.uuid4().hex[:8]}",
        "title": "QA Trabalhista — Audiência estratégica de horas extras e verbas",
        "description": (
            "Área jurídica: Trabalhista. "
            "Reclamante ajuíza reclamação trabalhista contra reclamada alegando jornada superior à registrada, "
            "supressão parcial de intervalo intrajornada, diferenças de horas extras, reflexos em DSR, férias, "
            "13º salário, FGTS e verbas rescisórias. "
            "O caso envolve controles de ponto, holerites, TRCT, extrato analítico do FGTS, mensagens com gestor, "
            "preposto da empresa, testemunhas do reclamante e da reclamada, RH responsável por folha e ponto, "
            "além de possível discussão sobre EPI, insalubridade e documentos de segurança do trabalho. "
            "O advogado deverá revisar jornada real, validade dos controles de ponto, banco de horas, pagamento de verbas, "
            "prova testemunhal, documentos rescisórios e riscos de perguntas que possam reforçar a tese contrária."
        ),
        "legal_area": "trabalhista",
        "action_type": "horas_extras",
        "status": "draft",
    }

    r_case = client.post("/api/v1/cases", json=create_case_payload, headers=headers)
    assert r_case.status_code == 200
    case_id = r_case.json()["id"]

    r_analysis = client.get(
        f"/api/v1/cases/{case_id}/analysis?force=true",
        headers=headers,
    )
    assert r_analysis.status_code == 200
    technical = r_analysis.json()["analysis"]["technical"]

    assert technical["legal_area"] == "trabalhista"

    create_document_payload = {
        "case_id": case_id,
        "area": "trabalhista",
        "document_type": "audiencia_estrategica",
        "title": "Roteiro de Audiência Estratégica Trabalhista — QA",
        "notes": "Documento criado para QA funcional da audiência estratégica trabalhista.",
        "metadata": {
            "source": "test_trabalhista_audiencia_estrategica_flow",
            "display_title": "Roteiro de Audiência Estratégica Trabalhista — QA",
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
    assert generated["area"] == "trabalhista"
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
        "reclamante / empregado",
        "preposto / representante da reclamada",
        "testemunha do reclamante",
        "testemunha da reclamada",
        "gestor / encarregado",
        "rh / responsável por folha, ponto e rescisão",
        "técnico de segurança / medicina do trabalho",
        "perito / responsável por laudo trabalhista",
        "controle de ponto",
        "fgts",
        "verbas rescisórias",
        "risco ocupacional",
        "material de apoio estratégico",
        "revisão e decisão final do advogado",
    ]

    for term in required_terms:
        assert term in combined_text

    forbidden_terms = [
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
        "notes": "Versão QA aprovada para exportação do roteiro de audiência estratégica trabalhista.",
        "metadata": {
            "source": "test_trabalhista_audiencia_estrategica_flow",
            "based_on_version_number": generated_version["version_number"],
            "qa_checkpoint": "QA_TRABALHISTA_AUDIENCIA_ESTRATEGICA_FLOW_OK",
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
