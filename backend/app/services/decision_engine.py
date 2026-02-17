from typing import Dict


def generate_decision(analysis: Dict, viability: Dict) -> Dict:
    """
    Consolida análise técnica + viabilidade estratégica
    e gera decisão executiva final.
    """

    score = viability.get("score", 0)
    probability = viability.get("probability", 0)

    # Classificação final executiva
    if score >= 75:
        final_status = "FAVORÁVEL"
    elif score >= 55:
        final_status = "MODERADA"
    else:
        final_status = "ARRISCADA"

    confidence_level = round(probability * 100, 1)

    return {
        "final_status": final_status,
        "confidence_level": confidence_level,
        "executive_recommendation": viability.get("recommendation"),
        "estimated_complexity": viability.get("complexity"),
        "estimated_time": viability.get("estimated_time"),
    }
