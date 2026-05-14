from types import SimpleNamespace

from app.api.v1.routes.editable_documents import _build_fgts_claim_values_section


def test_fgts_claim_values_calculates_estimated_amounts_when_minimum_data_exists():
    case = SimpleNamespace(
        case_number="PILOTO-TRAB-005",
        title="FGTS não recolhido — ausência de depósitos durante o contrato",
        description="Reclamante dispensado sem justa causa. FGTS não recolhido por 10 meses.",
    )
    metadata = {
        "salario_mensal": "R$ 2.300,00",
        "meses_sem_fgts": 10,
        "dispensa_sem_justa_causa": True,
    }

    content, calculated_cause_value = _build_fgts_claim_values_section(
        metadata,
        case,
        "[valor a ser definido pelo advogado]",
    )

    assert calculated_cause_value == "2.576,00"
    assert "Diferenças estimadas de FGTS" in content
    assert "R$ 1.840,00" in content
    assert "multa rescisória de 40%" in content
    assert "R$ 736,00" in content
    assert "Valor estimado da causa" in content
    assert "R$ 2.576,00" in content
    assert "revisão do advogado" in content


def test_fgts_claim_values_does_not_invent_amounts_without_minimum_data():
    case = SimpleNamespace(
        case_number="PILOTO-TRAB-005",
        title="FGTS não recolhido — ausência de depósitos durante o contrato",
        description="Relato de FGTS não recolhido sem salário e sem quantidade exata de meses.",
    )

    content, calculated_cause_value = _build_fgts_claim_values_section(
        {},
        case,
        "[valor a ser definido pelo advogado]",
    )

    assert calculated_cause_value is None
    assert "Cálculo pendente para ajuizamento" in content
    assert "Informar salário/remuneração mensal" in content
    assert "Informar quantidade de meses ou competências" in content
    assert "extrato analítico completo do FGTS" in content
    assert "Confirmar modalidade de rescisão" in content
