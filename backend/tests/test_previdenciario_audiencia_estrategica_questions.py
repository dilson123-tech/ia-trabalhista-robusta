from app.api.v1.routes.editable_documents import (
    _build_audiencia_person_specific_questions,
    _is_previdenciario_audiencia_area,
)


def test_previdenciario_audiencia_area_detector_accepts_variants():
    assert _is_previdenciario_audiencia_area("previdenciario") is True
    assert _is_previdenciario_audiencia_area("previdenciário") is True
    assert _is_previdenciario_audiencia_area("direito previdenciário") is True
    assert _is_previdenciario_audiencia_area("previdenciario-bpc-loas") is True
    assert _is_previdenciario_audiencia_area("bpc/loas") is True
    assert _is_previdenciario_audiencia_area("benefício assistencial") is True
    assert _is_previdenciario_audiencia_area("beneficio previdenciario") is True
    assert _is_previdenciario_audiencia_area("inss") is True


def test_previdenciario_audiencia_area_detector_rejects_non_social_security_areas():
    assert _is_previdenciario_audiencia_area("família") is False
    assert _is_previdenciario_audiencia_area("consumidor") is False
    assert _is_previdenciario_audiencia_area("trabalhista") is False
    assert _is_previdenciario_audiencia_area("criminal") is False
    assert _is_previdenciario_audiencia_area("civel") is False
    assert _is_previdenciario_audiencia_area(None) is False


def test_previdenciario_audiencia_questions_use_bpc_loas_roles():
    content = _build_audiencia_person_specific_questions(
        (
            "Caso previdenciário de BPC/LOAS com requerente, familiar cuidador, CadÚnico, "
            "renda familiar, laudo médico, deficiência, incapacidade, avaliação social, perícia e INSS."
        ),
        area="previdenciário",
    ).lower()

    required_terms = [
        "requerente / segurado:",
        "familiar cuidador / responsável pela rotina:",
        "representante legal / procurador:",
        "médico assistente / profissional de saúde:",
        "perito médico:",
        "assistente social / avaliador social:",
        "servidor / representante do inss:",
        "testemunha sobre rotina, incapacidade e vulnerabilidade:",
        "bpc/loas",
        "cadúnico",
        "renda familiar",
        "laudos médicos",
        "perícia médica",
        "avaliação social",
        "benefício assistencial",
    ]

    for term in required_terms:
        assert term in content

    forbidden_terms = [
        "genitor / requerente:",
        "consumidor / autor:",
        "fornecedor / empresa ré:",
        "reclamante / empregado:",
        "vítima / ofendido:",
        "policial militar / agente da abordagem:",
        "representante da pratic sider / parte autora:",
    ]

    for term in forbidden_terms:
        assert term not in content


def test_existing_audiencia_flows_remain_after_previdenciario_addition():
    family = _build_audiencia_person_specific_questions(
        "Caso de família com guarda, alimentos e convivência.",
        area="família",
    ).lower()
    assert "genitor / requerente:" in family
    assert "requerente / segurado:" not in family

    consumer = _build_audiencia_person_specific_questions(
        "Caso consumidor com banco, cobrança indevida e negativação.",
        area="consumidor",
    ).lower()
    assert "consumidor / autor:" in consumer
    assert "requerente / segurado:" not in consumer

    labor = _build_audiencia_person_specific_questions(
        "Caso trabalhista com reclamante, preposto, FGTS e controle de ponto.",
        area="trabalhista",
    ).lower()
    assert "reclamante / empregado:" in labor
    assert "requerente / segurado:" not in labor

    criminal = _build_audiencia_person_specific_questions(
        "Caso criminal com vítima, acusado, policial militar e delegado.",
        area="criminal",
    ).lower()
    assert "vítima / ofendido:" in criminal
    assert "requerente / segurado:" not in criminal

    civil = _build_audiencia_person_specific_questions(
        "Processo PRATIC SIDER contra Dilson Pereira envolvendo Edson Estevão e Rosangela.",
        area="civel",
    ).lower()
    assert "representante da pratic sider / parte autora:" in civil
    assert "requerente / segurado:" not in civil
