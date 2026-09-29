"""FastAPI backend application entrypoint for LegalEase."""
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from routes import router as api_router

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("LegalEase.Main")

# Initialize FastAPI application
app = FastAPI(
    title="LegalEase – AI-Powered Legal Document Generator API",
    description="High-precision legal contract and agreement drafting powered by Google Gemini and FastAPI.",
    version="1.0.0",
)

# Enable CORS for Streamlit frontend and external integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(api_router)


@app.get("/")
def root_health_check():
    """Health / status response confirming LegalEase is running."""
    return {
        "status": "online",
        "app": "LegalEase – AI-Powered Legal Document Generator",
        "version": "1.0.0",
        "message": "LegalEase backend API is running smoothly.",
        "endpoints": {
            "health": "/",
            "generate": "/generate",
            "preview_html": "/preview/html",
            "export_docx": "/export/docx",
            "export_pdf": "/export/pdf",
            "docs": "/docs",
        },
    }


@app.get("/health")
def detailed_health_check():
    """Detailed health check for container orchestration and uptime monitors."""
    import os
    has_gemini_key = bool(os.getenv("GEMINI_API_KEY") and os.getenv("GEMINI_API_KEY") not in ("your_api_key_here", "dummy_key"))
    return {
        "status": "healthy",
        "gemini_api_configured": has_gemini_key,
        "model": os.getenv("GEMINI_MODEL", "gemini-1.5-pro"),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
