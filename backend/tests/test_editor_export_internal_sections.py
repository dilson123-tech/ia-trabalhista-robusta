from app.services.editor_export_service import build_editor_html


def test_editor_export_hides_internal_protocol_checklist_from_final_html():
    html = build_editor_html(
        {
            "title": "FGTS não recolhido — ausência de depósitos durante o contrato",
            "area": "trabalhista",
            "document_type": "peticao_inicial",
        },
        {
            "version_number": 33,
            "sections": [
                {
                    "key": "fechamento",
                    "title": "Fechamento",
                    "content": "Termos em que,\n\nPede deferimento.",
                    "metadata": {},
                },
                {
                    "key": "checklist_final_protocolo",
                    "title": "Checklist Final para Protocolo",
                    "content": "Checklist interno de prontidão para protocolo.",
                    "metadata": {
                        "export_visibility": "internal",
                        "include_in_final_pdf": False,
                    },
                },
            ],
        },
    )

    assert "Fechamento" in html
    assert "Termos em que" in html
    assert "Checklist Final para Protocolo" not in html
    assert "Checklist interno de prontidão para protocolo" not in html



def test_editor_export_hides_protocol_checklist_by_key_even_without_metadata():
    html = build_editor_html(
        {
            "title": "FGTS não recolhido — ausência de depósitos durante o contrato",
            "area": "trabalhista",
            "document_type": "peticao_inicial",
        },
        {
            "version_number": 33,
            "sections": [
                {
                    "key": "fechamento",
                    "title": "Fechamento",
                    "content": "Joinville/SC, 14 de maio de 2026.\n\nDr. Advogado Responsável",
                    "metadata": {},
                },
                {
                    "key": "checklist_final_protocolo",
                    "title": "Checklist Final para Protocolo",
                    "content": "Pendências e conferências obrigatórias.",
                    "metadata": {},
                },
            ],
        },
    )

    assert "Fechamento" in html
    assert "Dr. Advogado Responsável" in html
    assert "Checklist Final para Protocolo" not in html
    assert "Pendências e conferências obrigatórias" not in html
