## 2026-11-08T17:15:07Z
From: 0c690da9-8015-410e-be9e-efc1b993c234
Priority: MESSAGE_PRIORITY_HIGH

You are Explorer 2 for Milestone 1 (PostgreSQL RLS, Database Migrations, Auth & Tenancy).
Working directory: e:\New folder (8)\.agents\teamwork\m1_explorer_rls_auth
The authoritative user request is: e:\New folder (8)\.agents\teamwork\ORIGINAL_REQUEST.md
You MUST read e:\New folder (8)\.agents\teamwork\ORIGINAL_REQUEST.md before starting work.
Also read:
- e:\New folder (8)\PROJECT.md
- e:\New folder (8)\.agents\teamwork\spec_miner_backend\handoff.md

Your objective:
Investigate and design the exact specifications for:
1. SQLAlchemy 2.0 ORM models for Milestone 1: users, organizations, memberships, client_businesses, refresh_tokens, document_batches, documents, audit_events. Ensure NUMERIC(18, 4) and Decimal are strictly enforced for all financial values (zero floats).
2. Alembic migration scripts: DDL definitions, primary keys (UUID v4), foreign keys with strict cascade/restrict rules, and indexes.
3. PostgreSQL Row-Level Security (RLS) policies: exact SQL statements to enable RLS and create isolation policies on tenant tables, using SET LOCAL app.current_org_id and SET LOCAL app.current_client_id. Define SQLAlchemy connection pool event listeners (checkout and checkin) to ensure RESET ALL is executed on connection return.
4. Auth & RBAC service design: Argon2id/Bcrypt password hashing, 15-minute JWT access tokens (payload: sub, org_id, client_id, roles, permissions), rotating refresh tokens, Redis revocation, and RBAC permission dependency (require_permission).
5. Append-only audit logging: event structure, immutability (REVOKE UPDATE, DELETE), and audit event helper.
Do NOT write application code yourself.
Write your report to e:\New folder (8)\.agents\teamwork\m1_explorer_rls_auth\handoff.md and message the orchestrator.
