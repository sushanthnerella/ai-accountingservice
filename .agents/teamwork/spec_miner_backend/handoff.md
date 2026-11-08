# Specification Extraction Report: Phase 1 Backend Architecture
**Author:** Backend Specification Miner  
**Date:** 2026-11-08  
**Scope:** Phase 1 Application Foundation & Document Upload Vertical Slice  
**Target Repository:** `e:\New folder (8)`  

---

## 1. Observation

A systematic inspection of `ORIGINAL_REQUEST.md` and the 10 architecture and specification documents located in `e:\New folder (8)` revealed the authoritative specifications for Phase 1. Below are the verbatim observations, file paths, and line references.

### 1.1 Backend Stack & Core Technology Choices
* **Python Runtime:** Python 3.11+ is mandated across all services.
  * *Source:* `ORIGINAL_REQUEST.md:63`: `- Python 3.11+`
  * *Source:* `SYSTEM_ARCHITECTURE.md:21`: `Application Core Services (Python 3.11+)`
* **API Framework:** FastAPI with asynchronous event handling and OpenAPI 3.1 generation.
  * *Source:* `ORIGINAL_REQUEST.md:64`: `- FastAPI`
  * *Source:* `SYSTEM_ARCHITECTURE.md:70-74`: `FastAPI Backend Application ... Async Asynchronous I/O ... Dependency Injection`
  * *Source:* `API_SPECIFICATION.md:1`: `# OpenAPI 3.1 & REST API Specification`
* **Validation & Serialization:** Pydantic V2 with strict type validation, regex constraints, and decimal serialization.
  * *Source:* `ORIGINAL_REQUEST.md:65`: `- Pydantic V2`
  * *Source:* `SYSTEM_ARCHITECTURE.md:72`: `Pydantic V2 Validation: Compile-time and runtime type safety; guarantees decimal precision serialization.`
  * *Source:* `AI_PIPELINE.md:30`: `Pydantic V2 Schema & Regex Validator`
* **Database & ORM:** PostgreSQL 16 with Row-Level Security, JSONB, and UUID primary keys; SQLAlchemy 2.0 (AsyncSession) and Alembic for migrations.
  * *Source:* `ORIGINAL_REQUEST.md:66-68`: `- PostgreSQL \n - SQLAlchemy \n - Alembic`
  * *Source:* `SYSTEM_ARCHITECTURE.md:37`: `PostgresDB[("PostgreSQL 16 (RLS, JSONB, Timescale/Auditing)")]`
  * *Source:* `DATABASE_DESIGN.md:11`: `UUID Primary Keys: All entities use UUID v4 (UUID DEFAULT gen_random_uuid())`
* **Caching & Message Broker:** Redis as broker and result store.
  * *Source:* `ORIGINAL_REQUEST.md:69`: `- Redis`
  * *Source:* `SYSTEM_ARCHITECTURE.md:30`: `RedisBroker[("Redis Broker & Result Store")]`
* **Asynchronous Task Queue:** Celery for background decoupled tasks.
  * *Source:* `ORIGINAL_REQUEST.md:70`: `- Celery`
  * *Source:* `SYSTEM_ARCHITECTURE.md:75-82`: `Asynchronous Execution Tier (Celery + Redis) ... Task Queues: ocr_queue, llm_extraction_queue, reconciliation_queue, sync_queue`
* **Object Store:** Encrypted private S3-compatible object store (AWS S3 or MinIO) using AES-256 server-side encryption.
  * *Source:* `SYSTEM_ARCHITECTURE.md:38`: `EncryptedS3[("Encrypted S3-Compatible Object Store (MinIO/AWS S3)")]`
  * *Source:* `SECURITY_ARCHITECTURE.md:88`: `Server-Side Encryption: S3 buckets use AWS KMS or customer-managed keys with AES-256.`

---

### 1.2 Database Schema & Exact Phase 1 Tables
The specifications define the relational model and table structures across `DATABASE_DESIGN.md`, `SECURITY_ARCHITECTURE.md`, `SYSTEM_ARCHITECTURE.md`, and `ORIGINAL_REQUEST.md`:

#### 1.2.1 `users` Table
* *Source:* `ORIGINAL_REQUEST.md:76-78`: `3. User registration and login. 4. Secure password hashing. 5. JWT access and refresh token handling.`
* *Source:* `SYSTEM_ARCHITECTURE.md:148`: `USER_MEMBERSHIP }o--|| USER : binds`
* *Source:* `SECURITY_ARCHITECTURE.md:102`: `actor_user_id UUID NOT NULL`
* *Required Schema:*
  ```sql
  CREATE TABLE users (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      email VARCHAR(255) NOT NULL UNIQUE,
      hashed_password VARCHAR(255) NOT NULL,
      full_name VARCHAR(255) NOT NULL,
      phone VARCHAR(30),
      is_active BOOLEAN NOT NULL DEFAULT TRUE,
      is_verified BOOLEAN NOT NULL DEFAULT FALSE,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
  );
  CREATE INDEX idx_users_email ON users(email);
  ```

#### 1.2.2 `organizations` Table
* *Source:* `DATABASE_DESIGN.md:44-58`:
  ```sql
  CREATE TABLE organizations (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      name VARCHAR(255) NOT NULL,
      organization_type VARCHAR(50) NOT NULL CHECK (organization_type IN ('FREELANCER', 'CA_FIRM', 'ENTERPRISE_PRACTICE')),
      primary_email VARCHAR(255) NOT NULL UNIQUE,
      phone VARCHAR(30),
      subscription_tier VARCHAR(50) NOT NULL DEFAULT 'FREE_TRIAL' CHECK (subscription_tier IN ('FREE_TRIAL', 'SILVER', 'GOLD', 'PLATINUM')),
      trial_ends_at TIMESTAMPTZ,
      is_active BOOLEAN NOT NULL DEFAULT TRUE,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
  );
  CREATE INDEX idx_orgs_email ON organizations(primary_email);
  ```

#### 1.2.3 `memberships` (Organization Memberships & Roles) Table
* *Source:* `SYSTEM_ARCHITECTURE.md:147-148`: `ORGANIZATION ||--o{ USER_MEMBERSHIP : employs; USER_MEMBERSHIP }o--|| USER : binds`
* *Source:* `ORIGINAL_REQUEST.md:82-83`: `9. Organization membership. 10. Role-based permissions.`
* *Source:* `SECURITY_ARCHITECTURE.md:70-84`: Roles matrix (`Freelancer Owner`, `CA Firm Partner`, `Staff Accountant`, `Client Read-Only`)
* *Required Schema:*
  ```sql
  CREATE TABLE memberships (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
      role VARCHAR(50) NOT NULL CHECK (role IN ('FREELANCER_OWNER', 'CA_ADMIN', 'CA_STAFF', 'AUDITOR', 'CLIENT_VIEWER')),
      is_active BOOLEAN NOT NULL DEFAULT TRUE,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      CONSTRAINT uq_user_organization UNIQUE (user_id, organization_id)
  );
  CREATE INDEX idx_memberships_user_org ON memberships(user_id, organization_id);
  CREATE INDEX idx_memberships_org ON memberships(organization_id);
  ```

#### 1.2.4 `client_businesses` Table
* *Source:* `DATABASE_DESIGN.md:63-79`:
  ```sql
  CREATE TABLE client_businesses (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
      legal_name VARCHAR(255) NOT NULL,
      trade_name VARCHAR(255),
      entity_type VARCHAR(50) NOT NULL CHECK (entity_type IN ('INDIVIDUAL_FREELANCER', 'PROPRIETORSHIP', 'PARTNERSHIP', 'LLP', 'PVT_LTD')),
      pan VARCHAR(10) NOT NULL CHECK (pan ~ '^[A-Z]{5}[0-9]{4}[A-Z]{1}$'),
      primary_gstin VARCHAR(15) CHECK (primary_gstin ~ '^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$'),
      gst_registered_state_code VARCHAR(2) NOT NULL,
      composition_scheme BOOLEAN NOT NULL DEFAULT FALSE,
      current_financial_year VARCHAR(9) NOT NULL DEFAULT '2024-2025',
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      CONSTRAINT uq_client_business_pan UNIQUE (organization_id, pan)
  );
  CREATE INDEX idx_client_biz_org ON client_businesses(organization_id);
  ```

#### 1.2.5 `document_batches` Table
* *Source:* `API_SPECIFICATION.md:51`: `"batch_id": "bch_01HP389AB01"`
* *Source:* `ORIGINAL_REQUEST.md:128`: `10. Return a batch ID and individual document IDs.`
* *Required Schema:*
  ```sql
  CREATE TABLE document_batches (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      batch_reference VARCHAR(100) NOT NULL UNIQUE,
      organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
      client_business_id UUID NOT NULL REFERENCES client_businesses(id) ON DELETE RESTRICT,
      uploaded_by_user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
      total_files INT NOT NULL DEFAULT 1,
      status VARCHAR(50) NOT NULL DEFAULT 'PROCESSING' CHECK (status IN ('PROCESSING', 'COMPLETED', 'FAILED', 'PARTIALLY_COMPLETED')),
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
  );
  CREATE INDEX idx_batches_org_client ON document_batches(organization_id, client_business_id);
  ```

#### 1.2.6 `documents` Table
* *Source:* `DATABASE_DESIGN.md:88-114`:
  ```sql
  CREATE TABLE documents (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
      client_business_id UUID NOT NULL REFERENCES client_businesses(id) ON DELETE RESTRICT,
      batch_id UUID REFERENCES document_batches(id) ON DELETE SET NULL,
      file_name VARCHAR(255) NOT NULL,
      file_size_bytes BIGINT NOT NULL,
      mime_type VARCHAR(100) NOT NULL,
      s3_storage_key VARCHAR(512) NOT NULL UNIQUE,
      sha256_hash CHAR(64) NOT NULL,
      document_category VARCHAR(50) NOT NULL CHECK (document_category IN (
          'BANK_STATEMENT', 'SALES_INVOICE', 'PURCHASE_INVOICE', 'EXPENSE_RECEIPT',
          'CREDIT_NOTE', 'DEBIT_NOTE', 'PAYMENT_RECEIPT', 'OTHER'
      )),
      processing_status VARCHAR(50) NOT NULL DEFAULT 'UPLOADED' CHECK (processing_status IN (
          'UPLOADED', 'PROCESSING', 'EXTRACTION_FAILED', 'EXTRACTED', 'MATCHED',
          'REVIEW_PENDING', 'APPROVED', 'REJECTED', 'POSTED', 'SYNCED', 'SYNC_FAILED'
      )),
      extracted_metadata JSONB DEFAULT '{}'::jsonb,
      extraction_confidence NUMERIC(5, 4) DEFAULT 0.0000,
      is_duplicate BOOLEAN NOT NULL DEFAULT FALSE,
      uploaded_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
  );
  CREATE INDEX idx_docs_org_client ON documents(organization_id, client_business_id);
  CREATE INDEX idx_docs_sha256 ON documents(organization_id, client_business_id, sha256_hash);
  CREATE INDEX idx_docs_status ON documents(processing_status);
  ```

#### 1.2.7 `audit_events` Table
* *Source:* `SECURITY_ARCHITECTURE.md:98-115`:
  ```sql
  CREATE TABLE audit_events (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
      actor_user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
      actor_ip_address VARCHAR(45) NOT NULL,
      user_agent TEXT,
      event_type VARCHAR(100) NOT NULL,
      target_entity_type VARCHAR(50) NOT NULL,
      target_entity_id UUID NOT NULL,
      previous_state JSONB,
      new_state JSONB,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
  );
  CREATE INDEX idx_audit_org_time ON audit_events(organization_id, created_at DESC);
  CREATE INDEX idx_audit_target ON audit_events(target_entity_type, target_entity_id);
  REVOKE UPDATE, DELETE ON audit_events FROM ALL;
  ```

#### 1.2.8 `refresh_tokens` Table (Token Revocation & Lifecycle)
* *Source:* `SECURITY_ARCHITECTURE.md:18`: `RefreshToken: Rotating HTTP-Only Secure Cookies`
* *Source:* `ORIGINAL_REQUEST.md:78`: `5. JWT access and refresh token handling.`
* *Required Schema:*
  ```sql
  CREATE TABLE refresh_tokens (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      token_hash VARCHAR(255) NOT NULL UNIQUE,
      expires_at TIMESTAMPTZ NOT NULL,
      revoked BOOLEAN NOT NULL DEFAULT FALSE,
      replaced_by_token_id UUID REFERENCES refresh_tokens(id) ON DELETE SET NULL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
  );
  CREATE INDEX idx_refresh_tokens_user ON refresh_tokens(user_id);
  CREATE INDEX idx_refresh_tokens_hash ON refresh_tokens(token_hash);
  ```

#### 1.2.9 Financial Precision Rule
* *Source:* `DATABASE_DESIGN.md:7`: `1. Financial Precision: All currency fields use NUMERIC(18, 4). No floating-point data types.`
* *Source:* `ASSUMPTIONS_AND_DECISIONS.md:11-13`: `Database: All monetary amounts, tax rates, and ledger balances MUST be stored as NUMERIC(18, 4) in PostgreSQL. Backend (Python): Use standard library decimal.Decimal exclusively. Never cast monetary values to float.`
* *Source:* `ORIGINAL_REQUEST.md:163`: `Never use floating-point types for financial amounts.`

---

### 1.3 Row-Level Security (RLS) & Tenant Isolation
* **PostgreSQL RLS Enablement:**
  * *Source:* `SECURITY_ARCHITECTURE.md:46-57`:
    ```sql
    ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
    ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;
    ALTER TABLE bank_transactions ENABLE ROW LEVEL SECURITY;
    ALTER TABLE journal_entries ENABLE ROW LEVEL SECURITY;
    ALTER TABLE journal_lines ENABLE ROW LEVEL SECURITY;

    CREATE POLICY tenant_isolation_policy ON invoices
        FOR ALL
        USING (organization_id = NULLIF(current_setting('app.current_org_id', true), '')::uuid);
    ```
* **Session Variables:**
  * `app.current_org_id`: UUID of the authenticated organization.
  * `app.current_client_id`: UUID of the active client business (for CA firms and multi-client tenancy).
  * *Source:* `SECURITY_ARCHITECTURE.md:59-66`:
    ```python
    async def set_tenant_db_context(db_session: AsyncSession, org_id: str):
        await db_session.execute(
            text("SET LOCAL app.current_org_id = :org_id"),
            {"org_id": org_id}
        )
    ```
* **Connection Pool Session Cleanup:**
  * In connection-pooled applications (SQLAlchemy `asyncpg`), unhandled exceptions or connection return can leak session parameters.
  * *Remedy:* Use `SET LOCAL` which expires upon transaction completion (`COMMIT` or `ROLLBACK`), and hook SQLAlchemy pool listeners (`after_cursor_execute` or `reset_on_return`) to issue `DISCARD ALL` or `RESET ALL`.
* **Bypass Roles:**
  * Database superuser (`postgres`) or administrative migration runner with `BYPASSRLS` permission. Regular web application user must NEVER possess `BYPASSRLS` or `SUPERUSER`.
  * *Source:* `DATABASE_DESIGN.md:2`, `SECURITY_ARCHITECTURE.md:43`.

---

### 1.4 Authentication, JWT Lifecycle & RBAC
* **Password Hashing:**
  * Argon2id or Bcrypt with cost factor $\ge 12$ rounds. Plaintext passwords must never be stored.
  * *Source:* `ORIGINAL_REQUEST.md:77`: `4. Secure password hashing.`
* **JWT Token Specification:**
  * Access Token: Stateless Ed25519 or HMAC-SHA256, 15-minute lifespan.
    Payload: `sub` (User UUID), `org_id` (Active Organization UUID), `client_id` (Active Client Business UUID), `roles` (list of roles), `permissions` (list of permission keys), `exp`, `iat`, `jti`.
    *Source:* `SECURITY_ARCHITECTURE.md:17`: `Stateless Ed25519 Signed JWTs (15 min lifespan)`.
  * Refresh Token: Rotating token stored in HTTP-Only, Secure, SameSite=Lax/Strict cookie.
    *Source:* `SECURITY_ARCHITECTURE.md:18`: `Rotating HTTP-Only Secure Cookies`.
  * Token Revocation: Redis blacklist checking token `jti` or user revocation timestamp upon logout.
* **RBAC Roles & Permissions Matrix:**
  * *Source:* `SECURITY_ARCHITECTURE.md:70-84`:
    * Roles:
      1. `FREELANCER_OWNER` (Freelancer Owner)
      2. `CA_ADMIN` (CA Firm Partner / Admin)
      3. `CA_STAFF` (Staff Accountant / Junior Reviewer)
      4. `AUDITOR` (Read-only Reviewer)
      5. `CLIENT_VIEWER` (Client Read-Only)
    * Permission mapping:
      * `doc:upload`: Freelancer ✅, CA Partner ✅, Staff Accountant ✅, Client Read-Only ✅
      * `doc:view`: Freelancer ✅, CA Partner ✅, Staff Accountant ✅, Client Read-Only ✅
      * `doc:override_extracted`: Freelancer ✅, CA Partner ✅, Staff Accountant ✅, Client Read-Only ❌
      * `recon:view_candidates`: Freelancer ✅, CA Partner ✅, Staff Accountant ✅, Client Read-Only ❌
      * `recon:approve_and_post`: Freelancer ✅, CA Partner ✅, Staff Accountant ❌, Client Read-Only ❌
      * `accounting:view_reports`: Freelancer ✅, CA Partner ✅, Staff Accountant ✅, Client Read-Only ✅ (Own books)
      * `accounting:period_lock`: Freelancer ✅, CA Partner ✅, Staff Accountant ❌, Client Read-Only ❌
      * `sync:tally_zoho`: Freelancer ✅, CA Partner ✅, Staff Accountant ❌, Client Read-Only ❌
      * `admin:manage_users`: Freelancer ✅, CA Partner ✅, Staff Accountant ❌, Client Read-Only ❌
* **Tenancy Headers:**
  * `X-Organization-Id`: UUID string
  * `X-Client-Business-Id`: UUID string
  * *Source:* `API_SPECIFICATION.md:9-11`.

---

### 1.5 Immutable Audit Logging Infrastructure
* **Append-Only Immutability:**
  * Table `audit_events` strictly prohibits `UPDATE` and `DELETE` queries (`SECURITY_ARCHITECTURE.md:115`: `REVOKE UPDATE, DELETE ON audit_events FROM ALL`).
* **Required Audit Fields:**
  * `id`: UUID Primary Key
  * `organization_id`: UUID Foreign Key
  * `actor_user_id`: UUID Foreign Key
  * `actor_ip_address`: IPv4/IPv6 string (`VARCHAR(45)`)
  * `user_agent`: Client User-Agent string
  * `event_type`: Event identifier string (e.g. `'USER_REGISTERED'`, `'ORGANIZATION_CREATED'`, `'CLIENT_CREATED'`, `'DOCUMENT_UPLOADED'`, `'JOB_ENQUEUED'`, `'DUPLICATE_FLAGGED'`)
  * `target_entity_type`: Target entity string (e.g. `'USER'`, `'ORGANIZATION'`, `'CLIENT_BUSINESS'`, `'DOCUMENT'`, `'BATCH'`)
  * `target_entity_id`: UUID of target entity
  * `previous_state`: JSONB before state (null on create)
  * `new_state`: JSONB after state (null on delete)
  * `created_at`: TIMESTAMPTZ default `NOW()`
  * *Source:* `SECURITY_ARCHITECTURE.md:98-115`, `ORIGINAL_REQUEST.md:86`.

---

### 1.6 File Upload & Processing Slice
* **Supported File Types:** PDF (vector & raster), JPG, PNG, CSV, XLS, XLSX, and ZIP.
  * *Source:* `ORIGINAL_REQUEST.md:121`, `REQUIREMENTS.md:61`, `API_SPECIFICATION.md:42`.
* **File Signature (Magic Bytes) Verification:**
  * Must inspect the binary stream header rather than relying solely on user-supplied MIME type or filename extension.
  * PDF: `%PDF-` (`0x25 0x50 0x44 0x46`)
  * PNG: `\x89PNG\r\n\x1a\n` (`0x89 0x50 0x4E 0x47`)
  * JPG: `\xFF\xD8\xFF`
  * ZIP/XLSX: `PK\x03\x04` (`0x50 0x4B 0x03 0x04`)
  * *Source:* `REQUIREMENTS.md:62`, `SECURITY_ARCHITECTURE.md:87`.
* **File Size Limit:** 50MB per file maximum.
  * *Source:* `REQUIREMENTS.md:62`: `file size limits (50MB per file)`.
* **Cryptographic Hashing & Duplicate Detection:**
  * Calculate SHA-256 hash across raw file bytes.
  * Scope: `(organization_id, client_business_id, sha256_hash)`.
  * If identical hash exists within the client business scope, mark `is_duplicate = TRUE`.
  * *Source:* `DATABASE_DESIGN.md:96, 107, 112`, `ORIGINAL_REQUEST.md:123-124`.
* **Storage Strategy:**
  * Encrypted S3-compatible bucket (AES-256).
  * Storage key schema: `tenants/{org_id}/{client_id}/documents/{year}/{month}/{doc_id}/{sanitized_filename}`.
  * Security: Private bucket; access via time-bounded 15-minute pre-signed URLs or authorized streaming. Plaintext passwords for bank statements are decrypted in-memory and never stored.
  * *Source:* `SECURITY_ARCHITECTURE.md:88-90`, `DATABASE_DESIGN.md:95`.
* **Celery Background Job Creation:**
  * Asynchronous task dispatched to Celery queue (`ocr_queue` or ingestion worker).
  * Phase 1 extraction stage constraint: Status remains clearly marked as `PROCESSING` or `UPLOADED`. No fake or simulated AI extraction.
  * *Source:* `ORIGINAL_REQUEST.md:127, 132, 207`.
* **Response Envelope for Upload:**
  * HTTP `202 Accepted` returning `batch_id` and array of `uploaded_files` (`document_id`, `file_name`, `sha256_hash`, `status: "PROCESSING"`, `is_duplicate: boolean`).
  * *Source:* `API_SPECIFICATION.md:47-62`.

---

### 1.7 Critical Design Issues, Accounting Rules & GST Constraints
* **Transaction Boundaries:**
  1. File Upload: (a) Stream to S3 with AES-256 -> (b) Open DB transaction -> (c) Insert `document_batches`, `documents`, and `audit_events` -> (d) Commit DB -> (e) Dispatch Celery task with `document_id`.
  2. If S3 upload fails, abort and do not write to DB. If DB commit succeeds but Celery enqueue fails, mark status as retryable.
* **Idempotency:**
  * Celery tasks must check current document status before execution.
  * Tally and Zoho sync require external idempotency keys (`journal_entries.id`).
  * *Source:* `ORIGINAL_REQUEST.md:50, 169`, `INTEGRATION_ARCHITECTURE.md:111-117`.
* **Financial Calculations & Invariants:**
  * Currency fields use `NUMERIC(18, 4)` and `decimal.Decimal`.
  * Double-entry balance invariant: $\sum \text{Debits} == \sum \text{Credits}$ enforced via database trigger `trg_verify_journal_balance`.
  * *Source:* `DATABASE_DESIGN.md:324-346`.
* **GST Rules Beyond Simple State Codes:**
  * Simple state code comparison (`Supplier State == POS State -> CGST + SGST`, else `IGST`) is necessary but not sufficient.
  * Special Economic Zone (SEZ) supplies: treated as inter-state supply (IGST or zero-rated) regardless of state code.
  * Export of Services with LUT: zero-rated supply without tax under Section 16 of IGST Act.
  * Reverse Charge Mechanism (RCM): Section 9(3) / 9(4) mandates buyer to pay output tax and claim matching ITC.
  * Ineligible ITC under Section 17(5): blocked credit on motor vehicles, food/beverage, personal consumption must NOT be routed to Electronic Credit Ledger.
  * TDS Deductions: Section 194J/194C generates compound journal vouchers.
  * *Source:* `ORIGINAL_REQUEST.md:54`, `REQUIREMENTS.md:115-128`, `REQUIREMENT_GAP_ANALYSIS.md:15-38`.

---

## 2. Features Discovered

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | Auth & Identity | User Registration | Creates user account with hashed password and verification state | Email, password, full_name, phone | User record, 201 Created | 400 on duplicate email or weak password | `ORIGINAL_REQUEST.md:76` |
| 2 | Auth & Identity | User Login | Authenticates user credentials and issues access & refresh tokens | Email, password | JWT access token (15m), refresh cookie, accessible orgs | 401 Unauthorized on invalid credentials | `API_SPECIFICATION.md:33`, `SECURITY_ARCHITECTURE.md:17` |
| 3 | Auth & Identity | Refresh Token Rotation | Exchanges valid refresh token for new access and rotated refresh token | HTTP-only refresh cookie | New access token, rotated refresh cookie | 401 Unauthorized; token reuse triggers family revocation | `SECURITY_ARCHITECTURE.md:18` |
| 4 | Auth & Identity | User Logout & Token Revocation | Revokes active refresh token and blacklists access token `jti` in Redis | Bearer token, refresh cookie | 200 OK, cleared cookies | 401 Unauthorized if invalid token | `SECURITY_ARCHITECTURE.md:18`, `ORIGINAL_REQUEST.md:78` |
| 5 | Tenancy | Organization Creation | Creates a Freelancer or CA Firm subscription tenant | Name, organization_type (`FREELANCER`, `CA_FIRM`, `ENTERPRISE_PRACTICE`), primary_email, phone | Organization record with default `FREE_TRIAL` tier | 400 on duplicate email, invalid org type | `DATABASE_DESIGN.md:44-58`, `ORIGINAL_REQUEST.md:79` |
| 6 | Tenancy | Organization Membership | Links users to organizations with assigned RBAC roles | user_id, organization_id, role | Membership record | 400 on duplicate membership; 403 if actor lacks `admin:manage_users` | `SYSTEM_ARCHITECTURE.md:147`, `SECURITY_ARCHITECTURE.md:70` |
| 7 | Tenancy | Client Business Management | Creates/manages legal accounting entity with PAN, GSTIN, and state code | organization_id, legal_name, trade_name, entity_type, pan, primary_gstin, gst_state_code | Client business record | 400 on invalid PAN/GSTIN regex; 409 on duplicate PAN within org | `DATABASE_DESIGN.md:63-79`, `ORIGINAL_REQUEST.md:81` |
| 8 | Tenancy | Client Business Context Switcher | CA Firm selects active client business for session | client_business_id, organization_id | Active client context set in headers/session | 404 if client does not belong to organization | `API_SPECIFICATION.md:35`, `SYSTEM_ARCHITECTURE.md:68` |
| 9 | Tenancy & Security | PostgreSQL Row-Level Security (RLS) | Enforces tenant boundary at database level using `app.current_org_id` and `app.current_client_id` | Database session, org_id, client_id | Isolated query results; cross-tenant rows filtered | RLS policy prevents data return/insert across tenants | `SECURITY_ARCHITECTURE.md:46-66`, `DATABASE_DESIGN.md:8` |
| 10 | Security & Audit | Append-Only Audit Logging | Emits immutable audit record for every critical state mutation | actor_user_id, org_id, event_type, target_entity, before/after JSON, IP, User-Agent | Audit event record | `REVOKE UPDATE, DELETE` prevents alteration; DB triggers reject modification | `SECURITY_ARCHITECTURE.md:98-115`, `ORIGINAL_REQUEST.md:86` |
| 11 | Ingestion Slice | Multi-File Upload Endpoint | Uploads one or more financial documents in a single request | Multipart form (`files`, `category`, optional `pdf_password`) | HTTP 202 Accepted (`batch_id`, list of documents with IDs and statuses) | 400 on invalid MIME/signature, 413 if file > 50MB | `API_SPECIFICATION.md:41-62`, `ORIGINAL_REQUEST.md:120` |
| 12 | Ingestion Slice | File Signature & Magic Bytes Validation | Verifies binary magic bytes (PDF, JPG, PNG, CSV, XLS, XLSX, ZIP) | File byte stream | Validated file stream or rejection | 400 Bad Request with error `INVALID_FILE_SIGNATURE` | `REQUIREMENTS.md:62`, `SECURITY_ARCHITECTURE.md:87` |
| 13 | Ingestion Slice | SHA-256 Deduplication | Calculates SHA-256 hash and detects duplicate within client business scope | File byte stream, org_id, client_business_id | SHA-256 hash string, `is_duplicate` boolean flag | Identical file marked `is_duplicate=TRUE` and excluded from billing | `DATABASE_DESIGN.md:96, 107`, `REQUIREMENT_GAP_ANALYSIS.md:85` |
| 14 | Ingestion Slice | S3-Compatible Encrypted Private Storage | Stores raw uploaded files in S3-compatible bucket using AES-256 encryption | Sanitized file, storage key path | S3 object reference with unique storage key | 500 Internal Error if S3 storage unreachable | `SYSTEM_ARCHITECTURE.md:38`, `SECURITY_ARCHITECTURE.md:88` |
| 15 | Ingestion Slice | Document Metadata Persistence | Records document metadata, batch association, and processing status in PostgreSQL | File metadata, hash, storage key, batch_id | Persisted `documents` record with status `UPLOADED`/`PROCESSING` | 500 on DB failure, rolled back transaction | `DATABASE_DESIGN.md:88-114`, `ORIGINAL_REQUEST.md:126` |
| 16 | Ingestion Slice | Asynchronous Celery Ingestion Job | Enqueues background processing task decoupled from HTTP request | `document_id`, `batch_id`, storage key | Celery task ID, queued task | Task retry with exponential backoff on transient failure | `SYSTEM_ARCHITECTURE.md:107`, `ORIGINAL_REQUEST.md:127` |
| 17 | Ingestion Slice | Document Status Query Endpoint | Retrieves document processing status, batch progress, and metadata | `document_id` | Document status, category, confidence score, extracted JSON | 404 if document not found; 403 if belonging to different tenant | `API_SPECIFICATION.md:64-94` |
| 18 | Infrastructure | Standard API Response & Error Handling | Wraps responses in standard envelopes with error codes and request IDs | API handler results or exceptions | JSON envelope with `success`, `error_code`, `message`, `request_id` | Structured JSON error instead of unhandled 500 | `API_SPECIFICATION.md:13-26`, `ORIGINAL_REQUEST.md:87` |
| 19 | Infrastructure | Health Check & Readiness Probes | Exposes liveness and readiness endpoints checking DB and Redis | HTTP GET `/health`, `/ready` | HTTP 200 OK `{"status": "healthy", "database": "ok", "redis": "ok"}` | 503 Service Unavailable if DB or Redis is down | `ORIGINAL_REQUEST.md:88` |
| 20 | Accounting Core (Rule) | Financial Precision Guard | Guarantees all monetary and financial calculations use `NUMERIC(18, 4)` and `Decimal` | Amount inputs | Fixed-precision 4-decimal values | Type error / schema validation failure if floating-point used | `ADR-01`, `DATABASE_DESIGN.md:7`, `ORIGINAL_REQUEST.md:163` |
| 21 | Accounting Core (Rule) | Double-Entry Balance Invariant | Verifies $\sum \text{Debits} == \sum \text{Credits}$ before posting journal entries | Journal entry and line items | Balanced journal entry | Invariant exception: `Journal Entry is not balanced` | `DATABASE_DESIGN.md:324-346`, `ADR-04` |
| 22 | GST Intelligence (Rule) | Enhanced Tax Determination | Distinguishes intra-state (CGST+SGST), inter-state (IGST), SEZ units, and LUT exports | Supplier state, POS state, SEZ flag, LUT flag | Correct tax classification | Rejection or human review flag if tax type conflicts with POS | `REQUIREMENTS.md:115-128`, `ORIGINAL_REQUEST.md:54` |
| 23 | Bank Ingestion (Rule) | In-Memory Statement Decryption | Decrypts password-protected PDF bank statements in-memory without storing passwords | Document bytes, user-supplied password | Decrypted PDF stream | 400 Bad Request `PASSWORD_REQUIRED` or `INVALID_PASSWORD` | `SECURITY_ARCHITECTURE.md:90`, `REQUIREMENT_GAP_ANALYSIS.md:53` |

---

## 3. Edge Cases Discovered

| # | Feature | Input | Observed Behavior / Required Handling |
|---|---------|-------|----------------------------------------|
| 1 | Multi-Tenant RLS | User from Org A requests Document ID belonging to Org B | RLS policy filters row at database engine level; query returns 0 rows; API responds with 404 Not Found (zero cross-tenant data exposure). |
| 2 | Multi-Tenant Switching | CA Staff user switches active client business header `X-Client-Business-Id` to a client outside their CA Firm | Middleware verifies membership and client ownership; rejects request with 403 Forbidden before database query execution. |
| 3 | Connection Pool Session Leakage | Connection returned to pool after request with `SET LOCAL app.current_org_id` | `SET LOCAL` automatically rolls back on transaction completion; pool check-in listener runs `RESET ALL` to eliminate state leakage between pooled requests. |
| 4 | File Upload & Hashing | User uploads identical invoice file twice to the same client business | SHA-256 matches existing record; system sets `is_duplicate = TRUE`, returns HTTP 202 with `is_duplicate: true`, and skips subscription usage increment. |
| 5 | File Upload & Hashing | User uploads identical file to two *different* client businesses | Duplicate check is scoped to `(organization_id, client_business_id, sha256_hash)`; file is accepted as legitimate independent document for each client. |
| 6 | File Validation | User renames an `.exe` or malware file to `.pdf` | File signature (magic bytes) validator detects missing `%PDF-` header; request rejected immediately with 400 Bad Request `INVALID_FILE_SIGNATURE`. |
| 7 | File Validation | User uploads a file of size 52 MB | File size validator rejects upload with 413 Payload Too Large (`MAX_FILE_SIZE_EXCEEDED: 50MB`). |
| 8 | Bank Statement Upload | User uploads password-protected PDF bank statement without password | Pre-validation detects encrypted PDF; returns 422/400 `PASSWORD_REQUIRED`. When password is provided, statement is decrypted in-memory; password is NEVER stored. |
| 9 | Decimal Precision | Financial calculation producing repeating decimal (e.g. $1000 \div 3$) | Standard `float` would produce $333.3333333333333$; `decimal.Decimal` with `ROUND_HALF_UP` preserves exact 4-decimal precision `333.3333`. |
| 10 | Audit Log Protection | Direct database query `UPDATE audit_events SET event_type = 'X'` | PostgreSQL database trigger and revoked permissions immediately abort query with `permission denied for table audit_events`. |
| 11 | Celery Worker Idempotency | Celery worker receives duplicate task trigger for the same `document_id` | Worker verifies current document state in DB; if already in `PROCESSING` or terminal state, exits cleanly without redundant processing. |
| 12 | Token Revocation & Refresh | Attacker attempts to replay an already-consumed refresh token | Refresh token rotation records `replaced_by_token_id`; replaying consumed token triggers immediate family invalidation, revoking all active sessions for that user. |
| 13 | Organization PAN Uniqueness | CA firm attempts to register a client business with a PAN already registered under another client in the same CA firm | Database constraint `uq_client_business_pan (organization_id, pan)` triggers conflict; API responds with 409 Conflict. |
| 14 | GST Determination | Supplier in Maharashtra supplies services to an SEZ unit located in Maharashtra | Simple state code check would erroneously assign intra-state CGST + SGST; SEZ treatment overrides to zero-rated or inter-state IGST. |
| 15 | TDS Remittance | Bank credit received is ₹90,000 for an invoice of ₹1,00,000 | Match engine detects ₹10,000 difference matches Section 194J (10% TDS); stages compound voucher (Dr Bank ₹90k, Dr TDS Receivable ₹10k, Cr Debtor ₹100k). |

---

## 4. Logic Chain

1. **Premise 1 (Tenancy & Security Foundations):**
   * *Observation:* `ORIGINAL_REQUEST.md:58-89` mandates building the Phase 1 Application Foundation: User registration, secure password hashing, JWT access/refresh handling, organizations (Freelancer & CA firm), client businesses, memberships, RBAC permissions, PostgreSQL RLS, audit event logging, and health endpoints.
   * *Inference:* The core foundation must support two distinct organizational models: a 1:1 relationship for Freelancers (Org = Client Business) and a 1:N relationship for CA Firms (1 Org contains $N$ Client Businesses).
   * *Inference:* PostgreSQL Row-Level Security cannot depend solely on application-level filtering; it must be enforced in PostgreSQL using session parameters (`app.current_org_id`, `app.current_client_id`) set via transaction-scoped `SET LOCAL` calls during API request execution.

2. **Premise 2 (Database Schema Completeness & Gap Rectification):**
   * *Observation:* `DATABASE_DESIGN.md` explicitly provides SQL DDL for `organizations`, `client_businesses`, `documents`, `invoices`, `bank_accounts`, `bank_transactions`, `reconciliation_matches`, `chart_of_accounts`, `journal_entries`, and `journal_lines`.
   * *Observation:* However, `DATABASE_DESIGN.md` omitted SQL DDL for `users`, `memberships`, `refresh_tokens`, and `document_batches`, despite them being explicitly required in `ORIGINAL_REQUEST.md:76-83, 128` and referenced in `SYSTEM_ARCHITECTURE.md:147-148` and `SECURITY_ARCHITECTURE.md:98-115`.
   * *Inference:* For Phase 1 implementation, the missing DDL definitions must be formalized with exact foreign keys, deletion rules (`ON DELETE CASCADE` for user memberships; `ON DELETE RESTRICT` for organizations and client businesses), and indexes.

3. **Premise 3 (Financial Integrity & Invariants):**
   * *Observation:* `ADR-01` and `ORIGINAL_REQUEST.md:163` strictly forbid floating-point types (`float`), mandating `NUMERIC(18, 4)` in PostgreSQL and `decimal.Decimal` in Python.
   * *Observation:* Double-entry accounting requires $\sum \text{Debits} == \sum \text{Credits}$ enforced via database triggers on `journal_entries`.
   * *Inference:* All Pydantic V2 schemas and SQLAlchemy models must use `Decimal` with custom JSON serializers to avoid JavaScript precision truncation.

4. **Premise 4 (First Vertical Slice: File Upload Pipeline):**
   * *Observation:* `ORIGINAL_REQUEST.md:115-133` mandates the document upload slice: client business selection, multi-file upload, format validation (PDF, JPG, PNG, CSV, XLS, XLSX), magic bytes verification, max size check, SHA-256 hashing, client-scoped duplicate detection, private S3 storage (AES-256), DB metadata persistence, and asynchronous Celery job creation.
   * *Observation:* `ORIGINAL_REQUEST.md:132, 207` explicitly commands: *"For this first phase, extraction can remain a clearly defined pending-processing stage. Do not pretend OCR or accounting extraction is complete. Do not build fake AI extraction functionality."*
   * *Inference:* The Celery task for Phase 1 must initialize the document record in `PROCESSING` status and handle file hashing/storage verification, without executing simulated or mocked OCR/accounting extractions.

---

## 5. Caveats & Identified Specification Gaps

1. **Gap in `DATABASE_DESIGN.md` Regarding User & Membership Tables:**
   * While `SYSTEM_ARCHITECTURE.md` Section 4 illustrates the ERD linking `ORGANIZATION`, `USER_MEMBERSHIP`, and `USER`, and `SECURITY_ARCHITECTURE.md` references `actor_user_id`, the DDL for `users` and `memberships` was omitted from Section 3.1 of `DATABASE_DESIGN.md`. This gap has been fully resolved above by specifying the complete DDL for `users`, `memberships`, and `refresh_tokens`.
2. **Gap in Document Batch Representation:**
   * `API_SPECIFICATION.md:51` returns `"batch_id": "bch_01HP389AB01"` and `ORIGINAL_REQUEST.md:128` requires returning a batch ID, but `DATABASE_DESIGN.md` did not have an explicit `document_batches` table. A dedicated `document_batches` table has been added to maintain the parent-child relationship for multi-file upload batches.
3. **CA Firm Client Business Permission Delegation:**
   * In a CA firm, multiple staff members work on specific clients. While `memberships` assigns a role at the organization level, fine-grained assignment of staff members to specific `client_businesses` can be managed either via an optional `client_business_assignments` mapping table or by permitting all CA firm staff to switch context across any client belonging to that CA firm (as described in `SYSTEM_ARCHITECTURE.md:153`). For Phase 1, organization-level membership with switchable client context satisfies all stated requirements.

---

## 6. Conclusion

The specification mining for Phase 1 Backend Architecture is complete and authoritative. Phase 1 requires:
1. **Tech Stack:** Python 3.11+, FastAPI (OpenAPI 3.1, async dependencies), Pydantic V2 (strict typing, Decimal serialization), PostgreSQL 16 (RLS, JSONB, UUIDs), SQLAlchemy 2.0 (asyncpg), Alembic, Redis, and Celery.
2. **Phase 1 Tables:**
   * Core Tenancy & Auth: `users`, `organizations`, `memberships`, `client_businesses`, `refresh_tokens`
   * Audit: `audit_events` (append-only, immutable)
   * File Ingestion: `document_batches`, `documents`
   * All amounts stored as `NUMERIC(18, 4)`.
3. **Tenant Isolation:** Enforced via PostgreSQL Row-Level Security on tenant tables using `SET LOCAL app.current_org_id` and `SET LOCAL app.current_client_id`, reset upon connection pool return.
4. **Auth & RBAC:** Argon2id/Bcrypt password hashing, 15-minute access JWTs (Ed25519/HS256), rotating refresh token cookies, Redis revocation, and 5 distinct RBAC roles.
5. **Document Upload Pipeline:** Multi-part file upload with magic byte checking, 50MB size limit, SHA-256 duplicate detection within client business scope, private S3 AES-256 storage, metadata persistence, and Celery background task dispatch (with pending status and no fake extraction).

---

## 7. Verification Method

To independently verify the completeness and compliance of the backend specifications against the repository:

1. **Verify Source Documentation:**
   * Inspect lines 44-115 of `DATABASE_DESIGN.md` to confirm base schemas for `organizations`, `client_businesses`, and `documents`.
   * Inspect lines 46-66 and 70-115 of `SECURITY_ARCHITECTURE.md` to confirm RLS policies, session variables, RBAC matrix, and `audit_events` immutability.
   * Inspect lines 41-62 of `API_SPECIFICATION.md` to confirm the upload endpoint contract and batch response format.
   * Inspect lines 58-134 of `ORIGINAL_REQUEST.md` to confirm Phase 1 scope and explicit anti-faking directives.
2. **Schema & Migration Verification Command (upon implementation):**
   * Run Alembic migrations: `alembic upgrade head`
   * Execute PostgreSQL RLS test:
     ```sql
     SET LOCAL app.current_org_id = '00000000-0000-0000-0000-000000000001';
     SELECT * FROM documents; -- Must return only rows matching this org_id
     ```
3. **Automated Test Suite Verification (Phase 1 Target):**
   * Run pytest suite:
     `pytest tests/ -v`
   * Mandatory automated test targets:
     * User registration, password hashing verification, login JWT issuance.
     * Organization and client business creation with PAN/GSTIN validation.
     * Cross-tenant isolation rejection (verifying Org A cannot access Org B documents via RLS).
     * File upload: valid PDF, JPG, PNG, CSV, XLSX accepted; invalid magic byte rejected; >50MB rejected.
     * Duplicate SHA-256 detection within client business scope.
     * Celery background task creation and document status lifecycle.
     * Audit trail creation for upload and auth events.
