## 2026-11-08T17:15:20Z
[Message] timestamp=2026-11-08T17:15:20Z sender=0c690da9-8015-410e-be9e-efc1b993c234 priority=MESSAGE_PRIORITY_HIGH content=You are Explorer 3 for Milestone 1 (Automated Test Strategy & Verification).
Working directory: e:\New folder (8)\.agents\teamwork\m1_explorer_tests
The authoritative user request is: e:\New folder (8)\.agents\teamwork\ORIGINAL_REQUEST.md
You MUST read e:\New folder (8)\.agents\teamwork\ORIGINAL_REQUEST.md before starting work.
Also read:
- e:\New folder (8)\PROJECT.md
- e:\New folder (8)\.agents\teamwork\spec_miner_backend\handoff.md
- e:\New folder (8)\.agents\teamwork\explorer_survey_repo\handoff.md

Your objective:
Investigate and formulate the comprehensive automated test suite strategy for Milestone 1:
1. Test infrastructure: pytest, pytest-asyncio, httpx (AsyncClient), test database configuration using the native PostgreSQL 18 instance (postgresql+asyncpg://postgres:123456@localhost:5432/accounting_test).
2. Test database isolation: transactional rollback fixtures or schema recreation per test run, ensuring tests are deterministic and clean.
3. Mandatory test specifications for Milestone 1:
   - User registration and login (password verification, invalid credentials, duplicate email).
   - JWT token lifecycle and refresh token rotation.
   - Organization creation (Freelancer vs CA Firm) and membership role assignment.
   - Client business creation (PAN and GSTIN regex validation, state code match).
   - Row-Level Security (RLS) enforcement at the database level: explicit test inserting Org A and Org B records, executing queries with Org A context, and verifying Org B records are invisible.
   - Cross-tenant access rejection: attempting to access Org B resources using Org A credentials, verifying HTTP 404/403.
   - CA firm client switching: switching active client business context and verifying access scoping.
   - RBAC permission enforcement: verifying Staff Accountant vs CA Partner permission boundaries.
   - Audit event verification: verifying that registration, org creation, and client creation generate immutable audit records.
   - API error handling: verifying structured error responses for validation and auth errors.
Do NOT write application code yourself.
Write your report to e:\New folder (8)\.agents\teamwork\m1_explorer_tests\handoff.md and message the orchestrator.
