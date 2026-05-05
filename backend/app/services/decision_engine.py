from typing import Dict


def _is_insufficient_data(viability: Dict, analysis: Dict) -> bool:
    viability_dimensions = viability.get("dimensions") or {}
    viability_label = str(viability.get("label", "") or "").strip().lower()
    analysis_issues = " ".join(analysis.get("issues", []) or []).lower()

    probability = viability.get("probability")
    score = viability.get("score")

    if viability_dimensions.get("insufficient_data") is True:
        return True
    if probability is None or score is None:
        return True
    if "dados insuficientes" in viability_label:
        return True

    hard_markers = (
        "dados insuficientes",
        "insuficiência de dados",
        "insuficiencia de dados",
        "sem base para calcular",
        "sem base para aferir",
        "sem base jurídica",
        "sem base juridica",
        "sem base factual",
        "informação insuficiente para diagnóstico",
        "informacao insuficiente para diagnostico",
        "ausência de causa de pedir",
        "ausencia de causa de pedir",
        "pedido definido",
        "insuficiência probatória",
        "insuficiencia probatoria",
        "inexistência de marco temporal",
        "inexistencia de marco temporal",
        "legitimidade ativa e passiva",
    )
    if any(marker in analysis_issues for marker in hard_markers):
        return True

    soft_markers = (
        "sem vínculo",
        "sem vinculo",
        "sem datas",
        "ausência de datas",
        "ausencia de datas",
        "sem documentos",
        "ausência de documentos",
        "ausencia de documentos",
    )
    soft_hits = sum(1 for marker in soft_markers if marker in analysis_issues)

    if soft_hits >= 2:
        return True

    return False


def build_executive_summary(viability: Dict, analysis: Dict) -> str:
    """
    Gera resumo executivo curto, direto e vendável.
    """
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

    if _is_insufficient_data(viability, analysis):
        direction = recommendation or "complementar fatos, documentos e recorte jurídico antes de qualquer conclusão"
        return (
            "Caso com dados insuficientes para prognóstico confiável. "
            f"Nível de risco atual: {risk_label}. "
            f"Direcionamento: {direction}."
        )

    label = str(viability.get("label", "") or "").lower()
    probability = int(float(viability.get("probability", 0) or 0) * 100)

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
        f"{status.capitalize()}. "
        f"Nível de risco: {risk_label}. "
        f"Direcionamento: {direction}. "
        "Avaliação estratégica qualitativa, condicionada à prova documental, cálculo atualizado e revisão profissional antes do protocolo."
    )


def generate_decision(analysis: Dict, viability: Dict) -> Dict:
    """
    Consolida análise técnica + viabilidade estratégica
    e gera decisão executiva final em linguagem premium.
    """
    recommendation = str(viability.get("recommendation", "") or "").strip()
    complexity = str(viability.get("complexity", "") or "").strip()
    estimated_time = str(viability.get("estimated_time", "") or "").strip()

    if _is_insufficient_data(viability, analysis):
        return {
            "final_status": "DADOS INSUFICIENTES",
            "confidence_level": None,
            "probability_percent": None,
            "score": None,
            "executive_recommendation": recommendation or "Complementar dados antes de qualquer conclusão executiva",
            "estimated_complexity": complexity or "Indefinida por insuficiência de dados",
            "complexity": complexity or "Indefinida por insuficiência de dados",
            "estimated_time": "Depende da complexidade, da fase processual, da prova disponível e do juízo competente.",
            "executive_summary": build_executive_summary(viability, analysis),
        }

    score = float(viability.get("score", 0) or 0)
    probability = float(viability.get("probability", 0) or 0)
    label = str(viability.get("label", "") or "").strip().lower()

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
    probability_percent = int(round(probability * 100))

    return {
        "final_status": final_status,
        "confidence_level": confidence_level,
        "probability_percent": probability_percent,
        "score": round(score, 2),
        "executive_recommendation": recommendation or "Sem recomendação executiva definida",
        "estimated_complexity": complexity or "Indefinida",
        "complexity": complexity or "Indefinida",
        "estimated_time": "Depende da complexidade, da fase processual, da prova disponível e do juízo competente.",
        "executive_summary": build_executive_summary(viability, analysis),
    }
