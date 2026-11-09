# Bugs, Defects & Remediation Log
## AI-Powered Accounting Intelligence SaaS
**Date:** November 9, 2026

---

### Bug 001: Missing Database Migrations for Phase 2–5 Operational Tables
- **Severity:** High (Fixed)
- **Affected File:** `backend/alembic/versions/002_phases_2_to_5.py`
- **Evidence:** Alembic version 001 only declared Phase 1 foundation tables. Initial PostgreSQL deployment would fail when accessing invoices or banking.
- **Correction Applied:** Created `002_phases_2_to_5.py` covering all tables (`invoices`, `invoice_items`, `bank_accounts`, `bank_transactions`, `chart_of_accounts`, `journal_entries`, `journal_lines`, `reconciliation_matches`) with foreign keys, indexes, and RLS policies.

### Bug 002: Dockerfile Context & PYTHONPATH Mismatch
- **Severity:** High (Fixed)
- **Affected File:** `docker-compose.yml` & `backend/Dockerfile`
- **Evidence:** Building from `./backend` with container working dir `/app` caused `ModuleNotFoundError: No module named 'backend'` when running `uvicorn backend.app.main:app`.
- **Correction Applied:** Updated `docker-compose.yml` to build from root context (`context: .`, `dockerfile: backend/Dockerfile`) and added `ENV PYTHONPATH=/app`.

### Bug 003: Rejection Event Logging in Reconciliation Service
- **Severity:** Low (Fixed)
- **Affected File:** `backend/app/services/reconciliation_service.py`
- **Evidence:** Rejection action previously recorded `event_type=AuditEventType.MATCH_ACCEPTED`.
- **Correction Applied:** Updated logic to capture rejection event distinctly with `rejection_reason`.

### Bug 004: Live OCR Provider Gateway Dependency
- **Severity:** Medium (Documented)
- **Affected File:** `backend/app/services/extraction_service.py`
- **Evidence:** Invariant verification and staging logic are fully functional, but direct multi-modal vision extraction requires production API keys (`GEMINI_API_KEY` or `OPENAI_API_KEY`).
- **Correction:** Documented as post-foundation production configuration.
