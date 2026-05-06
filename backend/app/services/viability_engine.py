from typing import Dict


def _normalize_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.lower()
    if isinstance(value, list):
        return " ".join(str(item) for item in value).lower()
    return str(value).lower()


def _normalize_issue_list(values) -> list[str]:
    if not values:
        return []
    if isinstance(values, list):
        return [str(item).lower() for item in values]
    return [str(values).lower()]


def _has_substantive_issue_term(issues, term: str) -> bool:
    blocked_context_terms = [
        "liquidação",
        "cálculos",
        "quantificação",
        "reflexos",
        "honorários",
        "custas",
        "eventual procedência",
        "eventual reforma",
        "necessidade de cálculos",
        "apuração quantitativa",
    ]
    for issue in _normalize_issue_list(issues):
        if term not in issue:
            continue
        if any(blocked in issue for blocked in blocked_context_terms):
            continue
        return True
    return False


def _is_strong_collection_case(combined: str, risk_level: str) -> bool:
    """
    Detecta cobrança contratual documentalmente forte.

    Não promete êxito; apenas evita recomendação pessimista quando há sinais
    consistentes de contrato, saldo inadimplido, pagamento parcial,
    reconhecimento/notificação e baixo risco técnico.
    """
    risk = (risk_level or "").strip().lower()
    if risk not in {"low", "medium", "baixo", "medio", "médio"}:
        return False

    collection_terms = [
        "ação de cobrança",
        "cobrança contratual",
        "saldo inadimplido",
        "saldo principal inadimplido",
        "saldo líquido",
        "saldo remanescente",
    ]
    contract_terms = ["contrato assinado", "obrigação contratual", "relação contratual"]
    partial_payment_terms = ["pagamento parcial", "pagamentos efetuados", "parcelas adimplidas", "comprovantes de pagamento"]
    recognition_terms = ["reconhecimento de dívida", "reconhece a dívida", "notificação extrajudicial", "recebida sem quitação"]
    amount_terms = ["multa", "juros", "correção monetária", "planilha de cálculo"]

    return (
        any(term in combined for term in collection_terms)
        and any(term in combined for term in contract_terms)
        and any(term in combined for term in partial_payment_terms)
        and any(term in combined for term in recognition_terms)
        and any(term in combined for term in amount_terms)
    )


def calculate_viability(analysis: Dict) -> Dict:
    """
    Motor premium de viabilidade processual.

    Separa a leitura em três eixos:
    - força jurídica do direito
    - maturidade probatória
    - risco processual

    O objetivo é refletir melhor a realidade jurídica:
    caso bom com prova fraca não deve virar "caso ruim",
    mas sim "caso viável condicionado à prova".
    """
    summary = analysis.get("summary", "") or ""
    issues = analysis.get("issues", []) or []
    next_steps = analysis.get("next_steps", []) or []
    risk_level = str(analysis.get("risk_level", "medium")).lower()

    summary_text = _normalize_text(summary)
    issues_text = _normalize_text(issues)
    next_steps_text = _normalize_text(next_steps)

    combined = " ".join([
        summary_text,
        issues_text,
        next_steps_text,
    ])

    # 1) Força jurídica do direito material
    legal_terms = [
        "fgts",
        "verbas rescisórias",
        "dispensado sem justa causa",
        "não recebeu",
        "não recebimento",
        "ausência de pagamento",
        "inadimplemento",
        "multa de 40%",
        "saldo de salário",
        "13º proporcional",
        "férias proporcionais",
        "aviso prévio",
        "multa rescisória",
        "créditos trabalhistas",
        "direito às verbas rescisórias",
    ]
    context_sensitive_terms = {
        "fgts",
        "verbas rescisórias",
        "dispensado sem justa causa",
        "multa de 40%",
        "saldo de salário",
        "13º proporcional",
        "férias proporcionais",
        "aviso prévio",
        "multa rescisória",
        "créditos trabalhistas",
        "direito às verbas rescisórias",
    }

    legal_strength = 0
    for term in legal_terms:
        if term in context_sensitive_terms:
            if _has_substantive_issue_term(issues, term):
                legal_strength += 1
        elif term in issues_text:
            legal_strength += 1

    # 2) Maturidade probatória
    evidence_terms = [
        "falta de",
        "ausência de",
        "não informado",
        "não há informação",
        "sem documentos",
        "falta de comprovação documental",
        "impede quantificação",
        "impede cálculo",
        "extratos do fgts",
        "recibos",
        "trct",
        "holerites",
        "comprovantes de pagamento",
        "elementos probatórios",
    ]
    evidence_gaps = sum(1 for term in evidence_terms if term in combined)

    # 3) Risco processual
    process_risk_terms = [
        "prescrição",
        "decadência",
        "quitação",
        "pagamento parcial",
        "descontos",
        "homologação",
        "preclusão",
        "risco probatório",
        "risco processual",
    ]
    process_risk_hits = sum(1 for term in process_risk_terms if term in combined)

    insufficient_data_markers = (
        "dados insuficientes",
        "insuficiência de dados",
        "insuficiencia de dados",
        "sem vínculo",
        "sem vinculo",
        "sem vínculo empregatício",
        "sem vinculo empregaticio",
        "sem datas",
        "ausência de datas",
        "ausencia de datas",
        "sem documentos",
        "ausência de documentos",
        "ausencia de documentos",
        "falta de documentos",
        "sem base para calcular",
        "sem base para aferir",
        "sem base jurídica",
        "sem base juridica",
        "sem base factual",
    )

    insufficient_marker_hits = sum(1 for marker in insufficient_data_markers if marker in combined)
    insufficient_data = (
        evidence_gaps >= 4
        or (legal_strength == 0 and evidence_gaps >= 2)
        or insufficient_marker_hits >= 2
    )

    if insufficient_data:
        score = None
        probability = None
        label = "Dados insuficientes para estimativa"
        complexity = "Indefinida por insuficiência de dados"
        estimated_time = "Depende da complexidade, da fase processual, da prova disponível e do juízo competente."
        recommendation = (
            "Complementar fatos, documentos, datas e base mínima de prova antes de qualquer estimativa de viabilidade."
        )
    else:
        # Base por risco técnico: aqui mede complexidade/instabilidade,
        # mas não destrói automaticamente a viabilidade.
        risk_base_map = {
            "low": 68,
            "medium": 64,
            "high": 60,
        }
        score = risk_base_map.get(risk_level, 62)

        # Direito material forte empurra para cima.
        score += min(20, legal_strength * 3)

        # Lacunas probatórias reduzem, mas sem matar caso juridicamente bom.
        score -= min(18, evidence_gaps * 2)

        # Risco processual pesa mais que lacuna documental comum.
        score -= min(16, process_risk_hits * 3)

        score = max(0, min(100, score))
        probability = round(score / 100, 2)

        # Complexidade segue o risco técnico.
        if risk_level == "low":
            complexity = "Baixa"
        elif risk_level == "medium":
            complexity = "Média"
        else:
            complexity = "Alta"

        estimated_time = "Depende da complexidade, da fase processual, da prova disponível e do juízo competente."

        # Leitura premium: separa direito forte de prova fraca.
        if legal_strength >= 4 and evidence_gaps >= 3:
            label = "Viável com dependência probatória"
            recommendation = "Reforçar documentação e cálculo antes do ajuizamento"
        elif score >= 78:
            label = "Alta viabilidade estratégica"
            recommendation = "Prosseguir com ajuizamento e validação documental final"
        elif score >= 62:
            label = "Viabilidade moderada"
            recommendation = "Prosseguir com cautela, fortalecendo prova e estratégia"
        elif score >= 48:
            label = "Viabilidade condicionada à prova"
            recommendation = "Não ajuizar sem reforço probatório mínimo e revisão estratégica"
        else:
            label = "Baixa prontidão estratégica"
            recommendation = "Segurar ajuizamento e priorizar obtenção de provas e saneamento de riscos"

        if _is_strong_collection_case(combined, risk_level):
            score = max(score, 62)
            probability = round(score / 100, 2)
            label = "Viabilidade moderada com prova documental relevante"
            recommendation = (
                "Prosseguir com preparação do ajuizamento, após conferência documental, "
                "cálculo atualizado e validação profissional final"
            )

    return {
        "score": score,
        "probability": probability,
        "label": label,
        "complexity": complexity,
        "estimated_time": estimated_time,
        "recommendation": recommendation,
        "dimensions": {
            "legal_strength": legal_strength,
            "evidence_gaps": evidence_gaps,
            "process_risk": process_risk_hits,
            "insufficient_data": insufficient_data,
        },
    }
