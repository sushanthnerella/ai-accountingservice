# Specification Mining Report: Frontend Phase 1 Foundation & Vertical Slice

**Target Directory:** `e:\New folder (8)\.agents\teamwork\spec_miner_frontend\handoff.md`  
**Author:** Frontend Specification Miner  
**Date:** 2026-11-08  
**Scope:** Phase 1 Application Foundation & Document Upload Vertical Slice  

---

## 1. Observation

Direct examination of authoritative repository specifications:
- **`ORIGINAL_REQUEST.md` (Lines 90–134):**
  - Frontend Stack mandated: React, TypeScript, Vite, Tailwind CSS, TanStack Query, Zustand.
  - Required Foundation: Professional login and registration pages, application layout and navigation, Freelancer workspace, CA firm workspace, organization & client-business switcher, client business creation screen, user profile and settings, role-aware navigation, loading/empty/success/error states.
  - Professional Design Standard: *"The interface should look like a serious financial SaaS product, not a generic admin template."*
  - First Vertical Slice: Document upload supporting multiple files, allowed types `PDF, JPG, PNG, CSV, XLS, XLSX`, client/server validation, SHA-256 calculation, duplicate detection, batch ID return, background job status display, audit logging.
  - Phase 1 Constraint: *"For this first phase, extraction can remain a clearly defined pending-processing stage. Do not pretend OCR or accounting extraction is complete."*
- **`SYSTEM_ARCHITECTURE.md` (Lines 64–69, 137–155):**
  - Section 2.1: Frontend is a modular SPA built with Vite, React 18+, TypeScript, Zustand (lightweight client state), TanStack Query (server state & caching), and Tailwind CSS for a minimal, dense, high-efficiency accounting UI.
  - Sub-Applications: Freelancer Portal (focused single workspace) & CA Firm Console (multi-client workspace switcher, high-density transaction tables, client portfolio).
  - Multi-tenant hierarchy: `ORGANIZATION` (top-level tenant) contains `WORKSPACE` contains `CLIENT_BUSINESS`. Freelancer has 1:1 Org to Client Business; CA firm has 1 Org to $N$ Client Businesses.
- **`API_SPECIFICATION.md` (Lines 7–26, 32–63):**
  - Base URL: `/api/v1`. Authentication: Bearer JWT in `Authorization` header.
  - Tenancy Headers: `X-Organization-Id: <UUID>`, `X-Client-Business-Id: <UUID>`.
  - Standard Error Envelope: `{"success": false, "error_code": "...", "message": "...", "details": {...}, "request_id": "..."}`.
  - Endpoints: `POST /api/v1/auth/login`, `GET /api/v1/workspaces/clients`, `POST /api/v1/workspaces/switch-context`, `POST /api/v1/documents/upload` (returns `202 Accepted` with `batch_id` and array of `uploaded_files`), `GET /api/v1/documents/{document_id}`.
- **`SECURITY_ARCHITECTURE.md` (Lines 16–37, 70–83, 94–115):**
  - Auth tokens: Stateless Ed25519-signed JWTs (15-min lifespan) paired with rotating refresh tokens.
  - RBAC Matrix: Roles `Freelancer Owner`, `CA Firm Partner`, `Staff Accountant`, `Client Read-Only`. Permissions: `doc:upload`, `doc:view`, `doc:override_extracted`, `recon:view_candidates`, `recon:approve_and_post`, `accounting:view_reports`, `accounting:period_lock`, `sync:tally_zoho`, `admin:manage_users`.
  - Audit Trail: Immutable table `audit_events` recording `actor_user_id`, `actor_ip_address`, `event_type`, `target_entity_type`, `target_entity_id`, `previous_state`, `new_state`, `created_at`.
- **`DATABASE_DESIGN.md` (Lines 42–115):**
  - `organizations`: `id` (UUID), `name`, `organization_type` (`'FREELANCER'`, `'CA_FIRM'`, `'ENTERPRISE_PRACTICE'`), `subscription_tier` (`'FREE_TRIAL'`, `'SILVER'`, `'GOLD'`, `'PLATINUM'`).
  - `client_businesses`: `id` (UUID), `organization_id` (UUID), `legal_name`, `trade_name`, `entity_type` (`'INDIVIDUAL_FREELANCER'`, `'PROPRIETORSHIP'`, `'PARTNERSHIP'`, `'LLP'`, `'PVT_LTD'`), `pan` (Regex: `^[A-Z]{5}[0-9]{4}[A-Z]{1}$`), `primary_gstin` (Regex: `^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$`), `gst_registered_state_code` (2 digits), `composition_scheme` (bool), `current_financial_year` (default `'2024-2025'`).
  - `documents`: `file_name`, `file_size_bytes` ($\le 50\text{MB}$), `mime_type`, `sha256_hash` (CHAR 64), `document_category` (`'BANK_STATEMENT'`, `'SALES_INVOICE'`, `'PURCHASE_INVOICE'`, `'EXPENSE_RECEIPT'`, `'CREDIT_NOTE'`, `'DEBIT_NOTE'`, `'PAYMENT_RECEIPT'`, `'OTHER'`), `processing_status` (`'UPLOADED'`, `'PROCESSING'`, `'EXTRACTION_FAILED'`, `'EXTRACTED'`, `'MATCHED'`, `'REVIEW_PENDING'`, `'APPROVED'`, `'REJECTED'`, `'POSTED'`, `'SYNCED'`, `'SYNC_FAILED'`), `is_duplicate` (bool).
- **`ASSUMPTIONS_AND_DECISIONS.md` (ADR-01 & ADR-02):**
  - Currency amounts must be rendered with exact decimal precision (never floating-point approximations), formatted for Indian numbering (`₹ 1,00,000.00`).
  - Financial Year defaults to April 1 to March 31 cycle (e.g. `'2024-2025'`).
- **`REQUIREMENT_GAP_ANALYSIS.md` (Lines 51–56):**
  - Support password-protected PDF bank statements via optional user decryption password during upload (processed in-memory, never persisted to disk or DB).

---

## 2. Logic Chain

1. **State Isolation & Interceptor Dependency:**
   - Because the backend enforces Row-Level Security (RLS) driven by headers `X-Organization-Id` and `X-Client-Business-Id`, the frontend cannot make operational API requests without an active organization and active client business in state.
   - Therefore, the client state store (Zustand) must store `activeOrganization` and `activeClientBusiness`, and the global HTTP client interceptor must inject these headers into every outgoing request.
   - Short-lived JWTs (15-min lifespan) dictate an automatic 401 response interceptor with token refresh queuing to prevent session drops during active document workflows.

2. **Workspace Segregation based on Organization Type:**
   - Freelancer accounts have a 1:1 relationship between organization and accounting subject. Rendering a client switcher for freelancers adds cognitive overhead and violates Persona 1 specifications (Rohan: single-click upload, simple P&L).
   - CA Firms manage $N$ client businesses. Thus, CA firm users need a multi-client portfolio table, a quick-switcher in the application header/sidebar, and a client onboarding creation modal.
   - The shell must dynamically adapt its navigation and workspace view based on `organization.organization_type`.

3. **Financial SaaS UI vs Generic Admin Dashboard:**
   - Standard admin templates use oversized rounded cards, pastel colors, and low-density layouts suitable for social media analytics but poor for financial accounting.
   - Indian financial compliance requires scanning hundreds of invoices, checking 15-digit GSTINs, 10-digit PANs, 64-char SHA-256 hashes, and tabular monetary amounts.
   - Therefore, the design system must enforce: tabular figures (`font-mono` / `tabular-nums`), dense padding (`py-2 px-3`), 1px structural borders (`border-slate-200 dark:border-slate-800`), neutral slate/zinc palettes with purposeful accent colors (emerald for credits/validations, rose for debits/errors, indigo for primary brand), and dark/light mode toggle.

4. **Multi-File Upload & Background Polling Lifecycle:**
   - Multi-file uploads may include mixed files (PDF, images, CSV, Excel) up to 50MB each.
   - Pre-validation in the browser (file type verification, size verification, and Web Crypto SHA-256 computation) catches duplicates and invalid formats before network transmission.
   - The API returns `202 Accepted` with a `batch_id` and list of documents in `PROCESSING` status.
   - TanStack Query must poll `GET /api/v1/documents?batch_id={batch_id}` at 2-second intervals with `refetchInterval` until all documents reach a terminal status (`EXTRACTED`, `EXTRACTION_FAILED`, or `UPLOADED`).

5. **Audit Logging Transparency:**
   - Because `ORIGINAL_REQUEST.md` mandates that every important action is recorded in the audit trail, the frontend must provide an Event Log / Audit Trail viewer displaying immutable audit records (`DOCUMENT_UPLOADED`, `DUPLICATE_DETECTED`, `PROCESSING_STARTED`, `PROCESSING_COMPLETED`).

---

## 3. Features Discovered

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | Auth | User Registration | Sign up with name, email, password, org name, and org type (`FREELANCER` vs `CA_FIRM`) | Full name, email, password, org name, org type, optional phone | Auth tokens, user profile, created organization | Validation errors (email exists, weak password, invalid org type) | `ORIGINAL_REQUEST.md` §3, `API_SPECIFICATION.md` §2.1 |
| 2 | Auth | User Login | Authenticate with email/password; stores JWT access token & rotating refresh token | Email, password | Access token (15-min), refresh token, user permissions, accessible orgs | 401 Unauthorized (`INVALID_CREDENTIALS`), lockouts | `API_SPECIFICATION.md` §2.1, `SECURITY_ARCHITECTURE.md` §1 |
| 3 | Auth | Token Refresh Flow | Automatic session renewal using refresh token when access token expires | Stored refresh token | New access token & rotated refresh token | 401 forces redirect to `/login` with session expiration toast | `SECURITY_ARCHITECTURE.md` §1, `ORIGINAL_REQUEST.md` §2 |
| 4 | Shell | App Shell Layout | Responsive desktop/mobile shell with collapsible Sidebar, Top Header, and Breadcrumbs | Navigation routes, active session state | Rendered layout container with theme & responsive states | Fallback to minimal shell if route unauthorized | `ORIGINAL_REQUEST.md` §3, `SYSTEM_ARCHITECTURE.md` §2.1 |
| 5 | Shell | Organization Switcher | Switch between user's organizations (e.g. personal vs firm) | User org selection | Updates `activeOrganization`, refreshes client business list | Rejection if user lacks membership | `ORIGINAL_REQUEST.md` §3, `SYSTEM_ARCHITECTURE.md` §4 |
| 6 | Shell | Client Business Switcher | Context switcher dropdown for CA firm users to switch active client books | Client business UUID selection | Updates `activeClientBusiness` in Zustand, sets `X-Client-Business-Id` header | Invalidation of client queries; warning on network fail | `API_SPECIFICATION.md` §2.1, `ORIGINAL_REQUEST.md` §3 |
| 7 | Workspace | Freelancer Workspace | Focused single-tenant dashboard showing upload dropzone, recent batches, statutory badges | Active freelancer client business | Single-business dashboard metrics and upload interface | Empty state when no documents uploaded yet | `REQUIREMENTS.md` FR-A02, `SYSTEM_ARCHITECTURE.md` §2.1 |
| 8 | Workspace | CA Firm Workspace | Multi-client portfolio table with client metrics, health status, and quick action buttons | List of client businesses under active org | Searchable, filterable client business data grid | Empty state with "Add your first client" CTA | `REQUIREMENTS.md` FR-A02, `API_SPECIFICATION.md` §2.1 |
| 9 | Workspace | Client Onboarding Modal | Modal form to register a new client business under current CA firm | Legal name, trade name, entity type, PAN, GSTIN, State Code, Composition flag, FY | Created `client_businesses` record; auto-selected as active | 400 Validation error (invalid PAN/GSTIN, duplicate PAN within org) | `DATABASE_DESIGN.md` §3.1, `ORIGINAL_REQUEST.md` §3 |
| 10 | Security | Role-Aware Navigation | Conditionally displays UI links and buttons based on user RBAC permissions | User role (`PARTNER`, `REVIEWER`, `STAFF`, `READ_ONLY`) | Filtered sidebar links and gated action buttons | Unauthorized routes redirected to 403 Forbidden page | `SECURITY_ARCHITECTURE.md` §3, `ORIGINAL_REQUEST.md` §3 |
| 11 | Upload | Multi-File Drag & Drop | Drag-and-drop dropzone supporting bulk selection of financial files | Native DragEvent or file picker selection | Array of staged File objects with preview metadata | Visual rejection on invalid file type or size > 50MB | `ORIGINAL_REQUEST.md` §4, `API_SPECIFICATION.md` §2.2 |
| 12 | Upload | Client-Side Pre-Validation | Validates MIME type, extension, size limit (50MB), and computes SHA-256 hash in browser | Staged `File` instances | Validation status, formatted file size, computed SHA-256 | Error badges on offending files, disables upload button | `REQUIREMENTS.md` FR-BC02, `API_SPECIFICATION.md` §2.2 |
| 13 | Upload | Password-Protected PDF Support | Optional input for password-protected bank statements (processed in-memory) | Decryption password string | Multipart field `pdf_password` sent to API | Backend error if password incorrect during processing | `REQUIREMENT_GAP_ANALYSIS.md` §3, `API_SPECIFICATION.md` §2.2 |
| 14 | Upload | Batch Progress & Status Badges | Live visual progress bar and status tags for batch upload execution | Upload progress events & `POST` response | `batch_id`, list of documents with IDs, filenames, statuses | Retry button on failed upload network chunks | `API_SPECIFICATION.md` §2.2, `ORIGINAL_REQUEST.md` §4 |
| 15 | Upload | Duplicate Detection Feedback | Visual callout and badge when an uploaded file is identified as a duplicate | Backend `is_duplicate: true` flag in upload response | Warning badge & alert: "Duplicate detected in this client scope" | Warning state (does not crash UI; highlights duplicate) | `ORIGINAL_REQUEST.md` §4, `DATABASE_DESIGN.md` §3.2 |
| 16 | Polling | Asynchronous Status Polling | TanStack Query hook polling document status until terminal state reached | `batch_id` or `document_id`, interval 2000ms | Real-time transitions: `PROCESSING` -> `EXTRACTED` or `EXTRACTION_FAILED` | Timeout fallback after 120s with manual refresh CTA | `ORIGINAL_REQUEST.md` §4, `API_SPECIFICATION.md` §2.2 |
| 17 | Audit | Audit Trail / Event Log Viewer | Component displaying immutable audit trail events for document operations | Filter query params (entity type, date range) | Table/feed of audit events with actor, IP, timestamp, delta | Empty state if no audit events recorded | `SECURITY_ARCHITECTURE.md` §5, `ORIGINAL_REQUEST.md` §4 |
| 18 | Settings | User Profile & Settings | View user profile, active organization subscription tier, client details, theme toggle | User session & organization data | Profile cards, subscription badge, appearance toggle | Form error validation on profile update | `ORIGINAL_REQUEST.md` §3, `DATABASE_DESIGN.md` §3.1 |
| 19 | UI System | Theme Management (Dark/Light) | Dark and light theme switcher with persistent user preference | Theme select (`light`, `dark`, `system`) | Applies `dark` class to `<html>`, stores in `localStorage` | Fallback to system OS preference | `ORIGINAL_REQUEST.md` §3, `SYSTEM_ARCHITECTURE.md` §2.1 |
| 20 | State | Toast & Error Envelope System | Standardized toast system parsing API standard error envelope and request IDs | API Error Response (`error_code`, `message`, `request_id`) | Non-blocking toast notification with copyable Request ID | Fallback to generic message if error payload non-standard | `API_SPECIFICATION.md` §1 |

---

## 4. Edge Cases

| # | Feature | Input | Observed Behavior |
|---|---------|-------|-------------------|
| 1 | File Upload Validation | File with uppercase extension e.g. `INVOICE.PDF` or `STATEMENT.XLSX` | Client-side validator must normalize extension to lowercase before validation; accept file without error. |
| 2 | File Upload Validation | File exceeding 50 MB (e.g. 52.4 MB scanned statement) | Immediate client-side validation failure; file marked with red danger badge: "File exceeds 50MB maximum limit"; upload button disabled. |
| 3 | File Upload Validation | Unsupported file type e.g. `.exe`, `.docx`, `.zip` (if ZIP disabled in slice) | Rejected with explicit error: "Unsupported file type. Only PDF, JPG, PNG, CSV, XLS, XLSX permitted." |
| 4 | Duplicate Upload | Same file uploaded twice within the same batch | Client-side SHA-256 pre-check detects identical hash; marks second file as "Duplicate in batch", preventing redundant network upload. |
| 5 | Duplicate Upload | File uploaded that already exists in database for this client business | Server accepts file, calculates SHA-256, matches existing hash, returns `is_duplicate: true` with status `UPLOADED`. Frontend shows warning tag. |
| 6 | Tenancy Header Missing | User clears `localStorage` or accesses direct link without selecting client business | HTTP interceptor detects missing `X-Client-Business-Id`; redirects to Client Switcher / Workspace selection screen before firing request. |
| 7 | Session Expiry | Access token expires (15 minutes) during an active document batch poll | HTTP response interceptor intercepts 401, issues `POST /api/v1/auth/refresh`, updates token in store, and replays polling request seamlessly. |
| 8 | Multiple Tabs Auth | User logs out in Tab A while Tab B is uploading documents | Tab B receives 401 on next request, refresh fails, auth store is cleared, and Tab B gracefully redirects to `/login`. |
| 9 | PAN & GSTIN Validation | User enters lowercase PAN `abcde1234f` or invalid format `12345ABCDE` | Client-side form auto-uppercases string; enforces regex `^[A-Z]{5}[0-9]{4}[A-Z]{1}$`; displays descriptive error if invalid. |
| 10 | GSTIN State Code Mismatch | User selects State "Karnataka (29)" but enters GSTIN starting with "27" (Maharashtra) | Client-side validation flags: "GSTIN state code (27) does not match selected state (Karnataka 29)." |
| 11 | Polling Worker Delays | Background Celery worker takes longer than 30s to process a large statement | Polling continues smoothly every 2s with animated spinner; UI does not freeze; status remains `PROCESSING` until complete. |
| 12 | Empty Client Portfolio | Newly registered CA Firm logs in with 0 client businesses | CA Workspace displays dedicated Empty State graphic: "No client businesses added yet", with primary action button "Create First Client Business". |
| 13 | Network Disconnection | Client drops offline during multi-file upload | Upload mutation catches network error; sets affected files to `FAILED`; triggers toast: "Network disconnected. Please check your internet connection." |
| 14 | Rapid Org Switching | User rapidly toggles between two CA firm organizations in switcher | TanStack Query cancels inflight queries (`abortSignal`); active client is reset to null; queries refetch cleanly under new `X-Organization-Id`. |

---

## 5. Exhaustive Specification Details across Focus Areas

### 5.1 Frontend Stack & Tooling Architecture

- **Project Foundation:**
  - Build Tool: **Vite 5.x** with `@vitejs/plugin-react` and TypeScript strict mode.
  - UI Library: **React 18.3+**.
  - Language: **TypeScript 5.x** (`"strict": true`, `"noImplicitAny": true`, `"strictNullChecks": true`).
  - CSS Framework: **Tailwind CSS 3.4+** with custom theme tokens, typography plugin, and dark mode class strategy (`darkMode: 'class'`).
  - Icons: **Lucide React** (high-precision financial icons: `Building2`, `Users`, `FileText`, `UploadCloud`, `CheckCircle2`, `AlertTriangle`, `RefreshCw`, `Shield`, `ArrowRightLeft`, `IndianRupee`).
  - Routing: **React Router v6** (`createBrowserRouter`) with layout wrappers and role-guarded route components.
  - Form Management: **React Hook Form** + **Zod** schema resolver.

- **Recommended Project Directory Structure:**
  ```
  frontend/
  ├── index.html
  ├── package.json
  ├── tsconfig.json
  ├── vite.config.ts
  ├── tailwind.config.ts
  ├── postcss.config.js
  └── src/
      ├── main.tsx
      ├── App.tsx
      ├── api/
      │   ├── client.ts             # Axios/fetch instance with auth & tenant headers, 401 retry
      │   ├── auth.api.ts           # login, register, refresh, me
      │   ├── clientBusiness.api.ts # list, create, switch
      │   ├── documents.api.ts      # upload, getStatus, listBatches
      │   └── audit.api.ts          # getAuditEvents
      ├── components/
      │   ├── common/               # Button, Input, Modal, Badge, Toast, EmptyState, Skeleton
      │   ├── shell/                # AppShell, Sidebar, Header, OrgSwitcher, ClientSwitcher
      │   ├── upload/               # Dropzone, FileQueue, BatchProgress, DuplicateWarning
      │   └── audit/                # AuditLogViewer, EventItem
      ├── pages/
      │   ├── auth/                 # LoginPage, RegisterPage
      │   ├── freelancer/           # FreelancerDashboardPage
      │   ├── ca-firm/              # CAFirmPortfolioPage
      │   ├── documents/            # DocumentUploadPage, BatchStatusPage
      │   ├── audit/                # AuditTrailPage
      │   └── settings/             # SettingsPage
      ├── stores/
      │   ├── auth.store.ts         # Zustand auth store (tokens, user, orgs, activeClient)
      │   └── ui.store.ts           # Theme (dark/light), sidebar collapse state
      ├── types/
      │   ├── auth.types.ts
      │   ├── clientBusiness.types.ts
      │   ├── document.types.ts
      │   └── audit.types.ts
      └── utils/
          ├── crypto.ts             # Web Crypto SHA-256 calculation
          ├── formatters.ts         # INR currency, Indian dates, file sizes
          └── validators.ts         # PAN regex, GSTIN regex
  ```

---

### 5.2 Styling & Design System Standards

The platform interface must convey the gravitas, precision, and density of enterprise financial software (resembling Stripe, Ramp, and Mercury).

1. **Color Palette & Theme Tokens:**
   - **Backgrounds:**
     - Light Mode: `bg-slate-50` (app canvas), `bg-white` (surfaces, cards, dialogs), `bg-slate-100` (subtle hover/inset).
     - Dark Mode: `dark:bg-slate-950` (app canvas), `dark:bg-slate-900` (surfaces, cards), `dark:bg-slate-850` (hover/inset).
   - **Borders & Dividers:**
     - Light: `border-slate-200` / `border-slate-300`.
     - Dark: `dark:border-slate-800` / `dark:border-slate-750`.
     - Crisp 1px borders on all cards, table headers, and inputs.
   - **Typography & Neutrals:**
     - Primary Text: `text-slate-900 dark:text-slate-100` (high contrast).
     - Secondary / Metadata: `text-slate-500 dark:text-slate-400`.
     - Disabled / Muted: `text-slate-400 dark:text-slate-600`.
   - **Functional Accent Colors:**
     - Primary Brand / Actions: Deep Navy / Indigo (`bg-indigo-600 hover:bg-indigo-700 text-white`).
     - Success / Credits / Verified: Emerald (`text-emerald-700 bg-emerald-50 border-emerald-200 dark:text-emerald-400 dark:bg-emerald-950/40 dark:border-emerald-800`).
     - Warning / Duplicate / Review: Amber (`text-amber-700 bg-amber-50 border-amber-200 dark:text-amber-400 dark:bg-amber-950/40 dark:border-amber-800`).
     - Danger / Debits / Failed: Rose / Crimson (`text-rose-700 bg-rose-50 border-rose-200 dark:text-rose-400 dark:bg-rose-950/40 dark:border-rose-800`).
     - Processing / Pending: Sky / Blue (`text-sky-700 bg-sky-50 border-sky-200 dark:text-sky-400 dark:bg-sky-950/40 dark:border-sky-800`).

2. **Typography & Tabular Numbers:**
   - Font family: Inter, system font stack.
   - Financial numbers, monetary figures, PAN, GSTIN, SHA-256 hashes, dates, and voucher numbers MUST use `font-mono` or `tabular-nums` so numbers align vertically in tables.
   - Hierarchy:
     - Headings: `text-lg font-semibold tracking-tight` (Page headers), `text-sm font-medium` (Section headers).
     - Body: `text-sm` (Default text).
     - Metadata & Badges: `text-xs font-medium`.

3. **Information Density & Spacing:**
   - Compact button heights (`h-8 text-xs` or `h-9 text-sm`).
   - Compact table cell padding: `py-2.5 px-3` (high density without visual clutter).
   - Form field spacing: `space-y-3`, with label `text-xs font-medium text-slate-700 dark:text-slate-300`.

---

### 5.3 Workspaces, Pages & Role-Aware Navigation

1. **Authentication Screens:**
   - **Login Page (`/login`):**
     - Clean, focused split-screen or centered card with platform badge.
     - Inputs: Email Address, Password (with toggle visibility), "Remember Me" checkbox.
     - Primary button: "Sign In".
     - Error banner displaying structured error message from API if credentials fail.
     - Footer: "Don't have an account? Register".
   - **Registration Page (`/register`):**
     - Inputs:
       - Full Name (`name`, text, required)
       - Email Address (`email`, email, required)
       - Password (`password`, minimum 8 characters, required)
       - Organization Name (`organization_name`, string, required)
       - Organization Type (`organization_type`: Radio / Segmented button: `FREELANCER` vs `CA_FIRM`, required)
       - Phone Number (optional)
     - Explanatory copy under org type:
       - *Freelancer:* "For individual consultants, developers, and sole proprietors managing their own accounts."
       - *CA Firm:* "For accounting practices and Chartered Accountants managing multiple client books."
     - Submit button: "Create Account & Workspace".

2. **Application Shell (`<AppShell>`):**
   - **Sidebar Component (`<Sidebar>`):**
     - Brand Header: Logo mark + "Accounting Intelligence".
     - **Organization Switcher (`<OrgSwitcher>`):**
       - Shows current Organization name and type pill (`Freelancer` or `CA Firm`).
       - Allows switching between organizations if user belongs to multiple.
     - **Client Business Switcher (`<ClientSwitcher>`):**
       - **When Org is CA Firm:** Searchable dropdown listing all client businesses. Selecting a client updates `activeClientBusiness` in Zustand and sets default header. Includes a quick action: "+ Add Client".
       - **When Org is Freelancer:** Static badge displaying the single business entity name and GSTIN.
     - **Navigation Links:**
       - Freelancer Workspace (Visible if org is Freelancer)
       - Client Portfolio (Visible if org is CA Firm)
       - Document Ingestion (`/documents` — Upload & Batches)
       - Audit Trail (`/audit-trail` — Event Log)
       - Settings (`/settings`)
     - **Sidebar Footer:**
       - User profile avatar / initials, name, and role badge.
       - Quick theme toggle (Sun / Moon).
       - Logout button with confirmation.
   - **Top Header (`<Header>`):**
     - Breadcrumb navigation: e.g. `Acme Advisory / Client: Acme Tech LLP / Document Upload`.
     - Active Client Pill: Legal Name, PAN, GSTIN status, FY `2024-2025`.
     - Quick Action Button: "+ Upload Documents".

3. **Freelancer Workspace (`/app/freelancer`):**
   - Single-business view for self-accounting.
   - Overview Cards:
     - Active Financial Year (`2024-2025`).
     - Documents Processed This Month.
     - Processing Status Queue.
   - Embedded Quick Upload Dropzone directly on the page for instant invoice/statement ingestion.
   - Recent Documents Table with status indicators.

4. **CA Firm Workspace (`/app/ca-firm`):**
   - Multi-client portfolio management dashboard.
   - Header with search bar (filters by client name, PAN, or GSTIN) and "+ New Client Business" button.
   - **Client Business Portfolio Table:**
     - Columns:
       1. `Client Legal Name` & `Trade Name`
       2. `Entity Type` (`Individual`, `Proprietorship`, `LLP`, `Pvt Ltd`)
       3. `PAN` (uppercase font-mono)
       4. `GSTIN` & `State Code` (badge showing Regular / Composition)
       5. `Financial Year` (e.g. `2024-2025`)
       6. `Documents Ingested`
       7. `Actions`: "Open Workspace", "Upload Files"
     - Clicking "Open Workspace" activates this client business and navigates to the document center.

5. **Client Onboarding Modal (`<NewClientModal>`):**
   - Form Fields:
     - `legal_name`: string (e.g., "Rohit Sharma Consulting LLP")
     - `trade_name`: string (optional, e.g., "RS Advisory")
     - `entity_type`: Select (`INDIVIDUAL_FREELANCER`, `PROPRIETORSHIP`, `PARTNERSHIP`, `LLP`, `PVT_LTD`)
     - `pan`: string (10 chars, regex `^[A-Z]{5}[0-9]{4}[A-Z]{1}$`)
     - `primary_gstin`: string (optional, 15 chars, regex `^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$`)
     - `gst_registered_state_code`: Select from Indian States dropdown (01 to 37)
     - `composition_scheme`: Switch / Checkbox
     - `current_financial_year`: Text, default `'2024-2025'`
   - Validation & Submission:
     - Real-time regex check for PAN and GSTIN.
     - Matching validation between GSTIN prefix (first 2 digits) and selected state code.
     - Submits `POST /api/v1/clients`. On success, adds to client list, sets as active, and closes modal.

6. **Role-Aware Navigation Matrix:**
   - RBAC rules from `SECURITY_ARCHITECTURE.md` enforced via client-side helper `hasPermission(role, permission)`:
     - `doc:upload`: Enabled for all authenticated roles (`Freelancer Owner`, `CA Firm Partner`, `Staff Accountant`, `Client Read-Only`).
     - `doc:view`: Enabled for all roles.
     - `client:create`: Enabled only for `CA Firm Partner` and `Freelancer Owner`.
     - `audit:view`: Enabled for `CA Firm Partner`, `Staff Accountant`, `Freelancer Owner`.
   - UI elements hidden or disabled with tooltips when current user lacks permission.

---

### 5.4 Vertical Slice UI: Multi-File Document Upload & Processing

The document ingestion UI is the primary operational vertical slice for Phase 1.

1. **Upload Modal / Screen (`<DocumentUploadView>`):**
   - Active Client Business confirmation banner: Displays the client business name and PAN to ensure files are ingested into the correct tenant boundary.
   - **Multi-File Dropzone (`<FileDropzone>`):**
     - Drag-over state changes border from dashed `border-slate-300` to solid `border-indigo-500 bg-indigo-50/50 dark:bg-indigo-950/20`.
     - Accepted formats: `.pdf`, `.jpg`, `.jpeg`, `.png`, `.csv`, `.xls`, `.xlsx`.
     - Max file size: `50 MB`.
     - Dropzone text: *"Drag and drop financial documents here, or browse files"*.
     - Format hint: *"Supports Bank Statements (PDF/Excel/CSV), Invoices, and Expense Receipts up to 50MB per file."*
   - **Upload Configuration:**
     - Category Selector: Dropdown with options:
       - `AUTO_DETECT` (Default — recommended)
       - `BANK_STATEMENT`
       - `SALES_INVOICE`
       - `PURCHASE_INVOICE`
       - `EXPENSE_RECEIPT`
     - Password-Protected PDF toggle:
       - Checkbox: "One or more bank statements are password protected"
       - Reveals password input: "Decryption Password (processed in-memory, never stored)"

2. **Pre-Upload Staging Queue (`<StagedFileList>`):**
   - Before firing the network request, staged files are listed in a compact review table:
     - File name and extension icon.
     - File size in KB/MB.
     - Computed SHA-256 hash (short preview: `e3b0c442...b855`).
     - Validation Status:
       - Valid (Green checkmark).
       - Exceeds size limit (Red error tag: "File > 50MB").
       - Unsupported extension (Red error tag: "Unsupported format").
       - Duplicate in batch (Amber warning tag: "Same file selected twice").
     - Action: Remove file from queue button.
   - Total batch summary: e.g. "5 files staged (14.2 MB total)".
   - Upload action button: "Upload 5 Documents". Disabled if any file has validation errors.

3. **Upload Execution & Batch Progress:**
   - Multi-file `multipart/form-data` POST to `/api/v1/documents/upload` containing:
     - `files`: File[] (binary)
     - `category`: string
     - `pdf_password`: string (optional)
     - Headers: `X-Organization-Id`, `X-Client-Business-Id`
   - Progress bar: Displays cumulative upload progress (0% to 100%) via `onUploadProgress`.

4. **Post-Upload Batch Processing & Polling:**
   - Upon receiving `202 Accepted` with `batch_id` and array of `uploaded_files`:
     ```json
     {
       "success": true,
       "batch_id": "bch_01HP389AB01",
       "uploaded_files": [
         {
           "document_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
           "file_name": "HDFC_Current_Statement_Oct2024.pdf",
           "sha256_hash": "e3b0c442...",
           "status": "PROCESSING",
           "is_duplicate": false
         }
       ]
     }
     ```
   - Transition to **Batch Processing Status Card**:
     - Displays `Batch ID: bch_...`.
     - Table of files in the batch:
       - File Name
       - SHA-256 Hash
       - Status Badge:
         - `UPLOADED` (Blue, clock icon)
         - `PROCESSING` (Indigo, spinning sync icon)
         - `EXTRACTED` (Emerald, check icon)
         - `EXTRACTION_FAILED` (Rose, alert icon)
         - `DUPLICATE` (Amber, copy icon)
     - Duplicate Warning Banner:
       - If `is_duplicate: true`, displays warning banner: *"Warning: [Filename] matches the cryptographic hash of an existing file in this business scope. Duplicate files are flagged to prevent double-entry errors."*
   - **Background Polling:**
     - Automatically polls `GET /api/v1/documents?batch_id={batch_id}` every 2000ms.
     - When all documents reach a terminal status (`EXTRACTED`, `EXTRACTION_FAILED`, or `UPLOADED` with `is_duplicate: true`), polling ceases.
     - Success banner: "Batch processing complete. [N] documents ready for review."

5. **Audit Trail Viewer Component (`<AuditLogViewer>`):**
   - Displays the immutable audit records required by Phase 1.
   - Columns:
     1. `Timestamp` (Formatted as `DD MMM YYYY, HH:mm:ss` + relative time `2 mins ago`)
     2. `Event Type` (Badges: `DOCUMENT_UPLOADED`, `DOCUMENT_HASHED`, `DUPLICATE_DETECTED`, `PROCESSING_STARTED`, `PROCESSING_COMPLETED`)
     3. `Actor` (User email & IP address)
     4. `Target Entity` (`DOCUMENT`, showing Document UUID)
     5. `Details` (Collapsible JSON snippet showing filename, file size, SHA-256, and status)
   - Filters: By Event Type and Date Range.

---

### 5.5 State Management & API Integration Architecture

1. **Auth Store (`useAuthStore` via Zustand):**
   ```typescript
   interface UserProfile {
     id: string;
     email: string;
     fullName: string;
     role: 'FREELANCER_OWNER' | 'CA_FIRM_PARTNER' | 'STAFF_ACCOUNTANT' | 'CLIENT_READ_ONLY';
   }

   interface Organization {
     id: string;
     name: string;
     organizationType: 'FREELANCER' | 'CA_FIRM' | 'ENTERPRISE_PRACTICE';
     subscriptionTier: 'FREE_TRIAL' | 'SILVER' | 'GOLD' | 'PLATINUM';
     trialEndsAt: string | null;
   }

   interface ClientBusiness {
     id: string;
     organizationId: string;
     legalName: string;
     tradeName?: string;
     entityType: 'INDIVIDUAL_FREELANCER' | 'PROPRIETORSHIP' | 'PARTNERSHIP' | 'LLP' | 'PVT_LTD';
     pan: string;
     primaryGstin?: string;
     gstRegisteredStateCode: string;
     compositionScheme: boolean;
     currentFinancialYear: string;
   }

   interface AuthState {
     user: UserProfile | null;
     accessToken: string | null;
     refreshToken: string | null;
     organizations: Organization[];
     activeOrganization: Organization | null;
     clientBusinesses: ClientBusiness[];
     activeClientBusiness: ClientBusiness | null;
     isAuthenticated: boolean;
     isLoading: boolean;
     
     // Actions
     setAuth: (payload: { user: UserProfile; accessToken: string; refreshToken: string; organizations: Organization[] }) => void;
     setActiveOrganization: (orgId: string) => void;
     setClientBusinesses: (clients: ClientBusiness[]) => void;
     setActiveClientBusiness: (clientId: string) => void;
     updateTokens: (accessToken: string, refreshToken?: string) => void;
     logout: () => void;
   }
   ```
   - Persisted via Zustand `persist` middleware in `localStorage` (excluding sensitive in-memory secrets).

2. **HTTP API Client & Interceptors (`api/client.ts`):**
   - **Request Interceptor:**
     - Injects `Authorization: Bearer ${accessToken}` if token exists.
     - Injects `X-Organization-Id: ${activeOrganization.id}` if active organization selected.
     - Injects `X-Client-Business-Id: ${activeClientBusiness.id}` if active client business selected.
   - **Response Interceptor:**
     - **401 Handling:** Maintains a request retry queue. When a 401 occurs, initiates a single refresh request to `/api/v1/auth/refresh`. Upon success, retries queued requests with new token. If refresh fails, purges auth store and redirects to `/login`.
     - **Error Envelope Parsing:** Standardizes error responses:
       ```typescript
       export interface ApiErrorResponse {
         success: false;
         error_code: string;
         message: string;
         details?: Record<string, any>;
         request_id: string;
       }
       ```
       Passes typed error to TanStack Query and UI toast.

3. **TanStack Query Hooks:**
   - `useClients(orgId)`:
     - Query key: `['clients', orgId]`.
     - Fetches `/api/v1/workspaces/clients`.
   - `useCreateClient()`:
     - Mutation for `POST /api/v1/clients`.
     - Invalidates `['clients', orgId]`.
     - Automatically activates the newly created client in `useAuthStore`.
   - `useUploadDocuments()`:
     - Mutation for `POST /api/v1/documents/upload`.
     - Sends `multipart/form-data`.
   - `useBatchStatus(batchId)`:
     - Query key: `['documents', 'batch', batchId]`.
     - Enabled when `!!batchId`.
     - `refetchInterval: (query) => isBatchFinished(query.state.data) ? false : 2000`.
   - `useAuditEvents(clientBusinessId)`:
     - Query key: `['audit-events', clientBusinessId]`.
     - Fetches `/api/v1/audit/events`.

4. **UI State, Toast System & Empty States:**
   - **Toast System:** Accessible via `toast.success()`, `toast.error()`, `toast.warning()`. Displays `message` and copyable `request_id` for debugging financial discrepancies.
   - **Loading Skeletons:**
     - `<TableSkeleton rows={5} columns={6} />` for client portfolio and document tables.
     - `<CardSkeleton />` for dashboard overview cards.
   - **Empty States:**
     - Dedicated `<EmptyState />` component with custom illustrations, clear descriptive text, and a primary CTA button.

---

## 6. Caveats

1. **AI Extraction Staging Limitation:**
   - Per `ORIGINAL_REQUEST.md` §4: Extraction remains a clearly defined pending-processing stage for Phase 1. The frontend displays `PROCESSING`, `EXTRACTED`, or `EXTRACTION_FAILED` statuses, but side-by-side OCR invoice line-item editing and deep double-entry voucher generation are staged for subsequent implementation phases.
2. **GST Filing Out of Scope:**
   - As affirmed in `PRODUCT_SCOPE.md` §4, automated GST portal filing and OTP/DSC submissions are explicitly out-of-scope for Phase 1.
3. **Local Storage of Passwords Prohibited:**
   - Password-protected PDF bank statements accept a decryption password on upload. This password must remain strictly in transient React component state during submission and must NEVER be saved to `localStorage`, Zustand persisted storage, or logs.
4. **Desktop Sync Daemon:**
   - TallyPrime local desktop sync daemon (port 9000) is optional and scheduled post-foundation; Phase 1 UI focuses on the web application shell and document upload slice.

---

## 7. Conclusion

Phase 1 Frontend specifications are fully extracted, unambiguous, and mathematically aligned with the authoritative architecture:
1. **Tooling & Stack:** React 18, TypeScript 5, Vite, Tailwind CSS, TanStack Query v5, Zustand.
2. **Design Language:** High-density financial SaaS design using tabular numerals, slate/indigo/emerald tokens, 1px structural borders, and dark/light themes.
3. **Core Workspaces:** Dual-mode architecture supporting Freelancers (single workspace) and CA Firms (multi-client portfolio, client switcher, client onboarding modal), guarded by role-aware permissions.
4. **Vertical Slice:** End-to-end multi-file document upload supporting PDF, JPG, PNG, CSV, XLS, XLSX up to 50MB, client-side SHA-256 pre-validation, duplicate warning callouts, live batch status polling every 2s, and an immutable audit trail viewer.
5. **State & Tenancy:** Zustand auth store coordinating JWT tokens, active organization, and active client business, with automatic header injection (`X-Organization-Id`, `X-Client-Business-Id`) and 401 refresh token rotation.

The frontend is ready for immediate modular implementation.

---

## 8. Verification Method

To verify the implementation independently once built:
1. **Type & Build Verification:**
   - Execute `npm run build` / `tsc --noEmit` to verify 100% TypeScript compile-time type safety.
   - Execute `npm run lint` for ESLint verification.
2. **Unit & Component Testing (Vitest + React Testing Library):**
   - Test client-side SHA-256 calculation with known test strings/files.
   - Test file size and extension pre-validation logic (validating rejection of >50MB and non-supported files).
   - Test PAN (`^[A-Z]{5}[0-9]{4}[A-Z]{1}$`) and GSTIN regex validation rules.
   - Test Zustand auth store token hydration, active org switching, and active client selection.
   - Test HTTP interceptor injection of `X-Organization-Id` and `X-Client-Business-Id`.
   - Test 401 response interception and token refresh replay.
3. **End-to-End Workflow Verification (Playwright / Manual Dev Server):**
   - Start frontend: `npm run dev`.
   - Navigate to `/register`: register a `CA_FIRM` user; verify redirection to CA Firm console.
   - Open Client Onboarding Modal: create a new client business with valid PAN and GSTIN; verify client appears in portfolio and becomes active in header.
   - Navigate to Document Upload: drag-and-drop multiple files (PDF, CSV, XLSX); verify pre-upload table displays file sizes and SHA-256 hashes.
   - Click "Upload Documents": verify `multipart/form-data` request includes `X-Organization-Id` and `X-Client-Business-Id` headers; verify `batch_id` is received.
   - Verify live polling transitions document status from `PROCESSING` to `EXTRACTED` or `UPLOADED`.
   - Test duplicate upload: upload the same file again; verify duplicate warning badge is displayed.
   - Inspect Audit Trail page: verify `DOCUMENT_UPLOADED` and `DOCUMENT_HASHED` events are rendered with timestamp, actor email, and metadata.
