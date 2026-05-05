from fastapi.testclient import TestClient
import uuid

from app.main import app
from app.core.settings import settings

client = TestClient(app)


def _auth_headers(monkeypatch):
    monkeypatch.setattr(settings, "ALLOW_SEED_ADMIN", True)
    monkeypatch.setattr(settings, "ADMIN_SEED_TOKEN", "test-seed-token")

    seed_payload = {
        "username": f"admin_edoc_{uuid.uuid4().hex[:8]}@example.com",
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


def test_editable_documents_authenticated_flow(monkeypatch):
    headers = _auth_headers(monkeypatch)

    create_case_payload = {
        "case_number": f"EDOC-{uuid.uuid4().hex[:8]}",
        "title": "Caso de teste do editor persistido",
        "description": "Validação do Editor Jurídico Vivo persistido.",
        "legal_area": "trabalhista",
        "action_type": "Petição Inicial Trabalhista",
        "status": "draft",
    }

    r_case = client.post("/api/v1/cases", json=create_case_payload, headers=headers)
    assert r_case.status_code == 200
    case_id = r_case.json()["id"]

    create_document_payload = {
        "case_id": case_id,
        "area": "trabalhista",
        "document_type": "peticao_inicial",
        "title": "Petição inicial persistida",
        "notes": "Versão inicial criada via teste automatizado.",
        "metadata": {
            "source": "test_editable_documents_flow",
        },
        "sections": [
            {
                "key": "facts",
                "title": "Fatos",
                "content": "A reclamante relata jornada extraordinária habitual.",
                "source": "manual",
                "status": "draft",
                "metadata": {"origin": "test_v1"},
            },
            {
                "key": "requests",
                "title": "Pedidos",
                "content": "Requer pagamento de horas extras e reflexos.",
                "source": "manual",
                "status": "draft",
                "metadata": {"origin": "test_v1"},
            },
        ],
    }

    r_create_doc = client.post(
        "/api/v1/editable-documents",
        json=create_document_payload,
        headers=headers,
    )
    assert r_create_doc.status_code == 200
    created_doc = r_create_doc.json()

    assert created_doc["case_id"] == case_id
    assert created_doc["current_version_number"] == 1
    assert created_doc["status"] == "draft"
    assert len(created_doc["versions"]) == 1

    document_id = created_doc["id"]

    r_list = client.get(
        f"/api/v1/editable-documents/case/{case_id}",
        headers=headers,
    )
    assert r_list.status_code == 200
    listed_docs = r_list.json()
    assert any(doc["id"] == document_id for doc in listed_docs)

    create_version_payload = {
        "approved": True,
        "notes": "Versão 2 revisada e aprovada.",
        "metadata": {
            "source": "test_editable_documents_flow_v2",
            "reviewed_by": "admin",
        },
        "sections": [
            {
                "key": "facts",
                "title": "Fatos",
                "content": "A reclamante relata jornada extraordinária habitual, inclusive aos sábados.",
                "source": "manual",
                "status": "reviewed",
                "metadata": {"origin": "test_v2"},
            },
            {
                "key": "requests",
                "title": "Pedidos",
                "content": "Requer pagamento de horas extras, reflexos e integração nas verbas rescisórias.",
                "source": "manual",
                "status": "reviewed",
                "metadata": {"origin": "test_v2"},
            },
        ],
    }

    r_create_version = client.post(
        f"/api/v1/editable-documents/{document_id}/versions",
        json=create_version_payload,
        headers=headers,
    )
    assert r_create_version.status_code == 200
    created_version = r_create_version.json()

    assert created_version["version_number"] == 2
    assert created_version["approved"] is True

    r_detail = client.get(
        f"/api/v1/editable-documents/{document_id}",
        headers=headers,
    )
    assert r_detail.status_code == 200
    detail = r_detail.json()

    assert detail["id"] == document_id
    assert detail["current_version_number"] == 2
    assert detail["status"] == "approved"
    assert len(detail["versions"]) == 2
    assert detail["versions"][0]["version_number"] == 1
    assert detail["versions"][1]["version_number"] == 2


def test_civel_cobranca_assisted_draft_uses_collection_specific_guardrails(monkeypatch):
    headers = _auth_headers(monkeypatch)

    create_case_payload = {
        "case_number": f"COBRANCA-{uuid.uuid4().hex[:8]}",
        "title": "Cobrança de contrato de prestação de serviços inadimplido",
        "description": (
            "A empresa autora foi contratada para executar serviços de manutenção elétrica "
            "no valor total de R$ 18.500,00. A primeira parcela de R$ 6.500,00 foi paga, "
            "mas duas parcelas vencidas em 25/02/2026 e 05/03/2026 permaneceram inadimplidas, "
            "totalizando saldo contratual de R$ 12.000,00. Há contrato assinado, comprovante "
            "de pagamento parcial, relatório técnico de execução dos serviços, fotografias, "
            "mensagens de WhatsApp com reconhecimento da dívida, notificação extrajudicial "
            "e planilha de cálculo com multa de 2%, juros de 1% ao mês e correção monetária. "
            "O objetivo é propor ação de cobrança contratual, sem pedido de dano moral."
        ),
        "legal_area": "civel",
        "action_type": "Ação de Cobrança",
        "status": "draft",
    }

    r_case = client.post("/api/v1/cases", json=create_case_payload, headers=headers)
    assert r_case.status_code == 200
    case_id = r_case.json()["id"]

    create_document_payload = {
        "case_id": case_id,
        "area": "civel",
        "document_type": "peticao_inicial",
        "title": "Petição Inicial — Ação de Cobrança Contratual",
        "notes": "Documento criado para regressão de guardrails de cobrança.",
        "metadata": {
            "source": "test_civel_cobranca_guardrails",
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
    assert generated["current_version_number"] == 2

    latest_version = max(generated["versions"], key=lambda item: item["version_number"])
    combined_text = "\n".join(
        (section.get("content") or "")
        for section in latest_version["sections"]
    ).lower()

    required_terms = [
        "ação de cobrança",
        "saldo contratual",
        "multa",
        "juros",
        "correção monetária",
        "honorários",
        "contrato",
        "planilha de cálculo",
    ]
    for term in required_terms:
        assert term in combined_text

    forbidden_terms = [
        "ambiental",
        "acústica",
        "acustica",
        "mitigação",
        "mitigacao",
        "obrigação de fazer",
        "obrigacao de fazer",
        "não fazer",
        "nao fazer",
        "cessar a lesão",
        "impactos narrados",
        "reiteração dos impactos",
        "persistência da conduta",
        "probabilidade estimada",
        "probabilidade estimada de êxito",
        "score",
        "/100",
    ]
    for term in forbidden_terms:
        assert term not in combined_text
