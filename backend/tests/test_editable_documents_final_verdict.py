from app.api.v1.routes.editable_documents import _build_editable_document_final_verdict


def test_final_verdict_flags_placeholders_missing_blocks_and_operational_text():
    result = _build_editable_document_final_verdict(
        document_id=428,
        title="Retomada de veículo",
        version_number=16,
        sections=[],
        export_text="""
        ENDEREÇAMENTO
        EXCELENTÍSSIMO(A) SENHOR(A) DOUTOR(A) DE [COMARCA A DEFINIR PELO ADVOGADO].
        QUALIFICAÇÃO DAS PARTES
        CPF nº [CPF a complementar].
        RESUMO FÁTICO
        O objetivo é montar o caso para avaliação de advogado.
        FUNDAMENTAÇÃO
        PEDIDOS
        PROVAS E REQUERIMENTOS
        FECHAMENTO
        Valor da causa R$ [valor a ser definido pelo advogado].
        """,
    )

    assert result["final_decision"] == "APROVADO APENAS PARA ADVOGADO AVALIAR"
    assert result["risk_level"] == "médio"
    assert "Checklist Final" in result["missing_blocks"]
    assert result["placeholders"]
    assert result["operational_text_flags"]
    assert result["critical_pending"]


def test_final_verdict_approves_clean_complete_export_text():
    result = _build_editable_document_final_verdict(
        document_id=1,
        title="Peça completa",
        version_number=3,
        sections=[],
        export_text="""
        ENDEREÇAMENTO
        QUALIFICAÇÃO DAS PARTES
        RESUMO FÁTICO
        FUNDAMENTAÇÃO
        PEDIDOS
        PEDIDOS E VALORES ESTIMADOS
        PROVAS E REQUERIMENTOS
        FECHAMENTO
        CHECKLIST FINAL
        Valor da causa: R$ 10.000,00.
        Advogado responsável: Nome Exemplo. OAB/SC 00000.
        """,
    )

    assert result["final_decision"] == "APROVADO COMO BENCHMARK"
    assert result["critical_pending"] == []
    assert result["missing_blocks"] == []
