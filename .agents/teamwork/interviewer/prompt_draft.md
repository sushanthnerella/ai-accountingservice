Act as a Principal Software Architect, Senior Full-Stack Engineer, Database Engineer, and QA Lead to implement Phase 1 (Application Foundation and Document Upload vertical slice) of the production-quality AI-Powered Accounting Intelligence Platform, following approved architecture specifications.

Working directory: e:\New folder (8)
Integrity mode: [OPEN: Which of these should the team NOT be allowed to do?]

Reference material:
Approved specifications in repository:
- REQUIREMENTS.md
- PRODUCT_SCOPE.md
- REQUIREMENT_GAP_ANALYSIS.md
- ASSUMPTIONS_AND_DECISIONS.md
- SYSTEM_ARCHITECTURE.md
- DATABASE_DESIGN.md
- API_SPECIFICATION.md
- AI_PIPELINE.md
- SECURITY_ARCHITECTURE.md
- INTEGRATION_ARCHITECTURE.md

## Verification Resources
[OPEN: Do you have existing test suites, sample financial documents, or evaluation guidelines to provide as verification resources?]

## Requirements

### R1. Repository Inspection and Architecture Alignment
Inspect the repository and specifications, resolve critical design issues (tenant isolation, PostgreSQL RLS, RBAC, decimal precision, transaction boundaries, background job idempotency, document storage security, approval permissions, and GST rules), and establish an implementation plan aligned with the approved architecture documents before writing code.

### R2. Multi-Tenant Application Foundation (Backend & Frontend)
Implement the core multi-tenant foundation including FastAPI backend (Python 3.11+, Pydantic V2, SQLAlchemy, Alembic, PostgreSQL, Redis, Celery, user auth, JWT lifecycle, organization and client business management, PostgreSQL RLS tenant isolation, RBAC, append-only audit event logging, and health endpoints) and React frontend (TypeScript, Vite, Tailwind CSS, TanStack Query, Zustand, login/registration, freelancer and CA firm workspaces, organization/client switcher, profile settings, and financial SaaS layout).

### R3. End-to-End Document Upload Vertical Slice
Implement the document upload workflow allowing authenticated users to select an active client business, upload multiple files (PDF, JPG, PNG, CSV, XLS, XLSX) with validation (file signatures, size, MIME type, SHA-256 duplicate detection), store files in private object storage [OPEN: What object storage setup should be used for local development?], persist metadata in PostgreSQL, dispatch idempotent asynchronous processing jobs, return batch and document IDs, display statuses in the UI, and emit audit logs.

### R4. Automated Testing and Verification
Implement an automated test suite verifying authentication, authorization, organization and client business isolation, cross-tenant access rejection, RLS enforcement at the database level, CA firm switching, file type/size validation, duplicate detection, multi-file upload, document metadata persistence, background job creation, and audit logging using realistic test data with multiple tenants.

### R5. Deliverables and Execution Constraints
Deliver working frontend, working backend, database schema and Alembic migrations, Docker-based local development setup, setup README, and PHASE_1_IMPLEMENTATION_REPORT.md. Work strictly within Phase 1 scope without implementing full accounting engines, GST filing, Tally/Zoho sync, or mock AI extraction.

## Acceptance Criteria

### Application Foundation & Security
- [ ] User registration, login, and JWT access/refresh token rotation function securely.
- [ ] Organizations (Freelancer and CA firm types), client businesses, and user memberships are manageable with RBAC.
- [ ] PostgreSQL Row-Level Security (RLS) and tenant context middleware reject cross-tenant data access at the database level.
- [ ] State mutations create immutable, append-only audit log records.
- [ ] Financial calculations and currency fields use exact decimal types rather than floating-point numbers.

### Document Upload Vertical Slice
- [ ] Authenticated users can select an active client business and upload multiple files in a single operation.
- [ ] File validation verifies MIME types, magic bytes/signatures, and size limits for PDF, JPG, PNG, CSV, XLS, and XLSX.
- [ ] Duplicate files within the same business scope are detected via SHA-256 hash calculation.
- [ ] Original files are stored securely in private object storage, and document metadata is saved in PostgreSQL.
- [ ] Asynchronous Celery background processing jobs are dispatched idempotently, returning batch ID and document IDs.
- [ ] Document upload and pending processing statuses are visible in the frontend UI.

### Quality & Deliverables
- [ ] Automated test suite passes for auth, tenant isolation, RLS enforcement, role permissions, file upload validation, and audit events.
- [ ] Docker-based local development setup orchestrates frontend, backend, database, Redis, Celery, and storage.
- [ ] README provides reproducible step-by-step setup and execution instructions.
- [ ] `PHASE_1_IMPLEMENTATION_REPORT.md` details completed features, created files, database tables, API endpoints, test results, limitations, and security gaps.
