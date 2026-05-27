from app.core.settings import settings
from app.services.ai_case_analysis import analyze_case


def test_consumer_case_inferred_from_generic_civel(monkeypatch):
    monkeypatch.setattr(settings, "LLM_ANALYSIS_ENABLED", False)

    payload = analyze_case(
        case_number="QA-CONSUMIDOR-REGISTRY-001",
        title="Produto com defeito e vício do produto",
        description="Consumidor comprou produto com defeito, acionou fornecedor e tem protocolos de atendimento.",
        legal_area="civel",
        action_type="Consumidor — vício do produto com pedido de restituição",
    )

    assert payload["legal_area"] == "consumidor"
    combined = " ".join([payload["summary"], *payload["issues"], *payload["next_steps"]]).lower()
    assert "fornecedor" in combined or "consumo" in combined
    assert "reclamação trabalhista" not in combined
    assert "fgts" not in combined


def test_family_case_inferred_from_generic_civel(monkeypatch):
    monkeypatch.setattr(settings, "LLM_ANALYSIS_ENABLED", False)

    payload = analyze_case(
        case_number="QA-FAMILIA-REGISTRY-001",
        title="Guarda e regulamentação de convivência",
        description="Caso envolve guarda de menor, convivência familiar e rotina escolar.",
        legal_area="civel",
        action_type="Família — guarda e convivência",
    )

    assert payload["legal_area"] == "familia"
    combined = " ".join([payload["summary"], *payload["issues"], *payload["next_steps"]]).lower()
    assert "guarda" in combined or "menor" in combined
    assert "reclamação trabalhista" not in combined
    assert "ctps" not in combined


def test_previdenciario_case_inferred_from_bpc_loas(monkeypatch):
    monkeypatch.setattr(settings, "LLM_ANALYSIS_ENABLED", False)

    payload = analyze_case(
        case_number="QA-PREV-REGISTRY-001",
        title="BPC/LOAS idoso",
        description="Pedido de BPC/LOAS para pessoa idosa em vulnerabilidade social perante o INSS, com CadÚnico e renda familiar.",
        legal_area="civel",
        action_type="Previdenciário — BPC/LOAS",
    )

    assert payload["legal_area"] == "previdenciario"
    combined = " ".join([payload["summary"], *payload["issues"], *payload["next_steps"]]).lower()
    assert "bpc" in combined or "loas" in combined or "inss" in combined
    assert "reclamação trabalhista" not in combined
    assert "fgts" not in combined
