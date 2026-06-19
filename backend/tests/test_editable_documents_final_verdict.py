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
    assert "Comarca/foro competente" in result["required_data_pending"]
    assert "CPF da parte autora" in result["required_data_pending"]
    assert "Valor da causa" in result["required_data_pending"]
    assert result["cause_value_analysis"]["status"] == "pendente"
    assert result["cause_value_analysis"]["has_value"] is False
    assert result["cause_value_analysis"]["pending_items"]
    assert "Advogado responsável" in result["required_data_pending"]
    assert "OAB/UF do advogado" in result["required_data_pending"]
    assert result["operational_text_flags"]
    assert result["critical_pending"]
    assert result["benchmark_analysis"]["benchmark_ready"] is False
    assert result["benchmark_analysis"]["status"] == "bloqueado_para_benchmark"
    assert result["benchmark_analysis"]["blocking_reasons"]
    assert result["preliminary_draft_analysis"]["is_preliminary_draft"] is True
    assert "Comarca/foro competente" in result["preliminary_draft_analysis"]["formal_pending_items"]
    assert "Advogado responsável" in result["preliminary_draft_analysis"]["formal_pending_items"]


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
        A parte autora realizou pagamento por Pix, com comprovantes de Pix vinculados aos valores pagos.
        FUNDAMENTAÇÃO
        PEDIDOS
        Requer a restituição dos valores pagos conforme a prova documental apresentada.
        PEDIDOS E VALORES ESTIMADOS
        PROVAS E REQUERIMENTOS
        Comprovantes de Pix e comprovantes de pagamento serão conferidos por data, valor e destinatário.
        FECHAMENTO
        CHECKLIST FINAL
        Valor da causa: R$ 10.000,00.
        Memória mínima de cálculo: valor principal estimado de R$ 10.000,00, correspondente aos pedidos economicamente quantificados nesta versão.
        Advogado responsável: Nome Exemplo. OAB/SC 00000.
        """,
    )

    assert result["final_decision"] == "APROVADO COMO BENCHMARK"
    assert result["critical_pending"] == []
    assert result["missing_blocks"] == []
    assert result["required_data_pending"] == []
    assert result["cause_value_analysis"]["status"] in {"informado", "estimado", "calculado"}
    assert result["cause_value_analysis"]["has_value"] is True
    assert result["cause_value_analysis"]["has_minimum_calculation"] is True
    assert result["fact_proof_request_links"]
    assert result["benchmark_analysis"]["benchmark_ready"] is True
    assert result["benchmark_analysis"]["status"] == "pronto_para_benchmark"
    assert result["benchmark_analysis"]["score"] == 100
    assert result["benchmark_analysis"]["blocking_reasons"] == []
    assert result["benchmark_analysis"]["caution_points"] == []
    assert result["preliminary_draft_analysis"]["is_preliminary_draft"] is False



def test_final_verdict_flags_value_without_minimum_calculation_as_non_critical_pending():
    result = _build_editable_document_final_verdict(
        document_id=2,
        title="Peça com valor sem memória",
        version_number=4,
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

    assert result["cause_value_analysis"]["status"] == "informado"
    assert result["cause_value_analysis"]["has_value"] is True
    assert result["cause_value_analysis"]["has_minimum_calculation"] is False
    assert "Valor da causa informado sem memória mínima de cálculo ou justificativa técnica explícita." in result["non_critical_pending"]
    assert result["final_decision"] == "APROVADO APENAS PARA ADVOGADO AVALIAR"
    assert result["benchmark_analysis"]["benchmark_ready"] is False
    assert result["benchmark_analysis"]["status"] == "quase_pronto_com_ressalvas"
    assert result["benchmark_analysis"]["caution_points"]



def test_final_verdict_builds_fact_proof_request_links_for_common_consumer_case():
    result = _build_editable_document_final_verdict(
        document_id=428,
        title="Retomada de veículo",
        version_number=21,
        sections=[],
        export_text="""
        ENDEREÇAMENTO
        QUALIFICAÇÃO DAS PARTES
        RESUMO FÁTICO
        A parte autora relata pagamento por Pix das parcelas do veículo, com comprovantes de Pix e comprovantes de pagamento.
        Também relata retomada do veículo pela revendedora, com fotos, vídeo e boletim de ocorrência.
        O contrato não localizado deverá ser exibido pela parte ré.
        FUNDAMENTAÇÃO
        PEDIDOS
        Requer restituição dos valores pagos, exibição do contrato e tutela de urgência para restituição do bem.
        PEDIDOS E VALORES ESTIMADOS
        Valor da causa: R$ 10.000,00.
        Memória mínima de cálculo: valores pagos por Pix estimados em R$ 10.000,00, sujeitos à conferência documental.
        PROVAS E REQUERIMENTOS
        Comprovantes de Pix, fotos, vídeo, boletim de ocorrência e pedido de exibição de contrato.
        FECHAMENTO
        CHECKLIST FINAL
        Advogado responsável: Nome Exemplo. OAB/SC 00000.
        """,
    )

    links = result["fact_proof_request_links"]

    assert any("Pagamento" in link["fact"] for link in links)
    assert any("Retomada" in link["fact"] for link in links)
    assert any("Relação contratual" in link["fact"] for link in links)
    assert any("restituição" in link["request"].lower() for link in links)
    assert any("Exibição" in link["request"] or "exibição" in link["request"] for link in links)
    assert result["final_decision"] in {
        "APROVADO COMO BENCHMARK",
        "APROVADO APENAS PARA ADVOGADO AVALIAR",
    }



def test_final_verdict_explains_formal_pending_as_preliminary_draft():
    result = _build_editable_document_final_verdict(
        document_id=428,
        title="Minuta preliminar para avaliação",
        version_number=23,
        sections=[],
        export_text="""
        ENDEREÇAMENTO
        EXCELENTÍSSIMO(A) SENHOR(A) DOUTOR(A) DE [COMARCA A DEFINIR PELO ADVOGADO].
        QUALIFICAÇÃO DAS PARTES
        [NOME COMPLETO DA PARTE AUTORA], CPF nº [CPF a complementar].
        RESUMO FÁTICO
        Pagamento por Pix com comprovantes de pagamento.
        FUNDAMENTAÇÃO
        PEDIDOS
        Requer restituição dos valores pagos.
        PEDIDOS E VALORES ESTIMADOS
        Valor da causa: R$ [valor a ser definido pelo advogado].
        PROVAS E REQUERIMENTOS
        Comprovantes de pagamento por Pix.
        FECHAMENTO
        Dá-se à causa o valor de R$ [valor a ser definido pelo advogado].
        [Local], [data].
        [Nome do advogado] — OAB/[UF] [número].
        CHECKLIST FINAL
        """,
    )

    analysis = result["preliminary_draft_analysis"]

    assert result["final_decision"] == "APROVADO APENAS PARA ADVOGADO AVALIAR"
    assert analysis["is_preliminary_draft"] is True
    assert "Comarca/foro competente" in analysis["formal_pending_items"]
    assert "Advogado responsável" in analysis["formal_pending_items"]
    assert "OAB/UF do advogado" in analysis["formal_pending_items"]
    assert "CPF da parte autora" in analysis["party_pending_items"]
    assert "impedem protocolo e benchmark final" in analysis["summary"]



def test_final_verdict_uses_sanitized_export_for_legacy_operational_request_direction():
    from app.api.v1.routes.editable_documents import (
        _build_editable_document_final_verdict,
        _strip_html_for_final_verdict,
    )
    from app.services.editor_export_service import build_editor_html

    html = build_editor_html(
        {
            "title": "Minuta preliminar genérica",
            "area": "consumidor",
            "document_type": "peticao_inicial",
        },
        {
            "version_number": 7,
            "sections": [
                {
                    "title": "Endereçamento",
                    "content": "EXCELENTÍSSIMO(A) SENHOR(A) DE [COMARCA A DEFINIR PELO ADVOGADO].",
                    "metadata": {"export_visibility": "final", "include_in_final_pdf": True},
                },
                {
                    "title": "Qualificação das Partes",
                    "content": "[NOME COMPLETO DA PARTE AUTORA], CPF nº [CPF a complementar].",
                    "metadata": {"export_visibility": "final", "include_in_final_pdf": True},
                },
                {
                    "title": "Resumo Fático",
                    "content": "A parte autora relata pagamento por Pix e retenção indevida de bem.",
                    "metadata": {"export_visibility": "final", "include_in_final_pdf": True},
                },
                {
                    "title": "Fundamentação",
                    "content": "Fundamentação preliminar sujeita à revisão profissional.",
                    "metadata": {"export_visibility": "final", "include_in_final_pdf": True},
                },
                {
                    "title": "Pedidos",
                    "content": (
                        "Requer exibição de documentos e apuração dos valores pagos. "
                        "V. O enquadramento provisório da análise indica a seguinte diretriz "
                        "para fechamento dos pedidos: MODERADA. "
                        "VI. Antes do protocolo definitivo, o advogado deverá revisar a aderência."
                    ),
                    "metadata": {"export_visibility": "final", "include_in_final_pdf": True},
                },
                {
                    "title": "Pedidos e Valores Estimados",
                    "content": "Valor da causa: R$ [valor a ser definido pelo advogado].",
                    "metadata": {"export_visibility": "final", "include_in_final_pdf": True},
                },
                {
                    "title": "Provas e Requerimentos",
                    "content": "Comprovantes de pagamento por Pix e documentos pendentes.",
                    "metadata": {"export_visibility": "final", "include_in_final_pdf": True},
                },
                {
                    "title": "Fechamento",
                    "content": "[Local], [data]. [Nome do advogado] — OAB/[UF] [número].",
                    "metadata": {"export_visibility": "final", "include_in_final_pdf": True},
                },
                {
                    "title": "Checklist Final para Protocolo",
                    "content": "Conferir dados formais e revisão profissional.",
                    "metadata": {"export_visibility": "final", "include_in_final_pdf": True},
                },
            ],
        },
    )

    export_text = _strip_html_for_final_verdict(html)
    result = _build_editable_document_final_verdict(
        document_id=999,
        title="Minuta preliminar genérica",
        version_number=7,
        sections=[],
        export_text=export_text,
    )

    assert "diretriz para fechamento dos pedidos" not in export_text.lower()
    assert "fechamento dos pedidos: moderada" not in export_text.lower()
    assert "A definição final dos pedidos deverá observar" in export_text
    assert result["preliminary_draft_analysis"]["is_preliminary_draft"] is True
    assert result["benchmark_analysis"]["benchmark_ready"] is False
