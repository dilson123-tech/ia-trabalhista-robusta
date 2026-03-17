from __future__ import annotations

from datetime import datetime


def _safe(value) -> str:
    return "" if value is None else str(value)


def _risk_label(value) -> str:
    mapping = {
        "low": "Baixo",
        "medium": "Médio",
        "high": "Alto",
        "baixo": "Baixo",
        "medio": "Médio",
        "médio": "Médio",
        "alto": "Alto",
    }
    value = "" if value is None else str(value).strip().lower()
    return mapping.get(value, value.capitalize() if value else "Indefinido")


def _probability_pct(executive_data: dict) -> str:
    probability = executive_data.get("viability", {}).get("probability", 0) or 0
    try:
        return f"{float(probability) * 100:.0f}%"
    except Exception:
        return "0%"


def _pdf_via_fpdf2(case_data: dict, executive_data: dict) -> bytes:
    from fpdf import FPDF

    case_number = _safe(case_data.get("case_number")) or "Não informado"
    title = _safe(case_data.get("title")) or "Não informado"
    generated_at = datetime.now().strftime("%d/%m/%Y %H:%M")

    decision = executive_data.get("decision", {}) or {}
    viability = executive_data.get("viability", {}) or {}
    strategic = executive_data.get("strategic", {}) or {}

    summary = _safe(decision.get("executive_summary")) or "(sem resumo executivo)"
    probability_pct = _probability_pct(executive_data)
    final_status = _safe(decision.get("final_status")) or "Indefinido"
    risk_level = _risk_label(strategic.get("financial_risk") or strategic.get("risk_level"))
    complexity = _safe(viability.get("complexity")) or "Indefinida"
    estimated_time = _safe(viability.get("estimated_time")) or "Indefinido"
    recommendation = _safe(viability.get("recommendation")) or "Sem recomendação"

    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "IA Trabalhista Robusta", ln=True)

    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 8, "Relatorio Executivo Juridico", ln=True)
    pdf.cell(0, 8, f"Data de geracao: {generated_at}", ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Dados do Caso", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 6, f"Processo: {case_number}")
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(0, 6, f"Titulo: {title}")
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Resumo Executivo", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 6, summary)
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Indicadores Estrategicos", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, f"Classificacao final: {final_status}", ln=True)
    pdf.cell(0, 7, f"Probabilidade estimada: {probability_pct}", ln=True)
    pdf.cell(0, 7, f"Nivel de risco: {risk_level}", ln=True)
    pdf.cell(0, 7, f"Complexidade: {complexity}", ln=True)
    pdf.cell(0, 7, f"Tempo estimado: {estimated_time}", ln=True)
    pdf.multi_cell(0, 6, f"Recomendacao: {recommendation}")
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Observacao Operacional", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(
        0,
        5,
        "Este documento possui finalidade de apoio a analise e a tomada de decisao juridica, devendo ser validado pelo profissional responsavel antes de uso externo, estrategico ou comercial."
    )

    pdf.ln(5)
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(0, 5, "Documento gerado automaticamente pelo sistema IA Trabalhista Robusta.")

    return bytes(pdf.output(dest="S"))


def generate_executive_pdf(case_data: dict, executive_data: dict) -> bytes:
    """
    PDF executivo.

    Estratégia:
    1) Tenta WeasyPrint (melhor layout), se o ambiente suportar libs nativas.
    2) Se falhar (ImportError/OSError), usa fallback pure-python (fpdf2).
    """
    try:
        from weasyprint import HTML  # type: ignore

        decision = executive_data.get("decision", {}) or {}
        viability = executive_data.get("viability", {}) or {}
        strategic = executive_data.get("strategic", {}) or {}

        generated_at = datetime.now().strftime("%d/%m/%Y %H:%M")
        probability_pct = _probability_pct(executive_data)

        html_content = f"""
        <html>
        <head>
          <meta charset="utf-8" />
          <style>
            body {{
              font-family: Arial, sans-serif;
              margin: 34px;
              color: #1f2937;
            }}
            .container {{
              border: 1px solid #e5e7eb;
              border-radius: 14px;
              padding: 28px;
            }}
            .eyebrow {{
              font-size: 11px;
              text-transform: uppercase;
              letter-spacing: 0.08em;
              color: #8b5e00;
              font-weight: bold;
            }}
            h1 {{
              margin: 6px 0 4px;
              font-size: 24px;
              color: #0b1220;
              font-weight: 800;
            }}
            h2 {{
              margin: 0 0 10px;
              font-size: 16px;
              color: #0f172a;
              font-weight: 800;
            }}
            .muted {{
              color: #374151;
              font-size: 12px;
              font-weight: 600;
            }}
            .section {{
              margin-top: 20px;
              padding-top: 16px;
              border-top: 1px solid #d9dee7;
            }}
            .grid {{
              display: grid;
              grid-template-columns: 1fr 1fr;
              gap: 10px;
            }}
            .card {{
              background: #f8fafc;
              border: 1px solid #c8d2e0;
              border-radius: 10px;
              padding: 10px 12px;
            }}
            .label {{
              display: block;
              font-size: 11px;
              text-transform: uppercase;
              letter-spacing: 0.05em;
              color: #334155;
              font-weight: 800;
              margin-bottom: 4px;
            }}
            .value {{
              font-size: 14px;
              font-weight: 800;
              color: #0b1220;
              line-height: 1.5;
                overflow-wrap: anywhere;
                word-break: break-word;
            }}
            .footer {{
              margin-top: 22px;
              font-size: 11px;
              color: #334155;
              font-weight: 600;
            }}
          </style>
        </head>
        <body>
          <div class="container">
            <div class="eyebrow">IA Trabalhista Robusta</div>
            <h1>Relatório Executivo Jurídico</h1>
            <p class="muted">Gerado em: {generated_at}</p>

            <div class="section">
              <h2>Dados do Caso</h2>
              <div class="grid">
                <div class="card">
                  <span class="label">Processo</span>
                  <span class="value">{_safe(case_data.get("case_number")) or "Não informado"}</span>
                </div>
                <div class="card">
                  <span class="label">Título</span>
                  <span class="value">{_safe(case_data.get("title")) or "Não informado"}</span>
                </div>
              </div>
            </div>

            <div class="section">
              <h2>Resumo Executivo</h2>
              <p style="color: #111827; line-height: 1.72; font-weight: 500;">{_safe(decision.get("executive_summary")) or "Sem resumo executivo disponível."}</p>
            </div>

            <div class="section">
              <h2>Indicadores Estratégicos</h2>
              <div class="grid">
                <div class="card">
                  <span class="label">Classificação final</span>
                  <span class="value">{_safe(decision.get("final_status")) or "Indefinido"}</span>
                </div>
                <div class="card">
                  <span class="label">Probabilidade estimada</span>
                  <span class="value">{probability_pct}</span>
                </div>
                <div class="card">
                  <span class="label">Nível de risco</span>
                  <span class="value">{_risk_label(strategic.get("financial_risk") or strategic.get("risk_level"))}</span>
                </div>
                <div class="card">
                  <span class="label">Complexidade</span>
                  <span class="value">{_safe(viability.get("complexity")) or "Indefinida"}</span>
                </div>
                <div class="card">
                  <span class="label">Tempo estimado</span>
                  <span class="value">{_safe(viability.get("estimated_time")) or "Indefinido"}</span>
                </div>
                <div class="card">
                  <span class="label">Recomendação</span>
                  <span class="value">{_safe(viability.get("recommendation")) or "Sem recomendação"}</span>
                </div>
              </div>
            </div>

            <div class="section">
              <h2>Observação Operacional</h2>
              <p style="color: #1f2937; line-height: 1.72; font-weight: 500;">Este documento possui finalidade de apoio à análise e à tomada de decisão jurídica, devendo ser validado pelo profissional responsável antes de uso externo, estratégico ou comercial.</p>
            </div>

            <div class="footer">
              Documento gerado automaticamente pelo sistema IA Trabalhista Robusta.
            </div>
          </div>
        </body>
        </html>
        """
        return HTML(string=html_content).write_pdf()
    except (ImportError, OSError):
        return _pdf_via_fpdf2(case_data, executive_data)
