from app.services.ai_case_analysis import analyze_case
from app.services.strategic_diagnosis import strategic_diagnosis
from app.services.viability_engine import calculate_viability
from app.services.decision_engine import generate_decision
from app.services.executive_summary_engine import generate_executive_summary


def test_analysis_pipeline_incomplete_labor_case_is_handled_safely():
    analysis = analyze_case(
        case_number="0001",
        title="Ação com horas extras e FGTS",
        description="Pedido de verbas rescisórias, horas extras e FGTS não recolhido.",
    )

    assert isinstance(analysis, dict)
    assert analysis["risk_level"] in {"medium", "high"}
    assert isinstance(analysis["summary"], str)
    assert len(analysis["summary"]) > 20
    assert isinstance(analysis["issues"], list)
    assert len(analysis["issues"]) >= 3
    assert isinstance(analysis["next_steps"], list)
    assert len(analysis["next_steps"]) >= 1

    strategic = strategic_diagnosis(analysis)
    assert strategic["financial_risk"] in {"baixo", "medio", "médio", "alto", "indeterminado"}
    assert strategic["critical_points"] == analysis["issues"]
    assert isinstance(strategic["recommended_strategy"], str)
    assert isinstance(strategic["strong_points"], list)

    if strategic["success_probability"] is None:
        assert strategic["complexity"] in {"indefinida", "preliminar"}
        assert "complementação factual e documental" in strategic["recommended_strategy"]
    else:
        assert 0 <= strategic["success_probability"] <= 1
        assert strategic["complexity"] in {"baixa", "média", "media", "alta", "preliminar"}

    viability = calculate_viability(analysis)

    if viability["score"] is None:
        assert viability["probability"] is None
        assert viability["label"] == "Dados insuficientes para estimativa"
        assert viability["complexity"] == "Indefinida por insuficiência de dados"
        assert viability["estimated_time"] in {
            "Indefinido por insuficiência de dados",
            "Depende da complexidade, da fase processual, da prova disponível e do juízo competente.",
        }
        assert "Complementar fatos" in viability["recommendation"]
    else:
        assert 0 <= viability["score"] <= 100
        assert 0 <= viability["probability"] <= 1
        assert isinstance(viability["label"], str)
        assert isinstance(viability["recommendation"], str)

    decision = generate_decision(analysis, viability)

    if viability["score"] is None:
        assert decision["final_status"] == "DADOS INSUFICIENTES"
        assert decision["confidence_level"] is None
    else:
        assert decision["final_status"] in {
            "FAVORÁVEL",
            "MODERADA",
            "MODERADA COM RISCO",
            "ARRISCADA",
        }
        assert isinstance(decision["confidence_level"], float)

    assert decision["executive_recommendation"] == viability["recommendation"]
    assert decision["estimated_complexity"] == viability["complexity"]
    assert decision["estimated_time"] == viability["estimated_time"]


def test_analysis_pipeline_vague_labor_case_returns_safe_contract():
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

    if viability["score"] is None:
        assert strategic["success_probability"] is None
        assert viability["probability"] is None
        assert viability["label"] == "Dados insuficientes para estimativa"
        assert decision["final_status"] == "DADOS INSUFICIENTES"
        assert decision["confidence_level"] is None
    else:
        assert 0 <= viability["score"] <= 100
        assert 0 <= viability["probability"] <= 1
        assert 0 <= strategic["success_probability"] <= 1
        assert decision["final_status"] in {
            "FAVORÁVEL",
            "MODERADA",
            "MODERADA COM RISCO",
            "ARRISCADA",
        }
        assert isinstance(decision["confidence_level"], float)


def test_civel_cobranca_strong_evidence_recommendation_is_not_overly_pessimistic():
    analysis = {
        "risk_level": "low",
        "summary": (
            "Ação de cobrança contratual com contrato assinado, obrigação contratual, "
            "relação contratual comprovada, execução integral dos serviços, pagamento parcial, "
            "parcelas vencidas, saldo principal inadimplido de R$ 16.000,00, saldo líquido, "
            "saldo remanescente, comprovantes de pagamento, relatório de entrega, fotografias, "
            "e-mails de aprovação, mensagens de WhatsApp com reconhecimento de dívida, "
            "notificação extrajudicial recebida sem quitação em 20/04/2026, multa de 2%, "
            "juros de 1% ao mês, correção monetária e planilha de cálculo."
        ),
        "issues": [
            "Cobrança contratual com saldo principal inadimplido e saldo líquido documentado.",
            "Contrato assinado, obrigação contratual e relação contratual comprovada.",
            "Pagamento parcial e comprovantes de pagamento das parcelas adimplidas.",
            "Reconhecimento de dívida e notificação extrajudicial recebida sem quitação.",
            "Necessidade de cálculo atualizado com multa, juros, correção monetária e planilha de cálculo.",
        ],
        "next_steps": [
            "Prosseguir com ação de cobrança após conferência documental.",
            "Atualizar planilha de cálculo e validar documentos antes do protocolo.",
        ],
    }

    strategic = strategic_diagnosis(analysis)
    viability = calculate_viability(analysis)
    decision = generate_decision(analysis, viability)
    executive = generate_executive_summary(analysis, viability, decision)

    assert viability["label"] == "Viabilidade moderada com prova documental relevante"
    assert "Prosseguir com preparação do ajuizamento" in viability["recommendation"]
    assert "cálculo atualizado" in viability["recommendation"]
    assert "validação profissional final" in viability["recommendation"]

    assert (
        "preparação de ajuizamento" in strategic["recommended_strategy"]
        or "preparação do ajuizamento" in strategic["recommended_strategy"]
    )

    assert decision["final_status"] == "MODERADA"
    assert executive["final_status"] == "MODERADA"
    assert "Caso com viabilidade moderada" in executive["executive_summary"]

    forbidden = "\n".join([
        viability["recommendation"],
        strategic["recommended_strategy"],
        executive["executive_summary"],
        decision["final_status"],
        executive["final_status"],
    ]).lower()

    assert "não ajuizar sem reforço probatório mínimo" not in forbidden
    assert "nao ajuizar sem reforco probatorio minimo" not in forbidden
    assert "moderada com risco" not in forbidden
    assert "probabilidade estimada" not in forbidden
    assert "/100" not in forbidden
