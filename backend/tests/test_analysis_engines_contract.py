from app.services.ai_case_analysis import analyze_case
from app.services.strategic_diagnosis import strategic_diagnosis
from app.services.viability_engine import calculate_viability
from app.services.decision_engine import generate_decision


def test_analysis_pipeline_high_risk_contract():
    analysis = analyze_case(
        case_number="0001",
        title="Ação com horas extras e FGTS",
        description="Pedido de verbas rescisórias, horas extras e FGTS não recolhido.",
    )

    assert isinstance(analysis, dict)
    assert analysis["risk_level"] == "high"
    assert isinstance(analysis["summary"], str)
    assert len(analysis["summary"]) > 20
    assert isinstance(analysis["issues"], list)
    assert len(analysis["issues"]) >= 3
    assert isinstance(analysis["next_steps"], list)
    assert len(analysis["next_steps"]) >= 1

    strategic = strategic_diagnosis(analysis)
    assert strategic["success_probability"] == 0.40
    assert strategic["complexity"] == "alta"
    assert strategic["financial_risk"] == "alto"
    assert strategic["critical_points"] == analysis["issues"]
    assert isinstance(strategic["recommended_strategy"], str)
    assert isinstance(strategic["strong_points"], list)

    viability = calculate_viability(analysis)
    assert viability["score"] == 31
    assert viability["probability"] == 0.31
    assert viability["label"] == "Baixa probabilidade"
    assert viability["complexity"] == "Alta"
    assert viability["estimated_time"] == "24+ meses"
    assert "Reavaliar" in viability["recommendation"]

    decision = generate_decision(analysis, viability)
    assert decision["final_status"] == "ARRISCADA"
    assert decision["confidence_level"] == 31.0
    assert decision["executive_recommendation"] == viability["recommendation"]
    assert decision["estimated_complexity"] == viability["complexity"]
    assert decision["estimated_time"] == viability["estimated_time"]


def test_analysis_pipeline_low_risk_contract():
    analysis = analyze_case(
        case_number="0002",
        title="Consulta trabalhista simples",
        description="Dúvida inicial sem pedido de FGTS, horas extras ou verbas rescisórias.",
    )

    assert isinstance(analysis, dict)
    assert analysis["risk_level"] in {"low", "medium", "high"}
    assert isinstance(analysis["issues"], list)
    assert isinstance(analysis["next_steps"], list)

    strategic = strategic_diagnosis(analysis)
    viability = calculate_viability(analysis)
    decision = generate_decision(analysis, viability)

    assert 0 <= viability["score"] <= 100
    assert 0 <= viability["probability"] <= 1
    assert decision["final_status"] in {"FAVORÁVEL", "MODERADA", "ARRISCADA"}
    assert isinstance(decision["confidence_level"], float)

    if analysis["risk_level"] == "low":
        assert strategic["success_probability"] == 0.80
        assert strategic["complexity"] == "baixa"
        assert viability["label"] == "Alta chance de êxito"
        assert decision["final_status"] == "FAVORÁVEL"
