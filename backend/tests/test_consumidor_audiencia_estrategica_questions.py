from app.api.v1.routes.editable_documents import (
    _build_audiencia_person_specific_questions,
    _is_consumidor_audiencia_area,
)


def test_consumidor_audiencia_area_detector_accepts_consumer_variants():
    assert _is_consumidor_audiencia_area("consumidor") is True
    assert _is_consumidor_audiencia_area("consumer") is True
    assert _is_consumidor_audiencia_area("direito do consumidor") is True
    assert _is_consumidor_audiencia_area("relacao de consumo") is True
    assert _is_consumidor_audiencia_area("relação de consumo") is True


def test_consumidor_audiencia_area_detector_rejects_non_consumer_areas():
    assert _is_consumidor_audiencia_area("criminal") is False
    assert _is_consumidor_audiencia_area("trabalhista") is False
    assert _is_consumidor_audiencia_area("civel") is False
    assert _is_consumidor_audiencia_area(None) is False


def test_consumidor_audiencia_questions_use_consumer_roles():
    content = _build_audiencia_person_specific_questions(
        (
            "Caso de consumidor com banco, cobrança indevida, negativação, contrato, "
            "protocolo de atendimento, SAC, fornecedor, testemunha e dano moral."
        ),
        area="consumidor",
    ).lower()

    required_terms = [
        "consumidor / autor:",
        "fornecedor / empresa ré:",
        "atendente / suporte / sac / ouvidoria:",
        "representante comercial / vendedor / loja:",
        "testemunha do consumidor:",
        "testemunha do fornecedor:",
        "responsável financeiro / cobrança / negativação:",
        "técnico / assistência / perito do produto ou serviço:",
        "cobrança indevida",
        "negativação",
        "protocolo",
        "relação de consumo",
    ]

    for term in required_terms:
        assert term in content

    forbidden_terms = [
        "reclamante / empregado:",
        "preposto / representante da reclamada:",
        "vítima / ofendido:",
        "policial militar / agente da abordagem:",
        "representante da pratic sider / parte autora:",
        "edson estevão:",
    ]

    for term in forbidden_terms:
        assert term not in content


def test_labor_criminal_and_civil_flows_remain_after_consumer_addition():
    labor = _build_audiencia_person_specific_questions(
        "Caso trabalhista com reclamante, preposto, FGTS e controle de ponto.",
        area="trabalhista",
    ).lower()
    assert "reclamante / empregado:" in labor
    assert "consumidor / autor:" not in labor

    criminal = _build_audiencia_person_specific_questions(
        "Caso criminal com vítima, acusado, policial militar e delegado.",
        area="criminal",
    ).lower()
    assert "vítima / ofendido:" in criminal
    assert "consumidor / autor:" not in criminal

    civil = _build_audiencia_person_specific_questions(
        "Processo PRATIC SIDER contra Dilson Pereira envolvendo Edson Estevão e Rosangela.",
        area="civel",
    ).lower()
    assert "representante da pratic sider / parte autora:" in civil
    assert "consumidor / autor:" not in civil
