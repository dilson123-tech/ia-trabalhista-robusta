from __future__ import annotations

import json
from typing import Any

import httpx

from app.core.settings import settings


class LLMClientError(RuntimeError):
    pass


def _build_url() -> str:
    if settings.LLM_BASE_URL:
        return settings.LLM_BASE_URL.rstrip("/")

    provider = (settings.LLM_PROVIDER or "").lower()
    if provider == "openai":
        return "https://api.openai.com/v1/responses"

    raise LLMClientError(f"Provider LLM não suportado: {settings.LLM_PROVIDER}")


def _build_headers() -> dict[str, str]:
    if not settings.LLM_API_KEY:
        raise LLMClientError("LLM_API_KEY não configurada.")

    provider = (settings.LLM_PROVIDER or "").lower()
    if provider == "openai":
        return {
            "Authorization": f"Bearer {settings.LLM_API_KEY}",
            "Content-Type": "application/json",
        }

    raise LLMClientError(f"Provider LLM não suportado: {settings.LLM_PROVIDER}")


def _extract_text_from_openai_response(data: dict[str, Any]) -> str:
    output = data.get("output", [])
    texts: list[str] = []

    for item in output:
        content = item.get("content", [])
        for block in content:
            if block.get("type") in {"output_text", "text"} and block.get("text"):
                texts.append(block["text"])

    text = "\n".join(t.strip() for t in texts if t and t.strip()).strip()
    if not text:
        raise LLMClientError("Resposta do provider não contém texto utilizável.")
    return text


def _extract_json_payload(raw_text: str) -> dict[str, Any]:
    raw_text = raw_text.strip()

    if raw_text.startswith("```"):
        parts = raw_text.split("```")
        candidates = [p.strip() for p in parts if p.strip() and not p.strip().lower().startswith("json")]
        if candidates:
            raw_text = candidates[0]

    start = raw_text.find("{")
    end = raw_text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise LLMClientError("Não foi possível localizar JSON válido na resposta do modelo.")

    candidate = raw_text[start:end + 1]
    try:
        return json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise LLMClientError(f"JSON inválido retornado pelo modelo: {exc}") from exc


def request_structured_analysis(prompt: str) -> dict[str, Any]:
    provider = (settings.LLM_PROVIDER or "").lower()

    if provider != "openai":
        raise LLMClientError(f"Provider LLM não suportado: {settings.LLM_PROVIDER}")

    payload = {
        "model": settings.LLM_MODEL,
        "input": prompt,
    }

    with httpx.Client(timeout=settings.LLM_TIMEOUT_SECONDS) as client:
        response = client.post(
            _build_url(),
            headers=_build_headers(),
            json=payload,
        )

    if response.status_code >= 400:
        raise LLMClientError(
            f"Falha na chamada LLM ({response.status_code}): {response.text[:500]}"
        )

    data = response.json()
    raw_text = _extract_text_from_openai_response(data)
    return _extract_json_payload(raw_text)
