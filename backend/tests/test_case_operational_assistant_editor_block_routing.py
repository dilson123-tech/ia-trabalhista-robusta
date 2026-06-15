from types import SimpleNamespace

from app.services.case_operational_assistant import _fallback_response


def _fake_case():
    return SimpleNamespace(id=428, case_number="VEICULO-QUINTINO-PIX-001")


def _joined_response_text(response: dict) -> str:
    parts: list[str] = [
        response.get("summary") or "",
        response.get("rewritten_input") or "",
        "\n".join(response.get("next_steps") or []),
        "\n".join(response.get("warnings") or []),
    ]

    for action in response.get("suggested_actions") or []:
        parts.extend(
            [
                action.get("destination") or "",
                action.get("label") or "",
                action.get("suggested_text") or "",
                action.get("reason") or "",
            ]
        )

    return "\n".join(parts)


def test_editor_block_correction_routes_enderecamento_to_editor_not_timeline():
    message = """
corrige esse
Versão atual
Número: 2
Aprovada: Não
Notas: Minuta assistida gerada a partir da análise do caso

Blocos da versão
Endereçamento — draft (assisted_draft)
EXCELENTÍSSIMO(A) SENHOR(A) DOUTOR(A) JUIZ(A) DE DIREITO DO JUÍZO COMPETENTE DA COMARCA DE [COMARCA A DEFINIR PELO ADVOGADO].

Na versão final, o advogado deverá confirmar a competência territorial, o órgão jurisdicional, eventual prevenção e o rito adequado antes do protocolo.

Editar bloco
"""

    response = _fallback_response(
        case=_fake_case(),
        message=message,
        context={},
        timeline=[],
    )

    output = _joined_response_text(response)
    destinations = [action["destination"] for action in response["suggested_actions"]]

    assert response["rewritten_input"] == ""
    assert response["metadata"]["source"] == "case_operational_assistant_editor_block_correction_routing_v1"
    assert destinations == ["editor_minuta"]

    assert "Revisar bloco: Endereçamento" in output
    assert "[COMARCA A CONFIRMAR PELO ADVOGADO]" in output
    assert "[COMARCAA" not in output

    assert "linha_do_tempo" not in destinations
    assert "anexos" not in destinations
    assert "Não salvar este conteúdo na Linha do Tempo" in output


def test_editor_block_correction_routes_resumo_fatico_to_editor_and_removes_strategy_tail():
    message = """
como esta esse resumo fatico, t bom ou precisa mexer

Resumo Fático — draft (assisted_draft)
Trata-se do caso VEICULO-QUINTINO-PIX-001 — Retomada de veículo por revendedora após pagamento parcelado via Pix.

Cliente relata que adquiriu veículo junto à revendedora QUINTINO COMÉRCIO DE AUTOMÓVEIS LTDA, nome fantasia QUINTINO AUTOMÓVEIS, CNPJ 15.304.437/0001-96, mediante negociação parcelada por nota promissória ou contrato. Informa que pagou 34 parcelas de R$ 1.180,00 via Pix. O cliente informa que perdeu sua via física do contrato, mas possui comprovantes Pix dos pagamentos. Após os pagamentos, relata que a revendedora tomou ou recolheu o veículo alegando que ele estaria “em bloqueio”, sem apresentar, até o momento, ordem judicial, cópia do contrato ou justificativa completa. O objetivo é montar o caso para avaliação de advogado, com possível pedido de exibição de contrato e documentos, restituição do veículo ou indenização.
"""

    response = _fallback_response(
        case=_fake_case(),
        message=message,
        context={},
        timeline=[],
    )

    output = _joined_response_text(response)
    destinations = [action["destination"] for action in response["suggested_actions"]]

    assert response["rewritten_input"] == ""
    assert destinations == ["editor_minuta"]

    assert "Revisar bloco: Resumo Fático" in output
    assert "O bloco está viável, mas deve permanecer narrativo" in output
    assert "A narrativa permanece sujeita à validação documental" in output
    assert "O objetivo é montar" not in output

    assert "linha_do_tempo" not in destinations
    assert "anexos" not in destinations


def test_editor_block_correction_preserves_inline_resumo_fatico_body():
    message = (
        "como esta esse resumo fatico, t bom ou precisa mexer "
        "Resumo Fático — draft (assisted_draft) "
        "Trata-se do caso VEICULO-QUINTINO-PIX-001 — Retomada de veículo por revendedora após pagamento parcelado via Pix. "
        "Cliente relata que adquiriu veículo junto à revendedora QUINTINO COMÉRCIO DE AUTOMÓVEIS LTDA. "
        "Informa que pagou 34 parcelas de R$ 1.180,00 via Pix. "
        "O cliente informa que perdeu sua via física do contrato, mas possui comprovantes Pix dos pagamentos. "
        "Após os pagamentos, relata que a revendedora tomou ou recolheu o veículo alegando que ele estaria em bloqueio. "
        "O objetivo é montar o caso para avaliação de advogado, com possível pedido de exibição de contrato e documentos."
    )

    response = _fallback_response(
        case=_fake_case(),
        message=message,
        context={},
        timeline=[],
    )

    output = _joined_response_text(response)
    destinations = [action["destination"] for action in response["suggested_actions"]]

    assert destinations == ["editor_minuta"]
    assert "Texto sugerido para substituir:" in output
    assert "Trata-se do caso VEICULO-QUINTINO-PIX-001" in output
    assert "Cliente relata que adquiriu veículo" in output
    assert "34 parcelas de R$ 1.180,00" in output
    assert "A narrativa permanece sujeita à validação documental" in output
    assert "O objetivo é montar" not in output
    assert "linha_do_tempo" not in destinations
    assert "anexos" not in destinations


def test_editor_block_verification_phrase_routes_to_editor_before_evidence_guidance():
    message = """
verifique o resumo fatico se esta de acordo

Resumo Fático — draft (assisted_draft)
Trata-se do caso VEICULO-QUINTINO-PIX-001 — Retomada de veículo por revendedora após pagamento parcelado via Pix.

Cliente relata que adquiriu veículo junto à revendedora QUINTINO COMÉRCIO DE AUTOMÓVEIS LTDA, nome fantasia QUINTINO AUTOMÓVEIS, CNPJ 15.304.437/0001-96, mediante negociação parcelada por nota promissória ou contrato. Informa que entregou como entrada um veículo Scenic 2004 avaliado em R$ 4.000,00 e uma motocicleta Honda CBX 300 avaliada em R$ 11.000,00, além de ter pago 34 parcelas de R$ 1.180,00 via Pix, totalizando R$ 40.120,00 em parcelas pagas. Considerando a entrada informada de R$ 15.000,00, há possível valor econômico total de R$ 55.120,00, pendente de conferência documental. O cliente informa que perdeu sua via física do contrato, mas possui comprovantes Pix dos pagamentos. Após os pagamentos, relata que a revendedora tomou ou recolheu o veículo alegando que ele estaria “em bloqueio”, sem apresentar, até o momento, ordem judicial, cópia do contrato, prestação de contas, documento formal da dívida, comprovante de busca e apreensão, comprovação do suposto bloqueio ou justificativa completa. O objetivo é montar o caso para avaliação de advogado, com possível pedido de exibição de contrato e documentos, esclarecimento da dívida e do alegado bloqueio, restituição do veículo ou devolução dos valores pagos, além de eventual indenização por danos materiais e morais e análise de tutela de urgência.
"""

    response = _fallback_response(
        case=_fake_case(),
        message=message,
        context={},
        timeline=[],
    )

    output = _joined_response_text(response)
    destinations = [action["destination"] for action in response["suggested_actions"]]

    assert response["rewritten_input"] == ""
    assert destinations == ["editor_minuta"]
    assert "Revisar bloco: Resumo Fático" in output
    assert "Texto sugerido para substituir:" in output
    assert "Trata-se do caso VEICULO-QUINTINO-PIX-001" in output
    assert "Cliente relata que adquiriu veículo" in output
    assert "34 parcelas de R$ 1.180,00" in output
    assert "A narrativa permanece sujeita à validação documental" in output
    assert "O objetivo é montar" not in output
    assert "linha_do_tempo" not in destinations
    assert "anexos" not in destinations


def test_editor_block_resumo_fatico_replacement_keeps_readable_paragraphs():
    message = """
como está esse resumo fático, tá bom ou precisa mexer?

Resumo Fático — draft (assisted_draft)
Trata-se do caso VEICULO-QUINTINO-PIX-001 — Retomada de veículo por revendedora após pagamento parcelado via Pix. Cliente relata que adquiriu veículo junto à revendedora QUINTINO COMÉRCIO DE AUTOMÓVEIS LTDA. Informa que entregou como entrada um veículo Scenic 2004 avaliado em R$ 4.000,00 e uma motocicleta Honda CBX 300 avaliada em R$ 11.000,00, além de ter pago 34 parcelas de R$ 1.180,00 via Pix. Considerando a entrada informada de R$ 15.000,00, há possível valor econômico total de R$ 55.120,00, pendente de conferência documental. O cliente informa que perdeu sua via física do contrato, mas possui comprovantes Pix dos pagamentos. Após os pagamentos, relata que a revendedora tomou ou recolheu o veículo alegando que ele estaria “em bloqueio”. O objetivo é montar o caso para avaliação de advogado, com possível pedido de exibição de contrato e documentos.
"""

    response = _fallback_response(
        case=_fake_case(),
        message=message,
        context={},
        timeline=[],
    )

    output = _joined_response_text(response)
    destinations = [action["destination"] for action in response["suggested_actions"]]

    assert destinations == ["editor_minuta"]
    assert "Trata-se do caso VEICULO-QUINTINO-PIX-001" in output
    assert "\n\nCliente relata que adquiriu veículo" in output
    assert "\n\nInforma que entregou como entrada" in output
    assert "\n\nConsiderando a entrada informada" in output
    assert "\n\nO cliente informa que perdeu sua via física do contrato" in output
    assert "\n\nApós os pagamentos" in output
    assert "\n\nA narrativa permanece sujeita à validação documental" in output
    assert "O objetivo é montar" not in output
