from typing import Dict, Optional
from datetime import datetime


def generate_report_html(case: Dict, analysis: Dict, viability: Dict, executive_decision: Optional[Dict] = None) -> str:
    generated_at = datetime.utcnow().strftime("%d/%m/%Y %H:%M UTC")

    risk_level_raw = (analysis.get("risk_level") or "indefinido")
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

    probability = viability.get("probability", None)
    try:
        probability_pct = (
            "Não informado"
            if probability is None
            else f"{float(probability) * 100:.0f}%"
        )
    except Exception:
        probability_pct = "Não informado"

    issues_html = "".join(f"<li>{item}</li>" for item in issues) or "<li>Nenhum ponto crítico identificado.</li>"
    next_steps_html = "".join(f"<li>{item}</li>" for item in next_steps) or "<li>Sem próximos passos sugeridos.</li>"

    html = f"""
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
            <p class=\"muted\">Gerado em: {generated_at}</p>

            <div class=\"section\">
                <h2>Dados do Caso</h2>
                <div class=\"grid\">
                    <div class=\"card\">
                        <span class=\"label\">Número do processo</span>
                        <span class=\"value\">{case.get("case_number") or "Não informado"}</span>
                    </div>
                    <div class=\"card\">
                        <span class=\"label\">Título</span>
                        <span class=\"value\">{case.get("title") or "Não informado"}</span>
                    </div>
                </div>
                <div class=\"card\" style=\"margin-top:14px;\">
                    <span class=\"label\">Descrição</span>
                    <div>{case.get("description") or "Sem descrição informada."}</div>
                </div>
            </div>

            <div class=\"section\">
                <h2>Resumo Executivo</h2>
                <p><span class=\"highlight\">Classificação: {viability.get("label") or "Indefinida"}</span></p>
                <p>{summary}</p>
            </div>

            <div class=\"section\">
                <h2>Indicadores Estratégicos</h2>
                <div class=\"grid\">
                    <div class=\"card\">
                        <span class=\"label\">Score</span>
                        <span class=\"value\">{("Não informado" if viability.get("score") is None else str(viability.get("score")) + "/100")}</span>
                    </div>
                    <div class=\"card\">
                        <span class=\"label\">Probabilidade estimada</span>
                        <span class=\"value\">{probability_pct}</span>
                    </div>
                    <div class=\"card\">
                        <span class=\"label\">Nível de risco</span>
                        <span class=\"value\">{risk_level}</span>
                    </div>
                    <div class=\"card\">
                        <span class=\"label\">Complexidade</span>
                        <span class=\"value\">{viability.get("complexity") or "Indefinida"}</span>
                    </div>
                    <div class=\"card\">
                        <span class=\"label\">Tempo estimado</span>
                        <span class=\"value\">{viability.get("estimated_time") or "Indefinido"}</span>
                    </div>
                    <div class=\"card\">
                        <span class=\"label\">Recomendação</span>
                        <span class=\"value\">{viability.get("recommendation") or "Sem recomendação"}</span>
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

    return html
