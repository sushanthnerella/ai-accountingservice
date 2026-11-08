# Product Scope & Boundary Definition
## AI-Powered Accounting Intelligence Platform

---

## 1. Scope Boundary Philosophy
To deliver a hardened, commercially viable, and mathematically flawless accounting platform, the scope of **Release 1.0** is laser-focused on **high-volume reconciliation, document extraction, double-entry ledgering, GST transaction attribution, and seamless export to Tally and Zoho Books**.

High-complexity tangential domains (such as payroll, physical inventory valuation, fixed asset depreciation schedules, and automated GST portal tax filing) are formally scheduled for subsequent releases.

---

## 2. Release 1.0 (In-Scope — Production Target)

### 2.1 Supported Legal Entities & Tax Profiles
- **Freelancers / Individual Professionals:** Consultants, Software Engineers, Lawyers, Designers (44ADA presumptive taxation awareness).
- **Sole Proprietorships & Partnerships / LLPs:** Small commercial service businesses and trading intermediaries.
- **Tax Regimes:** Regular GST Registered (Monthly / QRMP) & Composition Scheme, Unregistered/Exempt Freelancers.

### 2.2 Core Capabilities
1. **Multi-Tenant Hierarchy & RBAC:**
   - Freelancer single workspace.
   - CA Firm multi-client workspace with switchable client context.
   - Strict organization data isolation.
2. **Document Ingestion Engine:**
   - Formats: PDF (vector & raster), JPG, PNG, CSV, Excel (XLS/XLSX), ZIP archives.
   - Password-protected PDF support.
   - SHA-256 deduplication and validation.
3. **AI Document Extraction:**
   - Invoices (Sales & Purchase) & Expense Receipts.
   - Bank Statements (CSV/Excel parsers + PDF layout parser).
   - Structured JSON output with field confidence & arithmetic verification.
   - Side-by-side human correction & field override interface.
4. **Reconciliation & Matching Engine:**
   - 1-to-1 exact matching.
   - 1-to-many payments (bulk settlement).
   - Many-to-1 payments (staggered installments).
   - Partial payments with residual tracking.
   - TDS-adjusted settlements (Section 194J/194C).
   - Unmatched transaction classification (Contra, Drawings, Bank Charges, Capital).
5. **Double-Entry Accounting Core:**
   - Standard 5-tier Indian Chart of Accounts.
   - Immutable double-entry journal vouchers.
   - Sub-ledgers for Customers (Sundry Debtors) and Vendors (Sundry Creditors).
   - General Ledger, Trial Balance, Profit & Loss (Accrual), Balance Sheet, Cash Flow.
   - Period lock & reversal/adjustment journals.
6. **GST Intelligence & Attribution:**
   - Output GST (B2B, B2C, Exports with/without LUT).
   - Input GST tracking with Section 17(5) blocked credit flags.
   - GSTR-1 preparation staging table.
   - GSTR-3B monthly auto-computation summary.
   - GSTR-2B inward reconciliation match engine (Books vs Portal JSON).
7. **External Integrations:**
   - **TallyPrime:** Tally XML voucher export package & TDL-compatible HTTP push.
   - **Zoho Books:** OAuth2 integration, COA mapping, Contact sync, Bills/Invoices/Payments sync.
8. **Subscription & Metering:**
   - 7-day free trial workflow.
   - Document counting, tier limits (Silver: 100, Gold: 200, Platinum: 600), and overage calculation.

---

## 3. Release 2.0 (Post-Launch Enhancements)
- **Direct GST Portal API Filing:** Direct integration with GST Suvidha Provider (GSP) for automated 1-click filing of GSTR-1 and GSTR-3B with OTP/DSC.
- **E-Invoicing & E-Way Bill Generation:** IRP integration for real-time IRN and QR code generation for entities exceeding statutory turnover thresholds.
- **Multi-Currency Real-Time Exchange Rate Feed:** Automated RBI reference rate pulling for realized foreign exchange gain/loss calculations.
- **Automated Bank Feeds (Account Aggregator):** Integration with Sahamati Account Aggregator (AA) framework for direct statement streaming without manual PDF upload.
- **Client Portal Mobile App:** Flutter/React Native mobile app for freelancers to snap expense receipts on the fly.

---

## 4. Explicitly Out-of-Scope (All Initial Releases)

| Module | Out-of-Scope Reason | Alternative Workaround |
|---|---|---|
| **Full Payroll / HRMS** | High complexity (EPF, ESI, Professional Tax slabs across 28 states, Gratuity, Bonus Acts). | Post net salary payout bank transactions as a single journal entry against "Salaries Payable" or "Salaries Expense". |
| **Inventory Valuation (FIFO / Weighted Average)** | Manufacturing and complex retail inventory require bill-of-materials and physical stock auditing. | Periodic inventory journal adjustment entered by the CA at period end. |
| **Automated Fixed Asset Depreciation Schedules** | Schedule II Companies Act depreciation vs Section 32 Income Tax block of assets requires specialized asset registers. | Manual year-end adjustment voucher supported in the accounting engine. |
| **Automated Statutory Filing Without Review** | Strict regulatory principle: Filing false or unverified returns with the government incurs legal penalties on the taxpayer and CA. | System generates audit-ready, pre-validated summaries; filing is performed deliberately on the GST portal or via GSP. |
