from typing import Dict


def build_executive_summary(viability: Dict, analysis: Dict) -> str:
    """
    Gera resumo executivo curto, direto e vendável.
    """
    label = str(viability.get("label", "") or "").lower()
    probability = int((viability.get("probability", 0) or 0) * 100)
    recommendation = str(viability.get("recommendation", "") or "").strip()

    risk = str(analysis.get("risk_level", "indefinido") or "indefinido").strip().lower()
    risk_label_map = {
        "low": "baixo",
        "medium": "médio",
        "high": "alto",
        "baixo": "baixo",
        "medio": "médio",
        "médio": "médio",
        "alto": "alto",
    }
    risk_label = risk_label_map.get(risk, risk)

    if "alta viabilidade" in label:
        status = "caso altamente favorável"
    elif "viável com dependência probatória" in label:
        status = "caso juridicamente promissor, porém dependente de prova"
    elif "viabilidade moderada" in label:
        status = "caso com viabilidade moderada"
    elif "viabilidade condicionada à prova" in label:
        status = "caso com viabilidade condicionada à prova"
    elif "baixa prontidão estratégica" in label:
        status = "caso com risco relevante"
    else:
        status = "caso em avaliação estratégica"

    direction = recommendation or "avaliar estratégia antes de avançar"

    return (
        f"{status.capitalize()}, com probabilidade estimada de êxito em {probability}%. "
        f"Nível de risco: {risk_label}. "
        f"Direcionamento: {direction}."
    )


def generate_decision(analysis: Dict, viability: Dict) -> Dict:
    """
    Consolida análise técnica + viabilidade estratégica
    e gera decisão executiva final em linguagem premium.
    """
    score = float(viability.get("score", 0) or 0)
    probability = float(viability.get("probability", 0) or 0)
    label = str(viability.get("label", "") or "").strip().lower()
    recommendation = str(viability.get("recommendation", "") or "").strip()
    complexity = str(viability.get("complexity", "") or "").strip()
    estimated_time = str(viability.get("estimated_time", "") or "").strip()

    if "alta viabilidade" in label:
        final_status = "FAVORÁVEL"
    elif "viável com dependência probatória" in label:
        final_status = "VIÁVEL COM RESSALVAS"
    elif "viabilidade moderada" in label:
        final_status = "MODERADA"
    elif "viabilidade condicionada à prova" in label:
        final_status = "MODERADA COM RISCO"
    elif "baixa prontidão estratégica" in label:
        final_status = "ARRISCADA"
    else:
        if score >= 78:
            final_status = "FAVORÁVEL"
        elif score >= 62:
            final_status = "MODERADA"
        elif score >= 48:
            final_status = "MODERADA COM RISCO"
        else:
            final_status = "ARRISCADA"

    confidence_level = round(probability * 100, 1)

    return {
        "final_status": final_status,
        "confidence_level": confidence_level,
        "executive_recommendation": recommendation or "Sem recomendação executiva definida",
        "estimated_complexity": complexity or "Indefinida",
        "estimated_time": estimated_time or "Indefinido",
        "executive_summary": build_executive_summary(viability, analysis),
    }
