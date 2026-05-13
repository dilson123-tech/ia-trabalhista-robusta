from app.services.analysis_foundations import build_analysis_foundations


def test_trabalhista_fgts_foundations_do_not_leak_civil_environmental_facts():
    case = {
        "case_number": "PILOTO-TRAB-005",
        "title": "FGTS não recolhido — ausência de depósitos durante o contrato",
        "description": """
        Parte reclamante: Roberto Almeida Santos.
        Parte reclamada: Construções Atlântico LTDA.
        Área jurídica: Trabalhista.
        O reclamante relata ausência de depósitos mensais de FGTS,
        depósitos parciais, extrato analítico do FGTS, conta vinculada,
        GFIP, SEFIP e eSocial.
        """,
        "legal_area": "trabalhista",
    }
    technical = {
        "summary": "Caso trabalhista sobre FGTS não recolhido e necessidade de cálculo.",
        "issues": ["Necessidade de extrato analítico completo do FGTS."],
        "next_steps": ["Conferir holerites e comprovantes de recolhimento."],
    }

    payload = build_analysis_foundations(case, technical, {}, {})
    elements = payload["factual_elements_considered"]
    joined = " ".join(elements).lower()

    assert "poeira" not in joined
    assert "cimento" not in joined
    assert any("fgts" in item.lower() for item in elements)


def test_civil_ambiental_foundations_keep_environmental_facts_when_area_matches():
    case = {
        "case_number": "PILOTO-CIV-001",
        "title": "Poeira de cimento em imóvel vizinho",
        "description": """
        Área jurídica: Civil ambiental.
        Relato de poeira de cimento, ruído e material particulado vindos do imóvel vizinho.
        """,
        "legal_area": "civil_ambiental",
    }
    technical = {
        "summary": "Caso civil ambiental sobre poeira de cimento e ruído.",
        "issues": [],
        "next_steps": [],
    }

    payload = build_analysis_foundations(case, technical, {}, {})
    elements = payload["factual_elements_considered"]
    joined = " ".join(elements).lower()

    assert "poeira" in joined
    assert "cimento" in joined
