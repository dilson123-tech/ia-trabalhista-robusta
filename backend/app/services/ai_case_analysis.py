from __future__ import annotations

from typing import Any

from app.core.settings import settings
from app.services.llm_client import LLMClientError, request_structured_analysis


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

    summary = (
        f"Processo {case_number} analisado automaticamente em modo de contingência. "
        f"Foram identificados {len(issues)} ponto(s) relevante(s)."
    )

    next_steps = [
        "Analisar documentos do contrato de trabalho",
        "Verificar extratos de FGTS",
        "Conferir TRCT e recibos",
    ]

    return {
        "summary": summary,
        "risk_level": risk,
        "issues": issues,
        "next_steps": next_steps,
        "analysis_source": "fallback",
    }


def _build_prompt(case_number: str, title: str, description: str | None) -> str:
    return f"""
Você é um advogado trabalhista sênior no Brasil, especializado em análise estratégica pré-processual e processual.

Analise o caso abaixo com rigor técnico. Use apenas os fatos fornecidos. Não invente fatos.
Se houver falta de informação, deixe isso claro nas issues, no resumo e nos próximos passos.

CASO:
- Número/identificador: {case_number}
- Título: {title}
- Descrição: {description or "Sem descrição fornecida."}

Retorne exclusivamente um JSON válido, sem markdown, sem comentários, sem texto fora do JSON.

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
- Em caso de verbas rescisórias claras e documentação aparentemente favorável ao trabalhador, a análise pode apontar risco menor para a tese do reclamante.
- Em caso de múltiplos pedidos, falta de documentos, discussão de jornada, vínculo não registrado ou controvérsia probatória forte, a análise deve refletir maior risco/complexidade.
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

    return {
        "summary": summary,
        "risk_level": risk_level,
        "issues": [item.strip() for item in issues],
        "next_steps": [item.strip() for item in next_steps],
        "analysis_source": "llm",
        "case_number": case_number,
    }


def analyze_case(case_number: str, title: str, description: str | None) -> dict[str, Any]:
    """
    Análise jurídica inicial do caso.
    Quando LLM_ANALYSIS_ENABLED=true, usa provider real.
    Em contingência, usa fallback local.
    """

    if not settings.LLM_ANALYSIS_ENABLED:
        return _fallback_analysis(case_number, title, description)

    prompt = _build_prompt(case_number, title, description)

    try:
        payload = request_structured_analysis(prompt)
        return _normalize_analysis(payload, case_number)
    except Exception:
        return _fallback_analysis(case_number, title, description)
