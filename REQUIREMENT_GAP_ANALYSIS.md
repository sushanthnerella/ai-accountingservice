# Requirement Gap & Risk Analysis
## AI-Powered Accounting Intelligence Platform

---

## 1. Introduction
While the Product Requirements Document (PRD v0.1) outlines a visionary blueprint for an AI-assisted accounting layer for India, several critical domain-specific, legal, technical, and workflow gaps must be identified and resolved prior to software construction.

This document systematically breaks down the ambiguities, missing specifications, edge-case scenarios, and statutory accounting risks.

---

## 2. Statutory & Indian Accounting Domain Gaps

### 2.1 Tax Deducted at Source (TDS) Under Income Tax Act, 1961
- **The Gap in PRD:** Section 15, item 9 lists TDS as an "open decision to finalize". However, in India, virtually every freelancer and B2B SME has payments subject to Section 194J (Professional/Technical fees - 10% or 2%) or Section 194C (Contractor - 1% or 2%).
- **Reconciliation Impact:** When a client pays an invoice of ₹1,00,000, the bank statement will show an incoming credit of exactly **₹90,000** (or ₹98,000). If the reconciliation engine only attempts exact amount or simple partial matching, it will perpetually flag every single standard Indian professional remittance as a partial mismatch!
- **Architectural Remedy:** The match engine must natively support **TDS-deducted settlement rules**:
  $$\text{Expected Receipt} = \text{Invoice Total} - \text{TDS Section 194J/194C/194Q}$$
  The engine must generate a compound journal entry:
  - Debit: Bank Account (₹90,000)
  - Debit: TDS Receivable Asset Account (₹10,000)
  - Credit: Sundry Debtor (₹1,00,000)

### 2.2 GST Section 17(5) Blocked ITC Logic
- **The Gap in PRD:** Module G mentions: *"Input GST paid must not automatically be treated as eligible input tax credit"*, but provides no decision matrix for automated or assisted evaluation.
- **Statutory Constraint:** Under Sec 17(5) of the CGST Act 2017, input tax credit is blocked on:
  - Motor vehicles and conveyances (with specific exceptions).
  - Food and beverages, outdoor catering, beauty treatment, health services, travel benefits extended to employees on vacation.
  - Goods or services used for personal consumption.
  - Goods lost, stolen, destroyed, written off or disposed of by way of gift or free samples.
- **Architectural Remedy:** The AI categorizer cannot decide legal eligibility unilaterally. The system must map HSN/SAC codes and vendor expense categories to an **ITC Eligibility Flag**:
  - `ELIGIBLE_INPUT_SERVICES`
  - `ELIGIBLE_INPUT_GOODS`
  - `ELIGIBLE_CAPITAL_GOODS`
  - `BLOCKED_SEC_17_5` (Tax posted to Expense/Asset rather than Electronic Credit Ledger)
  - `PENDING_CA_DETERMINATION`

### 2.3 Foreign Inward Remittance, Zero-Rated Supplies & LUT
- **The Gap in PRD:** Freelancers in India predominantly export services (software development, digital marketing, design) to US/EU clients via platforms like Upwork, Stripe, Wise, or direct wire transfers.
- **Compliance Requirement:** Under GST rules, export of services is a zero-rated supply. If covered by a **Letter of Undertaking (LUT)**, no IGST is charged. However, the bank receives currency converted into INR with bank deductions and Foreign Inward Remittance Certificate (FIRC) / e-BRC references.
- **Architectural Remedy:** System must support:
  1. Multicurrency invoice definition with exchange rate at invoice date vs bank realized rate.
  2. Foreign Exchange Gain/Loss (Forex) ledger auto-generation upon realization.
  3. LUT reference number attachment on zero-rated export sales invoices.

---

## 3. Bank Statement Ingestion & Parsing Gaps

| Gap Identified | Description & Reality in Indian Banking | Technical Architecture Solution |
|---|---|---|
| **Password-Protected PDFs** | Indian banks (ICICI, HDFC, SBI, Axis) almost universally protect downloaded statements with passwords (e.g., DOB + PAN, last digits of card/account). | Ingestion pipeline must accept an optional document decryption password or prompt the user securely during upload without logging/storing passwords in plain text. |
| **Non-Standardized Narrations** | Narrations are cryptic strings: e.g., `UPI/412389128312/PAYTO/SWIGGY/ICIC/01923` or `NEFT-N12345678-M/S ACME TECHNOL-HDFCC000123`. | Regex pattern extractors for UPI Reference ID (12 digits), NEFT/RTGS UTR numbers (16 or 22 characters), IMPS RRN, and Cheque numbers. |
| **Merged / Multi-Page Statements** | Multi-page statements have repeated table headers, running footers, and page-split transactions. | Layout parser with running balance continuity verification across page boundaries. |

---

## 4. Integration Gaps & Practical Constraints

### 4.1 TallyPrime Interface Reality
- **The Gap in PRD:** "Export or synchronize approved journal entries... The exact supported objects and integration method must be verified".
- **Reality:** TallyPrime runs locally on Windows desktops or on a private LAN server. It does not provide a public cloud REST API. It listens on an internal HTTP port (default `9000`) accepting Tally XML / Tally Definition Language (TDL) POST requests, or requires importing XML files (`Import Data -> Vouchers`).
- **Architectural Solution for Release 1:**
  1. **Primary Interface:** Generate 100% compliant **Tally XML Voucher Import files** (zipped packages by date/batch) with exact ledger mappings.
  2. **Secondary/Advanced Interface:** Lightweight local Desktop Sync Agent (Python/Golang daemon) connecting to local `http://localhost:9000` via XML-over-HTTP for users desiring direct push.

### 4.2 Zoho Books OAuth & Rate Limits
- **The Gap in PRD:** Zoho Books rate limits and regional domains are not detailed.
- **Reality:** Zoho operates multiple data centers with distinct TLDs: `.com` (US), `.in` (India), `.eu` (Europe). Indian users are on `accounts.zoho.in` and `books.zoho.in`. Rate limits are 100 calls/minute per organization.
- **Architectural Solution:**
  1. Dynamic regional data center selection during OAuth handshake.
  2. Rate-limiter with token-bucket algorithm in the synchronization queue.
  3. Bulk API endpoints used where possible (e.g., batch invoice creation).

---

## 5. Subscription & Metering Gaps

### 5.1 Definition of "One Billable Document"
- **PRD Question:** What constitutes a document? (Is a 50-page bank statement 1 document or 50 documents? Is a 3-page invoice 1 document?)
- **Architectural Recommendation:**
  - Invoices / Receipts: **1 Document = 1 File up to 5 pages**.
  - Bank Statements: Metered by **Page Count** or **Transaction Batch** (e.g., 1 statement page = 1 document credit, OR 50 transactions = 1 document credit).
  - Failed extractions due to OCR unreadability or duplicate files are **zero-billed**.

---

## 6. Items Requiring Formal Validation by an Indian Practicing CA

1. **COA Seed Schema:** Validation of standard Ledger grouping and schedule compliance for Indian Sole Proprietorships and LLPs.
2. **Reverse Charge Mechanism (RCM) Rules:** Exhaustive list of RCM triggers under Section 9(3) of CGST Act.
3. **HSN/SAC Validation Rules:** Confirm whether 4-digit HSN is sufficient for freelancers/SMEs under ₹5 Cr turnover, or if 6/8 digits must be enforced.
4. **GST Rounding Off:** Verify compliance with Section 170 of CGST Act (rounding to nearest rupee).
5. **Electronic Cash vs Credit Ledger Offset Hierarchy:** Verification of IGST $\rightarrow$ CGST $\rightarrow$ SGST credit utilization sequence.
