# Comprehensive Requirements Specification (SRS)
## AI-Powered Accounting Intelligence Platform (India SaaS)
**Document Status:** Approved for Architecture Design  
**Target Market:** India (Freelancers, Sole Proprietors, LLPs, Small CA & Accounting Firms)  
**Standard Compliance:** Ind AS, ICAI Guidance Notes, CGST/SGST/IGST Acts 2017

---

## 1. Executive Summary & Product Objective
The platform is an **accountant-in-the-loop intelligence and reconciliation layer** positioned upstream from final accounting masters (TallyPrime, Zoho Books). Its core mission is to automate the ingestion, OCR/extraction, bank statement parsing, multi-way reconciliation, and GST-attributed journal staging while strictly preserving double-entry accounting integrity, mathematical determinism, and full auditability.

**Primary Principle:** AI suggests; deterministic rules validate; qualified humans (Freelancers/CAs) approve; the immutable engine posts.

---

## 2. Stakeholder Profiles & Personas

### 2.1 Persona 1: The Independent Professional / Freelancer (Rohan)
- **Profile:** Software consultant / creative freelancer operating as a sole proprietorship.
- **Pain Points:** 
  - Mixes domestic and international client remittances (FIRC/e-BRC).
  - Unclear about RCM liability on SaaS subscriptions and export zero-rating (LUT).
  - Struggles with quarterly GSTR-3B preparation and tracking TDS under Sec 194J.
- **Key Needs:**
  - One-click upload of bank statement (PDF/Excel) and sales invoices.
  - Transparent P&L, accounts receivable ageing, and net GST payable visibility.

### 2.2 Persona 2: The Small CA Firm Partner (Priya, FCA)
- **Profile:** Partner at a 4-person CA firm managing 45 SME and freelancer clients.
- **Pain Points:**
  - Clients send unstructured bags of invoices (WhatsApp scans, skewed PDFs) at month-end.
  - Manual cross-matching of ICICI/HDFC bank transactions with invoices takes 70% of junior staff time.
  - GSTR-2B ITC matching against purchase ledgers is prone to manual oversight.
- **Key Needs:**
  - Multi-tenant client workspace switcher.
  - High-throughput bulk document upload queue.
  - Batch review, difference-highlighting, and automated one-to-many match proposals.
  - Direct export of verified, balanced XML/JSON vouchers into TallyPrime and Zoho Books.

---

## 3. Functional Requirements (FR)

### Module A: Multi-Tenant Identity, Workspaces & RBAC
- **FR-A01:** Secure registration and multi-factor authentication (email + TOTP/SMS).
- **FR-A02:** Multi-tenant workspace separation:
  - *Freelancer Workspace:* Single business entity profile.
  - *CA Firm Workspace:* Multi-client hierarchy (Firm -> Clients -> FYs -> Books).
- **FR-A03:** Granular Role-Based Access Control (RBAC):
  - `Firm Admin / Partner`: Full master setup, client management, user permissions.
  - `Senior CA / Reviewer`: Final approval authority to post to internal ledger and trigger Tally/Zoho sync.
  - `Staff Accountant / Data Entry`: Ingestion, field correction, reconciliation verification.
  - `Client / Freelancer View`: Read-only or upload-only access with query submission.
- **FR-A04:** Business Profile & Statutory Config:
  - Entity type (Proprietorship, Partnership, LLP, Pvt Ltd).
  - 15-digit GSTIN profile, state code, composition vs regular scheme indicator.
  - Financial Year configuration (April 1 to March 31 cycle, multiple open/closed FYs).
  - Bank account master with IFSC, account number, opening balances.

### Module B & C: Document Ingestion & AI Intelligence Pipeline
- **FR-BC01:** Multi-format ingestion: PDF (vector & raster), JPG, PNG, CSV, XLS, XLSX, and bulk ZIP archives.
- **FR-BC02:** Deterministic pre-validation: MIME-type sniffing, SHA-256 cryptographic hashing to eliminate exact duplicates, file size limits (50MB per file).
- **FR-BC03:** Hybrid OCR & Document AI Engine:
  - Document layout parsing (header, line-items table, footer, tax breakup).
  - Zero-shot / Few-shot schema-constrained extraction via LLM abstraction layer (supporting OpenAI, Anthropic, Gemini, or self-hosted models).
- **FR-BC04:** Invoice Entity Extraction:
  - Vendor/Customer Name, Address, GSTIN (validated against regex `^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$`).
  - Invoice Number, Date, Due Date, PO/Reference Number.
  - Line items: Description, HSN/SAC code (4, 6, or 8 digits), Quantity, Unit Price, Taxable Amount, Discount.
  - Tax Breakup: CGST, SGST, IGST, UTGST, Cess.
  - Total Invoice Amount.
- **FR-BC05:** Field-level Confidence Scoring & Deterministic Math Validation:
  - Every extracted field assigned a confidence score ($0.00 - 1.00$).
  - **Inviolable Invariant:** $\text{Taxable Value} + \text{CGST} + \text{SGST} + \text{IGST} + \text{Cess} - \text{Discount} = \text{Total Amount} \pm 0.02$ (rounding tolerance).
  - If math fails or field confidence $< 0.85$, document is flagged for Human Review Queue.
- **FR-BC06:** Bank Statement Parsing Engine:
  - Out-of-the-box parsers for major Indian banks (HDFC, ICICI, SBI, Axis, Kotak, IndusInd, Yes Bank).
  - Extraction of Txn Date, Value Date, Narration/Description, Chq/Ref No, UTR Number, Debit, Credit, Running Balance.
  - Calculation and assertion of Balance Invariant: $\text{Opening Balance} + \sum \text{Credits} - \sum \text{Debits} = \text{Closing Balance}$.

### Module D & E: Reconciliation & Match Intelligence
- **FR-DE01:** Transaction Classification:
  - Rule-based & pattern-based classifier separating: (1) Operating Revenue, (2) Operating Expenses, (3) Contra/Internal Bank Transfers, (4) Capital Injection/Drawings, (5) Statutory Tax Payments (Advance Tax, GST, TDS), (6) Bank Interest & Charges.
- **FR-DE02:** Multi-Paradigm Match Engine:
  - Scenario 1: 1-to-1 exact match (Amount + Ref/UTR + Date window $\pm 30$ days).
  - Scenario 2: 1-to-many match (Single customer lump-sum payment clearing multiple sales invoices).
  - Scenario 3: Many-to-1 match (Single invoice cleared via multiple staggered installments/milestones).
  - Scenario 4: Partial payments with calculated residual balance tracking.
  - Scenario 5: Advance payments (money received before invoice issuance).
  - Scenario 6: TDS Deduction handling (Payment received = Invoice Total - 10% / 2% Sec 194J/194C TDS).
- **FR-DE03:** Explainable Match Scoring:
  - Match candidate card displaying match score breakdown (Amount Match: 40%, UTR/Ref Match: 30%, Entity Name Fuzzy Match: 20%, Date Proximity: 10%).
  - Text explanation (e.g., *"Matched with 98% confidence: UTR matches narration token, net amount equals Invoice #INV-2024-001 minus 10% Section 194J TDS"*).
- **FR-DE04:** Explicit Human Approval Gate:
  - AI NEVER auto-posts a match directly to the General Ledger. High-confidence matches are pre-staged; an authorized accountant or freelancer must trigger approval.

### Module F: Core Double-Entry Accounting Engine
- **FR-F01:** Chart of Accounts (COA) Hierarchy:
  - Standard Indian 5-level COA: Assets, Liabilities, Equity, Income, Expenses.
  - Pre-seeded sub-accounts tailored for Indian businesses (Output CGST/SGST/IGST, Input CGST/SGST/IGST, Electronic Cash Ledger, Electronic Credit Ledger, TDS Receivable, Sundry Debtors, Sundry Creditors).
- **FR-F02:** Immutable Journal Voucher Model:
  - Every entry must balance: $\sum \text{Debits} \equiv \sum \text{Credits}$.
  - Every line item must reference: Account ID, Currency, Amount (Fixed Precision `Numeric(18, 4)`), Source Document Ref, Entity (Customer/Vendor) Ref.
- **FR-F03:** Financial Year & Period Locking:
  - Closed periods cannot accept direct inserts or updates.
  - Corrections must be enacted exclusively through **Reversal Journals** or **Adjustment Vouchers** with full audit cross-reference.
- **FR-F04:** Real-Time Ledger & Financial Reporting:
  - General Ledger and Sub-Ledgers (Sundry Debtors & Creditors ageing).
  - Trial Balance (Opening, Period Movement, Closing).
  - Profit and Loss Statement (Accrual basis).
  - Balance Sheet (Schedule III format principles).
  - Cash Flow Statement (Direct and Indirect methods).

### Module G: Indian GST Intelligence Engine
- **FR-G01:** Tax Determination Engine:
  - Place of Supply (POS) matrix: If Supplier State Code == POS State Code $\rightarrow$ CGST + SGST; If Supplier State Code != POS State Code $\rightarrow$ IGST.
  - Special economic zones (SEZ) and export treatment (LUT zero-rated vs tax-paid refund).
- **FR-G02:** Input Tax Credit (ITC) Rules & Eligibility:
  - Deterministic evaluation under Section 16 & Section 17(5) of CGST Act.
  - Categorization into: Eligible ITC (Inputs, Input Services, Capital Goods), Ineligible ITC (Blocked under 17(5) - e.g., food & beverages, motor vehicles, personal consumption).
- **FR-G03:** Reverse Charge Mechanism (RCM):
  - Auto-flagging of transactions subject to RCM (e.g., GTA services, legal services from advocate, import of services).
  - Auto-generation of dual tax entries: Output RCM Liability and matching Input Tax Credit (subject to eligibility).
- **FR-G04:** GSTR Preparation & Reconciliation Views:
  - GSTR-1 staging summary: Table 4 (B2B), Table 6 (Exports), Table 7 (B2C Large), Table 8 (B2C Small), Table 9 (Credit/Debit Notes), Table 12 (HSN summary).
  - GSTR-3B monthly auto-computation: Table 3.1 (Outward Supplies & RCM), Table 4 (Eligible and Ineligible ITC).
  - GSTR-2B Inward Matching: Reconciliation of uploaded purchase register against GSTR-2B JSON statement with classification into: Matched, Missing in 2B, Missing in Books, Tax Mismatch.

### Module H: Review, Audit & Approval Workflow
- **FR-H01:** Workflow Status State Machine:
  - `UPLOADED` $\rightarrow$ `PROCESSING` $\rightarrow$ `EXTRACTION_FAILED` / `EXTRACTED` $\rightarrow$ `MATCHED` / `UNMATCHED` $\rightarrow$ `REVIEW_PENDING` $\rightarrow$ `APPROVED` $\rightarrow$ `POSTED` $\rightarrow$ `SYNC_PENDING` $\rightarrow$ `SYNCED` / `SYNC_FAILED`.
- **FR-H02:** Complete Immutable Audit Trail:
  - Records: actor UUID, IP address, timestamp, event type (`FIELD_MODIFIED`, `MATCH_ACCEPTED`, `MATCH_OVERRIDDEN`, `VOUCHER_POSTED`, `SYNC_ATTEMPTED`), before/after delta JSON.

### Module I & J: External Integrations & Subscription Monetization
- **FR-IJ01:** TallyPrime Integration:
  - Export format: Tally XML format (Tally Definition Language compliant XML).
  - Master sync: Ledgers, Groups, GST details.
  - Transaction sync: Sales Voucher, Purchase Voucher, Payment Voucher, Receipt Voucher, Journal Voucher.
  - Idempotency key tracking to guarantee zero duplicate vouchers on Tally import.
- **FR-IJ02:** Zoho Books Integration:
  - Secure OAuth2 authorization code flow with automatic refresh token rotation.
  - Bidirectional sync: Chart of Accounts mapping, Contacts (Customers/Vendors), Invoices, Bills, Bank Transactions.
  - Rate-limit aware queueing with exponential backoff.
- **FR-IJ03:** Subscription & Overage Engine:
  - Tiers: Silver (100 docs/mo), Gold (200 docs/mo), Platinum (600 docs/mo).
  - 7-day free trial enforcement with payment mandate authorization pre-check.
  - Monthly document meter incremented only on successfully extracted non-duplicate documents.
  - Hard cap alerts at 80%, 95%, and 100% allowance with overage pay-per-document charging logic.

---

## 4. Non-Functional Requirements (NFR)

| Category | Requirement | Target Metric / Standard |
|---|---|---|
| **Accuracy** | Financial & Math Precision | 100% deterministic decimal arithmetic using `Decimal` / `Numeric(18, 4)`. Zero floating-point rounding drifts. |
| **Throughput** | Document Processing Latency | $\le 12$ seconds for single-page PDF OCR + field extraction via async task queue. |
| **Scalability** | Multi-tenant concurrency | Horizontally scalable stateless API workers; decoupled worker pool for OCR/AI processing. |
| **Reliability** | Job idempotency & retry | Celery tasks with idempotency keys; dead-letter queue (DLQ) for failed jobs with max 3 automated retries. |
| **Security** | Data Encryption | AES-256 for documents at rest; TLS 1.3 in transit; tenant isolation enforced at repository layer. |
| **Auditability** | Record retention & immutability | Write-once append-only audit log; journals cannot be updated via SQL `UPDATE` once `POSTED`. |
| **Availability**| Uptime SLA | 99.9% availability for core API and web interface. |
