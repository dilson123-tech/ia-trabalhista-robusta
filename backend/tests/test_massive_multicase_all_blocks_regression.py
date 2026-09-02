from types import SimpleNamespace

import pytest

from app.services.case_operational_assistant import _fallback_response


ALL_BLOCKS_MESSAGE = """
Gere todos os blocos principais da minuta preliminar deste caso em formato de texto pronto para copiar e colar no Editor/minuta.

Entregue somente os blocos finais, separados por títulos exatamente assim:

BLOCO 1 — Endereçamento
BLOCO 2 — Qualificação das partes
BLOCO 3 — Resumo Fático
BLOCO 4 — Fundamentação preliminar
BLOCO 5 — Pedidos
BLOCO 6 — Provas e requerimentos
BLOCO 7 — Fechamento e conferência final

Não traga checklist operacional, linha do tempo, anexos, testemunhas, análise, próximos passos, alertas ou explicações fora dos blocos.

Não misture pedidos, provas, testemunhas ou pendências dentro do Resumo Fático.

Não invente dados. Use linguagem prudente.

Comece direto pelo BLOCO 1.
"""


BLOCK_TITLES = (
    "BLOCO 1 — Endereçamento",
    "BLOCO 2 — Qualificação das partes",
    "BLOCO 3 — Resumo Fático",
    "BLOCO 4 — Fundamentação preliminar",
    "BLOCO 5 — Pedidos",
    "BLOCO 6 — Provas e requerimentos",
    "BLOCO 7 — Fechamento e conferência final",
)


def fake_case(
    *,
    case_number: str,
    title: str,
    legal_area: str,
    action_type: str,
    description: str,
):
    return SimpleNamespace(
        id=9001,
        case_number=case_number,
        title=title,
        legal_area=legal_area,
        action_type=action_type,
        description=description,
    )


def split_blocks(rewritten: str) -> dict[str, str]:
    blocks: dict[str, str] = {}

    for index, title in enumerate(BLOCK_TITLES):
        assert rewritten.count(title) == 1, (
            f"Bloco ausente ou duplicado: {title}"
        )

        start = rewritten.index(title) + len(title)

        if index + 1 < len(BLOCK_TITLES):
            next_title = BLOCK_TITLES[index + 1]
            end = rewritten.index(next_title, start)
        else:
            end = len(rewritten)

        blocks[title] = rewritten[start:end].strip()

    return blocks


SCENARIOS = [
    {
        "id": "civil_collection",
        "case": {
            "case_number": "MASSIVE-CIVIL-COLLECTION-001",
            "title": "Cobrança cível por obrigação de pagamento não cumprida",
            "legal_area": "cível",
            "action_type": (
                "Cobrança cível / obrigação de pagamento não cumprida, "
                "a confirmar conforme documentos"
            ),
            "description": (
                "Cliente emprestou R$ 8.000,00 a um conhecido. "
                "O devedor prometeu devolver em três parcelas e nenhuma foi paga. "
                "Há conversas no WhatsApp e comprovante da transferência bancária."
            ),
        },
        "required": {
            "BLOCO 3 — Resumo Fático": (
                "R$ 8.000,00",
                "três parcelas",
                "WhatsApp",
            ),
            "BLOCO 6 — Provas e requerimentos": (
                "transferência bancária",
            ),
        },
        "forbidden": {
            "BLOCO 2 — Qualificação das partes": (
                "R$ 8.000,00",
                "três parcelas",
                "nenhuma foi paga",
            ),
        },
    },
    {
        "id": "consumer_defective_product",
        "case": {
            "case_number": "MASSIVE-CONSUMER-001",
            "title": "Produto defeituoso sem solução na garantia",
            "legal_area": "consumidor",
            "action_type": "Ação consumerista / reparação por falha no produto",
            "description": (
                "Consumidor comprou produto com defeito. "
                "A garantia foi acionada, mas o problema não foi solucionado. "
                "Há nota fiscal e mensagens com o fornecedor."
            ),
        },
        "required": {
            "BLOCO 3 — Resumo Fático": (
                "produto",
                "defeito",
                "garantia",
            ),
            "BLOCO 6 — Provas e requerimentos": (
                "nota fiscal",
            ),
        },
        "forbidden": {
            "BLOCO 2 — Qualificação das partes": (
                "produto com defeito",
                "problema não foi solucionado",
            ),
        },
    },
    {
        "id": "labor_hours",
        "case": {
            "case_number": "MASSIVE-LABOR-001",
            "title": "Horas extras não pagas",
            "legal_area": "trabalhista",
            "action_type": "Reclamação trabalhista / horas extras",
            "description": (
                "Empregado registrado relata jornada além do horário contratado "
                "e horas extras não pagas. Possui folhas de pagamento."
            ),
        },
        "required": {
            "BLOCO 3 — Resumo Fático": (
                "horas extras",
            ),
            "BLOCO 5 — Pedidos": (
                "horas extras",
            ),
        },
        "forbidden": {
            "BLOCO 2 — Qualificação das partes": (
                "horas extras não pagas",
                "jornada além",
            ),
        },
    },
    {
        "id": "social_security_bpc_loas",
        "case": {
            "case_number": "MASSIVE-PREVID-BPC-001",
            "title": "Pedido de benefício assistencial BPC/LOAS",
            "legal_area": "previdenciário",
            "action_type": "Concessão de benefício assistencial BPC/LOAS",
            "description": (
                "Pessoa requerente relata pedido de BPC/LOAS perante o INSS. "
                "O benefício foi negado. Há documentos do requerimento administrativo "
                "e informações socioeconômicas que deverão ser conferidas pelo advogado."
            ),
        },
        "required": {
            "BLOCO 3 — Resumo Fático": (
                "BPC/LOAS",
                "INSS",
            ),
        },
        "forbidden": {
            "BLOCO 2 — Qualificação das partes": (
                "benefício foi negado",
                "informações socioeconômicas",
            ),
        },
    },
    {
        "id": "family_guardianship_visitation",
        "case": {
            "case_number": "MASSIVE-FAMILY-001",
            "title": "Guarda e regulamentação de convivência",
            "legal_area": "família",
            "action_type": "Ação de guarda e regulamentação de convivência",
            "description": (
                "Genitor relata divergência sobre guarda e convivência com a criança. "
                "Pretende regulamentação judicial das visitas e definição da guarda. "
                "Dados completos das partes e da criança permanecem a confirmar."
            ),
        },
        "required": {
            "BLOCO 3 — Resumo Fático": (
                "guarda",
                "convivência",
            ),
            "BLOCO 5 — Pedidos": (
                "guarda",
            ),
        },
        "forbidden": {
            "BLOCO 2 — Qualificação das partes": (
                "divergência sobre guarda",
                "regulamentação judicial",
            ),
        },
    },
    {
        "id": "criminal_response_to_accusation",
        "case": {
            "case_number": "MASSIVE-CRIMINAL-001",
            "title": "Resposta à acusação em ação penal",
            "legal_area": "criminal",
            "action_type": "Defesa criminal / resposta à acusação",
            "description": (
                "Pessoa acusada relata recebimento de denúncia e necessidade de apresentação "
                "de resposta à acusação. O conteúdo integral dos autos, datas, imputação e "
                "elementos de prova permanecem sujeitos à conferência profissional."
            ),
        },
        "required": {
            "BLOCO 3 — Resumo Fático": (
                "denúncia",
                "resposta à acusação",
            ),
            "BLOCO 5 — Pedidos": (
                "resposta à acusação",
            ),
        },
        "forbidden": {
            "BLOCO 2 — Qualificação das partes": (
                "recebimento de denúncia",
                "elementos de prova",
            ),
        },
    },
    {
        "id": "civil_professional_risk_lgpd_edson",
        "case": {
            "case_number": "MASSIVE-CIVIL-RISK-001",
            "title": "Restrição profissional de motorista por análise de risco a esclarecer",
            "legal_area": "cível",
            "action_type": (
                "Obrigação de fazer / revisão de restrição profissional / "
                "dados e responsabilidade civil, a confirmar"
            ),
            "description": (
                "Edson Estevão, motorista profissional e empregado CLT da Silva Transporte, "
                "relata impedimentos para realizar carregamentos e viagens após análise de risco. "
                "Segundo informado, a Raster retorna recusa ou não liberação para determinadas operações. "
                "Edson recebe salário-base e valores vinculados às viagens realizadas, mas não é possível "
                "determinar com segurança quantas viagens foram perdidas nem o prejuízo exato. "
                "Há quatro gravações relacionadas aos fatos, cujo conteúdo deverá ser conferido. "
                "Também há referência a ocorrência antiga de aproximadamente 2015, sem prova de que seja "
                "a causa da restrição atual. Pretende-se identificar os dados pessoais utilizados, origem, "
                "tratamento, eventual compartilhamento, critérios da análise, procedimento de contestação "
                "e revisão da restrição. Não presumir decisão exclusivamente automatizada, ilicitude da "
                "análise de risco, valores, conteúdo dos áudios ou responsabilidade ainda não comprovada."
            ),
        },
        "required": {
            "BLOCO 3 — Resumo Fático": (
                "análise de risco",
                "Raster",
            ),
        },
        "forbidden": {
            "BLOCO 2 — Qualificação das partes": (
                "salário-base",
                "viagens realizadas",
                "Raster retorna",
                "quatro gravações",
                "prejuízo exato",
            ),
        },
    },
]


@pytest.mark.parametrize(
    "scenario",
    SCENARIOS,
    ids=[scenario["id"] for scenario in SCENARIOS],
)
def test_massive_multicase_all_blocks_universal_contract(scenario):
    case = fake_case(**scenario["case"])

    response = _fallback_response(
        case=case,
        message=ALL_BLOCKS_MESSAGE,
        context={},
        timeline=[],
    )

    assert response["assistant_mode"] == "editor_all_blocks_ready"

    rewritten = response["rewritten_input"]

    blocks = split_blocks(rewritten)

    assert len(blocks) == 7

    for title, body in blocks.items():
        assert body.strip(), f"Bloco vazio: {title}"
        assert "traceback" not in body.lower()
        assert "none" != body.strip().lower()

    assert response["metadata"]["blocks"] == list(BLOCK_TITLES)

    for title, required_markers in scenario.get("required", {}).items():
        normalized_body = " ".join(blocks[title].split()).lower()
        for marker in required_markers:
            assert marker.lower() in normalized_body, (
                f"[{scenario['id']}] conteúdo obrigatório ausente em {title}: {marker}"
            )

    for title, forbidden_markers in scenario.get("forbidden", {}).items():
        normalized_body = " ".join(blocks[title].split()).lower()
        for marker in forbidden_markers:
            assert marker.lower() not in normalized_body, (
                f"[{scenario['id']}] contaminação detectada em {title}: {marker}"
            )


def test_civil_professional_risk_edson_uses_specific_specialization():
    scenario = next(
        item for item in SCENARIOS
        if item["id"] == "civil_professional_risk_lgpd_edson"
    )

    case = fake_case(**scenario["case"])

    response = _fallback_response(
        case=case,
        message=ALL_BLOCKS_MESSAGE,
        context={},
        timeline=[],
    )

    assert response["assistant_mode"] == "editor_all_blocks_ready"
    assert response["metadata"]["action_specialization_kind"] == (
        "civil_professional_risk_restriction_claim"
    )
