import html
from typing import Dict, Optional
from datetime import datetime


def _escape(value) -> str:
    return html.escape(str(value or ""), quote=True)


def _items_html(items, empty_text: str) -> str:
    safe_items = [_escape(item) for item in (items or []) if str(item or "").strip()]
    return "".join(f"<li>{item}</li>" for item in safe_items) or f"<li>{_escape(empty_text)}</li>"


def _status_label(value) -> str:
    raw = str(value or "").strip()
    normalized = raw.lower()

    mapping = {
        "validated": "Validado",
        "validado": "Validado",
        "done": "Validado",
        "concluído": "Concluído",
        "concluido": "Concluído",
        "pending": "Pendente",
        "pendente": "Pendente",
        "requested": "Solicitado",
        "received": "Recebido",
        "needs_review": "Precisa revisão",
        "open": "Pendente",
        "aberto": "Pendente",
        "waived": "Dispensado",
        "dispensado": "Dispensado",
        "active": "Ativo",
        "ativo": "Ativo",
    }

    return mapping.get(normalized, raw or "Sem status")


def _context_section_html(analysis: Dict) -> str:
    context = analysis.get("case_context") or {}
    facts = analysis.get("case_context_facts") or context.get("facts") or []
    summary = analysis.get("case_context_summary") or context.get("summary") or ""
    attachments = context.get("attachments") or []
    checklist = context.get("checklist") or {}
    witnesses = context.get("witnesses") or []

    if not (facts or summary or attachments or checklist.get("total") or witnesses):
        return ""

    facts_html = _items_html(facts, "Nenhum fato-chave estruturado informado.")

    attachment_items = []
    for item in attachments:
        filename = item.get("filename") or "Arquivo sem nome"
        category = item.get("category")
        description = item.get("description")
        label = filename
        if category:
            label += f" — {category}"
        if description:
            label += f" — {description}"
        attachment_items.append(label)
    attachments_html = _items_html(attachment_items, "Nenhum anexo cadastrado.")

    checklist_items = []
    for item in checklist.get("items") or []:
        title = item.get("title") or "Item de checklist"
        status = _status_label(item.get("status"))
        checklist_items.append(f"{title} — {status}")
    checklist_intro = (
        f"{checklist.get('validated', 0)}/{checklist.get('total', 0)} item(ns) validados; "
        f"{checklist.get('pending', 0)} pendente(s)."
        if checklist.get("total")
        else "Sem checklist cadastrado."
    )
    checklist_html = _items_html(checklist_items, "Nenhum item de checklist cadastrado.")

    witness_items = []
    for item in witnesses:
        name = item.get("name") or "Pessoa sem nome informado"
        role = item.get("role") or "testemunha/depoente"
        knowledge = item.get("knowledge")
        label = f"{name} — {role}"
        if knowledge:
            label += f" — {knowledge}"
        witness_items.append(label)
    witnesses_html = _items_html(witness_items, "Nenhuma testemunha/depoente cadastrada.")

    summary_html = f"<p>{_escape(summary)}</p>" if summary else ""

    return f"""
            <div class=\"section\">
                <h2>Contexto específico do caso</h2>
                {summary_html}
                <div class=\"grid\">
                    <div class=\"card\">
                        <span class=\"label\">Fatos-chave estruturados</span>
                        <ul>{facts_html}</ul>
                    </div>
                    <div class=\"card\">
                        <span class=\"label\">Anexos cadastrados</span>
                        <ul>{attachments_html}</ul>
                    </div>
                    <div class=\"card\">
                        <span class=\"label\">Checklist de provas</span>
                        <div>{_escape(checklist_intro)}</div>
                        <ul>{checklist_html}</ul>
                    </div>
                    <div class=\"card\">
                        <span class=\"label\">Testemunhas/depoentes</span>
                        <ul>{witnesses_html}</ul>
                    </div>
                </div>
            </div>
    """


def generate_report_html(case: Dict, analysis: Dict, viability: Dict, executive_decision: Optional[Dict] = None) -> str:
    generated_at = datetime.utcnow().strftime("%d/%m/%Y %H:%M UTC")

    risk_level_raw = analysis.get("risk_level") or "indefinido"
    risk_level_map = {
        "low": "Baixo",
        "medium": "Médio",
        "high": "Alto",
        "indefinido": "Indefinido",
    }
    risk_level = risk_level_map.get(str(risk_level_raw).lower(), str(risk_level_raw).capitalize())
    executive_summary = (executive_decision or {}).get("executive_summary")
    summary = executive_summary or analysis.get("summary") or "Sem resumo executivo disponível."
    issues = analysis.get("issues") or []
    next_steps = analysis.get("next_steps") or []

    assessment_note = "Avaliação qualitativa, sem previsão percentual de resultado judicial"
    time_perspective = "Depende da complexidade, da fase processual, da prova disponível e do juízo competente."

    case_number = _escape(case.get("case_number") or "Não informado")
    case_title = _escape(case.get("title") or "Não informado")
    case_description = _escape(case.get("description") or "Sem descrição informada.")
    summary_html = _escape(summary)
    viability_label = _escape(viability.get("label") or "Indefinida")
    risk_level_html = _escape(risk_level)
    complexity_html = _escape(viability.get("complexity") or "Indefinida")
    recommendation_html = _escape(viability.get("recommendation") or "Sem recomendação")
    context_section_html = _context_section_html(analysis)

    issues_html = _items_html(issues, "Nenhum ponto crítico identificado.")
    next_steps_html = _items_html(next_steps, "Sem próximos passos sugeridos.")

    html_doc = f"""
    <html>
    <head>
        <meta charset=\"utf-8\" />
        <style>
            body {{
                font-family: Arial, sans-serif;
                background: #f7f7f5;
                color: #1f2937;
                margin: 0;
                padding: 32px;
            }}
            .container {{
                max-width: 900px;
                margin: 0 auto;
                background: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 14px;
                padding: 36px;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05);
            }}
            .eyebrow {{
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                color: #8b5e00;
                font-weight: bold;
            }}
            h1 {{
                margin: 8px 0 6px;
                font-size: 28px;
                color: #111827;
            }}
            h2 {{
                margin: 0 0 14px;
                font-size: 18px;
                color: #111827;
            }}
            .muted {{
                color: #6b7280;
                font-size: 14px;
            }}
            .section {{
                margin-top: 24px;
                padding-top: 20px;
                border-top: 1px solid #e5e7eb;
            }}
            .grid {{
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 14px;
            }}
            .card {{
                background: #fafaf9;
                border: 1px solid #ececec;
                border-radius: 12px;
                padding: 14px 16px;
            }}
            .label {{
                display: block;
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 0.06em;
                color: #6b7280;
                margin-bottom: 6px;
            }}
            .value {{
                font-size: 16px;
                font-weight: bold;
                color: #111827;
            }}
            .highlight {{
                display: inline-block;
                padding: 6px 10px;
                border-radius: 999px;
                background: #fef3c7;
                color: #92400e;
                font-weight: bold;
                font-size: 13px;
            }}
            ul {{
                margin: 10px 0 0 18px;
                padding: 0;
            }}
            li {{
                margin-bottom: 6px;
            }}
            .footer {{
                margin-top: 26px;
                font-size: 12px;
                color: #6b7280;
            }}
        </style>
    </head>
    <body>
        <div class=\"container\">
            <div class=\"eyebrow\">Plataforma Jurídica Multiárea</div>
            <h1>Relatório Executivo do Caso</h1>
            <p class=\"muted\">Gerado em: {_escape(generated_at)}</p>

            <div class=\"section\">
                <h2>Dados do Caso</h2>
                <div class=\"grid\">
                    <div class=\"card\">
                        <span class=\"label\">Número do processo</span>
                        <span class=\"value\">{case_number}</span>
                    </div>
                    <div class=\"card\">
                        <span class=\"label\">Título</span>
                        <span class=\"value\">{case_title}</span>
                    </div>
                </div>
                <div class=\"card\" style=\"margin-top:14px;\">
                    <span class=\"label\">Descrição</span>
                    <div>{case_description}</div>
                </div>
            </div>

            <div class=\"section\">
                <h2>Resumo Executivo</h2>
                <p><span class=\"highlight\">Classificação: {viability_label}</span></p>
                <p>{summary_html}</p>
            </div>

            {context_section_html}

            <div class=\"section\">
                <h2>Indicadores Estratégicos</h2>
                <div class=\"grid\">
                    <div class=\"card\">
                        <span class=\"label\">Classificação estratégica</span>
                        <span class=\"value\">{viability_label}</span>
                    </div>
                    <div class=\"card\">
                        <span class=\"label\">Confiança da análise</span>
                        <span class=\"value\">{_escape(assessment_note)}</span>
                    </div>
                    <div class=\"card\">
                        <span class=\"label\">Nível de risco</span>
                        <span class=\"value\">{risk_level_html}</span>
                    </div>
                    <div class=\"card\">
                        <span class=\"label\">Complexidade</span>
                        <span class=\"value\">{complexity_html}</span>
                    </div>
                    <div class=\"card\">
                        <span class=\"label\">Perspectiva de tramitação</span>
                        <span class=\"value\">{_escape(time_perspective)}</span>
                    </div>
                    <div class=\"card\">
                        <span class=\"label\">Recomendação</span>
                        <span class=\"value\">{recommendation_html}</span>
                    </div>
                </div>
            </div>

            <div class=\"section\">
                <h2>Pontos Críticos Identificados</h2>
                <ul>{issues_html}</ul>
            </div>

            <div class=\"section\">
                <h2>Próximos Passos Sugeridos</h2>
                <ul>{next_steps_html}</ul>
            </div>

            <div class=\"section\">
                <h2>Observação Operacional</h2>
                <p>Este relatório tem finalidade de apoio à análise e à tomada de decisão jurídica, devendo ser validado pelo profissional responsável antes de uso externo ou estratégico.</p>
            </div>

            <div class=\"footer\">
                Documento gerado automaticamente pelo sistema Plataforma Jurídica Multiárea.
            </div>
        </div>
    </body>
    </html>
    """

    return html_doc
