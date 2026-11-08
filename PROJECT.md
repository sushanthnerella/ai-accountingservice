# Project: AI-Powered Accounting Intelligence Platform (Phase 1)

## Architecture
- **System Pattern**: Hexagonal / Clean Modular Architecture.
- **Backend Core**: Python 3.12 (via `uv`), FastAPI (asynchronous I/O, OpenAPI 3.1), Pydantic V2 (strict typing, Decimal serialization), SQLAlchemy 2.0 (asyncpg), Alembic migrations, Redis (broker & cache), Celery (task queue with Windows `--pool=solo` & eager test mode).
- **Storage Subsystem**: Pluggable `StorageService` with `LocalStorageService` (AES-256 local encrypted storage for host dev) and `S3StorageService` (AWS S3 / MinIO).
- **Frontend Core**: React 18, TypeScript 5, Vite, Tailwind CSS 3.4 (high-density financial styling, tabular numerals, dark/light themes), TanStack Query v5, Zustand state management, React Hook Form + Zod.
- **Tenancy & Security Boundary**: PostgreSQL Row-Level Security (RLS) driven by transaction-scoped session parameters (`app.current_org_id`, `app.current_client_id`) with connection pool session cleanup (`RESET ALL`).
- **Audit Subsystem**: Append-only immutable `audit_events` table (`REVOKE UPDATE, DELETE`).

## Code Layout
```
e:\New folder (8)\
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── deps.py               # Auth, DB, and tenant context dependencies
│   │   │   └── v1/
│   │   │       ├── router.py         # Main API router (/api/v1)
│   │   │       ├── auth.py           # Login, register, refresh, logout
│   │   │       ├── organizations.py  # Org creation & management
│   │   │       ├── clients.py        # Client business CRUD & switching
│   │   │       ├── documents.py      # Upload, batch status, metadata
│   │   │       └── audit.py          # Audit event log retrieval
│   │   ├── core/
│   │   │   ├── config.py             # Pydantic-settings configuration
│   │   │   ├── security.py           # Argon2id/Bcrypt, JWT Ed25519/HS256 tokens
│   │   │   ├── rls.py                # Tenant context session setter & pool listeners
│   │   │   └── logging.py            # Structured logging
│   │   ├── db/
│   │   │   ├── session.py            # AsyncSession engine & sessionmaker
│   │   │   └── base.py               # DeclarativeBase with common timestamp/UUID mixins
│   │   ├── models/                   # SQLAlchemy 2.0 ORM models
│   │   │   ├── user.py               # User and RefreshToken models
│   │   │   ├── organization.py       # Organization and Membership models
│   │   │   ├── client_business.py    # ClientBusiness model
│   │   │   ├── document.py           # DocumentBatch and Document models
│   │   │   └── audit.py              # AuditEvent model
│   │   ├── schemas/                  # Pydantic V2 schemas (strict, Decimal)
│   │   │   ├── auth.py
│   │   │   ├── organization.py
│   │   │   ├── client_business.py
│   │   │   ├── document.py
│   │   │   ├── audit.py
│   │   │   └── common.py             # Error envelope & pagination
│   │   ├── services/                 # Domain business logic (no DB logic in route handlers)
│   │   │   ├── auth_service.py
│   │   │   ├── organization_service.py
│   │   │   ├── client_service.py
│   │   │   ├── document_service.py
│   │   │   ├── storage_service.py    # LocalStorageService & S3StorageService
│   │   │   └── audit_service.py
│   │   └── tasks/                    # Celery background tasks
│   │       ├── celery_app.py
│   │       └── document_tasks.py     # Ingestion & hashing tasks (pending extraction)
│   ├── alembic/                      # Database migrations
│   │   ├── env.py
│   │   └── versions/                 # Version migration scripts
│   ├── tests/                        # Automated backend tests (pytest)
│   │   ├── conftest.py               # Test DB fixtures, client fixtures, auth helpers
│   │   ├── test_auth.py
│   │   ├── test_tenancy_rls.py       # RLS isolation & cross-tenant rejection tests
│   │   ├── test_client_business.py
│   │   ├── test_document_upload.py   # Magic bytes, SHA-256, duplicates, Celery
│   │   └── test_audit_log.py
│   ├── pyproject.toml / requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/                      # API client, interceptors, endpoints
│   │   ├── components/               # UI components (common, shell, upload, audit)
│   │   ├── pages/                    # Auth, Workspaces, Documents, Audit, Settings
│   │   ├── stores/                   # Zustand stores (auth, UI)
│   │   ├── types/                    # TypeScript interfaces & types
│   │   └── utils/                    # Crypto, formatting, validation
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   └── Dockerfile
├── e2e_tests/                        # Independent Opaque-Box E2E Test Suite
│   ├── runner.py                     # E2E test runner
│   ├── tier1_feature/
│   ├── tier2_boundary/
│   ├── tier3_combination/
│   └── tier4_workload/
├── docker-compose.yml
└── README.md
```

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Application Configuration & Logging | Structured logging, environment management, health/readiness endpoints | M1 | `ORIGINAL_REQUEST.md:74, 88`, Survey |
| 2 | PostgreSQL Connection & Migrations | Async SQLAlchemy 2.0, Alembic migrations for all Phase 1 tables | M1 | `ORIGINAL_REQUEST.md:75`, `DATABASE_DESIGN.md` |
| 3 | User Registration & Password Hashing | Argon2id/Bcrypt secure password hashing, user registration API | M1 | `ORIGINAL_REQUEST.md:76-77`, `SECURITY_ARCHITECTURE.md` |
| 4 | JWT Access & Refresh Token Lifecycle | 15-minute access JWT, rotating refresh cookies, Redis revocation | M1 | `ORIGINAL_REQUEST.md:78`, `SECURITY_ARCHITECTURE.md` |
| 5 | Organization Creation & Typing | Freelancer, CA Firm, Enterprise Practice org models | M1 | `ORIGINAL_REQUEST.md:79-80`, `DATABASE_DESIGN.md` |
| 6 | Organization Membership & RBAC | 5 RBAC roles (Freelancer Owner, CA Partner, CA Staff, Auditor, Client Viewer) | M1 | `ORIGINAL_REQUEST.md:82-83`, `SECURITY_ARCHITECTURE.md` |
| 7 | Client Business Creation & Management | Legal entity with PAN & GSTIN regex, state code, composition flag | M1 | `ORIGINAL_REQUEST.md:81`, `DATABASE_DESIGN.md` |
| 8 | PostgreSQL Row-Level Security (RLS) | `SET LOCAL app.current_org_id` and pool session cleanup (`RESET ALL`) | M1 | `ORIGINAL_REQUEST.md:84-85`, `SECURITY_ARCHITECTURE.md` |
| 9 | Append-Only Audit Event Subsystem | Immutable `audit_events` table (`REVOKE UPDATE, DELETE`), event logging service | M1 | `ORIGINAL_REQUEST.md:86`, `SECURITY_ARCHITECTURE.md` |
| 10 | Standard API Response Envelope | Uniform error formatting with `error_code`, `message`, `request_id` | M1 | `ORIGINAL_REQUEST.md:87`, `API_SPECIFICATION.md` |
| 11 | Financial Precision Enforcer | `NUMERIC(18, 4)` and `Decimal` everywhere; zero floats | M1 | `ADR-01`, `ORIGINAL_REQUEST.md:163` |
| 12 | Frontend Scaffold & Tooling | React 18, Vite, TypeScript 5, Tailwind CSS, TanStack Query v5, Zustand | M2 | `ORIGINAL_REQUEST.md:93-100`, Survey |
| 13 | Professional Financial SaaS Styling | High-density tables, tabular numbers, slate/indigo tokens, dark/light theme | M2 | `ORIGINAL_REQUEST.md:113`, Survey |
| 14 | Login & Registration Pages | Clean auth UI for Freelancers and CA Firms with validation | M2 | `ORIGINAL_REQUEST.md:103`, `API_SPECIFICATION.md` |
| 15 | Application Shell Layout | Collapsible sidebar, header, breadcrumbs, user menu | M2 | `ORIGINAL_REQUEST.md:104`, `SYSTEM_ARCHITECTURE.md` |
| 16 | Organization & Client Switcher | Active context switching dropdown for CA firms; static pill for freelancers | M2 | `ORIGINAL_REQUEST.md:107`, Survey |
| 17 | Freelancer Workspace | Focused single-tenant dashboard with direct upload & metrics | M2 | `ORIGINAL_REQUEST.md:105`, `SYSTEM_ARCHITECTURE.md` |
| 18 | CA Firm Workspace | Multi-client portfolio table, search/filter by PAN/GSTIN, status indicators | M2 | `ORIGINAL_REQUEST.md:106`, `REQUIREMENTS.md` |
| 19 | Client Onboarding Modal | Modal form with real-time PAN (`^[A-Z]{5}[0-9]{4}[A-Z]{1}$`) & GSTIN validation | M2 | `ORIGINAL_REQUEST.md:108`, `DATABASE_DESIGN.md` |
| 20 | Role-Aware Navigation | UI element gating and route protection based on user RBAC permissions | M2 | `ORIGINAL_REQUEST.md:110`, `SECURITY_ARCHITECTURE.md` |
| 21 | State Management & Interceptors | Zustand auth store, auto-injection of `X-Organization-Id` & `X-Client-Business-Id`, 401 refresh | M2 | `API_SPECIFICATION.md`, Survey |
| 22 | Multi-File Drag & Drop Upload | Drag-and-drop dropzone supporting bulk file selection (PDF, JPG, PNG, CSV, XLS, XLSX) | M3 | `ORIGINAL_REQUEST.md:120-121`, `API_SPECIFICATION.md` |
| 23 | File Binary Signature Validation | Binary magic byte verification (PDF `%PDF-`, PNG, JPG, ZIP/XLSX `PK\x03\x04`) | M3 | `ORIGINAL_REQUEST.md:122`, `SECURITY_ARCHITECTURE.md` |
| 24 | Cryptographic SHA-256 Hashing | Raw byte hashing on client and server | M3 | `ORIGINAL_REQUEST.md:123`, `DATABASE_DESIGN.md` |
| 25 | Client-Scoped Duplicate Detection | Deduplication scoped to `(organization_id, client_business_id, sha256_hash)` | M3 | `ORIGINAL_REQUEST.md:124`, `DATABASE_DESIGN.md` |
| 26 | Encrypted Storage Service | AES-256 private storage: `LocalStorageService` (local dev) & `S3StorageService` | M3 | `ORIGINAL_REQUEST.md:125`, `SYSTEM_ARCHITECTURE.md` |
| 27 | Document & Batch Metadata Persistence | `document_batches` and `documents` tables with status lifecycle | M3 | `ORIGINAL_REQUEST.md:126, 128`, Survey |
| 28 | Asynchronous Celery Ingestion Job | Background job creation, status `PROCESSING` (no fake OCR extraction) | M3 | `ORIGINAL_REQUEST.md:127, 132`, Survey |
| 29 | Upload & Processing Status Polling | TanStack Query 2s polling hook, status badges, duplicate warning alert | M3 | `ORIGINAL_REQUEST.md:129`, `API_SPECIFICATION.md` |
| 30 | Audit Trail Event Logging for Upload | Record upload, hash, duplicate, and processing events in audit log | M3 | `ORIGINAL_REQUEST.md:130`, `SECURITY_ARCHITECTURE.md` |
| 31 | In-Memory Password-Protected PDF Support | Transient in-memory password entry for protected statements (never saved) | M3 | `REQUIREMENT_GAP_ANALYSIS.md`, Survey |
| 32 | Audit Log Viewer UI | Audit trail page rendering immutable events with actor, IP, timestamp | M3 | `ORIGINAL_REQUEST.md:130`, Survey |
| 33 | Docker Compose Configuration | Multi-container compose for Postgres, Redis, Celery, API, and Frontend | M4 | `ORIGINAL_REQUEST.md:185`, Survey |
| 34 | Production Dockerfiles | Multi-stage Dockerfiles for Backend (Python 3.12) and Frontend (Nginx/Vite) | M4 | `ORIGINAL_REQUEST.md:185`, Survey |
| 35 | Database Seed & Init Scripts | Realistic test data (multiple orgs, CA firm with clients, Freelancer) | M4 | `ORIGINAL_REQUEST.md:154`, Survey |
| 36 | Documentation & README Execution Guide | Clear setup for native Windows development AND Docker development | M4 | `ORIGINAL_REQUEST.md:186`, Survey |
| 37 | E2E Test Suite (Tiers 1-4) | Opaque-box requirement-driven tests verifying full user journey | M5 / Test Track | `ORIGINAL_REQUEST.md:136-155` |
| 38 | Adversarial Coverage Hardening (Tier 5) | White-box edge-case and penetration verification by Challenger | M5 | Project Pattern Tier 5 |
| 39 | Forensic Integrity Verification | Binary veto check by `teamwork_auditor` (zero tolerance for faking/cheating) | M5 | System Instructions |
| 40 | Phase 1 Implementation Report | `PHASE_1_IMPLEMENTATION_REPORT.md` documenting deliverables & metrics | M5 | `ORIGINAL_REQUEST.md:187-199` |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| E2E | E2E Testing Track | Independent opaque-box test runner & Tiers 1-4 test suite derived from requirements | none | IN_PROGRESS |
| 1 | Backend Foundation & Multi-Tenant Infrastructure | FastAPI, Alembic, PostgreSQL RLS, Auth/JWT/RBAC, Audit log, Health probes | none | IN_PROGRESS |
| 2 | Frontend Foundation & Financial Workspaces | React/Vite/Tailwind, Auth pages, Workspaces (Freelancer & CA), Switcher, Zustand store | M1 (interfaces) | IN_PROGRESS |
| 3 | Vertical Slice: Multi-File Ingestion & Status Lifecycle | File validation, SHA-256 duplicate detection, AES-256 storage, Celery job, UI upload & polling | M1, M2 | PLANNED |
| 4 | DevOps, Containerization & Local Dev Setup | Dockerfile, docker-compose.yml, db seed scripts, comprehensive README | M1, M2, M3 | PLANNED |
| 5 | Integration Verification, Adversarial Hardening & Final Report | Pass 100% E2E tests, Tier 5 hardening, Forensic Audit, PHASE_1_IMPLEMENTATION_REPORT.md | E2E, M1-M4 | PLANNED |

## Interface Contracts

### Backend ↔ Frontend API Contract
- Base URL: `/api/v1`
- Content-Type: `application/json` (except multi-file upload: `multipart/form-data`)
- Authentication: `Authorization: Bearer <access_token>`
- Tenancy Headers:
  - `X-Organization-Id: <UUID>`
  - `X-Client-Business-Id: <UUID>`
- Standard Error Envelope:
  ```json
  {
    "success": false,
    "error_code": "STRING_ENUM",
    "message": "Human readable explanation",
    "details": {},
    "request_id": "req_uuid"
  }
  ```
- Upload Endpoint:
  - `POST /api/v1/documents/upload`
  - Body (form-data): `files` (File[]), `category` (string, default "AUTO_DETECT"), `pdf_password` (optional string)
  - Response (202 Accepted):
    ```json
    {
      "success": true,
      "batch_id": "bch_01HP389AB01",
      "uploaded_files": [
        {
          "document_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
          "file_name": "sample.pdf",
          "sha256_hash": "e3b0c442...",
          "status": "PROCESSING",
          "is_duplicate": false
        }
      ]
    }
    ```
- Document Status Endpoint:
  - `GET /api/v1/documents/{document_id}`
  - Response (200 OK): Document details, processing status, extracted metadata, confidence.

### Backend ↔ Database RLS Contract
- Session parameters:
  - `SET LOCAL app.current_org_id = '<UUID>'`
  - `SET LOCAL app.current_client_id = '<UUID>'`
- Enforced on all queries within database transaction.
- Connection pool check-in listener executes `RESET ALL` to prevent session variable leakage across requests.
