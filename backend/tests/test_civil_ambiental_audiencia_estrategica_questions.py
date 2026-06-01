import pytest

from app.api.v1.routes.editable_documents import (
    _build_audiencia_person_specific_questions,
    _build_civil_ambiental_audiencia_person_specific_questions,
    _is_civil_ambiental_audiencia_area,
)


@pytest.mark.parametrize(
    "area",
    [
        "civil_ambiental",
        "civil ambiental",
        "cível ambiental",
        "ambiental",
        "direito ambiental",
        "responsabilidade civil ambiental",
        "vizinhança",
        "direito de vizinhanca",
        "dano ambiental",
    ],
)
def test_civil_ambiental_detector_accepts_expected_variants(area):
    assert _is_civil_ambiental_audiencia_area(area) is True


@pytest.mark.parametrize(
    "area",
    [
        "previdenciário",
        "familia",
        "família",
        "consumidor",
        "trabalhista",
        "criminal",
        "civel",
        "cível",
        None,
    ],
)
def test_civil_ambiental_detector_rejects_other_areas(area):
    assert _is_civil_ambiental_audiencia_area(area) is False


def test_civil_ambiental_questions_include_expected_roles_and_themes():
    text = _build_civil_ambiental_audiencia_person_specific_questions(
        """
        Ação de responsabilidade civil ambiental por dano de vizinhança.
        Há alegação de ruído, fumaça, odor, infiltração e descarte irregular.
        Existem fotos, vídeos, laudo técnico e auto de fiscalização.
        O advogado quer demonstrar nexo causal, obrigação de fazer/não fazer
        e reparação pelos danos.
        """
    ).lower()

    expected_terms = [
        "autor",
        "prejudicado",
        "réu",
        "causador",
        "testemunha do autor",
        "testemunha da defesa",
        "perito",
        "técnico",
        "fiscalização",
        "órgão público",
        "vizinho",
        "comunidade afetada",
        "documentos",
        "fotos",
        "vídeos",
        "laudos",
        "dano ambiental",
        "dano de vizinhança",
        "responsabilidade civil",
        "nexo causal",
        "perícia",
        "laudo",
        "obrigação de fazer",
        "não fazer",
    ]

    for term in expected_terms:
        assert term in text


def test_civil_ambiental_questions_do_not_contaminate_other_areas():
    text = _build_civil_ambiental_audiencia_person_specific_questions(
        "Caso ambiental com laudo técnico, vizinhos afetados e fiscalização."
    ).lower()

    forbidden_terms = [
        "requerente / segurado",
        "genitor / requerente",
        "consumidor / autor",
        "reclamante / empregado",
        "vítima / ofendido",
        "representante da pratic sider",
    ]

    for term in forbidden_terms:
        assert term not in text


def test_civil_ambiental_dispatcher_uses_specific_questions():
    text = _build_audiencia_person_specific_questions(
        area="civil_ambiental",
        context_text="Dano ambiental, vizinhança, laudo, fiscalização e nexo causal.",
    ).lower()

    assert "dano ambiental" in text
    assert "dano de vizinhança" in text
    assert "fiscalização" in text
    assert "nexo causal" in text
    assert "perito" in text


@pytest.mark.parametrize(
    "area,context_text,expected_any",
    [
        (
            "previdenciário",
            "Caso previdenciário de BPC/LOAS, INSS, segurado, perícia médica e avaliação social.",
            ["requerente", "segurado"],
        ),
        (
            "família",
            "Caso de família com guarda, alimentos, genitor, criança/adolescente e estudo psicossocial.",
            ["genitor", "criança"],
        ),
        (
            "consumidor",
            "Caso consumidor com fornecedor, cobrança, negativação, SAC e falha na prestação de serviço.",
            ["consumidor", "fornecedor"],
        ),
        (
            "trabalhista",
            "Caso trabalhista com reclamante, empregado, jornada, verbas rescisórias e testemunhas.",
            ["reclamante", "empregado"],
        ),
        (
            "criminal",
            "Caso criminal com vítima/ofendido, acusado, flagrante, testemunhas e prova penal.",
            ["vítima", "ofendido"],
        ),
        (
            "cível",
            "Caso cível fallback PRATIC SIDER x Dilson Pereira, com parte autora, parte ré e testemunhas.",
            ["pratic sider", "parte autora", "parte ré"],
        ),
    ],
)
def test_existing_audiencia_flows_are_preserved(area, context_text, expected_any):
    text = _build_audiencia_person_specific_questions(
        area=area,
        context_text=context_text,
    ).lower()

    assert any(expected in text for expected in expected_any)
    assert "responsável por documentos, fotos, vídeos ou laudos" not in text
