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
        "preliminar": "Preliminar",
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
        "DADOS INSUFICIENTES": "caso com dados insuficientes para prognóstico confiável",
    }
    return mapping.get(normalized, "caso em avaliação estratégica")


def _is_insufficient_data(analysis: Dict, viability: Dict, decision: Dict) -> bool:
    viability_dimensions = viability.get("dimensions") or {}
    viability_label = str(viability.get("label", "") or "").strip().lower()
    final_status = str(decision.get("final_status", "") or "").strip().upper()
    analysis_issues = " ".join(analysis.get("issues", []) or []).lower()

    probability = viability.get("probability")
    score = viability.get("score")

    if viability_dimensions.get("insufficient_data") is True:
        return True
    if probability is None or score is None:
        return True
    if "dados insuficientes" in viability_label:
        return True
    if final_status == "DADOS INSUFICIENTES":
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


def generate_executive_summary(
    analysis: Dict,
    viability: Dict,
    decision: Dict,
) -> Dict:
    """
    Consolida análise técnica + viabilidade + decisão final
    e gera um resumo executivo curto, direto e comercial.
    """
    risk_level = _risk_label(analysis.get("risk_level", "medium"))
    final_status = decision.get("final_status", "INDEFINIDO")
    confidence = decision.get("confidence_level")
    recommendation = viability.get("recommendation", "Sem recomendação estratégica definida.")

    if _is_insufficient_data(analysis, viability, decision):
        complexity = _complexity_label(viability.get("complexity", "Indefinida por insuficiência de dados"))
        estimated_time = "Depende da complexidade, da fase processual, da prova disponível e do juízo competente."
        executive_text = (
            "Caso com dados insuficientes para prognóstico confiável. "
            f"Nível de risco: {risk_level}. "
            f"Complexidade: {complexity}. "
            f"Perspectiva de tramitação: Depende da complexidade, da fase processual, da prova disponível e do juízo competente.. "
            f"Direcionamento: {recommendation}."
        )
        return {
            "executive_summary": executive_text,
            "final_status": "DADOS INSUFICIENTES",
            "confidence_level": None,
            "probability_percent": None,
            "score": None,
            "complexity": complexity,
            "estimated_time": estimated_time,
        }

    score = viability.get("score", 0)
    probability = viability.get("probability", 0) or 0
    complexity = _complexity_label(viability.get("complexity", "Indefinida"))
    estimated_time = "Depende da complexidade, da fase processual, da prova disponível e do juízo competente."
    status_phrase = _status_phrase(final_status)
    probability_percent = int(round(float(probability) * 100))

    executive_text = (
        f"{status_phrase.capitalize()}. "
        f"Nível de risco: {risk_level}. "
        f"Complexidade: {complexity}. "
        f"Perspectiva de tramitação: Depende da complexidade, da fase processual, da prova disponível e do juízo competente. "
        f"Direcionamento: {recommendation}. "
        "Avaliação estratégica qualitativa, condicionada à prova documental, cálculo atualizado e revisão profissional antes do protocolo."
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
