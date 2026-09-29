"""Backend tests for LegalEase FastAPI routes and validation."""
import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app

client = TestClient(app)


def test_root_health_check():
    """Verify GET / returns online status and registered endpoints."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "LegalEase" in data["app"]
    assert "endpoints" in data


def test_detailed_health_check():
    """Verify GET /health returns detailed status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "gemini_api_configured" in data


def test_generate_document_success():
    """Verify POST /generate produces a structured legal document."""
    payload = {
        "document_type": "NDA",
        "parties": {
            "disclosing_party": "Apex Technologies LLC",
            "receiving_party": "Bright Star Systems Inc."
        },
        "terms": "Maintain absolute confidentiality of technical specs; 2 years duration; Delaware law",
        "effective_date": "2026-10-15",
        "additional_information": {
            "governing_law": "State of Delaware",
            "confidentiality": "Strict standard of care applies"
        }
    }
    response = client.post("/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["document_type"] == "NDA"
    assert len(data["content"]) > 100
    assert "Apex Technologies" in data["content"]
    assert "Bright Star Systems" in data["content"]


def test_generate_document_missing_doc_type():
    """Verify validation failure when document_type is empty or missing."""
    payload = {
        "document_type": "",
        "parties": "Party A and Party B",
        "terms": "Some terms",
        "effective_date": "2026-10-15"
    }
    response = client.post("/generate", json=payload)
    assert response.status_code == 422


def test_generate_document_missing_terms():
    """Verify validation failure when terms are empty."""
    payload = {
        "document_type": "Contract",
        "parties": "Party A and Party B",
        "terms": "",
        "effective_date": "2026-10-15"
    }
    response = client.post("/generate", json=payload)
    assert response.status_code == 422


def test_generate_document_missing_effective_date():
    """Verify validation failure when effective_date is missing."""
    payload = {
        "document_type": "Contract",
        "parties": "Party A and Party B",
        "terms": "Term 1; Term 2",
        "effective_date": ""
    }
    response = client.post("/generate", json=payload)
    assert response.status_code == 422


def test_preview_html_endpoint():
    """Verify POST /preview/html returns sanitized HTML structure."""
    payload = {
        "content": "# TEST TITLE\n\nThis is paragraph content.\n- Bullet clause",
        "document_type": "Test Agreement",
        "company_name": "Test Firm LLC"
    }
    response = client.post("/preview/html", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "<h1 class=\"doc-title\">TEST TITLE</h1>" in data["html"]
    assert "Test Firm LLC" in data["html"]


def test_export_docx_endpoint():
    """Verify POST /export/docx returns valid binary DOCX content."""
    payload = {
        "content": "# EMPLOYMENT AGREEMENT\n\nEffective Date: 2026-10-01\n\nParties: Employer and Employee",
        "document_type": "Employment Agreement",
        "company_name": "LegalEase Corp"
    }
    response = client.post("/export/docx", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    assert len(response.content) > 1000


def test_export_pdf_endpoint():
    """Verify POST /export/pdf returns valid binary PDF content."""
    payload = {
        "content": "# LEASE AGREEMENT\n\nEffective Date: 2026-10-01\n\nParties: Landlord and Tenant",
        "document_type": "Lease Agreement",
        "company_name": "LegalEase Corp"
    }
    response = client.post("/export/pdf", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")
