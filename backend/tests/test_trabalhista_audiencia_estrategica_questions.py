from app.api.v1.routes.editable_documents import (
    _build_audiencia_person_specific_questions,
    _is_trabalhista_audiencia_area,
)


def test_trabalhista_audiencia_area_detector_accepts_labor_variants():
    assert _is_trabalhista_audiencia_area("trabalhista") is True
    assert _is_trabalhista_audiencia_area("trabalho") is True
    assert _is_trabalhista_audiencia_area("laboral") is True
    assert _is_trabalhista_audiencia_area("direito do trabalho") is True
    assert _is_trabalhista_audiencia_area("processo-do-trabalho") is True
    assert _is_trabalhista_audiencia_area("processo_do_trabalho") is True


def test_trabalhista_audiencia_area_detector_rejects_non_labor_areas():
    assert _is_trabalhista_audiencia_area("criminal") is False
    assert _is_trabalhista_audiencia_area("penal") is False
    assert _is_trabalhista_audiencia_area("civel") is False
    assert _is_trabalhista_audiencia_area("consumidor") is False
    assert _is_trabalhista_audiencia_area(None) is False


def test_trabalhista_audiencia_questions_use_labor_roles():
    content = _build_audiencia_person_specific_questions(
        (
            "Caso trabalhista com reclamante, reclamada, preposto, gestor, RH, testemunhas, "
            "FGTS, horas extras, verbas rescisórias, controle de ponto, EPI e insalubridade."
        ),
        area="trabalhista",
    ).lower()

    required_terms = [
        "reclamante / empregado:",
        "preposto / representante da reclamada:",
        "testemunha do reclamante:",
        "testemunha da reclamada:",
        "gestor / encarregado:",
        "rh / responsável por folha, ponto e rescisão:",
        "técnico de segurança / medicina do trabalho:",
        "perito / responsável por laudo trabalhista:",
        "controle de ponto",
        "fgts",
        "verbas rescisórias",
        "risco ocupacional",
    ]

    for term in required_terms:
        assert term in content

    forbidden_terms = [
        "vítima / ofendido:",
        "policial militar / agente da abordagem:",
        "delegado / autoridade policial:",
        "representante da pratic sider / parte autora:",
        "edson estevão:",
        "locação da carreta",
    ]

    for term in forbidden_terms:
        assert term not in content


def test_criminal_audiencia_questions_remain_criminal_after_labor_addition():
    content = _build_audiencia_person_specific_questions(
        "Caso criminal com vítima, acusado, policial militar, delegado e laudo pericial.",
        area="criminal",
    ).lower()

    assert "vítima / ofendido:" in content
    assert "policial militar / agente da abordagem:" in content
    assert "acusado / réu:" in content
    assert "reclamante / empregado:" not in content
    assert "preposto / representante da reclamada:" not in content


def test_civil_pratic_sider_flow_remains_civil_after_labor_addition():
    content = _build_audiencia_person_specific_questions(
        "Processo PRATIC SIDER contra Dilson Pereira envolvendo Edson Estevão e Rosangela.",
        area="civel",
    ).lower()

    assert "representante da pratic sider / parte autora:" in content
    assert "edson estevão:" in content
    assert "rosangela de lourdes siqueira:" in content
    assert "dilson pereira / parte ré:" in content
    assert "reclamante / empregado:" not in content
    assert "policial militar / agente da abordagem:" not in content
