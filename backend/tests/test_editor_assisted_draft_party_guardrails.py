from app.api.v1.routes.editable_documents import (
    _format_party_inline_qualification,
    _select_assisted_draft_litigation_parties,
)


def test_assisted_draft_does_not_use_witness_grid_person_as_author():
    witness_party = {
        "name": "Edson Estevão",
        "role": "testemunha / condutor",
        "party_type": "person",
        "document_id": "",
        "party_metadata": {
            "grid_source": "case_witness_grid_v1",
            "what_knows": "Responsável/condutor relacionado ao contrato.",
        },
    }

    author_party, defendant_party = _select_assisted_draft_litigation_parties([witness_party])

    assert author_party is None
    assert defendant_party is None

    qualification = _format_party_inline_qualification(
        author_party,
        "[NOME COMPLETO DA PARTE AUTORA]",
    )

    assert "Edson Estevão" not in qualification
    assert "[NOME COMPLETO DA PARTE AUTORA]" in qualification


def test_assisted_draft_selects_real_process_parties_when_available():
    author = {
        "name": "Dilson Pereira",
        "role": "autor",
        "party_type": "person",
        "document_id": "",
        "party_metadata": {},
    }
    defendant = {
        "name": "Empresa Ré Ltda.",
        "role": "ré",
        "party_type": "company",
        "document_id": "",
        "party_metadata": {},
    }
    witness = {
        "name": "Edson Estevão",
        "role": "testemunha / condutor",
        "party_type": "person",
        "document_id": "",
        "party_metadata": {"grid_source": "case_witness_grid_v1"},
    }

    author_party, defendant_party = _select_assisted_draft_litigation_parties(
        [witness, author, defendant]
    )

    assert author_party["name"] == "Dilson Pereira"
    assert defendant_party["name"] == "Empresa Ré Ltda."
