"""Regressões F1/F2 (IA-TRAB-001): sem contaminação de fatos entre casos do mesmo tenant.

F1: fallback genérico de audiência estratégica não pode injetar nomes/fatos fixos
    nem casar por substring (ex.: "praticamente").
F2: guias do assistente operacional não podem injetar fatos, valores, datas ou
    veículos fixos, nem classificar por substring (ex.: "motorista" -> "moto").
"""
from types import SimpleNamespace

from app.api.v1.routes.editable_documents import _build_audiencia_person_specific_questions
from app.services.case_operational_assistant import (
    _attachments_guide_text,
    _checklist_guide_text,
    _dealer_case_flags,
    _formal_block_document_status,
    _is_vehicle_dealer_pix_context,
    _proof_documents_status,
    _timeline_guide_text,
)

FIXED_FACTS = [
    "pratic sider",
    "edson",
    "dilson",
    "rosangela",
    "carreta",
    "locação",
]

ASSISTANT_FIXED_FACTS = [
    "scenic",
    "cbx",
    "4.000,00",
    "11.000,00",
    "1.180,00",
    "40.120,00",
    "34 parcelas",
    "28/05",
    "quintino",
]


def _case(title="", description="", case_number="CASO-X"):
    return SimpleNamespace(
        id=1,
        case_number=case_number,
        title=title,
        description=description,
        legal_area="",
        action_type="",
    )


# ---------------------------------------------------------------- F1


def test_f1_praticamente_does_not_trigger_pratic_sider_block():
    content = _build_audiencia_person_specific_questions(
        "O cliente praticamente não recebeu resposta e praticou atos de cobrança.",
        area="civel",
    )
    lowered = content.lower()
    for fact in FIXED_FACTS:
        assert fact not in lowered
    assert "Nenhuma pessoa específica foi identificada" in content


def test_f1_unrelated_cases_same_tenant_do_not_receive_fixed_names_or_facts():
    contexts = [
        "Caso A: Maria Souza contra Banco Alfa por cobrança indevida. Praticamente sem provas.",
        "Caso B: João Lima, motorista, acidente de trânsito em 2023 com colisão traseira.",
        "",
        None,
    ]
    for ctx in contexts:
        lowered = _build_audiencia_person_specific_questions(ctx, area="civel").lower()
        for fact in FIXED_FACTS:
            assert fact not in lowered, (fact, ctx)


def test_f1_name_without_carreta_context_gets_no_carreta_facts_and_flags_gap():
    content = _build_audiencia_person_specific_questions(
        "Processo envolvendo Edson Estevão e Dilson Pereira, tema contratual diverso.",
        area="civel",
    )
    lowered = content.lower()
    assert "edson estevão:" in lowered
    # papel de parte ré não é afirmado sem sustentação no contexto
    assert "dilson pereira:" in lowered
    assert "parte ré" not in lowered
    assert "carreta" not in lowered
    assert "locação" not in lowered
    assert "desaparecimento" not in lowered
    assert "lacuna" in lowered


def test_f1_partial_names_do_not_introduce_full_names_roles_or_facts():
    content = _build_audiencia_person_specific_questions(
        "Cliente conversou com Edson, Dilson e Rosangela sobre o contrato de prestação de serviço.",
        area="civel",
    )
    lowered = content.lower()
    for forbidden in ("estevão", "pereira", "siqueira", "de lourdes", "parte ré", "carreta", "locação", "pratic sider"):
        assert forbidden not in lowered, forbidden
    assert "nome parcial" in lowered
    assert "identidade a confirmar" in lowered


def test_f1_incidental_carreta_mention_does_not_introduce_unsupported_facts():
    # carreta citada de passagem, sem locação, seguro, posse/condução ou valores
    content = _build_audiencia_person_specific_questions(
        "PRATIC SIDER e Edson Estevão discutem cláusula contratual; uma carreta foi citada de passagem.",
        area="civel",
    )
    lowered = content.lower()
    assert "locação" not in lowered
    assert "seguro" not in lowered
    assert "apólice" not in lowered
    assert "posse" not in lowered
    assert "parte autora" not in lowered
    assert "valor" not in lowered


def test_f1_carreta_case_keeps_specialised_flow_and_does_not_leak_to_next_case():
    carreta_ctx = (
        "Processo PRATIC SIDER contra Dilson Pereira envolvendo Edson Estevão e Rosangela de Lourdes Siqueira, "
        "locação de carreta com seguro e discussão sobre quem tinha a posse."
    )
    first = _build_audiencia_person_specific_questions(carreta_ctx, area="civel")
    assert "Representante da PRATIC SIDER / parte autora:" in first
    assert "Dilson Pereira / parte ré:" in first
    assert "Rosangela de Lourdes Siqueira:" in first
    assert "carreta" in first.lower()
    assert "seguro da carreta" in first.lower()

    other = _build_audiencia_person_specific_questions(
        "Caso distinto: Ana Prado e Loja Beta discutem troca de produto.", area="civel"
    )
    for fact in FIXED_FACTS:
        assert fact not in other.lower()

    # repetir o primeiro caso depois do segundo: resultado estável (sem estado compartilhado)
    assert _build_audiencia_person_specific_questions(carreta_ctx, area="civel") == first


# ---------------------------------------------------------------- F2


def test_f2_motorista_is_not_classified_as_vehicle_dealer_context():
    blob = (
        "motorista profissional relata pagamento via pix de parcelas; "
        "a automóveis ltda alega entrada e bloqueio do cadastro"
    )
    # "moto" não pode casar dentro de "motorista"; sem veículo real, não é caso de revendedora
    assert _is_vehicle_dealer_pix_context(blob) is False


def test_f2_real_dealer_case_still_classified():
    blob = "comprou o veículo da revendedora, pagou parcelas via pix e houve recolhimento"
    assert _is_vehicle_dealer_pix_context(blob) is True


def test_f2_guides_for_motorista_case_have_no_fixed_facts():
    case = _case(
        title="Motorista de aplicativo - restrição de cadastro",
        description="O motorista relata bloqueio do cadastro e pagamento de entrada de curso via pix.",
    )
    for guide in (_timeline_guide_text, _checklist_guide_text, _attachments_guide_text):
        lowered = guide(case, {}, "").lower()
        for fact in ASSISTANT_FIXED_FACTS:
            assert fact not in lowered, (guide.__name__, fact)


def test_f2_two_dealer_cases_same_tenant_keep_own_values_without_cross_contamination():
    case_a = _case(
        title="Compra de veículo",
        description=(
            "Cliente comprou veículo da revendedora Garagem Alfa e pagou 12 parcelas de R$ 900,00 via Pix, "
            "totalizando R$ 10.800,00. Revendedora recolheu o veículo."
        ),
    )
    case_b = _case(
        title="Compra de moto",
        description=(
            "Cliente comprou moto da revendedora Garagem Beta e pagou 8 parcelas de R$ 500,00 via Pix. "
            "Houve bloqueio alegado."
        ),
    )
    case_c = _case(
        title="Compra de carro",
        description="Cliente comprou carro de garagem e pagou entrada via Pix; sem outros dados.",
    )

    for guide in (_timeline_guide_text, _checklist_guide_text, _attachments_guide_text):
        out_a = guide(case_a, {}, "").lower()
        out_b = guide(case_b, {}, "").lower()
        out_c = guide(case_c, {}, "").lower()

        for out in (out_a, out_b, out_c):
            for fact in ASSISTANT_FIXED_FACTS:
                assert fact not in out, (guide.__name__, fact)

        # valores só do próprio caso
        assert "8 parcelas" not in out_a and "500,00" not in out_a
        assert "12 parcelas" not in out_b and "900,00" not in out_b and "10.800,00" not in out_b
        for token in ("12 parcelas", "8 parcelas", "900,00", "500,00", "10.800,00"):
            assert token not in out_c, (guide.__name__, token)

    assert "12 parcelas de r$ 900,00" in _checklist_guide_text(case_a, {}, "").lower()
    assert "10.800,00" in _checklist_guide_text(case_a, {}, "").lower()
    assert "8 parcelas de r$ 500,00" in _checklist_guide_text(case_b, {}, "").lower()
    # sem dados no contexto: lacuna explícita
    assert "a confirmar" in _checklist_guide_text(case_c, {}, "").lower()


def test_f2_dealer_case_without_lost_contract_or_retention_omits_those_facts():
    case = _case(
        title="Compra de veículo",
        description="Cliente comprou veículo da revendedora e pagou parcelas via Pix. Pede cópia do contrato.",
    )
    out = _timeline_guide_text(case, {}, "").lower()
    assert "perda da via física" not in out
    assert "retomada ou recolhimento" not in out


def test_f2_patio_guide_has_no_fixed_date_and_acordo_only_when_in_context():
    without = _timeline_guide_text(_case(description="Carreta deixada no pátio e não localizada."), {}, "").lower()
    assert "28/05" not in without
    assert "acordo anterior" not in without

    with_acordo = _timeline_guide_text(
        _case(description="Carreta no pátio; houve acordo em audiência anterior."), {}, ""
    ).lower()
    assert "28/05" not in with_acordo
    assert "acordo anterior" in with_acordo


def test_f2_classifier_is_restricted_to_real_vehicle_purchase_from_dealer():
    # placa/chassi e "entrada"/"R$" isolados, sem compra de veículo em revendedora
    assert _is_vehicle_dealer_pix_context("placa do carro; garagem da casa; pagou entrada r$ 50,00") is False
    # sem compra
    assert _is_vehicle_dealer_pix_context("carro na garagem, pagamento via pix de parcelas") is False
    # sem revendedora/garagem
    assert _is_vehicle_dealer_pix_context("comprou carro de particular e pagou via pix") is False


def test_f2_each_claim_requires_current_case_evidence():
    case = _case(
        title="Compra de veículo",
        description="Cliente comprou veículo da revendedora e pagou parcelas via Pix.",
    )
    for guide in (_timeline_guide_text, _checklist_guide_text, _attachments_guide_text):
        out = guide(case, {}, "").lower()
        assert "perdeu" not in out, guide.__name__
        assert "bloqueio" not in out, guide.__name__
        assert "recolh" not in out and "retomada" not in out, guide.__name__
        assert "bens entregues" not in out and "entrega de bens" not in out, guide.__name__
        assert "detran" not in out, guide.__name__


def test_f2_attachments_distinguish_available_from_requested():
    without_proofs = _attachments_guide_text(
        _case(description="Cliente comprou veículo da revendedora e pagou parcelas via Pix."), {}, ""
    )
    assert "Anexo disponível" not in without_proofs
    assert "solicitar ao cliente" in without_proofs.lower()

    with_proofs = _attachments_guide_text(
        _case(description="Cliente comprou veículo da revendedora, pagou parcelas via Pix e tem os comprovantes."),
        {},
        "",
    )
    assert "Anexo disponível 1" in with_proofs


# ------------------------------------------------ F2 (IA-TRAB-003-R1)


def test_f2_disconnected_terms_in_same_context_do_not_trigger_dealer_flow():
    # veículo, compra, revendedora, Pix e recolhimento presentes, mas em relações factuais distintas
    blobs = (
        "Cliente comprou um carro de um particular. A revendedora de celulares cobra parcelas via Pix em outro contrato.",
        "Recolhimento do carro na garagem do prédio. Cliente comprou geladeira na revendedora de eletrodomésticos e pagou via Pix.",
        "Cliente comprou um carro de particular e visitou uma revendedora; pagou parcelas via Pix de outro contrato.",
    )
    for blob in blobs:
        assert _is_vehicle_dealer_pix_context(blob) is False, blob

    case = _case(title="Contrato de telefonia", description=blobs[0])
    for guide in (_timeline_guide_text, _checklist_guide_text, _attachments_guide_text):
        out = guide(case, {}, "").lower()
        assert "revendedora" not in out, guide.__name__
        assert "anexo disponível" not in out, guide.__name__


def test_f2_legitimate_vehicle_purchase_from_dealer_is_still_classified():
    for blob in (
        "Cliente relata que adquiriu veículo junto à revendedora Alfa Comércio de Automóveis Ltda, mediante nota promissória.",
        "Cliente adquiriu veículo junto à revendedora. A revendedora recolheu o veículo alegando bloqueio.",
        "Veículo comprado na garagem Beta; o cliente pagou as parcelas do carro via Pix.",
    ):
        assert _is_vehicle_dealer_pix_context(blob) is True, blob


def test_f2_requested_pix_proofs_are_not_reported_as_available():
    case = _case(
        description="Cliente comprou veículo da revendedora e pagou parcelas via Pix. Solicitar comprovantes Pix ao cliente."
    )
    attachments = _attachments_guide_text(case, {}, "")
    assert "Anexo disponível" not in attachments
    assert "Solicitado:" in attachments
    checklist = _checklist_guide_text(case, {}, "")
    assert "informa possuir" not in checklist.lower()
    assert "Solicitado:" in checklist

    pending = _attachments_guide_text(
        _case(description="Cliente comprou veículo da revendedora e pagou parcelas via Pix, mas não possui os comprovantes."),
        {},
        "",
    )
    assert "Anexo disponível" not in pending
    assert "Pendente:" in pending


def test_f2_explicitly_available_pix_proofs_are_reported_as_available():
    case = _case(
        description="Cliente comprou veículo da revendedora e pagou parcelas via Pix. O cliente possui comprovantes Pix dos pagamentos."
    )
    attachments = _attachments_guide_text(case, {}, "")
    assert "Anexo disponível 1" in attachments
    assert "Comprovantes Pix das parcelas pagas" in attachments
    assert "Disponível: cliente informa possuir" in _checklist_guide_text(case, {}, "")


def test_f2_unknown_document_availability_is_flagged_as_unknown():
    case = _case(description="Cliente comprou veículo da revendedora e pagou parcelas via Pix.")
    attachments = _attachments_guide_text(case, {}, "")
    assert "Anexo disponível" not in attachments
    assert "Disponibilidade desconhecida:" in attachments
    checklist = _checklist_guide_text(case, {}, "")
    assert "Disponibilidade desconhecida:" in checklist
    assert "informa possuir" not in checklist.lower()


def test_f2_block_without_formal_document_info_does_not_assert_absence():
    case = _case(
        description="Cliente comprou veículo da revendedora e pagou parcelas via Pix. A revendedora recolheu o veículo alegando bloqueio."
    )
    for guide in (_timeline_guide_text, _checklist_guide_text, _attachments_guide_text):
        out = guide(case, {}, "").lower()
        assert "ausência de documentação clara" not in out, guide.__name__
        assert "não consta documento" not in out, guide.__name__
        assert "não ter recebido documento formal" not in out, guide.__name__
    timeline = _timeline_guide_text(case, {}, "").lower()
    assert "documentação do bloqueio alegado a confirmar" in timeline
    assert "não informa se existe ou não documento formal" in timeline


def test_f2_block_with_explicit_absence_of_formal_document_is_reported():
    case = _case(
        description=(
            "Cliente comprou veículo da revendedora e pagou parcelas via Pix. A revendedora recolheu o veículo "
            "alegando bloqueio, sem apresentar, até o momento, ordem judicial ou documento formal."
        )
    )
    timeline = _timeline_guide_text(case, {}, "").lower()
    assert "ausência de documentação clara sobre o suposto bloqueio" in timeline
    assert "o cliente informa não ter recebido documento formal" in timeline
    attachments = _attachments_guide_text(case, {}, "").lower()
    assert "o cliente informa não ter recebido documento formal do bloqueio alegado" in attachments


# ------------------------------------------------ F2 (IA-TRAB-003-R1, contraexemplos Codex)

_GUIDES = (_timeline_guide_text, _checklist_guide_text, _attachments_guide_text)


def test_f2_counterexample_pix_of_other_vehicle_is_not_linked_to_dealer_purchase():
    blob = "Cliente comprou veículo da revendedora Alfa. O veículo do irmão tem parcelas via Pix."
    assert _is_vehicle_dealer_pix_context(blob) is False
    case = _case(title="Compra de veículo", description=blob)
    for guide in _GUIDES:
        out = guide(case, {}, "").lower()
        assert "pagamentos via pix" not in out, guide.__name__
        assert "comprovantes pix das parcelas" not in out, guide.__name__
        assert "compra do veículo junto à revendedora" not in out, guide.__name__


def test_f2_pix_of_other_vehicle_is_not_attributed_even_when_dealer_flow_is_active():
    # compra vinculada a parcelas na própria frase; o Pix pertence a outro veículo
    blob = (
        "Cliente comprou veículo da revendedora Alfa e pagou parcelas em boleto. "
        "O veículo do irmão tem 10 parcelas de R$ 700,00 via Pix."
    )
    assert _is_vehicle_dealer_pix_context(blob) is True
    flags = _dealer_case_flags(blob)
    assert flags["pix"] is False
    assert "irmão" not in flags["linked_text"]
    case = _case(title="Compra de veículo", description=blob)
    for guide in _GUIDES:
        out = guide(case, {}, "").lower()
        assert "via pix" not in out, guide.__name__
        assert "10 parcelas" not in out and "700,00" not in out, guide.__name__


def test_f2_other_vehicle_or_other_relation_in_same_sentence_is_ambiguous():
    for blob in (
        "Cliente comprou veículo da revendedora Alfa e o veículo do irmão tem parcelas via Pix.",
        "Cliente comprou veículo da revendedora Alfa; pagou parcelas via Pix de outro contrato.",
        "Cliente comprou veículo da revendedora Alfa. Outra revendedora recolheu o carro.",
    ):
        assert _is_vehicle_dealer_pix_context(blob) is False, blob


def test_f2_counterexample_contract_and_entry_receipts_do_not_make_pix_proofs_available():
    text = (
        "Cliente comprou veículo da revendedora e pagou parcelas via Pix. "
        "Cliente possui contrato e recibos da entrada, mas não possui comprovantes Pix."
    )
    assert _proof_documents_status(text.lower()) == "pendente"
    case = _case(description=text)
    attachments = _attachments_guide_text(case, {}, "")
    assert "Anexo disponível" not in attachments
    assert "Comprovantes Pix das parcelas pagas" not in attachments
    assert "informa possuir" not in attachments.lower()
    assert "Pendente:" in attachments
    checklist = _checklist_guide_text(case, {}, "")
    assert "informa possuir" not in checklist.lower()
    assert "Disponível:" not in checklist
    assert "Pendente:" in checklist


def test_f2_counterexample_verification_of_pix_proofs_is_unknown_not_pending():
    text = "Cliente comprou veículo da revendedora e pagou parcelas via Pix. Verificar se possui comprovantes Pix."
    assert _proof_documents_status(text.lower()) == "desconhecido"
    case = _case(description=text)
    for guide in (_checklist_guide_text, _attachments_guide_text):
        out = guide(case, {}, "")
        assert "Disponibilidade desconhecida:" in out, guide.__name__
        assert "Pendente:" not in out, guide.__name__
        assert "Disponível:" not in out, guide.__name__
        assert "Anexo disponível" not in out, guide.__name__


def test_f2_document_availability_is_per_nature_and_per_clause():
    # outra natureza documental nunca é agregada aos comprovantes de pagamento
    assert _proof_documents_status("cliente possui recibos da entrada e comprovantes bancários.") == "desconhecido"
    assert _proof_documents_status("cliente possui comprovantes de residência; pagou parcelas via pix.") == "desconhecido"
    # posse afirmada em outra oração não se estende aos comprovantes Pix
    assert _proof_documents_status("não possui contrato, mas possui comprovantes pix.") == "disponivel"
    assert _proof_documents_status("possui comprovantes pix, mas não possui o contrato.") == "disponivel"
    # afirmações conflitantes => solicitar confirmação
    assert (
        _proof_documents_status("possui comprovantes pix. não possui comprovantes pix das últimas parcelas.")
        == "desconhecido"
    )
    # comprovantes de licenciamento não herdam a disponibilidade dos comprovantes Pix
    case = _case(
        description=(
            "Cliente comprou veículo da revendedora e pagou parcelas via Pix. "
            "O cliente possui comprovantes Pix dos pagamentos. Também pagou o IPVA do veículo."
        )
    )
    attachments = _attachments_guide_text(case, {}, "")
    assert "Anexo disponível 1" in attachments
    assert "Anexo disponível 2" not in attachments
    assert "Nome/descrição sugerida: Comprovantes de pagamento dos licenciamentos" not in attachments
    assert "Comprovantes de pagamento dos licenciamentos/IPVA mencionados: Disponibilidade desconhecida:" in attachments


def test_f2_counterexample_received_court_order_is_not_reported_as_absent():
    sentence = "Não recebeu o veículo, mas recebeu ordem judicial."
    assert _formal_block_document_status(sentence.lower()) == "mencionado"
    case = _case(
        description=(
            "Cliente comprou veículo da revendedora e pagou parcelas via Pix. "
            "A revendedora recolheu o veículo alegando bloqueio. " + sentence
        )
    )
    assert _dealer_case_flags(_case_context(case))["no_formal_docs"] is False
    for guide in _GUIDES:
        out = guide(case, {}, "").lower()
        assert "ausência de documentação clara" not in out, guide.__name__
        assert "não ter recebido documento formal" not in out, guide.__name__
        assert "não consta documento" not in out, guide.__name__
    timeline = _timeline_guide_text(case, {}, "").lower()
    assert "documentação do bloqueio alegado a confirmar" in timeline
    assert "verificar o documento com o cliente" in timeline
    attachments = _attachments_guide_text(case, {}, "").lower()
    assert "não permite confirmar se o documento formal mencionado se refere ao bloqueio alegado" in attachments


def test_f2_formal_document_absence_does_not_cross_clauses_or_objects():
    for text in (
        "não recebeu o veículo, mas recebeu ordem judicial.",
        "não recebeu o veículo e recebeu ordem judicial.",
        "não recebeu o carro nem a chave; recebeu notificação.",
        "não recebeu documentos do veículo.",
        "verificar se não recebeu ordem judicial.",
    ):
        assert _formal_block_document_status(text) != "ausente", text
    assert _formal_block_document_status("não recebeu documentos do veículo.") == "desconhecido"
    # ausência explícita, na própria oração, continua reconhecida
    for text in (
        "a revendedora recolheu o veículo sem apresentar ordem judicial.",
        "o cliente não recebeu nenhuma notificação.",
        "a revendedora alegou bloqueio, sem apresentar, até o momento, ordem judicial ou documento formal.",
    ):
        assert _formal_block_document_status(text) == "ausente", text
    # ausência contradita por outra oração => não afirmar ausência
    assert (
        _formal_block_document_status("não recebeu notificação. depois recebeu mandado de busca e apreensão.")
        == "mencionado"
    )



# ------------------------------------------------ F2 (IA-TRAB-003-R1, simplificação conservadora)

_GOODS_QUESTION = "houve entrega de algum bem como parte do pagamento desta negociação?"
_CONTRACT_COPY_QUESTION = "o cliente possui uma via do contrato referente a esta negociação?"


def test_f2_counterexample_payments_to_distinct_dealer_use_generic_flow():
    blob = "Cliente comprou veículo da revendedora Alfa e pagou parcelas via Pix à revendedora Beta."
    assert _is_vehicle_dealer_pix_context(blob) is False
    # mesmas contrapartes em frases distintas: também ambíguo
    assert (
        _is_vehicle_dealer_pix_context(
            "Cliente comprou veículo da revendedora Alfa. Pagou parcelas do veículo via Pix à revendedora Beta."
        )
        is False
    )
    case = _case(title="Compra de veículo", description=blob)
    for guide in _GUIDES:
        out = guide(case, {}, "").lower()
        assert "revendedora" not in out, guide.__name__
        assert "via pix" not in out and "comprovantes pix" not in out, guide.__name__
        assert "beta" not in out and "alfa" not in out, guide.__name__
        assert "anexo disponível" not in out, guide.__name__


def test_f2_counterexample_third_party_payments_are_not_attributed():
    blob = (
        "Cliente comprou veículo da revendedora Alfa, e o irmão pagou 10 parcelas de R$ 700,00 "
        "via Pix do financiamento dele."
    )
    assert _is_vehicle_dealer_pix_context(blob) is False
    flags = _dealer_case_flags(blob)
    assert flags["pix"] is False and flags["installments"] is False
    assert "irmão" not in flags["linked_text"] and "700,00" not in flags["linked_text"]
    case = _case(title="Compra de veículo", description=blob)
    for guide in _GUIDES:
        out = guide(case, {}, "").lower()
        for token in ("10 parcelas", "700,00", "via pix", "irmão", "comprovantes pix das parcelas"):
            assert token not in out, (guide.__name__, token)
        assert "anexo disponível" not in out, guide.__name__

    # pagamento de terceiro em frase separada que retoma o veículo: não é vinculado
    separate = (
        "Cliente comprou veículo da revendedora Alfa e pagou parcelas em boleto. "
        "O irmão pagou 10 parcelas de R$ 700,00 do veículo via Pix."
    )
    assert _dealer_case_flags(separate)["pix"] is False
    for guide in _GUIDES:
        out = guide(_case(description=separate), {}, "").lower()
        assert "700,00" not in out and "10 parcelas" not in out and "via pix" not in out, guide.__name__


def test_f2_counterexample_goods_in_other_deal_is_not_asserted():
    case = _case(
        title="Compra de veículo",
        description=(
            "Cliente comprou veículo da revendedora e pagou Pix; "
            "entregou uma bicicleta como entrada em outro negócio."
        ),
    )
    for guide in _GUIDES:
        out = guide(case, {}, "").lower()
        assert "bicicleta" not in out, guide.__name__
        assert "entrega de bens" not in out and "bens entregues" not in out, guide.__name__
        assert "bens como entrada" not in out and "bens de entrada" not in out, guide.__name__
    # substituído por pergunta neutra
    assert _GOODS_QUESTION in _timeline_guide_text(case, {}, "").lower()
    assert _GOODS_QUESTION in _checklist_guide_text(case, {}, "").lower()
    assert _GOODS_QUESTION in _attachments_guide_text(case, {}, "").lower()


def test_f2_counterexample_lost_lease_contract_is_not_asserted():
    case = _case(
        title="Compra de veículo",
        description=(
            "Cliente comprou veículo da revendedora e pagou Pix; "
            "perdeu a via do contrato de locação."
        ),
    )
    for guide in _GUIDES:
        out = guide(case, {}, "").lower()
        assert "perdeu" not in out and "perda da via" not in out, guide.__name__
        assert "locação" not in out, guide.__name__
    assert _CONTRACT_COPY_QUESTION in _timeline_guide_text(case, {}, "").lower()
    assert _CONTRACT_COPY_QUESTION in _checklist_guide_text(case, {}, "").lower()


def test_f2_goods_and_lost_contract_flags_are_no_longer_derived_from_text():
    flags = _dealer_case_flags(
        "Cliente comprou veículo da revendedora e pagou parcelas via Pix. "
        "Entregou uma moto como entrada e perdeu a via física do contrato."
    )
    assert "goods" not in flags and "lost_contract" not in flags


def test_f2_single_named_dealer_with_payments_keeps_specialized_flow():
    case = _case(
        title="Compra de veículo",
        description=(
            "Cliente comprou veículo da revendedora Alfa Comércio de Automóveis Ltda e pagou 6 parcelas "
            "de R$ 400,00 via Pix. A revendedora Alfa recolheu o veículo."
        ),
    )
    assert _is_vehicle_dealer_pix_context(_case_context(case)) is True
    checklist = _checklist_guide_text(case, {}, "").lower()
    assert "6 parcelas de r$ 400,00" in checklist
    assert "comprovar retomada ou recolhimento do veículo" in checklist
    timeline = _timeline_guide_text(case, {}, "").lower()
    assert "compra do veículo junto à revendedora" in timeline
    assert "pagamentos via pix" in timeline



# ------------------------------------------------ F2 (IA-TRAB-003-R1, múltiplas menções a revendedoras)


def _assert_generic_dealer_free(blob):
    assert _is_vehicle_dealer_pix_context(blob) is False, blob
    case = _case(title="Compra de veículo", description=blob)
    for guide in _GUIDES:
        out = guide(case, {}, "").lower()
        assert "revendedora" not in out, (guide.__name__, blob)
        assert "via pix" not in out and "comprovantes pix" not in out, (guide.__name__, blob)
        assert "alfa" not in out and "beta" not in out, (guide.__name__, blob)
        assert "anexo disponível" not in out, (guide.__name__, blob)


def test_f2_multiple_dealer_mentions_lowercase_use_generic_flow():
    _assert_generic_dealer_free("cliente comprou veículo da revendedora alfa e pagou parcelas via pix à revendedora beta.")


def test_f2_multiple_dealer_mentions_with_shared_name_prefix_use_generic_flow():
    _assert_generic_dealer_free(
        "Cliente comprou veículo da revendedora Auto Alfa e pagou parcelas via Pix à revendedora Auto Beta."
    )


def test_f2_multiple_dealer_mentions_in_distinct_sentences_use_generic_flow():
    _assert_generic_dealer_free(
        "Cliente comprou veículo da revendedora alfa. Pagou as parcelas do veículo via Pix à revendedora beta."
    )


def test_f2_single_dealer_mention_keeps_specialized_flow_in_all_guides():
    case = _case(
        title="Compra de veículo",
        description="cliente comprou veículo da revendedora alfa e pagou 6 parcelas de R$ 400,00 via pix.",
    )
    assert _is_vehicle_dealer_pix_context(_case_context(case)) is True
    timeline = _timeline_guide_text(case, {}, "").lower()
    assert "compra do veículo junto à revendedora" in timeline
    assert "pagamentos via pix" in timeline
    assert "pagamento de 6 parcelas via pix" in timeline
    checklist = _checklist_guide_text(case, {}, "").lower()
    assert "6 parcelas de r$ 400,00" in checklist
    assert "conferir e anexar comprovantes pix das parcelas pagas" in checklist
    attachments = _attachments_guide_text(case, {}, "").lower()
    assert "contrato de compra e venda ou financiamento/parcelamento firmado com a revendedora" in attachments
    assert "comprovantes dos pagamentos mencionados (pix/parcelas)" in attachments



def test_f2_payment_recipient_continuity_versus_distinct_recipient():
    # continuidade da mesma negociação: destinatário "nu" (à revendedora) mantém o fluxo
    same = _case(
        title="Compra de veículo",
        description=(
            "cliente comprou veículo da revendedora alfa. "
            "pagou 10 parcelas de R$ 700,00 via pix à revendedora, que recolheu o veículo."
        ),
    )
    assert _is_vehicle_dealer_pix_context(_case_context(same)) is True
    assert "10 parcelas de r$ 700,00" in _checklist_guide_text(same, {}, "").lower()
    # destinatário qualificado sem crase ou como sujeito do recebimento: vínculo ambíguo
    for blob in (
        "cliente comprou veículo da revendedora alfa e pagou a revendedora beta via pix.",
        "cliente comprou veículo da revendedora alfa. a revendedora beta recebeu os pix das parcelas.",
    ):
        _assert_generic_dealer_free(blob)


def _case_context(case):
    return f"{case.title} {case.description}"
