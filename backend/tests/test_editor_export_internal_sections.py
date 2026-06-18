from app.services.editor_export_service import build_editor_html


def test_editor_export_includes_protocol_checklist_in_final_html_when_exportable():
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
                    "content": "Checklist final de conferência antes do protocolo.",
                    "metadata": {
                        "export_visibility": "final",
                        "include_in_final_pdf": True,
                    },
                },
            ],
        },
    )

    assert "Fechamento" in html
    assert "Termos em que" in html
    assert "Checklist Final para Protocolo" in html
    assert "Checklist final de conferência antes do protocolo" in html


def test_editor_export_includes_protocol_checklist_by_key_without_internal_metadata():
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
    assert "Checklist Final para Protocolo" in html
    assert "Pendências e conferências obrigatórias" in html


def test_editor_export_still_hides_generic_internal_sections_from_final_html():
    html = build_editor_html(
        {
            "title": "Documento jurídico",
            "area": "juridico",
            "document_type": "peticao_inicial",
        },
        {
            "version_number": 1,
            "sections": [
                {
                    "key": "resumo_fatico",
                    "title": "Resumo Fático",
                    "content": "Conteúdo exportável.",
                    "metadata": {},
                },
                {
                    "key": "nota_interna",
                    "title": "Nota Interna",
                    "content": "Controle interno do escritório.",
                    "metadata": {
                        "export_visibility": "internal",
                        "include_in_final_pdf": False,
                    },
                },
            ],
        },
    )

    assert "Resumo Fático" in html
    assert "Conteúdo exportável" in html
    assert "Nota Interna" not in html
    assert "Controle interno do escritório" not in html
