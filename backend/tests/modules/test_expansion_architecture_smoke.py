from app.modules.document_factory import DocumentFactoryService
from app.modules.engines import get_engine, list_engines
from app.modules.engines.base import EngineContext
from app.modules.jobs import JobService
from app.modules.jobs.contracts import JobRequest


def test_engines_registry_exposes_trabalhista():
    assert "trabalhista" in list_engines()
    engine = get_engine("trabalhista")
    assert engine.area == "trabalhista"


def test_trabalhista_engine_analysis_scaffold():
    engine = get_engine("trabalhista")
    result = engine.analyze_case(
        EngineContext(
            area="trabalhista",
            case_id=1,
            tenant_id=1,
            user_id=1,
            payload={"title": "Horas extras e verbas rescisórias"},
        )
    )

    assert result.area == "trabalhista"
    assert result.risk_level == "medium"
    assert "Horas extras" in result.summary


def test_document_factory_builds_structured_trabalhista_pleading():
    service = DocumentFactoryService()
    draft = service.build_pleading(
        area="trabalhista",
        pleading_type="peticao_inicial_trabalhista",
        case_id=1,
        tenant_id=1,
        user_id=1,
        payload={
            "title": "Horas extras e verbas rescisórias",
            "reclamante_nome": "João da Silva",
            "reclamada_nome": "Empresa XPTO Ltda",
            "contrato_resumo": "Admissão em 01/02/2020, dispensa em 10/01/2025, função de auxiliar de produção.",
            "fatos": "O reclamante laborava em sobrejornada habitual sem o devido pagamento das horas extras.",
            "fundamentos": "Aplicação da CLT e dos entendimentos consolidados sobre jornada e reflexos.",
            "pedidos": "Pagamento de horas extras, reflexos em DSR, férias, 13º salário e FGTS.",
            "provas": "Cartões de ponto, holerites e prova testemunhal.",
            "valor_causa": "R$ 25.000,00",
        },
    )

    assert draft.area == "trabalhista"
    assert draft.pleading_type == "peticao_inicial_trabalhista"
    assert draft.title == "Petição Inicial Trabalhista"
    assert len(draft.sections) == 8
    assert draft.sections[0]["key"] == "partes"
    assert draft.sections[1]["key"] == "contrato_trabalho"
    assert draft.sections[2]["key"] == "fatos"
    assert draft.sections[3]["key"] == "fundamentos"
    assert draft.sections[4]["key"] == "pedidos"
    assert draft.sections[5]["key"] == "provas"
    assert draft.sections[6]["key"] == "valor_causa"
    assert draft.sections[7]["key"] == "fechamento"
    assert "João da Silva" in draft.sections[0]["content"]
    assert "Empresa XPTO Ltda" in draft.sections[0]["content"]


def test_job_service_enqueues_scaffold_job():
    service = JobService()
    job = service.enqueue(
        JobRequest(
            job_type="pleading_generation",
            area="trabalhista",
            case_id=1,
            tenant_id=1,
            user_id=1,
            payload={"pleading_type": "peticao_inicial_trabalhista"},
        )
    )

    assert job.job_type == "pleading_generation"
    assert job.status == "queued"
    assert job.result["area"] == "trabalhista"
    assert job.result["scaffold"] is True
