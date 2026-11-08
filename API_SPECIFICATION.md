# OpenAPI 3.1 & REST API Specification
## AI-Powered Accounting Intelligence Platform

---

## 1. API Architecture Conventions
- **Base URL:** `/api/v1`
- **Authentication:** Bearer JWT in `Authorization` header (`Bearer <access_token>`).
- **Tenancy Headers:**
  - `X-Organization-Id: <UUID>` (Identifies subscriber firm/freelancer)
  - `X-Client-Business-Id: <UUID>` (Identifies active client profile for CA firms)
- **Content-Type:** `application/json` (except multi-part upload endpoints)
- **Standard Error Envelope:**
  ```json
  {
    "success": false,
    "error_code": "ACCOUNTING_INVARIANT_VIOLATION",
    "message": "Debit total (1000.00) does not equal Credit total (950.00).",
    "details": {
      "sum_debits": "1000.0000",
      "sum_credits": "950.0000",
      "difference": "50.0000"
    },
    "request_id": "req_01HP3794XYZ"
  }
  ```

---

## 2. Core Endpoints Breakdown

### 2.1 Authentication & Workspace Switcher
- `POST /api/v1/auth/login` — Returns JWT with user permissions and accessible organizations.
- `GET /api/v1/workspaces/clients` — Returns list of clients under the authenticated CA Firm with reconciliation health indicators.
- `POST /api/v1/workspaces/switch-context` — Sets active client business for the session.

---

### 2.2 Document Management & Ingestion

#### `POST /api/v1/documents/upload`
Upload single or multiple files (PDF, JPG, PNG, CSV, XLSX, ZIP).
- **Request:** `multipart/form-data`
  - `files`: File[] (binary)
  - `category`: `AUTO_DETECT | BANK_STATEMENT | SALES_INVOICE | PURCHASE_INVOICE | EXPENSE_RECEIPT`
  - `pdf_password`: (Optional string for password-protected bank statements)
- **Response:** `202 Accepted`
  ```json
  {
    "success": true,
    "batch_id": "bch_01HP389AB01",
    "uploaded_files": [
      {
        "document_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
        "file_name": "HDFC_Current_Statement_Oct2024.pdf",
        "sha256_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "status": "PROCESSING",
        "is_duplicate": false
      }
    ]
  }
  ```

#### `GET /api/v1/documents/{document_id}`
Retrieves document processing status and extracted schema.
- **Response:** `200 OK`
  ```json
  {
    "document_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "file_name": "INV_2024_089.pdf",
    "status": "EXTRACTED",
    "confidence_score": 0.9450,
    "extracted_data": {
      "invoice_number": "INV-2024-089",
      "invoice_date": "2024-10-15",
      "counterparty_name": "Infosys BPM Limited",
      "counterparty_gstin": "29AABCI1234F1Z8",
      "taxable_amount": "100000.0000",
      "igst_amount": "18000.0000",
      "cgst_amount": "0.0000",
      "sgst_amount": "0.0000",
      "total_amount": "118000.0000",
      "line_items": [
        {
          "description": "IT Consulting Services for Oct 2024",
          "hsn_sac": "998311",
          "rate": 18.0,
          "taxable_value": "100000.0000"
        }
      ]
    }
  }
  ```

#### `PATCH /api/v1/documents/{document_id}/override`
Allows the user/accountant to correct OCR/AI field extractions before approval.

---

### 2.3 Bank Transactions & Reconciliation

#### `GET /api/v1/reconciliations/candidates`
Returns proposed matches computed by the multi-factor reconciliation engine.
- **Query Params:** `status=PENDING&min_confidence=0.70`
- **Response:** `200 OK`
  ```json
  {
    "candidates": [
      {
        "match_id": "f8a91c32-4411-4b10-8b54-7f8e3d09a231",
        "match_scenario": "TDS_ADJUSTED_SETTLEMENT",
        "confidence_score": 0.9650,
        "bank_transaction": {
          "id": "tx_01HP3901",
          "transaction_date": "2024-10-25",
          "narration": "NEFT-N298310-INFOSYS BPM LTD-HDFCC000123",
          "credit_amount": "108000.0000",
          "utr_number": "N298310"
        },
        "matched_invoice": {
          "id": "inv_01HP3881",
          "invoice_number": "INV-2024-089",
          "counterparty_name": "Infosys BPM Limited",
          "total_amount": "118000.0000"
        },
        "settlement_breakdown": {
          "bank_credit": "108000.0000",
          "tds_deducted": "10000.0000",
          "tds_section": "194J_PROF",
          "difference": "0.0000"
        },
        "match_rationale": "UTR token found in narration; Credit amount equals Invoice Total minus 10% Section 194J TDS (₹10,000.00)."
      }
    ]
  }
  ```

#### `POST /api/v1/reconciliations/{match_id}/approve`
Approves the match, locks invoice and bank transaction, and posts a balanced double-entry journal voucher.

#### `POST /api/v1/reconciliations/{match_id}/reject`
Rejects the suggestion with an optional audit note and returns items to the review queue.

---

### 2.4 Accounting Engine & Financial Reporting

- `GET /api/v1/accounting/trial-balance?financial_year=2024-2025&as_of_date=2024-10-31`
- `GET /api/v1/accounting/profit-and-loss?from_date=2024-04-01&to_date=2024-10-31`
- `GET /api/v1/accounting/balance-sheet?as_of_date=2024-10-31`
- `GET /api/v1/accounting/general-ledger/{account_id}?from_date=2024-04-01&to_date=2024-10-31`

---

### 2.5 Indian GST Intelligence

#### `GET /api/v1/gst/gstr-1/summary?financial_year=2024-2025&period=2024-10`
Returns Section-wise GSTR-1 preparation figures (Table 4 B2B, Table 6 Exports, Table 7/8 B2C, Table 12 HSN Summary).

#### `GET /api/v1/gst/gstr-3b/computation?financial_year=2024-2025&period=2024-10`
Computes monthly GSTR-3B tax liability:
- Table 3.1: Taxable turnover, IGST, CGST, SGST collected.
- Table 4: Eligible ITC segregated from Ineligible ITC under Section 17(5).
- Net Tax Payable after automated credit ledger utilization rules.

#### `POST /api/v1/gst/gstr-2b/reconcile`
Uploads GSTR-2B JSON downloaded from the government portal and matches against the internal Purchase Register.

---

### 2.6 External Integrations (Tally & Zoho)

- `POST /api/v1/integrations/tally/export-xml` — Generates a downloadable Tally Definition Language (TDL) XML package for the selected voucher batch.
- `POST /api/v1/integrations/zoho/connect` — Initiates OAuth2 authorization flow for `books.zoho.in`.
- `POST /api/v1/integrations/zoho/sync` — Synchronizes approved journal vouchers and contact records to Zoho Books with idempotency and rate limiting.
