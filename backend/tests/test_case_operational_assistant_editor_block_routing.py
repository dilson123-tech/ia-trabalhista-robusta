from types import SimpleNamespace

from app.services.case_operational_assistant import _fallback_response


def _fake_case(
    description: str = "",
    title: str = "",
    legal_area: str = "",
    action_type: str = "",
    case_number: str = "VEICULO-QUINTINO-PIX-001",
):
    return SimpleNamespace(
        id=428,
        case_number=case_number,
        description=description,
        title=title,
        legal_area=legal_area,
        action_type=action_type,
    )


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


def test_editor_block_pedidos_valores_uses_known_case_amounts_from_case_description():
    message = """
verifique o campo pedidos e valores estimados

Pedidos e Valores Estimados — draft (assisted_draft)
Os pedidos deverão ser acompanhados de indicação de valores estimados ou liquidados antes do protocolo.
"""

    case = _fake_case(
        description=(
            "Cliente relata compra de veículo por nota promissória/parcelamento. "
            "Foram informadas 34 parcelas de R$ 1.180,00 via Pix, total R$ 40.120,00. "
            "Entrada informada: R$ 15.000,00, com Scenic 2004 e Honda CBX 300. "
            "Valor econômico preliminar informado: R$ 55.120,00."
        )
    )

    response = _fallback_response(
        case=case,
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
    assert "Valores preliminares já identificados no caso" in replacement
    assert "34 parcelas de R$ 1.180,00" in replacement
    assert "R$ 40.120,00" in replacement
    assert "R$ 15.000,00" in replacement
    assert "R$ 55.120,00" in replacement
    assert "sujeitos à conferência documental" in replacement
    assert "linha_do_tempo" not in destinations
    assert "anexos" not in destinations


def test_editor_block_provas_requerimentos_gets_structured_vehicle_revision():
    message = """
verifique o bloco provas e requerimentos

Provas e Requerimentos — draft (assisted_draft)
Requer-se a produção de todos os meios de prova em direito admitidos, especialmente documental, testemunhal e pericial, conforme a natureza das controvérsias identificadas.
"""

    case = _fake_case(
        description=(
            "Cliente relata compra de veículo com revendedora, 34 parcelas via Pix, "
            "entrada com bens usados, contrato perdido e retomada/recolhimento do veículo "
            "sob alegação de suposto bloqueio, pendente de conferência documental."
        )
    )

    response = _fallback_response(
        case=case,
        message=message,
        context={},
        timeline=[],
    )

    action = response["suggested_actions"][0]
    destinations = [item["destination"] for item in response["suggested_actions"]]
    suggested_text = action["suggested_text"]
    replacement = suggested_text.split("Texto sugerido para substituir:", 1)[1].split("Ação agora:", 1)[0]

    assert destinations == ["editor_minuta"]
    assert action["label"] == "Revisar bloco: Provas e Requerimentos"
    assert "O bloco está viável, mas precisa deixar de ser genérico" in suggested_text

    assert "I. Das provas documentais já informadas pelo cliente." in replacement
    assert "II. Das provas documentais pendentes de juntada ou conferência." in replacement
    assert "III. Da exibição de documentos pela parte ré." in replacement
    assert "IV. Das diligências e consultas úteis." in replacement
    assert "V. Da prova testemunhal." in replacement
    assert "VI. Da cautela quanto à prova." in replacement
    assert "VII. Dos requerimentos probatórios finais." in replacement

    assert "simples relato como prova documental já confirmada" in replacement
    assert "contrato ou instrumento de negociação" in replacement
    assert "registro do suposto bloqueio" in replacement
    assert "Não se deve afirmar que houve bloqueio irregular, fraude, abuso, dano ou responsabilidade definitiva" in replacement

    assert "linha_do_tempo" not in destinations
    assert "anexos" not in destinations

def test_editor_block_provas_requerimentos_gets_generic_structured_revision():
    message = """
verifique o bloco provas e requerimentos

Provas e Requerimentos — draft (assisted_draft)
Requer-se a produção de todos os meios de prova em direito admitidos, especialmente documental, testemunhal e pericial.
"""

    case = _fake_case(
        case_number="CONTRATO-GENERICO-001",
        description=(
            "Cliente relata controvérsia contratual com documentos pendentes de conferência, "
            "mensagens a validar, possíveis testemunhas e necessidade de exibição de documentos."
        )
    )

    response = _fallback_response(
        case=case,
        message=message,
        context={},
        timeline=[],
    )

    action = response["suggested_actions"][0]
    destinations = [item["destination"] for item in response["suggested_actions"]]
    suggested_text = action["suggested_text"]
    replacement = suggested_text.split("Texto sugerido para substituir:", 1)[1].split("Ação agora:", 1)[0]

    assert destinations == ["editor_minuta"]
    assert action["label"] == "Revisar bloco: Provas e Requerimentos"
    assert "O bloco está viável, mas precisa deixar de ser genérico" in suggested_text

    assert "I. Das provas documentais já informadas." in replacement
    assert "II. Das provas pendentes de juntada ou conferência." in replacement
    assert "III. Da exibição de documentos e informações." in replacement
    assert "IV. Das diligências e demais meios de prova." in replacement
    assert "V. Da cautela quanto à prova." in replacement

    assert "evitando afirmar como provado aquilo que ainda exige validação" in replacement
    assert "revendedora" not in replacement.lower()
    assert "veículo" not in replacement.lower()
    assert "bloqueio" not in replacement.lower()
    assert "linha_do_tempo" not in destinations
    assert "anexos" not in destinations


def test_editor_block_pedidos_generic_contract_pix_does_not_get_vehicle_revision():
    message = """
verifique o bloco pedidos se esta de acordo

Pedidos — draft (assisted_draft)
Caso de contrato de prestação de serviços, com pagamento via Pix, comprovantes pendentes e pedido de devolução de valores.
"""

    response = _fallback_response(
        case=_fake_case(case_number="CONTRATO-SERVICO-001"),
        message=message,
        context={},
        timeline=[],
    )

    action = response["suggested_actions"][0]
    destinations = [item["destination"] for item in response["suggested_actions"]]
    replacement = action["suggested_text"].split("Texto sugerido para substituir:", 1)[1].split("Ação agora:", 1)[0]

    assert destinations == ["editor_minuta"]
    assert action["label"] == "Revisar bloco: Pedidos"
    assert "II. Dos pedidos principais." in replacement
    assert "III. Da exibição de documentos e produção de prova." in replacement
    assert "revendedora" not in replacement.lower()
    assert "veículo" not in replacement.lower()
    assert "suposto bloqueio" not in replacement.lower()
    assert "linha_do_tempo" not in destinations
    assert "anexos" not in destinations


def test_editor_block_fundamentacao_consumer_generic_does_not_get_vehicle_revision():
    message = """
verifique o bloco fundamentação

Fundamentação — draft (assisted_draft)
Relação de consumo envolvendo fornecedor de serviço, contrato, pagamento via Pix, falha na prestação e documentos pendentes de conferência.
"""

    response = _fallback_response(
        case=_fake_case(case_number="CONSUMIDOR-SERVICO-001"),
        message=message,
        context={},
        timeline=[],
    )

    action = response["suggested_actions"][0]
    destinations = [item["destination"] for item in response["suggested_actions"]]
    replacement = action["suggested_text"].split("Texto sugerido para substituir:", 1)[1].split("Ação agora:", 1)[0]

    assert destinations == ["editor_minuta"]
    assert action["label"] == "Revisar bloco: Fundamentação"
    assert "II. Da relação de consumo, se confirmada." in replacement
    assert "III. Dos documentos, pagamentos e registros relevantes." in replacement
    assert "IV. Das lacunas probatórias e da necessidade de exibição ou complementação documental." in replacement
    assert "revendedora de veículos" not in replacement.lower()
    assert "retomada/recolhimento do veículo" not in replacement.lower()
    assert "suposto bloqueio" not in replacement.lower()
    assert "linha_do_tempo" not in destinations
    assert "anexos" not in destinations


def test_editor_block_resumo_fatico_generic_case_uses_universal_caution():
    message = """
verifique o resumo fático

Resumo Fático — draft (assisted_draft)
Cliente relata contrato de prestação de serviços, pagamento realizado, mensagens pendentes de conferência e possível descumprimento contratual.

O objetivo é montar uma ação com pedido de devolução de valores e indenização.
"""

    response = _fallback_response(
        case=_fake_case(case_number="CONTRATO-SERVICO-RESUMO-001"),
        message=message,
        context={},
        timeline=[],
    )

    action = response["suggested_actions"][0]
    destinations = [item["destination"] for item in response["suggested_actions"]]
    replacement = action["suggested_text"].split("Texto sugerido para substituir:", 1)[1].split("Ação agora:", 1)[0]

    assert destinations == ["editor_minuta"]
    assert action["label"] == "Revisar bloco: Resumo Fático"
    assert "A narrativa permanece sujeita à validação documental e revisão profissional" in replacement
    assert "confirmação dos fatos relatados" in replacement
    assert "pontos ainda pendentes de prova" in replacement
    assert "O objetivo é montar" not in replacement
    assert "Pix" not in replacement
    assert "suposto bloqueio" not in replacement
    assert "retomada/recolhimento do veículo" not in replacement
    assert "linha_do_tempo" not in destinations
    assert "anexos" not in destinations


def test_editor_block_resumo_fatico_vehicle_case_keeps_vehicle_caution():
    message = """
verifique o resumo fático

Resumo Fático — draft (assisted_draft)
Cliente relata compra de veículo em revendedora, pagamento parcelado via Pix, contrato perdido e retomada/recolhimento do veículo sob alegação de suposto bloqueio.

O objetivo é montar o caso para avaliação de advogado.
"""

    response = _fallback_response(
        case=_fake_case(),
        message=message,
        context={},
        timeline=[],
    )

    action = response["suggested_actions"][0]
    destinations = [item["destination"] for item in response["suggested_actions"]]
    replacement = action["suggested_text"].split("Texto sugerido para substituir:", 1)[1].split("Ação agora:", 1)[0]

    assert destinations == ["editor_minuta"]
    assert action["label"] == "Revisar bloco: Resumo Fático"
    assert "destinatário dos Pix" in replacement
    assert "motivo formal do suposto bloqueio" in replacement
    assert "circunstâncias da retomada/recolhimento do veículo" in replacement
    assert "O objetivo é montar" not in replacement
    assert "linha_do_tempo" not in destinations
    assert "anexos" not in destinations


def test_editor_block_pedidos_valores_uses_generic_amounts_without_pix_or_quintino_values():
    message = """
verifique pedidos e valores

Pedidos e Valores Estimados — draft (assisted_draft)
Cliente relata contrato de prestação de serviços com 12 parcelas de R$ 500,00, entrada de R$ 2.000,00 e valor econômico preliminar de R$ 8.000,00.
"""

    response = _fallback_response(
        case=_fake_case(
            case_number="CONTRATO-SERVICO-VALORES-001",
            description="Contrato de prestação de serviços com pagamento parcelado e entrada.",
        ),
        message=message,
        context={},
        timeline=[],
    )

    action = response["suggested_actions"][0]
    destinations = [item["destination"] for item in response["suggested_actions"]]
    replacement = action["suggested_text"].split("Texto sugerido para substituir:", 1)[1].split("Ação agora:", 1)[0]

    assert destinations == ["editor_minuta"]
    assert action["label"] == "Revisar bloco: Pedidos e Valores Estimados"
    assert "12 parcelas de R$ 500,00" in replacement
    assert "total preliminar de R$ 6.000,00" in replacement
    assert "Entrada informada: R$ 2.000,00" in replacement
    assert "Valor econômico preliminar informado: R$ 8.000,00" in replacement
    assert "comprovantes/documentos de pagamento" in replacement
    assert "comprovantes Pix" not in replacement
    assert "R$ 40.120,00" not in replacement
    assert "R$ 15.000,00" not in replacement
    assert "R$ 55.120,00" not in replacement


def test_editor_block_pedidos_valores_keeps_pix_language_when_context_mentions_pix():
    message = """
verifique pedidos e valores

Pedidos e Valores Estimados — draft (assisted_draft)
Cliente informa 34 parcelas de R$ 1.180,00 via Pix, entrada informada de R$ 15.000,00 e valor econômico preliminar de R$ 55.120,00.
"""

    response = _fallback_response(
        case=_fake_case(),
        message=message,
        context={},
        timeline=[],
    )

    action = response["suggested_actions"][0]
    replacement = action["suggested_text"].split("Texto sugerido para substituir:", 1)[1].split("Ação agora:", 1)[0]

    assert "34 parcelas de R$ 1.180,00" in replacement
    assert "total preliminar de R$ 40.120,00" in replacement
    assert "Entrada informada: R$ 15.000,00" in replacement
    assert "Valor econômico preliminar informado: R$ 55.120,00" in replacement
    assert "comprovantes Pix" in replacement


def test_editor_block_pedidos_uses_vehicle_case_context_when_body_is_generic():
    message = """
verifique pedidos

Pedidos — draft (assisted_draft)
Requer-se a procedência dos pedidos, com tutela provisória se cabível, exibição de documentos, produção de provas e condenação da parte ré nas medidas aplicáveis.
"""

    response = _fallback_response(
        case=_fake_case(
            description=(
                "Cliente relata compra de veículo junto à revendedora, pagamentos via Pix, "
                "perda do contrato e retomada/recolhimento do veículo sob alegação de suposto bloqueio."
            )
        ),
        message=message,
        context={},
        timeline=[],
    )

    action = response["suggested_actions"][0]
    destinations = [item["destination"] for item in response["suggested_actions"]]
    replacement = action["suggested_text"].split("Texto sugerido para substituir:", 1)[1].split("Ação agora:", 1)[0]

    assert destinations == ["editor_minuta"]
    assert action["label"] == "Revisar bloco: Pedidos"
    assert "Da exibição do contrato e documentos da negociação" in replacement
    assert "Da prestação de contas e apuração dos valores pagos" in replacement
    assert "Do esclarecimento formal do suposto bloqueio" in replacement
    assert "Da restituição do veículo ou devolução de valores" in replacement
    assert "linha_do_tempo" not in destinations
    assert "anexos" not in destinations


def test_editor_block_checklist_final_gets_structured_revision():
    message = """
verificar Checklist Final para Protocolo

Checklist Final para Protocolo — draft (assisted_draft)
Checklist interno de prontidão para protocolo. Este bloco serve como apoio operacional do escritório e deve ser revisado antes do ajuizamento.

Pendências e conferências obrigatórias:
- Informar e conferir CPF da parte autora.
- Informar e conferir CNPJ da parte ré.
- Definir ou revisar valor da causa antes do protocolo.
"""

    response = _fallback_response(
        case=_fake_case(case_number="CHECKLIST-GENERICO-001"),
        message=message,
        context={},
        timeline=[],
    )

    action = response["suggested_actions"][0]
    destinations = [item["destination"] for item in response["suggested_actions"]]
    replacement = action["suggested_text"].split("Texto sugerido para substituir:", 1)[1].split("Ação agora:", 1)[0]

    assert destinations == ["editor_minuta"]
    assert action["label"] == "Revisar bloco: Checklist Final"
    assert "I. Conferência da qualificação das partes." in replacement
    assert "II. Conferência do advogado responsável e assinatura." in replacement
    assert "III. Conferência da competência, rito e endereçamento." in replacement
    assert "IV. Conferência dos fatos, fundamentos e pedidos." in replacement
    assert "V. Conferência do valor da causa e cálculos." in replacement
    assert "VI. Conferência de documentos, anexos e provas." in replacement
    assert "VII. Conferência final antes do protocolo." in replacement
    assert "[Cole aqui o texto revisado" not in replacement
    assert "linha_do_tempo" not in destinations
    assert "anexos" not in destinations


def test_editor_block_pure_text_request_returns_only_rewritten_input():
    message = """
Reescreva somente o bloco Resumo Fático deste caso em formato de texto pronto para minuta preliminar.

Entregue apenas o texto final pronto para copiar e colar no bloco Resumo Fático do Editor/minuta.

Não traga checklist, linha do tempo, anexos, testemunhas, análise, próximos passos, alertas ou explicações.

Não invente dados. Use linguagem prudente, como “o Autor relata”, “segundo informado”, “a confirmar”, “até o momento” e “sujeito à conferência documental”.

Quando faltar informação, escreva “a confirmar”.

Comece direto pelo texto do bloco.
"""

    response = _fallback_response(
        case=_fake_case(
            description=(
                "Autor relata aquisição de veículo junto à revendedora Quintino Automóveis, "
                "entrega de Renault Scenic 2004 e Honda CBX 300 como entrada, "
                "pagamento de 34 parcelas via Pix de R$ 1.180,00, perda da via física do contrato "
                "e retomada/recolhimento do veículo sob alegação de bloqueio sem apresentação de documentos."
            )
        ),
        message=message,
        context={},
        timeline=[],
    )

    output = _joined_response_text(response)

    assert response["assistant_mode"] == "editor_block_pure_text"
    assert response["metadata"]["source"] == "case_operational_assistant_editor_block_pure_text_v1"
    assert response["rewritten_input"]
    assert response["suggested_actions"] == []
    assert response["next_steps"] == []
    assert response["warnings"] == []
    assert response["disclaimer"] == ""

    rewritten = response["rewritten_input"]

    assert "Autor" in rewritten
    assert "Quintino Automóveis" in rewritten
    assert "34 parcelas" in rewritten or "R$ 1.180,00" in rewritten
    assert "Reescreva somente o bloco" not in rewritten
    assert "Entregue apenas o texto final" not in rewritten
    assert "Não traga checklist" not in rewritten
    assert "Comece direto pelo texto do bloco" not in rewritten
    assert "Linha do Tempo" not in output
    assert "Checklist" not in output
    assert "Anexos" not in output
    assert "Testemunhas" not in output
    assert "Próximos passos" not in output
    assert "Alertas" not in output
    assert "Sugestões de aplicação" not in output



def test_editor_all_blocks_ready_request_returns_all_blocks_not_single_enderecamento():
    message = """
Gere todos os blocos principais da minuta preliminar deste caso em formato de texto pronto para copiar e colar no Editor/minuta.

Entregue somente os blocos finais, separados por títulos exatamente assim:

BLOCO 1 — Endereçamento

BLOCO 2 — Qualificação das partes

BLOCO 3 — Resumo Fático

BLOCO 4 — Fundamentação preliminar

BLOCO 5 — Pedidos

BLOCO 6 — Provas e requerimentos

BLOCO 7 — Fechamento e conferência final

Não traga checklist operacional, linha do tempo, anexos, testemunhas, análise, próximos passos, alertas ou explicações fora dos blocos.

Comece direto pelo BLOCO 1.
"""

    response = _fallback_response(
        case=_fake_case(
            description=(
                "Parte autora: Dilson Pereira, CPF a confirmar, residente em Itapoá/SC. "
                "Parte ré: QUINTINO COMÉRCIO DE AUTOMÓVEIS LTDA, nome fantasia Quintino Automóveis. "
                "O autor relata aquisição de veículo junto à revendedora, entrega de bens como entrada, "
                "pagamento de 34 parcelas de R$ 1.180,00 via Pix e posterior recolhimento do veículo sob alegação de bloqueio. "
                "Provas existentes ou indicadas: comprovantes Pix, conversas, consulta de restrição e documentos do veículo. "
                "Pontos a confirmar: datas, contrato, endereço da ré, placa, RENAVAM e eventual ordem judicial. "
                "Testemunhas/depoentes a confirmar: pessoas que presenciaram a negociação ou retirada do bem. "
                "Pedidos a avaliar pelo advogado: exibição de documentos, restituição, indenização e tutela de urgência."
            )
        ),
        message=message,
        context={},
        timeline=[],
    )

    output = _joined_response_text(response)
    rewritten = response["rewritten_input"]

    assert response["assistant_mode"] == "editor_all_blocks_ready"
    assert response["metadata"]["source"] == "case_operational_assistant_editor_all_blocks_ready_v1"
    assert response["suggested_actions"] == []
    assert response["next_steps"] == []
    assert response["warnings"] == []
    assert response["disclaimer"] == ""

    for title in (
        "BLOCO 1 — Endereçamento",
        "BLOCO 2 — Qualificação das partes",
        "BLOCO 3 — Resumo Fático",
        "BLOCO 4 — Fundamentação preliminar",
        "BLOCO 5 — Pedidos",
        "BLOCO 6 — Provas e requerimentos",
        "BLOCO 7 — Fechamento e conferência final",
    ):
        assert title in rewritten

    resumo = rewritten.split("BLOCO 3 — Resumo Fático", 1)[1].split("BLOCO 4 — Fundamentação preliminar", 1)[0]

    assert "Quintino Automóveis" in rewritten
    assert "34 parcelas" in rewritten or "R$ 1.180,00" in rewritten
    assert "34 parcelas" in resumo or "R$ 1.180,00" in resumo
    assert "Parte autora:" not in resumo
    assert "Parte ré:" not in resumo
    assert "Provas existentes" not in resumo
    assert "Pontos a confirmar" not in resumo
    assert "Testemunhas/depoentes" not in resumo
    assert "Pedidos a avaliar" not in resumo
    assert "Tutela de urgência" not in resumo
    assert "Texto pronto para colar no bloco Endereçamento" not in output
    assert "Gere todos os blocos principais" not in rewritten
    assert "Comece direto pelo BLOCO 1" not in rewritten


def test_editor_all_blocks_ready_quality_gate_keeps_exact_sections_and_no_operational_output():
    message = """
Gere todos os blocos principais da minuta preliminar deste caso em formato de texto pronto para copiar e colar no Editor/minuta.

Entregue somente os blocos finais, separados por títulos exatamente assim:

BLOCO 1 — Endereçamento
BLOCO 2 — Qualificação das partes
BLOCO 3 — Resumo Fático
BLOCO 4 — Fundamentação preliminar
BLOCO 5 — Pedidos
BLOCO 6 — Provas e requerimentos
BLOCO 7 — Fechamento e conferência final

Não traga checklist operacional, linha do tempo, anexos, testemunhas, análise, próximos passos, alertas ou explicações fora dos blocos.

Comece direto pelo BLOCO 1.
"""

    response = _fallback_response(
        case=_fake_case(
            case_number="CONTRATO-GENERICO-QUALITY-001",
            description=(
                "Parte autora: cliente a confirmar por documentos pessoais. "
                "Parte ré: fornecedora de serviço a confirmar por contrato e cadastro público. "
                "O autor relata contrato de prestação de serviços, pagamento realizado, "
                "mensagens pendentes de conferência e possível descumprimento contratual. "
                "Provas existentes ou indicadas: contrato, comprovantes de pagamento e mensagens. "
                "Pontos a confirmar: datas, valor da causa, endereço da parte ré e documentos essenciais. "
                "Testemunhas/depoentes a confirmar: pessoas que acompanharam a negociação. "
                "Pedidos a avaliar pelo advogado: exibição de documentos, devolução de valores e indenização se comprovada."
            ),
        ),
        message=message,
        context={},
        timeline=[],
    )

    expected_titles = [
        "BLOCO 1 — Endereçamento",
        "BLOCO 2 — Qualificação das partes",
        "BLOCO 3 — Resumo Fático",
        "BLOCO 4 — Fundamentação preliminar",
        "BLOCO 5 — Pedidos",
        "BLOCO 6 — Provas e requerimentos",
        "BLOCO 7 — Fechamento e conferência final",
    ]

    rewritten = response["rewritten_input"]

    assert response["assistant_mode"] == "editor_all_blocks_ready"
    assert response["metadata"]["source"] == "case_operational_assistant_editor_all_blocks_ready_v1"
    assert response["metadata"]["blocks"] == expected_titles
    assert response["suggested_actions"] == []
    assert response["next_steps"] == []
    assert response["warnings"] == []
    assert response["disclaimer"] == ""

    assert rewritten.startswith("BLOCO 1 — Endereçamento")
    assert rewritten.count("BLOCO ") == 7

    positions = [rewritten.index(title) for title in expected_titles]
    assert positions == sorted(positions)

    for title in expected_titles:
        assert rewritten.count(title) == 1

    forbidden_operational_markers = (
        "Linha do Tempo",
        "Checklist operacional",
        "Anexos/provas",
        "Testemunhas/depoentes",
        "Próximos passos",
        "Alertas",
        "Sugestões de aplicação",
        "Texto sugerido para substituir:",
        "Ação agora:",
    )

    for marker in forbidden_operational_markers:
        assert marker not in rewritten

    resumo = rewritten.split("BLOCO 3 — Resumo Fático", 1)[1].split(
        "BLOCO 4 — Fundamentação preliminar", 1
    )[0]

    assert "contrato de prestação de serviços" in resumo
    assert "pagamento realizado" in resumo
    assert "Provas existentes ou indicadas" not in resumo
    assert "Pontos a confirmar" not in resumo
    assert "Testemunhas/depoentes" not in resumo
    assert "Pedidos a avaliar" not in resumo


def test_frontend_all_blocks_ready_prompt_still_triggers_backend_all_blocks_mode():
    import re
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[2]
    component_path = repo_root / "frontend/src/components/CaseOperationalAssistantPanel.tsx"
    component_text = component_path.read_text()

    match = re.search(
        r"const ALL_BLOCKS_READY_MINUTA_PROMPT = `(?P<prompt>.*?)`\n",
        component_text,
        re.DOTALL,
    )

    assert match is not None

    frontend_prompt = match.group("prompt")

    response = _fallback_response(
        case=_fake_case(
            case_number="CONTRATO-FRONTEND-PROMPT-SYNC-001",
            description=(
                "Parte autora: cliente a confirmar. "
                "Parte ré: empresa fornecedora a confirmar. "
                "O autor relata contrato de prestação de serviços, pagamento realizado "
                "e possível descumprimento contratual pendente de conferência documental."
            ),
        ),
        message=frontend_prompt,
        context={},
        timeline=[],
    )

    expected_titles = [
        "BLOCO 1 — Endereçamento",
        "BLOCO 2 — Qualificação das partes",
        "BLOCO 3 — Resumo Fático",
        "BLOCO 4 — Fundamentação preliminar",
        "BLOCO 5 — Pedidos",
        "BLOCO 6 — Provas e requerimentos",
        "BLOCO 7 — Fechamento e conferência final",
    ]

    rewritten = response["rewritten_input"]

    assert response["assistant_mode"] == "editor_all_blocks_ready"
    assert response["metadata"]["source"] == "case_operational_assistant_editor_all_blocks_ready_v1"
    assert response["metadata"]["blocks"] == expected_titles
    assert response["suggested_actions"] == []
    assert response["next_steps"] == []
    assert response["warnings"] == []
    assert response["disclaimer"] == ""

    assert rewritten.startswith("BLOCO 1 — Endereçamento")
    assert rewritten.count("BLOCO ") == 7

    for title in expected_titles:
        assert title in rewritten


def test_frontend_all_blocks_ready_prompt_keeps_legal_safety_clauses():
    import re
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[2]
    component_path = repo_root / "frontend/src/components/CaseOperationalAssistantPanel.tsx"
    component_text = component_path.read_text()

    match = re.search(
        r"const ALL_BLOCKS_READY_MINUTA_PROMPT = `(?P<prompt>.*?)`\n",
        component_text,
        re.DOTALL,
    )

    assert match is not None

    frontend_prompt = match.group("prompt")
    normalized_prompt = " ".join(frontend_prompt.split()).lower()

    expected_block_titles = (
        "BLOCO 1 — Endereçamento",
        "BLOCO 2 — Qualificação das partes",
        "BLOCO 3 — Resumo Fático",
        "BLOCO 4 — Fundamentação preliminar",
        "BLOCO 5 — Pedidos",
        "BLOCO 6 — Provas e requerimentos",
        "BLOCO 7 — Fechamento e conferência final",
    )

    for title in expected_block_titles:
        assert title in frontend_prompt

    required_safety_clauses = (
        "não traga checklist operacional",
        "linha do tempo",
        "anexos",
        "testemunhas",
        "próximos passos",
        "alertas",
        "não misture pedidos, provas, testemunhas ou pendências dentro do resumo fático",
        "não invente dados",
        "linguagem prudente",
        "a confirmar",
        "sujeito à conferência documental",
        "revisão obrigatória do advogado",
        "competência",
        "rito",
        "valor da causa",
        "tutela de urgência",
        "comece direto pelo bloco 1",
    )

    for clause in required_safety_clauses:
        assert clause in normalized_prompt


def test_editor_all_blocks_ready_output_keeps_legal_caution_clauses():
    message = """
Gere todos os blocos principais da minuta preliminar deste caso em formato de texto pronto para copiar e colar no Editor/minuta.

Entregue somente os blocos finais, separados por títulos exatamente assim:

BLOCO 1 — Endereçamento
BLOCO 2 — Qualificação das partes
BLOCO 3 — Resumo Fático
BLOCO 4 — Fundamentação preliminar
BLOCO 5 — Pedidos
BLOCO 6 — Provas e requerimentos
BLOCO 7 — Fechamento e conferência final

Não invente dados. Use linguagem prudente, como “o Autor relata”, “segundo informado”, “a confirmar”, “até o momento” e “sujeito à conferência documental”.

Comarca, competência, rito, valor da causa, pedidos finais, tutela de urgência e estratégia devem permanecer sujeitos à revisão do advogado.

Comece direto pelo BLOCO 1.
"""

    response = _fallback_response(
        case=_fake_case(
            case_number="CONTRATO-OUTPUT-CAUTION-001",
            description=(
                "Parte autora: cliente a confirmar por documentos pessoais. "
                "Parte ré: empresa fornecedora a confirmar por contrato e cadastro público. "
                "O autor relata contrato de prestação de serviços, pagamento realizado, "
                "mensagens pendentes de conferência e possível descumprimento contratual. "
                "Provas indicadas: contrato, comprovantes de pagamento e mensagens. "
                "Pontos a confirmar: datas, endereço da parte ré, valor da causa e documentos essenciais."
            ),
        ),
        message=message,
        context={},
        timeline=[],
    )

    rewritten = response["rewritten_input"]
    normalized_rewritten = " ".join(rewritten.split()).lower()

    assert response["assistant_mode"] == "editor_all_blocks_ready"
    assert response["suggested_actions"] == []
    assert response["next_steps"] == []
    assert response["warnings"] == []
    assert response["disclaimer"] == ""

    required_output_cautions = (
        "minuta é preliminar",
        "revisada pelo advogado responsável",
        "a confirmar",
        "conferência",
        "análise documental",
        "competência",
        "rito",
        "valor da causa",
        "urgência",
        "sujeitos à revisão profissional",
    )

    for caution in required_output_cautions:
        assert caution in normalized_rewritten

    fechamento = rewritten.split("BLOCO 7 — Fechamento e conferência final", 1)[1]

    assert "A presente minuta é preliminar" in fechamento
    assert "advogado responsável" in fechamento
    assert "competência" in fechamento
    assert "rito" in fechamento
    assert "valor da causa" in fechamento
    assert "documentos essenciais" in fechamento
    assert "a confirmar" in fechamento.lower()


def test_editor_all_blocks_ready_qualification_block_does_not_absorb_case_sections():
    message = """
Gere todos os blocos principais da minuta preliminar deste caso em formato de texto pronto para copiar e colar no Editor/minuta.

Entregue somente os blocos finais, separados por títulos exatamente assim:

BLOCO 1 — Endereçamento
BLOCO 2 — Qualificação das partes
BLOCO 3 — Resumo Fático
BLOCO 4 — Fundamentação preliminar
BLOCO 5 — Pedidos
BLOCO 6 — Provas e requerimentos
BLOCO 7 — Fechamento e conferência final

Não traga checklist operacional, linha do tempo, anexos, testemunhas, análise, próximos passos, alertas ou explicações fora dos blocos.

Não misture pedidos, provas, testemunhas ou pendências dentro do Resumo Fático. Coloque cada conteúdo no bloco próprio.

Não invente dados. Use linguagem prudente.

Comece direto pelo BLOCO 1.
"""

    response = _fallback_response(
        case=_fake_case(
            case_number="QUALIFICACAO-BOUNDARY-001",
            description=(
                "Parte autora: Maria de Souza, CPF a confirmar, residente em Joinville/SC. "
                "Parte ré: Empresa Alfa Serviços LTDA, CNPJ a confirmar, endereço a confirmar. "
                "O autor relata contrato de prestação de serviços, pagamento realizado e possível descumprimento contratual. "
                "Provas existentes ou indicadas: contrato, comprovantes de pagamento e mensagens. "
                "Pontos a confirmar: datas, valor da causa, endereço completo da parte ré e documentos essenciais. "
                "Testemunhas/depoentes a confirmar: pessoas que acompanharam a negociação. "
                "Pedidos a avaliar pelo advogado: exibição de documentos, devolução de valores, indenização e tutela de urgência se comprovada. "
                "Análise estratégica: avaliar risco probatório antes do protocolo."
            ),
        ),
        message=message,
        context={},
        timeline=[],
    )

    rewritten = response["rewritten_input"]

    assert response["assistant_mode"] == "editor_all_blocks_ready"

    qualificacao = rewritten.split("BLOCO 2 — Qualificação das partes", 1)[1].split(
        "BLOCO 3 — Resumo Fático", 1
    )[0]

    assert "Consumidor(a):" in qualificacao
    assert "Maria de Souza" in qualificacao
    assert "Fornecedor(a):" in qualificacao
    assert "Empresa Alfa Serviços LTDA" in qualificacao

    forbidden_qualification_markers = (
        "O autor relata",
        "contrato de prestação de serviços",
        "pagamento realizado",
        "possível descumprimento contratual",
        "Provas existentes",
        "comprovantes de pagamento",
        "Pontos a confirmar",
        "Testemunhas/depoentes",
        "Pedidos a avaliar",
        "devolução de valores",
        "indenização",
        "tutela de urgência",
        "Análise estratégica",
        "risco probatório",
    )

    for marker in forbidden_qualification_markers:
        assert marker not in qualificacao


def test_editor_all_blocks_ready_fundamentacao_block_keeps_preliminary_legal_boundary():
    message = """
Gere todos os blocos principais da minuta preliminar deste caso em formato de texto pronto para copiar e colar no Editor/minuta.

Entregue somente os blocos finais, separados por títulos exatamente assim:

BLOCO 1 — Endereçamento
BLOCO 2 — Qualificação das partes
BLOCO 3 — Resumo Fático
BLOCO 4 — Fundamentação preliminar
BLOCO 5 — Pedidos
BLOCO 6 — Provas e requerimentos
BLOCO 7 — Fechamento e conferência final

Não traga checklist operacional, linha do tempo, anexos, testemunhas, análise, próximos passos, alertas ou explicações fora dos blocos.

Não invente dados. Use linguagem prudente.

Comece direto pelo BLOCO 1.
"""

    response = _fallback_response(
        case=_fake_case(
            case_number="FUNDAMENTACAO-BOUNDARY-001",
            description=(
                "Parte autora: cliente a confirmar por documentos pessoais. "
                "Parte ré: empresa fornecedora a confirmar por contrato e cadastro público. "
                "O autor relata contrato de prestação de serviços, pagamento realizado e possível descumprimento contratual. "
                "Provas existentes ou indicadas: contrato, comprovantes de pagamento e mensagens. "
                "Pontos a confirmar: datas, valor da causa, endereço completo da parte ré e documentos essenciais. "
                "Testemunhas/depoentes a confirmar: pessoas que acompanharam a negociação. "
                "Pedidos a avaliar pelo advogado: exibição de documentos, devolução de valores, indenização e tutela de urgência se comprovada. "
                "Análise estratégica: avaliar risco probatório antes do protocolo."
            ),
        ),
        message=message,
        context={},
        timeline=[],
    )

    rewritten = response["rewritten_input"]

    assert response["assistant_mode"] == "editor_all_blocks_ready"

    fundamentacao = rewritten.split("BLOCO 4 — Fundamentação preliminar", 1)[1].split(
        "BLOCO 5 — Pedidos", 1
    )[0]
    normalized_fundamentacao = " ".join(fundamentacao.split()).lower()

    assert "advogado responsável" in normalized_fundamentacao
    assert "fatos relatados" in normalized_fundamentacao
    assert "documentos disponíveis" in normalized_fundamentacao
    assert "sujeitos à revisão profissional" in normalized_fundamentacao

    forbidden_fundamentacao_markers = (
        "requer-se",
        "pede-se",
        "julgar procedente",
        "condenação",
        "tutela de urgência",
        "protesta-se pela produção",
        "provas existentes",
        "testemunhas/depoentes",
        "pontos a confirmar",
        "checklist",
        "próximos passos",
        "análise estratégica",
        "risco probatório",
        "restou comprovado",
        "ficou demonstrado",
        "é incontroverso",
    )

    for marker in forbidden_fundamentacao_markers:
        assert marker not in normalized_fundamentacao


def test_editor_all_blocks_ready_pedidos_block_keeps_request_boundary():
    message = """
Gere todos os blocos principais da minuta preliminar deste caso em formato de texto pronto para copiar e colar no Editor/minuta.

Entregue somente os blocos finais, separados por títulos exatamente assim:

BLOCO 1 — Endereçamento
BLOCO 2 — Qualificação das partes
BLOCO 3 — Resumo Fático
BLOCO 4 — Fundamentação preliminar
BLOCO 5 — Pedidos
BLOCO 6 — Provas e requerimentos
BLOCO 7 — Fechamento e conferência final

Não traga checklist operacional, linha do tempo, anexos, testemunhas, análise, próximos passos, alertas ou explicações fora dos blocos.

Não invente dados. Use linguagem prudente.

Comece direto pelo BLOCO 1.
"""

    response = _fallback_response(
        case=_fake_case(
            case_number="PEDIDOS-BOUNDARY-001",
            description=(
                "Parte autora: cliente a confirmar por documentos pessoais. "
                "Parte ré: empresa fornecedora a confirmar por contrato e cadastro público. "
                "O autor relata contrato de prestação de serviços, pagamento realizado e possível descumprimento contratual. "
                "Fundamentação preliminar: avaliar deveres de informação, boa-fé, transparência e responsabilidade civil. "
                "Provas existentes ou indicadas: contrato, comprovantes de pagamento, mensagens e prints. "
                "Pontos a confirmar: datas, valor da causa, endereço completo da parte ré e documentos essenciais. "
                "Testemunhas/depoentes a confirmar: pessoas que acompanharam a negociação. "
                "Pedidos a avaliar pelo advogado: exibição de documentos, devolução de valores, indenização e tutela de urgência se comprovada. "
                "Análise estratégica: avaliar risco probatório antes do protocolo."
            ),
        ),
        message=message,
        context={},
        timeline=[],
    )

    rewritten = response["rewritten_input"]

    assert response["assistant_mode"] == "editor_all_blocks_ready"

    pedidos = rewritten.split("BLOCO 5 — Pedidos", 1)[1].split(
        "BLOCO 6 — Provas e requerimentos", 1
    )[0]
    normalized_pedidos = " ".join(pedidos.split()).lower()

    assert "requer-se" in normalized_pedidos
    assert "pedidos finais" in normalized_pedidos
    assert "advogado" in normalized_pedidos
    assert "documentos essenciais" in normalized_pedidos

    forbidden_pedidos_markers = (
        "fundamentação preliminar",
        "deveres de informação",
        "boa-fé",
        "transparência",
        "responsabilidade civil",
        "provas existentes",
        "mensagens e prints",
        "pontos a confirmar",
        "testemunhas/depoentes",
        "análise estratégica",
        "risco probatório",
        "checklist",
        "próximos passos",
        "restou comprovado",
        "ficou demonstrado",
        "é incontroverso",
    )

    for marker in forbidden_pedidos_markers:
        assert marker not in normalized_pedidos


def test_editor_all_blocks_ready_provas_requerimentos_block_keeps_evidence_boundary():
    message = """
Gere todos os blocos principais da minuta preliminar deste caso em formato de texto pronto para copiar e colar no Editor/minuta.

Entregue somente os blocos finais, separados por títulos exatamente assim:

BLOCO 1 — Endereçamento
BLOCO 2 — Qualificação das partes
BLOCO 3 — Resumo Fático
BLOCO 4 — Fundamentação preliminar
BLOCO 5 — Pedidos
BLOCO 6 — Provas e requerimentos
BLOCO 7 — Fechamento e conferência final

Não traga checklist operacional, linha do tempo, anexos, testemunhas, análise, próximos passos, alertas ou explicações fora dos blocos.

Não invente dados. Use linguagem prudente.

Comece direto pelo BLOCO 1.
"""

    response = _fallback_response(
        case=_fake_case(
            case_number="PROVAS-BOUNDARY-001",
            description=(
                "Parte autora: cliente a confirmar por documentos pessoais. "
                "Parte ré: empresa fornecedora a confirmar por contrato e cadastro público. "
                "Resumo fático: o autor relata contrato de prestação de serviços, pagamento realizado e possível descumprimento contratual. "
                "Fundamentação preliminar: avaliar deveres de informação, boa-fé, transparência e responsabilidade civil. "
                "Pedidos a avaliar pelo advogado: exibição de documentos, devolução de valores, indenização e tutela de urgência se comprovada. "
                "Provas existentes ou indicadas: contrato, comprovantes de pagamento, mensagens, prints, áudios e protocolos. "
                "Pontos a confirmar: datas, valor da causa, endereço completo da parte ré e documentos essenciais. "
                "Testemunhas/depoentes a confirmar: pessoas que acompanharam a negociação. "
                "Análise estratégica: avaliar risco probatório antes do protocolo."
            ),
        ),
        message=message,
        context={},
        timeline=[],
    )

    rewritten = response["rewritten_input"]

    assert response["assistant_mode"] == "editor_all_blocks_ready"

    provas = rewritten.split("BLOCO 6 — Provas e requerimentos", 1)[1].split(
        "BLOCO 7 — Fechamento e conferência final", 1
    )[0]
    normalized_provas = " ".join(provas.split()).lower()

    assert "protesta-se" in normalized_provas
    assert "meios de prova" in normalized_provas
    assert "documentos" in normalized_provas
    assert "testemunhas" in normalized_provas
    assert "advogado" in normalized_provas
    assert "juntada" in normalized_provas

    forbidden_provas_markers = (
        "resumo fático",
        "parte autora:",
        "parte ré:",
        "fundamentação preliminar",
        "deveres de informação",
        "boa-fé",
        "transparência",
        "responsabilidade civil",
        "procedência dos pedidos",
        "devolução de valores",
        "indenização",
        "tutela de urgência",
        "valor da causa",
        "análise estratégica",
        "risco probatório",
        "checklist",
        "próximos passos",
        "restou comprovado",
        "ficou demonstrado",
        "é incontroverso",
    )

    for marker in forbidden_provas_markers:
        assert marker not in normalized_provas


def test_editor_all_blocks_ready_fechamento_block_keeps_final_caution_boundary():
    message = """
Gere todos os blocos principais da minuta preliminar deste caso em formato de texto pronto para copiar e colar no Editor/minuta.

Entregue somente os blocos finais, separados por títulos exatamente assim:

BLOCO 1 — Endereçamento
BLOCO 2 — Qualificação das partes
BLOCO 3 — Resumo Fático
BLOCO 4 — Fundamentação preliminar
BLOCO 5 — Pedidos
BLOCO 6 — Provas e requerimentos
BLOCO 7 — Fechamento e conferência final

Não traga checklist operacional, linha do tempo, anexos, testemunhas, análise, próximos passos, alertas ou explicações fora dos blocos.

Não invente dados. Use linguagem prudente.

Comece direto pelo BLOCO 1.
"""

    response = _fallback_response(
        case=_fake_case(
            case_number="FECHAMENTO-BOUNDARY-001",
            description=(
                "Parte autora: cliente a confirmar por documentos pessoais. "
                "Parte ré: empresa fornecedora a confirmar por contrato e cadastro público. "
                "Resumo fático: o autor relata contrato de prestação de serviços, pagamento realizado e possível descumprimento contratual. "
                "Fundamentação preliminar: avaliar deveres de informação, boa-fé, transparência e responsabilidade civil. "
                "Pedidos a avaliar pelo advogado: exibição de documentos, devolução de valores, indenização e tutela de urgência se comprovada. "
                "Provas existentes ou indicadas: contrato, comprovantes de pagamento, mensagens, prints, áudios e protocolos. "
                "Pontos a confirmar: datas, valor da causa, endereço completo da parte ré e documentos essenciais. "
                "Testemunhas/depoentes a confirmar: pessoas que acompanharam a negociação. "
                "Análise estratégica: avaliar risco probatório antes do protocolo."
            ),
        ),
        message=message,
        context={},
        timeline=[],
    )

    rewritten = response["rewritten_input"]

    assert response["assistant_mode"] == "editor_all_blocks_ready"

    fechamento = rewritten.split("BLOCO 7 — Fechamento e conferência final", 1)[1]
    normalized_fechamento = " ".join(fechamento.split()).lower()

    assert "minuta é preliminar" in normalized_fechamento
    assert "advogado responsável" in normalized_fechamento
    assert "competência" in normalized_fechamento
    assert "rito" in normalized_fechamento
    assert "valor da causa" in normalized_fechamento
    assert "documentos essenciais" in normalized_fechamento
    assert "a confirmar" in normalized_fechamento

    forbidden_fechamento_markers = (
        "parte autora:",
        "parte ré:",
        "o autor relata contrato",
        "prestação de serviços",
        "pagamento realizado",
        "descumprimento contratual",
        "fundamentação preliminar",
        "deveres de informação",
        "boa-fé",
        "transparência",
        "responsabilidade civil",
        "requer-se",
        "procedência dos pedidos",
        "devolução de valores",
        "indenização",
        "protesta-se",
        "meios de prova",
        "comprovantes de pagamento",
        "mensagens, prints",
        "testemunhas/depoentes",
        "risco probatório",
        "checklist",
        "próximos passos",
        "restou comprovado",
        "ficou demonstrado",
        "é incontroverso",
    )

    for marker in forbidden_fechamento_markers:
        assert marker not in normalized_fechamento


def test_editor_all_blocks_ready_structural_regression_suite_keeps_seven_clean_blocks():
    message = """
Gere todos os blocos principais da minuta preliminar deste caso em formato de texto pronto para copiar e colar no Editor/minuta.

Entregue somente os blocos finais, separados por títulos exatamente assim:

BLOCO 1 — Endereçamento
BLOCO 2 — Qualificação das partes
BLOCO 3 — Resumo Fático
BLOCO 4 — Fundamentação preliminar
BLOCO 5 — Pedidos
BLOCO 6 — Provas e requerimentos
BLOCO 7 — Fechamento e conferência final

Não traga checklist operacional, linha do tempo, anexos, testemunhas, análise, próximos passos, alertas ou explicações fora dos blocos.

Não invente dados. Use linguagem prudente.

Comece direto pelo BLOCO 1.
"""

    response = _fallback_response(
        case=_fake_case(
            case_number="STRUCTURAL-REGRESSION-001",
            description=(
                "Parte autora: cliente a confirmar por documentos pessoais. "
                "Parte ré: empresa fornecedora a confirmar por contrato e cadastro público. "
                "Resumo fático: o autor relata contrato de prestação de serviços, pagamento realizado e possível descumprimento contratual. "
                "Fundamentação preliminar: avaliar deveres de informação, boa-fé, transparência e responsabilidade civil. "
                "Pedidos a avaliar pelo advogado: exibição de documentos, devolução de valores, indenização e tutela de urgência se comprovada. "
                "Provas existentes ou indicadas: contrato, comprovantes de pagamento, mensagens, prints, áudios e protocolos. "
                "Pontos a confirmar: datas, valor da causa, endereço completo da parte ré e documentos essenciais. "
                "Testemunhas/depoentes a confirmar: pessoas que acompanharam a negociação. "
                "Análise estratégica: avaliar risco probatório antes do protocolo."
            ),
        ),
        message=message,
        context={},
        timeline=[],
    )

    rewritten = response["rewritten_input"]

    assert response["assistant_mode"] == "editor_all_blocks_ready"
    assert response["metadata"]["source"] == "case_operational_assistant_editor_all_blocks_ready_v1"

    expected_titles = [
        "BLOCO 1 — Endereçamento",
        "BLOCO 2 — Qualificação das partes",
        "BLOCO 3 — Resumo Fático",
        "BLOCO 4 — Fundamentação preliminar",
        "BLOCO 5 — Pedidos",
        "BLOCO 6 — Provas e requerimentos",
        "BLOCO 7 — Fechamento e conferência final",
    ]

    assert rewritten.startswith(expected_titles[0])

    positions = [rewritten.index(title) for title in expected_titles]
    assert positions == sorted(positions)

    for title in expected_titles:
        assert rewritten.count(title) == 1

    for current_title, next_title in zip(expected_titles, expected_titles[1:]):
        section = rewritten.split(current_title, 1)[1].split(next_title, 1)[0]
        assert len(section.strip()) > 40
        for other_title in expected_titles:
            assert other_title not in section

    final_section = rewritten.split(expected_titles[-1], 1)[1]
    assert len(final_section.strip()) > 40

    forbidden_global_markers = (
        "suggested_actions",
        "next_steps",
        "warnings",
        "disclaimer",
        "Texto sugerido para substituir",
        "Ação agora",
        "Checklist operacional",
        "Linha do Tempo",
        "Anexos/provas",
        "Próximos passos",
        "Alertas",
        "Comece direto pelo BLOCO 1",
    )

    for marker in forbidden_global_markers:
        assert marker not in rewritten


def test_editor_all_blocks_ready_golden_fixture_keeps_representative_block_signatures():
    message = """
Gere todos os blocos principais da minuta preliminar deste caso em formato de texto pronto para copiar e colar no Editor/minuta.

Entregue somente os blocos finais, separados por títulos exatamente assim:

BLOCO 1 — Endereçamento
BLOCO 2 — Qualificação das partes
BLOCO 3 — Resumo Fático
BLOCO 4 — Fundamentação preliminar
BLOCO 5 — Pedidos
BLOCO 6 — Provas e requerimentos
BLOCO 7 — Fechamento e conferência final

Não traga checklist operacional, linha do tempo, anexos, testemunhas, análise, próximos passos, alertas ou explicações fora dos blocos.

Não invente dados. Use linguagem prudente.

Comece direto pelo BLOCO 1.
"""

    response = _fallback_response(
        case=_fake_case(
            case_number="GOLDEN-ALL-BLOCKS-001",
            description=(
                "Parte autora: consumidor a confirmar por documentos pessoais. "
                "Parte ré: empresa fornecedora a confirmar por contrato e cadastro público. "
                "O autor relata contratação de serviço, pagamento realizado, falha na prestação e ausência de solução administrativa. "
                "Fundamentação preliminar: avaliar relação de consumo, dever de informação, boa-fé, responsabilidade civil e falha na prestação do serviço. "
                "Pedidos a avaliar pelo advogado: obrigação de fazer, restituição de valores, indenização e tutela de urgência se houver prova suficiente. "
                "Provas existentes ou indicadas: contrato, comprovantes de pagamento, mensagens, prints, protocolos de atendimento e notificações. "
                "Pontos a confirmar: datas, valor da causa, endereço completo da parte ré, documentos essenciais e estratégia processual. "
                "Testemunhas/depoentes a confirmar: pessoas que acompanharam a contratação e as tentativas de solução."
            ),
        ),
        message=message,
        context={},
        timeline=[],
    )

    rewritten = response["rewritten_input"]

    assert response["assistant_mode"] == "editor_all_blocks_ready"
    assert response["metadata"]["source"] == "case_operational_assistant_editor_all_blocks_ready_v1"

    expected_titles = [
        "BLOCO 1 — Endereçamento",
        "BLOCO 2 — Qualificação das partes",
        "BLOCO 3 — Resumo Fático",
        "BLOCO 4 — Fundamentação preliminar",
        "BLOCO 5 — Pedidos",
        "BLOCO 6 — Provas e requerimentos",
        "BLOCO 7 — Fechamento e conferência final",
    ]

    sections = {}
    for current_title, next_title in zip(expected_titles, expected_titles[1:]):
        sections[current_title] = rewritten.split(current_title, 1)[1].split(next_title, 1)[0]

    sections[expected_titles[-1]] = rewritten.split(expected_titles[-1], 1)[1]

    golden_signatures = {
        "BLOCO 1 — Endereçamento": (
            "juízo",
            "competente",
        ),
        "BLOCO 2 — Qualificação das partes": (
            "consumidor(a)",
            "fornecedor(a)",
            "a confirmar",
        ),
        "BLOCO 3 — Resumo Fático": (
            "relata",
            "pagamento",
            "serviço",
        ),
        "BLOCO 4 — Fundamentação preliminar": (
            "fundamentação",
            "preliminar",
            "documentos",
            "advogado",
        ),
        "BLOCO 5 — Pedidos": (
            "requer-se",
            "pedidos finais",
            "advogado",
            "documentos essenciais",
        ),
        "BLOCO 6 — Provas e requerimentos": (
            "protesta-se",
            "meios de prova",
            "documentos",
            "juntada",
        ),
        "BLOCO 7 — Fechamento e conferência final": (
            "minuta é preliminar",
            "advogado responsável",
            "competência",
            "valor da causa",
            "a confirmar",
        ),
    }

    for title, expected_fragments in golden_signatures.items():
        normalized_section = " ".join(sections[title].split()).lower()
        for fragment in expected_fragments:
            assert fragment in normalized_section

    assert "suggested_actions" not in rewritten
    assert "next_steps" not in rewritten
    assert "warnings" not in rewritten
    assert "disclaimer" not in rewritten


def test_editor_all_blocks_ready_frontend_prompt_stays_synced_with_golden_contract():
    import re
    from pathlib import Path

    frontend_source = Path("frontend/src/components/CaseOperationalAssistantPanel.tsx").read_text()

    match = re.search(
        r"const ALL_BLOCKS_READY_MINUTA_PROMPT\s*=\s*`(?P<prompt>.*?)`\n",
        frontend_source,
        flags=re.S,
    )
    assert match is not None

    prompt = match.group("prompt")

    expected_titles = [
        "BLOCO 1 — Endereçamento",
        "BLOCO 2 — Qualificação das partes",
        "BLOCO 3 — Resumo Fático",
        "BLOCO 4 — Fundamentação preliminar",
        "BLOCO 5 — Pedidos",
        "BLOCO 6 — Provas e requerimentos",
        "BLOCO 7 — Fechamento e conferência final",
    ]

    assert "Gere todos os blocos principais da minuta preliminar" in prompt
    assert "Entregue somente os blocos finais" in prompt
    assert "Não invente dados" in prompt
    assert "Use linguagem prudente" in prompt
    assert "Comece direto pelo BLOCO 1" in prompt

    for title in expected_titles:
        assert prompt.count(title) == 1

    response = _fallback_response(
        case=_fake_case(
            case_number="FRONTEND-PROMPT-GOLDEN-SYNC-001",
            description=(
                "Parte autora: consumidor a confirmar por documentos pessoais. "
                "Parte ré: empresa fornecedora a confirmar por contrato e cadastro público. "
                "O autor relata contratação de serviço, pagamento realizado, falha na prestação e ausência de solução administrativa. "
                "Fundamentação preliminar: avaliar relação de consumo, dever de informação, boa-fé, responsabilidade civil e falha na prestação do serviço. "
                "Pedidos a avaliar pelo advogado: obrigação de fazer, restituição de valores, indenização e tutela de urgência se houver prova suficiente. "
                "Provas existentes ou indicadas: contrato, comprovantes de pagamento, mensagens, prints, protocolos de atendimento e notificações. "
                "Pontos a confirmar: datas, valor da causa, endereço completo da parte ré, documentos essenciais e estratégia processual. "
                "Testemunhas/depoentes a confirmar: pessoas que acompanharam a contratação e as tentativas de solução."
            ),
        ),
        message=prompt,
        context={},
        timeline=[],
    )

    rewritten = response["rewritten_input"]

    assert response["assistant_mode"] == "editor_all_blocks_ready"
    assert response["metadata"]["source"] == "case_operational_assistant_editor_all_blocks_ready_v1"
    assert response["metadata"]["blocks"] == expected_titles

    assert rewritten.startswith(expected_titles[0])

    for title in expected_titles:
        assert rewritten.count(title) == 1

    sections = {}
    for current_title, next_title in zip(expected_titles, expected_titles[1:]):
        sections[current_title] = rewritten.split(current_title, 1)[1].split(next_title, 1)[0]

    sections[expected_titles[-1]] = rewritten.split(expected_titles[-1], 1)[1]

    golden_signatures = {
        "BLOCO 1 — Endereçamento": (
            "juízo",
            "competente",
        ),
        "BLOCO 2 — Qualificação das partes": (
            "consumidor(a)",
            "fornecedor(a)",
            "a confirmar",
        ),
        "BLOCO 3 — Resumo Fático": (
            "relata",
            "pagamento",
            "serviço",
        ),
        "BLOCO 4 — Fundamentação preliminar": (
            "fundamentação",
            "preliminar",
            "documentos",
            "advogado",
        ),
        "BLOCO 5 — Pedidos": (
            "requer-se",
            "pedidos finais",
            "advogado",
            "documentos essenciais",
        ),
        "BLOCO 6 — Provas e requerimentos": (
            "protesta-se",
            "meios de prova",
            "documentos",
            "juntada",
        ),
        "BLOCO 7 — Fechamento e conferência final": (
            "minuta é preliminar",
            "advogado responsável",
            "competência",
            "valor da causa",
            "a confirmar",
        ),
    }

    for title, expected_fragments in golden_signatures.items():
        normalized_section = " ".join(sections[title].split()).lower()
        for fragment in expected_fragments:
            assert fragment in normalized_section

    forbidden_operational_markers = (
        "suggested_actions",
        "next_steps",
        "warnings",
        "disclaimer",
        "Texto sugerido para substituir",
        "Ação agora",
        "Checklist operacional",
        "Linha do Tempo",
        "Anexos/provas",
        "Próximos passos",
        "Alertas",
    )

    for marker in forbidden_operational_markers:
        assert marker not in rewritten


def test_editor_all_blocks_ready_cobranca_contratual_without_moral_damage_keeps_specific_requests():
    message = """
Gere todos os blocos principais da minuta preliminar deste caso em formato de texto pronto para copiar e colar no Editor/minuta.

Entregue somente os blocos finais, separados por títulos exatamente assim:

BLOCO 1 — Endereçamento
BLOCO 2 — Qualificação das partes
BLOCO 3 — Resumo Fático
BLOCO 4 — Fundamentação preliminar
BLOCO 5 — Pedidos
BLOCO 6 — Provas e requerimentos
BLOCO 7 — Fechamento e conferência final

Não traga checklist operacional, linha do tempo, anexos, testemunhas, análise, próximos passos, alertas ou explicações fora dos blocos.

Não invente dados. Use linguagem prudente.

Comece direto pelo BLOCO 1.
"""

    response = _fallback_response(
        case=_fake_case(
            case_number="COBRANCA-CONTRATUAL-001",
            title="Cobrança contratual de saldo de manutenção elétrica",
            legal_area="cível",
            action_type="ação de cobrança contratual",
            description=(
                "A empresa DLP Manutenção e Serviços Ltda. foi contratada pela empresa Restaurante Mar Azul Ltda. "
                "para realizar serviços de manutenção elétrica. "
                "O valor total contratado foi de R$ 18.500,00. "
                "Houve pagamento parcial de R$ 6.500,00. "
                "Permaneceu saldo contratual inadimplido de R$ 12.000,00. "
                "Os serviços foram executados conforme combinado. "
                "Pedido pretendido: propor ação de cobrança contratual, sem pedido de dano moral. "
                "Observação estratégica: a prova documental é considerada forte. "
                "Provas existentes ou indicadas: contrato, proposta, comprovantes de pagamento, notas, mensagens e planilha de cálculo."
            ),
        ),
        message=message,
        context={},
        timeline=[],
    )

    rewritten = response["rewritten_input"]

    assert response["assistant_mode"] == "editor_all_blocks_ready"

    for title in (
        "BLOCO 1 — Endereçamento",
        "BLOCO 2 — Qualificação das partes",
        "BLOCO 3 — Resumo Fático",
        "BLOCO 4 — Fundamentação preliminar",
        "BLOCO 5 — Pedidos",
        "BLOCO 6 — Provas e requerimentos",
        "BLOCO 7 — Fechamento e conferência final",
    ):
        assert title in rewritten

    qualificacao = rewritten.split("BLOCO 2 — Qualificação das partes", 1)[1].split(
        "BLOCO 3 — Resumo Fático", 1
    )[0]
    resumo = rewritten.split("BLOCO 3 — Resumo Fático", 1)[1].split(
        "BLOCO 4 — Fundamentação preliminar", 1
    )[0]
    fundamentacao = rewritten.split("BLOCO 4 — Fundamentação preliminar", 1)[1].split(
        "BLOCO 5 — Pedidos", 1
    )[0]
    pedidos = rewritten.split("BLOCO 5 — Pedidos", 1)[1].split(
        "BLOCO 6 — Provas e requerimentos", 1
    )[0]

    normalized_fundamentacao = " ".join(fundamentacao.split()).lower()
    normalized_pedidos = " ".join(pedidos.split()).lower()

    assert "DLP Manutenção e Serviços" in qualificacao
    assert "Restaurante Mar Azul" in qualificacao

    assert "Pedido pretendido" not in resumo
    assert "Observação estratégica" not in resumo
    assert "Observacao estrategica" not in resumo

    assert "cobrança contratual" in normalized_fundamentacao
    assert "inadimplemento" in normalized_fundamentacao
    assert "saldo contratual" in normalized_fundamentacao

    assert "saldo contratual inadimplido" in normalized_pedidos
    assert "correção monetária" in normalized_pedidos
    assert "juros" in normalized_pedidos

    forbidden_positive_request_markers = (
        "eventual indenização por danos materiais e/ou morais",
        "obrigação de fazer ou não fazer",
        "tutela de urgência, valor da causa",
    )
    for marker in forbidden_positive_request_markers:
        assert marker not in normalized_pedidos


def test_editor_all_blocks_ready_universal_action_specialization_router_keeps_consumer_vehicle_requests_specific():
    message = """
Gere todos os blocos principais da minuta preliminar deste caso em formato de texto pronto para copiar e colar no Editor/minuta.

Entregue somente os blocos finais, separados por títulos exatamente assim:

BLOCO 1 — Endereçamento
BLOCO 2 — Qualificação das partes
BLOCO 3 — Resumo Fático
BLOCO 4 — Fundamentação preliminar
BLOCO 5 — Pedidos
BLOCO 6 — Provas e requerimentos
BLOCO 7 — Fechamento e conferência final

Não traga checklist operacional, linha do tempo, anexos, testemunhas, análise, próximos passos, alertas ou explicações fora dos blocos.

Não invente dados. Use linguagem prudente.

Comece direto pelo BLOCO 1.
"""

    response = _fallback_response(
        case=_fake_case(
            case_number="VEICULO-QUINTINO-PIX-001",
            title="Retomada de veículo por revendedora após pagamento parcelado via Pix",
            legal_area="consumidor",
            action_type="exibição de contrato, restituição de veículo ou indenização",
            description=(
                "Parte autora: Dilson Pereira, CPF a confirmar, residente em Itapoá/SC. "
                "Parte ré: QUINTINO COMÉRCIO DE AUTOMÓVEIS LTDA, nome fantasia Quintino Automóveis. "
                "O autor relata aquisição de veículo junto à revendedora, entrega de bens como entrada, "
                "pagamento de 34 parcelas de R$ 1.180,00 via Pix e posterior recolhimento do veículo sob alegação de bloqueio. "
                "A parte ré não apresentou, até o momento, ordem judicial, cópia do contrato ou justificativa completa para a retirada do veículo. "
                "Provas existentes ou indicadas: comprovantes Pix, conversas, consulta de restrição e documentos do veículo. "
                "Pedido pretendido: exibição do contrato e documentos, restituição do veículo ou indenização material conforme revisão do advogado."
            ),
        ),
        message=message,
        context={},
        timeline=[],
    )

    rewritten = response["rewritten_input"]

    assert response["assistant_mode"] == "editor_all_blocks_ready"
    assert response["metadata"]["action_specialization_kind"] == "consumer_vehicle_contract_display_restitution"

    fundamentacao = rewritten.split("BLOCO 4 — Fundamentação preliminar", 1)[1].split(
        "BLOCO 5 — Pedidos", 1
    )[0]
    pedidos = rewritten.split("BLOCO 5 — Pedidos", 1)[1].split(
        "BLOCO 6 — Provas e requerimentos", 1
    )[0]

    normalized_fundamentacao = " ".join(fundamentacao.split()).lower()
    normalized_pedidos = " ".join(pedidos.split()).lower()

    assert "aquisição de veículo" in normalized_fundamentacao
    assert "exibição de documentos" in normalized_fundamentacao
    assert "restituição do veículo" in normalized_fundamentacao

    assert "exibição do contrato" in normalized_pedidos
    assert "restituição do veículo" in normalized_pedidos
    assert "indenização material equivalente" in normalized_pedidos
    assert "comprovantes pix" in normalized_pedidos
    assert "tutela de urgência, busca do bem" not in normalized_pedidos

    forbidden_wrong_family_markers = (
        "saldo contratual inadimplido",
        "multa contratual se prevista",
        "eventual indenização por danos materiais e/ou morais",
        "prestação de contas ou esclarecimentos formais sobre os fatos controvertidos",
    )
    for marker in forbidden_wrong_family_markers:
        assert marker not in normalized_pedidos


def test_editor_all_blocks_ready_labor_hours_interval_router_keeps_labor_requests_specific():
    message = """
Gere todos os blocos principais da minuta preliminar deste caso em formato de texto pronto para copiar e colar no Editor/minuta.

Entregue somente os blocos finais, separados por títulos exatamente assim:

BLOCO 1 — Endereçamento
BLOCO 2 — Qualificação das partes
BLOCO 3 — Resumo Fático
BLOCO 4 — Fundamentação preliminar
BLOCO 5 — Pedidos
BLOCO 6 — Provas e requerimentos
BLOCO 7 — Fechamento e conferência final

Não traga checklist operacional, linha do tempo, anexos, testemunhas, análise, próximos passos, alertas ou explicações fora dos blocos.

Não invente dados. Use linguagem prudente.

Comece direto pelo BLOCO 1.
"""

    response = _fallback_response(
        case=_fake_case(
            case_number="TRAB-HORAS-INTERVALO-001",
            title="Reclamação trabalhista por horas extras e intervalo intrajornada",
            legal_area="Trabalhista",
            action_type="reclamação trabalhista",
            description=(
                "Área jurídica: Trabalhista. "
                "Reclamante ajuíza reclamação trabalhista contra reclamada alegando jornada superior à registrada, "
                "supressão parcial de intervalo intrajornada, diferenças de horas extras, reflexos em DSR, férias, "
                "13º salário, FGTS e verbas rescisórias. "
                "O caso envolve controles de ponto, holerites, TRCT, extrato analítico do FGTS, mensagens com gestor, "
                "preposto da empresa e testemunhas a confirmar."
            ),
        ),
        message=message,
        context={},
        timeline=[],
    )

    rewritten = response["rewritten_input"]

    assert response["assistant_mode"] == "editor_all_blocks_ready"
    assert response["metadata"]["action_specialization_kind"] == "labor_hours_interval_claim"

    fundamentacao = rewritten.split("BLOCO 4 — Fundamentação preliminar", 1)[1].split(
        "BLOCO 5 — Pedidos", 1
    )[0]
    pedidos = rewritten.split("BLOCO 5 — Pedidos", 1)[1].split(
        "BLOCO 6 — Provas e requerimentos", 1
    )[0]

    normalized_fundamentacao = " ".join(fundamentacao.split()).lower()
    normalized_pedidos = " ".join(pedidos.split()).lower()

    assert "reclamação trabalhista" in normalized_fundamentacao
    assert "jornada de trabalho" in normalized_fundamentacao
    assert "intervalo intrajornada" in normalized_fundamentacao
    assert "controles de ponto" in normalized_fundamentacao
    assert "fgts" in normalized_fundamentacao

    assert "notificação da reclamada" in normalized_pedidos
    assert "horas extras" in normalized_pedidos
    assert "intervalo intrajornada" in normalized_pedidos
    assert "dsr" in normalized_pedidos
    assert "férias" in normalized_pedidos
    assert "13º salário" in normalized_pedidos
    assert "fgts" in normalized_pedidos
    assert "verbas rescisórias" in normalized_pedidos

    forbidden_civil_generic_markers = (
        "restituição, obrigação de fazer ou não fazer",
        "eventual indenização por danos materiais e/ou morais",
        "prestação de contas ou esclarecimentos formais sobre os fatos controvertidos",
        "saldo contratual inadimplido",
        "exibição do contrato, recibos, documentos do veículo",
    )
    for marker in forbidden_civil_generic_markers:
        assert marker not in normalized_pedidos


def test_editor_all_blocks_ready_labor_health_risk_router_keeps_insalubridade_requests_specific():
    message = """
Gere todos os blocos principais da minuta preliminar deste caso em formato de texto pronto para copiar e colar no Editor/minuta.

Entregue somente os blocos finais, separados por títulos exatamente assim:

BLOCO 1 — Endereçamento
BLOCO 2 — Qualificação das partes
BLOCO 3 — Resumo Fático
BLOCO 4 — Fundamentação preliminar
BLOCO 5 — Pedidos
BLOCO 6 — Provas e requerimentos
BLOCO 7 — Fechamento e conferência final

Não traga checklist operacional, linha do tempo, anexos, testemunhas, análise, próximos passos, alertas ou explicações fora dos blocos.

Não invente dados. Use linguagem prudente.

Comece direto pelo BLOCO 1.
"""

    response = _fallback_response(
        case=_fake_case(
            case_number="TRAB-INSALUBRIDADE-CALOR-001",
            title="Adicional de insalubridade por calor em setor de fusão",
            legal_area="Trabalhista",
            action_type="reclamação trabalhista",
            description=(
                "Resumo técnico: Reclamante trabalhou em setor de fusão da Tupy S.A. em Joinville/SC, "
                "de fevereiro de 2024 a julho de 2024, com salário de R$ 2.200,00. "
                "Alega direito a adicional de insalubridade por exposição a calor intenso, com metal em fusão, "
                "e, subsidiariamente, periculosidade. "
                "A pretensão depende de prova técnica, perícia e medições, além de PPP, LTCAT, PGR, PCMSO, "
                "fichas de EPI, registros de fornecimento e uso de EPI, folhas de pagamento e prova testemunhal. "
                "Há necessidade de cálculos para reflexos em férias, 13º salário e FGTS. "
                "Risco prescricional bienal deve ser verificado pela data exata da rescisão em julho de 2024."
            ),
        ),
        message=message,
        context={},
        timeline=[],
    )

    rewritten = response["rewritten_input"]

    assert response["assistant_mode"] == "editor_all_blocks_ready"
    assert response["metadata"]["action_specialization_kind"] == "labor_health_risk_premium_claim"

    fundamentacao = rewritten.split("BLOCO 4 — Fundamentação preliminar", 1)[1].split(
        "BLOCO 5 — Pedidos", 1
    )[0]
    pedidos = rewritten.split("BLOCO 5 — Pedidos", 1)[1].split(
        "BLOCO 6 — Provas e requerimentos", 1
    )[0]

    normalized_fundamentacao = " ".join(fundamentacao.split()).lower()
    normalized_pedidos = " ".join(pedidos.split()).lower()

    assert "adicional de insalubridade" in normalized_fundamentacao
    assert "exposição a calor" in normalized_fundamentacao
    assert "metal em fusão" in normalized_fundamentacao
    assert "periculosidade" in normalized_fundamentacao
    assert "prova técnica" in normalized_fundamentacao
    assert "ppp" in normalized_fundamentacao
    assert "ltcat" in normalized_fundamentacao
    assert "pgr" in normalized_fundamentacao
    assert "pcmso" in normalized_fundamentacao
    assert "epi" in normalized_fundamentacao

    assert "adicional de insalubridade" in normalized_pedidos
    assert "periculosidade" in normalized_pedidos
    assert "prova pericial" in normalized_pedidos
    assert "ppp" in normalized_pedidos
    assert "ltcat" in normalized_pedidos
    assert "pgr" in normalized_pedidos
    assert "pcmso" in normalized_pedidos
    assert "ficha de epi" in normalized_pedidos
    assert "férias" in normalized_pedidos
    assert "13º salário" in normalized_pedidos
    assert "fgts" in normalized_pedidos

    forbidden_wrong_labor_family_markers = (
        "horas extras",
        "intervalo intrajornada",
        "diferenças de jornada",
        "controles de ponto",
        "dsr",
        "saldo contratual inadimplido",
        "exibição do contrato, recibos, documentos do veículo",
        "eventual indenização por danos materiais e/ou morais",
    )
    for marker in forbidden_wrong_labor_family_markers:
        assert marker not in normalized_pedidos


def test_editor_all_blocks_ready_labor_health_risk_evidence_block_keeps_technical_proof_specific():
    message = """
Gere todos os blocos principais da minuta preliminar deste caso em formato de texto pronto para copiar e colar no Editor/minuta.

Entregue somente os blocos finais, separados por títulos exatamente assim:

BLOCO 1 — Endereçamento
BLOCO 2 — Qualificação das partes
BLOCO 3 — Resumo Fático
BLOCO 4 — Fundamentação preliminar
BLOCO 5 — Pedidos
BLOCO 6 — Provas e requerimentos
BLOCO 7 — Fechamento e conferência final

Não traga checklist operacional, linha do tempo, anexos, testemunhas, análise, próximos passos, alertas ou explicações fora dos blocos.

Não invente dados. Use linguagem prudente.

Comece direto pelo BLOCO 1.
"""

    response = _fallback_response(
        case=_fake_case(
            case_number="TRAB-INSALUBRIDADE-PROVAS-001",
            title="Provas de insalubridade por calor em setor de fusão",
            legal_area="Trabalhista",
            action_type="reclamação trabalhista",
            description=(
                "Resumo técnico: Reclamante trabalhou em setor de fusão da Tupy S.A. em Joinville/SC, "
                "com processo produtivo envolvendo metal em fusão e exposição a calor intenso. "
                "Alega adicional de insalubridade por calor e, subsidiariamente, periculosidade. "
                "A pretensão depende de prova técnica, perícia, medições ambientais, PPP, LTCAT, PGR, PCMSO, "
                "ficha de EPI, registros de entrega e treinamento de EPI, folhas de pagamento, CTPS, TRCT e testemunhas do setor de fusão."
            ),
        ),
        message=message,
        context={},
        timeline=[],
    )

    rewritten = response["rewritten_input"]

    assert response["assistant_mode"] == "editor_all_blocks_ready"
    assert response["metadata"]["action_specialization_kind"] == "labor_health_risk_premium_claim"

    provas = rewritten.split("BLOCO 6 — Provas e requerimentos", 1)[1].split(
        "BLOCO 7 — Fechamento e conferência final", 1
    )[0]
    normalized_provas = " ".join(provas.split()).lower()

    assert "prova técnica pericial" in normalized_provas
    assert "saúde e segurança do trabalho" in normalized_provas
    assert "setor de fusão" in normalized_provas
    assert "exposição a calor" in normalized_provas
    assert "metal em fusão" in normalized_provas
    assert "medições ambientais" in normalized_provas
    assert "grau de insalubridade" in normalized_provas
    assert "periculosidade" in normalized_provas
    assert "eficácia dos epis" in normalized_provas
    assert "quesitos periciais" in normalized_provas
    assert "assistente técnico" in normalized_provas
    assert "ppp" in normalized_provas
    assert "ltcat" in normalized_provas
    assert "pgr" in normalized_provas
    assert "pcmso" in normalized_provas
    assert "ficha de epi" in normalized_provas
    assert "registros de entrega e treinamento de epi" in normalized_provas
    assert "folhas de pagamento" in normalized_provas
    assert "ctps" in normalized_provas
    assert "trct" in normalized_provas
    assert "testemunhal de colegas do setor de fusão" in normalized_provas

    forbidden_generic_evidence_markers = (
        "áudios, vídeos, consultas oficiais",
        "comprovantes de pagamento, contratos, recibos, mensagens, prints",
        "documentos do veículo",
        "comprovantes pix",
        "controles de ponto",
    )
    for marker in forbidden_generic_evidence_markers:
        assert marker not in normalized_provas


def test_editor_all_blocks_ready_labor_health_risk_uses_labor_court_heading_and_parties():
    message = """
Gere todos os blocos principais da minuta preliminar deste caso em formato de texto pronto para copiar e colar no Editor/minuta.

Entregue somente os blocos finais, separados por títulos exatamente assim:

BLOCO 1 — Endereçamento
BLOCO 2 — Qualificação das partes
BLOCO 3 — Resumo Fático
BLOCO 4 — Fundamentação preliminar
BLOCO 5 — Pedidos
BLOCO 6 — Provas e requerimentos
BLOCO 7 — Fechamento e conferência final

Não traga checklist operacional, linha do tempo, anexos, testemunhas, análise, próximos passos, alertas ou explicações fora dos blocos.

Não invente dados. Use linguagem prudente.

Comece direto pelo BLOCO 1.
"""

    response = _fallback_response(
        case=_fake_case(
            case_number="TRAB-ENDERECAMENTO-VT-001",
            title="Endereçamento trabalhista em adicional de insalubridade",
            legal_area="Trabalhista",
            action_type="reclamação trabalhista",
            description=(
                "Resumo técnico: Reclamante trabalhou em setor de fusão da Tupy S.A. em Joinville/SC, "
                "com exposição a calor intenso e metal em fusão. "
                "Alega adicional de insalubridade por calor e, subsidiariamente, periculosidade, "
                "dependendo de perícia técnica, PPP, LTCAT, PGR, PCMSO e fichas de EPI."
            ),
        ),
        message=message,
        context={},
        timeline=[],
    )

    rewritten = response["rewritten_input"]

    assert response["assistant_mode"] == "editor_all_blocks_ready"
    assert response["metadata"]["action_specialization_kind"] == "labor_health_risk_premium_claim"

    enderecamento = rewritten.split("BLOCO 1 — Endereçamento", 1)[1].split(
        "BLOCO 2 — Qualificação das partes", 1
    )[0]
    qualificacao = rewritten.split("BLOCO 2 — Qualificação das partes", 1)[1].split(
        "BLOCO 3 — Resumo Fático", 1
    )[0]

    normalized_enderecamento = " ".join(enderecamento.split()).lower()
    normalized_qualificacao = " ".join(qualificacao.split()).lower()

    assert "juiz(a) da vara do trabalho" in normalized_enderecamento
    assert "justiça do trabalho" in normalized_enderecamento
    assert "vara do trabalho competente" in normalized_enderecamento
    assert "rito trabalhista" in normalized_enderecamento
    assert "local da prestação de serviços" in normalized_enderecamento

    assert "reclamante:" in normalized_qualificacao
    assert "reclamada:" in normalized_qualificacao
    assert "ctps" in normalized_qualificacao
    assert "contrato de trabalho" in normalized_qualificacao

    forbidden_civil_heading_markers = (
        "juiz(a) de direito",
        "comarca de [comarca",
        "parte autora:",
        "parte ré:",
        "parte re:",
    )
    combined = f"{normalized_enderecamento} {normalized_qualificacao}"
    for marker in forbidden_civil_heading_markers:
        assert marker not in combined


def test_editor_all_blocks_ready_family_support_guardianship_router_keeps_family_requests_specific():
    message = """
Gere todos os blocos principais da minuta preliminar deste caso em formato de texto pronto para copiar e colar no Editor/minuta.

Entregue somente os blocos finais, separados por títulos exatamente assim:

BLOCO 1 — Endereçamento
BLOCO 2 — Qualificação das partes
BLOCO 3 — Resumo Fático
BLOCO 4 — Fundamentação preliminar
BLOCO 5 — Pedidos
BLOCO 6 — Provas e requerimentos
BLOCO 7 — Fechamento e conferência final

Não traga checklist operacional, linha do tempo, anexos, testemunhas, análise, próximos passos, alertas ou explicações fora dos blocos.

Não invente dados. Use linguagem prudente.

Comece direto pelo BLOCO 1.
"""

    response = _fallback_response(
        case=_fake_case(
            case_number="FAM-ALIMENTOS-GUARDA-001",
            title="Alimentos, guarda e convivência de menor",
            legal_area="Família",
            action_type="ação de alimentos, guarda e regulamentação de convivência",
            description=(
                "Representante legal pretende fixação de alimentos, guarda e regulamentação de convivência em favor de menor. "
                "Há certidão de nascimento, comprovantes de despesas do menor, informações escolares, documentos de saúde, "
                "comprovante de residência, mensagens entre os genitores e informações sobre renda aproximada do genitor. "
                "A análise deve observar o melhor interesse do menor, rotina de cuidados, capacidade econômica dos genitores "
                "e necessidade de visitas adequadas."
            ),
        ),
        message=message,
        context={},
        timeline=[],
    )

    rewritten = response["rewritten_input"]

    assert response["assistant_mode"] == "editor_all_blocks_ready"
    assert response["metadata"]["action_specialization_kind"] == "family_support_guardianship_claim"

    enderecamento = rewritten.split("BLOCO 1 — Endereçamento", 1)[1].split(
        "BLOCO 2 — Qualificação das partes", 1
    )[0]
    qualificacao = rewritten.split("BLOCO 2 — Qualificação das partes", 1)[1].split(
        "BLOCO 3 — Resumo Fático", 1
    )[0]
    fundamentacao = rewritten.split("BLOCO 4 — Fundamentação preliminar", 1)[1].split(
        "BLOCO 5 — Pedidos", 1
    )[0]
    pedidos = rewritten.split("BLOCO 5 — Pedidos", 1)[1].split(
        "BLOCO 6 — Provas e requerimentos", 1
    )[0]

    normalized_enderecamento = " ".join(enderecamento.split()).lower()
    normalized_qualificacao = " ".join(qualificacao.split()).lower()
    normalized_fundamentacao = " ".join(fundamentacao.split()).lower()
    normalized_pedidos = " ".join(pedidos.split()).lower()

    assert "vara de família" in normalized_enderecamento
    assert "segredo de justiça" in normalized_enderecamento
    assert "ministério público" in normalized_enderecamento

    assert "requerente:" in normalized_qualificacao
    assert "requerido(a):" in normalized_qualificacao
    assert "criança/adolescente:" in normalized_qualificacao
    assert "certidão de nascimento" in normalized_qualificacao

    assert "demanda de família" in normalized_fundamentacao
    assert "alimentos" in normalized_fundamentacao
    assert "guarda" in normalized_fundamentacao
    assert "convivência familiar" in normalized_fundamentacao
    assert "melhor interesse da criança" in normalized_fundamentacao
    assert "despesas" in normalized_fundamentacao
    assert "capacidade econômica dos genitores" in normalized_fundamentacao

    assert "fixação" in normalized_pedidos
    assert "alimentos" in normalized_pedidos
    assert "guarda" in normalized_pedidos
    assert "regime de convivência familiar" in normalized_pedidos
    assert "certidão de nascimento" in normalized_pedidos
    assert "documentos escolares" in normalized_pedidos
    assert "documentos médicos" in normalized_pedidos
    assert "comprovantes de renda" in normalized_pedidos
    assert "alimentos provisórios" in normalized_pedidos
    assert "ministério público" in normalized_pedidos
    assert "melhor interesse da criança" in normalized_pedidos

    forbidden_generic_civil_markers = (
        "prestação de contas ou esclarecimentos formais",
        "restituição, obrigação de fazer ou não fazer",
        "saldo contratual inadimplido",
        "horas extras",
        "intervalo intrajornada",
        "adicional de insalubridade",
        "documentos do veículo",
    )
    combined = f"{normalized_fundamentacao} {normalized_pedidos}"
    for marker in forbidden_generic_civil_markers:
        assert marker not in combined


def test_editor_all_blocks_ready_family_guardianship_router_handles_visitation_without_support_word():
    message = """
Gere todos os blocos principais da minuta preliminar deste caso em formato de texto pronto para copiar e colar no Editor/minuta.

Entregue somente os blocos finais, separados por títulos exatamente assim:

BLOCO 1 — Endereçamento
BLOCO 2 — Qualificação das partes
BLOCO 3 — Resumo Fático
BLOCO 4 — Fundamentação preliminar
BLOCO 5 — Pedidos
BLOCO 6 — Provas e requerimentos
BLOCO 7 — Fechamento e conferência final

Não invente dados. Use linguagem prudente.

Comece direto pelo BLOCO 1.
"""

    response = _fallback_response(
        case=_fake_case(
            case_number="FAM-GUARDA-VISITAS-001",
            title="Guarda e regulamentação de visitas",
            legal_area="Família",
            action_type="ação de guarda e regulamentação de convivência",
            description=(
                "Genitora pretende regularizar guarda e convivência de filho menor, com histórico de cuidados diários, "
                "escola, saúde e divergência sobre visitas. Há necessidade de documentos da criança, comprovante de residência, "
                "informações escolares, documentos de saúde e análise do melhor interesse do menor."
            ),
        ),
        message=message,
        context={},
        timeline=[],
    )

    rewritten = response["rewritten_input"]

    assert response["assistant_mode"] == "editor_all_blocks_ready"
    assert response["metadata"]["action_specialization_kind"] == "family_support_guardianship_claim"

    normalized = " ".join(rewritten.split()).lower()

    assert "vara de família" in normalized
    assert "requerente:" in normalized
    assert "requerido(a):" in normalized
    assert "guarda" in normalized
    assert "convivência" in normalized
    assert "visitas" in normalized
    assert "melhor interesse" in normalized
    assert "prestação de contas ou esclarecimentos formais" not in normalized


def test_editor_all_blocks_ready_family_evidence_block_keeps_family_proof_specific():
    message = """
Gere todos os blocos principais da minuta preliminar deste caso em formato de texto pronto para copiar e colar no Editor/minuta.

Entregue somente os blocos finais, separados por títulos exatamente assim:

BLOCO 1 — Endereçamento
BLOCO 2 — Qualificação das partes
BLOCO 3 — Resumo Fático
BLOCO 4 — Fundamentação preliminar
BLOCO 5 — Pedidos
BLOCO 6 — Provas e requerimentos
BLOCO 7 — Fechamento e conferência final

Não invente dados. Use linguagem prudente.

Comece direto pelo BLOCO 1.
"""

    response = _fallback_response(
        case=_fake_case(
            case_number="FAM-ALIMENTOS-PROVAS-001",
            title="Provas em ação de alimentos",
            legal_area="Família",
            action_type="ação de alimentos",
            description=(
                "Representante legal pretende fixação de alimentos em favor de criança. "
                "Há certidão de nascimento, comprovante de residência, comprovantes das despesas da criança, "
                "documentos escolares, laudos e receitas médicas, mensagens entre os genitores, comprovantes de pagamentos esporádicos "
                "e informações sobre renda formal ou informal do genitor. "
                "Pode ser necessário estudo psicossocial, prova testemunhal, segredo de justiça e intervenção do Ministério Público."
            ),
        ),
        message=message,
        context={},
        timeline=[],
    )

    rewritten = response["rewritten_input"]

    assert response["assistant_mode"] == "editor_all_blocks_ready"
    assert response["metadata"]["action_specialization_kind"] == "family_support_guardianship_claim"

    provas = rewritten.split("BLOCO 6 — Provas e requerimentos", 1)[1].split(
        "BLOCO 7 — Fechamento e conferência final", 1
    )[0]
    normalized_provas = " ".join(provas.split()).lower()

    assert "certidão de nascimento" in normalized_provas
    assert "comprovantes das despesas da criança" in normalized_provas
    assert "comprovantes de renda" in normalized_provas
    assert "documentos escolares" in normalized_provas
    assert "documentos médicos" in normalized_provas
    assert "mensagens entre os responsáveis" in normalized_provas
    assert "comprovantes de pagamentos de alimentos" in normalized_provas
    assert "estudo psicossocial" in normalized_provas
    assert "avaliação interdisciplinar" in normalized_provas
    assert "prova testemunhal" in normalized_provas
    assert "segredo de justiça" in normalized_provas
    assert "ministério público" in normalized_provas
    assert "melhor interesse da criança" in normalized_provas

    forbidden_wrong_evidence_markers = (
        "ppp",
        "ltcat",
        "pcmso",
        "ficha de epi",
        "ctps",
        "trct",
        "horas extras",
        "intervalo intrajornada",
        "insalubridade",
        "documentos do veículo",
        "comprovantes pix",
    )
    for marker in forbidden_wrong_evidence_markers:
        assert marker not in normalized_provas


def test_editor_all_blocks_ready_family_request_scope_keeps_support_only():
    message = """
Gere todos os blocos principais da minuta preliminar deste caso em formato de texto pronto para copiar e colar no Editor/minuta.

Entregue somente os blocos finais, separados por títulos exatamente assim:

BLOCO 1 — Endereçamento
BLOCO 2 — Qualificação das partes
BLOCO 3 — Resumo Fático
BLOCO 4 — Fundamentação preliminar
BLOCO 5 — Pedidos
BLOCO 6 — Provas e requerimentos
BLOCO 7 — Fechamento e conferência final

Não invente dados. Use linguagem prudente.

Comece direto pelo BLOCO 1.
"""

    response = _fallback_response(
        case=_fake_case(
            case_number="FAM-ALIMENTOS-ESCOPO-001",
            title="Ação de alimentos",
            legal_area="Família",
            action_type="ação de alimentos",
            description=(
                "Representante legal pretende a fixação de alimentos provisórios e definitivos em favor de criança. "
                "Há certidão de nascimento, despesas escolares e médicas, comprovantes de residência, mensagens "
                "e informações sobre a renda do genitor."
            ),
        ),
        message=message,
        context={},
        timeline=[],
    )

    rewritten = response["rewritten_input"]
    assert response["metadata"]["action_specialization_kind"] == "family_support_guardianship_claim"

    pedidos = rewritten.split("BLOCO 5 — Pedidos", 1)[1].split(
        "BLOCO 6 — Provas e requerimentos", 1
    )[0]
    normalized = " ".join(pedidos.split()).lower()

    assert "alimentos provisórios e definitivos" in normalized
    assert "necessidades da criança" in normalized
    assert "capacidade econômica" in normalized

    assert "regularização da guarda" not in normalized
    assert "guarda unilateral" not in normalized
    assert "guarda compartilhada" not in normalized
    assert "regime de convivência familiar" not in normalized
    assert "definição de visitas" not in normalized
    assert "datas comemorativas" not in normalized


def test_editor_all_blocks_ready_family_request_scope_keeps_guardianship_only():
    message = """
Gere todos os blocos principais da minuta preliminar deste caso em formato de texto pronto para copiar e colar no Editor/minuta.

Entregue somente os blocos finais, separados por títulos exatamente assim:

BLOCO 1 — Endereçamento
BLOCO 2 — Qualificação das partes
BLOCO 3 — Resumo Fático
BLOCO 4 — Fundamentação preliminar
BLOCO 5 — Pedidos
BLOCO 6 — Provas e requerimentos
BLOCO 7 — Fechamento e conferência final

Não invente dados. Use linguagem prudente.

Comece direto pelo BLOCO 1.
"""

    response = _fallback_response(
        case=_fake_case(
            case_number="FAM-GUARDA-ESCOPO-001",
            title="Ação de guarda",
            legal_area="Família",
            action_type="ação de guarda",
            description=(
                "Genitora pretende regularização da guarda da criança conforme a rotina de cuidados já existente. "
                "Há certidão de nascimento, comprovante de residência, documentos escolares, documentos médicos "
                "e informações sobre a participação de cada responsável nos cuidados."
            ),
        ),
        message=message,
        context={},
        timeline=[],
    )

    rewritten = response["rewritten_input"]
    assert response["metadata"]["action_specialization_kind"] == "family_support_guardianship_claim"

    pedidos = rewritten.split("BLOCO 5 — Pedidos", 1)[1].split(
        "BLOCO 6 — Provas e requerimentos", 1
    )[0]
    normalized = " ".join(pedidos.split()).lower()

    assert "regularização da guarda" in normalized
    assert "unilateral ou compartilhada" in normalized
    assert "rotina de cuidados" in normalized
    assert "melhor interesse" in normalized

    assert "alimentos provisórios" not in normalized
    assert "alimentos definitivos" not in normalized
    assert "regime de convivência familiar" not in normalized
    assert "definição de visitas" not in normalized
    assert "datas comemorativas" not in normalized


def test_editor_all_blocks_ready_family_request_scope_keeps_visitation_only():
    message = """
Gere todos os blocos principais da minuta preliminar deste caso em formato de texto pronto para copiar e colar no Editor/minuta.

Entregue somente os blocos finais, separados por títulos exatamente assim:

BLOCO 1 — Endereçamento
BLOCO 2 — Qualificação das partes
BLOCO 3 — Resumo Fático
BLOCO 4 — Fundamentação preliminar
BLOCO 5 — Pedidos
BLOCO 6 — Provas e requerimentos
BLOCO 7 — Fechamento e conferência final

Não invente dados. Use linguagem prudente.

Comece direto pelo BLOCO 1.
"""

    response = _fallback_response(
        case=_fake_case(
            case_number="FAM-CONVIVENCIA-ESCOPO-001",
            title="Regulamentação de convivência",
            legal_area="Família",
            action_type="regulamentação de convivência e visitas",
            description=(
                "Genitor pretende regulamentação da convivência com a criança, incluindo visitas, férias, "
                "datas comemorativas e forma de comunicação entre os responsáveis. "
                "Há mensagens, calendário anterior e informações sobre a rotina escolar."
            ),
        ),
        message=message,
        context={},
        timeline=[],
    )

    rewritten = response["rewritten_input"]
    assert response["metadata"]["action_specialization_kind"] == "family_support_guardianship_claim"

    pedidos = rewritten.split("BLOCO 5 — Pedidos", 1)[1].split(
        "BLOCO 6 — Provas e requerimentos", 1
    )[0]
    normalized = " ".join(pedidos.split()).lower()

    assert "regime de convivência familiar" in normalized
    assert "visitas" in normalized
    assert "férias" in normalized
    assert "datas comemorativas" in normalized
    assert "comunicação entre os responsáveis" in normalized

    assert "alimentos provisórios" not in normalized
    assert "alimentos definitivos" not in normalized
    assert "regularização da guarda" not in normalized
    assert "guarda unilateral" not in normalized
    assert "guarda compartilhada" not in normalized


def _consumer_scope_ready_response(case_number, title, action_type, description):
    message = """
Gere todos os blocos principais da minuta preliminar deste caso em formato de texto pronto para copiar e colar no Editor/minuta.

Entregue somente os blocos finais, separados por títulos exatamente assim:

BLOCO 1 — Endereçamento
BLOCO 2 — Qualificação das partes
BLOCO 3 — Resumo Fático
BLOCO 4 — Fundamentação preliminar
BLOCO 5 — Pedidos
BLOCO 6 — Provas e requerimentos
BLOCO 7 — Fechamento e conferência final

Não invente dados. Use linguagem prudente.

Comece direto pelo BLOCO 1.
"""
    return _fallback_response(
        case=_fake_case(
            case_number=case_number,
            title=title,
            legal_area="Consumidor",
            action_type=action_type,
            description=description,
        ),
        message=message,
        context={},
        timeline=[],
    )


def _consumer_scope_block(response, start, end):
    rewritten = response["rewritten_input"]
    value = rewritten.split(start, 1)[1].split(end, 1)[0]
    return " ".join(value.split()).lower()


def test_editor_all_blocks_ready_consumer_universal_scope_combines_bank_charge_and_negative_listing():
    response = _consumer_scope_ready_response(
        "CONS-BANCO-001",
        "Fraude Pix, cobrança e negativação",
        "ação declaratória consumerista",
        (
            "Consumidor sofreu fraude bancária com Pix não reconhecido, contestou a transação e mesmo assim recebeu cobrança indevida. "
            "Posteriormente houve negativação indevida no Serasa. Há extratos, boletim de ocorrência, protocolos, mensagens e comprovantes."
        ),
    )

    assert response["metadata"]["action_specialization_kind"] == "consumer_universal_action_scope_claim"
    pedidos = _consumer_scope_block(response, "BLOCO 5 — Pedidos", "BLOCO 6 — Provas e requerimentos")

    assert "transações impugnadas" in pedidos
    assert "logs" in pedidos
    assert "inexistência ou inexigibilidade da cobrança" in pedidos
    assert "retirada ou suspensão da anotação indevida" in pedidos
    assert "documentos que originaram a inscrição" in pedidos
    assert "reparo, a substituição do produto" not in pedidos
    assert "cobertura do procedimento" not in pedidos


def test_editor_all_blocks_ready_consumer_universal_scope_keeps_defective_product_specific():
    response = _consumer_scope_ready_response(
        "CONS-PRODUTO-001",
        "Produto defeituoso",
        "ação consumerista por vício do produto",
        (
            "Consumidora comprou eletrodoméstico com defeito, apresentou nota fiscal e acionou a garantia e a assistência técnica, "
            "mas o produto continuou impróprio para uso. Pretende solução compatível com o vício do produto."
        ),
    )

    assert response["metadata"]["action_specialization_kind"] == "consumer_universal_action_scope_claim"
    pedidos = _consumer_scope_block(response, "BLOCO 5 — Pedidos", "BLOCO 6 — Provas e requerimentos")

    assert "reparo, a substituição do produto" in pedidos
    assert "restituição do preço" in pedidos
    assert "nota fiscal" in pedidos
    assert "logs, ips, dispositivos" not in pedidos
    assert "retirada ou suspensão da anotação" not in pedidos
    assert "cobertura do procedimento" not in pedidos


def test_editor_all_blocks_ready_consumer_universal_scope_keeps_defective_service_specific():
    response = _consumer_scope_ready_response(
        "CONS-SERVICO-001",
        "Falha na prestação de serviço",
        "ação consumerista por serviço defeituoso",
        (
            "Consumidor contratou serviço que foi prestado de forma incompleta e defeituosa. "
            "Há contrato, oferta, comprovantes de pagamento, protocolos e mensagens solicitando correção."
        ),
    )

    assert response["metadata"]["action_specialization_kind"] == "consumer_universal_action_scope_claim"
    pedidos = _consumer_scope_block(response, "BLOCO 5 — Pedidos", "BLOCO 6 — Provas e requerimentos")

    assert "refazimento adequado do serviço" in pedidos
    assert "correção da falha" in pedidos
    assert "restituição dos valores" in pedidos
    assert "substituição do produto" not in pedidos
    assert "transações impugnadas" not in pedidos
    assert "cobertura do procedimento" not in pedidos


def test_editor_all_blocks_ready_consumer_universal_scope_keeps_health_plan_specific():
    response = _consumer_scope_ready_response(
        "CONS-SAUDE-001",
        "Negativa de cobertura médica",
        "obrigação de fazer contra plano de saúde",
        (
            "Consumidora teve procedimento médico e cirurgia negados pelo plano de saúde, apesar de relatório e prescrição médica. "
            "Há risco de agravamento, contrato, protocolos e justificativa de negativa de cobertura."
        ),
    )

    assert response["metadata"]["action_specialization_kind"] == "consumer_universal_action_scope_claim"
    fundamentacao = _consumer_scope_block(
        response,
        "BLOCO 4 — Fundamentação preliminar",
        "BLOCO 5 — Pedidos",
    )
    pedidos = _consumer_scope_block(
        response,
        "BLOCO 5 — Pedidos",
        "BLOCO 6 — Provas e requerimentos",
    )

    assert "autorização ou cobertura" in pedidos
    assert "procedimento" in pedidos
    assert "cirurgia" in pedidos
    assert "exame" not in pedidos
    assert "internação" not in pedidos
    assert "com tutela de urgência apenas quando sustentada" in pedidos
    assert "risco de agravamento" in fundamentacao
    assert "relatório médico" in pedidos
    assert "justificativa formal da negativa" in pedidos
    assert "substituição do produto" not in pedidos
    assert "retirada ou suspensão da anotação" not in pedidos


def test_editor_all_blocks_ready_consumer_universal_scope_keeps_general_contract_fallback_prudent():
    response = _consumer_scope_ready_response(
        "CONS-GERAL-001",
        "Descumprimento de oferta",
        "ação consumerista contratual",
        (
            "Consumidor realizou compra após oferta anunciada pelo fornecedor, efetuou pagamento, mas a entrega não ocorreu. "
            "Há pedido, publicidade, comprovantes, protocolos de atendimento e solicitação de cancelamento e reembolso."
        ),
    )

    assert response["metadata"]["action_specialization_kind"] == "consumer_universal_action_scope_claim"
    pedidos = _consumer_scope_block(response, "BLOCO 5 — Pedidos", "BLOCO 6 — Provas e requerimentos")

    assert "documentos essenciais da contratação" in pedidos
    assert "cumprimento da oferta" in pedidos
    assert "cancelamento" in pedidos
    assert "restituição" in pedidos
    assert "correção do serviço" not in pedidos
    assert "transações impugnadas" not in pedidos
    assert "substituição do produto" not in pedidos
    assert "cobertura do procedimento" not in pedidos



def test_editor_all_blocks_ready_consumer_evidence_scope_combines_bank_charge_and_negative_listing():
    response = _consumer_scope_ready_response(
        "CONS-BANCO-PROVAS-001",
        "Fraude Pix, cobrança e negativação",
        "ação declaratória consumerista",
        (
            "Consumidor sofreu fraude bancária com Pix não reconhecido, recebeu cobrança indevida "
            "e posteriormente foi negativado no Serasa. "
            "Há extratos bancários, boletim de ocorrência, protocolos de contestação, mensagens "
            "e comprovante de negativação."
        ),
    )

    provas = _consumer_scope_block(
        response,
        "BLOCO 6 — Provas e requerimentos",
        "BLOCO 7 — Fechamento e conferência final",
    )

    assert "extratos bancários" in provas
    assert "boletim de ocorrência" in provas
    assert "protocolos de contestação" in provas
    assert "logs" in provas
    assert "ips" in provas
    assert "dispositivos" in provas
    assert "comprovante de negativação" in provas
    assert "órgãos de proteção ao crédito" not in provas
    assert "assistência técnica" not in provas
    assert "prescrição médica" not in provas


def test_editor_all_blocks_ready_consumer_evidence_scope_keeps_defective_product_specific():
    response = _consumer_scope_ready_response(
        "CONS-PRODUTO-PROVAS-001",
        "Produto defeituoso",
        "ação consumerista por vício do produto",
        (
            "Consumidora comprou eletrodoméstico com defeito. "
            "Há nota fiscal, certificado de garantia, fotografias, vídeos, ordens de serviço "
            "e registros da assistência técnica."
        ),
    )

    provas = _consumer_scope_block(
        response,
        "BLOCO 6 — Provas e requerimentos",
        "BLOCO 7 — Fechamento e conferência final",
    )

    assert "nota fiscal" in provas
    assert "certificado de garantia" in provas
    assert "fotografias" in provas
    assert "vídeos" in provas
    assert "ordens de serviço" in provas
    assert "assistência técnica" in provas
    assert "logs, ips" not in provas
    assert "prescrição médica" not in provas


def test_editor_all_blocks_ready_consumer_evidence_scope_keeps_defective_service_specific():
    response = _consumer_scope_ready_response(
        "CONS-SERVICO-PROVAS-001",
        "Falha na prestação de serviço",
        "ação consumerista por serviço defeituoso",
        (
            "Consumidor contratou serviço prestado de forma incompleta. "
            "Há contrato, oferta, ordem de serviço, comprovantes de pagamento, protocolos, "
            "mensagens e registros das tentativas de correção."
        ),
    )

    provas = _consumer_scope_block(
        response,
        "BLOCO 6 — Provas e requerimentos",
        "BLOCO 7 — Fechamento e conferência final",
    )

    assert "contrato" in provas
    assert "oferta" in provas
    assert "ordem de serviço" in provas
    assert "comprovantes de pagamento" in provas
    assert "protocolos" in provas
    assert "tentativas de correção" in provas
    assert "documentos do veículo" not in provas
    assert "relatório médico" not in provas


def test_editor_all_blocks_ready_consumer_evidence_scope_keeps_health_plan_specific():
    response = _consumer_scope_ready_response(
        "CONS-SAUDE-PROVAS-001",
        "Negativa de cobertura médica",
        "obrigação de fazer contra plano de saúde",
        (
            "Consumidora teve cirurgia negada pelo plano de saúde. "
            "Há contrato do plano, relatório médico, prescrição médica, exames, prontuário, "
            "protocolos e negativa formal da operadora."
        ),
    )

    provas = _consumer_scope_block(
        response,
        "BLOCO 6 — Provas e requerimentos",
        "BLOCO 7 — Fechamento e conferência final",
    )

    assert "contrato do plano" in provas
    assert "relatório médico" in provas
    assert "prescrição médica" in provas
    assert "exames" in provas
    assert "prontuário" in provas
    assert "negativa formal" in provas
    assert "urgência clínica" not in provas
    assert "assistência técnica" not in provas
    assert "órgãos de proteção ao crédito" not in provas


def test_editor_all_blocks_ready_consumer_evidence_scope_keeps_general_contract_prudent():
    response = _consumer_scope_ready_response(
        "CONS-GERAL-PROVAS-001",
        "Descumprimento de oferta",
        "ação consumerista contratual",
        (
            "Consumidor realizou compra após oferta anunciada, mas a entrega não ocorreu. "
            "Há publicidade, pedido, comprovante de pagamento, rastreamento, protocolos, "
            "mensagens, solicitação de cancelamento e pedido de reembolso."
        ),
    )

    provas = _consumer_scope_block(
        response,
        "BLOCO 6 — Provas e requerimentos",
        "BLOCO 7 — Fechamento e conferência final",
    )

    assert "oferta" in provas
    assert "publicidade" in provas
    assert "pedido" in provas
    assert "comprovante de pagamento" in provas
    assert "rastreamento" in provas
    assert "cancelamento" in provas
    assert "reembolso" in provas
    assert "logs, ips" not in provas
    assert "prescrição médica" not in provas


def test_editor_all_blocks_ready_consumer_vehicle_evidence_scope_keeps_vehicle_documents_specific():
    response = _consumer_scope_ready_response(
        "CONS-VEICULO-PROVAS-001",
        "Retenção de veículo e exibição contratual",
        "ação consumerista envolvendo veículo",
        (
            "Consumidor adquiriu veículo de revendedora, realizou pagamentos por Pix e depois o bem foi retomado. "
            "Há contrato, recibos, comprovantes Pix, documentos do veículo, placa, RENAVAM, "
            "consulta de restrição, mensagens e dúvida sobre eventual ordem judicial."
        ),
    )

    provas = _consumer_scope_block(
        response,
        "BLOCO 6 — Provas e requerimentos",
        "BLOCO 7 — Fechamento e conferência final",
    )

    assert response["metadata"]["action_specialization_kind"] == (
        "consumer_vehicle_contract_display_restitution"
    )
    assert "contrato" in provas
    assert "recibos" in provas
    assert "comprovantes pix" in provas
    assert "documentos do veículo" in provas
    assert "placa" in provas
    assert "renavam" in provas
    assert "consulta de restrição" in provas
    assert "ordem judicial" in provas
    assert "prescrição médica" not in provas


def test_editor_all_blocks_ready_consumer_browser_regression_detects_plain_negative_listing_without_general_contract_noise():
    response = _consumer_scope_ready_response(
        "TESTE-CONSUMIDOR-PIX-NEGATIVACAO-001",
        "Fraude bancária por Pix, cobrança indevida e negativação",
        "Ação consumerista por fraude bancária, cobrança indevida e negativação",
        (
            "O consumidor identificou uma transferência via Pix que afirma não ter realizado nem autorizado. "
            "Comunicou imediatamente a instituição financeira, contestou a operação e solicitou o bloqueio e a restituição do valor, "
            "mas o banco manteve a cobrança. Posteriormente, houve inscrição do nome do consumidor em cadastro restritivo "
            "por débito relacionado à operação contestada. O consumidor possui extratos bancários, comprovante da transação, "
            "protocolos de atendimento e documento da negativação."
        ),
    )

    assert response["metadata"]["action_specialization_kind"] == (
        "consumer_universal_action_scope_claim"
    )

    fundamentacao = _consumer_scope_block(
        response,
        "BLOCO 4 — Fundamentação preliminar",
        "BLOCO 5 — Pedidos",
    )
    pedidos = _consumer_scope_block(
        response,
        "BLOCO 5 — Pedidos",
        "BLOCO 6 — Provas e requerimentos",
    )
    provas = _consumer_scope_block(
        response,
        "BLOCO 6 — Provas e requerimentos",
        "BLOCO 7 — Fechamento e conferência final",
    )

    assert "segurança da operação bancária" in fundamentacao
    assert "origem da cobrança" in fundamentacao
    assert "regularidade da inscrição" in fundamentacao
    assert "cumprimento efetivo das obrigações assumidas" not in fundamentacao

    assert "transações impugnadas" in pedidos
    assert "inexistência ou inexigibilidade da cobrança" in pedidos
    assert "retirada ou suspensão da anotação indevida" in pedidos
    assert "documentos essenciais da contratação" not in pedidos

    assert "extratos bancários" in provas
    assert "histórico dos débitos" not in provas
    assert "comprovante de negativação" in provas
    assert "órgãos de proteção ao crédito" not in provas
    assert "contrato consumerista geral" not in provas



def test_editor_all_blocks_ready_consumer_browser_regression_keeps_banking_fraud_isolated():
    response = _consumer_scope_ready_response(
        "TESTE-CONSUMIDOR-FRAUDE-BANCARIA-ISOLADA-001",
        "Fraude bancária por Pix não reconhecido",
        "ação declaratória consumerista por transação não reconhecida",
        (
            "O consumidor identificou uma transferência via Pix que afirma não ter realizado nem autorizado. "
            "Comunicou imediatamente a instituição financeira e contestou a operação. "
            "Possui extratos bancários, comprovante da transação, protocolos e mensagens."
        ),
    )

    assert response["metadata"]["action_specialization_kind"] == (
        "consumer_universal_action_scope_claim"
    )

    fundamentacao = _consumer_scope_block(
        response,
        "BLOCO 4 — Fundamentação preliminar",
        "BLOCO 5 — Pedidos",
    )
    pedidos = _consumer_scope_block(
        response,
        "BLOCO 5 — Pedidos",
        "BLOCO 6 — Provas e requerimentos",
    )
    provas = _consumer_scope_block(
        response,
        "BLOCO 6 — Provas e requerimentos",
        "BLOCO 7 — Fechamento e conferência final",
    )

    assert "segurança da operação bancária" in fundamentacao
    assert "origem da cobrança" not in fundamentacao
    assert "regularidade da inscrição" not in fundamentacao
    assert "cumprimento efetivo das obrigações assumidas" not in fundamentacao

    assert "transações impugnadas" in pedidos
    assert "logs" in pedidos
    assert "ips" in pedidos
    assert "dispositivos" in pedidos
    assert "bloqueio de cobranças relacionadas" not in pedidos
    assert "inexistência ou inexigibilidade da cobrança" not in pedidos
    assert "retirada ou suspensão da anotação indevida" not in pedidos
    assert "documentos essenciais da contratação" not in pedidos

    assert "extratos bancários" in provas
    assert "comprovantes das transações" in provas
    assert "protocolos de contestação" in provas
    assert "logs" in provas
    assert "ips" in provas
    assert "dispositivos" in provas
    assert "boletim de ocorrência" not in provas
    assert "gravações" not in provas
    assert "respostas da instituição financeira" not in provas
    assert "histórico dos débitos" not in provas
    assert "comprovante de negativação" not in provas
    assert "órgãos de proteção ao crédito" not in provas


def test_editor_all_blocks_ready_consumer_browser_regression_keeps_wrongful_charge_isolated():
    response = _consumer_scope_ready_response(
        "TESTE-CONSUMIDOR-COBRANCA-INDEVIDA-ISOLADA-001",
        "Cobrança indevida isolada",
        "ação declaratória consumerista por cobrança indevida",
        (
            "A consumidora identificou tarifa indevida em sua fatura e afirma não ter autorizado o lançamento. "
            "Contestou administrativamente a cobrança. "
            "Possui fatura, extrato, comprovante de pagamento e protocolos de atendimento."
        ),
    )

    assert response["metadata"]["action_specialization_kind"] == (
        "consumer_universal_action_scope_claim"
    )

    fundamentacao = _consumer_scope_block(
        response,
        "BLOCO 4 — Fundamentação preliminar",
        "BLOCO 5 — Pedidos",
    )
    pedidos = _consumer_scope_block(
        response,
        "BLOCO 5 — Pedidos",
        "BLOCO 6 — Provas e requerimentos",
    )
    provas = _consumer_scope_block(
        response,
        "BLOCO 6 — Provas e requerimentos",
        "BLOCO 7 — Fechamento e conferência final",
    )

    assert "origem da cobrança" in fundamentacao
    assert "segurança da operação bancária" not in fundamentacao
    assert "regularidade da inscrição" not in fundamentacao
    assert "cumprimento efetivo das obrigações assumidas" not in fundamentacao

    assert "inexistência ou inexigibilidade da cobrança" in pedidos
    assert "restituição simples ou em dobro" in pedidos
    assert "interrupção de novos débitos" not in pedidos
    assert "transações impugnadas" not in pedidos
    assert "retirada ou suspensão da anotação indevida" not in pedidos
    assert "documentos essenciais da contratação" not in pedidos

    assert "fatura" in provas
    assert "extrato" in provas
    assert "comprovante de pagamento" in provas
    assert "protocolos de contestação" in provas
    assert "contrato" not in provas
    assert "autorizações" not in provas
    assert "histórico dos débitos" not in provas
    assert "logs, ips, dispositivos" not in provas
    assert "comprovante de negativação" not in provas
    assert "órgãos de proteção ao crédito" not in provas


def test_editor_all_blocks_ready_consumer_browser_regression_keeps_negative_listing_isolated():
    response = _consumer_scope_ready_response(
        "TESTE-CONSUMIDOR-NEGATIVACAO-INDEVIDA-ISOLADA-001",
        "Negativação indevida isolada",
        "ação consumerista por inscrição indevida",
        (
            "O consumidor descobriu que seu nome foi negativado no Serasa. "
            "Afirma desconhecer a origem do débito e solicitou esclarecimentos ao fornecedor. "
            "Possui comprovante de negativação, consulta do órgão de proteção ao crédito, "
            "protocolos de atendimento e mensagens."
        ),
    )

    assert response["metadata"]["action_specialization_kind"] == (
        "consumer_universal_action_scope_claim"
    )

    fundamentacao = _consumer_scope_block(
        response,
        "BLOCO 4 — Fundamentação preliminar",
        "BLOCO 5 — Pedidos",
    )
    pedidos = _consumer_scope_block(
        response,
        "BLOCO 5 — Pedidos",
        "BLOCO 6 — Provas e requerimentos",
    )
    provas = _consumer_scope_block(
        response,
        "BLOCO 6 — Provas e requerimentos",
        "BLOCO 7 — Fechamento e conferência final",
    )

    assert "regularidade da inscrição" in fundamentacao
    assert "comunicação prévia" not in fundamentacao
    assert "efeitos concretos da restrição" not in fundamentacao
    assert "segurança da operação bancária" not in fundamentacao
    assert "origem da cobrança" not in fundamentacao
    assert "cumprimento efetivo das obrigações assumidas" not in fundamentacao

    assert "retirada ou suspensão da anotação indevida" in pedidos
    assert "documentos que originaram a inscrição" in pedidos
    assert "transações impugnadas" not in pedidos
    assert "inexistência ou inexigibilidade da cobrança" not in pedidos
    assert "documentos essenciais da contratação" not in pedidos

    assert "comprovante de negativação" in provas
    assert "consulta do órgão de proteção ao crédito" in provas
    assert "protocolos de atendimento" in provas
    assert "mensagens" in provas
    assert "comunicação prévia" not in provas
    assert "documentos que originaram a inscrição" not in provas
    assert "histórico do débito" not in provas
    assert "efeitos concretos da restrição" not in provas
    assert "extratos bancários" not in provas
    assert "logs, ips, dispositivos" not in provas

def test_editor_all_blocks_ready_consumer_addressing_qualification_uses_consumer_civil_boundaries():
    response = _consumer_scope_ready_response(
        "CONS-END-QUAL-001",
        "Fraude bancária por Pix",
        "ação declaratória consumerista",
        (
            "Consumidor afirma não reconhecer transferência Pix e apresentou extratos, "
            "comprovante da transação e protocolos de contestação."
        ),
    )

    assert response["metadata"]["action_specialization_kind"] == (
        "consumer_universal_action_scope_claim"
    )

    enderecamento = _consumer_scope_block(
        response,
        "BLOCO 1 — Endereçamento",
        "BLOCO 2 — Qualificação das partes",
    )
    qualificacao = _consumer_scope_block(
        response,
        "BLOCO 2 — Qualificação das partes",
        "BLOCO 3 — Resumo Fático",
    )

    assert "juiz(a) de direito do juízo cível competente" in enderecamento
    assert "vara cível ou juizado especial cível" in enderecamento
    assert "competência territorial" in enderecamento
    assert "domicílio do consumidor" in enderecamento
    assert "valor da causa" in enderecamento
    assert "complexidade probatória" in enderecamento
    assert "necessidade de perícia" in enderecamento
    assert "rito aplicável" in enderecamento

    assert "consumidor(a):" in qualificacao
    assert "fornecedor(a):" in qualificacao
    assert "cpf" in qualificacao
    assert "comprovante de endereço" in qualificacao
    assert "cnpj ou cpf" in qualificacao
    assert "endereço para citação" in qualificacao
    assert "documentos da relação de consumo" in qualificacao

    combined = f"{enderecamento} {qualificacao}"
    forbidden_markers = (
        "vara do trabalho",
        "justiça do trabalho",
        "reclamante:",
        "reclamada:",
        "vara de família",
        "requerente:",
        "requerido(a):",
        "criança/adolescente:",
        "parte autora:",
        "parte ré:",
        "parte re:",
    )
    for marker in forbidden_markers:
        assert marker not in combined


def test_editor_all_blocks_ready_consumer_addressing_qualification_preserves_named_parties():
    response = _consumer_scope_ready_response(
        "CONS-END-QUAL-NOMES-001",
        "Cobrança indevida e negativação",
        "ação declaratória consumerista",
        (
            "Parte autora: Maria de Souza, CPF 000.000.000-00, residente em Joinville/SC. "
            "Parte ré: Banco Exemplo S.A., CNPJ 00.000.000/0001-00. "
            "A consumidora contesta cobrança indevida e inscrição em cadastro restritivo."
        ),
    )

    qualificacao = _consumer_scope_block(
        response,
        "BLOCO 2 — Qualificação das partes",
        "BLOCO 3 — Resumo Fático",
    )

    assert "consumidor(a): maria de souza" in qualificacao
    assert "cpf 000.000.000-00" in qualificacao
    assert "fornecedor(a): banco exemplo s.a." in qualificacao
    assert "cnpj 00.000.000/0001-00" in qualificacao
    assert "parte autora:" not in qualificacao
    assert "parte ré:" not in qualificacao
    assert "parte re:" not in qualificacao


def test_editor_all_blocks_ready_consumer_vehicle_addressing_qualification_uses_same_consumer_boundaries():
    response = _consumer_scope_ready_response(
        "CONS-VEICULO-END-QUAL-001",
        "Retenção de veículo e exibição contratual",
        "ação consumerista envolvendo veículo",
        (
            "Consumidor adquiriu veículo de revendedora, realizou pagamentos por Pix "
            "e depois o bem foi retomado. Há contrato, recibos, documentos do veículo, "
            "placa, RENAVAM, consulta de restrição e mensagens."
        ),
    )

    assert response["metadata"]["action_specialization_kind"] == (
        "consumer_vehicle_contract_display_restitution"
    )

    enderecamento = _consumer_scope_block(
        response,
        "BLOCO 1 — Endereçamento",
        "BLOCO 2 — Qualificação das partes",
    )
    qualificacao = _consumer_scope_block(
        response,
        "BLOCO 2 — Qualificação das partes",
        "BLOCO 3 — Resumo Fático",
    )

    assert "juízo cível competente" in enderecamento
    assert "vara cível ou juizado especial cível" in enderecamento
    assert "consumidor(a):" in qualificacao
    assert "fornecedor(a):" in qualificacao
    assert "documentos da relação de consumo" in qualificacao


def test_editor_all_blocks_ready_consumer_service_does_not_infer_damage_from_without_inventing_losses():
    response = _consumer_scope_ready_response(
        "TESTE-CONSUMIDOR-SERVICO-001",
        "Serviço contratado prestado de forma incompleta e defeituosa",
        "Ação consumerista por serviço defeituoso e incompleto",
        (
            "O consumidor contratou um serviço que foi executado de forma incompleta e apresentou falhas no resultado. "
            "Possui contrato, oferta, ordem de serviço, comprovantes de pagamento, protocolos de atendimento e mensagens. "
            "Solicitou a correção do problema, mas as tentativas não resolveram a falha. "
            "Pretende a análise das medidas cabíveis, sem inventar datas, valores, prejuízos ou documentos não informados."
        ),
    )

    fundamentacao = _consumer_scope_block(
        response,
        "BLOCO 4 — Fundamentação preliminar",
        "BLOCO 5 — Pedidos",
    )
    pedidos = _consumer_scope_block(
        response,
        "BLOCO 5 — Pedidos",
        "BLOCO 6 — Provas e requerimentos",
    )

    assert "serviço contratado" in fundamentacao
    assert "tentativas de correção" in fundamentacao
    assert "danos materiais ou morais" not in fundamentacao
    assert "eventual indenização" not in pedidos
    assert "danos materiais ou morais" not in pedidos


def test_editor_all_blocks_ready_consumer_service_keeps_explicit_material_damage_scope():
    response = _consumer_scope_ready_response(
        "CONS-SERVICO-DANO-MATERIAL-001",
        "Serviço defeituoso com prejuízo material comprovado",
        "Ação consumerista por serviço defeituoso e danos materiais",
        (
            "O consumidor contratou serviço executado de forma defeituosa. "
            "Relata prejuízo material decorrente da falha e possui comprovantes dos gastos adicionais, "
            "contrato, ordem de serviço, protocolos e mensagens."
        ),
    )

    fundamentacao = _consumer_scope_block(
        response,
        "BLOCO 4 — Fundamentação preliminar",
        "BLOCO 5 — Pedidos",
    )
    pedidos = _consumer_scope_block(
        response,
        "BLOCO 5 — Pedidos",
        "BLOCO 6 — Provas e requerimentos",
    )

    assert "danos materiais ou morais" in fundamentacao
    assert "demonstração da conduta" in fundamentacao
    assert "eventual indenização por danos materiais ou morais" in pedidos
    assert "documentados e confirmados pelo advogado" in pedidos


def test_editor_all_blocks_ready_health_plan_does_not_infer_unsupported_medical_scope():
    response = _consumer_scope_ready_response(
        "TESTE-CONSUMIDOR-PLANO-SAUDE-001",
        "Plano de saúde negou autorização de procedimento prescrito",
        "Ação consumerista contra plano de saúde por negativa de autorização",
        (
            "O consumidor é beneficiário de plano de saúde e recebeu prescrição médica "
            "para realização de procedimento ou tratamento. "
            "A operadora negou ou não concluiu a autorização, apesar dos pedidos e protocolos. "
            "Possui contrato ou carteirinha, prescrição médica, pedido de autorização, "
            "resposta ou negativa da operadora, protocolos e mensagens. "
            "Pretende a análise das medidas cabíveis, sem inventar diagnóstico, urgência, "
            "datas, valores, cobertura contratual ou documentos não informados."
        ),
    )

    fundamentacao = _consumer_scope_block(
        response,
        "BLOCO 4 — Fundamentação preliminar",
        "BLOCO 5 — Pedidos",
    )
    pedidos = _consumer_scope_block(
        response,
        "BLOCO 5 — Pedidos",
        "BLOCO 6 — Provas e requerimentos",
    )
    provas = _consumer_scope_block(
        response,
        "BLOCO 6 — Provas e requerimentos",
        "BLOCO 7 — Fechamento e conferência final",
    )

    assert "contrato" in fundamentacao
    assert "prescrição médica" in fundamentacao
    assert "justificativa de negativa" in fundamentacao
    assert "urgência clínica" not in fundamentacao
    assert "risco de agravamento" not in fundamentacao

    assert "autorização ou cobertura" in pedidos
    assert "procedimento" in pedidos
    assert "tratamento" in pedidos
    assert "exame" not in pedidos
    assert "internação" not in pedidos
    assert "cirurgia" not in pedidos
    assert "com tutela de urgência apenas quando sustentada" not in pedidos
    assert "risco concreto" not in pedidos

    assert "contrato do plano" in provas
    assert "prescrição médica" in provas
    assert "pedido de autorização" in provas
    assert "negativa formal" in provas
    assert "protocolos" in provas
    assert "mensagens" in provas
    assert "exames" not in provas
    assert "prontuário" not in provas
    assert "urgência clínica" not in provas
    assert "risco de agravamento" not in provas


def test_editor_all_blocks_ready_consumer_vehicle_does_not_infer_unsupported_damage_or_urgency():
    response = _consumer_scope_ready_response(
        "TESTE-CONSUMIDOR-VEICULO-001",
        "Revendedora recolheu veículo sem apresentar contrato ou justificativa completa",
        "Ação consumerista para exibição de contrato e restituição de veículo",
        (
            "O consumidor adquiriu um veículo de uma revendedora mediante negociação parcelada. "
            "Possui recibos, comprovantes Pix, mensagens e documentos do veículo, "
            "mas não dispõe de cópia integral do contrato. "
            "Após os pagamentos informados, a revendedora recolheu o veículo alegando bloqueio, "
            "sem apresentar ordem judicial, justificativa documental completa ou prestação de contas. "
            "Pretende a análise da exibição do contrato e dos documentos da negociação, "
            "do esclarecimento do alegado bloqueio e da possível restituição do veículo "
            "ou dos valores comprovados, sem inventar datas, valores, dívida, restrição, "
            "ordem judicial, danos ou urgência não informados."
        ),
    )

    fundamentacao = _consumer_scope_block(
        response,
        "BLOCO 4 — Fundamentação preliminar",
        "BLOCO 5 — Pedidos",
    )
    pedidos = _consumer_scope_block(
        response,
        "BLOCO 5 — Pedidos",
        "BLOCO 6 — Provas e requerimentos",
    )

    assert response["metadata"]["action_specialization_kind"] == (
        "consumer_vehicle_contract_display_restitution"
    )

    assert "aquisição de veículo" in fundamentacao
    assert "exibição de documentos" in fundamentacao
    assert "restituição do veículo" in fundamentacao
    assert "perdas e danos" not in fundamentacao

    assert "exibição do contrato" in pedidos
    assert "restituição do veículo" in pedidos
    assert "restituição dos valores comprovados" in pedidos
    assert "indenização material equivalente" not in pedidos
    assert "perdas e danos" not in pedidos
    assert "tutela de urgência" not in pedidos
    assert "busca do bem" not in pedidos


def test_editor_all_blocks_ready_consumer_general_contract_does_not_infer_service_correction_or_unavailable_delivery_evidence():
    response = _consumer_scope_ready_response(
        "TESTE-CONSUMIDOR-CONTRATO-GERAL-001",
        "Compra não entregue após pagamento e pedido de cancelamento",
        "Ação consumerista por descumprimento de oferta e não entrega",
        (
            "O consumidor realizou uma compra após oferta divulgada pelo fornecedor e efetuou o pagamento. "
            "O pedido não foi entregue, e as tentativas de solução e cancelamento não foram concluídas. "
            "Possui oferta ou publicidade, registro do pedido, comprovante de pagamento, "
            "protocolos de atendimento, mensagens, solicitação de cancelamento e pedido de reembolso. "
            "Pretende a análise do cumprimento da oferta, do cancelamento da contratação "
            "ou da restituição dos valores comprovados, sem inventar datas, valores, danos, "
            "urgência, entrega parcial ou documentos não informados."
        ),
    )

    fundamentacao = _consumer_scope_block(
        response,
        "BLOCO 4 — Fundamentação preliminar",
        "BLOCO 5 — Pedidos",
    )
    pedidos = _consumer_scope_block(
        response,
        "BLOCO 5 — Pedidos",
        "BLOCO 6 — Provas e requerimentos",
    )
    provas = _consumer_scope_block(
        response,
        "BLOCO 6 — Provas e requerimentos",
        "BLOCO 7 — Fechamento e conferência final",
    )

    assert response["metadata"]["action_specialization_kind"] == (
        "consumer_universal_action_scope_claim"
    )

    assert "oferta" in fundamentacao
    assert "comprovantes de pagamento" in fundamentacao
    assert "cancelamento" in fundamentacao
    assert "cumprimento efetivo das obrigações" in fundamentacao
    assert "contrato informado" not in fundamentacao

    assert "cumprimento da oferta" in pedidos
    assert "cancelamento" in pedidos
    assert "restituição dos valores comprovados" in pedidos
    assert "correção do serviço" not in pedidos
    assert "obrigação específica" not in pedidos
    assert "análise de o cumprimento" not in pedidos
    assert "contratos, faturas" not in pedidos
    assert "extratos" not in pedidos
    assert "notas fiscais" not in pedidos
    assert "gravações" not in pedidos
    assert "relatórios" not in pedidos

    assert "oferta" in provas
    assert "publicidade" in provas
    assert "pedido" in provas
    assert "comprovante de pagamento" in provas
    assert "protocolos" in provas
    assert "mensagens" in provas
    assert "solicitação de cancelamento" in provas
    assert "reembolso" in provas
    assert "rastreamento" not in provas
    assert "registros de entrega" not in provas
    assert "juntados contrato," not in provas




def test_editor_all_blocks_ready_consumer_offer_publicity_is_separate_from_general_contract_fallback():
    response = _consumer_scope_ready_response(
        "CONS-OFERTA-PUBLICIDADE-001",
        "Oferta anunciada não cumprida",
        "Ação consumerista por descumprimento de oferta e publicidade",
        (
            "O consumidor relata que o fornecedor divulgou oferta com preço e condições específicas, "
            "mas se recusou a cumprir o conteúdo anunciado. Possui captura da publicidade, "
            "registro da oferta, pedido, comprovante de pagamento, protocolos e mensagens. "
            "Pretende o cumprimento da oferta nos limites do conteúdo comprovado, "
            "sem inventar fatos, datas, valores ou prejuízos não informados."
        ),
    )

    fundamentacao = _consumer_scope_block(
        response,
        "BLOCO 4 — Fundamentação preliminar",
        "BLOCO 5 — Pedidos",
    )
    pedidos = _consumer_scope_block(
        response,
        "BLOCO 5 — Pedidos",
        "BLOCO 6 — Provas e requerimentos",
    )
    provas = _consumer_scope_block(
        response,
        "BLOCO 6 — Provas e requerimentos",
        "BLOCO 7 — Fechamento e conferência final",
    )

    assert response["metadata"]["action_specialization_kind"] == (
        "consumer_universal_action_scope_claim"
    )

    assert "conteúdo anunciado" in fundamentacao
    assert "conduta do fornecedor" in fundamentacao
    assert "captura da publicidade" in fundamentacao
    assert "registro da oferta" in fundamentacao
    assert "pedido" in fundamentacao
    assert "comprovante de pagamento" in fundamentacao
    assert "protocolos" in fundamentacao
    assert "mensagens" in fundamentacao
    assert "não entrega relatada" not in fundamentacao

    assert "cumprimento da oferta nos limites do conteúdo comprovado" in pedidos
    assert "cancelamento da contratação" not in pedidos
    assert "restituição dos valores comprovados" not in pedidos
    assert "correção do serviço" not in pedidos

    assert "captura da publicidade" in provas
    assert "registro da oferta" in provas
    assert "pedido" in provas
    assert "comprovante de pagamento" in provas
    assert "protocolos" in provas
    assert "mensagens" in provas
    assert "rastreamento" not in provas
    assert "registros de entrega" not in provas
    assert "solicitação de cancelamento" not in provas
    assert "pedido de reembolso" not in provas


def test_editor_all_blocks_ready_consumer_offer_publicity_does_not_infer_unreported_documents_or_remedies():
    response = _consumer_scope_ready_response(
        "CONS-OFERTA-PUBLICIDADE-MINIMO-001",
        "Oferta não cumprida",
        "Ação consumerista por descumprimento de oferta",
        (
            "O consumidor relata que o fornecedor divulgou uma oferta e depois se recusou "
            "a cumprir as condições anunciadas. Pretende a análise das medidas juridicamente "
            "cabíveis, sem inventar fatos, documentos, datas, valores ou prejuízos não informados."
        ),
    )

    fundamentacao = _consumer_scope_block(
        response,
        "BLOCO 4 — Fundamentação preliminar",
        "BLOCO 5 — Pedidos",
    )
    pedidos = _consumer_scope_block(
        response,
        "BLOCO 5 — Pedidos",
        "BLOCO 6 — Provas e requerimentos",
    )
    provas = _consumer_scope_block(
        response,
        "BLOCO 6 — Provas e requerimentos",
        "BLOCO 7 — Fechamento e conferência final",
    )

    assert "conteúdo anunciado" in fundamentacao
    assert "conduta do fornecedor" in fundamentacao
    assert "captura da publicidade" not in fundamentacao
    assert "registro da oferta" not in fundamentacao
    assert "comprovante de pagamento" not in fundamentacao
    assert "protocolos" not in fundamentacao
    assert "mensagens" not in fundamentacao

    assert "cumprimento da oferta quando ainda útil e juridicamente cabível" in pedidos
    assert "cancelamento da contratação" not in pedidos
    assert "restituição dos valores comprovados" not in pedidos
    assert "obrigação específica expressamente indicada" not in pedidos

    assert "elementos efetivamente disponíveis sobre a oferta ou publicidade" in provas
    assert "captura da publicidade" not in provas
    assert "registro da oferta" not in provas
    assert "pedido" not in provas
    assert "comprovante de pagamento" not in provas
    assert "protocolos" not in provas
    assert "mensagens" not in provas
    assert "rastreamento" not in provas
    assert "solicitação de cancelamento" not in provas
    assert "pedido de reembolso" not in provas



def test_editor_all_blocks_ready_consumer_cancellation_not_respected_is_separate_from_general_contract_fallback():
    response = _consumer_scope_ready_response(
        "CONS-CANCELAMENTO-001",
        "Cancelamento solicitado e não efetivado",
        "Ação consumerista por cancelamento não respeitado",
        (
            "O consumidor solicitou o cancelamento da contratação, mas o fornecedor não efetivou o pedido "
            "e continuou realizando cobranças. Possui contrato, solicitação de cancelamento, protocolo, "
            "mensagens, faturas posteriores ao pedido e comprovantes dos pagamentos realizados após o cancelamento solicitado. "
            "Pretende a efetivação definitiva do cancelamento, a interrupção das cobranças posteriores "
            "e a análise da restituição dos valores comprovadamente pagos após o pedido, "
            "sem inventar fatos, datas, valores, danos ou documentos não informados."
        ),
    )

    fundamentacao = _consumer_scope_block(
        response,
        "BLOCO 4 — Fundamentação preliminar",
        "BLOCO 5 — Pedidos",
    )
    pedidos = _consumer_scope_block(
        response,
        "BLOCO 5 — Pedidos",
        "BLOCO 6 — Provas e requerimentos",
    )
    provas = _consumer_scope_block(
        response,
        "BLOCO 6 — Provas e requerimentos",
        "BLOCO 7 — Fechamento e conferência final",
    )

    assert response["metadata"]["action_specialization_kind"] == (
        "consumer_universal_action_scope_claim"
    )

    assert "pedido de cancelamento não efetivado" in fundamentacao
    assert "contrato" in fundamentacao
    assert "solicitação de cancelamento" in fundamentacao
    assert "protocolo" in fundamentacao
    assert "mensagens" in fundamentacao
    assert "faturas posteriores" in fundamentacao
    assert "comprovantes dos pagamentos realizados após" in fundamentacao
    assert "não entrega relatada" not in fundamentacao
    assert "conteúdo anunciado" not in fundamentacao

    assert "efetivação definitiva do cancelamento" in pedidos
    assert "interrupção das cobranças posteriores" in pedidos
    assert "restituição dos valores comprovadamente pagos após o pedido de cancelamento" in pedidos
    assert "cumprimento da oferta" not in pedidos
    assert "medida contratual compatível" not in pedidos

    assert "contrato" in provas
    assert "solicitação de cancelamento" in provas
    assert "protocolo" in provas
    assert "mensagens" in provas
    assert "faturas posteriores ao pedido" in provas
    assert "comprovantes dos pagamentos realizados após o pedido" in provas
    assert "rastreamento" not in provas
    assert "registros de entrega" not in provas
    assert "publicidade" not in provas


def test_editor_all_blocks_ready_consumer_cancellation_not_respected_does_not_infer_unreported_charges_payments_or_documents():
    response = _consumer_scope_ready_response(
        "CONS-CANCELAMENTO-MINIMO-001",
        "Cancelamento não respeitado",
        "Ação consumerista por cancelamento não respeitado",
        (
            "O consumidor relata que solicitou o cancelamento da contratação, mas o fornecedor não efetivou o pedido. "
            "Pretende a análise das medidas juridicamente cabíveis, sem inventar fatos, documentos, "
            "datas, valores, cobranças posteriores, pagamentos ou prejuízos não informados."
        ),
    )

    fundamentacao = _consumer_scope_block(
        response,
        "BLOCO 4 — Fundamentação preliminar",
        "BLOCO 5 — Pedidos",
    )
    pedidos = _consumer_scope_block(
        response,
        "BLOCO 5 — Pedidos",
        "BLOCO 6 — Provas e requerimentos",
    )
    provas = _consumer_scope_block(
        response,
        "BLOCO 6 — Provas e requerimentos",
        "BLOCO 7 — Fechamento e conferência final",
    )

    assert "pedido de cancelamento não efetivado" in fundamentacao
    assert "contrato" not in fundamentacao
    assert "protocolo de atendimento" not in fundamentacao
    assert "mensagens" not in fundamentacao
    assert "faturas posteriores" not in fundamentacao
    assert "comprovantes dos pagamentos realizados após" not in fundamentacao

    assert "efetivação definitiva do cancelamento" in pedidos
    assert "interrupção das cobranças posteriores" not in pedidos
    assert "restituição dos valores comprovadamente pagos após" not in pedidos
    assert "cumprimento da oferta" not in pedidos
    assert "obrigação específica expressamente indicada" not in pedidos

    assert "elementos efetivamente disponíveis sobre o pedido de cancelamento não efetivado" in provas
    assert "contrato" not in provas
    assert "protocolo" not in provas
    assert "mensagens" not in provas
    assert "faturas posteriores ao pedido" not in provas
    assert "comprovantes dos pagamentos realizados após o pedido" not in provas
    assert "rastreamento" not in provas
    assert "pedido de reembolso" not in provas



def test_editor_all_blocks_ready_consumer_delivery_delay_is_separate_from_general_contract_fallback():
    response = _consumer_scope_ready_response(
        "CONS-ENTREGA-ATRASADA-001",
        "Prazo vencido e pedido não entregue",
        "Ação consumerista por atraso ou falha de entrega",
        (
            "O consumidor realizou uma compra com prazo de entrega informado no pedido, "
            "mas o prazo venceu e a entrega não foi concluída. Possui registro do pedido, "
            "comprovante de pagamento, comprovante do prazo de entrega, código de rastreio, "
            "protocolos e mensagens. Pretende a entrega do pedido quando ainda útil e "
            "juridicamente cabível, sem inventar datas, valores, entrega parcial, tentativa "
            "de entrega, cancelamento, reembolso, danos ou documentos não informados."
        ),
    )

    fundamentacao = _consumer_scope_block(
        response,
        "BLOCO 4 — Fundamentação preliminar",
        "BLOCO 5 — Pedidos",
    )
    pedidos = _consumer_scope_block(
        response,
        "BLOCO 5 — Pedidos",
        "BLOCO 6 — Provas e requerimentos",
    )
    provas = _consumer_scope_block(
        response,
        "BLOCO 6 — Provas e requerimentos",
        "BLOCO 7 — Fechamento e conferência final",
    )

    assert response["metadata"]["action_specialization_kind"] == (
        "consumer_universal_action_scope_claim"
    )

    assert "atraso ou falha de entrega relatada" in fundamentacao
    assert "registro do pedido" in fundamentacao
    assert "comprovante de pagamento" in fundamentacao
    assert "prazo de entrega informado" in fundamentacao
    assert "código de rastreio" in fundamentacao
    assert "protocolos" in fundamentacao
    assert "mensagens" in fundamentacao
    assert "solicitação de cancelamento" not in fundamentacao
    assert "conteúdo anunciado" not in fundamentacao

    assert "entrega do pedido quando ainda útil e juridicamente cabível" in pedidos
    assert "cancelamento da contratação" not in pedidos
    assert "restituição dos valores" not in pedidos
    assert "cumprimento da oferta" not in pedidos
    assert "medida contratual compatível" not in pedidos

    assert "registro do pedido" in provas
    assert "comprovante de pagamento" in provas
    assert "comprovante do prazo de entrega" in provas
    assert "código de rastreio" in provas
    assert "protocolos" in provas
    assert "mensagens" in provas
    assert "registros de tentativa de entrega" not in provas
    assert "registros de entrega parcial" not in provas
    assert "solicitação de cancelamento" not in provas
    assert "pedido de reembolso" not in provas
    assert "publicidade" not in provas


def test_editor_all_blocks_ready_consumer_delivery_delay_does_not_infer_unreported_documents_or_remedies():
    response = _consumer_scope_ready_response(
        "CONS-ENTREGA-ATRASADA-MINIMO-001",
        "Pedido não entregue no prazo",
        "Ação consumerista por atraso de entrega",
        (
            "O consumidor relata que o prazo de entrega venceu e o pedido ainda não foi entregue. "
            "Pretende a análise das medidas juridicamente cabíveis, sem inventar fatos, documentos, "
            "datas, valores ou prejuízos não informados."
        ),
    )

    fundamentacao = _consumer_scope_block(
        response,
        "BLOCO 4 — Fundamentação preliminar",
        "BLOCO 5 — Pedidos",
    )
    pedidos = _consumer_scope_block(
        response,
        "BLOCO 5 — Pedidos",
        "BLOCO 6 — Provas e requerimentos",
    )
    provas = _consumer_scope_block(
        response,
        "BLOCO 6 — Provas e requerimentos",
        "BLOCO 7 — Fechamento e conferência final",
    )

    assert "atraso ou falha de entrega relatada" in fundamentacao
    assert "registro do pedido" not in fundamentacao
    assert "comprovante de pagamento" not in fundamentacao
    assert "prazo de entrega informado" not in fundamentacao
    assert "código de rastreio" not in fundamentacao
    assert "protocolos de atendimento" not in fundamentacao
    assert "mensagens disponíveis" not in fundamentacao

    assert "entrega do pedido quando ainda útil e juridicamente cabível" in pedidos
    assert "cancelamento da contratação" not in pedidos
    assert "restituição dos valores" not in pedidos
    assert "cumprimento da oferta" not in pedidos
    assert "obrigação específica expressamente indicada" not in pedidos

    assert "elementos efetivamente disponíveis sobre o atraso ou a falha de entrega" in provas
    assert "registro do pedido" not in provas
    assert "comprovante de pagamento" not in provas
    assert "comprovante do prazo de entrega" not in provas
    assert "código de rastreio" not in provas
    assert "protocolos" not in provas
    assert "mensagens" not in provas
    assert "registros de tentativa de entrega" not in provas
    assert "registros de entrega parcial" not in provas
    assert "solicitação de cancelamento" not in provas
    assert "pedido de reembolso" not in provas


def test_editor_all_blocks_ready_consumer_warranty_failure_is_separate_from_defective_product_scope():
    response = _consumer_scope_ready_response(
        "CONS-GARANTIA-FALHA-001",
        "Garantia acionada e defeito não solucionado",
        "Ação consumerista por falha de garantia",
        (
            "A consumidora comprou um eletrodoméstico que apresentou defeito durante a garantia. "
            "Acionou a garantia e a assistência técnica, mas o defeito persistiu após a tentativa "
            "de reparo. Possui nota fiscal, certificado de garantia, ordens de serviço, protocolos, "
            "mensagens, fotografias e vídeos. Pretende o cumprimento adequado da garantia, sem "
            "inventar laudo técnico, nova tentativa de reparo, substituição do produto, restituição "
            "do preço, abatimento proporcional, danos, urgência, datas, valores ou documentos "
            "não informados."
        ),
    )

    fundamentacao = _consumer_scope_block(
        response,
        "BLOCO 4 — Fundamentação preliminar",
        "BLOCO 5 — Pedidos",
    )
    pedidos = _consumer_scope_block(
        response,
        "BLOCO 5 — Pedidos",
        "BLOCO 6 — Provas e requerimentos",
    )
    provas = _consumer_scope_block(
        response,
        "BLOCO 6 — Provas e requerimentos",
        "BLOCO 7 — Fechamento e conferência final",
    )

    assert response["metadata"]["action_specialization_kind"] == (
        "consumer_universal_action_scope_claim"
    )

    assert "falha de garantia relatada" in fundamentacao
    assert "nota fiscal" in fundamentacao
    assert "certificado de garantia" in fundamentacao
    assert "ordens de serviço" in fundamentacao
    assert "protocolos" in fundamentacao
    assert "mensagens" in fundamentacao
    assert "fotografias" in fundamentacao
    assert "vídeos" in fundamentacao
    assert "tentativa de reparo" in fundamentacao
    assert "oferta" not in fundamentacao
    assert "finalidade anunciada" not in fundamentacao

    assert "cumprimento adequado da garantia" in pedidos
    assert "substituição do produto" not in pedidos
    assert "restituição do preço" not in pedidos
    assert "abatimento proporcional" not in pedidos
    assert "medida contratual compatível" not in pedidos

    assert "nota fiscal" in provas
    assert "certificado de garantia" in provas
    assert "ordens de serviço" in provas
    assert "protocolos" in provas
    assert "mensagens" in provas
    assert "fotografias" in provas
    assert "vídeos" in provas
    assert "registros da tentativa de reparo" in provas
    assert "laudo técnico" not in provas
    assert "manual" not in provas
    assert "oferta" not in provas
    assert "próprio produto" not in provas


def test_editor_all_blocks_ready_consumer_warranty_failure_does_not_infer_unreported_documents_or_remedies():
    response = _consumer_scope_ready_response(
        "CONS-GARANTIA-FALHA-MINIMO-001",
        "Falha não solucionada durante a garantia",
        "Ação consumerista por falha de garantia",
        (
            "O consumidor relata que o produto apresentou defeito durante a garantia e que o "
            "fornecedor não solucionou a falha. Pretende a análise das medidas juridicamente "
            "cabíveis, sem inventar nota fiscal, certificado de garantia, ordem de serviço, "
            "assistência técnica, tentativa de reparo, protocolos, mensagens, fotografias, vídeos, "
            "laudo técnico, substituição, restituição, abatimento, danos, datas ou valores."
        ),
    )

    fundamentacao = _consumer_scope_block(
        response,
        "BLOCO 4 — Fundamentação preliminar",
        "BLOCO 5 — Pedidos",
    )
    pedidos = _consumer_scope_block(
        response,
        "BLOCO 5 — Pedidos",
        "BLOCO 6 — Provas e requerimentos",
    )
    provas = _consumer_scope_block(
        response,
        "BLOCO 6 — Provas e requerimentos",
        "BLOCO 7 — Fechamento e conferência final",
    )

    assert "falha de garantia relatada" in fundamentacao
    assert "nota fiscal" not in fundamentacao
    assert "certificado de garantia" not in fundamentacao
    assert "ordens de serviço" not in fundamentacao
    assert "assistência técnica" not in fundamentacao
    assert "tentativa de reparo" not in fundamentacao
    assert "protocolos" not in fundamentacao
    assert "mensagens" not in fundamentacao
    assert "fotografias" not in fundamentacao
    assert "vídeos" not in fundamentacao

    assert "cumprimento adequado da garantia" in pedidos
    assert "substituição do produto" not in pedidos
    assert "restituição do preço" not in pedidos
    assert "abatimento proporcional" not in pedidos
    assert "medida contratual compatível" not in pedidos

    assert "elementos efetivamente disponíveis sobre a falha de garantia" in provas
    assert "nota fiscal" not in provas
    assert "certificado de garantia" not in provas
    assert "ordens de serviço" not in provas
    assert "assistência técnica" not in provas
    assert "registros da tentativa de reparo" not in provas
    assert "protocolos" not in provas
    assert "mensagens" not in provas
    assert "fotografias" not in provas
    assert "vídeos" not in provas
    assert "laudo técnico" not in provas


def test_editor_all_blocks_ready_consumer_telecom_is_separate_from_defective_service():
    response = _consumer_scope_ready_response(
        "CONS-TELECOM-001",
        "Falha persistente em serviço de telefonia e internet",
        "Ação consumerista por falha em serviço de telecomunicações",
        (
            "A consumidora relata falha na prestação do serviço de telefonia e internet banda larga, "
            "com quedas de sinal e períodos de internet indisponível. Possui contrato do plano, "
            "faturas, protocolos, mensagens, testes de velocidade e registros de suporte técnico. "
            "Também solicitou portabilidade. Pretende a regularização adequada do serviço e a análise "
            "do pedido de portabilidade, sem inventar ordem de serviço, comprovante de pagamento, "
            "cancelamento, restituição, danos, urgência, datas, valores ou outros documentos."
        ),
    )

    fundamentacao = _consumer_scope_block(
        response,
        "BLOCO 4 — Fundamentação preliminar",
        "BLOCO 5 — Pedidos",
    )
    pedidos = _consumer_scope_block(
        response,
        "BLOCO 5 — Pedidos",
        "BLOCO 6 — Provas e requerimentos",
    )
    provas = _consumer_scope_block(
        response,
        "BLOCO 6 — Provas e requerimentos",
        "BLOCO 7 — Fechamento e conferência final",
    )

    assert response["metadata"]["action_specialization_kind"] == (
        "consumer_universal_action_scope_claim"
    )

    assert "falha no serviço de telecomunicações relatada" in fundamentacao
    assert "contrato ou plano informado" in fundamentacao
    assert "faturas informadas" in fundamentacao
    assert "protocolos de atendimento" in fundamentacao
    assert "mensagens disponíveis" in fundamentacao
    assert "registros da falha ou interrupção do serviço" in fundamentacao
    assert "testes ou medições de velocidade" in fundamentacao
    assert "registros de suporte ou atendimento técnico" in fundamentacao
    assert "pedido de portabilidade informado" in fundamentacao
    assert "resultado prometido" not in fundamentacao
    assert "tentativas de correção" not in fundamentacao

    assert "regularização adequada do serviço de telecomunicações" in pedidos
    assert "pedido de portabilidade expressamente informado" in pedidos
    assert "refazimento adequado do serviço" not in pedidos
    assert "restituição dos valores incompatíveis" not in pedidos

    assert "contrato ou registro do plano contratado" in provas
    assert "faturas" in provas
    assert "protocolos" in provas
    assert "mensagens" in provas
    assert "registros da falha ou interrupção do serviço" in provas
    assert "testes ou medições de velocidade" in provas
    assert "registros de suporte ou atendimento técnico" in provas
    assert "registro do pedido de portabilidade" in provas
    assert "ordem de serviço" not in provas
    assert "comprovantes de pagamento" not in provas
    assert "registros do resultado prometido" not in provas
    assert "evidências da execução" not in provas
    assert "tentativas de correção" not in provas


def test_editor_all_blocks_ready_consumer_telecom_does_not_infer_unreported_documents_or_remedies():
    response = _consumer_scope_ready_response(
        "CONS-TELECOM-MINIMO-001",
        "Falha em serviço de telefonia",
        "Ação consumerista por falha em serviço de telecomunicações",
        (
            "O consumidor relata falha na prestação do serviço de telefonia e informa que a prestadora "
            "não solucionou o problema. Pretende a análise das medidas juridicamente cabíveis, sem "
            "inventar contrato, plano, faturas, protocolos, mensagens, registros de interrupção, "
            "testes de velocidade, suporte técnico, portabilidade, cancelamento, restituição, danos, "
            "urgência, datas ou valores."
        ),
    )

    fundamentacao = _consumer_scope_block(
        response,
        "BLOCO 4 — Fundamentação preliminar",
        "BLOCO 5 — Pedidos",
    )
    pedidos = _consumer_scope_block(
        response,
        "BLOCO 5 — Pedidos",
        "BLOCO 6 — Provas e requerimentos",
    )
    provas = _consumer_scope_block(
        response,
        "BLOCO 6 — Provas e requerimentos",
        "BLOCO 7 — Fechamento e conferência final",
    )

    assert "falha no serviço de telecomunicações relatada" in fundamentacao
    assert "contrato ou plano informado" not in fundamentacao
    assert "faturas informadas" not in fundamentacao
    assert "protocolos de atendimento" not in fundamentacao
    assert "mensagens disponíveis" not in fundamentacao
    assert "registros da falha ou interrupção do serviço" not in fundamentacao
    assert "testes ou medições de velocidade" not in fundamentacao
    assert "registros de suporte ou atendimento técnico" not in fundamentacao
    assert "pedido de portabilidade informado" not in fundamentacao
    assert "resultado prometido" not in fundamentacao
    assert "tentativas de correção" not in fundamentacao

    assert "regularização adequada do serviço de telecomunicações" in pedidos
    assert "pedido de portabilidade expressamente informado" not in pedidos
    assert "refazimento adequado do serviço" not in pedidos
    assert "restituição dos valores incompatíveis" not in pedidos

    assert (
        "elementos efetivamente disponíveis sobre a falha no serviço de telecomunicações"
        in provas
    )
    assert "contrato ou registro do plano contratado" not in provas
    assert "faturas" not in provas
    assert "protocolos" not in provas
    assert "mensagens" not in provas
    assert "registros da falha ou interrupção do serviço" not in provas
    assert "testes ou medições de velocidade" not in provas
    assert "registros de suporte ou atendimento técnico" not in provas
    assert "registro do pedido de portabilidade" not in provas
    assert "ordem de serviço" not in provas
    assert "comprovantes de pagamento" not in provas


def test_editor_all_blocks_ready_consumer_service_not_rendered_is_separate_from_defective_service():
    response = _consumer_scope_ready_response(
        "CONS-SERVICO-NAO-PRESTADO-001",
        "Serviço contratado e não prestado",
        "Ação consumerista por serviço não prestado",
        (
            "O consumidor contratou um serviço, efetuou o pagamento e o fornecedor não iniciou nem executou a prestação. "
            "Possui contrato, oferta, comprovante de pagamento, protocolos e mensagens cobrando o início do serviço. "
            "Pretende o cumprimento da prestação ou, se juridicamente cabível, a resolução da contratação "
            "com restituição do valor pago."
        ),
    )

    fundamentacao = _consumer_scope_block(
        response,
        "BLOCO 4 — Fundamentação preliminar",
        "BLOCO 5 — Pedidos",
    )
    pedidos = _consumer_scope_block(
        response,
        "BLOCO 5 — Pedidos",
        "BLOCO 6 — Provas e requerimentos",
    )
    provas = _consumer_scope_block(
        response,
        "BLOCO 6 — Provas e requerimentos",
        "BLOCO 7 — Fechamento e conferência final",
    )

    assert response["metadata"]["action_specialization_kind"] == (
        "consumer_universal_action_scope_claim"
    )

    assert "ausência de execução do serviço" in fundamentacao
    assert "extensão da falha" not in fundamentacao
    assert "tentativas de correção" not in fundamentacao

    assert "prestação do serviço" in pedidos
    assert "resolução da contratação" in pedidos
    assert "restituição dos valores comprovadamente pagos" in pedidos
    assert "refazimento adequado do serviço" not in pedidos
    assert "correção da falha" not in pedidos
    assert "serviço efetivamente prestado" not in pedidos

    assert "contrato" in provas
    assert "oferta" in provas
    assert "comprovante de pagamento" in provas
    assert "protocolos" in provas
    assert "mensagens" in provas
    assert "evidências da execução" not in provas
    assert "tentativas de correção" not in provas


def test_editor_all_blocks_ready_consumer_service_not_rendered_does_not_infer_unreported_documents_or_execution():
    response = _consumer_scope_ready_response(
        "CONS-SERVICO-NAO-PRESTADO-MINIMO-001",
        "Serviço não prestado",
        "Ação consumerista por serviço não prestado",
        (
            "O consumidor relata que o serviço contratado não foi prestado. "
            "Pretende a análise das medidas juridicamente cabíveis, sem inventar fatos, "
            "documentos, datas, valores ou prejuízos não informados."
        ),
    )

    fundamentacao = _consumer_scope_block(
        response,
        "BLOCO 4 — Fundamentação preliminar",
        "BLOCO 5 — Pedidos",
    )
    pedidos = _consumer_scope_block(
        response,
        "BLOCO 5 — Pedidos",
        "BLOCO 6 — Provas e requerimentos",
    )
    provas = _consumer_scope_block(
        response,
        "BLOCO 6 — Provas e requerimentos",
        "BLOCO 7 — Fechamento e conferência final",
    )

    assert "ausência de execução do serviço" in fundamentacao
    assert "extensão da falha" not in fundamentacao
    assert "tentativas de correção" not in fundamentacao

    assert "refazimento adequado do serviço" not in pedidos
    assert "correção da falha" not in pedidos
    assert "serviço efetivamente prestado" not in pedidos
    assert "restituição dos valores comprovadamente pagos" not in pedidos

    assert "contrato, oferta" not in provas
    assert "ordem de serviço" not in provas
    assert "comprovantes de pagamento" not in provas
    assert "protocolos" not in provas
    assert "mensagens" not in provas
    assert "evidências da execução" not in provas
    assert "tentativas de correção" not in provas
