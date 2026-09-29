"""FastAPI route definitions and Pydantic schemas for LegalEase."""
import logging
from typing import Optional, Union, Dict, Any, List
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response
from pydantic import BaseModel, Field, field_validator

from ai_core.gemini_generator import GeminiDocumentGenerator
from utils.text_utils import sanitize_text, parse_terms_list
from utils.document_formatter import format_html_preview, format_docx
from utils.pdf_generator import format_pdf

logger = logging.getLogger("LegalEase.Routes")
router = APIRouter()


class DocumentRequest(BaseModel):
    """Input payload for generating a legal document."""
    document_type: str = Field(..., description="Document type (e.g. NDA, Employment Contract, Lease Agreement)")
    parties: Union[Dict[str, Any], List[Any], str] = Field(
        ..., description="Parties involved in the contract with names, roles, or details"
    )
    terms: Union[List[str], str] = Field(
        ..., description="Clauses, terms, or semicolon-separated requirements"
    )
    effective_date: str = Field(..., description="Effective date (YYYY-MM-DD or formatted string)")
    additional_information: Optional[Union[Dict[str, Any], str]] = Field(
        default=None, description="Optional extra parameters (compensation, governing law, termination, etc.)"
    )

    @field_validator("document_type")
    @classmethod
    def validate_doc_type(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("document_type must not be empty.")
        if len(cleaned) > 200:
            raise ValueError("document_type is too long (maximum 200 characters).")
        return cleaned

    @field_validator("effective_date")
    @classmethod
    def validate_effective_date(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("effective_date must not be empty.")
        return cleaned

    @field_validator("terms")
    @classmethod
    def validate_terms(cls, v: Union[List[str], str]):
        if isinstance(v, str) and not v.strip():
            raise ValueError("terms must not be empty.")
        if isinstance(v, list) and len(v) == 0:
            raise ValueError("terms list must contain at least one term.")
        return v


class DocumentResponse(BaseModel):
    """Structured response payload for document generation."""
    success: bool
    document_type: str
    content: str
    message: str


class FormatRequest(BaseModel):
    """Payload for converting edited document content into DOCX, PDF, or HTML."""
    content: str = Field(..., description="The markdown/text content of the document")
    document_type: str = Field(default="Legal Document", description="Document type title")
    company_name: Optional[str] = Field(default="LegalEase AI Legal Systems", description="Company or firm name")


@router.post("/generate", response_model=DocumentResponse)
def generate_legal_document(req: DocumentRequest):
    """
    Primary endpoint for generating AI-powered legal documents.
    Validates input, invokes Gemini generator, sanitizes response, and returns structured JSON.
    """
    try:
        generator = GeminiDocumentGenerator()
        result = generator.generate_document(
            document_type=req.document_type,
            parties=req.parties,
            terms=req.terms,
            effective_date=req.effective_date,
            additional_information=req.additional_information,
        )

        sanitized_content = sanitize_text(result.get("content", ""))
        if not sanitized_content:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Generated document was empty.",
            )

        return DocumentResponse(
            success=True,
            document_type=req.document_type,
            content=sanitized_content,
            message="Document generated successfully",
        )

    except ValueError as ve:
        logger.warning(f"Validation error in /generate: {ve}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve),
        )
    except Exception as e:
        logger.error(f"Error during document generation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate legal document: {str(e)}",
        )


@router.post("/preview/html")
def preview_html_document(req: FormatRequest):
    """Converts document text into sanitized, styled HTML for preview."""
    try:
        html_out = format_html_preview(req.content, company_name=req.company_name)
        return {"success": True, "html": html_out}
    except Exception as e:
        logger.error(f"Error formatting HTML preview: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/export/docx")
def export_docx_document(req: FormatRequest):
    """Exports document text to DOCX binary stream."""
    try:
        docx_bytes = format_docx(
            text=req.content,
            doc_type=req.document_type,
            company_name=req.company_name,
        )
        return Response(
            content=docx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename=LegalEase_{req.document_type.replace(' ', '_')}.docx"}
        )
    except Exception as e:
        logger.error(f"Error exporting DOCX: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/export/pdf")
def export_pdf_document(req: FormatRequest):
    """Exports document text to PDF binary stream."""
    try:
        pdf_bytes = format_pdf(
            text=req.content,
            doc_type=req.document_type,
            company_name=req.company_name,
        )
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=LegalEase_{req.document_type.replace(' ', '_')}.pdf"}
        )
    except Exception as e:
        logger.error(f"Error exporting PDF: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
