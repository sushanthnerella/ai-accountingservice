# Dispatch Log

## 2026-11-08T17:05:03Z

Sender: 806cbd1c-4ced-445c-8d19-ba2d06b89390
Priority: MESSAGE_PRIORITY_HIGH

# IMPLEMENTATION DIRECTIVE: PHASE 1
## AI-Powered Accounting Intelligence Platform

You are now moving from architecture design into implementation.

Act as a Principal Software Architect, Senior Full-Stack Engineer, Database Engineer, and QA Lead.

The following documents are the approved project specifications. Read and follow them:

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

The objective is to build a production-quality application incrementally. Do not attempt to implement the entire product in one pass.

## 1. First: Inspect the Existing Repository

Before writing code:

1. Inspect the complete existing repository.
2. Identify existing frontend, backend, database, configurations, dependencies and infrastructure.
3. Identify reusable code and existing functionality.
4. Do not overwrite or delete existing working code without justification.
5. Identify conflicts between the architecture documents and the actual repository.
6. Create an implementation plan based on the actual repository.

If a critical requirement is ambiguous, document it rather than inventing a business or accounting rule.

## 2. Resolve Critical Design Issues

Before implementation, verify:

- Tenant isolation and PostgreSQL RLS behavior.
- Authentication, JWT lifecycle, refresh tokens and RBAC.
- Organization versus client-business ownership.
- Database foreign keys, deletion policies and audit retention.
- Decimal precision and financial serialization.
- Database transaction boundaries.
- Background job idempotency and retry behavior.
- Document storage security.
- Accountant approval and journal-posting permissions.

Pay particular attention to accounting and GST rules. Do not treat simple state-code comparison as a complete GST tax determination. Support explicit tax treatment and human review where classification is uncertain.

Do not assume that every technical claim in the architecture documents is already verified. Validate external integration capabilities before implementing them.

## 3. Implement Phase 1: Application Foundation

### Backend
Use the approved architecture:

- Python 3.11+
- FastAPI
- Pydantic V2
- PostgreSQL
- SQLAlchemy
- Alembic
- Redis
- Celery

Implement:

1. Application configuration and environment management.
2. Database connection and migrations.
3. User registration and login.
4. Secure password hashing.
5. JWT access and refresh token handling.
6. Organization creation.
7. Freelancer and CA firm organization types.
8. Client business creation and management.
9. Organization membership.
10. Role-based permissions.
11. PostgreSQL Row-Level Security.
12. Tenant-context middleware/dependencies.
13. Append-only audit event infrastructure.
14. Standard API response and error handling.
15. Health-check and readiness endpoints.

### Frontend

Use:

- React
- TypeScript
- Vite
- Tailwind CSS
- TanStack Query
- Zustand

Implement:

1. Professional login and registration pages.
2. Application layout and navigation.
3. Freelancer workspace.
4. CA firm workspace.
5. Organization and client-business switcher.
6. Client business creation screen.
7. User profile and settings.
8. Role-aware navigation.
9. Loading, empty, success and error states.

The interface should look like a serious financial SaaS product, not a generic admin template.

## 4. First End-to-End Vertical Slice: Document Upload

Once the foundation works, implement the first document workflow:

1. Allow authenticated users to select the active client business.
2. Support uploading multiple files in one operation.
3. Support PDF, JPG, PNG, CSV, XLS and XLSX.
4. Validate file signatures, size and MIME type.
5. Calculate SHA-256 hashes.
6. Detect duplicate files within the appropriate business scope.
7. Store original documents in private object storage.
8. Save document metadata in PostgreSQL.
9. Create an asynchronous processing job.
10. Return a batch ID and individual document IDs.
11. Display upload and processing statuses in the frontend.
12. Record upload and processing events in the audit log.

For this first phase, extraction can remain a clearly defined pending-processing stage. Do not pretend OCR or accounting extraction is complete.

## 5. Testing Requirements

Write automated tests alongside the implementation.

Mandatory tests:

- Authentication and authorization.
- Organization isolation.
- Cross-tenant access rejection.
- CA firm client switching.
- Role permission enforcement.
- RLS enforcement at database level.
- File type and size validation.
- Duplicate detection.
- Multi-file upload.
- Document metadata persistence.
- Background job creation.
- Audit event creation.
- API error handling.

Use realistic test data, including multiple organizations and multiple client businesses.

Do not use production financial data.

## 6. Engineering Standards

- Follow clean architecture and modular service boundaries.
- Keep business logic out of API route handlers.
- Use migrations for every database schema change.
- Never use floating-point types for financial amounts.
- Do not hardcode secrets, credentials or API keys.
- Use environment variables.
- Add structured logging.
- Add type hints and meaningful documentation.
- Implement proper error handling.
- Make background tasks idempotent.
- Do not leave placeholder implementations disguised as completed features.

## 7. Deliverables

At the end of Phase 1, provide:

1. Working frontend.
2. Working backend.
3. Database schema and migrations.
4. Authentication and tenant isolation.
5. Organization and client management.
6. Multi-file document upload.
7. Background processing status.
8. Audit event infrastructure.
9. Automated test suite.
10. Docker-based local development setup.
11. README with exact setup and execution instructions.
12. PHASE_1_IMPLEMENTATION_REPORT.md.

The implementation report must contain:

- Features completed.
- Files created or modified.
- Database tables created.
- API endpoints implemented.
- Tests executed and actual results.
- Known limitations.
- Security gaps.
- Outstanding issues.
- Recommended Phase 2 tasks.

## 8. Strict Execution Rules

- Work only on Phase 1.
- Do not start implementing the complete accounting engine yet.
- Do not implement GST filing yet.
- Do not implement Tally or Zoho synchronization yet.
- Do not build fake AI extraction functionality.
- Do not claim a feature works unless it has been implemented and tested.
- Do not skip tests to save time.
- Do not silently change approved architecture decisions.

First inspect the repository and produce a short execution plan with identified blockers. Then proceed with Phase 1 implementation.

Work incrementally. Run tests after each meaningful module. Fix failures before moving forward.

**Definition of done:** A user can register, log in, create an organization, create or switch a client business, upload multiple financial documents, see their processing status, and have every important action recorded in the audit trail. Tenant isolation must be verified by automated tests.
