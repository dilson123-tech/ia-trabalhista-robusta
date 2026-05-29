from app.api.v1.routes.editable_documents import (
    _build_audiencia_person_specific_questions,
    _is_criminal_audiencia_area,
)


def test_criminal_audiencia_area_detector_accepts_penal_variants():
    assert _is_criminal_audiencia_area("criminal") is True
    assert _is_criminal_audiencia_area("penal") is True
    assert _is_criminal_audiencia_area("direito penal") is True
    assert _is_criminal_audiencia_area("processo penal") is True
    assert _is_criminal_audiencia_area("direito-penal") is True
    assert _is_criminal_audiencia_area("processo_penal") is True


def test_criminal_audiencia_area_detector_rejects_non_criminal_areas():
    assert _is_criminal_audiencia_area("civel") is False
    assert _is_criminal_audiencia_area("civil_ambiental") is False
    assert _is_criminal_audiencia_area("trabalhista") is False
    assert _is_criminal_audiencia_area("consumidor") is False
    assert _is_criminal_audiencia_area(None) is False


def test_criminal_audiencia_questions_use_criminal_roles():
    content = _build_audiencia_person_specific_questions(
        "Caso criminal com vítima, acusado, policial militar, testemunha, delegado e laudo pericial.",
        area="criminal",
    )

    required_terms = [
        "Vítima / ofendido:",
        "Policial militar / agente da abordagem:",
        "Policial civil / investigador:",
        "Delegado / autoridade policial:",
        "Testemunha de acusação:",
        "Testemunha de defesa:",
        "Acusado / réu:",
        "Perito / responsável por laudo:",
        "cadeia de custódia",
        "risco de autoincriminação",
    ]

    for term in required_terms:
        assert term in content

    assert "Representante da PRATIC SIDER / parte autora:" not in content
    assert "Edson Estevão:" not in content


def test_civil_audiencia_questions_keep_existing_pratic_sider_flow():
    content = _build_audiencia_person_specific_questions(
        "Processo PRATIC SIDER contra Dilson Pereira envolvendo Edson Estevão e Rosangela.",
        area="civel",
    )

    required_terms = [
        "Representante da PRATIC SIDER / parte autora:",
        "Edson Estevão:",
        "Rosangela de Lourdes Siqueira:",
        "Dilson Pereira / parte ré:",
    ]

    for term in required_terms:
        assert term in content

    assert "Policial militar / agente da abordagem:" not in content
    assert "Acusado / réu:" not in content
