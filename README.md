# AI-Powered Accounting Intelligence Platform
> High-precision, accountant-in-the-loop intelligence, document extraction, reconciliation, and GST ledgering platform for Indian Freelancers and Small CA firms.

---

## 1. Project Overview & Philosophy
The platform acts as an **intelligent accounting assistance layer** positioned upstream from final accounting masters (TallyPrime, Zoho Books). Its mission is to automate ingestion, OCR/extraction, bank statement parsing, multi-way reconciliation, and GST-attributed journal staging while strictly preserving:
- **Double-Entry Invariants:** Every posted entry balances ($\sum \text{Debits} \equiv \sum \text{Credits}$).
- **Mathematical Precision:** Zero floating-point rounding drifts via `NUMERIC(18, 4)` and Python `decimal.Decimal`.
- **Statutory Auditability:** Append-only immutable journal ledgers and audit trails.
- **Accountant-Controlled Gates:** AI never auto-posts unverified entries. Qualified professionals approve; the immutable engine posts.

---

## 2. Documentation Index

| Document | Purpose & Scope |
|---|---|
| [CURRENT_STAGE_AND_STATUS.md](file:///e:/New%20folder%20(8)/CURRENT_STAGE_AND_STATUS.md) | **Current Project Stage**: Completed deliverables, halted subagents, and next milestone |
| [CUSTOM_INSTRUCTIONS.md](file:///e:/New%20folder%20(8)/CUSTOM_INSTRUCTIONS.md) | **User Custom Directives**: Architectural invariants, interview answers, and storage choices |
| [TESTING_STEPS.md](file:///e:/New%20folder%20(8)/TESTING_STEPS.md) | **Testing & Verification Guide**: Step-by-step test procedures, RLS tests, invariant validation |
| [REQUIREMENTS.md](file:///e:/New%20folder%20(8)/REQUIREMENTS.md) | **Software Requirements Specification**: Functional & non-functional requirements |
| [REQUIREMENT_GAP_ANALYSIS.md](file:///e:/New%20folder%20(8)/REQUIREMENT_GAP_ANALYSIS.md) | **Indian Statutory Gap Analysis**: TDS Sec 194J/C, GST Sec 17(5) blocked ITC, FIRC/e-BRC |
| [PRODUCT_SCOPE.md](file:///e:/New%20folder%20(8)/PRODUCT_SCOPE.md) | **Product Scope Boundaries**: Release 1.0 (MVP) vs. Release 2.0 vs. Out-of-Scope items |
| [ASSUMPTIONS_AND_DECISIONS.md](file:///e:/New%20folder%20(8)/ASSUMPTIONS_AND_DECISIONS.md) | **Architectural Decision Records (ADRs)**: Numeric precision, RLS, LLM abstraction |
| [SYSTEM_ARCHITECTURE.md](file:///e:/New%20folder%20(8)/SYSTEM_ARCHITECTURE.md) | **System Architecture**: Hexagonal modular architecture, component flowcharts |
| [DATABASE_DESIGN.md](file:///e:/New%20folder%20(8)/DATABASE_DESIGN.md) | **Relational Database Design**: Complete PostgreSQL 16 schema, tables, triggers, indexes |
| [API_SPECIFICATION.md](file:///e:/New%20folder%20(8)/API_SPECIFICATION.md) | **RESTful API Specification**: OpenAPI 3.1 endpoints, multi-tenant headers, payload schemas |
| [AI_PIPELINE.md](file:///e:/New%20folder%20(8)/AI_PIPELINE.md) | **Document AI Pipeline**: Provider-agnostic LLM extraction, deterministic math checks |
| [SECURITY_ARCHITECTURE.md](file:///e:/New%20folder%20(8)/SECURITY_ARCHITECTURE.md) | **Security Architecture**: PostgreSQL Row-Level Security (RLS), RBAC matrix, audit log |
| [INTEGRATION_ARCHITECTURE.md](file:///e:/New%20folder%20(8)/INTEGRATION_ARCHITECTURE.md) | **Integration Architecture**: TallyPrime TDL XML export, Zoho Books OAuth2, bank parsers |
| [PROJECT.md](file:///e:/New%20folder%20(8)/PROJECT.md) | **Implementation Blueprint**: Target directory structure and feature inventory |

---

## 3. Technology Stack

- **Backend:** Python 3.11+, FastAPI (async), Pydantic V2, SQLAlchemy 2.0 (asyncpg), Alembic.
- **Database:** PostgreSQL 16 with Row-Level Security (RLS) policies and balance-check triggers.
- **Task Queue & Broker:** Celery + Redis 7+ with dedicated worker queues.
- **Object Storage:** Pluggable `StorageService` (AWS S3 / MinIO / Local Encrypted Storage).
- **Frontend:** React 18, TypeScript 5, Vite, Tailwind CSS, TanStack Query, Zustand.
- **Integrations:** TallyPrime (TDL XML export package), Zoho Books (`books.zoho.in` OAuth2 REST API).

---

## 4. Current Status & Handoff State
All architecture specifications, database schemas, API contracts, gap analyses, and implementation blueprints have been finalized. The background subagent processes have been stopped per user request, and the entire repository state is committed and pushed to GitHub at:
`https://github.com/sushanthnerella/ai-accountingservice.git`
