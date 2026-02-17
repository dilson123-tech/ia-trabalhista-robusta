from typing import Dict


def calculate_viability(analysis: Dict) -> Dict:
    """
    Motor estratégico de viabilidade processual.
    Gera score, probabilidade, complexidade e recomendação.
    """

    risk_level = analysis.get("risk_level", "medium")
    issues = analysis.get("issues", [])
    next_steps = analysis.get("next_steps", [])

    # Base score
    score_map = {
        "low": 85,
        "medium": 65,
        "high": 40,
    }

    base_score = score_map.get(risk_level, 60)

    # Penalidade por muitos problemas detectados
    penalty = len(issues) * 3
    score = max(0, min(100, base_score - penalty))

    probability = round(score / 100, 2)

    # Classificação estratégica
    if score >= 75:
        label = "Alta chance de êxito"
        recommendation = "Recomendado entrar com a ação"
    elif score >= 55:
        label = "Chance moderada"
        recommendation = "Entrar com cautela estratégica"
    else:
        label = "Baixa probabilidade"
        recommendation = "Reavaliar provas e estratégia antes de ajuizar"

    # Complexidade baseada em risco
    if risk_level == "low":
        complexity = "Baixa"
        estimated_time = "6-12 meses"
    elif risk_level == "medium":
        complexity = "Média"
        estimated_time = "12-24 meses"
    else:
        complexity = "Alta"
        estimated_time = "24+ meses"

    return {
        "score": score,
        "probability": probability,
        "label": label,
        "complexity": complexity,
        "estimated_time": estimated_time,
        "recommendation": recommendation,
    }
