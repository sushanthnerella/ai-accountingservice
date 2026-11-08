# Orchestrator Plan: Phase 1 Implementation

## Phase 0: Survey & Repository Inspection
- Step 1: Dispatch 3 parallel survey subagents:
  1. `teamwork_explorer` -> Inspect existing codebase, files, configs, scripts, tools in workspace root.
  2. `teamwork_spec_miner` -> Mine Backend, DB, RLS, Auth, Audit, and Storage specifications from approved docs.
  3. `teamwork_spec_miner` -> Mine Frontend, Workspaces, UI states, Navigation, and Client-switching specifications from approved docs.
- Step 2: Aggregate survey reports into `PROJECT.md` Feature Inventory & Architecture.
- Step 3: Verify all Phase 1 requirements from `ORIGINAL_REQUEST.md` are accounted for in milestones.

## Phase 1: Dual Track Dispatch
- Track A: E2E Testing Orchestrator
  - Scope: Test harness, test runners, Tier 1-4 opaque-box tests according to requirements.
  - Deliverable: `TEST_INFRA.md` and `TEST_READY.md`.
- Track B: Implementation Track Sub-Orchestrators
  - Milestone 1: Backend Foundation (FastAPI, Alembic, PostgreSQL, RLS policies, Auth/JWT/RBAC, Audit logging, Health endpoints).
  - Milestone 2: Frontend Foundation (React, Vite, Tailwind, TanStack Query, Zustand, Auth pages, Workspaces for Freelancer & CA firm, Org/Client switcher).
  - Milestone 3: End-to-End Vertical Slice (Multi-file document upload, SHA-256 hash, duplicate check, metadata storage, Celery job creation, status polling UI).
  - Milestone 4: Docker & Infrastructure Configuration (Docker Compose for Postgres, Redis, Celery, Backend, Frontend; README and setup scripts).
  - Milestone 5: E2E Test Suite Execution & Hardening (Phase 1: 100% pass of Tiers 1-4; Phase 2: Adversarial coverage hardening Tier 5).

## Phase 2: Final Audit & Deliverable Generation
- Forensic Audit verification.
- Generation of `PHASE_1_IMPLEMENTATION_REPORT.md`.
- Handover to Sentinel.
