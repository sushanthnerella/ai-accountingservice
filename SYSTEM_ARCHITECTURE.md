# System Architecture Specification
## AI-Powered Accounting Intelligence Platform

---

## 1. Architectural Philosophy & Overview
The platform follows a **Clean Hexagonal Architecture (Ports and Adapters)** combined with an **Asynchronous Event-Driven Ingestion Pipeline**. This ensures the core double-entry accounting engine and GST rules remain completely isolated from database technologies, UI frameworks, OCR tools, and commercial AI providers.

```mermaid
flowchart TD
    subgraph ClientLayer ["Client Layer (Web Application)"]
        UI_Freelancer["Freelancer Web SPA (React/TS)"]
        UI_CA["CA Firm Multi-Client Dashboard (React/TS)"]
    end

    subgraph GatewayLayer ["API Gateway & Security Layer"]
        ReverseProxy["Nginx / Traefik Reverse Proxy"]
        FastAPI_Gateway["FastAPI Gateway (JWT Auth, RBAC, Rate Limiting)"]
    end

    subgraph CoreServices ["Application Core Services (Python 3.11+)"]
        DocIngestService["Document Ingestion & Hash Service"]
        ReconService["Reconciliation & Match Engine"]
        AcctEngine["Double-Entry Accounting Core"]
        GSTEngine["GST Intelligence & Attribution Engine"]
        SyncService["Sync Orchestrator (Tally & Zoho)"]
    end

    subgraph AsyncPipeline ["Asynchronous Processing Pipeline"]
        RedisBroker[("Redis Broker & Result Store")]
        CeleryWorker_OCR["OCR & Layout Workers (PyMuPDF / PaddleOCR)"]
        CeleryWorker_LLM["AI Extraction Workers (LLM Gateway)"]
        CeleryWorker_Recon["Reconciliation Batch Workers"]
    end

    subgraph DataStorage ["Data & Storage Layer"]
        PostgresDB[("PostgreSQL 16 (RLS, JSONB, Timescale/Auditing)")]
        EncryptedS3[("Encrypted S3-Compatible Object Store (MinIO/AWS S3)")]
    end

    subgraph ExternalEcosystem ["External Integrations"]
        TallyDesktop["TallyPrime (XML / Local HTTP 9000)"]
        ZohoCloud["Zoho Books API (OAuth2 Cloud)"]
        AI_Providers["Commercial LLMs / Local vLLM"]
    end

    ClientLayer --> ReverseProxy
    ReverseProxy --> FastAPI_Gateway
    FastAPI_Gateway --> CoreServices
    CoreServices --> PostgresDB
    CoreServices --> EncryptedS3
    CoreServices --> RedisBroker
    RedisBroker --> AsyncPipeline
    AsyncPipeline --> AI_Providers
    AsyncPipeline --> PostgresDB
    SyncService --> TallyDesktop
    SyncService --> ZohoCloud
```

---

## 2. High-Level Component Decomposition

### 2.1 Web Frontend (React + TypeScript + Tailwind CSS)
- **Architecture:** Modular SPA built with Vite, React 18+, TypeScript, Zustand (lightweight client state), TanStack Query (server state & caching), and Tailwind CSS for a minimal, dense, high-efficiency accounting UI.
- **Sub-Applications:**
  1. *Freelancer Portal:* Focused on rapid bank statement upload, expense categorization, net tax payable, and simple P&L.
  2. *CA Firm Console:* Multi-client workspace switcher, high-density transaction tables, split-screen PDF verification viewer, bulk approval actions, and GSTR-2B reconciliation grids.

### 2.2 FastAPI Backend Application
- **Async Asynchronous I/O:** High concurrency handling of upload streams and real-time reconciliation event streams (SSE).
- **Pydantic V2 Validation:** Compile-time and runtime type safety; guarantees decimal precision serialization.
- **Dependency Injection:** Pluggable repositories, authentication contexts, and unit-of-work transactions.

### 2.3 Asynchronous Execution Tier (Celery + Redis)
- **Task Decoupling:** Long-running OCR parsing, document embedding, and multi-invoice fuzzy matching are decoupled from user HTTP request cycles.
- **Task Queues:**
  - `ocr_queue`: CPU-intensive PDF rendering and text/table extraction.
  - `llm_extraction_queue`: Rate-limited external LLM API calls with backoff.
  - `reconciliation_queue`: Heavy multi-way combinatorial matching.
  - `sync_queue`: Network I/O for Zoho Books API and Tally export generation.

---

## 3. End-to-End Document Ingestion & Posting Flow

The diagram below maps the end-to-end journey of an invoice or bank statement:

```mermaid
sequenceDiagram
    autonumber
    actor User as Freelancer / CA User
    participant Web as React Web SPA
    participant API as FastAPI Gateway
    participant S3 as Encrypted S3 Store
    participant Celery as Celery Async Queue
    participant AI as AI Extraction Gateway
    participant Recon as Reconciliation Engine
    participant DB as PostgreSQL 16
    participant Ledger as Accounting Core

    User->>Web: Uploads Invoices / Bank Statement (PDF/ZIP)
    Web->>API: POST /api/v1/documents/upload (Multi-part)
    API->>API: Compute SHA-256 Hash & Validate Duplicate
    API->>S3: Stream Encrypted Document (AES-256)
    API->>DB: Insert Document Record (Status: PROCESSING)
    API->>Celery: Enqueue Ingestion Task (doc_id)
    API-->>Web: 202 Accepted (doc_id, status: PROCESSING)

    Celery->>S3: Read Document Stream
    Celery->>Celery: OCR & Layout Analysis (PyMuPDF/PaddleOCR)
    Celery->>AI: Structured Extraction Request (Prompt + Schema)
    AI-->>Celery: JSON Payload (Confidence Scores + Line Items)
    Celery->>Celery: Deterministic Math & Tax Verification
    Celery->>DB: Store Extracted Entities & Update Status (EXTRACTED)

    Celery->>Recon: Trigger Reconcile Pipeline (Invoice <-> Bank)
    Recon->>DB: Query Unmatched Bank Txns & Open Invoices
    Recon->>Recon: Multi-Factor Matching (Amount, UTR, Name, Date)
    Recon->>DB: Stage Match Suggestion (Confidence, Reasoning)
    Recon->>DB: Update Status (REVIEW_PENDING)

    User->>Web: Views Side-by-Side Document & Match Card
    User->>Web: Modifies line item or Clicks "Approve & Post"
    Web->>API: POST /api/v1/reconciliations/{id}/approve
    API->>Ledger: Prepare Double-Entry Journal Voucher
    Ledger->>Ledger: Invariant Check (Sum Dr == Sum Cr)
    Ledger->>DB: Insert Immutable Journal Entry & Lines (Status: POSTED)
    Ledger->>DB: Update Document Status (POSTED)
    API-->>Web: 200 OK (Voucher Posted Successfully)
```

---

## 4. Multi-Tenant Organization Data Hierarchy

```mermaid
erDiagram
    ORGANIZATION ||--o{ WORKSPACE : contains
    WORKSPACE ||--o{ CLIENT_BUSINESS : manages
    CLIENT_BUSINESS ||--o{ FINANCIAL_YEAR : operates
    CLIENT_BUSINESS ||--o{ BANK_ACCOUNT : owns
    CLIENT_BUSINESS ||--o{ DOCUMENT : owns
    CLIENT_BUSINESS ||--o{ INVOICE : owns
    CLIENT_BUSINESS ||--o{ BANK_TRANSACTION : owns
    CLIENT_BUSINESS ||--o{ JOURNAL_ENTRY : records
    ORGANIZATION ||--o{ USER_MEMBERSHIP : employs
    USER_MEMBERSHIP }o--|| USER : binds
```

- **Top-Level Tenant (`ORGANIZATION`):** The legal billing entity (either an independent Freelancer or a CA Practice Firm).
- **Workspace (`WORKSPACE`):** Sub-partition (e.g., "Direct Freelance Practice", "Audit Division", "SME Retainer Clients").
- **Client Business (`CLIENT_BUSINESS`):** The actual accounting subject (has its own GSTIN, PAN, Financial Years, and Chart of Accounts). For freelancers, the organization and client business have a 1:1 relationship. For CA firms, 1 workspace has $N$ client businesses.
- **Tenant Context Enforcement:** Every query filters by `organization_id` and `client_business_id`, preventing cross-client or cross-firm data exposure.
