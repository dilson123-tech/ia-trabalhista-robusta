from typing import Dict

def strategic_diagnosis(analysis: Dict) -> Dict:
    """
    Motor estratégico híbrido:
    - Parte determinística (regras claras)
    - Estrutura preparada para IA futura
    """

    risk_level = analysis.get("risk_level", "medium")

    # Base determinística simples (vamos evoluir)
    if risk_level == "low":
        success_probability = 0.80
        complexity = "baixa"
        financial_risk = "baixo"
    elif risk_level == "medium":
        success_probability = 0.60
        complexity = "moderada"
        financial_risk = "medio"
    else:
        success_probability = 0.40
        complexity = "alta"
        financial_risk = "alto"

    return {
        "success_probability": success_probability,
        "complexity": complexity,
        "financial_risk": financial_risk,
        "recommended_strategy": "Reforçar provas documentais e preparar testemunhas.",
        "critical_points": analysis.get("issues", []),
        "strong_points": ["Estrutura contratual existente", "Possível vínculo comprovável"]
    }
