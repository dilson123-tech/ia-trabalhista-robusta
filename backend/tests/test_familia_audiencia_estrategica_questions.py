from app.api.v1.routes.editable_documents import (
    _build_audiencia_person_specific_questions,
    _is_familia_audiencia_area,
)


def test_familia_audiencia_area_detector_accepts_family_variants():
    assert _is_familia_audiencia_area("familia") is True
    assert _is_familia_audiencia_area("família") is True
    assert _is_familia_audiencia_area("family") is True
    assert _is_familia_audiencia_area("direito de familia") is True
    assert _is_familia_audiencia_area("direito de família") is True
    assert _is_familia_audiencia_area("familia-e-sucessoes") is True
    assert _is_familia_audiencia_area("família_e_sucessões") is True
    assert _is_familia_audiencia_area("vara de família") is True


def test_familia_audiencia_area_detector_rejects_non_family_areas():
    assert _is_familia_audiencia_area("consumidor") is False
    assert _is_familia_audiencia_area("trabalhista") is False
    assert _is_familia_audiencia_area("criminal") is False
    assert _is_familia_audiencia_area("civel") is False
    assert _is_familia_audiencia_area(None) is False


def test_familia_audiencia_questions_use_family_roles():
    content = _build_audiencia_person_specific_questions(
        (
            "Caso de família com guarda, alimentos, convivência, divórcio, união estável, "
            "alienação parental, estudo social, renda, rotina da criança e testemunhas familiares."
        ),
        area="família",
    ).lower()

    required_terms = [
        "genitor / requerente:",
        "genitor / requerido:",
        "criança / adolescente, quando houver escuta adequada:",
        "responsável financeiro / alimentos:",
        "testemunha familiar:",
        "testemunha escolar / cuidador / profissional próximo:",
        "assistente social / equipe técnica:",
        "psicólogo / perito psicossocial:",
        "guarda",
        "alimentos",
        "convivência",
        "rotina da criança",
        "melhor interesse da criança",
    ]

    for term in required_terms:
        assert term in content

    forbidden_terms = [
        "consumidor / autor:",
        "fornecedor / empresa ré:",
        "reclamante / empregado:",
        "preposto / representante da reclamada:",
        "vítima / ofendido:",
        "policial militar / agente da abordagem:",
        "representante da pratic sider / parte autora:",
    ]

    for term in forbidden_terms:
        assert term not in content


def test_existing_audiencia_flows_remain_after_family_addition():
    consumer = _build_audiencia_person_specific_questions(
        "Caso consumidor com banco, cobrança indevida e negativação.",
        area="consumidor",
    ).lower()
    assert "consumidor / autor:" in consumer
    assert "genitor / requerente:" not in consumer

    labor = _build_audiencia_person_specific_questions(
        "Caso trabalhista com reclamante, preposto, FGTS e controle de ponto.",
        area="trabalhista",
    ).lower()
    assert "reclamante / empregado:" in labor
    assert "genitor / requerente:" not in labor

    criminal = _build_audiencia_person_specific_questions(
        "Caso criminal com vítima, acusado, policial militar e delegado.",
        area="criminal",
    ).lower()
    assert "vítima / ofendido:" in criminal
    assert "genitor / requerente:" not in criminal

    civil = _build_audiencia_person_specific_questions(
        "Processo PRATIC SIDER contra Dilson Pereira envolvendo Edson Estevão e Rosangela.",
        area="civel",
    ).lower()
    assert "representante da pratic sider / parte autora:" in civil
    assert "genitor / requerente:" not in civil
