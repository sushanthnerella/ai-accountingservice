# Journal Entry Validation Log
## Scenario: Suresh Enterprises (Telangana Sole Proprietorship)

---

### Voucher 1: Owner Capital Introduced
- **Entry Number:** `JV-001`
- **Voucher Type:** `RECEIPT`
- **Posting Date:** `2026-11-09`
- **Lines:**
  1. `DR` Account 1001 (Current Bank Account) — ₹100,000.00
  2. `CR` Account 3001 (Owner Capital) — ₹100,000.00
- **Balance Invariant Check:** DR 100,000 == CR 100,000 (**PASSED**)

### Voucher 2: Purchase Service on Credit
- **Entry Number:** `JV-002`
- **Voucher Type:** `PURCHASE_BILL`
- **Posting Date:** `2026-11-09`
- **Lines:**
  1. `DR` Account 5001 (Service Expenses) — ₹10,000.00
  2. `DR` Account 1003 (Input CGST @ 9%) — ₹900.00
  3. `DR` Account 1004 (Input SGST @ 9%) — ₹900.00
  4. `CR` Account 2001 (Accounts Payable) — ₹11,800.00
- **Balance Invariant Check:** DR 11,800 == CR 11,800 (**PASSED**)

### Voucher 3: Sales Service on Credit
- **Entry Number:** `JV-003`
- **Voucher Type:** `SALES_INVOICE`
- **Posting Date:** `2026-11-09`
- **Lines:**
  1. `DR` Account 1002 (Accounts Receivable) — ₹23,600.00
  2. `CR` Account 4001 (Service Revenue) — ₹20,000.00
  3. `CR` Account 2002 (Output CGST @ 9%) — ₹1,800.00
  4. `CR` Account 2003 (Output SGST @ 9%) — ₹1,800.00
- **Balance Invariant Check:** DR 23,600 == CR 23,600 (**PASSED**)

### Voucher 4: Partial Customer Payment Received
- **Entry Number:** `JV-004`
- **Voucher Type:** `RECEIPT`
- **Posting Date:** `2026-11-09`
- **Lines:**
  1. `DR` Account 1001 (Current Bank Account) — ₹10,000.00
  2. `CR` Account 1002 (Accounts Receivable) — ₹10,000.00
- **Balance Invariant Check:** DR 10,000 == CR 10,000 (**PASSED**)
- **Sub-Ledger Impact:** Customer balance reduced from ₹23,600.00 to ₹13,600.00.

### Voucher 5: Partial Supplier Payment
- **Entry Number:** `JV-005`
- **Voucher Type:** `PAYMENT`
- **Posting Date:** `2026-11-09`
- **Lines:**
  1. `DR` Account 2001 (Accounts Payable) — ₹5,000.00
  2. `CR` Account 1001 (Current Bank Account) — ₹5,000.00
- **Balance Invariant Check:** DR 5,000 == CR 5,000 (**PASSED**)
- **Sub-Ledger Impact:** Supplier balance reduced from ₹11,800.00 to ₹6,800.00.
