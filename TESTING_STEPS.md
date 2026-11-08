# Comprehensive Testing Steps & Verification Strategy
## AI-Powered Accounting Intelligence Platform

---

## 1. Overview & Verification Philosophy
The platform manages statutory financial books and tax records. Testing must guarantee:
1. **Mathematical Determinism:** Inviolable double-entry balancing ($\sum \text{Debits} \equiv \sum \text{Credits}$) and tax arithmetic.
2. **Strict Multi-Tenant Isolation:** Zero data leakage across organizations or clients.
3. **Data Integrity:** Invariant checks preventing corrupt documents or duplicate transactions from entering accounting ledgers.

---

## 2. Test Suites Structure (Four-Tier Architecture)

```
tests/
├── unit/
│   ├── test_decimal_math.py          # Currency precision & rounding invariant checks
│   ├── test_gst_determination.py     # Place of Supply & Section 17(5) ITC rules
│   └── test_hash_deduplication.py    # SHA-256 computation and duplicate detection
├── integration/
│   ├── test_auth_jwt.py              # User registration, Argon2id, JWT lifecycle
│   ├── test_tenancy_rls.py           # PostgreSQL RLS session switching & cross-tenant leak checks
│   ├── test_client_switcher.py       # CA Firm client switching and scoped querying
│   ├── test_document_upload.py       # Multi-file upload, magic bytes validation, S3 storage
│   └── test_audit_immutability.py    # Append-only audit trail verification
├── invariants/
│   └── test_journal_balance_trigger.py # DB trigger aborting imbalanced journal entries
└── e2e/
    └── test_upload_to_review_flow.py   # Full flow: Auth -> Client Switch -> Upload -> Status
```

---

## 3. Step-by-Step Test Execution Procedures

### Test Step 1: Authentication & Authorization Flow
1. **User Registration:**
   - Send `POST /api/v1/auth/register` with valid email, password, and organization type (`FREELANCER` or `CA_FIRM`).
   - *Expected:* Status `201 Created`, user created with hashed password (Argon2id), organization created.
2. **User Login:**
   - Send `POST /api/v1/auth/login` with registered credentials.
   - *Expected:* Status `200 OK`, response contains Ed25519/HS256 signed access token (15-min lifespan) and secure HTTP-only refresh cookie.
3. **Protected Endpoint Access:**
   - Send `GET /api/v1/workspaces/clients` with `Authorization: Bearer <token>`.
   - *Expected:* Status `200 OK`.
   - Send without token or with expired token:
   - *Expected:* Status `401 Unauthorized`.

---

### Test Step 2: Multi-Tenant Isolation & PostgreSQL Row-Level Security (RLS)
1. **Setup Two Independent Organizations:**
   - Org A: "Alpha CA Firm" (ID: `org_alpha_uuid`) with Client A1 ("Acme Tech").
   - Org B: "Beta CA Firm" (ID: `org_beta_uuid`) with Client B1 ("Apex Traders").
2. **Execute Cross-Tenant Query Test:**
   - Authenticate as User A (Org A).
   - Set database context: `SET LOCAL app.current_org_id = 'org_alpha_uuid'`.
   - Attempt to query document or client ID belonging to Client B1:
     `SELECT * FROM client_businesses WHERE id = '<client_b1_uuid>';`
   - *Expected:* Zero rows returned (or `404 Not Found` via API).
3. **Tampered Header Attack Test:**
   - Send request with User A's JWT but with header `X-Organization-Id: <org_beta_uuid>`.
   - *Expected:* Status `403 Forbidden` (Middleware validates that the user's membership permits access to the requested organization).

---

### Test Step 3: Document Ingestion, Validation & Deduplication
1. **Valid File Upload:**
   - Send `POST /api/v1/documents/upload` with a valid PDF invoice and CSV bank statement.
   - Header: `X-Organization-Id: <org_id>`, `X-Client-Business-Id: <client_id>`.
   - *Expected:* Status `202 Accepted`, batch ID returned, document status `PROCESSING`, SHA-256 hash computed.
2. **MIME & File Signature (Magic Bytes) Spoofing Test:**
   - Rename an `.exe` executable file to `invoice.pdf` and upload.
   - *Expected:* Status `400 Bad Request` with error code `INVALID_FILE_SIGNATURE`.
3. **Duplicate File Detection Test:**
   - Upload the identical file (matching SHA-256) within the same client business scope.
   - *Expected:* The system detects the duplicate, marks `is_duplicate = TRUE`, and bypasses redundant Celery ingestion tasks without consuming billable document quota.
4. **Password-Protected Statement Test:**
   - Upload password-protected bank statement PDF with `pdf_password` parameter.
   - *Expected:* Parser decrypts in memory, extracts records, and does not persist the plaintext password to disk or logs.

---

### Test Step 4: Accounting Invariant & Double-Entry Verification
1. **Balanced Journal Entry Test:**
   - Stage journal entry:
     - Debit: Bank Account ₹10,000.00
     - Credit: Customer Ledger ₹10,000.00
   - Update entry status to `is_posted = TRUE`.
   - *Expected:* Successfully committed to `journal_entries` and `journal_lines`.
2. **Imbalanced Entry Invariant Rejection Test:**
   - Stage journal entry:
     - Debit: Bank Account ₹10,000.00
     - Credit: Customer Ledger ₹9,500.00 (Difference: ₹500.00)
   - Attempt to commit with `is_posted = TRUE`.
   - *Expected:* PostgreSQL trigger `trg_verify_journal_balance` aborts the transaction with error:
     `Accounting Invariant Violation: Journal Entry is not balanced! Total Debits: 10000.00, Total Credits: 9500.00`.
3. **Posted Record Immutability Test:**
   - Attempt `UPDATE journal_entries SET narration = 'Changed' WHERE is_posted = TRUE;`
   - *Expected:* Aborted by immutability trigger. Corrections must use reversal journals.

---

### Test Step 5: Indian Statutory Reconciliation & GST Determination
1. **Place of Supply (POS) Intrastate vs Interstate Test:**
   - Supplier State Code: `27` (Maharashtra), Buyer State Code: `27` (Maharashtra).
   - *Expected:* Tax decomposed into CGST (9%) + SGST (9%), IGST = 0.
   - Supplier State Code: `27` (Maharashtra), Buyer State Code: `29` (Karnataka).
   - *Expected:* Tax decomposed into IGST (18%), CGST = 0, SGST = 0.
2. **Section 194J TDS Deduction Settlement Test:**
   - Invoice Amount: ₹1,00,000.00 (Plus 18% GST = ₹1,18,000.00).
   - Bank Remittance Received: ₹1,08,000.00 (Client deducted 10% TDS on base = ₹10,000.00).
   - Run reconciliation match engine.
   - *Expected:* Matched under scenario `TDS_ADJUSTED_SETTLEMENT` with confidence $> 95\%$. Staged compound journal voucher:
     - Dr: Bank Account (₹1,08,000.00)
     - Dr: TDS Receivable (₹10,000.00)
     - Cr: Sundry Debtor (₹1,18,000.00).
3. **Section 17(5) Blocked ITC Test:**
   - Expense Invoice for "Corporate Restaurant Catering / Food & Beverage".
   - *Expected:* System flags `itc_eligibility = 'INELIGIBLE_SEC_17_5'`. GST is capitalized to expense rather than credited to Electronic Credit Ledger.

---

## 4. How to Run the Automated Test Suite

### Prerequisites
- Python 3.11+
- PostgreSQL 16 (with test database `accounting_test`)
- Redis 7+

### Commands
```bash
# 1. Activate virtual environment
cd backend
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# 2. Run all unit and invariant tests
pytest tests/unit tests/invariants -v

# 3. Run integration & tenant isolation tests
pytest tests/integration -v --tb=short

# 4. Run full test suite with coverage report
pytest --cov=app --cov-report=term-missing tests/
```
