"""LegalEase Streamlit Frontend Application.

AI-Powered Legal Document Generator with rich editing, preview, and multi-format exports.
"""
import os
import io
import datetime
import requests
import streamlit as st
from PIL import Image

# Import formatting and generator utilities for direct fallback and client-side processing
from utils.text_utils import sanitize_text, parse_terms_list, extract_terms_table
from utils.document_formatter import format_html_preview, format_docx
from utils.pdf_generator import format_pdf
from ai_core.gemini_generator import GeminiDocumentGenerator

# Page Configuration
st.set_page_config(
    page_title="LegalEase – AI Legal Document Generator",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling for modern Legal-Tech appearance
st.markdown(
    """
    <style>
        /* General page styling */
        .main {
            background-color: #f8fafc;
        }
        /* Top Hero Banner */
        .hero-banner {
            background: linear-gradient(135deg, #1a365d 0%, #2b6cb0 100%);
            color: white;
            padding: 24px 32px;
            border-radius: 10px;
            margin-bottom: 24px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.06);
        }
        .hero-title {
            font-size: 2.1rem;
            font-weight: 800;
            margin-bottom: 6px;
            letter-spacing: -0.5px;
        }
        .hero-subtitle {
            font-size: 1.05rem;
            opacity: 0.92;
            font-weight: 300;
        }
        /* Legal Disclaimer Card */
        .disclaimer-card {
            background-color: #fffaf0;
            border-left: 4px solid #dd6b20;
            padding: 12px 18px;
            border-radius: 4px;
            margin-bottom: 20px;
            font-size: 0.88rem;
            color: #7b341e;
            line-height: 1.5;
        }
        /* Card Containers */
        .stTabs [data-baseweb="tab-list"] {
            gap: 12px;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 6px;
            padding: 8px 18px;
            font-weight: 600;
        }
        /* Button highlights */
        .stButton>button {
            border-radius: 6px;
            font-weight: 600;
            transition: all 0.2s ease-in-out;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize Session State
if "generated_doc" not in st.session_state:
    st.session_state["generated_doc"] = None
if "edited_doc" not in st.session_state:
    st.session_state["edited_doc"] = None
if "doc_type" not in st.session_state:
    st.session_state["doc_type"] = "Non-Disclosure Agreement (NDA)"
if "uploaded_logo_bytes" not in st.session_state:
    st.session_state["uploaded_logo_bytes"] = None
if "temp_logo_path" not in st.session_state:
    st.session_state["temp_logo_path"] = None

# Backend API Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


def check_backend_health() -> bool:
    """Checks if FastAPI backend is currently online."""
    try:
        resp = requests.get(f"{BACKEND_URL}/", timeout=1.5)
        return resp.status_code == 200
    except Exception:
        return False


# ==========================================
# SIDEBAR: SETTINGS & QUICK PRESETS
# ==========================================
with st.sidebar:
    st.image(
        os.path.join(os.path.dirname(__file__), "assets", "logo", "legalease_logo.png")
        if os.path.exists(os.path.join(os.path.dirname(__file__), "assets", "logo", "legalease_logo.png"))
        else "⚖️",
        use_container_width=True,
    )
    st.markdown("### ⚙️ System & Branding")

    # Backend Status Badge
    is_backend_online = check_backend_health()
    if is_backend_online:
        st.success(f"🟢 Backend Online (`{BACKEND_URL}`)")
    else:
        st.warning("🟠 Backend Unreachable (Using Integrated Drafting Mode)")

    st.markdown("---")
    st.markdown("#### 🏢 Branding Options")
    company_name = st.text_input("Firm / Company Name", value="Global Tech Solutions Inc.")
    preferred_font = st.selectbox(
        "Document Font (DOCX)",
        ["Times New Roman", "Arial", "Georgia", "Calibri"],
        index=0,
    )

    logo_file = st.file_uploader("Upload Company Logo (PNG / JPG)", type=["png", "jpg", "jpeg"])
    if logo_file:
        st.session_state["uploaded_logo_bytes"] = logo_file.getvalue()
        # Save temp logo for generator utilities
        temp_logo = os.path.join(os.path.dirname(__file__), "assets", "logo", "user_logo_temp.png")
        with open(temp_logo, "wb") as f:
            f.write(logo_file.getvalue())
        st.session_state["temp_logo_path"] = temp_logo
        st.image(logo_file, caption="Uploaded Logo", width=140)
    else:
        # Default logo fallback
        default_logo = os.path.join(os.path.dirname(__file__), "assets", "logo", "legalease_logo.png")
        st.session_state["temp_logo_path"] = default_logo if os.path.exists(default_logo) else None

    st.markdown("---")
    st.markdown("#### ⚡ Quick Templates")
    st.caption("Click to pre-fill test scenarios:")

    sample_preset = st.radio(
        "Load Preset Scenario:",
        [
            "Custom Draft",
            "Mutual NDA",
            "Employment Contract",
            "Freelance Service Contract",
            "Commercial Lease Agreement",
        ],
        index=0,
    )


# ==========================================
# HEADER SECTION
# ==========================================
st.markdown(
    """
    <div class="hero-banner">
        <div class="hero-title">LegalEase</div>
        <div class="hero-subtitle">Production-Ready AI Legal Document Drafting & Assembly System</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Mandatory Visible Legal Disclaimer
st.markdown(
    """
    <div class="disclaimer-card">
        <strong>LEGAL SAFETY NOTICE & DISCLAIMER:</strong><br/>
        LegalEase generates documents using artificial intelligence for informational and drafting assistance only.
        AI-generated documents may contain errors or may not be appropriate for your specific circumstances.
        Review the document carefully and consult a qualified legal professional when appropriate.
        Do not execute documents without independent legal verification.
    </div>
    """,
    unsafe_allow_html=True,
)


# ==========================================
# PRESET DATA POPULATION
# ==========================================
preset_data = {
    "Mutual NDA": {
        "doc_type": "NDA",
        "p1_name": "Apex Innovations LLC",
        "p1_role": "Disclosing / Receiving Party",
        "p1_org": "Apex Innovations LLC",
        "p1_addr": "100 Tech Blvd, Suite 400, Austin, TX 78701",
        "p2_name": "Quantum Data Labs Inc.",
        "p2_role": "Disclosing / Receiving Party",
        "p2_org": "Quantum Data Labs Inc.",
        "p2_addr": "500 Market St, Floor 8, San Francisco, CA 94105",
        "terms": "Mutual non-disclosure of proprietary algorithms, customer lists, and financial projections;\nStrict standard of care required;\nConfidentiality obligations survive for 3 years from disclosure;\nTrade secrets protected indefinitely;\nReturn or destruction of all materials upon 10 days notice",
        "jurisdiction": "State of Delaware",
        "compensation": "Mutual business evaluation (no fee consideration)",
        "termination": "Agreement may be terminated by either party upon 30 days written notice",
    },
    "Employment Contract": {
        "doc_type": "Employment Contract",
        "p1_name": "Apex Innovations LLC",
        "p1_role": "Employer",
        "p1_org": "Apex Innovations LLC",
        "p1_addr": "100 Tech Blvd, Suite 400, Austin, TX 78701",
        "p2_name": "Alexander Morgan",
        "p2_role": "Senior Cloud Architect",
        "p2_org": "Individual",
        "p2_addr": "742 Evergreen Terrace, Austin, TX 78704",
        "terms": "Full-time position with 40 hours per week;\nAnnual base salary of $165,000 paid semi-monthly;\nParticipation in company comprehensive healthcare and 401(k) matching;\nAll code and patentable inventions belong exclusively to employer;\nAt-will employment with 2 weeks notice of resignation",
        "jurisdiction": "State of Texas",
        "compensation": "$165,000 USD per annum plus discretionary annual performance bonus",
        "termination": "At-will employment; either party may terminate with two (2) weeks written notice",
    },
    "Freelance Service Contract": {
        "doc_type": "Freelance Work Contract",
        "p1_name": "Nexus Media Group",
        "p1_role": "Client",
        "p1_org": "Nexus Media Group Corp",
        "p1_addr": "250 Broadway, New York, NY 10007",
        "p2_name": "Elena Rostova",
        "p2_role": "Lead UI/UX Designer & Consultant",
        "p2_org": "Rostova Creative Studio",
        "p2_addr": "12 Elm Street, Brooklyn, NY 11201",
        "terms": "Delivery of complete brand guidelines, design system, and responsive web mockups;\nDelivery deadline within 45 calendar days;\nPayment net 30 upon invoice approval;\nContractor retains moral rights but assigns all copyright upon full payment;\nImmediate termination for material breach not cured within 7 days",
        "jurisdiction": "State of New York",
        "compensation": "$12,500 total project fee (50% upfront deposit, 50% upon milestone completion)",
        "termination": "Either party may terminate upon 14 days written notice; accrued fees payable immediately",
    },
    "Commercial Lease Agreement": {
        "doc_type": "Lease Agreement",
        "p1_name": "Sterling Real Estate Holdings LLC",
        "p1_role": "Landlord",
        "p1_org": "Sterling Real Estate Holdings LLC",
        "p1_addr": "800 Fifth Avenue, New York, NY 10021",
        "p2_name": "Bright Horizon Tech Co.",
        "p2_role": "Tenant",
        "p2_org": "Bright Horizon Tech Co.",
        "p2_addr": "45 Wall Street, Suite 1200, New York, NY 10005",
        "terms": "Lease of Suite 1200 comprising 4,500 square feet of commercial office space;\nMonthly base rent of $18,000 due on 1st of each month;\nSecurity deposit of $36,000 held in escrow;\nTenant responsible for interior janitorial and minor utilities;\nLandlord responsible for HVAC, roof, and structural maintenance",
        "jurisdiction": "State of New York",
        "compensation": "$18,000 per month base rent plus pro-rata share of operating expenses",
        "termination": "3-year lease term; notice of non-renewal required 180 days prior to expiration",
    },
}

cur_preset = preset_data.get(sample_preset, {})


# ==========================================
# INPUT FORM
# ==========================================
st.markdown("### 📋 1. Document Parameters & Specifications")

col_left, col_right = st.columns(2)

with col_left:
    doc_types = [
        "NDA",
        "Employment Contract",
        "Employment Offer Letter",
        "Lease Agreement",
        "Freelance Work Contract",
        "Service Agreement",
        "Agreement",
        "Contract",
        "Other",
    ]
    preset_doc_type = cur_preset.get("doc_type", "NDA")
    doc_index = doc_types.index(preset_doc_type) if preset_doc_type in doc_types else 0

    selected_doc_type = st.selectbox("Document Type *", doc_types, index=doc_index)
    if selected_doc_type == "Other":
        custom_doc_type = st.text_input("Specify Document Title *", value="Consulting Agreement")
        effective_doc_type = custom_doc_type
    else:
        effective_doc_type = selected_doc_type

    effective_date = st.date_input("Effective Date *", datetime.date.today())

with col_right:
    st.markdown("##### 👥 Parties Involved *")
    st.caption("Identify both parties clearly. All entered details will be preserved.")

# Party Details Inputs
p_col1, p_col2 = st.columns(2)

with p_col1:
    st.markdown("###### First Party (Disclosing Party / Employer / Landlord / Client)")
    p1_name = st.text_input("Name / Entity *", value=cur_preset.get("p1_name", "Acme Corporation"))
    p1_role = st.text_input("Role *", value=cur_preset.get("p1_role", "Disclosing Party"))
    p1_org = st.text_input("Organization", value=cur_preset.get("p1_org", "Acme Corp LLC"))
    p1_addr = st.text_area("Address / Contact *", value=cur_preset.get("p1_addr", "100 Innovation Way, Suite 100, Austin, TX 78701"), height=68)

with p_col2:
    st.markdown("###### Second Party (Receiving Party / Employee / Tenant / Contractor)")
    p2_name = st.text_input("Name / Entity *", value=cur_preset.get("p2_name", "Jane Doe"))
    p2_role = st.text_input("Role *", value=cur_preset.get("p2_role", "Receiving Party"))
    p2_org = st.text_input("Organization / Affiliation", value=cur_preset.get("p2_org", "Doe Consulting"))
    p2_addr = st.text_area("Address / Contact *", value=cur_preset.get("p2_addr", "452 Maple Street, Austin, TX 78704"), height=68)

# Terms & Conditions Section
st.markdown("---")
st.markdown("##### 📜 Terms & Conditions *")
st.caption("Enter key terms separated by semicolons (`;`) or newlines. The generator converts these into structured legal clauses and a summary table.")

default_terms = cur_preset.get(
    "terms",
    "Confidential Information shall not be disclosed to any third party;\nRecipient shall exercise standard of reasonable care;\nAgreement shall remain in effect for two (2) years;\nEither party may terminate upon thirty (30) days written notice"
)
raw_terms_input = st.text_area(
    "Contractual Terms & Obligations *",
    value=default_terms,
    height=120,
    placeholder="e.g. Payment within 30 days of invoice; Provider delivers work by agreed deadline; Confidentiality must be maintained for 2 years; Either party may terminate with 15 days notice",
)

# Live Terms Parser & Table Preview
parsed_terms_list = parse_terms_list(raw_terms_input)
if parsed_terms_list:
    with st.expander(f"🔍 Live Terms Breakdown ({len(parsed_terms_list)} clauses detected)", expanded=False):
        terms_table_data = [{"Clause No.": f"Clause {idx}", "Structured Term": t} for idx, t in enumerate(parsed_terms_list, 1)]
        st.table(terms_table_data)

# Additional Information Section
with st.expander("➕ Additional Information & Document Specifications (Optional)", expanded=False):
    add_col1, add_col2 = st.columns(2)
    with add_col1:
        comp_input = st.text_input(
            "Compensation / Payment Terms",
            value=cur_preset.get("compensation", "As stated in mutual commercial agreement"),
            help="Specify fee, salary, rent, or payment milestones.",
        )
        term_input = st.text_input(
            "Termination Conditions",
            value=cur_preset.get("termination", "Either party may terminate upon thirty (30) days written notice"),
        )
    with add_col2:
        law_input = st.text_input(
            "Governing Law / Jurisdiction",
            value=cur_preset.get("jurisdiction", "State of Delaware"),
            help="If left blank, the AI will explicitly flag '[CONFIRM: Governing Jurisdiction]'.",
        )
        conf_input = st.text_input(
            "Confidentiality Specifics",
            value="All proprietary and technical materials must remain strictly confidential.",
        )


# ==========================================
# GENERATE DOCUMENT ACTION
# ==========================================
st.markdown("<br/>", unsafe_allow_html=True)
generate_btn = st.button("⚡ Generate Legal Document", type="primary", use_container_width=True)

if generate_btn:
    # 1. Validation
    if not effective_doc_type.strip():
        st.error("Please specify a document type.")
    elif not p1_name.strip() or not p2_name.strip():
        st.error("Please specify names for both parties.")
    elif not raw_terms_input.strip():
        st.error("Please enter at least one term or condition.")
    else:
        with st.spinner("🤖 Assembling formal legal document with AI drafting engine..."):
            parties_payload = {
                "party_1": {
                    "name": p1_name.strip(),
                    "role": p1_role.strip(),
                    "organization": p1_org.strip(),
                    "address": p1_addr.strip(),
                },
                "party_2": {
                    "name": p2_name.strip(),
                    "role": p2_role.strip(),
                    "organization": p2_org.strip(),
                    "address": p2_addr.strip(),
                },
            }

            additional_payload = {
                "compensation": comp_input.strip() if comp_input else None,
                "termination": term_input.strip() if term_input else None,
                "governing_law": law_input.strip() if law_input else None,
                "confidentiality": conf_input.strip() if conf_input else None,
            }

            request_body = {
                "document_type": effective_doc_type,
                "parties": parties_payload,
                "terms": parsed_terms_list,
                "effective_date": str(effective_date),
                "additional_information": additional_payload,
            }

            doc_content = None
            # Attempt FastAPI backend communication first
            if is_backend_online:
                try:
                    resp = requests.post(
                        f"{BACKEND_URL}/generate",
                        json=request_body,
                        timeout=45,
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        doc_content = data.get("content")
                    else:
                        st.warning(f"Backend responded with status {resp.status_code}. Using direct generator.")
                except Exception as ex:
                    st.warning(f"Backend call error: {ex}. Proceeding with direct generator.")

            # Fallback to direct client-side generator if backend call was unsuccessful
            if not doc_content:
                direct_gen = GeminiDocumentGenerator()
                res = direct_gen.generate_document(
                    document_type=effective_doc_type,
                    parties=parties_payload,
                    terms=parsed_terms_list,
                    effective_date=str(effective_date),
                    additional_information=additional_payload,
                )
                doc_content = res.get("content")

            if doc_content:
                cleaned_doc = sanitize_text(doc_content)
                st.session_state["generated_doc"] = cleaned_doc
                st.session_state["edited_doc"] = cleaned_doc
                st.session_state["doc_type"] = effective_doc_type
                st.success("✅ Document generated successfully! Review, edit, and download below.")
            else:
                st.error("Failed to generate document. Please check your inputs and try again.")


# ==========================================
# DOCUMENT REVIEW, EDIT, & EXPORT TABS
# ==========================================
if st.session_state.get("edited_doc"):
    st.markdown("---")
    st.markdown("### 📄 2. Document Review, Editing & Download")

    tab_preview, tab_edit = st.tabs(["👁️ Preview Document", "✏️ Edit Document"])

    # --- TAB 1: HTML PREVIEW ---
    with tab_preview:
        html_markup = format_html_preview(
            st.session_state["edited_doc"],
            company_name=company_name,
            logo_path=st.session_state.get("temp_logo_path"),
        )
        st.components.v1.html(html_markup, height=750, scrolling=True)

    # --- TAB 2: EDIT DOCUMENT ---
    with tab_edit:
        st.caption("You have full control to modify any clause, add customized terms, or adjust language prior to downloading.")
        new_text = st.text_area(
            "Document Markdown Editor",
            value=st.session_state["edited_doc"],
            height=600,
            key="markdown_editor",
        )

        col_save, col_reset = st.columns([1, 4])
        with col_save:
            if st.button("💾 Apply & Save Edits", type="primary"):
                st.session_state["edited_doc"] = sanitize_text(new_text)
                st.success("Edits saved! The preview and download files have been updated.")
                st.rerun()

        with col_reset:
            if st.button("🔄 Reset to Original AI Draft"):
                st.session_state["edited_doc"] = st.session_state["generated_doc"]
                st.info("Reset to original draft.")
                st.rerun()

    # ==========================================
    # DOWNLOAD ACTION BUTTONS
    # ==========================================
    st.markdown("#### 📥 3. Download Formal Document")
    st.caption("All downloads automatically include your latest edits.")

    doc_to_export = st.session_state["edited_doc"]
    active_doc_type = st.session_state.get("doc_type", "Legal_Document")
    clean_filename = f"LegalEase_{active_doc_type.replace(' ', '_').replace('/', '_')}"

    # Generate binary outputs from the latest edited text
    docx_data = format_docx(
        text=doc_to_export,
        doc_type=active_doc_type,
        company_name=company_name,
        logo_path=st.session_state.get("temp_logo_path"),
        font_name=preferred_font,
    )

    pdf_data = format_pdf(
        text=doc_to_export,
        doc_type=active_doc_type,
        company_name=company_name,
        logo_path=st.session_state.get("temp_logo_path"),
    )

    txt_data = doc_to_export.encode("utf-8")

    d_col1, d_col2, d_col3 = st.columns(3)

    with d_col1:
        st.download_button(
            label="📄 Download as TXT",
            data=txt_data,
            file_name=f"{clean_filename}.txt",
            mime="text/plain",
            use_container_width=True,
        )

    with d_col2:
        st.download_button(
            label="📝 Download as DOCX",
            data=docx_data,
            file_name=f"{clean_filename}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        )

    with d_col3:
        st.download_button(
            label="📑 Download as PDF",
            data=pdf_data,
            file_name=f"{clean_filename}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
