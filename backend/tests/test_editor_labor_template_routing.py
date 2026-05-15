from types import SimpleNamespace

from app.api.v1.routes.editable_documents import _build_assisted_sections


class FakeDB:
    def query(self, *args, **kwargs):
        return self

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def first(self):
        return None


def test_severance_case_is_not_overridden_by_fgts_template():
    case = SimpleNamespace(
        id=184,
        tenant_id=77,
        case_number="PILOTO-TRAB-003",
        title="Verbas rescisórias não pagas — dispensa sem justa causa",
        legal_area="trabalhista",
        action_type="recisão",
        status="draft",
        description=(
            "Parte reclamante: João Carlos da Silva, CPF parcialmente informado.\n\n"
            "Parte reclamada: Mercado Central Alfa LTDA., Joinville/SC.\n\n"
            "Tipo de ação pretendida: Reclamação trabalhista para cobrança de verbas rescisórias "
            "decorrentes de dispensa sem justa causa.\n\n"
            "O reclamante trabalhou para a reclamada, exercendo a função de auxiliar de loja, "
            "com remuneração mensal aproximada de R$ 2.400,00. Foi dispensado sem justa causa "
            "e alega ausência de pagamento integral de saldo de salário, aviso-prévio, férias, "
            "13º salário proporcional, FGTS, multa de 40%, guias e multas dos arts. 477 e 467 da CLT."
        ),
    )

    analysis_record = SimpleNamespace(
        analysis={
            "technical": {
                "summary": "Caso trabalhista de verbas rescisórias decorrentes de dispensa sem justa causa.",
                "issues": [
                    "saldo de salário",
                    "aviso-prévio",
                    "férias proporcionais acrescidas de 1/3",
                    "13º salário proporcional",
                    "multa do art. 477 da CLT",
                    "multa do art. 467 da CLT",
                ],
                "next_steps": ["Conferir TRCT, CTPS, holerites e extrato de FGTS."],
            },
            "strategic": {
                "recommended_strategy": "Cobrar verbas rescisórias e guias decorrentes de dispensa sem justa causa.",
                "critical_points": ["Apurar valores pagos e diferenças rescisórias."],
            },
        },
        executive_data={},
    )

    sections = _build_assisted_sections(
        FakeDB(),
        case,
        analysis_record,
        tenant_id=77,
        document_metadata={},
    )

    by_key = {section["key"]: section["content"] for section in sections}

    resumo = by_key["resumo_fatico"].lower()
    pedidos = by_key["pedidos"].lower()

    assert "verbas rescisórias" in resumo
    assert "dispensa sem justa causa" in resumo
    assert "saldo de salário" in pedidos
    assert "aviso-prévio" in pedidos or "aviso previo" in pedidos
    assert "férias" in pedidos
    assert "13º" in pedidos or "13°" in pedidos
    assert "art. 477" in pedidos
    assert "art. 467" in pedidos

    assert "cobrança, regularização ou indenização de depósitos de fgts não recolhidos" not in resumo
