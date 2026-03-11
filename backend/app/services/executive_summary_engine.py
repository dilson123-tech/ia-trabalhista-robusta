from typing import Dict


def _risk_label(value: str) -> str:
    mapping = {
        "low": "Baixo",
        "medium": "Médio",
        "high": "Alto",
    }
    return mapping.get((value or "").lower(), value.capitalize() if value else "Indefinido")


def _complexity_label(value: str) -> str:
    mapping = {
        "baixa": "Baixa",
        "moderada": "Moderada",
        "alta": "Alta",
    }
    return mapping.get((value or "").lower(), value.capitalize() if value else "Indefinida")


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
    complexity = _complexity_label(viability.get("complexity", "Indefinida"))
    estimated_time = viability.get("estimated_time", "Indefinido")
    recommendation = viability.get("recommendation", "Sem recomendação estratégica definida.")

    final_status = decision.get("final_status", "INDEFINIDO")
    confidence = decision.get("confidence_level", 0)

    risk_level = _risk_label(analysis.get("risk_level", "medium"))
    summary = analysis.get("summary", "Sem resumo técnico disponível.")

    executive_text = (
        f"Após análise técnica e estratégica preliminar, o caso foi classificado como "
        f"{final_status.lower()}, com probabilidade estimada de êxito de {int(probability * 100)}% "
        f"e score estratégico de {score}/100. "
        f"O nível de risco identificado foi {risk_level}, com complexidade {complexity} "
        f"e tempo estimado de tramitação de {estimated_time}. "
        f"Como direcionamento inicial, a recomendação estratégica é: {recommendation}. "
        f"Síntese técnica do caso: {summary}"
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
