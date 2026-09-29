"""Formatting tests for HTML, DOCX, and PDF generators."""
import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.text_utils import sanitize_text, parse_terms_list, extract_terms_table
from utils.document_formatter import format_html_preview, format_docx
from utils.pdf_generator import format_pdf


def test_sanitize_text_normalizes_quotes_and_dashes():
    """Verify typographic quotes, dashes, and ellipses are normalized."""
    raw = "Here is ‘single’ and “double” quote with an em—dash and ellipsis…"
    cleaned = sanitize_text(raw)
    assert "‘" not in cleaned
    assert "’" not in cleaned
    assert "“" not in cleaned
    assert "”" not in cleaned
    assert "—" not in cleaned
    assert "…" not in cleaned
    assert "'single'" in cleaned
    assert '"double"' in cleaned
    assert "..." in cleaned


def test_sanitize_text_strips_xss_scripts():
    """Verify malicious script injection is thoroughly removed."""
    malicious = "<script>alert('pwned')</script>Hello <iframe src='evil.com'></iframe><b onclick='steal()'>Legal</b>"
    cleaned = sanitize_text(malicious)
    assert "<script>" not in cleaned
    assert "alert" not in cleaned
    assert "<iframe" not in cleaned
    assert "onclick=" not in cleaned
    assert "Legal" in cleaned


def test_parse_terms_list_semicolons():
    """Verify semicolon-delimited clauses are converted into structured lists."""
    raw = "Payment within 30 days; Delivery by Friday; Termination on 10 days notice;"
    terms = parse_terms_list(raw)
    assert len(terms) == 3
    assert terms[0] == "Payment within 30 days"
    assert terms[1] == "Delivery by Friday"
    assert terms[2] == "Termination on 10 days notice"


def test_parse_terms_list_bullets_and_newlines():
    """Verify newline-delimited and bulleted clauses are properly parsed."""
    raw = """1. Clause number one
- Clause number two
* Clause number three"""
    terms = parse_terms_list(raw)
    assert len(terms) == 3
    assert terms[0] == "Clause number one"
    assert terms[1] == "Clause number two"
    assert terms[2] == "Clause number three"


def test_extract_terms_table():
    """Verify table extraction from markdown text."""
    md_text = """
| No. | Term | Details |
|---|---|---|
| 1 | Payment | Net 30 days |
| 2 | Confidentiality | 2 years |
"""
    rows = extract_terms_table(md_text)
    assert len(rows) >= 2
    assert rows[0]["no"] == "1"
    assert "Payment" in rows[0]["term"]


def test_format_html_preview_structure():
    """Verify HTML preview contains title, tables, and disclaimer."""
    doc_text = """# TEST LEGAL CONTRACT

Effective Date: 2026-10-01

### 1. SCOPE
The parties agree to perform.
- Item one
- Item two

| No. | Clause |
|---|---|
| 1 | Term Alpha |

LEGAL DISCLAIMER: Review with counsel.
"""
    html_out = format_html_preview(doc_text, company_name="Lex Corp")
    assert "<h1 class=\"doc-title\">TEST LEGAL CONTRACT</h1>" in html_out
    assert "<li class=\"doc-bullet\">Item one</li>" in html_out
    assert "<table class=\"legal-table\">" in html_out
    assert "DISCLAIMER:" in html_out
    assert "Lex Corp" in html_out


def test_format_docx_generation():
    """Verify DOCX binary output is generated properly."""
    doc_text = """# NON-DISCLOSURE AGREEMENT

Effective Date: 2026-10-01

### PARTIES
Acme Corp and Beta LLC.

### 1. CONFIDENTIALITY
Information must remain protected.

| No. | Term | Details |
|---|---|---|
| 1 | Non-disclosure | 2 years |
"""
    logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", "logo", "legalease_logo.png")
    docx_bytes = format_docx(
        text=doc_text,
        doc_type="NDA",
        logo_path=logo_path if os.path.exists(logo_path) else None,
        company_name="Acme Legal",
        font_name="Times New Roman"
    )
    assert isinstance(docx_bytes, bytes)
    assert len(docx_bytes) > 2000


def test_format_pdf_generation_multi_page():
    """Verify PDF binary output is generated and handles long documents without error."""
    long_paragraphs = "\n\n".join([f"### {idx}. SECTION {idx}\nThis is a detailed paragraph explaining clause {idx} with extensive commercial legal language." for idx in range(1, 15)])
    doc_text = f"""# MASTER SERVICES AGREEMENT

Effective Date: 2026-10-01

{long_paragraphs}

| No. | Clause | Obligation |
|---|---|---|
| 1 | Payment | Monthly invoicing |
| 2 | Notice | 30 days written |

LEGAL DISCLAIMER: Consult qualified legal counsel.
"""
    logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", "logo", "legalease_logo.png")
    pdf_bytes = format_pdf(
        text=doc_text,
        doc_type="Master Services Agreement",
        logo_path=logo_path if os.path.exists(logo_path) else None,
        company_name="Apex Global"
    )
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 4000
