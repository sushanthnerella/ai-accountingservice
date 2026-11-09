# Ledger and Report Reconciliation Report
## Scenario: Suresh Enterprises (Telangana Sole Proprietorship)

---

## 1. General Ledger Account Balances

| Account Code | Account Name | Type | Debit (₹) | Credit (₹) | Net Balance (₹) |
|---|---|---|---|---|---|
| `1001` | Current Bank Account | ASSET | 110,000.00 | 5,000.00 | **105,000.00 (DR)** |
| `1002` | Accounts Receivable | ASSET | 23,600.00 | 10,000.00 | **13,600.00 (DR)** |
| `1003` | Input CGST | ASSET | 900.00 | 0.00 | **900.00 (DR)** |
| `1004` | Input SGST | ASSET | 900.00 | 0.00 | **900.00 (DR)** |
| `2001` | Accounts Payable | LIABILITY | 5,000.00 | 11,800.00 | **6,800.00 (CR)** |
| `2002` | Output CGST | LIABILITY | 0.00 | 1,800.00 | **1,800.00 (CR)** |
| `2003` | Output SGST | LIABILITY | 0.00 | 1,800.00 | **1,800.00 (CR)** |
| `3001` | Owner Capital | EQUITY | 0.00 | 100,000.00 | **100,000.00 (CR)** |
| `4001` | Service Revenue | INCOME | 0.00 | 20,000.00 | **20,000.00 (CR)** |
| `5001` | Service Expenses | EXPENSE | 10,000.00 | 0.00 | **10,000.00 (DR)** |
| **TOTAL** | | | **150,400.00** | **150,400.00** | **0.00** |

---

## 2. Statement of Profit and Loss (Accrual Basis)

```
Revenues:
  Service Revenue (Account 4001):                         ₹ 20,000.00
  Total Revenue:                                          ₹ 20,000.00

Expenses:
  Service Expenses (Account 5001):                        ₹ 10,000.00
  Total Expenses:                                         ₹ 10,000.00
---------------------------------------------------------------------
NET PROFIT:                                               ₹ 10,000.00
```

---

## 3. Balance Sheet (as of November 9, 2026)

```
ASSETS
Current Assets:
  Current Bank Account:                   ₹ 105,000.00
  Accounts Receivable (Sundry Debtors):   ₹  13,600.00
  Input Tax Credit (CGST + SGST):         ₹   1,800.00
------------------------------------------------------
TOTAL ASSETS:                             ₹ 120,400.00

LIABILITIES & PROPRIETOR'S EQUITY
Current Liabilities:
  Accounts Payable (Sundry Creditors):    ₹   6,800.00
  Output GST Liability (CGST + SGST):     ₹   3,600.00
Total Liabilities:                                        ₹  10,400.00

Proprietor's Capital & Equity:
  Owner Capital:                          ₹ 100,000.00
  Add: Net Profit for Period:             ₹  10,000.00
Total Equity:                                             ₹ 110,000.00
------------------------------------------------------
TOTAL LIABILITIES & EQUITY:                               ₹ 120,400.00
```
---

## 4. GST Computation (GSTR-3B Summary)

- **Total Outward Tax (CGST + SGST @ 9% each):** ₹3,600.00
- **Total Eligible Input Tax Credit:** ₹1,800.00
- **Net GST Payable to Government:** ₹1,800.00 (CGST: ₹900.00, SGST: ₹900.00)
- **Reconciliation Status:** Perfectly aligned with general ledger balances.
