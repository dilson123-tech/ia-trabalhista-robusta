from typing import Dict


def _risk_label(value: str) -> str:
    mapping = {
        "low": "Baixo",
        "medium": "Médio",
        "high": "Alto",
        "baixo": "Baixo",
        "medio": "Médio",
        "médio": "Médio",
        "alto": "Alto",
    }
    return mapping.get((value or "").lower(), value.capitalize() if value else "Indefinido")


def _complexity_label(value: str) -> str:
    mapping = {
        "baixa": "Baixa",
        "moderada": "Moderada",
        "alta": "Alta",
        "média": "Média",
        "media": "Média",
    }
    return mapping.get((value or "").lower(), value.capitalize() if value else "Indefinida")


def _status_phrase(final_status: str) -> str:
    normalized = (final_status or "").strip().upper()
    mapping = {
        "FAVORÁVEL": "caso altamente favorável",
        "VIÁVEL COM RESSALVAS": "caso juridicamente promissor, porém dependente de prova",
        "MODERADA": "caso com viabilidade moderada",
        "MODERADA COM RISCO": "caso com viabilidade moderada e risco relevante",
        "ARRISCADA": "caso com risco relevante",
    }
    return mapping.get(normalized, "caso em avaliação estratégica")


def generate_executive_summary(
    analysis: Dict,
    viability: Dict,
    decision: Dict,
) -> Dict:
    """
    Consolida análise técnica + viabilidade + decisão final
    e gera um resumo executivo curto, direto e comercial.
    """

    score = viability.get("score", 0)
    probability = viability.get("probability", 0) or 0
    complexity = _complexity_label(viability.get("complexity", "Indefinida"))
    estimated_time = viability.get("estimated_time", "Indefinido")
    recommendation = viability.get("recommendation", "Sem recomendação estratégica definida.")

    final_status = decision.get("final_status", "INDEFINIDO")
    confidence = decision.get("confidence_level", 0)

    risk_level = _risk_label(analysis.get("risk_level", "medium"))
    status_phrase = _status_phrase(final_status)
    probability_percent = int(float(probability) * 100)

    executive_text = (
        f"{status_phrase.capitalize()}, com probabilidade estimada de êxito em {probability_percent}%. "
        f"Nível de risco: {risk_level}. "
        f"Complexidade: {complexity}. "
        f"Tempo estimado: {estimated_time}. "
        f"Direcionamento: {recommendation}."
    )

    return {
        "executive_summary": executive_text,
        "final_status": final_status,
        "confidence_level": confidence,
        "probability_percent": probability_percent,
        "score": score,
        "complexity": complexity,
        "estimated_time": estimated_time,
    }
