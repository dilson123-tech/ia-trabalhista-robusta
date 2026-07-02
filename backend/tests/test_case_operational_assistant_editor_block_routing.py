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

