"""Gemini AI Document Generator module for LegalEase."""
import os
import re
import json
import logging
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger("LegalEase.GeminiGenerator")


class GeminiDocumentGenerator:
    """
    AI-powered legal document drafting engine using Google Gemini API.
    Supports google-genai, google-generativeai, and intelligent fallback drafting.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        # Default model: gemini-1.5-pro or gemini-2.5-flash / gemini-1.5-flash
        self.model_name = model_name or os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
        self._genai_client = None
        self._legacy_genai = None

        self._init_client()

    def _init_client(self):
        """Initializes the Gemini client using modern google-genai or legacy google-generativeai."""
        if not self.api_key or self.api_key.strip() in ("", "your_api_key_here", "dummy_key"):
            logger.info("No valid GEMINI_API_KEY found. Generator will operate in intelligent fallback mode.")
            return

        # Attempt modern google.genai first
        try:
            from google import genai
            self._genai_client = genai.Client(api_key=self.api_key)
            logger.info("Initialized modern google.genai client.")
            return
        except Exception as e:
            logger.warning(f"Could not initialize modern google.genai: {e}. Trying google.generativeai.")

        # Attempt legacy google.generativeai
        try:
            import google.generativeai as legacy_genai
            legacy_genai.configure(api_key=self.api_key)
            self._legacy_genai = legacy_genai
            logger.info("Initialized google.generativeai client.")
        except Exception as e:
            logger.error(f"Failed to initialize any Gemini client: {e}")

    def generate_document(
        self,
        document_type: str,
        parties: Any,
        terms: Any,
        effective_date: str,
        additional_information: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Generates a formal legal document from structured inputs.
        """
        # Format parties into readable string
        parties_desc = self._format_parties_input(parties)
        terms_desc, terms_list = self._format_terms_input(terms)
        add_info_desc = self._format_additional_info(additional_information)

        prompt = self._build_prompt(
            doc_type=document_type,
            parties_desc=parties_desc,
            terms_desc=terms_desc,
            effective_date=effective_date,
            additional_info_desc=add_info_desc,
            terms_list=terms_list,
        )

        # Attempt Gemini Generation if client is available
        generated_content = None
        if self._genai_client or self._legacy_genai:
            try:
                generated_content = self._call_gemini_api(prompt)
            except Exception as e:
                logger.error(f"Gemini API call failed: {e}. Falling back to structured drafting engine.")
                generated_content = None

        # If live API call didn't yield output (no key, rate limit, offline), use high-fidelity template engine
        if not generated_content:
            generated_content = self._generate_fallback_document(
                document_type=document_type,
                parties_desc=parties_desc,
                parties_raw=parties,
                terms_list=terms_list,
                effective_date=effective_date,
                additional_info=additional_information,
            )

        return {
            "success": True,
            "document_type": document_type,
            "content": generated_content,
            "message": "Document generated successfully",
        }

    def _call_gemini_api(self, prompt: str) -> Optional[str]:
        """Invokes Gemini model using available client."""
        # Try modern google.genai client
        if self._genai_client:
            try:
                # Use specified model or fallback to 1.5-flash / 2.5-flash if pro fails
                models_to_try = [self.model_name, "gemini-1.5-pro", "gemini-2.5-flash", "gemini-1.5-flash"]
                for m in models_to_try:
                    try:
                        response = self._genai_client.models.generate_content(
                            model=m,
                            contents=prompt,
                        )
                        if response and response.text:
                            return response.text.strip()
                    except Exception as me:
                        logger.warning(f"Error invoking model {m}: {me}")
            except Exception as e:
                logger.error(f"Error in genai_client call: {e}")

        # Try legacy google.generativeai client
        if self._legacy_genai:
            try:
                models_to_try = [self.model_name, "gemini-1.5-pro", "gemini-1.5-flash"]
                for m in models_to_try:
                    try:
                        model = self._legacy_genai.GenerativeModel(m)
                        response = model.generate_content(prompt)
                        if response and response.text:
                            return response.text.strip()
                    except Exception as me:
                        logger.warning(f"Error in legacy model {m}: {me}")
            except Exception as e:
                logger.error(f"Error in legacy_genai call: {e}")

        return None

    def _build_prompt(
        self,
        doc_type: str,
        parties_desc: str,
        terms_desc: str,
        effective_date: str,
        additional_info_desc: str,
        terms_list: List[str],
    ) -> str:
        """Constructs an exhaustive legal drafting prompt for Gemini."""
        prompt = f"""You are LegalEase AI, an expert legal drafting assistant specialized in commercial contracts and legal documentation.
Your task is to generate a comprehensive, highly professional, production-ready legal document of type: "{doc_type}".

=== MANDATORY DRAFTING RULES ===
1. FORMAL STRUCTURE:
   - Begin with the formal DOCUMENT TITLE in bold capital letters (e.g., NON-DISCLOSURE AGREEMENT, COMMERCIAL LEASE AGREEMENT, EMPLOYMENT AGREEMENT).
   - Prominently state the Effective Date: "{effective_date}".
   - Identify all PARTIES with exact names, roles, entities, and addresses as provided.
   - Include formal BACKGROUND / RECITALS ("WHEREAS..." clauses explaining the context).
   - Divide the document into clear, logical, numbered sections (e.g., 1. PURPOSE, 2. DEFINITIONS, 3. SCOPE / RESPONSIBILITIES, 4. COMPENSATION / PAYMENT, 5. CONFIDENTIALITY, 6. INTELLECTUAL PROPERTY, 7. TERM AND TERMINATION, 8. REPRESENTATIONS AND WARRANTIES, 9. INDEMNIFICATION AND LIABILITY, 10. DISPUTE RESOLUTION, 11. GOVERNING LAW, 12. GENERAL PROVISIONS).
   - Include a dedicated markdown TERMS TABLE summarizing key clauses.
   - End with clean, professional SIGNATURE BLOCKS with lines for Signature, Printed Name, Title, and Date for all parties.

2. PRESERVATION OF USER FACTS:
   - You MUST preserve all party names, addresses, compensation, payment terms, and specific terms provided.
   - NEVER invent or fabricate user-specific facts, monetary amounts, specific jurisdictions, or company names.
   - If a specific legal jurisdiction or state was NOT provided by the user, explicitly write "[CONFIRM: Governing Jurisdiction / State]" rather than making one up.
   - If any critical detail is missing, clearly denote it in brackets (e.g., "[INSERT: Specific Notice Address if different]").

3. CONVERSION OF TERMS:
   - Convert all supplied terms and conditions into rigorous, legally binding clauses.
   - Add standard protective covenants customary for this document type (severability, entire agreement, amendments in writing, force majeure, notice).

4. TERMS TABLE:
   - Include a Markdown table titled "SUMMARY OF KEY TERMS" with columns:
     | No. | Clause / Term | Specific Terms & Obligations |

5. LEGAL SAFETY & DISCLAIMER:
   - Do NOT claim that this document constitutes formal legal advice.
   - Conclude with the following exact disclaimer block at the bottom:
     ---
     LEGAL DISCLAIMER: This document was generated using LegalEase AI for drafting and informational assistance only. Laws vary by jurisdiction. All parties should have this agreement reviewed by a qualified legal professional prior to signature and execution.

=== INPUT DATA ===
Document Type: {doc_type}
Effective Date: {effective_date}
Parties Involved:
{parties_desc}

Terms & Conditions (Raw user clauses):
{terms_desc}

Additional Information / Specific Clauses:
{additional_info_desc}

Draft the complete, formal legal document now:"""
        return prompt

    def _format_parties_input(self, parties: Any) -> str:
        """Formats parties input from string, list, or dict into structured text."""
        if not parties:
            return "Party 1: [INSERT: First Party Name/Role]\nParty 2: [INSERT: Second Party Name/Role]"

        if isinstance(parties, str):
            return parties.strip()

        if isinstance(parties, list):
            lines = []
            for idx, p in enumerate(parties, 1):
                if isinstance(p, dict):
                    name = p.get("name", f"Party {idx}")
                    role = p.get("role", "Party")
                    org = p.get("organization", "")
                    addr = p.get("address", "")
                    line = f"- Party {idx} ({role}): {name}"
                    if org:
                        line += f", representing {org}"
                    if addr:
                        line += f", located at {addr}"
                    lines.append(line)
                else:
                    lines.append(f"- Party {idx}: {p}")
            return "\n".join(lines)

        if isinstance(parties, dict):
            lines = []
            for k, v in parties.items():
                if isinstance(v, dict):
                    name = v.get("name", k)
                    role = v.get("role", k)
                    addr = v.get("address", "")
                    lines.append(f"- {role}: {name} ({addr})")
                else:
                    lines.append(f"- {k}: {v}")
            return "\n".join(lines)

        return str(parties)

    def _format_terms_input(self, terms: Any) -> tuple[str, List[str]]:
        """Parses and formats user terms into description and clause list."""
        from utils.text_utils import parse_terms_list

        if not terms:
            return "No custom terms provided. Draft standard commercial covenants.", []

        if isinstance(terms, list):
            clauses = [str(t).strip() for t in terms if str(t).strip()]
            desc = "\n".join(f"{idx}. {t}" for idx, t in enumerate(clauses, 1))
            return desc, clauses

        if isinstance(terms, str):
            clauses = parse_terms_list(terms)
            desc = "\n".join(f"{idx}. {t}" for idx, t in enumerate(clauses, 1))
            return desc, clauses

        return str(terms), []

    def _format_additional_info(self, add_info: Optional[Any]) -> str:
        """Formats additional clauses, compensation, jurisdiction, etc."""
        if not add_info:
            return "Standard industry terms apply."

        if isinstance(add_info, dict):
            parts = []
            for k, v in add_info.items():
                if v:
                    parts.append(f"- {k.replace('_', ' ').capitalize()}: {v}")
            return "\n".join(parts) if parts else "Standard industry terms apply."

        return str(add_info).strip()

    def _generate_fallback_document(
        self,
        document_type: str,
        parties_desc: str,
        parties_raw: Any,
        terms_list: List[str],
        effective_date: str,
        additional_info: Optional[Any] = None,
    ) -> str:
        """
        Generates an extensive, highly structured, legally compliant document
        directly using standard legal drafting templates tailored to user inputs.
        Ensures zero-drop reliability and strict fidelity to requirements.
        """
        doc_type_upper = document_type.upper()
        if "CONTRACT" not in doc_type_upper and "AGREEMENT" not in doc_type_upper and "LETTER" not in doc_type_upper:
            doc_title = f"{doc_type_upper} AGREEMENT"
        else:
            doc_title = doc_type_upper

        # Parse party names
        party1_name = "First Party"
        party1_role = "Disclosing Party / Employer / Client / Landlord"
        party1_addr = "[INSERT: Address / Principal Place of Business]"

        party2_name = "Second Party"
        party2_role = "Receiving Party / Employee / Contractor / Tenant"
        party2_addr = "[INSERT: Address / Principal Place of Business]"

        if isinstance(parties_raw, dict):
            keys = list(parties_raw.keys())
            if len(keys) >= 1:
                p1 = parties_raw[keys[0]]
                if isinstance(p1, dict):
                    party1_name = p1.get("name") or keys[0]
                    party1_role = p1.get("role") or "First Party"
                    party1_addr = p1.get("address") or party1_addr
                else:
                    party1_name = str(p1)
                    party1_role = keys[0]
            if len(keys) >= 2:
                p2 = parties_raw[keys[1]]
                if isinstance(p2, dict):
                    party2_name = p2.get("name") or keys[1]
                    party2_role = p2.get("role") or "Second Party"
                    party2_addr = p2.get("address") or party2_addr
                else:
                    party2_name = str(p2)
                    party2_role = keys[1]
        elif isinstance(parties_raw, list) and len(parties_raw) > 0:
            if isinstance(parties_raw[0], dict):
                party1_name = parties_raw[0].get("name", "Party 1")
                party1_role = parties_raw[0].get("role", "First Party")
                party1_addr = parties_raw[0].get("address", party1_addr)
            else:
                party1_name = str(parties_raw[0])
            if len(parties_raw) > 1:
                if isinstance(parties_raw[1], dict):
                    party2_name = parties_raw[1].get("name", "Party 2")
                    party2_role = parties_raw[1].get("role", "Second Party")
                    party2_addr = parties_raw[1].get("address", party2_addr)
                else:
                    party2_name = str(parties_raw[1])
        elif isinstance(parties_raw, str) and parties_raw.strip():
            # Try to extract from text
            lines = [l.strip() for l in parties_raw.split("\n") if l.strip()]
            if len(lines) >= 1:
                party1_name = lines[0]
            if len(lines) >= 2:
                party2_name = lines[1]

        # Extract additional info details
        jurisdiction = "[CONFIRM: Governing Jurisdiction / State]"
        payment_info = "[CONFIRM: Compensation and Payment Terms]"
        termination_info = "Either party may terminate upon thirty (30) days written notice."
        confidentiality_info = "All proprietary materials shall remain strictly confidential."

        if isinstance(additional_info, dict):
            if additional_info.get("governing_law"):
                jurisdiction = additional_info["governing_law"]
            if additional_info.get("compensation"):
                payment_info = additional_info["compensation"]
            if additional_info.get("termination"):
                termination_info = additional_info["termination"]
            if additional_info.get("confidentiality"):
                confidentiality_info = additional_info["confidentiality"]
        elif isinstance(additional_info, str) and additional_info.strip():
            payment_info = additional_info.strip()

        # Build terms table
        table_rows = []
        if terms_list:
            for idx, term in enumerate(terms_list, 1):
                clean_term = term.strip()
                table_rows.append(f"| {idx} | Clause {idx} | {clean_term} |")
        else:
            table_rows.append("| 1 | Core Obligations | The parties agree to fulfill all stated mutual obligations in good faith. |")
            table_rows.append(f"| 2 | Term & Termination | {termination_info} |")

        terms_table_md = "\n".join([
            "| No. | Clause / Term | Specific Terms & Obligations |",
            "|---|---|---|",
            *table_rows
        ])

        # Tailor sections based on document type
        specific_sections = self._build_document_sections(
            doc_type=document_type,
            party1_name=party1_name,
            party1_role=party1_role,
            party2_name=party2_name,
            party2_role=party2_role,
            terms_list=terms_list,
            payment_info=payment_info,
            termination_info=termination_info,
            confidentiality_info=confidentiality_info,
            jurisdiction=jurisdiction,
        )

        doc = f"""# {doc_title}

**Effective Date:** {effective_date}

---

### PARTIES

This {doc_title} (this "Agreement") is entered into and made effective as of **{effective_date}** (the "Effective Date"), by and between:

1. **{party1_name}** (hereinafter referred to as the "{party1_role}"), located at {party1_addr}; and
2. **{party2_name}** (hereinafter referred to as the "{party2_role}"), located at {party2_addr}.

The {party1_role} and the {party2_role} may collectively be referred to as the "Parties" or individually as a "Party."

---

### BACKGROUND AND RECITALS

**WHEREAS**, the Parties wish to establish a formal legal relationship governing their mutual commitments, expectations, and legal rights in connection with {document_type};

**WHEREAS**, each Party possesses the full legal authority, capacity, and power to enter into this Agreement and perform the obligations set forth herein;

**NOW, THEREFORE**, in consideration of the mutual covenants, premises, and valuable consideration contained herein, the receipt and legal sufficiency of which are hereby acknowledged, the Parties agree as follows:

---

{specific_sections}

---

### SUMMARY OF KEY TERMS

{terms_table_md}

---

### GENERAL PROVISIONS

1. **Entire Agreement:** This Agreement, including any attached exhibits and schedules, constitutes the entire understanding between the Parties concerning the subject matter hereof and supersedes all prior negotiations, understandings, and agreements, whether oral or written.
2. **Severability:** If any provision of this Agreement is held to be invalid, illegal, or unenforceable, the remaining provisions shall continue in full force and effect to the maximum extent permissible by law.
3. **Amendments:** No amendment, modification, or waiver of any provision of this Agreement shall be effective unless made in writing and signed by authorized representatives of both Parties.
4. **Counterparts & Electronic Signatures:** This Agreement may be executed in counterparts, each of which shall be deemed an original, and all of which together shall constitute one instrument. Electronic and facsimile signatures shall have the same binding legal effect as handwritten originals.
5. **Notice:** Any notice required or permitted under this Agreement shall be delivered in writing to the addresses specified herein by certified mail, recognized commercial courier, or verified electronic mail.

---

### SIGNATURE BLOCKS

IN WITNESS WHEREOF, the Parties hereto have caused this {doc_title} to be duly executed by their authorized representatives as of the Effective Date.

| **FOR {party1_role.upper()}** | **FOR {party2_role.upper()}** |
| :--- | :--- |
| **Entity / Name:** {party1_name} | **Entity / Name:** {party2_name} |
| **By (Signature):** ___________________________ | **By (Signature):** ___________________________ |
| **Printed Name:** {party1_name} | **Printed Name:** {party2_name} |
| **Title:** Authorized Representative | **Title:** Authorized Representative |
| **Date:** ___________________________ | **Date:** ___________________________ |

---

LEGAL DISCLAIMER: This document was generated using LegalEase AI for drafting and informational assistance only. AI-generated documents may contain errors or may not be appropriate for your specific circumstances. Review the document carefully and consult a qualified legal professional when appropriate.
"""
        return doc.strip()

    def _build_document_sections(
        self,
        doc_type: str,
        party1_name: str,
        party1_role: str,
        party2_name: str,
        party2_role: str,
        terms_list: List[str],
        payment_info: str,
        termination_info: str,
        confidentiality_info: str,
        jurisdiction: str,
    ) -> str:
        """Constructs domain-specific clauses for employment, NDA, lease, freelance, etc."""
        d_lower = doc_type.lower()

        # Build custom terms clauses
        custom_clauses = ""
        if terms_list:
            custom_clauses = "\n".join(
                f"3.{idx} **Specific Term:** {clause}"
                for idx, clause in enumerate(terms_list, 1)
            )
        else:
            custom_clauses = "3.1 The Parties shall cooperate diligently to perform their respective obligations."

        if "nda" in d_lower or "confidential" in d_lower:
            return f"""### 1. DEFINITION OF CONFIDENTIAL INFORMATION
For purposes of this Agreement, "Confidential Information" includes all non-public, proprietary, trade secret, financial, commercial, operational, technical, or customer information disclosed by {party1_name} to {party2_name}, whether orally, visually, or in written or electronic form.

### 2. NON-DISCLOSURE OBLIGATIONS
The Receiving Party ({party2_name}) agrees to:
- Maintain the Disclosing Party's Confidential Information in strict confidence.
- Exercise at least a reasonable standard of care in protecting such information.
- Use Confidential Information solely for the agreed business evaluation.
- Not disclose, publish, or disseminate any Confidential Information to third parties without prior written consent.

### 3. EXCLUSIONS FROM CONFIDENTIALITY
Confidential Information does not include information that:
- Is or becomes publicly known through no breach of this Agreement.
- Was already lawfully in the possession of the Receiving Party prior to disclosure.
- Is independently developed without reference to the Disclosing Party's information.
- Is required to be disclosed pursuant to a lawful court order or regulatory directive.

### 4. SPECIFIC OPERATIONAL TERMS
{custom_clauses}

### 5. DURATION AND RETURN OF MATERIALS
The non-disclosure obligations under this Agreement shall endure for a period of two (2) years from the Effective Date, except for trade secrets, which shall remain protected indefinitely. Upon request, the Receiving Party shall immediately return or securely destroy all proprietary materials.

### 6. REMEDIES FOR BREACH
The Parties acknowledge that any unauthorized disclosure or use of Confidential Information will cause irreparable harm. Accordingly, the Disclosing Party shall be entitled to seek injunctive relief, in addition to any other remedies available at law or in equity.

### 7. GOVERNING LAW & JURISDICTION
This Agreement shall be governed by, construed, and enforced in accordance with the laws of **{jurisdiction}**, without giving effect to conflicts of law principles."""

        elif "employment" in d_lower or "offer" in d_lower:
            return f"""### 1. POSITION, DUTIES, AND RESPONSIBILITIES
The Employer ({party1_name}) hereby engages the Employee ({party2_name}) to perform the duties and responsibilities customary to this role. The Employee agrees to perform all assignments faithfully, diligently, and to the best of their professional ability.

### 2. COMPENSATION AND BENEFITS
- **Compensation:** The Employer shall compensate the Employee in accordance with the agreed terms: {payment_info}.
- **Benefits:** The Employee shall be eligible to participate in company benefit plans, paid time off, and statutory protections in accordance with applicable laws.

### 3. AGREED TERMS AND WORKING CONDITIONS
{custom_clauses}

### 4. CONFIDENTIALITY AND PROPRIETARY INFORMATION
The Employee recognizes that during the course of employment, they will have access to sensitive business data. {confidentiality_info} The Employee agrees not to disclose or misappropriate any proprietary knowledge during or after employment.

### 5. INTELLECTUAL PROPERTY ASSIGNMENT
All inventions, creative works, software, designs, and business methods developed by the Employee in connection with employment shall be deemed "works made for hire" and shall remain the exclusive property of the Employer.

### 6. TERM AND TERMINATION
This employment relationship may be terminated in accordance with the following terms: {termination_info} Upon termination, the Employee shall immediately surrender all company hardware, credentials, and confidential documents.

### 7. GOVERNING LAW
This Agreement shall be governed by and construed in accordance with the laws of **{jurisdiction}**."""

        elif "lease" in d_lower or "tenan" in d_lower:
            return f"""### 1. LEASED PREMISES
The Landlord ({party1_name}) hereby leases to the Tenant ({party2_name}) the real property located at [CONFIRM: Premises Physical Address] (the "Premises").

### 2. TERM AND RENT
- **Term:** The lease term shall commence on {payment_info or 'the Effective Date'}.
- **Rent:** Tenant agrees to pay rent on or before the first day of each calendar month.
- **Security Deposit:** A refundable deposit shall be held to guarantee faithful performance of lease terms.

### 3. TENANCY TERMS AND RESTRICTIONS
{custom_clauses}

### 4. MAINTENANCE, UTILITIES, AND USE
- **Permitted Use:** The Premises shall be used exclusively for lawful residential/commercial purposes.
- **Maintenance:** Tenant shall maintain the Premises in good order and cleanliness, reasonable wear and tear excepted.

### 5. TERMINATION AND SURRENDER
{termination_info} Upon lease expiration or termination, Tenant shall surrender the Premises vacant and in broom-clean condition.

### 6. GOVERNING LAW
This Lease Agreement shall be governed by the landlord-tenant laws of **{jurisdiction}**."""

        elif "freelance" in d_lower or "service" in d_lower or "consult" in d_lower:
            return f"""### 1. SCOPE OF SERVICES AND DELIVERABLES
The Contractor ({party2_name}) agrees to perform professional services and provide deliverables to the Client ({party1_name}) in a timely and workmanlike manner.

### 2. COMPENSATION AND INVOICING
- **Fees:** The Client shall compensate the Contractor pursuant to the agreed rates: {payment_info}.
- **Payment Schedule:** Undisputed invoices shall be payable within thirty (30) days of receipt.

### 3. SPECIFIC CONTRACTUAL TERMS
{custom_clauses}

### 4. INDEPENDENT CONTRACTOR STATUS
The Contractor is an independent contractor, not an employee, agent, or partner of the Client. The Contractor is solely responsible for all income taxes, self-employment taxes, and worker compensation obligations.

### 5. INTELLECTUAL PROPERTY AND WORK PRODUCT
Upon full payment, all deliverables created specifically for the Client shall be assigned to and owned exclusively by the Client. The Contractor retains ownership of pre-existing tools and generic methodologies.

### 6. CONFIDENTIALITY
{confidentiality_info}

### 7. TERM AND TERMINATION
{termination_info}

### 8. GOVERNING LAW AND DISPUTE RESOLUTION
This Agreement shall be governed by the laws of **{jurisdiction}**. Any controversy arising out of this Agreement shall be settled first by good-faith negotiation, followed by binding arbitration if unresolved."""

        else:
            # Generic commercial agreement
            return f"""### 1. PURPOSE AND SCOPE
This Agreement establishes the rights, duties, and covenants of the Parties with respect to the business transaction described herein.

### 2. RESPONSIBILITIES OF THE PARTIES
Each Party shall exercise commercial best efforts, care, and diligence to perform their respective obligations under this Agreement.

### 3. TERMS AND CONDITIONS
{custom_clauses}

### 4. COMPENSATION AND COMMERCIAL CONSIDERATION
{payment_info}

### 5. CONFIDENTIALITY AND NON-DISCLOSURE
{confidentiality_info}

### 6. TERM AND TERMINATION
{termination_info}

### 7. GOVERNING LAW AND JURISDICTION
This Agreement shall be construed, interpreted, and governed under the laws of **{jurisdiction}**."""
