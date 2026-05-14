from app.api.v1.routes.editable_documents import (
    _extract_labor_parties_from_case_description,
    _format_party_inline_qualification,
    _select_primary_party,
)


def test_extract_labor_parties_from_case_description_for_fgts_case():
    description = """
    Parte reclamante: Roberto Almeida Santos, CPF parcialmente informado.

    Parte reclamada: Construções Atlântico LTDA., Joinville/SC.

    O reclamante trabalhou para a reclamada Construções Atlântico LTDA.,
    exercendo a função de servente de obras, com remuneração mensal aproximada
    de R$ 2.300,00.
    """

    parties = _extract_labor_parties_from_case_description(description)

    author = _select_primary_party(parties, ["reclamante"])
    defendant = _select_primary_party(parties, ["reclamada"])

    assert author is not None
    assert author["name"] == "Roberto Almeida Santos"
    assert author["party_metadata"]["profissao"] == "servente de obras"

    assert defendant is not None
    assert defendant["name"] == "Construções Atlântico LTDA"
    assert defendant["party_metadata"]["endereco"] == "Joinville/SC"


def test_format_extracted_labor_parties_keeps_missing_fields_as_placeholders():
    description = """
    Parte reclamante: Roberto Almeida Santos, CPF parcialmente informado.
    Parte reclamada: Construções Atlântico LTDA., Joinville/SC.
    O reclamante exercendo a função de servente de obras.
    """

    parties = _extract_labor_parties_from_case_description(description)
    author = _select_primary_party(parties, ["reclamante"])
    defendant = _select_primary_party(parties, ["reclamada"])

    author_text = _format_party_inline_qualification(
        author,
        "[NOME COMPLETO DA PARTE AUTORA]",
    )
    defendant_text = _format_party_inline_qualification(
        defendant,
        "[NOME/RAZÃO SOCIAL DA PARTE RÉ]",
        default_is_company=True,
    )

    assert "Roberto Almeida Santos" in author_text
    assert "servente de obras" in author_text
    assert "[CPF a complementar]" in author_text
    assert "[RG a complementar]" in author_text

    assert "Construções Atlântico LTDA" in defendant_text
    assert "CNPJ nº [CNPJ a complementar]" in defendant_text
    assert "Joinville/SC" in defendant_text



def test_select_primary_party_does_not_match_short_re_inside_reclamante():
    description = """
    Parte reclamante: Roberto Almeida Santos, CPF parcialmente informado.

    Parte reclamada: Construções Atlântico LTDA., Joinville/SC.

    O reclamante trabalhou para a reclamada Construções Atlântico LTDA.,
    exercendo a função de servente de obras.
    """

    parties = _extract_labor_parties_from_case_description(description)

    author = _select_primary_party(
        parties,
        ["autor", "autora", "parte autora", "requerente", "demandante", "reclamante", "impetrante"],
    )
    defendant = _select_primary_party(
        parties,
        ["reu", "ré", "réu", "parte re", "parte ré", "requerido", "demandado", "reclamada", "impetrado"],
    )

    assert author is not None
    assert defendant is not None
    assert author["name"] == "Roberto Almeida Santos"
    assert defendant["name"] == "Construções Atlântico LTDA"
    assert defendant is not author
