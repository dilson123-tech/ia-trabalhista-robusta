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


def _clean_multiline_text(value: Any, limit: int = 6000) -> str:
    raw = str(value or "").replace("\\n", "\n").strip()
    lines = [" ".join(line.split()) for line in raw.splitlines()]
    text = "\n".join(line for line in lines if line)
    return text[:limit]


def _suggestion(destination: str, label: str, suggested_text: str, reason: str, priority: str = "normal") -> dict[str, str]:
    return {
        "destination": destination,
        "label": label,
        "suggested_text": _clean_multiline_text(suggested_text, 6000),
        "reason": _clean_text(reason, 500),
        "priority": priority,
    }



def _case_context_text(case: Case, context: dict[str, Any]) -> str:
    parts = [
        getattr(case, "case_number", ""),
        getattr(case, "title", ""),
        getattr(case, "description", ""),
        getattr(case, "legal_area", ""),
        getattr(case, "action_type", ""),
        context.get("summary", ""),
    ]
    return _clean_text(" ".join(str(part or "") for part in parts), 3000).lower()


def _requested_guidance_modules(lowered: str) -> list[str]:
    guidance_markers = (
        "o que escrevo",
        "o que eu escrevo",
        "o que coloco",
        "o que eu coloco",
        "como preencher",
        "como monto",
        "como montar",
        "me ajude a montar",
        "me ajuda a montar",
        "o que devo preencher",
        "o que vai",
        "quais campos",
        "como faço",
    )

    if not any(marker in lowered for marker in guidance_markers):
        return []

    modules: list[str] = []

    if "linha do tempo" in lowered or "timeline" in lowered:
        modules.append("linha_do_tempo")

    if "checklist" in lowered or "pendência" in lowered or "pendencia" in lowered:
        modules.append("checklist")

    if "anexo" in lowered or "anexar" in lowered or "prova" in lowered or "documento" in lowered:
        modules.append("anexos")

    if "testemunha" in lowered or "depoente" in lowered or "pessoa" in lowered:
        modules.append("testemunhas")

    if "dossiê" in lowered or "dossie" in lowered:
        modules.append("dossie")

    ordered = []
    for module in modules:
        if module not in ordered:
            ordered.append(module)
    return ordered


def _timeline_guide_text(case: Case, context: dict[str, Any]) -> str:
    case_title = _clean_text(getattr(case, "title", ""), 220) or "este caso"
    blob = _case_context_text(case, context)

    if "pátio" in blob or "patio" in blob or "carreta" in blob:
        facts = [
            ("A confirmar", "Entrada ou permanência da carreta no pátio", "Registrar quando, onde, por quem e por qual motivo a carreta ficou sob guarda do pátio.", "contrato, recibo, mensagens, comprovante de entrada ou documentos do pátio", "quem entregou, recebeu, autorizou ou acompanhou a guarda", "confirmar data exata, responsável pela guarda e documento de entrada"),
            ("A confirmar", "Desaparecimento, furto ou não localização da carreta", "Registrar quando foi percebido que a carreta não estava mais disponível, quem comunicou o fato e qual foi a resposta do pátio.", "BO, mensagens, ligações, fotos, comunicações e registros do pátio", "pessoa que constatou ou comunicou o desaparecimento", "confirmar data, horário, local e versão do pátio"),
            ("A confirmar", "Boletim de ocorrência e comunicações do fato", "Registrar a data do BO e demais comunicações feitas ao pátio, seguradora, locador, locatário ou responsáveis.", "boletim de ocorrência, protocolos, mensagens e e-mails", "quem registrou o BO ou participou da comunicação", "anexar BO e identificar todos os protocolos"),
            ("28/05 ou data a confirmar", "Audiência/acordo anterior envolvendo a carreta", "Registrar que houve audiência ou acordo anterior relacionado ao pagamento da carreta, sem confundir esse acordo com a responsabilidade do pátio.", "ata de audiência, termo de acordo, processo anterior", "partes presentes na audiência", "confirmar número do processo, termos do acordo e valores"),
            ("A confirmar", "Avaliação de responsabilidade do pátio", "Registrar as providências para apurar se o pátio tinha dever de guarda e se houve falha na custódia do bem.", "contrato, recibos, regulamento do pátio, mensagens, BO e documentos do veículo", "responsável do pátio, cliente, condutor ou testemunhas", "confirmar fundamento da guarda e documentos faltantes"),
        ]
    else:
        facts = [
            ("A confirmar", "Início da relação ou situação jurídica", "Registrar quando e como começou a relação entre as partes, serviço, contrato, trabalho, benefício, atendimento, guarda, compra ou conflito.", "contrato, mensagens, recibos, cadastro, protocolo ou documento inicial", "quem participou ou presenciou o início dos fatos", "confirmar data inicial e partes envolvidas"),
            ("A confirmar", "Fato principal que gerou o problema", "Registrar o acontecimento central do caso: negativa, dano, cobrança, descumprimento, acidente, dispensa, falha, perda, furto ou outro evento relevante.", "documentos, prints, fotos, vídeos, laudos, BO ou comprovantes", "quem viu, sabe ou confirma o fato", "confirmar data, local e consequências"),
            ("A confirmar", "Providências tomadas pelo cliente", "Registrar reclamações, contatos, protocolos, BO, notificações, pedidos administrativos, atendimentos ou tentativas de solução.", "protocolos, mensagens, e-mails, notificações e comprovantes", "quem recebeu ou respondeu", "organizar documentos e respostas"),
            ("A confirmar", "Situação atual e prejuízos", "Registrar o estado atual do problema, valores envolvidos, impactos, documentos faltantes e urgências.", "comprovantes de prejuízo, orçamento, laudo, extrato, recibos ou documentos atuais", "pessoas que podem confirmar o prejuízo", "quantificar valores e lacunas probatórias"),
        ]

    blocks = [f"Para o caso: {case_title}", "Preencha a Linha do Tempo por fatos, um item por vez:"]
    for index, (date, title, description, evidence, witness, pending) in enumerate(facts, start=1):
        blocks.append(
            f"\nFato {index}\n"
            f"Data/período: {date}\n"
            f"Título do fato: {title}\n"
            f"Descrição do fato: {description}\n"
            f"Prova relacionada: {evidence}\n"
            f"Testemunha/depoente relacionado: {witness}\n"
            f"Pendência/observação: {pending}\n"
            f"Ordem: {index}"
        )
    return "\\n".join(blocks)


def _checklist_guide_text(case: Case, context: dict[str, Any]) -> str:
    case_title = _clean_text(getattr(case, "title", ""), 220) or "este caso"
    return f"""Para o caso: {case_title}
No Checklist de provas, crie pendências objetivas. Sugestões:

Pendência 1
Título: Localizar documento principal do caso
Categoria: documento
Prioridade: alta
Solicitar de: cliente
Prazo: a definir
Observações: pedir contrato, recibo, BO, mensagens, protocolos ou documento que comprove a origem do caso.

Pendência 2
Título: Confirmar datas principais
Categoria: informação
Prioridade: alta
Solicitar de: cliente/testemunha
Prazo: a definir
Observações: confirmar data inicial, data do fato principal, comunicações feitas e situação atual.

Pendência 3
Título: Separar provas de responsabilidade e prejuízo
Categoria: prova
Prioridade: alta
Solicitar de: cliente/advogado
Prazo: a definir
Observações: organizar documentos que mostram quem tinha obrigação, o que aconteceu, qual dano houve e o valor envolvido."""


def _attachments_guide_text(case: Case, context: dict[str, Any]) -> str:
    case_title = _clean_text(getattr(case, "title", ""), 220) or "este caso"
    return f"""Para o caso: {case_title}
Em Anexos/provas, só envie documentos reais. Para cada arquivo, descreva o que ele comprova.

Anexo sugerido 1
Tipo: documento principal
Descrição: comprova a relação entre as partes ou a origem da obrigação.

Anexo sugerido 2
Tipo: comunicação/protocolo
Descrição: comprova que o fato foi comunicado ou que houve tentativa de solução.

Anexo sugerido 3
Tipo: prova do dano/prejuízo
Descrição: comprova valor, perda, dano, pagamento, orçamento, laudo ou consequência do fato.

Cuidado: texto digitado não substitui prova. Quando citar BO, contrato, print, foto ou mensagem, tente anexar o arquivo correspondente."""


def _witness_guide_text(case: Case, context: dict[str, Any]) -> str:
    case_title = _clean_text(getattr(case, "title", ""), 220) or "este caso"
    return f"""Para o caso: {case_title}
Em Testemunhas/depoentes, cadastre pessoas que possam confirmar fatos, datas, guarda, comunicação, dano ou providências.

Pessoa 1
Nome: a confirmar
Papel: cliente/parte envolvida
O que sabe ou confirma: explica a narrativa principal, documentos disponíveis, datas e prejuízos.

Pessoa 2
Nome: a confirmar
Papel: testemunha/depoente
O que sabe ou confirma: viu, recebeu, entregou, comunicou, acompanhou ou pode confirmar algum fato da linha do tempo.

Pessoa 3
Nome: a confirmar
Papel: representante/responsável da outra parte ou terceiro
O que sabe ou confirma: pode esclarecer responsabilidade, guarda, resposta dada, protocolos ou documentos emitidos.

Cuidado: não inventar testemunha. Se o nome ainda não existir, cadastre como pendência no Checklist."""


def _dossier_guide_text(case: Case, context: dict[str, Any]) -> str:
    case_title = _clean_text(getattr(case, "title", ""), 220) or "este caso"
    return f"""Para o caso: {case_title}
O Dossiê interno deve ser atualizado depois de preencher os módulos principais.

Antes de atualizar o dossiê, confira:
1. Linha do Tempo com os fatos principais.
2. Checklist com documentos e pendências.
3. Anexos/provas reais já enviados.
4. Testemunhas/depoentes ou pessoas-chave.
5. Dados do cliente e WhatsApp, se aplicável.

Depois clique em Atualizar dossiê. Ele serve para visão operacional do advogado, não é peça processual e não substitui revisão jurídica."""


def _module_guide_suggestion(destination: str, case: Case, context: dict[str, Any]) -> dict[str, str]:
    if destination == "linha_do_tempo":
        return _suggestion(
            "linha_do_tempo",
            "Preencher Linha do Tempo por campos",
            _timeline_guide_text(case, context),
            "A pergunta é sobre como preencher a Linha do Tempo; a resposta deve orientar campo por campo, não tratar a pergunta como fato.",
            "alta",
        )

    if destination == "checklist":
        return _suggestion(
            "checklist",
            "Preencher Checklist de provas",
            _checklist_guide_text(case, context),
            "A pergunta pede organização de pendências e documentos; isso pertence ao Checklist.",
            "alta",
        )

    if destination == "anexos":
        return _suggestion(
            "anexos",
            "Organizar Anexos/provas",
            _attachments_guide_text(case, context),
            "A pergunta envolve documentos/provas que devem ser anexados quando existirem arquivos reais.",
            "normal",
        )

    if destination == "testemunhas":
        return _suggestion(
            "testemunhas",
            "Preencher Testemunhas/depoentes",
            _witness_guide_text(case, context),
            "A pergunta envolve pessoas que podem confirmar fatos e devem ser cadastradas com papel e o que sabem.",
            "normal",
        )

    return _suggestion(
        "dossie",
        "Atualizar Dossiê interno",
        _dossier_guide_text(case, context),
        "O dossiê consolida o que foi preenchido nos módulos do caso.",
        "normal",
    )


def _module_guidance_response(
    case: Case,
    message: str,
    context: dict[str, Any],
    timeline: list[dict[str, Any]],
    modules: list[str],
) -> dict[str, Any]:
    suggestions = [_module_guide_suggestion(module, case, context) for module in modules]

    if "dossie" not in modules:
        suggestions.append(_module_guide_suggestion("dossie", case, context))

    return {
        "case_id": case.id,
        "assistant_mode": "orientation_only",
        "summary": "Entendi que você quer orientação de preenchimento. Vou responder por campos, para copiar e adaptar dentro do módulo correto.",
        "rewritten_input": _clean_text(message, 2500),
        "suggested_actions": suggestions[:8],
        "next_steps": [
            "Clique no botão Abrir do módulo indicado.",
            "Copie/adapte os campos sugeridos.",
            "Salve um item por vez, revisando datas, documentos e nomes.",
            "Depois atualize o Dossiê interno para consolidar a visão do caso.",
        ],
        "warnings": [
            "Esta V1 orienta o preenchimento, mas não salva dados automaticamente.",
            "Não invente datas, documentos, valores ou testemunhas. Use 'a confirmar' quando faltar informação.",
        ],
        "disclaimer": "Assistente operacional de apoio. Não substitui revisão técnica, prova documental, estratégia jurídica ou decisão profissional.",
        "metadata": {
            "source": "case_operational_assistant_module_guidance_v1",
            "provider": "fallback",
            "case_number": _clean_text(getattr(case, "case_number", "")),
            "requested_modules": modules,
            "timeline_items_considered": len(timeline),
        },
    }


def _fallback_response(case: Case, message: str, context: dict[str, Any], timeline: list[dict[str, Any]]) -> dict[str, Any]:
    text = _clean_text(message, 2500)
    lowered = text.lower()

    requested_guidance_modules = _requested_guidance_modules(lowered)
    if requested_guidance_modules:
        return _module_guidance_response(
            case=case,
            message=text,
            context=context,
            timeline=timeline,
            modules=requested_guidance_modules,
        )

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
- Quando a mensagem for uma pergunta de orientação do tipo "o que escrevo", "o que coloco", "como preencher", "como montar" ou "me ajude a montar", NÃO trate a pergunta como fato do caso.
- Nesses casos, entregue um guia preenchível por campos do módulo solicitado, com exemplos práticos e textos que o advogado possa copiar/adaptar.
- Se o advogado pedir vários módulos na mesma mensagem, inclua uma sugestão para cada módulo solicitado.
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
