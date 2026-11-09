# Accounting & GST Statutory Audit Report
## AI-Powered Accounting Intelligence SaaS
**Date:** November 9, 2026
**Auditor:** Accounting Systems Engineer & Tax Architect

---

## 1. Accounting Engine Invariant Audit
- **Double-Entry Equality:** Verified in `backend/app/services/ledger_service.py` (`verify_entry_balanced`). If $\sum \text{Debits} \ne \sum \text{Credits}$, the transaction is aborted with `Accounting Invariant Violation`.
- **Numeric Precision:** Verified across all models (`invoices`, `invoice_items`, `bank_accounts`, `bank_transactions`, `journal_lines`). Every amount column uses `Numeric(18, 4)` and Python `Decimal`. Floating-point numbers are completely prohibited.
- **Traceability:** Every journal voucher references its source document ID and reconciliation match ID.

## 2. Indian GST Statutory Engine Audit
- **Place of Supply (POS) Logic:**
  - Evaluated in `backend/app/services/gst_service.py` (`determine_tax_breakup`).
  - Correctly routes Intrastate supplies ($Supplier State == POS State$) to CGST + SGST (split 50/50).
  - Correctly routes Interstate supplies ($Supplier State \ne POS State$) to IGST.
- **Section 17(5) Blocked ITC:**
  - Evaluated in `evaluate_itc_eligibility`. Correctly blocks credits for Food & Beverages, Catering, Motor Vehicles, and Personal Consumption.
- **GSTR-3B Computation:**
  - Correctly aggregates outward tax liabilities (Table 3.1) and subtracts eligible ITC while isolating blocked ITC (Table 4) to produce the net GST payable.
- **Finding (Medium):** Special Economic Zone (SEZ) supplies and deemed exports with LUT zero-rating require explicit LUT expiration validation.
  - *Recommendation:* Add LUT validity date checks and forex remittance (FIRC) tracking fields in Phase 2 enhancements.

## 3. Indian TDS Audit (Sections 194J & 194C)
- **Matching Rules:**
  - `backend/app/services/reconciliation_service.py` evaluates 10% TDS (Section 194J Professional) and 2% TDS (Section 194J Technical).
  - Asserts that Bank Remittance + TDS Deducted clears the Invoice total.
- **Finding (Low):** Section 194C individual/HUF contractor rate (1%) vs company rate (2%) is not currently bifurcated based on vendor entity type.
  - *Recommendation:* Incorporate vendor entity classification into TDS rate determination.
