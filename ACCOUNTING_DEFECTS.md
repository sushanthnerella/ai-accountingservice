# Accounting Defects & Remediation Log
## Independent Accounting Engine Verification

---

### Defect 1: Trial Balance Zero Account Filtering
- **Severity:** Low
- **Observed Behavior:** Accounts with zero activity or completely reversed vouchers remain visible in the trial balance report as zero-balance rows.
- **Remediation Recommendation:** Add an optional boolean filter query parameter `include_zero_balances=False` to the `/ledger/trial-balance` endpoint.

### Defect 2: Customer / Vendor Sub-Ledger Linking on Generic Journal Entries
- **Severity:** Medium
- **Observed Behavior:** When manual journal vouchers are entered directly via the API without an invoice reference, the sub-ledger outstanding balance must be inferred from the Chart of Accounts rather than an explicit `party_id`.
- **Remediation Recommendation:** Introduce an explicit `party_id` (foreign key to `client_businesses` or counterparties) on individual `journal_lines` to facilitate multi-currency debtor ageing.

### Defect 3: GST Cess & Round-Off Line Item Automation
- **Severity:** Low
- **Observed Behavior:** Cess amounts and round-off paisa corrections must currently be explicitly calculated in the payload lines.
- **Remediation Recommendation:** Implement an auto-balancing round-off posting line helper in `LedgerService` that stages `Round Off Expense/Income` when totals differ by $< ₹1.00$.
