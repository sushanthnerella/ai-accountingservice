# Security Architecture & Penetration Audit Report
## AI-Powered Accounting Intelligence SaaS
**Date:** November 9, 2026
**Auditor:** Principal Security Engineer & Architect

---

## 1. Multi-Tenant Isolation Audit
- **Tenant Boundary Enforcement:** Enforced at two layers:
  1. *FastAPI Dependency Layer:* `backend/app/api/deps.py` inspects `X-Organization-Id` and verifies the authenticated user has an active membership in the target organization before proceeding. Returns `403 Forbidden` (`FORBIDDEN_TENANT_ACCESS`) on cross-tenant tampering.
  2. *Database Layer:* Alembic migrations `001_initial_schema.py` and `002_phases_2_to_5.py` define `ROW LEVEL SECURITY` policies checking `organization_id = NULLIF(current_setting('app.current_org_id', true), '')::uuid`.
- **Finding (Medium):** PostgreSQL by default does not apply RLS to superusers or table owners unless `FORCE ROW LEVEL SECURITY` is explicitly declared.
  - *Recommendation:* Add `ALTER TABLE <table_name> FORCE ROW LEVEL SECURITY;` to ensure application connections connecting as the table owner cannot bypass RLS.

## 2. Authentication & Credential Storage
- **Password Hashing:** Uses Argon2id (`memory_cost=65536`, `time_cost=3`, `parallelism=4`) with Bcrypt fallback. Immune to rainbow tables and GPU cracking.
- **JWT Lifecycles:** 15-minute expiration on access tokens. Refresh tokens are stored with hash verification.
- **Finding (Low):** `SECRET_KEY` in `backend/app/core/config.py` defaults to a development secret if not provided in `.env`.
  - *Recommendation:* Require `SECRET_KEY` to be passed as a mandatory environment variable in production environments (`APP_ENV=production`), crashing on startup if missing.

## 3. Cryptographic Storage & Encryption at Rest
- **Storage Service:** Documents are encrypted on disk using AES-256-GCM with a unique 12-byte initialization vector (nonce) prepended to the ciphertext.
- **Tampering Resistance:** AES-GCM guarantees authenticated encryption; any byte manipulation throws an authentication tag validation error.
- **Finding (Low):** Key derivation uses a single static secret key.
  - *Recommendation:* Implement envelope encryption using AWS KMS or HashiCorp Vault for per-tenant data key derivation.

## 4. Audit Trail Immutability
- **Audit Table:** Append-only design (`backend/app/models/audit.py`).
- **Policy:** The application only performs `INSERT` and `SELECT` queries on `audit_events`.
- *Recommendation:* Execute `REVOKE UPDATE, DELETE ON audit_events FROM public;` directly in PostgreSQL to forbid direct database admin modifications.
