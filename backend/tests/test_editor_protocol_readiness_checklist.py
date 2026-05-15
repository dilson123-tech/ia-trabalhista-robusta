from app.api.v1.routes.editable_documents import _build_protocol_readiness_checklist_section


def test_protocol_readiness_checklist_flags_missing_qualification_and_fgts_documents():
    content = _build_protocol_readiness_checklist_section(
        author_inline_qualification=(
            "Roberto Almeida Santos, [nacionalidade], [estado civil], servente de obras, "
            "inscrito(a) no CPF nº [CPF a complementar] e RG nº [RG a complementar], "
            "residente e domiciliado(a) em [endereço completo]"
        ),
        defendant_inline_qualification=(
            "Construções Atlântico LTDA, pessoa jurídica inscrita no CNPJ nº [CNPJ a complementar], "
            "com sede em Joinville/SC"
        ),
        lawyer_name="Dr. Advogado Responsável",
        lawyer_oab="000000",
        lawyer_uf="SC",
        signature_local="Joinville/SC",
        signature_date="14 de maio de 2026",
        cause_value="2.576,00",
        is_fgts_case=True,
    )

    assert "Checklist interno de prontidão para protocolo" in content
    assert "Informar e conferir CPF do reclamante" in content
    assert "Informar e conferir RG/documento pessoal do reclamante" in content
    assert "Informar endereço completo do reclamante" in content
    assert "Informar e conferir CNPJ da reclamada" in content
    assert "Conferir se a sede/endereço da reclamada está completo para citação" in content
    assert "Anexar extrato analítico completo do FGTS" in content
    assert "Anexar ou conferir holerites/recibos salariais" in content
    assert "Revisar memória de cálculo das competências sem recolhimento" in content
    assert "Valor da causa preenchido/revisável: R$ 2.576,00" in content


def test_protocol_readiness_checklist_flags_missing_lawyer_signature_data():
    content = _build_protocol_readiness_checklist_section(
        author_inline_qualification="Autor completo, CPF nº 00000000000 e RG nº 000000, residente e domiciliado(a) em Rua Teste",
        defendant_inline_qualification="Empresa Teste LTDA, pessoa jurídica inscrita no CNPJ nº 00000000000100, com sede em Rua Empresa",
        lawyer_name="[Nome do advogado]",
        lawyer_oab="[número]",
        lawyer_uf="[UF]",
        signature_local="[Local]",
        signature_date="[data]",
        cause_value="[valor a ser definido pelo advogado]",
        is_fgts_case=False,
    )

    assert "Informar nome do advogado responsável" in content
    assert "Informar OAB/UF do advogado responsável" in content
    assert "Informar local de assinatura" in content
    assert "Informar data de assinatura" in content
    assert "Definir ou revisar valor da causa antes do protocolo" in content
