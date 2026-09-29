"""Text utilities for sanitization and parsing."""
import re
import html
from typing import List, Dict, Any


def sanitize_text(text: str) -> str:
    """
    Sanitizes user and AI generated text.
    - Normalizes typographic quotes and dashes.
    - Removes control characters while preserving newlines and tabs.
    - Strips dangerous HTML tags or script injection attempts.
    - Normalizes consecutive blank lines and trailing whitespaces.
    """
    if not text:
        return ""

    # Replace typographic/curly quotes and apostrophes
    replacements = {
        "\u2018": "'",  # Left single quotation mark
        "\u2019": "'",  # Right single quotation mark
        "\u201c": '"',  # Left double quotation mark
        "\u201d": '"',  # Right double quotation mark
        "\u2013": "-",  # En dash
        "\u2014": "--", # Em dash
        "\u2026": "...",# Horizontal ellipsis
        "\u00a0": " ",  # Non-breaking space
        "\u2022": "*",  # Bullet
        "\ufeff": "",   # Byte order mark
    }
    for char, rep in replacements.items():
        text = text.replace(char, rep)

    # Remove script tags and embedded scripts
    text = re.sub(r"<\s*script[^>]*>.*?<\s*/\s*script\s*>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<\s*iframe[^>]*>.*?<\s*/\s*iframe\s*>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"on\w+\s*=\s*['\"][^'\"]*['\"]", "", text, flags=re.IGNORECASE)
    text = re.sub(r"javascript:\s*", "", text, flags=re.IGNORECASE)

    # Filter out non-printable ASCII control characters except \n, \r, \t
    cleaned_chars = []
    for ch in text:
        code = ord(ch)
        if code in (9, 10, 13) or code >= 32:
            cleaned_chars.append(ch)
    text = "".join(cleaned_chars)

    # Normalize line breaks to \n
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Strip trailing whitespace on each line
    lines = [line.rstrip() for line in text.split("\n")]
    text = "\n".join(lines)

    # Normalize multiple consecutive empty lines to max 2
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def parse_terms_list(terms_input: str) -> List[str]:
    """
    Converts user-entered terms (semicolon-separated, newline-separated, or bulleted)
    into a structured list of individual clean clauses.
    """
    if not terms_input:
        return []

    cleaned_input = sanitize_text(terms_input)
    raw_terms: List[str] = []

    # If semicolons are present, prioritize semicolon splitting
    if ";" in cleaned_input:
        parts = cleaned_input.split(";")
        raw_terms.extend(parts)
    else:
        # Otherwise split by newlines
        parts = cleaned_input.split("\n")
        raw_terms.extend(parts)

    formatted_terms: List[str] = []
    for item in raw_terms:
        term = item.strip()
        # Remove bullet points, numbers like "1.", "1)", "-", "*"
        term = re.sub(r"^(\d+[\.\)]|\-|\*|\•)\s*", "", term).strip()
        if term:
            # Capitalize first letter if not already
            if len(term) > 1:
                term = term[0].upper() + term[1:]
            formatted_terms.append(term)

    return formatted_terms


def extract_terms_table(text: str, default_terms: List[str] = None) -> List[Dict[str, Any]]:
    """
    Extracts terms table data as a list of dicts.
    If markdown table format exists in text, parses it.
    Otherwise uses default_terms or parsed clauses.
    """
    table_rows: List[Dict[str, Any]] = []

    # Check for markdown table in text
    table_regex = re.search(r"\|.*No\.?.*\|.*Term.*\|[\s\S]*?(?=\n\s*\n|\Z)", text, re.IGNORECASE)
    if table_regex:
        table_block = table_regex.group(0)
        lines = [line.strip() for line in table_block.strip().split("\n") if line.strip()]
        # Skip header and divider lines
        for line in lines:
            if not line.startswith("|") or "---" in line or "No." in line or "Term" in line:
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) >= 2:
                no = cells[0]
                term_desc = cells[1]
                table_rows.append({"no": no, "term": term_desc})

    if not table_rows and default_terms:
        for idx, term in enumerate(default_terms, 1):
            table_rows.append({"no": str(idx), "term": term})

    return table_rows
