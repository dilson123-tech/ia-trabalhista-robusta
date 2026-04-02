from typing import Dict


def _normalize_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.lower()
    if isinstance(value, list):
        return " ".join(str(item) for item in value).lower()
    return str(value).lower()


def calculate_viability(analysis: Dict) -> Dict:
    """
    Motor estratégico de viabilidade processual.

    Esta régua mede prontidão estratégica do caso com base em:
    - risco técnico informado pela análise
    - maturidade probatória/documental
    - sinais favoráveis ou críticos presentes no texto da análise

    Não representa verdade absoluta sobre êxito judicial.
    """
    risk_level = str(analysis.get("risk_level", "medium")).lower()
    issues = analysis.get("issues", []) or []
    next_steps = analysis.get("next_steps", []) or []
    summary = analysis.get("summary", "") or ""

    combined_text = " ".join(
        [
            _normalize_text(summary),
            _normalize_text(issues),
            _normalize_text(next_steps),
        ]
    )

    risk_score_map = {
        "low": 78,
        "medium": 66,
        "high": 52,
    }
    score = risk_score_map.get(risk_level, 62)

    issue_count = len(issues)

    # Penalidade mais suave: análise boa tende a listar vários pontos,
    # então contar issues de forma agressiva distorce o resultado.
    if issue_count >= 8:
        score -= 18
    elif issue_count >= 6:
        score -= 12
    elif issue_count >= 4:
        score -= 7
    elif issue_count >= 2:
        score -= 3

    favorable_terms = [
        "obrigação legal presumível",
        "inadimplência",
        "ausência de pagamento",
        "não recebimento correto",
        "dispensado sem justa causa",
        "verbas rescisórias",
        "fgts",
        "multa de 40%",
        "vínculo comprovável",
        "provas documentais",
    ]
    caution_terms = [
        "faltam elementos documentais",
        "prazo prescricional",
        "prescrição",
        "pagamento parcial",
        "quitação",
        "descontos",
        "homologação",
        "impedem cálculo",
        "avaliação plena",
        "ausência de informação",
    ]

    favorable_hits = sum(1 for term in favorable_terms if term in combined_text)
    caution_hits = sum(1 for term in caution_terms if term in combined_text)

    score += min(12, favorable_hits * 2)
    score -= min(15, caution_hits * 2)

    score = max(0, min(100, score))
    probability = round(score / 100, 2)

    if risk_level == "low":
        complexity = "Baixa"
        estimated_time = "6-12 meses"
    elif risk_level == "medium":
        complexity = "Média"
        estimated_time = "12-24 meses"
    else:
        complexity = "Alta"
        estimated_time = "24+ meses"

    if score >= 76:
        label = "Alta viabilidade estratégica"
        recommendation = "Prosseguir com ajuizamento, mantendo validação documental final"
    elif score >= 61:
        label = "Viabilidade moderada"
        recommendation = "Prosseguir com cautela, reforçando documentação e cálculo"
    elif score >= 46:
        label = "Viabilidade condicionada à prova"
        recommendation = "Não ajuizar sem reforço probatório mínimo e revisão estratégica"
    else:
        label = "Baixa prontidão estratégica"
        recommendation = "Segurar ajuizamento e priorizar obtenção de provas e saneamento de riscos"

    return {
        "score": score,
        "probability": probability,
        "label": label,
        "complexity": complexity,
        "estimated_time": estimated_time,
        "recommendation": recommendation,
    }
