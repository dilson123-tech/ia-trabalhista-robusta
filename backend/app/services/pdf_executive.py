from __future__ import annotations

from datetime import datetime

def _pdf_via_fpdf2(case_data: dict, executive_data: dict) -> bytes:
    # Fallback pure-python: funciona no Railway sem libs nativas.
    from fpdf import FPDF

    def _safe(s) -> str:
        # Evita None e garante string
        return "" if s is None else str(s)

    case_number = _safe(case_data.get("case_number"))
    title = _safe(case_data.get("title"))
    summary = _safe(executive_data.get("decision", {}).get("executive_summary", ""))

    probability = executive_data.get("viability", {}).get("probability", 0) or 0
    try:
        probability_pct = f"{float(probability) * 100:.0f}%"
    except Exception:
        probability_pct = "0%"

    final_status = _safe(executive_data.get("decision", {}).get("final_status", "Indefinido"))
    risk_level = _safe(executive_data.get("strategic", {}).get("risk_level", "Médio"))

    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Fonte padrão (latin-1). Mantém simples e estável no Railway.
    pdf.set_font("Helvetica", size=16)
    pdf.cell(0, 10, "Relatorio Executivo Juridico", ln=True)

    pdf.set_font("Helvetica", size=11)
    pdf.cell(0, 8, f"Processo: {case_number}", ln=True)
    pdf.multi_cell(0, 6, f"Titulo: {title}")
    pdf.cell(0, 8, f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
    pdf.ln(2)

    pdf.set_font("Helvetica", size=12)
    pdf.cell(0, 8, "Resumo Estrategico", ln=True)
    pdf.set_font("Helvetica", size=11)
    pdf.multi_cell(0, 6, summary or "(sem resumo)")
    pdf.ln(2)

    pdf.set_font("Helvetica", size=12)
    pdf.cell(0, 8, "Indicadores", ln=True)
    pdf.set_font("Helvetica", size=11)
    pdf.cell(0, 7, f"Probabilidade de Exito: {probability_pct}", ln=True)
    pdf.cell(0, 7, f"Status Final: {final_status}", ln=True)
    pdf.cell(0, 7, f"Nivel de Risco: {risk_level}", ln=True)

    pdf.ln(6)
    pdf.set_font("Helvetica", size=9)
    pdf.multi_cell(0, 5, "Documento gerado automaticamente pelo sistema IA Trabalhista Robusta.")

    # fpdf2 retorna bytearray via output(dest="S")
    return bytes(pdf.output(dest="S"))

def generate_executive_pdf(case_data: dict, executive_data: dict) -> bytes:
    """
    PDF executivo.

    Estratégia:
    1) Tenta WeasyPrint (melhor layout), se o ambiente suportar libs nativas.
    2) Se falhar (ImportError/OSError), usa fallback pure-python (fpdf2) — sempre funciona no Railway.
    """
    try:
        from weasyprint import HTML  # type: ignore

        html_content = f"""
        <html><head><style>
          body {{ font-family: Arial, sans-serif; margin: 40px; color: #222; }}
          h1 {{ color: #111; border-bottom: 2px solid #000; padding-bottom: 5px; }}
          .section {{ margin-top: 25px; }}
          .highlight {{ font-weight: bold; color: #0b5394; }}
          .footer {{ margin-top: 50px; font-size: 12px; color: #666; }}
        </style></head><body>
          <h1>Relatório Executivo Jurídico</h1>
          <div class="section">
            <p><strong>Processo:</strong> {case_data.get("case_number")}</p>
            <p><strong>Título:</strong> {case_data.get("title")}</p>
            <p><strong>Data:</strong> {datetime.now().strftime("%d/%m/%Y %H:%M")}</p>
          </div>
          <div class="section"><h2>Resumo Estratégico</h2>
            <p>{executive_data.get("decision", {}).get("executive_summary", "")}</p>
          </div>
          <div class="section"><h2>Indicadores</h2>
            <p><span class="highlight">Probabilidade de Êxito:</span>
              { (executive_data.get("viability", {}).get("probability", 0) or 0) * 100:.0f}%</p>
            <p><span class="highlight">Status Final:</span>
              {executive_data.get("decision", {}).get("final_status", "Indefinido")}</p>
            <p><span class="highlight">Nível de Risco:</span>
              {executive_data.get("strategic", {}).get("risk_level", "Médio")}</p>
          </div>
          <div class="footer">Documento gerado automaticamente pelo sistema IA Trabalhista Robusta.</div>
        </body></html>
        """
        return HTML(string=html_content).write_pdf()
    except (ImportError, OSError):
        return _pdf_via_fpdf2(case_data, executive_data)
