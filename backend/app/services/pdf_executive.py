from datetime import datetime
from fastapi import HTTPException

def generate_executive_pdf(case_data: dict, executive_data: dict) -> bytes:
    """
    PDF executivo.
    Railway/Railpack pode não ter libs nativas do WeasyPrint (gobject/pango/cairo).
    Para não derrubar o app no boot, importamos WeasyPrint aqui dentro.
    """
    try:
        from weasyprint import HTML
    except (ImportError, OSError):
        raise HTTPException(
            status_code=503,
            detail="PDF temporariamente indisponível neste ambiente (dependências nativas do WeasyPrint ausentes).",
        )

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
          {executive_data.get("viability", {}).get("probability", 0) * 100:.0f}%</p>
        <p><span class="highlight">Status Final:</span>
          {executive_data.get("decision", {}).get("final_status", "Indefinido")}</p>
        <p><span class="highlight">Nível de Risco:</span>
          {executive_data.get("strategic", {}).get("risk_level", "Médio")}</p>
      </div>
      <div class="footer">Documento gerado automaticamente pelo sistema IA Trabalhista Robusta.</div>
    </body></html>
    """
    return HTML(string=html_content).write_pdf()
