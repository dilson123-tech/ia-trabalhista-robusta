from typing import Dict


def generate_executive_summary(
    analysis: Dict,
    viability: Dict,
    decision: Dict,
) -> Dict:
    """
    Consolida análise técnica + viabilidade + decisão final
    e gera um resumo executivo pronto para advogado ou cliente.
    """

    score = viability.get("score", 0)
    probability = viability.get("probability", 0)
    complexity = viability.get("complexity", "Indefinida")
    estimated_time = viability.get("estimated_time", "Indefinido")
    recommendation = viability.get("recommendation", "")

    final_status = decision.get("final_status", "INDEFINIDO")
    confidence = decision.get("confidence_level", 0)

    risk_level = analysis.get("risk_level", "medium")
    summary = analysis.get("summary", "")

    # Texto executivo consolidado
    executive_text = (
        f"Após análise técnica e estratégica do caso, "
        f"identificou-se nível de risco '{risk_level}'. "
        f"A probabilidade estimada de êxito é de {int(probability * 100)}%, "
        f"com score estratégico {score}/100. "
        f"O caso apresenta complexidade {complexity} "
        f"e tempo estimado de tramitação de {estimated_time}. "
        f"Decisão executiva: {final_status}, "
        f"com grau de confiança de {confidence}%. "
        f"Recomendação estratégica: {recommendation}. "
        f"Resumo técnico: {summary}"
    )

    return {
        "executive_summary": executive_text,
        "final_status": final_status,
        "confidence_level": confidence,
        "probability_percent": int(probability * 100),
        "score": score,
        "complexity": complexity,
        "estimated_time": estimated_time,
    }
