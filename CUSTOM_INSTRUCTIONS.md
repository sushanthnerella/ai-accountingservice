# User Custom Instructions & Engineering Directives
## AI-Powered Accounting Intelligence Platform

---

## 1. Primary User Directives & Role Definition

### Role Specification
- **Assumed Roles:** Principal Software Architect, Senior Full-Stack Engineer, Database Engineer, Accounting Systems Engineer, Security Engineer, QA Lead, and DevOps Engineer.
- **Product Mandate:** Build a production-grade, commercially viable SaaS platform based on the Product Requirements Document (PRD v0.1) for Indian Freelancers and Small CA firms.
- **Foundational Principle:** The platform is an **accounting assistance layer with human-in-the-loop control**, not an uncontrolled auto-pilot bookkeeping tool. AI suggests; deterministic rules validate; qualified accountants approve; the immutable engine posts.

---

## 2. Specific Directives Provided by the User

### Directive 1: Phased Execution & Incremental Delivery
- Do not attempt to implement the entire product in one pass.
- Execute architecture design and gap analysis first before building code.
- Implement Phase 1 (Application Foundation & Document Upload Slice) first before building accounting or GST filing modules.
- Maintain documentation integrity as implementation evolves.

### Directive 2: Custom Implementation vs. Open Source
- **User Clarification (Interview Answer 1):**
  > *"See everything must be custom built, but you can copy open-source code and modify it. It must be properly modified and be a custom-built solution."*
- **Constraint:** All core modules (tenant isolation, accounting engine, match engine, GST engine, bank parser) must be tailored and custom-integrated rather than relying on unvetted black-box third-party monoliths.

### Directive 3: Private Object Storage Architecture
- **User Clarification (Interview Answer 2):**
  > *"Cloud-hosted bucket (e.g. AWS S3) configured via environment variables."*
- **Implementation Strategy:** Implement an abstract `StorageService` interface with support for AWS S3 / Cloudflare R2 / MinIO via standard S3 environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `S3_BUCKET_NAME`, `S3_ENDPOINT_URL`), with a fallback to local encrypted filesystem storage during offline local test runs.

### Directive 4: Test Fixtures & Verification
- **User Clarification (Interview Answer 3):**
  > *"None: the team should generate realistic mock documents and test fixtures from scratch."*
- **Constraint:** Synthetic test fixtures (realistic Indian invoices with GSTINs, HSNs, CGST/SGST/IGST, and Indian bank statements with UTR narrations from HDFC/ICICI/SBI) must be generated programmatically for test suites. Production client data must never be used.

### Directive 5: Strict Invariants & Anti-Patterns
- **No Floating-Point Arithmetic:** Monetary values must strictly use `NUMERIC(18, 4)` in PostgreSQL and `decimal.Decimal` in Python.
- **No Hallucinated Accounting:** AI must never invent invoice fields, silently overwrite closed periods, or automatically treat bank credits as revenue or debits as expenses.
- **No Direct Mutation of Posted Vouchers:** Posted journal entries are immutable. Any error correction must be performed via traceable reversal or adjustment vouchers.
- **Tenant Isolation:** A user from one organization or client must never see or manipulate data belonging to another. PostgreSQL Row-Level Security (RLS) must enforce this at the database layer.

---

## 3. GitHub Remote Repository Directive
- **Target Repository:** `https://github.com/sushanthnerella/ai-accountingservice.git`
- **Action:** Commit all architecture documentation, status reports, custom instructions, and test step guides, and push the entire codebase to the remote Git repository.
