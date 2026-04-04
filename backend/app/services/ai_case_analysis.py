from __future__ import annotations

from typing import Any

from app.core.settings import settings
from app.services.llm_client import LLMClientError, request_structured_analysis


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


def _fallback_analysis(case_number: str, title: str, description: str | None) -> dict[str, Any]:
    text = f"{title} {description or ''}".lower()

    issues: list[str] = []
    risk = "low"

    if "fgts" in text:
        issues.append("Possível ausência de recolhimento de FGTS")
        risk = "medium"

    if "verbas rescisórias" in text or "rescis" in text:
        issues.append("Discussão sobre verbas rescisórias")
        risk = "medium"

    if "horas extras" in text:
        issues.append("Pedido de horas extras")
        risk = "high"

    if not issues:
        issues.append("Necessária análise documental detalhada para identificar a controvérsia principal")

    summary = (
        f"Processo {case_number} analisado automaticamente em modo de contingência. "
        f"Foram identificados {len(issues)} ponto(s) relevante(s)."
    )

    next_steps = [
        "Analisar documentos do contrato de trabalho",
        "Verificar documentos rescisórios e comprovantes",
        "Estruturar linha do tempo dos fatos e provas disponíveis",
    ]

    return {
        "summary": summary,
        "risk_level": risk,
        "issues": issues,
        "next_steps": next_steps,
        "analysis_source": "fallback",
        "case_number": case_number,
    }


def _build_prompt(case_number: str, title: str, description: str | None) -> str:
    return f"""
Você é um advogado trabalhista sênior no Brasil, especializado em análise estratégica pré-processual e processual.

Analise o caso abaixo com rigor técnico. Use apenas os fatos fornecidos. Não invente fatos.
Se houver falta de informação, deixe isso claro no resumo, nos pontos relevantes e nos próximos passos.

CASO:
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
- O resumo deve indicar, quando cabível, se há direito material aparentemente forte, dependência probatória, risco prescricional ou necessidade de cálculo.
- Não usar linguagem vaga como "pode haver algo" sem explicar o motivo técnico.
- Não inventar documentos, datas, testemunhas ou fatos não descritos.
- Quando a narrativa indicar verbas rescisórias, FGTS, aviso prévio, 13º, férias ou multa, tratar isso com precisão jurídica.
- Quando faltarem datas, documentos ou valores, isso deve aparecer como limitação objetiva da análise.
""".strip()


def _normalize_analysis(payload: dict[str, Any], case_number: str) -> dict[str, Any]:
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
    }


def analyze_case(case_number: str, title: str, description: str | None) -> dict[str, Any]:
    llm_enabled = bool(getattr(settings, "LLM_ANALYSIS_ENABLED", False))

    if not llm_enabled:
        return _fallback_analysis(case_number=case_number, title=title, description=description)

    prompt = _build_prompt(case_number=case_number, title=title, description=description)

    try:
        payload = request_structured_analysis(prompt)
        return _normalize_analysis(payload, case_number=case_number)
    except Exception:
        return _fallback_analysis(case_number=case_number, title=title, description=description)
