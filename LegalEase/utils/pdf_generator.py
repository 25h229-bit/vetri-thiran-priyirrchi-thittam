"""PDF generation module using fpdf2 for LegalEase."""
import os
import re
from typing import Optional, List
from fpdf import FPDF
from fpdf.enums import XPos, YPos

from .text_utils import sanitize_text


class LegalPDF(FPDF):
    """Custom FPDF class with legal-styled headers, footers, and page numbers."""

    def __init__(self, company_name: Optional[str] = None, logo_path: Optional[str] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.company_name = company_name or "LegalEase AI Legal Systems"
        self.logo_path = logo_path
        self.set_auto_page_break(auto=True, margin=22)

    def header(self):
        # Top banner on all pages
        self.set_font("helvetica", "B", 8)
        self.set_text_color(100, 110, 125)

        # Optional Logo
        if self.logo_path and os.path.exists(self.logo_path):
            try:
                # Add logo top left
                self.image(self.logo_path, x=15, y=8, h=9)
            except Exception:
                pass

        # Company branding top right
        self.set_xy(15, 8)
        self.cell(180, 8, f"{self.company_name.upper()} | PRIVILEGED & CONFIDENTIAL", align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Subtle rule
        self.set_draw_color(220, 225, 235)
        self.set_line_width(0.3)
        self.line(15, 18, 195, 18)
        self.ln(6)

    def footer(self):
        # Position at 15 mm from bottom
        self.set_y(-16)
        self.set_draw_color(220, 225, 235)
        self.set_line_width(0.3)
        self.line(15, self.get_y(), 195, self.get_y())
        self.ln(2)

        self.set_font("helvetica", "I", 7.5)
        self.set_text_color(140, 140, 140)

        # Left: Legal disclaimer
        self.cell(130, 6, "Legal Drafting Assistance - Consult Qualified Legal Counsel Prior to Execution", align="L")
        # Right: Page X of Y
        page_str = f"Page {self.page_no()}/{{nb}}"
        self.cell(50, 6, page_str, align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)


def _safe_fpdf_text(text: str) -> str:
    """Replaces characters not supported by standard PDF latin-1 font."""
    if not text:
        return ""
    # Mapping for common unicode characters
    charmap = {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "--",
        "\u2026": "...",
        "\u00a0": " ",
        "\u2022": "*",
        "\u2122": "(TM)",
        "\u00a9": "(c)",
        "\u00ae": "(R)",
        "€": "EUR",
        "£": "GBP",
        "\t": "    ",
    }
    for k, v in charmap.items():
        text = text.replace(k, v)

    # Encode to latin-1, replace unsupported characters with ?
    return text.encode("latin-1", errors="replace").decode("latin-1")


def format_pdf(
    text: str,
    doc_type: str,
    logo_path: Optional[str] = None,
    company_name: Optional[str] = None,
    terms_list: Optional[List[str]] = None,
) -> bytes:
    """
    Renders professional PDF legal document using fpdf2.
    - Margins: 15mm
    - Clean typography with proper hierarchy
    - Markdown table rendering
    - Multi-page wrapping
    - Clean signature blocks
    """
    cleaned_text = sanitize_text(text)
    safe_text = _safe_fpdf_text(cleaned_text)

    pdf = LegalPDF(company_name=company_name, logo_path=logo_path, orientation="P", unit="mm", format="A4")
    pdf.alias_nb_pages()
    pdf.set_margins(15, 18, 15)
    pdf.add_page()

    lines = safe_text.split("\n")
    in_table = False
    table_rows: List[List[str]] = []

    def flush_pdf_table():
        nonlocal in_table, table_rows
        if not table_rows:
            in_table = False
            return

        valid_rows = [r for r in table_rows if not any("---" in cell for cell in r)]
        if not valid_rows:
            in_table = False
            table_rows = []
            return

        # Widths: Total printable width ~ 180mm
        # If 3 columns: 18mm, 52mm, 110mm
        # If 2 columns: 35mm, 145mm
        cols_count = max(len(r) for r in valid_rows)
        if cols_count == 2:
            col_widths = [35, 145]
        elif cols_count == 3:
            col_widths = [18, 52, 110]
        else:
            col_widths = [180 / cols_count] * cols_count

        pdf.ln(3)
        for row_idx, r in enumerate(valid_rows):
            is_header = (row_idx == 0)

            # Check if page break needed
            if pdf.get_y() > 255:
                pdf.add_page()

            if is_header:
                pdf.set_fill_color(43, 108, 176)
                pdf.set_text_color(255, 255, 255)
                pdf.set_font("helvetica", "B", 9)
                row_height = 8
            else:
                if row_idx % 2 == 1:
                    pdf.set_fill_color(248, 250, 252)
                else:
                    pdf.set_fill_color(255, 255, 255)
                pdf.set_text_color(45, 55, 72)
                pdf.set_font("helvetica", "", 8.5)
                row_height = 7

            # Print cells
            start_x = pdf.get_x()
            start_y = pdf.get_y()

            # For multi-line last cell:
            if len(r) > 1 and len(r[-1]) > 50:
                # Print leading cells
                for c_idx in range(len(col_widths) - 1):
                    val = r[c_idx] if c_idx < len(r) else ""
                    pdf.cell(col_widths[c_idx], row_height, val, border=1, fill=True, align="C" if c_idx == 0 else "L")

                # Multi-cell for the long text column
                last_val = r[-1] if len(r) >= len(col_widths) else ""
                pdf.multi_cell(col_widths[-1], 5, last_val, border=1, fill=True, align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            else:
                for c_idx, width in enumerate(col_widths):
                    val = r[c_idx] if c_idx < len(r) else ""
                    align = "C" if c_idx == 0 else "L"
                    if c_idx == len(col_widths) - 1:
                        pdf.cell(width, row_height, val, border=1, fill=True, align=align, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                    else:
                        pdf.cell(width, row_height, val, border=1, fill=True, align=align)

        pdf.ln(4)
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
            flush_pdf_table()

        if not stripped:
            pdf.ln(2.5)
            continue

        if stripped.startswith("# "):
            # Main Title
            pdf.set_font("helvetica", "B", 16)
            pdf.set_text_color(26, 54, 93)
            title_text = stripped[2:].strip().upper()
            pdf.ln(3)
            pdf.cell(180, 9, title_text, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(2)

        elif stripped.startswith("## "):
            # Heading 2
            pdf.ln(4)
            pdf.set_font("helvetica", "B", 12)
            pdf.set_text_color(43, 108, 176)
            pdf.cell(180, 7, stripped[3:].strip(), align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(1)

        elif stripped.startswith("### "):
            # Heading 3
            pdf.ln(3)
            pdf.set_font("helvetica", "B", 10.5)
            pdf.set_text_color(45, 55, 72)
            pdf.cell(180, 6, stripped[4:].strip(), align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(1)

        elif stripped == "---":
            # Horizontal rule
            pdf.ln(2)
            pdf.set_draw_color(226, 232, 240)
            pdf.set_line_width(0.4)
            pdf.line(15, pdf.get_y(), 195, pdf.get_y())
            pdf.ln(3)

        elif stripped.startswith("- ") or stripped.startswith("* "):
            # Bullet point
            clean_bullet = _strip_markdown_bold(stripped[2:].strip())
            pdf.set_font("helvetica", "", 9.5)
            pdf.set_text_color(45, 55, 72)
            pdf.cell(6, 5, chr(149), align="R")
            pdf.multi_cell(174, 5, f" {clean_bullet}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        elif re.match(r"^\d+\.\s+", stripped):
            # Numbered clause
            clean_clause = _strip_markdown_bold(stripped)
            pdf.set_font("helvetica", "", 9.5)
            pdf.set_text_color(45, 55, 72)
            pdf.multi_cell(180, 5, clean_clause, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(1.5)

        elif "LEGAL DISCLAIMER:" in stripped:
            # Disclaimer Box
            pdf.ln(4)
            pdf.set_fill_color(255, 250, 240)
            pdf.set_draw_color(221, 107, 32)
            pdf.set_line_width(0.4)
            pdf.set_font("helvetica", "I", 8)
            pdf.set_text_color(123, 52, 30)
            pdf.multi_cell(180, 4.5, stripped, border=1, fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(3)

        else:
            # Regular paragraph
            clean_p = _strip_markdown_bold(stripped)
            pdf.set_font("helvetica", "", 9.5)
            pdf.set_text_color(45, 55, 72)
            pdf.multi_cell(180, 5.2, clean_p, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(1.5)

    if in_table:
        flush_pdf_table()

    # Return bytes
    return bytes(pdf.output())


def _strip_markdown_bold(text: str) -> str:
    """Removes ** and * markdown formatting symbols for clean plain PDF rendering."""
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    return text
