from pathlib import Path


ROUTE_TEXT = Path("backend/app/api/v1/routes/editable_documents.py").read_text()


def test_editable_documents_provas_requerimentos_uses_structured_generic_sections():
    assert "I. Das provas documentais já informadas." in ROUTE_TEXT
    assert "II. Das provas pendentes de juntada ou conferência." in ROUTE_TEXT
    assert "III. Da exibição de documentos e informações." in ROUTE_TEXT
    assert "IV. Das diligências e demais meios de prova." in ROUTE_TEXT
    assert "V. Da cautela quanto à prova." in ROUTE_TEXT


def test_editable_documents_provas_requerimentos_no_longer_uses_old_single_paragraph_base():
    old_text = (
        "Requer-se a produção de todos os meios de prova em direito admitidos, "
        "especialmente documental, testemunhal e pericial, conforme a natureza das controvérsias identificadas."
    )
    assert old_text not in ROUTE_TEXT
    assert "Na versão final, devem ser especificados os documentos já existentes, a prova técnica pertinente" not in ROUTE_TEXT
