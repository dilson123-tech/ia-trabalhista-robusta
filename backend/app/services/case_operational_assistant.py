from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.api.v1.routes.cases import _build_case_operational_context
from app.models import Case
from app.services.llm_client import LLMClientError, request_structured_analysis


DESTINATION_LABELS = {
    "linha_do_tempo": "Linha do tempo",
    "checklist": "Checklist de provas",
    "anexos": "Anexos/provas",
    "testemunhas": "Testemunhas/depoentes",
    "dossie": "Dossiê interno",
    "analise": "Análise do caso",
    "editor_minuta": "Editor/minuta",
    "contato_cliente": "Cliente/WhatsApp",
}


def _clean_text(value: Any, limit: int = 1200) -> str:
    text = str(value or "").strip()
    text = " ".join(text.split())
    return text[:limit]


def _as_list(value: Any, limit: int = 8) -> list[str]:
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for item in value:
        text = _clean_text(item, limit=500)
        if text:
            items.append(text)
        if len(items) >= limit:
            break
    return items


def _load_timeline_items(db: Session, case: Case, current_user) -> list[dict[str, Any]]:
    try:
        from app.models.case_timeline import CaseTimelineItem
    except Exception:
        return []

    try:
        rows = (
            db.query(CaseTimelineItem)
            .filter(
                CaseTimelineItem.tenant_id == current_user["tenant_id"],
                CaseTimelineItem.case_id == case.id,
            )
            .order_by(
                CaseTimelineItem.sort_order.asc(),
                CaseTimelineItem.created_at.asc(),
                CaseTimelineItem.id.asc(),
            )
            .limit(20)
            .all()
        )
    except Exception:
        return []

    return [
        {
            "event_date": _clean_text(getattr(row, "event_date", ""), 120),
            "title": _clean_text(getattr(row, "title", ""), 240),
            "description": _clean_text(getattr(row, "description", ""), 500),
            "related_evidence": _clean_text(getattr(row, "related_evidence", ""), 240),
            "related_witness": _clean_text(getattr(row, "related_witness", ""), 240),
            "pending_note": _clean_text(getattr(row, "pending_note", ""), 300),
            "sort_order": getattr(row, "sort_order", 0),
        }
        for row in rows
    ]


def _suggestion(destination: str, label: str, suggested_text: str, reason: str, priority: str = "normal") -> dict[str, str]:
    return {
        "destination": destination,
        "label": label,
        "suggested_text": _clean_text(suggested_text, 900),
        "reason": _clean_text(reason, 500),
        "priority": priority,
    }


def _fallback_response(case: Case, message: str, context: dict[str, Any], timeline: list[dict[str, Any]]) -> dict[str, Any]:
    text = _clean_text(message, 2500)
    lowered = text.lower()

    suggestions: list[dict[str, str]] = []

    has_fact = any(
        marker in lowered
        for marker in (
            "aconteceu",
            "ocorreu",
            "fato",
            "evento",
            "data",
            "dia ",
            "quando",
            "antes",
            "depois",
            "pagou",
            "pagamento",
            "audiência",
            "audiencia",
            "contratou",
            "demitiu",
            "dispensou",
            "comprou",
            "vendeu",
            "negou",
            "recusou",
            "sumiu",
            "furto",
            "roubo",
            "ameaça",
            "ameaca",
            "agressão",
            "agressao",
            "acidente",
            "doença",
            "doenca",
            "benefício",
            "beneficio",
            "inss",
            "cliente informou",
            "cliente disse",
        )
    )
    has_document = any(
        marker in lowered
        for marker in (
            "bo",
            "boletim",
            "contrato",
            "comprovante",
            "nota fiscal",
            "print",
            "foto",
            "imagem",
            "áudio",
            "audio",
            "vídeo",
            "video",
            "documento",
            "seguro",
            "laudo",
            "atestado",
            "receita",
            "exame",
            "holerite",
            "contracheque",
            "ctps",
            "rescisão",
            "rescisao",
            "termo",
            "declaração",
            "declaracao",
            "sentença",
            "sentenca",
            "decisão",
            "decisao",
            "notificação",
            "notificacao",
            "mensagem",
            "whatsapp",
            "email",
            "e-mail",
        )
    )
    has_person = any(
        marker in lowered
        for marker in (
            "testemunha",
            "depoente",
            "viu",
            "presenciou",
            "confirmou",
            "sabe",
            "relatou",
            "declarou",
            "cliente falou",
            "cliente disse",
            "pessoa",
            "parte",
            "autor",
            "réu",
            "reu",
            "empregado",
            "empregador",
            "consumidor",
            "fornecedor",
            "médico",
            "medico",
            "perito",
            "servidor",
            "fiscal",
            "motorista",
            "condutor",
        )
    )

    if has_fact or not suggestions:
        suggestions.append(
            _suggestion(
                "linha_do_tempo",
                "Organizar como fato do caso",
                text,
                "A informação parece narrar um acontecimento relevante e deve ser organizada em ordem cronológica.",
                "alta" if has_fact else "normal",
            )
        )

    if has_document:
        suggestions.append(
            _suggestion(
                "checklist",
                "Criar ou revisar pendência probatória",
                "Conferir/anexar documento mencionado: contrato, comprovante, print, foto, áudio, vídeo, laudo, BO, decisão, notificação, mensagem ou outro registro citado.",
                "Documentos citados precisam entrar no checklist de pendências/provas e, quando existirem, também nos anexos/provas.",
                "alta",
            )
        )
        suggestions.append(
            _suggestion(
                "anexos",
                "Anexar prova documental",
                "Anexar o documento citado e descrever de forma objetiva o que ele comprova.",
                "O sistema não deve tratar uma informação digitada como prova sem o respectivo arquivo/documento.",
                "normal",
            )
        )

    if has_person:
        suggestions.append(
            _suggestion(
                "testemunhas",
                "Cadastrar pessoa-chave",
                "Cadastrar nome, papel e o que a pessoa sabe ou confirma sobre o fato.",
                "A informação parece envolver pessoa relevante, testemunha, depoente, parte ou alguém que pode confirmar fatos.",
                "alta",
            )
        )

    suggestions.append(
        _suggestion(
            "dossie",
            "Atualizar visão operacional",
            "Depois de organizar a informação nos módulos corretos, atualizar o dossiê interno do caso.",
            "O dossiê consolida timeline, checklist, anexos, testemunhas e prontidão para apoiar a decisão do advogado.",
            "normal",
        )
    )

    context_summary = _clean_text(context.get("summary"), 700)
    timeline_count = len(timeline)

    next_steps = [
        "Revisar a sugestão antes de copiar para qualquer campo.",
        "Salvar o fato na Linha do Tempo se ele representar um acontecimento do caso.",
        "Criar pendência no Checklist se depender de documento, prova ou confirmação.",
        "Atualizar o Dossiê depois de cadastrar as informações nos módulos corretos.",
    ]

    return {
        "case_id": case.id,
        "assistant_mode": "orientation_only",
        "summary": (
            "Entendi a informação e organizei em orientação operacional para o caso. "
            "Nenhum dado foi salvo automaticamente."
        ),
        "rewritten_input": text,
        "suggested_actions": suggestions[:6],
        "next_steps": next_steps,
        "warnings": [
            "Esta V1 apenas orienta; ela não salva timeline, checklist, anexos, testemunhas ou minuta automaticamente.",
            "Toda sugestão deve ser revisada por advogado responsável antes de uso jurídico.",
        ],
        "disclaimer": "Assistente operacional de apoio. Não substitui revisão técnica, prova documental, estratégia jurídica ou decisão profissional.",
        "metadata": {
            "source": "case_operational_assistant_v1",
            "provider": "fallback",
            "case_number": _clean_text(getattr(case, "case_number", "")),
            "context_summary": context_summary,
            "timeline_items_considered": timeline_count,
        },
    }


def _normalize_suggestions(value: Any, fallback: list[dict[str, str]]) -> list[dict[str, str]]:
    raw_items = value if isinstance(value, list) else []
    items: list[dict[str, str]] = []

    for raw in raw_items:
        if not isinstance(raw, dict):
            continue

        destination = _clean_text(raw.get("destination"), 80) or "linha_do_tempo"
        if destination not in DESTINATION_LABELS:
            destination = "linha_do_tempo"

        items.append(
            _suggestion(
                destination=destination,
                label=_clean_text(raw.get("label"), 160) or DESTINATION_LABELS[destination],
                suggested_text=_clean_text(raw.get("suggested_text"), 900),
                reason=_clean_text(raw.get("reason"), 500) or "Sugestão operacional gerada a partir da mensagem e do contexto do caso.",
                priority=_clean_text(raw.get("priority"), 40) or "normal",
            )
        )

        if len(items) >= 8:
            break

    return items or fallback


def _normalize_response(raw: dict[str, Any], fallback: dict[str, Any], case_id: int) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return fallback

    suggestions = _normalize_suggestions(
        raw.get("suggested_actions") or raw.get("actions") or raw.get("suggestions"),
        fallback.get("suggested_actions", []),
    )

    warnings = _as_list(raw.get("warnings"), limit=5) or fallback["warnings"]
    if not any("não salva" in warning.lower() or "não salva" in warning.lower() for warning in warnings):
        warnings.insert(0, "Esta V1 apenas orienta; ela não salva dados automaticamente.")

    return {
        "case_id": case_id,
        "assistant_mode": "orientation_only",
        "summary": _clean_text(raw.get("summary"), 900) or fallback["summary"],
        "rewritten_input": _clean_text(raw.get("rewritten_input"), 2500) or fallback["rewritten_input"],
        "suggested_actions": suggestions,
        "next_steps": _as_list(raw.get("next_steps"), limit=8) or fallback["next_steps"],
        "warnings": warnings[:6],
        "disclaimer": _clean_text(raw.get("disclaimer"), 700) or fallback["disclaimer"],
        "metadata": {
            **dict(fallback.get("metadata") or {}),
            "provider": "llm",
            "source": "case_operational_assistant_v1",
        },
    }


def _build_prompt(case: Case, message: str, context: dict[str, Any], timeline: list[dict[str, Any]]) -> str:
    payload = {
        "case": {
            "id": getattr(case, "id", None),
            "case_number": getattr(case, "case_number", ""),
            "title": getattr(case, "title", ""),
            "description": getattr(case, "description", ""),
            "legal_area": getattr(case, "legal_area", ""),
            "action_type": getattr(case, "action_type", ""),
            "status": getattr(case, "status", ""),
        },
        "operational_context": context,
        "timeline": timeline,
        "lawyer_message": message,
    }

    return f"""
Você é uma IA assistente operacional universal de um painel jurídico multiárea.
Você atua como copiloto operacional dentro do caso aberto, independentemente da área jurídica.
Sua função é ajudar o advogado a entender, corrigir, organizar e decidir ONDE colocar cada informação dentro do sistema.

REGRAS:
- Responda apenas em JSON válido.
- Não diga que salvou dados.
- Não crie peça processual final.
- Não prometa resultado judicial.
- Seja prático, objetivo e operacional.
- Quando houver fato cronológico, evento, data, sequência ou narrativa de acontecimento, sugira Linha do Tempo.
- Quando houver documento, prova, arquivo, print, áudio, vídeo, contrato, laudo, decisão, BO, notificação, comprovante ou prova faltante, sugira Checklist e/ou Anexos.
- Quando houver pessoa envolvida, parte, testemunha, depoente, servidor, médico, perito, fiscal, empregado, empregador, consumidor, fornecedor ou alguém que viu/sabe/confirma, sugira Testemunhas/depoentes ou Cliente/WhatsApp conforme o caso.
- Quando a informação ajudar a consolidar visão estratégica/operacional, sugira Dossiê.
- Quando a informação parecer fundamento, tese, risco, pedido, estratégia ou dúvida técnica, sugira Análise do caso.
- Quando a informação parecer texto aproveitável para petição, manifestação, audiência, recurso ou minuta, sugira Editor/minuta.
- Sempre mantenha revisão humana obrigatória.

DESTINOS permitidos:
linha_do_tempo, checklist, anexos, testemunhas, dossie, analise, editor_minuta, contato_cliente

JSON obrigatório:
{{
  "summary": "resumo do que entendeu",
  "rewritten_input": "versão corrigida e mais clara da informação enviada",
  "suggested_actions": [
    {{
      "destination": "linha_do_tempo",
      "label": "nome curto da ação",
      "suggested_text": "texto sugerido para copiar ou adaptar",
      "reason": "por que isso vai nesse módulo",
      "priority": "alta|normal|baixa"
    }}
  ],
  "next_steps": ["passo 1", "passo 2"],
  "warnings": ["alerta operacional"],
  "disclaimer": "aviso de revisão humana"
}}

DADOS:
{json.dumps(payload, ensure_ascii=False, default=str)}
""".strip()


def build_case_operational_assistant_response(
    db: Session,
    case: Case,
    current_user,
    message: str,
) -> dict[str, Any]:
    cleaned_message = _clean_text(message, 6000)

    context = _build_case_operational_context(db=db, case=case, current_user=current_user)
    timeline = _load_timeline_items(db=db, case=case, current_user=current_user)
    fallback = _fallback_response(case=case, message=cleaned_message, context=context, timeline=timeline)

    try:
        raw = request_structured_analysis(_build_prompt(case=case, message=cleaned_message, context=context, timeline=timeline))
    except LLMClientError:
        return fallback
    except Exception:
        return fallback

    return _normalize_response(raw=raw, fallback=fallback, case_id=case.id)
