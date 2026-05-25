from pathlib import Path


def test_criminal_editor_routing_is_present_and_supervised():
    source = Path("backend/app/api/v1/routes/editable_documents.py").read_text()

    assert 'is_criminal_area = normalized_area in {"criminal", "penal"}' in source
    assert "criminal_editable_document_routing_v1" in source
    assert "PEDIDO DE LIBERDADE PROVISÓRIA" in source
    assert "PEDIDO DE RELAXAMENTO DE PRISÃO" in source
    assert "HABEAS CORPUS COM PEDIDO LIMINAR" in source
    assert "RESPOSTA À ACUSAÇÃO" in source
    assert "não representa promessa de resultado" in source
    assert "não afirma culpa ou inocência" in source
    assert "não deve ser usado externamente sem revisão" in source
    assert "Nenhuma prova deve ser inventada, adulterada, ocultada ou orientada de forma ilegal" in source
