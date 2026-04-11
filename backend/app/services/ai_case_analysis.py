from __future__ import annotations

from datetime import date
import logging
from typing import Any

from app.core.settings import settings
from app.services.llm_client import LLMClientError, request_structured_analysis

logger = logging.getLogger(__name__)


def _combined_analysis_text(summary: str, issues: list[str], next_steps: list[str]) -> str:
    return " ".join([summary, *issues, *next_steps]).lower()


def _coerce_risk_level(summary: str, issues: list[str], next_steps: list[str], risk_level: str) -> str:
    combined = _combined_analysis_text(summary, issues, next_steps)

    high_fragility_terms = [
        "ausência de prova documental",
        "falta de prova documental",
        "fragilidade probatória",
        "ônus da prova não cumprido",
        "ônus da prova nao cumprido",
        "sentença de improcedência baseada na ausência de prova",
        "sentenca de improcedencia baseada na ausencia de prova",
        "improcedência por ausência de prova",
        "improcedencia por ausencia de prova",
        "ausência de testemunhas",
        "ausencia de testemunhas",
        "falta de datas",
        "faltam datas",
        "não há datas",
        "nao ha datas",
        "não há valores detalhados",
        "nao ha valores detalhados",
        "impossibilidade de fundamentar reflexos",
        "dependência probatória",
        "dependencia probatoria",
    ]

    medium_fragility_terms = [
        "risco prescricional",
        "prescrição",
        "prescricao",
        "impossibilidade de cálculo",
        "impossibilidade de calculo",
        "impede apuração",
        "impede apuracao",
        "impede cálculo",
        "impede calculo",
        "sem documentos",
        "sem testemunhas",
        "prova testemunhal",
        "produção de prova",
        "producao de prova",
        "liquidação",
        "liquidacao",
    ]

    high_hits = sum(1 for term in high_fragility_terms if term in combined)
    medium_hits = sum(1 for term in medium_fragility_terms if term in combined)

    if risk_level == "low":
        if high_hits >= 3:
            return "high"
        if high_hits >= 2 or medium_hits >= 2:
            return "medium"

    if risk_level == "medium":
        if high_hits >= 4 or (high_hits >= 2 and medium_hits >= 3):
            return "high"

    return risk_level



def _assert_area_coherence(legal_area: str, summary: str, issues: list[str], next_steps: list[str]) -> None:
    normalized_area = (legal_area or "trabalhista").strip().lower()
    if normalized_area == "trabalhista":
        return

    combined = " ".join([summary, *issues, *next_steps]).lower()
    forbidden_terms = [
        "trabalhista",
        "reclamação trabalhista",
        "reclamacao trabalhista",
        "justiça do trabalho",
        "justica do trabalho",
        "vínculo empregatício",
        "vinculo empregaticio",
        "vínculo de emprego",
        "vinculo de emprego",
        "empregador",
        "contrato de trabalho",
        "fgts",
        "ctps",
        "holerite",
        "holerites",
        "insalubridade",
        "prescrição bienal",
        "prescricao bienal",
        "quinquenal",
    ]
    hits = sorted({term for term in forbidden_terms if term in combined})
    if hits:
        raise LLMClientError(
            f"contaminação de área detectada para '{normalized_area}': {', '.join(hits[:6])}"
        )


def _fallback_analysis(
    case_number: str,
    title: str,
    description: str | None,
    legal_area: str = "trabalhista",
    action_type: str | None = None,
) -> dict[str, Any]:
    normalized_area = (legal_area or "trabalhista").strip().lower()
    text = f"{title} {description or ''}".lower()

    issues: list[str] = []
    risk = "low"

    if normalized_area == "trabalhista":
        if "fgts" in text:
            issues.append("Possível ausência de recolhimento de FGTS")
            risk = "medium"

        if "verbas rescisórias" in text or "rescis" in text:
            issues.append("Discussão sobre verbas rescisórias")
            risk = "medium"

        if "horas extras" in text:
            issues.append("Pedido de horas extras")
            risk = "high"

        if len(issues) < 2:
            issues.append("Necessária análise documental detalhada para identificar a controvérsia principal")
            issues.append("Necessário verificar enquadramento jurídico e maturidade probatória do caso")

        next_steps = [
            "Analisar documentos do contrato de trabalho",
            "Verificar documentos rescisórios e comprovantes",
            "Estruturar linha do tempo dos fatos e provas disponíveis",
        ]

    elif normalized_area == "civil_ambiental":
        if any(term in text for term in ["poeira", "cimento", "poluição", "poluicao", "ruído", "ruido", "barulho"]):
            issues.append("Há indícios de interferência nociva compatível com tutela inibitória, obrigação de fazer/não fazer e prova técnica ambiental/acústica")
            risk = "medium"

        if any(term in text for term in ["idosa", "pulmonar", "saúde", "saude"]):
            issues.append("A presença de pessoa idosa e a alegação de comprometimento respiratório reforçam urgência e necessidade de prova médica")
            risk = "medium"

        if any(term in text for term in ["notificação", "notificacao", "extrajudicial"]):
            issues.append("A tentativa prévia extrajudicial pode fortalecer a narrativa de omissão da ré, desde que comprovada documentalmente")
            risk = "medium"

        if len(issues) < 2:
            issues.append("Necessária análise específica de direito de vizinhança, tutela de urgência e responsabilidade civil ambiental")
            issues.append("Necessário consolidar fatos, documentos, prova médica e prova técnica antes de conclusão definitiva")

        next_steps = [
            "Organizar cronologia objetiva dos fatos, da perturbação e das tentativas extrajudiciais já realizadas",
            "Reunir prova visual, médica e técnica mínima sobre poeira, ruído, saúde da autora e obstrução da via",
            "Estruturar estratégia de obrigação de fazer/não fazer com tutela de urgência e eventual pedido indenizatório compatível com a prova disponível",
        ]

    else:
        if any(term in text for term in ["dano moral", "danos morais", "indenização", "indenizacao"]):
            issues.append("Há indicativo de pretensão indenizatória dependente de demonstração do dano e do nexo causal")
            risk = "medium"

        if any(term in text for term in ["urgência", "urgencia", "liminar", "tutela"]):
            issues.append("Há elementos para avaliar tutela de urgência, condicionada à probabilidade do direito e ao perigo de dano")
            risk = "medium"

        if len(issues) < 2:
            issues.append("Necessária análise jurídica específica da controvérsia conforme a área informada")
            issues.append("Necessário consolidar fatos, documentos e estratégia processual antes de conclusão técnica")

        next_steps = [
            "Organizar linha do tempo dos fatos e das provas disponíveis",
            "Conferir documentos essenciais, notificações e registros relacionados à controvérsia",
            "Definir estratégia processual compatível com a área jurídica informada e com o tipo de ação pretendido",
        ]

    summary = (
        f"Processo {case_number} analisado automaticamente em modo de contingência, "
        f"considerando a área jurídica '{normalized_area}'"
    )
    if action_type:
        summary += f" e o tipo de ação '{action_type}'."
    else:
        summary += "."

    summary += f" Foram identificados {len(issues)} ponto(s) relevante(s)."

    return {
        "summary": summary,
        "risk_level": risk,
        "issues": issues[:6],
        "next_steps": next_steps[:5],
        "analysis_source": "fallback",
        "case_number": case_number,
        "legal_area": normalized_area,
        "action_type": action_type,
    }



def _build_prompt(
    case_number: str,
    title: str,
    description: str | None,
    legal_area: str = "trabalhista",
    action_type: str | None = None,
) -> str:
    today = date.today().isoformat()
    normalized_area = (legal_area or "trabalhista").strip().lower()
    action_label = action_type or "Não informado"

    return f"""
    Você é um advogado brasileiro sênior, especializado na área jurídica informada abaixo, com atuação estratégica pré-processual e processual.

    Analise o caso abaixo com rigor técnico. Use apenas os fatos fornecidos. Não invente fatos.
    Se houver falta de informação, deixe isso claro no resumo, nos pontos relevantes e nos próximos passos.
    Considere como data atual da análise: {today}.

    CASO:
    - Área jurídica: {normalized_area}
    - Tipo de ação/medida pretendida: {action_label}
    - Número/identificador: {case_number}
    - Título: {title}
    - Descrição: {description or "Sem descrição fornecida."}

    Retorne exclusivamente um JSON válido, sem markdown, sem comentários e sem texto fora do JSON.

    Formato obrigatório:
    {{
      "summary": "resumo técnico objetivo em português",
      "risk_level": "low|medium|high",
      "issues": ["lista objetiva de pontos jurídicos relevantes"],
      "next_steps": ["lista objetiva de próximos passos recomendados"]
    }}

    Regras obrigatórias:
    - "risk_level" deve ser exatamente "low", "medium" ou "high".
    - "issues" deve ter de 2 a 6 itens.
    - "next_steps" deve ter de 2 a 5 itens.
    - O conteúdo deve variar conforme os fatos do caso.
    - A área jurídica informada é mandatória e deve prevalecer sobre inferências soltas do texto.
    - Quando a área indicada NÃO for trabalhista, é proibido mencionar ou pressupor: reclamação trabalhista, Justiça do Trabalho, vínculo empregatício, empregador, FGTS, CTPS, insalubridade, contrato de trabalho, prescrição bienal trabalhista ou créditos trabalhistas.
    - Se a área for civil_ambiental, priorizar direito de vizinhança, obrigação de fazer/não fazer, tutela de urgência, responsabilidade civil, dano moral, prova ambiental/acústica/médica e proteção à saúde/sossego/segurança.
    - O resumo deve indicar, quando cabível, se há direito material aparentemente forte, dependência probatória, risco prescricional/decadencial ou necessidade de cálculo.
    - Não usar linguagem vaga sem explicar o motivo técnico.
    - Não inventar documentos, datas, testemunhas ou fatos não descritos.
    - Quando faltarem datas, documentos, medições, laudos, valores ou prova técnica, isso deve aparecer como limitação objetiva da análise.
    - Quando houver pedido de tutela de urgência, avaliar tecnicamente probabilidade do direito e perigo de dano.
    - Se a área for trabalhista, aplicar corretamente as distinções técnicas próprias dessa área, inclusive prescrição bienal quando pertinente.
    - Se a resposta violar a área indicada, ela será descartada.
    """.strip()



def _normalize_analysis(
    payload: dict[str, Any],
    case_number: str,
    legal_area: str = "trabalhista",
    action_type: str | None = None,
) -> dict[str, Any]:
    summary = str(payload.get("summary") or "").strip()
    risk_level = str(payload.get("risk_level") or "").strip().lower()
    issues = payload.get("issues") or []
    next_steps = payload.get("next_steps") or []

    if risk_level not in {"low", "medium", "high"}:
        raise LLMClientError(f"risk_level inválido retornado pelo modelo: {risk_level}")

    if not summary:
        raise LLMClientError("summary vazio retornado pelo modelo")

    if not isinstance(issues, list) or not all(isinstance(item, str) and item.strip() for item in issues):
        raise LLMClientError("issues inválido retornado pelo modelo")

    if not isinstance(next_steps, list) or not all(isinstance(item, str) and item.strip() for item in next_steps):
        raise LLMClientError("next_steps inválido retornado pelo modelo")

    normalized_issues = [str(item).strip() for item in issues][:6]
    normalized_steps = [str(item).strip() for item in next_steps][:5]

    if len(normalized_issues) < 2:
        raise LLMClientError("issues insuficiente retornado pelo modelo")

    if len(normalized_steps) < 2:
        raise LLMClientError("next_steps insuficiente retornado pelo modelo")

    _assert_area_coherence(
        legal_area=legal_area,
        summary=summary,
        issues=normalized_issues,
        next_steps=normalized_steps,
    )

    coerced_risk_level = _coerce_risk_level(
        summary=summary,
        issues=normalized_issues,
        next_steps=normalized_steps,
        risk_level=risk_level,
    )

    return {
        "summary": summary,
        "risk_level": coerced_risk_level,
        "issues": normalized_issues,
        "next_steps": normalized_steps,
        "analysis_source": "llm",
        "case_number": case_number,
        "legal_area": (legal_area or "trabalhista").strip().lower(),
        "action_type": action_type,
    }



def analyze_case(
    case_number: str,
    title: str,
    description: str | None,
    legal_area: str = "trabalhista",
    action_type: str | None = None,
) -> dict[str, Any]:
    llm_enabled = bool(getattr(settings, "LLM_ANALYSIS_ENABLED", False))

    if not llm_enabled:
        return _fallback_analysis(
            case_number=case_number,
            title=title,
            description=description,
            legal_area=legal_area,
            action_type=action_type,
        )

    prompt = _build_prompt(
        case_number=case_number,
        title=title,
        description=description,
        legal_area=legal_area,
        action_type=action_type,
    )

    try:
        payload = request_structured_analysis(prompt)
        return _normalize_analysis(
            payload,
            case_number=case_number,
            legal_area=legal_area,
            action_type=action_type,
        )
    except Exception as exc:
        logger.exception("ai_case_analysis fallback acionado para case_number=%s: %s", case_number, exc)
        return _fallback_analysis(
            case_number=case_number,
            title=title,
            description=description,
            legal_area=legal_area,
            action_type=action_type,
        )
