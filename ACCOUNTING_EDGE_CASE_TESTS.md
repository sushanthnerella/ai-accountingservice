# Accounting Edge-Case & Invariant Stress Tests
## Automated Test Results & Forensic Evidence

---

### Test ID: `EDGE-001` — Unbalanced Journal Voucher Rejection
- **Input:** A journal voucher containing total debits of ₹1,000.00 and total credits of ₹900.00.
- **Expected Result:** Immediate rejection with `ValueError: Accounting Invariant Violation: Total Debits != Total Credits`.
- **Actual Result:** Rejection triggered; database rollback executed.
- **Status:** **PASS**

### Test ID: `EDGE-002` — Extraction Math Drift Detection
- **Input:** Extracted invoice data where `Taxable (1000) + CGST (90) + SGST (90) = 1180`, but header total is stated as `₹1,200.00`.
- **Expected Result:** `validate_arithmetic_invariants` returns `False`, automatically routing the document to `REVIEW_PENDING`.
- **Actual Result:** Identified arithmetic discrepancy; returned `False`.
- **Status:** **PASS**

### Test ID: `EDGE-003` — Traceable Journal Reversal
- **Input:** Original voucher `ORIG-1` for ₹5,000.00 reversed by equal and opposite voucher `REV-1`.
- **Expected Result:** Posting of `REV-1` succeeds; trial balance net movement returns to exactly `₹0.0000`.
- **Actual Result:** Net balance across all impacted accounts evaluates strictly to `0.00`.
- **Status:** **PASS**

### Test ID: `EDGE-004` — Cross-Tenant Isolation
- **Input:** User belonging to Organization B attempting to query client ledgers belonging to Organization A via HTTP headers.
- **Expected Result:** API returns `403 Forbidden` (`FORBIDDEN_TENANT_ACCESS`).
- **Actual Result:** Verified `403 Forbidden` returned.
- **Status:** **PASS**

### Test ID: `EDGE-005` — Deduplication Scoping
- **Input:** Re-uploading an identical file (identical SHA-256 hash) within the same client business scope.
- **Expected Result:** Upload accepted without duplicating disk storage; flagged as `is_duplicate = True` and links `duplicate_of_id`.
- **Actual Result:** Successfully detected and flagged with duplicate audit event.
- **Status:** **PASS**
