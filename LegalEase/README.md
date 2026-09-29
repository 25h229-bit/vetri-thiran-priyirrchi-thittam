# LegalEase – AI-Powered Legal Document Generator

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-red.svg)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**LegalEase** is a production-grade, AI-powered legal document generation, editing, and assembly platform. It transforms structured user inputs into customizable, legally rigorous, professional legal documents such as Non-Disclosure Agreements (NDAs), Employment Contracts, Commercial Lease Agreements, Freelance Work Contracts, and Service Agreements.

The system combines **Google Gemini generative intelligence** with a structured drafting engine, real-time sanitization, an interactive editable preview, and multi-format document compilation (**TXT, DOCX, and PDF** with headers, footers, custom branding, and formatted terms tables).

---

## 📑 Table of Contents

- [Key Features](#-key-features)
- [Architecture & Data Flow](#-architecture--data-flow)
- [Technology Stack](#-technology-stack)
- [Project Directory Structure](#-project-directory-structure)
- [Prerequisites & Installation](#-prerequisites--installation)
- [Environment Configuration](#-environment-configuration)
- [Running the Application](#-running-the-application)
- [API Documentation](#-api-documentation)
- [Document Generation Workflow](#-document-generation-workflow)
- [Supported Document Types](#-supported-document-types)
- [Export Formats & Styling](#-export-formats--styling)
- [Automated Testing](#-automated-testing)
- [Deployment Guide](#-deployment-guide)
- [Security & Privacy](#-security--privacy)
- [Legal Disclaimer & Safety](#-legal-disclaimer--safety)

---

## 🌟 Key Features

1. **AI-Powered Legal Drafting:**
   - Deep structured prompting utilizing Google Gemini (`gemini-1.5-pro`, `gemini-2.5-flash`, `gemini-1.5-flash`).
   - Adapts contract structure, covenants, recitals, and warranties specifically to the document type.
   - Preserves user-supplied facts (names, roles, addresses, compensation) with zero fabrication.
   - Explicitly flags missing jurisdictional details (`[CONFIRM: Governing Jurisdiction]`) rather than guessing.

2. **Streamlit Executive Interface:**
   - Polished, responsive legal-tech user interface.
   - One-click presets for common legal scenarios (Mutual NDA, Senior Cloud Engineer Employment, Commercial Office Lease, Freelance UI/UX Contract).
   - Dynamic clause parser that translates semicolon-separated and newline-separated terms into a structured table.

3. **Editable Document Lifecycle:**
   - **Generate → Preview → Edit → Save Changes → Download**.
   - Full live markdown editor enabling users to fine-tune clauses before downloading.
   - Reset button to restore the original AI draft at any time.

4. **Multi-Format Export Engine:**
   - **Plain Text (TXT):** Clean, unencumbered text export.
   - **Microsoft Word (DOCX):** Formatted with Times New Roman (or configurable fonts), 1-inch margins, custom logo in header, page footers, styled terms table, and two-column signature blocks.
   - **Adobe PDF (PDF):** Generated via `fpdf2` with running headers, footers with page numbers ("Page X of Y"), confidentiality markers, styled terms table, and Latin-1 character normalization preventing crashes.

5. **Built-in Brand Customization:**
   - Upload custom company logos (PNG / JPG).
   - Custom organization name embedded into headers and footers.
   - Configurable typography (Times New Roman, Arial, Georgia, Calibri).

6. **Zero-Drop Fallback Drafting Engine:**
   - Seamless offline operation: if an API key is not configured or network calls fail, LegalEase utilizes an internal structured contract generation engine ensuring 100% testability and reliability.

---

## 🏛 Architecture & Data Flow

```text
User Input (Browser)
       ↓
Streamlit Frontend (app.py)
       ↓  (HTTP POST /generate)
FastAPI Backend (main.py / routes.py)
       ↓  (Pydantic Schema Validation)
AI Core Engine (ai_core/gemini_generator.py)
       ↓  (Gemini API with Structured Prompt / Fallback)
Sanitization Pipeline (utils/text_utils.py)
       ↓
Editable Document Session (Streamlit UI)
       ↓  (User Modifies Clauses & Approves)
Formatting Engines:
   ├── HTML Preview  (utils/document_formatter.py)
   ├── Word DOCX     (python-docx)
   ├── Adobe PDF     (fpdf2)
   └── Clean TXT     (Plain UTF-8)
       ↓
User Download
```

---

## 💻 Technology Stack

| Component | Technology | Description |
|---|---|---|
| **Frontend** | Streamlit | Responsive, stateful interactive UI |
| **Backend** | FastAPI | High-performance asynchronous REST API |
| **Server** | Uvicorn | ASGI server implementation |
| **AI Integration** | `google-genai` & `google-generativeai` | Google Gemini API integration |
| **Validation** | Pydantic v2 | Strict schema validation and sanitization |
| **DOCX Generation** | `python-docx` | Native Word document compilation with styling |
| **PDF Generation** | `fpdf2` | Multi-page PDF generation with running headers/footers |
| **Image Processing** | Pillow (PIL) | Logo processing, validation, and rendering |
| **Testing** | Pytest & TestClient | 23 comprehensive unit and integration tests |

---

## 📁 Project Directory Structure

```text
LegalEase/
│
├── main.py                     # FastAPI application entrypoint & health routes
├── routes.py                   # Pydantic models & API endpoints (/generate, /export)
├── app.py                      # Streamlit interactive frontend application
├── requirements.txt            # Dependency manifest with version pinning
├── .env.example                # Environment variable template
├── .env                        # Local environment configuration
├── Dockerfile                  # Production container definition
├── docker-compose.yml          # Multi-service deployment configuration
├── .gitignore                  # Git ignore rules
├── README.md                   # Comprehensive documentation
│
├── ai_core/
│   ├── __init__.py
│   └── gemini_generator.py     # Gemini client, structured prompt & drafting engine
│
├── utils/
│   ├── __init__.py
│   ├── text_utils.py           # Text sanitization, XSS protection, clause parsing
│   ├── document_formatter.py   # HTML preview rendering & python-docx formatting
│   └── pdf_generator.py        # fpdf2 PDF compilation with headers and footers
│
├── assets/
│   └── logo/
│       └── legalease_logo.png  # Default application brand logo
│
├── tests/
│   ├── __init__.py
│   ├── test_backend.py         # FastAPI route & validation tests
│   ├── test_generator.py       # AI generation & contract adaptation tests
│   └── test_formatting.py      # Sanitization, DOCX, and PDF compilation tests
│
└── generated_documents/        # Directory for temporary file exports
    └── .gitkeep
```

---

## 🚀 Prerequisites & Installation

### Prerequisites
- Python 3.10, 3.11, 3.12, 3.13, or 3.14
- pip package manager

### 1. Clone or Navigate to LegalEase
```bash
cd LegalEase
```

### 2. Create and Activate Virtual Environment (Recommended)
```bash
# On Linux / macOS
python3 -m venv venv
source venv/bin/activate

# On Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## ⚙️ Environment Configuration

1. Copy the sample environment file:
   ```bash
   cp .env.example .env
   ```

2. Open `.env` and set your configuration:
   ```env
   # Google Gemini API Key (from https://aistudio.google.com/)
   GEMINI_API_KEY=your_gemini_api_key_here

   # Gemini Model (e.g., gemini-1.5-pro, gemini-2.5-flash, gemini-1.5-flash)
   GEMINI_MODEL=gemini-1.5-pro

   # Backend URL (used by Streamlit frontend)
   BACKEND_URL=http://localhost:8000
   ```

> **Note:** If `GEMINI_API_KEY` is not provided, LegalEase automatically switches to its deterministic fallback legal drafting engine, enabling complete offline testing and demonstration without failure.

---

## 🏃 Running the Application

### Option A: Local Development (Two Terminals)

**Terminal 1 — FastAPI Backend:**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
*API will be available at:* `http://localhost:8000`  
*Swagger Documentation:* `http://localhost:8000/docs`

**Terminal 2 — Streamlit Frontend:**
```bash
streamlit run app.py
```
*Frontend UI will open automatically at:* `http://localhost:8501`

---

### Option B: Docker Compose

Start both frontend and backend concurrently with a single command:
```bash
docker-compose up --build
```
- Access Frontend: `http://localhost:8501`
- Access Backend API: `http://localhost:8000`

---

## 📡 API Documentation

### 1. Root Health Check
- **Endpoint:** `GET /`
- **Description:** Verifies service availability and registered endpoints.
- **Response:**
  ```json
  {
    "status": "online",
    "app": "LegalEase – AI-Powered Legal Document Generator",
    "version": "1.0.0",
    "message": "LegalEase backend API is running smoothly."
  }
  ```

### 2. Generate Legal Document
- **Endpoint:** `POST /generate`
- **Headers:** `Content-Type: application/json`
- **Request Body:**
  ```json
  {
    "document_type": "NDA",
    "parties": {
      "party_1": {
        "name": "Apex Innovations LLC",
        "role": "Disclosing Party",
        "address": "100 Tech Blvd, Austin, TX"
      },
      "party_2": {
        "name": "Quantum Data Labs Inc.",
        "role": "Receiving Party",
        "address": "500 Market St, San Francisco, CA"
      }
    },
    "terms": [
      "Mutual non-disclosure of proprietary algorithms",
      "Strict standard of reasonable care required",
      "Confidentiality survives for 3 years",
      "Either party may terminate upon 30 days notice"
    ],
    "effective_date": "2026-10-01",
    "additional_information": {
      "governing_law": "State of Delaware",
      "confidentiality": "Strict standard of care applies"
    }
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "success": true,
    "document_type": "NDA",
    "content": "# NON-DISCLOSURE AGREEMENT\n\n**Effective Date:** 2026-10-01\n\n### PARTIES...",
    "message": "Document generated successfully"
  }
  ```

### 3. Binary Exports
- `POST /export/docx`: Converts document text into a styled Microsoft Word binary stream.
- `POST /export/pdf`: Converts document text into a paginated PDF binary stream.
- `POST /preview/html`: Returns sanitized, styled HTML for document rendering.

---

## 🔄 Document Generation Workflow

```text
1. Select Document Type (NDA, Employment, Lease, Freelance, etc.)
2. Input Parties (Name, Role, Entity, Address)
3. Input Terms & Conditions (Semicolon-separated or bulleted)
4. Select Effective Date
5. Add Optional Details (Compensation, Jurisdiction, Termination)
6. Upload Optional Logo & Specify Branding
7. Click "⚡ Generate Legal Document"
8. Review in Executive HTML Preview
9. Click "✏️ Edit Document" to refine any clause
10. Click "💾 Apply & Save Edits"
11. Download as TXT, DOCX, or PDF (Includes latest edits)
```

---

## 🛡 Security and Privacy

- **No Hard-Coded Secrets:** All API keys are loaded strictly from environment variables (`.env`).
- **Client Key Isolation:** Streamlit frontend never exposes the Gemini API key to the browser.
- **XSS & Injection Protection:** `sanitize_text()` filters out `<script>`, `<iframe>`, javascript URLs, and active event handlers from both user input and AI output.
- **No Document Storage Without Permission:** Generated documents are processed in memory and streamed directly to the user as byte buffers, minimizing server-side data retention.
- **Temporary File Cleanup:** Any uploaded branding images stored temporarily are segregated and safe for containerized ephemeral lifecycles.

---

## 🧪 Automated Testing

LegalEase includes an automated test suite with **23 unit and integration tests** covering backend endpoints, schema validation, Gemini generation, fact preservation, HTML rendering, DOCX binary creation, and multi-page PDF formatting.

Run the test suite with:
```bash
python -m pytest tests -v
```

**Test Breakdown:**
- `tests/test_backend.py`: Health checks, `/generate` endpoint, Pydantic validation (empty fields, missing dates, missing terms), DOCX & PDF export endpoints.
- `tests/test_generator.py`: Prompt construction, NDA generation, Employment contracts, Lease agreements, Freelance contracts, fact preservation, missing jurisdiction flagging (`[CONFIRM: Governing Jurisdiction]`).
- `tests/test_formatting.py`: XSS sanitization, typographic quote normalization, terms table extraction, HTML preview markup, Word DOCX generation, and PDF generation with multi-page handling.

---

## 🚢 Deployment Guide

### Streamlit Community Cloud (Frontend)
1. Fork or push this repository to GitHub.
2. Link your repository on [share.streamlit.io](https://share.streamlit.io).
3. Set Main file path to `app.py`.
4. In Advanced Settings, add `BACKEND_URL` pointing to your hosted FastAPI backend URL.

### Render / Railway / Fly.io (FastAPI Backend)
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Environment Variables:** Set `GEMINI_API_KEY` and `GEMINI_MODEL`.

### Docker Deployment
```bash
# Build the image
docker build -t legalease-app .

# Run the container
docker run -p 8000:8000 -p 8501:8501 -e GEMINI_API_KEY=your_key legalease-app
```

---

## ⚠️ Legal Disclaimer & Safety

> **IMPORTANT NOTICE:**  
> **LegalEase generates documents using artificial intelligence for informational and drafting assistance only. AI-generated documents may contain errors, omissions, or clauses not suitable for your specific legal or commercial circumstances. Laws vary significantly across jurisdictions.**  
> **LegalEase does not provide legal advice, nor does the use of this software establish an attorney-client relationship. Always review documents carefully and consult a qualified, licensed legal professional in your jurisdiction before executing any agreement.**
