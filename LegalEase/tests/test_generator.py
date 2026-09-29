"""Tests for GeminiDocumentGenerator and prompt logic."""
import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ai_core.gemini_generator import GeminiDocumentGenerator


@pytest.fixture
def generator():
    return GeminiDocumentGenerator()


def test_nda_generation(generator):
    """Test generating a Non-Disclosure Agreement."""
    res = generator.generate_document(
        document_type="NDA",
        parties={"Disclosing": "Alpha Tech", "Receiving": "Beta Analytics"},
        terms="Non-disclosure of confidential algorithms; 2 years validity",
        effective_date="2026-10-01",
        additional_information={"governing_law": "State of California"}
    )
    assert res["success"] is True
    content = res["content"]
    assert "NDA" in content or "NON-DISCLOSURE" in content
    assert "Alpha Tech" in content
    assert "Beta Analytics" in content
    assert "2026-10-01" in content
    assert "State of California" in content
    assert "SUMMARY OF KEY TERMS" in content
    assert "SIGNATURE BLOCKS" in content
    assert "LEGAL DISCLAIMER" in content


def test_employment_contract_generation(generator):
    """Test generating an Employment Contract."""
    res = generator.generate_document(
        document_type="Employment Contract",
        parties={
            "Employer": "Tech Innovations Inc.",
            "Employee": "John Doe"
        },
        terms="Full time 40 hours per week; Annual salary $120,000; At-will termination with 2 weeks notice",
        effective_date="2026-11-01",
        additional_information={
            "compensation": "$120,000 per year",
            "termination": "Two weeks written notice"
        }
    )
    assert res["success"] is True
    content = res["content"]
    assert "EMPLOYMENT" in content
    assert "Tech Innovations" in content
    assert "John Doe" in content
    assert "COMPENSATION" in content
    assert "SIGNATURE BLOCKS" in content


def test_lease_agreement_generation(generator):
    """Test generating a Lease Agreement."""
    res = generator.generate_document(
        document_type="Lease Agreement",
        parties=[
            {"name": "Landlord Properties LLC", "role": "Landlord"},
            {"name": "Robert Smith", "role": "Tenant"}
        ],
        terms="Monthly rent $2,500 due on 1st; Security deposit $2,500; No subleasing without written consent",
        effective_date="2026-12-01",
        additional_information={"governing_law": "State of Florida"}
    )
    assert res["success"] is True
    content = res["content"]
    assert "LEASE" in content
    assert "Landlord Properties" in content
    assert "Robert Smith" in content
    assert "State of Florida" in content
    assert "PREMISES" in content


def test_freelance_service_agreement_generation(generator):
    """Test generating a Freelance Work Contract."""
    res = generator.generate_document(
        document_type="Freelance Work Contract",
        parties="Client: Modern Studios\nContractor: Alice Wonder",
        terms="Deliver website redesign within 30 days; 50% upfront deposit; Client owns final intellectual property",
        effective_date="2026-10-20"
    )
    assert res["success"] is True
    content = res["content"]
    assert "FREELANCE" in content or "CONTRACT" in content
    assert "Modern Studios" in content
    assert "Alice Wonder" in content
    assert "INDEPENDENT CONTRACTOR" in content
    assert "INTELLECTUAL PROPERTY" in content


def test_missing_jurisdiction_flagging(generator):
    """Test that missing jurisdiction is explicitly flagged rather than invented."""
    res = generator.generate_document(
        document_type="Service Agreement",
        parties={"Client": "Enterprise Co", "Vendor": "Cloud Services Inc"},
        terms="Deliver monthly reporting; Net 30 payment terms",
        effective_date="2026-10-01",
        additional_information=None  # No jurisdiction provided
    )
    assert res["success"] is True
    content = res["content"]
    assert "[CONFIRM: Governing Jurisdiction" in content


def test_semicolon_terms_table_creation(generator):
    """Test that semicolon-delimited terms are converted into table rows."""
    terms_input = "Clause A payment in 15 days; Clause B delivery on Friday; Clause C warranty for 1 year"
    res = generator.generate_document(
        document_type="Contract",
        parties={"P1": "Alpha", "P2": "Omega"},
        terms=terms_input,
        effective_date="2026-10-01"
    )
    content = res["content"]
    assert "| 1 |" in content or "| Clause 1 |" in content
    assert "| 2 |" in content or "| Clause 2 |" in content
    assert "| 3 |" in content or "| Clause 3 |" in content
