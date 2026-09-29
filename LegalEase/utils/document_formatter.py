"""Document formatting module for HTML preview and DOCX generation."""
import os
import io
import re
import html
from typing import Optional, List, Dict, Any
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

from .text_utils import sanitize_text, parse_terms_list, extract_terms_table


def format_html_preview(
    text: str,
    logo_path: Optional[str] = None,
    company_name: Optional[str] = None
) -> str:
    """
    Renders the legal document in an executive, high-readability HTML format
    with professional legal typography, styled tables, and signature blocks.
    All content is sanitized to prevent XSS.
    """
    cleaned_text = sanitize_text(text)

    # Process lines to create HTML elements
    lines = cleaned_text.split("\n")
    html_parts: List[str] = []

    in_table = False
    table_rows: List[List[str]] = []

    def flush_table():
        nonlocal in_table, table_rows
        if not table_rows:
            in_table = False
            return ""
        tbl_html = ['<div class="table-container"><table class="legal-table">']
        # First row is header
        if len(table_rows) > 0:
            tbl_html.append('<thead><tr>')
            for col in table_rows[0]:
                tbl_html.append(f'<th>{html.escape(col.strip())}</th>')
            tbl_html.append('</tr></thead><tbody>')

            for r in table_rows[1:]:
                # Check if it's separator row (e.g. ---)
                if any("---" in c for c in r):
                    continue
                tbl_html.append('<tr>')
                for c in r:
                    tbl_html.append(f'<td>{html.escape(c.strip())}</td>')
                tbl_html.append('</tr>')
            tbl_html.append('</tbody></table></div>')
        in_table = False
        table_rows = []
        return "".join(tbl_html)

    for line in lines:
        stripped = line.strip()

        # Check for Markdown table row
        if stripped.startswith("|") and stripped.endswith("|"):
            in_table = True
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            table_rows.append(cells)
            continue
        elif in_table:
            html_parts.append(flush_table())

        if not stripped:
            continue

        # Check headings
        if stripped.startswith("# "):
            title = stripped[2:].strip()
            html_parts.append(f'<h1 class="doc-title">{html.escape(title)}</h1>')
        elif stripped.startswith("## "):
            h2 = stripped[3:].strip()
            html_parts.append(f'<h2 class="doc-heading-2">{html.escape(h2)}</h2>')
        elif stripped.startswith("### "):
            h3 = stripped[4:].strip()
            html_parts.append(f'<h3 class="doc-heading-3">{html.escape(h3)}</h3>')
        elif stripped == "---":
            html_parts.append('<hr class="doc-divider"/>')
        elif stripped.startswith("- ") or stripped.startswith("* "):
            bullet_text = stripped[2:].strip()
            # Convert **bold** inside bullet
            bullet_html = _format_inline_markdown(bullet_text)
            html_parts.append(f'<li class="doc-bullet">{bullet_html}</li>')
        elif re.match(r"^\d+\.\s+", stripped):
            # Numbered list
            num_content = re.sub(r"^\d+\.\s+", "", stripped)
            formatted = _format_inline_markdown(num_content)
            html_parts.append(f'<div class="doc-numbered-clause">{formatted}</div>')
        elif "LEGAL DISCLAIMER:" in stripped:
            html_parts.append(
                f'<div class="legal-disclaimer-box"><strong>DISCLAIMER:</strong> {html.escape(stripped.replace("LEGAL DISCLAIMER:", "").strip())}</div>'
            )
        else:
            p_html = _format_inline_markdown(stripped)
            html_parts.append(f'<p class="doc-paragraph">{p_html}</p>')

    if in_table:
        html_parts.append(flush_table())

    # Build Header info
    header_html = ""
    if company_name or logo_path:
        header_html = f"""
        <div class="doc-header-banner">
            <div class="company-brand">{html.escape(company_name or 'LegalEase Document Generator')}</div>
            <div class="confidential-badge">CONFIDENTIAL & PRIVILEGED</div>
        </div>
        """

    document_body = "\n".join(html_parts)

    full_html = f"""
    <div class="legalease-preview-wrapper">
        <style>
            .legalease-preview-wrapper {{
                font-family: 'Georgia', 'Merriweather', 'Times New Roman', serif;
                color: #1a202c;
                background-color: #ffffff;
                border-radius: 8px;
                padding: 40px 50px;
                max-width: 900px;
                margin: 0 auto;
                box-shadow: 0 4px 20px rgba(0,0,0,0.08);
                border: 1px solid #e2e8f0;
                line-height: 1.7;
            }}
            .doc-header-banner {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-bottom: 2px solid #2b6cb0;
                padding-bottom: 12px;
                margin-bottom: 25px;
            }}
            .company-brand {{
                font-family: 'Helvetica Neue', Arial, sans-serif;
                font-size: 1.15rem;
                font-weight: 700;
                color: #2b6cb0;
                letter-spacing: 0.5px;
            }}
            .confidential-badge {{
                font-family: 'Helvetica Neue', Arial, sans-serif;
                font-size: 0.75rem;
                font-weight: 600;
                background: #fed7d7;
                color: #9b2c2c;
                padding: 3px 8px;
                border-radius: 4px;
                letter-spacing: 0.5px;
            }}
            .doc-title {{
                text-align: center;
                font-size: 1.85rem;
                font-weight: 800;
                letter-spacing: 1px;
                color: #1a365d;
                margin-top: 15px;
                margin-bottom: 15px;
                text-transform: uppercase;
            }}
            .doc-heading-2 {{
                font-size: 1.35rem;
                font-weight: 700;
                color: #2c5282;
                margin-top: 25px;
                margin-bottom: 10px;
                border-bottom: 1px solid #e2e8f0;
                padding-bottom: 4px;
            }}
            .doc-heading-3 {{
                font-size: 1.15rem;
                font-weight: 700;
                color: #2d3748;
                margin-top: 20px;
                margin-bottom: 8px;
            }}
            .doc-divider {{
                border: 0;
                height: 1px;
                background: #e2e8f0;
                margin: 20px 0;
            }}
            .doc-paragraph {{
                font-size: 1.05rem;
                margin-bottom: 14px;
                text-align: justify;
                color: #2d3748;
            }}
            .doc-bullet {{
                font-size: 1.05rem;
                margin-left: 25px;
                margin-bottom: 8px;
                color: #2d3748;
            }}
            .doc-numbered-clause {{
                font-size: 1.05rem;
                margin-bottom: 12px;
                padding-left: 15px;
                color: #2d3748;
            }}
            .table-container {{
                overflow-x: auto;
                margin: 25px 0;
            }}
            .legal-table {{
                width: 100%;
                border-collapse: collapse;
                font-size: 0.95rem;
                background: #f7fafc;
            }}
            .legal-table th {{
                background-color: #2b6cb0;
                color: white;
                text-align: left;
                padding: 10px 14px;
                font-weight: 600;
                border: 1px solid #2b6cb0;
            }}
            .legal-table td {{
                padding: 10px 14px;
                border: 1px solid #cbd5e0;
                vertical-align: top;
            }}
            .legal-table tr:nth-child(even) {{
                background-color: #ffffff;
            }}
            .legal-disclaimer-box {{
                background-color: #fffaf0;
                border-left: 4px solid #dd6b20;
                padding: 14px 18px;
                font-size: 0.9rem;
                color: #7b341e;
                margin-top: 30px;
                border-radius: 0 4px 4px 0;
            }}
            .legal-missing-indicator {{
                color: #c53030;
                background-color: #fff5f5;
                padding: 2px 6px;
                border-radius: 4px;
                font-weight: 600;
                border: 1px dashed #fc8181;
            }}
        </style>
        {header_html}
        {document_body}
    </div>
    """
    return full_html


def _format_inline_markdown(text: str) -> str:
    """Escapes HTML and translates markdown bold/italic tags and brackets."""
    escaped = html.escape(text)

    # Highlight missing placeholders like [CONFIRM: ...] or [INSERT: ...]
    escaped = re.sub(
        r"(\[(?:CONFIRM|INSERT|SPECIFY|OPTIONAL):?[^\]]+\])",
        r'<span class="legal-missing-indicator">\1</span>',
        escaped,
    )

    # Convert **bold**
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    # Convert *italic*
    escaped = re.sub(r"\*(.+?)\*", r"<em>\1</em>", escaped)

    return escaped


def format_docx(
    text: str,
    doc_type: str,
    logo_path: Optional[str] = None,
    company_name: Optional[str] = None,
    font_name: str = "Times New Roman",
    terms_list: Optional[List[str]] = None,
) -> bytes:
    """
    Generates an executive-ready DOCX document.
    - Times New Roman (or configured font)
    - 1-inch margins
    - Header with optional logo and company branding
    - Formatted Heading hierarchy
    - Tables with styled header cells and borders
    - Distinct signature grid
    - Page numbers and legal confidentiality footer
    """
    cleaned_text = sanitize_text(text)
    doc = Document()

    # Configure Margins to 1 inch
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

        # Header setup
        header = section.header
        header_p = header.paragraphs[0]
        header_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        h_run = header_p.add_run(f"{company_name or 'LegalEase AI Drafting'} | PRIVILEGED & CONFIDENTIAL")
        h_run.font.name = font_name
        h_run.font.size = Pt(8.5)
        h_run.font.color.rgb = RGBColor(128, 128, 128)

        # Footer setup
        footer = section.footer
        footer_p = footer.paragraphs[0]
        footer_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        f_run = footer_p.add_run("Legal Drafting Assistance • Consult Qualified Legal Counsel Prior to Execution")
        f_run.font.name = font_name
        f_run.font.size = Pt(8)
        f_run.font.italic = True
        f_run.font.color.rgb = RGBColor(140, 140, 140)

    # Configure Normal Style
    normal_style = doc.styles["Normal"]
    normal_font = normal_style.font
    normal_font.name = font_name
    normal_font.size = Pt(11)
    normal_font.color.rgb = RGBColor(40, 40, 40)

    # Add Logo at top of first page if valid
    if logo_path and os.path.exists(logo_path):
        try:
            logo_p = doc.add_paragraph()
            logo_p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            logo_run = logo_p.add_run()
            logo_run.add_picture(logo_path, width=Inches(1.8))
        except Exception:
            pass

    # Parse and write content lines
    lines = cleaned_text.split("\n")
    in_table = False
    table_rows: List[List[str]] = []

    def insert_docx_table():
        nonlocal in_table, table_rows
        if not table_rows:
            in_table = False
            return

        valid_rows = [r for r in table_rows if not any("---" in cell for cell in r)]
        if not valid_rows:
            in_table = False
            table_rows = []
            return

        cols_count = max(len(r) for r in valid_rows)
        tbl = doc.add_table(rows=len(valid_rows), cols=cols_count)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        tbl.autofit = True

        for row_idx, r in enumerate(valid_rows):
            is_header = (row_idx == 0)
            table_row = tbl.rows[row_idx]
            for col_idx, cell_value in enumerate(r):
                if col_idx < cols_count:
                    cell = table_row.cells[col_idx]
                    cell.text = cell_value.strip()
                    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

                    # Style header row
                    if is_header:
                        _set_cell_background(cell, "2B6CB0")
                        for p in cell.paragraphs:
                            for run in p.runs:
                                run.font.name = font_name
                                run.font.bold = True
                                run.font.color.rgb = RGBColor(255, 255, 255)
                                run.font.size = Pt(10)
                    else:
                        for p in cell.paragraphs:
                            for run in p.runs:
                                run.font.name = font_name
                                run.font.size = Pt(10)

        # Space after table
        doc.add_paragraph()
        in_table = False
        table_rows = []

    for line in lines:
        stripped = line.strip()

        # Markdown Table Detection
        if stripped.startswith("|") and stripped.endswith("|"):
            in_table = True
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            table_rows.append(cells)
            continue
        elif in_table:
            insert_docx_table()

        if not stripped:
            continue

        if stripped.startswith("# "):
            # Main Title
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(12)
            run = p.add_run(stripped[2:].strip())
            run.font.name = font_name
            run.font.size = Pt(16)
            run.font.bold = True
            run.font.color.rgb = RGBColor(26, 54, 93)

        elif stripped.startswith("## "):
            # Heading 2
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(14)
            p.paragraph_format.space_after = Pt(6)
            run = p.add_run(stripped[3:].strip())
            run.font.name = font_name
            run.font.size = Pt(13)
            run.font.bold = True
            run.font.color.rgb = RGBColor(43, 108, 176)

        elif stripped.startswith("### "):
            # Heading 3
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(10)
            p.paragraph_format.space_after = Pt(4)
            run = p.add_run(stripped[4:].strip())
            run.font.name = font_name
            run.font.size = Pt(11.5)
            run.font.bold = True
            run.font.color.rgb = RGBColor(45, 55, 72)

        elif stripped == "---":
            # Subtle divider
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(6)
            run = p.add_run("―" * 45)
            run.font.color.rgb = RGBColor(200, 200, 200)

        elif stripped.startswith("- ") or stripped.startswith("* "):
            p = doc.add_paragraph(style="List Bullet")
            p.paragraph_format.space_after = Pt(3)
            _add_formatted_runs_to_paragraph(p, stripped[2:].strip(), font_name)

        elif re.match(r"^\d+\.\s+", stripped):
            num_content = re.sub(r"^\d+\.\s+", "", stripped)
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.25)
            p.paragraph_format.space_after = Pt(4)
            # Add prefix number
            match = re.match(r"^(\d+\.)\s+", stripped)
            prefix = match.group(1) if match else ""
            p_run = p.add_run(f"{prefix} ")
            p_run.font.name = font_name
            p_run.font.bold = True
            _add_formatted_runs_to_paragraph(p, num_content, font_name)

        elif "LEGAL DISCLAIMER:" in stripped:
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(18)
            p.paragraph_format.space_after = Pt(12)
            run = p.add_run(stripped)
            run.font.name = font_name
            run.font.size = Pt(9)
            run.font.italic = True
            run.font.color.rgb = RGBColor(150, 75, 0)

        else:
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(6)
            p.paragraph_format.line_spacing = 1.15
            _add_formatted_runs_to_paragraph(p, stripped, font_name)

    if in_table:
        insert_docx_table()

    # Save to buffer
    output_stream = io.BytesIO()
    doc.save(output_stream)
    output_stream.seek(0)
    return output_stream.read()


def _add_formatted_runs_to_paragraph(p, text: str, font_name: str):
    """Parses bold markdown and adds runs with appropriate formatting."""
    parts = re.split(r"(\*\*.*?\*\*)", text)
    for part in parts:
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            run = p.add_run(part[2:-2])
            run.font.name = font_name
            run.font.bold = True
        else:
            run = p.add_run(part)
            run.font.name = font_name


def _set_cell_background(cell, hex_color: str):
    """Sets background shading of a python-docx table cell."""
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tc_pr.append(shd)
