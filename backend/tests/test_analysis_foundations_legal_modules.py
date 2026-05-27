from app.services.analysis_foundations import build_analysis_foundations


def test_consumer_foundations_use_consumer_basis_from_generic_civel():
    foundations = build_analysis_foundations(
        case={
            "legal_area": "civel",
            "action_type": "Consumidor — vício do produto",
            "description": "Consumidor comprou produto com defeito e tem protocolo contra fornecedor.",
        },
        technical={
            "legal_area": "consumidor",
            "summary": "Caso consumerista com produto com defeito.",
            "issues": ["Produto com defeito e protocolos pendentes."],
            "next_steps": ["Anexar nota fiscal e protocolos."],
        },
        viability={"label": "Viabilidade moderada"},
        decision={"final_status": "MODERADA"},
    )

    assert foundations["analysis_context"]["legal_area"] == "consumidor"
    assert any("Código de Defesa do Consumidor" in item for item in foundations["normative_basis"])
    assert any("produto" in item.lower() or "fornecedor" in item.lower() for item in foundations["factual_elements_considered"])


def test_family_foundations_use_sensitive_family_disclaimer():
    foundations = build_analysis_foundations(
        case={
            "legal_area": "civel",
            "action_type": "Família — guarda",
            "description": "Caso de guarda de menor e convivência familiar.",
        },
        technical={
            "summary": "Caso de família com guarda e menor.",
            "issues": ["Guarda e convivência precisam de prova."],
            "next_steps": ["Anexar certidão e documentos familiares."],
        },
        viability={"label": "Viabilidade moderada"},
        decision={"final_status": "MODERADA"},
    )

    assert foundations["analysis_context"]["legal_area"] == "familia"
    assert any("Código Civil" in item for item in foundations["normative_basis"])
    assert "dados sensíveis" in foundations["disclaimer"]


def test_previdenciario_foundations_use_bpc_loas_basis():
    foundations = build_analysis_foundations(
        case={
            "legal_area": "civel",
            "action_type": "BPC/LOAS",
            "description": "Pedido de BPC/LOAS para idoso com CadÚnico, renda familiar e indeferimento do INSS.",
        },
        technical={
            "summary": "Caso de BPC/LOAS com vulnerabilidade social.",
            "issues": ["Necessário CadÚnico, renda e laudo."],
            "next_steps": ["Anexar decisão do INSS e documentos sociais."],
        },
        viability={"label": "Viabilidade moderada"},
        decision={"final_status": "MODERADA"},
    )

    assert foundations["analysis_context"]["legal_area"] == "previdenciario"
    assert any("Lei 8.742/1993" in item for item in foundations["normative_basis"])
    assert "previdenciária/assistencial" in foundations["disclaimer"]
