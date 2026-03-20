from app.modules.document_factory import (
    DocumentFactoryService,
    IntakeEmployment,
    IntakeItem,
    IntakeParty,
    PeticaoInicialTrabalhistaIntake,
    build_peticao_inicial_payload_from_intake,
)


def test_build_peticao_inicial_payload_from_intake_maps_structured_data():
    intake = PeticaoInicialTrabalhistaIntake(
        reclamante=IntakeParty(
            nome="João da Silva",
            documento="111.111.111-11",
            qualificacao="brasileiro, solteiro, operador de máquina",
        ),
        reclamada=IntakeParty(
            nome="Empresa XYZ Ltda.",
            documento="12.345.678/0001-99",
            qualificacao="pessoa jurídica de direito privado",
        ),
        vinculo=IntakeEmployment(
            data_admissao="2023-01-10",
            data_dispensa="2024-08-20",
            funcao="Operador de máquina",
            salario="R$ 2.500,00",
            jornada="Segunda a sábado, das 07h às 17h",
        ),
        fatos=[
            IntakeItem(
                titulo="Horas extras habituais",
                descricao="O reclamante laborava além da 8ª diária sem pagamento integral.",
            ),
        ],
        pedidos=[
            IntakeItem(
                titulo="Horas extras e reflexos",
                descricao="Pagamento de horas extras com reflexos em DSR, férias, 13º e FGTS.",
            ),
        ],
        fundamentos=[
            IntakeItem(
                titulo="CLT e CF",
                descricao="Violação às normas de duração do trabalho e remuneração.",
            ),
        ],
        provas=[
            IntakeItem(
                titulo="Cartões de ponto",
                descricao="Juntada de cartões de ponto e prova testemunhal.",
            ),
        ],
        valor_causa="R$ 18.500,00",
    )

    payload = build_peticao_inicial_payload_from_intake(intake)

    assert payload["reclamante_nome"] == "João da Silva"
    assert payload["reclamada_nome"] == "Empresa XYZ Ltda."
    assert "Admissão: 2023-01-10" in payload["contrato_resumo"]
    assert "Dispensa: 2024-08-20" in payload["contrato_resumo"]
    assert "Função: Operador de máquina" in payload["contrato_resumo"]
    assert "Salário: R$ 2.500,00" in payload["contrato_resumo"]
    assert "Jornada: Segunda a sábado, das 07h às 17h" in payload["contrato_resumo"]
    assert "Horas extras habituais" in payload["fatos"]
    assert "Horas extras e reflexos" in payload["pedidos"]
    assert "CLT e CF" in payload["fundamentos"]
    assert "Cartões de ponto" in payload["provas"]
    assert payload["valor_causa"] == "R$ 18.500,00"


def test_build_peticao_inicial_payload_from_intake_uses_fallbacks_when_sections_are_empty():
    intake = PeticaoInicialTrabalhistaIntake(
        reclamante=IntakeParty(nome="Maria Souza"),
        reclamada=IntakeParty(nome="Comércio Alfa"),
    )

    payload = build_peticao_inicial_payload_from_intake(intake)

    assert payload["reclamante_nome"] == "Maria Souza"
    assert payload["reclamada_nome"] == "Comércio Alfa"
    assert "Admissão: não informada" in payload["contrato_resumo"]
    assert "Dispensa: não informada" in payload["contrato_resumo"]
    assert "Função: não informada" in payload["contrato_resumo"]
    assert "Salário: não informado" in payload["contrato_resumo"]
    assert "Jornada: não informada" in payload["contrato_resumo"]
    assert "Descrever os fatos principais" in payload["fatos"]
    assert "Listar pedidos de forma objetiva" in payload["pedidos"]
    assert "Indicar fundamentos jurídicos aplicáveis" in payload["fundamentos"]
    assert "Indicar documentos, testemunhas" in payload["provas"]
    assert payload["valor_causa"] == "Informar valor estimado da causa."


def test_document_factory_service_builds_peticao_from_intake():
    intake = PeticaoInicialTrabalhistaIntake(
        reclamante=IntakeParty(
            nome="Carlos Pereira",
            documento="222.222.222-22",
            qualificacao="brasileiro, soldador",
        ),
        reclamada=IntakeParty(
            nome="Metalúrgica Beta",
            documento="98.765.432/0001-10",
            qualificacao="pessoa jurídica de direito privado",
        ),
        vinculo=IntakeEmployment(
            data_admissao="2022-02-01",
            data_dispensa="2024-01-15",
            funcao="Soldador",
            salario="R$ 3.200,00",
            jornada="Segunda a sexta, das 08h às 18h",
        ),
        fatos=[
            IntakeItem(
                titulo="Acúmulo de função",
                descricao="O reclamante acumulava atividades sem contraprestação salarial.",
            ),
        ],
        pedidos=[
            IntakeItem(
                titulo="Diferenças salariais",
                descricao="Pagamento das diferenças decorrentes do acúmulo de função.",
                fundamento_legal="CLT, art. 460",
            ),
        ],
        fundamentos=[
            IntakeItem(
                titulo="Base legal do pedido",
                descricao="Aplicação do art. 460 da CLT ao caso concreto.",
                fundamento_legal="CLT, art. 460",
            ),
        ],
        provas=[
            IntakeItem(
                titulo="Prova testemunhal",
                descricao="Oitiva de testemunhas do setor de produção.",
            ),
        ],
    )

    service = DocumentFactoryService()
    draft = service.build_peticao_inicial_trabalhista_from_intake(
        intake=intake,
        case_id=123,
        tenant_id=10,
        user_id=20,
    )

    sections_by_key = {section["key"]: section["content"] for section in draft.sections}

    assert draft.area == "trabalhista"
    assert draft.pleading_type == "peticao_inicial_trabalhista"
    assert "Petição Inicial" in draft.title

    assert len(draft.parties) == 2
    assert draft.parties[0].role == "reclamante"
    assert draft.parties[0].name == "Carlos Pereira"
    assert draft.parties[0].document_id == "222.222.222-22"
    assert draft.parties[1].role == "reclamada"
    assert draft.parties[1].name == "Metalúrgica Beta"
    assert draft.parties[1].document_id == "98.765.432/0001-10"

    assert len(draft.facts) == 1
    assert draft.facts[0].title == "Acúmulo de função"

    assert len(draft.requests) == 1
    assert draft.requests[0].title == "Diferenças salariais"
    assert draft.requests[0].legal_basis == "CLT, art. 460"

    assert len(draft.grounds) == 1
    assert draft.grounds[0].title == "Base legal do pedido"
    assert draft.grounds[0].citations == ["CLT, art. 460"]

    assert len(draft.evidences) == 1
    assert draft.evidences[0].title == "Prova testemunhal"

    assert "Carlos Pereira" in sections_by_key["partes"]
    assert "Metalúrgica Beta" in sections_by_key["partes"]
    assert "Soldador" in sections_by_key["contrato_trabalho"]
    assert "Acúmulo de função" in sections_by_key["fatos"]
    assert "Diferenças salariais" in sections_by_key["pedidos"]
