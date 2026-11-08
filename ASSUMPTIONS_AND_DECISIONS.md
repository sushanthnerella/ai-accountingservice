# Architectural Decisions & Baseline Assumptions (ADR)
## AI-Powered Accounting Intelligence Platform

---

## 1. Architectural Decisions Records (ADRs)

### ADR-01: Financial Precision & Numeric Data Types
- **Context:** Floating-point numbers (`float`, `double`, JavaScript `number`) suffer from IEEE 754 binary rounding inaccuracies (e.g., `0.1 + 0.2 = 0.30000000000000004`). In financial accounting, any rounding drift violates double-entry balancing ($\sum \text{Dr} = \sum \text{Cr}$) and statutory tax reconciliation.
- **Decision:**
  - **Database:** All monetary amounts, tax rates, and ledger balances MUST be stored as `NUMERIC(18, 4)` in PostgreSQL.
  - **Backend (Python):** Use the standard library `decimal.Decimal` exclusively. Never cast monetary values to `float`.
  - **Frontend (TypeScript):** Amounts transmitted as JSON strings or formatted via dedicated fixed-precision helpers (`bignumber.js` or `currency.js`).
  - **Tax Rounding:** Follow Section 170 of CGST Act (rounding final tax amounts to the nearest integer rupee, but maintaining exact paise at the line-item level).
- **Status:** **APPROVED & INVIOLABLE**.

### ADR-02: Tenant Isolation Strategy
- **Context:** The platform serves both individual freelancers and CA firms managing hundreds of client businesses. Cross-tenant data leakage would be catastrophic for compliance and trust.
- **Decision:**
  - **Hybrid Tenant Isolation:** Logical row-level tenant isolation via an indexed `organization_id` on every table, combined with PostgreSQL Row-Level Security (RLS) policies and SQLAlchemy multi-tenant query interception.
  - Every API request authenticates a JWT containing `tenant_id`, `user_id`, and `role`. The database connection context sets `app.current_org_id` in PostgreSQL session parameters for RLS enforcement.
- **Status:** **APPROVED**.

### ADR-03: AI Decoupling & LLM Abstraction Layer
- **Context:** Commercial LLM APIs (OpenAI, Gemini, Anthropic) change models, pricing, and rate limits frequently. In addition, some enterprise CA firms require on-premise or sovereign data processing using open-source models (Llama 3, Mistral, Qwen).
- **Decision:**
  - Design a unified `DocumentExtractionProvider` interface:
    ```python
    class DocumentExtractionProvider(ABC):
        @abstractmethod
        async def extract_invoice(self, document_bytes: bytes, mime_type: str) -> ExtractedInvoiceSchema:
            pass
        @abstractmethod
        async def extract_bank_statement(self, document_bytes: bytes, mime_type: str) -> ExtractedStatementSchema:
            pass
    ```
  - Implement swappable adapters: `OpenAIProvider`, `GeminiProvider`, `ClaudeProvider`, and `LocalOcrLayoutProvider` (PyMuPDF + PaddleOCR/Tesseract + Local LLM).
  - Use Pydantic V2 schemas with strict regex and arithmetic validators for zero-hallucination structured output.
- **Status:** **APPROVED**.

### ADR-04: Double-Entry Ledger Immutability
- **Context:** Standard CRUD applications allow updating records. In accounting, updating or deleting a posted journal entry destroys the audit trail and invalidates historical financial reports.
- **Decision:**
  - `journal_entries` and `journal_lines` tables have `INSERT`-only permissions for posted statuses.
  - Corrections are enacted via **Reversal Entries** (`is_reversal = True`, `reversal_of_entry_id = <UUID>`) or **Adjustment Entries**.
  - A PostgreSQL trigger prohibits `UPDATE` or `DELETE` on records where `status = 'POSTED'`.
- **Status:** **APPROVED**.

### ADR-05: Human-in-the-Loop Reconciliation Gate
- **Context:** An AI model might match a bank credit of ₹50,000 to an invoice of ₹50,000, but in reality, the payment was a shareholder loan or customer advance. Unchecked auto-posting leads to misstated financial statements.
- **Decision:**
  - AI matching calculates a confidence score and generates an audit explanation, but sets status to `MATCH_SUGGESTED` or `REVIEW_PENDING`.
  - Only an authorized user action (`APPROVE`) moves the match to `MATCHED` and triggers journal entry staging.
- **Status:** **APPROVED**.

---

## 2. Baseline Assumptions

1. **Financial Year Calendar:** The Indian statutory financial year runs from **April 1 to March 31**. The system will support historical FYs and handle the March-April transition period seamlessly.
2. **GST State Codes:** India uses a standardized 2-digit state code system (01 Jammu & Kashmir to 37 Andhra Pradesh, 97 Other Territory, etc.). Tax logic will use this statutory state code mapping to compute CGST/SGST vs IGST.
3. **Primary Base Currency:** Indian Rupee (`INR` / `₹`). Multi-currency invoices (USD, EUR, GBP) will be translated to INR using the exchange rate specified on the invoice or realized at the bank settlement date.
4. **Bank Statement Integrity:** We assume bank statement transactions represent realized cash movements. Unpresented cheques or dishonored cheques are handled during bank reconciliation adjustments.
5. **Subscription Billing Gate:** Document limits are tracked per billing cycle (monthly). A document counts towards usage only upon successful OCR extraction and schema parsing.
