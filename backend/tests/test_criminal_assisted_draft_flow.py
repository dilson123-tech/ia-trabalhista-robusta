from fastapi.testclient import TestClient
import uuid

from app.main import app
from app.core.settings import settings

client = TestClient(app)


def _auth_headers(monkeypatch):
    monkeypatch.setattr(settings, "ALLOW_SEED_ADMIN", True)
    monkeypatch.setattr(settings, "ADMIN_SEED_TOKEN", "test-seed-token")

    seed_payload = {
        "username": f"admin_criminal_{uuid.uuid4().hex[:8]}@example.com",
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


def test_criminal_liberdade_provisoria_assisted_draft_flow(monkeypatch):
    headers = _auth_headers(monkeypatch)

    create_case_payload = {
        "case_number": f"CRIM-QA-{uuid.uuid4().hex[:8]}",
        "title": "Pedido de liberdade provisória em prisão em flagrante",
        "description": (
            "Área jurídica: Criminal. "
            "Pessoa presa em flagrante em Joinville/SC, com audiência de custódia realizada. "
            "A defesa pretende avaliar liberdade provisória com ou sem medidas cautelares diversas da prisão. "
            "Documentos disponíveis: boletim de ocorrência, auto de prisão em flagrante, nota de culpa, "
            "ata de audiência de custódia, comprovante de residência e documentos pessoais. "
            "Há testemunha conhecida e necessidade de conferência da decisão de custódia. "
            "O advogado deverá revisar competência, legalidade da prisão, necessidade concreta da custódia "
            "e adequação de medidas cautelares antes de qualquer protocolo."
        ),
        "legal_area": "criminal",
        "action_type": "liberdade_provisoria",
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
    analysis_payload = r_analysis.json()["analysis"]
    technical = analysis_payload["technical"]

    assert technical["legal_area"] == "criminal"
    assert technical["action_type"] == "liberdade_provisoria"

    create_document_payload = {
        "case_id": case_id,
        "area": "criminal",
        "document_type": "pedido_liberdade_provisoria",
        "title": "Pedido de Liberdade Provisória — Minuta Assistida",
        "notes": "Documento criado para validação funcional do Criminal V1.",
        "metadata": {
            "source": "test_criminal_assisted_draft_flow",
            "case_comarca": "JOINVILLE/SC",
            "lawyer_name": "Advogado Responsável",
            "lawyer_oab": "00000",
            "lawyer_uf": "SC",
            "signature_local": "Joinville/SC",
            "signature_date": "25/05/2026",
        },
        "sections": [
            {
                "key": "resumo_fatico",
                "title": "Resumo Fático",
                "content": "",
                "source": "manual",
                "status": "draft",
                "metadata": {},
            },
            {
                "key": "fundamentacao",
                "title": "Fundamentação",
                "content": "",
                "source": "manual",
                "status": "draft",
                "metadata": {},
            },
            {
                "key": "pedidos",
                "title": "Pedidos",
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
    assert generated["area"] == "criminal"
    assert generated["document_type"] == "pedido_liberdade_provisoria"
    assert generated["current_version_number"] == 2
    assert generated["status"] == "draft"

    latest_version = max(generated["versions"], key=lambda item: item["version_number"])
    assert latest_version["approved"] is False
    assert latest_version["version_metadata"]["source"] == "assisted_draft_from_analysis"

    combined_text = "\n".join(
        (section.get("content") or "")
        for section in latest_version["sections"]
    ).lower()

    required_terms = [
        "pedido de liberdade provisória",
        "juízo criminal competente",
        "joinville/sc",
        "prisão em flagrante",
        "audiência de custódia",
        "medidas cautelares",
        "advogado",
        "não representa promessa de resultado",
        "não afirma culpa ou inocência",
        "não deve ser usado externamente sem revisão",
        "nenhuma prova deve ser inventada",
        "boletim de ocorrência",
        "auto de prisão em flagrante",
        "nota de culpa",
        "ata de audiência de custódia",
    ]
    for term in required_terms:
        assert term in combined_text

    forbidden_terms = [
        "fgts",
        "clt",
        "verbas rescisórias",
        "horas extras",
        "insalubridade",
        "periculosidade",
        "reclamação trabalhista",
        "vara do trabalho",
        "direito de vizinhança",
        "poeira",
        "cimento",
        "obrigação de fazer",
        "score",
        "probabilidade estimada",
        "/100",
    ]
    for term in forbidden_terms:
        assert term not in combined_text
