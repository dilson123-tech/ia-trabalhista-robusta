from typing import Dict


def _normalize_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.lower()
    if isinstance(value, list):
        return " ".join(str(item) for item in value).lower()
    return str(value).lower()


def strategic_diagnosis(analysis: Dict) -> Dict:
    """
    Camada estratégica premium.

    Objetivo:
    transformar a análise técnica em orientação consultiva real,
    distinguindo:
    - força jurídica do caso
    - dependência probatória
    - risco processual
    - oportunidade de negociação
    - rota de execução recomendada
    """
    summary = analysis.get("summary", "") or ""
    issues = analysis.get("issues", []) or []
    next_steps = analysis.get("next_steps", []) or []
    risk_level = str(analysis.get("risk_level", "medium")).lower()

    combined = " ".join([
        _normalize_text(summary),
        _normalize_text(issues),
        _normalize_text(next_steps),
    ])

    strong_legal_terms = [
        "fgts",
        "verbas rescisórias",
        "dispensado sem justa causa",
        "não pagamento",
        "ausência de pagamento",
        "inadimplemento",
        "multa de 40%",
        "multa do art. 477",
        "aviso prévio",
        "13º proporcional",
        "férias proporcionais",
        "créditos trabalhistas",
    ]
    proof_gap_terms = [
        "falta de",
        "ausência de",
        "não há informação",
        "não informado",
        "recibos",
        "trct",
        "holerites",
        "extratos do fgts",
        "comprovantes de pagamento",
        "elementos probatórios",
        "impede cálculo",
        "impede quantificação",
    ]
    process_risk_terms = [
        "prescrição",
        "decadência",
        "quitação",
        "pagamento parcial",
        "descontos",
        "homologação",
        "preclusão",
        "risco processual",
        "risco probatório",
    ]
    negotiation_terms = [
        "notificar extrajudicialmente",
        "notificação extrajudicial",
        "acordo",
        "regularização",
        "prazo curto",
        "pagamento imediato",
    ]

    legal_strength = sum(1 for term in strong_legal_terms if term in combined)
    proof_gaps = sum(1 for term in proof_gap_terms if term in combined)
    process_risk_hits = sum(1 for term in process_risk_terms if term in combined)
    negotiation_hits = sum(1 for term in negotiation_terms if term in combined)

    if risk_level == "low":
        complexity = "baixa"
        base_probability = 0.78
        financial_risk = "baixo"
    elif risk_level == "medium":
        complexity = "moderada"
        base_probability = 0.64
        financial_risk = "medio"
    else:
        complexity = "alta"
        base_probability = 0.58
        financial_risk = "alto"

    probability = base_probability
    probability += min(0.12, legal_strength * 0.02)
    probability -= min(0.15, proof_gaps * 0.015)
    probability -= min(0.12, process_risk_hits * 0.025)
    probability = max(0.15, min(0.92, round(probability, 2)))

    strong_points = []
    if legal_strength >= 1:
        strong_points.append("Há indícios jurídicos concretos de pretensão material relevante")
    if "fgts" in combined:
        strong_points.append("O eixo de FGTS aparece como frente objetiva de cobrança e recomposição")
    if "verbas rescisórias" in combined:
        strong_points.append("A discussão de verbas rescisórias tende a favorecer abordagem de cobrança estruturada")
    if "dispensado sem justa causa" in combined:
        strong_points.append("A narrativa de dispensa sem justa causa fortalece a coerência dos pedidos rescisórios")
    if not strong_points:
        strong_points.append("Há necessidade de consolidação técnica dos fundamentos antes da tomada de decisão")

    critical_points = list(issues[:6]) if issues else [
        "A análise identificou necessidade de aprofundamento técnico e documental antes da decisão final"
    ]

    if legal_strength >= 4 and proof_gaps >= 3:
        positioning = "Caso juridicamente promissor, porém dependente de amadurecimento probatório antes do ajuizamento."
    elif probability >= 0.72:
        positioning = "Caso com posição estratégica favorável e boa condição para avanço estruturado."
    elif probability >= 0.55:
        positioning = "Caso com viabilidade moderada, exigindo cautela tática e reforço de instrução."
    else:
        positioning = "Caso sensível, com fragilidades relevantes que recomendam contenção estratégica inicial."

    if negotiation_hits >= 1 or legal_strength >= 3:
        negotiation_opportunity = (
            "Há espaço concreto para tentativa de composição extrajudicial, "
            "especialmente se acompanhada de cálculo preliminar e notificação formal."
        )
    else:
        negotiation_opportunity = (
            "A oportunidade de negociação existe, mas depende de melhor consolidação "
            "dos fatos e da documentação mínima de suporte."
        )

    if proof_gaps >= 4 and process_risk_hits >= 2:
        recommended_strategy = (
            "Priorizar saneamento probatório imediato, validar risco prescricional "
            "e somente avançar para ajuizamento após fechamento da documentação crítica."
        )
    elif legal_strength >= 4 and proof_gaps >= 3:
        recommended_strategy = (
            "Adotar estratégia em duas etapas: tentativa extrajudicial curta com cálculo "
            "preliminar e, na ausência de resposta útil, ajuizamento já instruído com prova mínima."
        )
    elif probability >= 0.72:
        recommended_strategy = (
            "Prosseguir com preparação de ajuizamento, mantendo revisão documental final "
            "e definição objetiva dos pedidos economicamente mais relevantes."
        )
    elif probability >= 0.55:
        recommended_strategy = (
            "Prosseguir com cautela estratégica, reforçando documentação, cálculo e "
            "linha do tempo dos fatos antes da decisão final de litigar."
        )
    else:
        recommended_strategy = (
            "Segurar avanço litigioso imediato e concentrar esforços em prova, "
            "diagnóstico de risco e definição mais precisa da tese."
        )

    if process_risk_hits >= 2:
        risk_alerts = (
            "Há alertas processuais relevantes, com destaque para prescrição, quitação "
            "ou outras variáveis que podem reduzir o espaço útil da pretensão."
        )
    elif proof_gaps >= 3:
        risk_alerts = (
            "O principal alerta estratégico está na insuficiência documental, que pode "
            "enfraquecer quantificação, narrativa e previsibilidade de resultado."
        )
    else:
        risk_alerts = (
            "Os riscos identificados são administráveis, desde que a execução siga com "
            "documentação mínima, cálculo consistente e validação profissional final."
        )

    if proof_gaps >= 3:
        execution_plan = [
            "Consolidar imediatamente documentos essenciais, cronologia dos fatos e base mínima de prova.",
            "Fechar cálculo preliminar dos pedidos e identificar eventuais lacunas de quantificação.",
            "Avaliar tentativa extrajudicial curta e documentada antes do litígio, quando isso aumentar pressão negocial.",
            "Se persistir inadimplemento ou resistência, estruturar ajuizamento com narrativa limpa e prova organizada.",
        ]
    else:
        execution_plan = [
            "Validar coerência final entre fatos, pedidos e documentação já reunida.",
            "Fechar cálculo preliminar e priorizar os pedidos com maior aderência probatória.",
            "Definir estratégia de negociação ou ajuizamento conforme resposta da parte contrária.",
            "Executar a medida principal com monitoramento de risco e revisão profissional final.",
        ]

    return {
        "success_probability": probability,
        "complexity": complexity,
        "financial_risk": financial_risk,
        "positioning": positioning,
        "recommended_strategy": recommended_strategy,
        "negotiation_opportunity": negotiation_opportunity,
        "risk_alerts": risk_alerts,
        "execution_plan": execution_plan,
        "critical_points": critical_points,
        "strong_points": strong_points,
    }
