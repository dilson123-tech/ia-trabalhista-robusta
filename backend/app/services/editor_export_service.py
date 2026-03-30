from __future__ import annotations

from html import escape
from typing import Dict, List


def _normalize_html_text(value: str | None) -> str:
    if not value:
        return "<p></p>"
    return value.strip()


def build_editor_html(document: dict, version: dict) -> str:
    title = escape(document.get("title", "Documento Jurídico"))
    area = escape(document.get("area", "Jurídico"))
    document_type = escape(document.get("document_type", "Documento"))
    version_number = version.get("version_number", "-")
    sections: List[Dict] = version.get("sections", [])

    html_sections: list[str] = []

    for index, section in enumerate(sections, start=1):
        section_title = escape(section.get("title", f"Seção {index}"))
        content = _normalize_html_text(section.get("content", ""))

        html_sections.append(
            f"""
            <section class="doc-section">
                <h2>{index}. {section_title}</h2>
                <div class="doc-content">
                    {content}
                </div>
            </section>
            """
        )

    rendered_sections = "\n".join(html_sections) if html_sections else """
        <section class="doc-section">
            <h2>1. Conteúdo</h2>
            <div class="doc-content">
                <p>Documento sem conteúdo disponível para exportação.</p>
            </div>
        </section>
    """

    return f"""
    <html lang="pt-BR">
        <head>
            <meta charset="utf-8">
            <title>{title}</title>
            <style>
                body {{
                    font-family: Arial, Helvetica, sans-serif;
                    color: #111;
                    background: #fff;
                    margin: 0;
                    padding: 40px;
                    line-height: 1.65;
                    font-size: 12px;
                }}

                .doc-shell {{
                    max-width: 860px;
                    margin: 0 auto;
                }}

                .doc-header {{
                    border-bottom: 2px solid #111;
                    padding-bottom: 16px;
                    margin-bottom: 28px;
                }}

                .doc-kicker {{
                    font-size: 11px;
                    text-transform: uppercase;
                    letter-spacing: 0.08em;
                    margin-bottom: 8px;
                }}

                h1 {{
                    font-size: 24px;
                    margin: 0 0 10px 0;
                }}

                .doc-meta {{
                    font-size: 11px;
                    color: #333;
                }}

                .doc-section {{
                    margin-bottom: 24px;
                }}

                .doc-section h2 {{
                    font-size: 15px;
                    margin: 0 0 10px 0;
                }}

                .doc-content p {{
                    margin: 0 0 12px 0;
                }}

                .doc-content ul,
                .doc-content ol {{
                    margin: 0 0 12px 20px;
                }}

                .doc-footer {{
                    border-top: 1px solid #bbb;
                    margin-top: 32px;
                    padding-top: 12px;
                    font-size: 10px;
                    color: #555;
                }}
            </style>
        </head>
        <body>
            <main class="doc-shell">
                <header class="doc-header">
                    <div class="doc-kicker">IA Trabalhista Robusta</div>
                    <h1>{title}</h1>
                    <div class="doc-meta">
                        Área: {area} · Tipo: {document_type} · Versão aprovada: {version_number}
                    </div>
                </header>

                {rendered_sections}

                <footer class="doc-footer">
                    Documento final exportado a partir da versão aprovada do Editor Jurídico Vivo.
                </footer>
            </main>
        </body>
    </html>
    """


def generate_editor_pdf(html: str) -> bytes:
    try:
        from weasyprint import HTML
        return HTML(string=html).write_pdf()
    except (ImportError, OSError):
        from fpdf import FPDF

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=10)

        # fallback simples: remove tags básicas
        import re
        clean = re.sub("<[^<]+?>", "", html)

        for line in clean.split("\n"):
            pdf.multi_cell(0, 5, line)

        return bytes(pdf.output(dest="S"))
