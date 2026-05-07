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
                @page {{
                    size: A4;
                    margin: 22mm 18mm 20mm 18mm;

                    @bottom-right {{
                        content: "Página " counter(page) " de " counter(pages);
                        color: #6b7280;
                        font-size: 9px;
                    }}

                    @bottom-left {{
                        content: "Editor Jurídico Vivo";
                        color: #6b7280;
                        font-size: 9px;
                    }}
                }}

                * {{
                    box-sizing: border-box;
                }}

                body {{
                    font-family: "Times New Roman", Georgia, serif;
                    color: #111827;
                    background: #ffffff;
                    margin: 0;
                    padding: 0;
                    line-height: 1.72;
                    font-size: 12.2px;
                    text-rendering: optimizeLegibility;
                }}

                .doc-shell {{
                    width: 100%;
                    margin: 0 auto;
                }}

                .doc-header {{
                    border-top: 4px solid #0f2f4a;
                    border-bottom: 1px solid #d1d5db;
                    padding: 14px 0 18px 0;
                    margin-bottom: 26px;
                    position: relative;
                }}

                .doc-header::after {{
                    content: "";
                    display: block;
                    width: 110px;
                    height: 3px;
                    background: #b08d2f;
                    margin-top: 14px;
                }}

                .doc-kicker {{
                    font-family: Arial, Helvetica, sans-serif;
                    font-size: 9.5px;
                    text-transform: uppercase;
                    letter-spacing: 0.16em;
                    color: #0f2f4a;
                    font-weight: 700;
                    margin-bottom: 8px;
                }}

                h1 {{
                    font-size: 21px;
                    line-height: 1.25;
                    margin: 0 0 12px 0;
                    font-weight: 700;
                    color: #111827;
                }}

                .doc-meta {{
                    display: inline-block;
                    font-family: Arial, Helvetica, sans-serif;
                    font-size: 10.2px;
                    color: #374151;
                    background: #f8fafc;
                    border: 1px solid #e5e7eb;
                    border-left: 3px solid #b08d2f;
                    padding: 7px 10px;
                    border-radius: 2px;
                }}

                .doc-section {{
                    margin-bottom: 25px;
                    page-break-inside: auto;
                    break-inside: auto;
                }}

                .doc-section h2 {{
                    font-family: Arial, Helvetica, sans-serif;
                    font-size: 12.5px;
                    line-height: 1.35;
                    margin: 0 0 11px 0;
                    padding: 7px 10px;
                    color: #0f172a;
                    background: #f9fafb;
                    border-left: 4px solid #0f2f4a;
                    border-bottom: 1px solid #e5e7eb;
                    text-transform: uppercase;
                    letter-spacing: 0.035em;
                }}

                .doc-content {{
                    white-space: pre-line;
                    text-align: justify;
                    orphans: 3;
                    widows: 3;
                }}

                .doc-content p {{
                    margin: 0 0 11px 0;
                }}

                .doc-content ul,
                .doc-content ol {{
                    margin: 0 0 12px 22px;
                    padding-left: 12px;
                }}

                .doc-content li {{
                    margin-bottom: 6px;
                }}

                .doc-footer {{
                    border-top: 1px solid #d1d5db;
                    margin-top: 34px;
                    padding-top: 10px;
                    font-family: Arial, Helvetica, sans-serif;
                    font-size: 9.5px;
                    color: #6b7280;
                }}
            </style>
        </head>
        <body>
            <main class="doc-shell">
                <header class="doc-header">
                    <div class="doc-kicker">Plataforma Jurídica Multiárea</div>
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
        import re
        import unicodedata

        def _pdf_safe_text(value: str) -> str:
            normalized = (
                value.replace("—", "-")
                .replace("–", "-")
                .replace("“", '"')
                .replace("”", '"')
                .replace("‘", "'")
                .replace("’", "'")
                .replace("•", "-")
                .replace("\u00a0", " ")
            )
            normalized = unicodedata.normalize("NFKD", normalized)
            return normalized.encode("latin-1", "ignore").decode("latin-1")

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Helvetica", size=10)

        clean = re.sub("<[^<]+?>", "", html)
        clean = _pdf_safe_text(clean)

        for raw_line in clean.split("\n"):
            line = raw_line.strip()
            if not line:
                pdf.ln(2)
                continue
            pdf.multi_cell(0, 5, line)

        output = pdf.output(dest="S")
        return output if isinstance(output, bytes) else output.encode("latin-1", "ignore")
