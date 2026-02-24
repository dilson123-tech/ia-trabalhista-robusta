from typing import Dict
from datetime import datetime


def generate_report_html(case: Dict, analysis: Dict, viability: Dict) -> str:
    generated_at = datetime.utcnow().strftime("%d/%m/%Y %H:%M UTC")

    html = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #111;
                color: #eee;
                padding: 40px;
            }}
            h1, h2 {{
                color: #f4c542;
            }}
            .section {{
                margin-bottom: 30px;
                padding: 20px;
                background-color: #1e1e1e;
                border-radius: 8px;
            }}
            .badge {{
                font-weight: bold;
                padding: 6px 12px;
                border-radius: 6px;
                background-color: #f4c542;
                color: #111;
            }}
        </style>
    </head>
    <body>

        <h1>IA Trabalhista Robusta</h1>
        <p><strong>Relatório Estratégico Processual</strong></p>
        <p>Gerado em: {generated_at}</p>

        <div class="section">
            <h2>Dados do Caso</h2>
            <p><strong>Número:</strong> {case.get("case_number")}</p>
            <p><strong>Título:</strong> {case.get("title")}</p>
            <p><strong>Descrição:</strong> {case.get("description")}</p>
        </div>

        <div class="section">
            <h2>Diagnóstico Técnico</h2>
            <p><strong>Nível de Risco:</strong> {analysis.get("risk_level")}</p>
            <p><strong>Resumo:</strong> {analysis.get("summary")}</p>
        </div>

        <div class="section">
            <h2>Viabilidade Estratégica</h2>
            <p><span class="badge">Score: {viability.get("score")}</span></p>
            <p><strong>Probabilidade:</strong> {viability.get("probability")}</p>
            <p><strong>Classificação:</strong> {viability.get("label")}</p>
            <p><strong>Complexidade:</strong> {viability.get("complexity")}</p>
            <p><strong>Tempo Estimado:</strong> {viability.get("estimated_time")}</p>
            <p><strong>Recomendação:</strong> {viability.get("recommendation")}</p>
        </div>

        <div class="section">
            <h2>Conclusão</h2>
            <p>Relatório gerado pela IA Trabalhista Robusta.</p>
        </div>

    </body>
    </html>
    """

    return html
