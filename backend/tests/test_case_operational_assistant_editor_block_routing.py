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


def test_editor_block_fundamentacao_gets_structured_revision_not_plain_echo():
    message = """
verifique o bloco fundamentação se esta de acordo

Fundamentação — draft (assisted_draft)
I. Do cabimento da pretensão. À luz do quadro fático narrado, a demanda deve ser estruturada para tutelar o direito material afirmado e enfrentar a controvérsia central com base na prova já disponível.

II. Dos fundamentos normativos aplicáveis:
- Código de Defesa do Consumidor — relação de consumo, responsabilidade do fornecedor, vício/defeito do produto ou serviço e práticas abusivas.
- Código Civil — responsabilidade civil, perdas e danos e inadimplemento quando aplicável.
- Código de Processo Civil — tutela de urgência, produção de prova, inversão do ônus probatório quando cabível e técnicas executivas.
- Constituição Federal, art. 5º e art. 170 — acesso à justiça, defesa do consumidor e ordem econômica.

III. Da estratégia jurídica sugerida. Prosseguir com cautela estratégica, reforçando documentação, cálculo e linha do tempo dos fatos antes da decisão final de litigar.

IV. Dos pontos controvertidos que exigem enfrentamento direto:
- Relação de consumo com revendedora de veículos, exigindo validação do fornecedor, contrato, negociação e documentos do veículo.
- Pagamentos relevantes por Pix e entrada com bens usados, exigindo conferência de valores, destinatário dos Pix, notas promissórias e eventual saldo discutido.
- Retomada/recolhimento do veículo sob alegação de suposto bloqueio, sem documentação clara apresentada até o momento.

V. Das lacunas probatórias a suprir antes do protocolo definitivo:
- Relação de consumo com revendedora de veículos, exigindo validação do fornecedor, contrato, negociação e documentos do veículo.
- Pagamentos relevantes por Pix e entrada com bens usados, exigindo conferência de valores, destinatário dos Pix, notas promissórias e eventual saldo discutido.
- Retomada/recolhimento do veículo sob alegação de suposto bloqueio, sem documentação clara apresentada até o momento.
"""

    response = _fallback_response(
        case=_fake_case(),
        message=message,
        context={},
        timeline=[],
    )

    destinations = [action["destination"] for action in response["suggested_actions"]]
    suggested_text = response["suggested_actions"][0]["suggested_text"]
    replacement = suggested_text.split("Texto sugerido para substituir:", 1)[1].split("Ação agora:", 1)[0]

    assert destinations == ["editor_minuta"]
    assert "Revisar bloco: Fundamentação" in response["suggested_actions"][0]["label"]
    assert "O bloco está viável, mas precisa ajuste estrutural" in suggested_text
    assert "II. Da relação de consumo e dos deveres de informação e transparência." in replacement
    assert "IV. Da retomada/recolhimento do veículo" in replacement
    assert "V. Da exibição de documentos e da produção de prova." in replacement
    assert "Não se deve afirmar, sem prova suficiente" in replacement
    assert "III. Da estratégia jurídica sugerida" not in replacement
    assert replacement.count("Relação de consumo com revendedora de veículos") == 0
    assert "linha_do_tempo" not in destinations
    assert "anexos" not in destinations


def test_all_known_editable_blocks_route_to_editor_minuta():
    block_names = [
        "Endereçamento",
        "Qualificação das Partes",
        "Resumo Fático",
        "Fundamentação",
        "Pedidos",
        "Pedidos e Valores Estimados",
        "Provas e Requerimentos",
        "Checklist Final",
        "Fechamento",
    ]

    for block_name in block_names:
        message = f"""
verifique o bloco {block_name} se esta de acordo

{block_name} — draft (assisted_draft)
Texto base do bloco {block_name}, pendente de validação profissional.
"""

        response = _fallback_response(
            case=_fake_case(),
            message=message,
            context={},
            timeline=[],
        )

        destinations = [action["destination"] for action in response["suggested_actions"]]

        assert destinations == ["editor_minuta"], block_name
        assert response["rewritten_input"] == "", block_name
        assert "linha_do_tempo" not in destinations, block_name
        assert "anexos" not in destinations, block_name


def test_editor_block_pedidos_detects_header_before_fechamento_word_and_rewrites_points_as_requests():
    message = """
verifique o bloco pedidos se esta de acordo

Pedidos — draft (assisted_draft)
I. Requer-se, quando presentes os requisitos legais, a concessão da tutela provisória cabível para resguardar desde logo a utilidade do provimento final.

II. Pedidos principais sugeridos para a minuta final:
- Relação de consumo com revendedora de veículos, exigindo validação do fornecedor, contrato, negociação e documentos do veículo.
- Pagamentos relevantes por Pix e entrada com bens usados, exigindo conferência de valores, destinatário dos Pix, notas promissórias e eventual saldo discutido.
- Retomada/recolhimento do veículo sob alegação de suposto bloqueio, sem documentação clara apresentada até o momento.
- Necessário verificar se houve ordem judicial, busca e apreensão, bloqueio administrativo, restrição no Detran ou mera alegação comercial da revendedora.
- Avaliar exibição de contrato/documentos, restituição do veículo ou devolução de valores, danos materiais/morais e tutela de urgência conforme prova disponível.

V. O enquadramento provisório da análise indica a seguinte diretriz para fechamento dos pedidos: MODERADA.
"""

    response = _fallback_response(
        case=_fake_case(),
        message=message,
        context={},
        timeline=[],
    )

    action = response["suggested_actions"][0]
    destinations = [item["destination"] for item in response["suggested_actions"]]
    suggested_text = action["suggested_text"]
    replacement = suggested_text.split("Texto sugerido para substituir:", 1)[1].split("Ação agora:", 1)[0]

    assert destinations == ["editor_minuta"]
    assert action["label"] == "Revisar bloco: Pedidos"
    assert "Bloco: Pedidos." in suggested_text
    assert "O bloco precisa ajuste estrutural" in suggested_text

    assert "II. Da exibição do contrato e documentos da negociação." in replacement
    assert "III. Da prestação de contas e apuração dos valores pagos." in replacement
    assert "IV. Do esclarecimento formal do suposto bloqueio" in replacement
    assert "V. Da restituição do veículo ou devolução de valores" in replacement
    assert "VI. Dos danos materiais e morais, se comprovados." in replacement

    assert "Relação de consumo com revendedora de veículos, exigindo validação" not in replacement
    assert "Pagamentos relevantes por Pix e entrada com bens usados" not in replacement
    assert "diretriz para fechamento dos pedidos: MODERADA" not in replacement
    assert "linha_do_tempo" not in destinations
    assert "anexos" not in destinations


def test_editor_block_pedidos_valores_estimados_gets_structured_revision_not_placeholder():
    message = """
verifique o campo pedidos e valores estimados

Pedidos e Valores Estimados — draft (assisted_draft)
Os pedidos deverão ser acompanhados de indicação de valores estimados ou liquidados antes do protocolo, conforme os dados disponíveis no caso e a memória de cálculo revisada pelo advogado responsável.

Valor da causa atualmente informado: R$ [valor a ser definido pelo advogado].

Caso ainda não exista memória de cálculo, recomenda-se inserir os valores por pedido antes do ajuizamento, com indicação expressa de eventual natureza estimativa/preliminar.
"""

    response = _fallback_response(
        case=_fake_case(),
        message=message,
        context={},
        timeline=[],
    )

    action = response["suggested_actions"][0]
    destinations = [item["destination"] for item in response["suggested_actions"]]
    suggested_text = action["suggested_text"]
    replacement = suggested_text.split("Texto sugerido para substituir:", 1)[1].split("Ação agora:", 1)[0]

    assert destinations == ["editor_minuta"]
    assert action["label"] == "Revisar bloco: Pedidos e Valores Estimados"
    assert "Bloco: Pedidos e Valores Estimados." in suggested_text
    assert "O bloco está viável, mas precisa deixar de ser apenas orientação genérica" in suggested_text

    assert "[Cole aqui o texto revisado" not in suggested_text
    assert "I. Do valor da causa." in replacement
    assert "II. Dos valores a apurar por pedido." in replacement
    assert "III. Da memória de cálculo." in replacement
    assert "IV. Dos valores estimados ou pendentes de liquidação." in replacement
    assert "V. Da cautela antes do protocolo." in replacement

    assert "linha_do_tempo" not in destinations
    assert "anexos" not in destinations

def test_editor_block_pedidos_valores_uses_known_case_amounts_from_context():
    message = """
verifique o campo pedidos e valores estimados

Pedidos e Valores Estimados — draft (assisted_draft)
Os pedidos deverão ser acompanhados de indicação de valores estimados ou liquidados antes do protocolo.
"""

    context = {
        "case_summary": (
            "Cliente relata 34 parcelas de R$ 1.180,00 via Pix, total R$ 40.120,00. "
            "Entrada informada de R$ 15.000,00 com Scenic e Honda. "
            "Valor econômico preliminar informado: R$ 55.120,00."
        )
    }

    response = _fallback_response(
        case=_fake_case(),
        message=message,
        context=context,
        timeline=[],
    )

    action = response["suggested_actions"][0]
    destinations = [item["destination"] for item in response["suggested_actions"]]
    suggested_text = action["suggested_text"]
    replacement = suggested_text.split("Texto sugerido para substituir:", 1)[1].split("Ação agora:", 1)[0]

    assert destinations == ["editor_minuta"]
    assert action["label"] == "Revisar bloco: Pedidos e Valores Estimados"
    assert "Valores preliminares já identificados no caso" in replacement
    assert "34 parcelas de R$ 1.180,00" in replacement
    assert "R$ 40.120,00" in replacement
    assert "R$ 15.000,00" in replacement
    assert "R$ 55.120,00" in replacement
    assert "sujeitos à conferência documental" in replacement
    assert "linha_do_tempo" not in destinations
    assert "anexos" not in destinations
