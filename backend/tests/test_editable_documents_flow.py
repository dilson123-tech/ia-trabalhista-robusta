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
            "A empresa DLP Manutenção e Serviços Ltda. foi contratada pela empresa Restaurante Mar Azul Ltda. "
            "para executar serviços de manutenção elétrica preventiva e corretiva no estabelecimento comercial "
            "localizado em Itapoá/SC. "
            "O contrato foi firmado em 10/02/2026, no valor total de R$ 18.500,00, com pagamento previsto em "
            "três parcelas: R$ 6.500,00 na assinatura do contrato, R$ 6.000,00 após a conclusão da primeira etapa "
            "e R$ 6.000,00 na entrega final dos serviços. "
            "A contratada executou integralmente os serviços entre 12/02/2026 e 28/02/2026, incluindo troca de "
            "disjuntores, revisão do quadro elétrico, substituição de fiação danificada, instalação de tomadas "
            "industriais e emissão de relatório técnico de conclusão. "
            "A primeira parcela de R$ 6.500,00 foi paga em 10/02/2026. Porém, as duas parcelas restantes, "
            "vencidas em 25/02/2026 e 05/03/2026, não foram pagas, totalizando dívida principal de R$ 12.000,00. "
            "A devedora reconheceu a dívida por mensagens de WhatsApp enviadas em 08/03/2026 e 15/03/2026, "
            "alegando dificuldades financeiras e prometendo pagamento até 20/03/2026, o que não ocorreu. "
            "Em 25/03/2026, foi enviada notificação extrajudicial por e-mail e WhatsApp, concedendo prazo de "
            "cinco dias para pagamento. A notificação foi recebida, mas não houve quitação nem proposta formal "
            "de acordo. "
            "Documentos disponíveis: contrato assinado, comprovante de pagamento parcial, relatório técnico, "
            "fotografias, mensagens, notificação extrajudicial, e-mails e planilha de cálculo. "
            "Pedido pretendido: propor ação de cobrança contratual, sem pedido de dano moral. "
            "Observação estratégica: a prova documental é considerada forte."
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
    petition_sections = [
        section
        for section in latest_version["sections"]
        if "checklist" not in (section.get("key") or "").lower()
        and "checklist" not in (section.get("title") or "").lower()
    ]

    combined_text = "\n".join(
        (section.get("content") or "")
        for section in petition_sections
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
        "dlp manutenção e serviços",
        "restaurante mar azul",
        "itapoá/sc",
        "r$ 12.000,00",
        "pessoa jurídica de direito privado",
        "vara cível",
        "conjunto probatório documental robusto",
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
        "documentos disponíveis",
        "pedido pretendido",
        "observação estratégica",
        "estratégia jurídica sugerida",
        "estratégia sugerida",
        "lacunas probatórias",
        "viabilidade moderada",
        "risco baixo",
        "complexidade baixa",
        "título executivo extrajudicial probatório",
        "titulo executivo extrajudicial probatorio",
        "nome completo da parte autora",
        "comarca a definir",
        "fgts",
        "clt",
        "verbas rescisórias",
        "horas extras",
        "insalubridade",
        "periculosidade",
        "reclamação trabalhista",
        "vara do trabalho",
        "reclamante",
        "reclamada",
        "r$ 12.000,00.,",
    ]
    for term in forbidden_terms:
        assert term not in combined_text


def test_trabalhista_insalubridade_assisted_draft_uses_labor_template(monkeypatch):
    headers = _auth_headers(monkeypatch)

    create_case_payload = {
        "case_number": f"TRAB-INSAL-{uuid.uuid4().hex[:8]}",
        "title": "Adicional de insalubridade/periculosidade — setor de fusão",
        "description": (
            "Parte reclamante trabalhou para Tupy S.A., em Joinville/SC, no setor de fusão, "
            "com processo produtivo envolvendo metal em fusão e exposição a calor intenso. "
            "O período trabalhado foi de fevereiro de 2024 a julho de 2024, com salário de "
            "R$ 2.200,00. A pretensão envolve adicional de insalubridade por calor e, "
            "subsidiariamente, periculosidade, com necessidade de PPP, LTCAT, PGR, PCMSO, "
            "ficha de EPI, perícia técnica, prova testemunhal e reflexos em férias, 13º e FGTS."
        ),
        "legal_area": "trabalhista",
        "action_type": "Reclamação trabalhista — adicional de insalubridade/periculosidade",
        "status": "draft",
    }

    r_case = client.post("/api/v1/cases", json=create_case_payload, headers=headers)
    assert r_case.status_code == 200
    case_id = r_case.json()["id"]

    create_document_payload = {
        "case_id": case_id,
        "area": "trabalhista",
        "document_type": "peticao_inicial",
        "title": "Reclamação Trabalhista — Adicional de Insalubridade/Periculosidade",
        "notes": "Documento criado para regressão de template trabalhista.",
        "metadata": {"source": "test_trabalhista_insalubridade_template"},
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
    latest_version = max(generated["versions"], key=lambda item: item["version_number"])
    combined_text = "\\n".join(
        (section.get("content") or "")
        for section in latest_version["sections"]
    ).lower()

    required_terms = [
        "vara do trabalho",
        "reclamação trabalhista",
        "insalubridade",
        "periculosidade",
        "perícia técnica",
        "ppp",
        "ltcat",
        "pgr",
        "pcmso",
        "epi",
        "fgts",
        "13º",
    ]
    for term in required_terms:
        assert term in combined_text

    forbidden_terms = [
        "juiz(a) de direito",
        "vara cível",
        "varas cíveis",
        "ação de cobrança",
        "saldo contratual",
        "alfa reformas",
        "beta comércio",
    ]
    for term in forbidden_terms:
        assert term not in combined_text



def test_new_draft_version_becomes_current_even_when_approved_version_exists(monkeypatch):
    headers = _auth_headers(monkeypatch)

    create_case_payload = {
        "case_number": f"EDITOR-DRAFT-CURRENT-{uuid.uuid4().hex[:8]}",
        "title": "Caso para testar versão draft atual",
        "description": "Caso de teste para validar fluxo de versões aprovadas e rascunhos editáveis.",
        "legal_area": "consumidor",
        "action_type": "Petição Inicial",
        "status": "draft",
    }

    r_case = client.post("/api/v1/cases", json=create_case_payload, headers=headers)
    assert r_case.status_code == 200
    case_id = r_case.json()["id"]

    create_document_payload = {
        "case_id": case_id,
        "area": "consumidor",
        "document_type": "peticao_inicial",
        "title": "Petição Inicial — Teste de versão atual",
        "notes": "Documento criado para regressão de versão atual.",
        "metadata": {"source": "test_new_draft_current"},
        "sections": [
            {
                "key": "resumo_fatico",
                "title": "Resumo Fático",
                "content": "Resumo inicial.",
                "source": "manual",
                "status": "draft",
                "metadata": {},
            },
            {
                "key": "pedidos",
                "title": "Pedidos",
                "content": "Pedidos iniciais.",
                "source": "manual",
                "status": "draft",
                "metadata": {},
            },
        ],
    }

    r_doc = client.post("/api/v1/editable-documents", json=create_document_payload, headers=headers)
    assert r_doc.status_code == 200
    document_id = r_doc.json()["id"]

    approve_payload = {
        "approved": True,
        "notes": "Versão aprovada para exportação.",
        "metadata": {"source": "test_approval"},
        "sections": [
            {
                "key": "resumo_fatico",
                "title": "Resumo Fático",
                "content": "Resumo aprovado.",
                "source": "manual",
                "status": "reviewed",
                "metadata": {},
            },
            {
                "key": "pedidos",
                "title": "Pedidos",
                "content": "Pedidos aprovados.",
                "source": "manual",
                "status": "reviewed",
                "metadata": {},
            },
        ],
    }

    r_approved = client.post(
        f"/api/v1/editable-documents/{document_id}/versions",
        json=approve_payload,
        headers=headers,
    )
    assert r_approved.status_code == 200
    assert r_approved.json()["version_number"] == 2
    assert r_approved.json()["approved"] is True

    draft_payload = {
        "approved": False,
        "notes": "Nova versão draft para edição após aprovação.",
        "metadata": {"source": "test_new_draft_after_approval"},
        "sections": [
            {
                "key": "resumo_fatico",
                "title": "Resumo Fático",
                "content": "Resumo editável v3.",
                "source": "manual",
                "status": "draft",
                "metadata": {},
            },
            {
                "key": "pedidos",
                "title": "Pedidos",
                "content": "Pedidos editáveis v3.",
                "source": "manual",
                "status": "draft",
                "metadata": {},
            },
        ],
    }

    r_draft = client.post(
        f"/api/v1/editable-documents/{document_id}/versions",
        json=draft_payload,
        headers=headers,
    )
    assert r_draft.status_code == 200
    assert r_draft.json()["version_number"] == 3
    assert r_draft.json()["approved"] is False

    r_detail = client.get(f"/api/v1/editable-documents/{document_id}", headers=headers)
    assert r_detail.status_code == 200
    detail = r_detail.json()

    assert detail["current_version_number"] == 3
    assert detail["status"] == "draft"

    versions = {item["version_number"]: item for item in detail["versions"]}
    assert versions[2]["approved"] is True
    assert versions[3]["approved"] is False

    r_export = client.get(f"/api/v1/editable-documents/{document_id}/export/html", headers=headers)
    assert r_export.status_code == 200
    assert "Resumo aprovado." in r_export.text
    assert "Resumo editável v3." not in r_export.text
