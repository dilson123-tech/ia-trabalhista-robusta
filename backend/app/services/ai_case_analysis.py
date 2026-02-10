from __future__ import annotations

from typing import Any


def analyze_case(case_number: str, title: str, description: str | None) -> dict[str, Any]:
    """
    Análise inicial do processo (stub IA).
    Regras simples agora, LLM depois.
    """

    text = f"{title} {description or ''}".lower()

    issues = []
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
        f"Processo {case_number} analisado automaticamente. "
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
    }
