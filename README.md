# Health Supply Chain Platform — RBAC & Authentication Backend

Multi-tenant health supply chain backend for India built with **Python 3.11+**, **FastAPI**, **SQLAlchemy 2.x**, **Pydantic v2**, **PostgreSQL 16**, **Redis 7**, and **Alembic**.

Provides multi-tenants geographic isolation (National, State, District, PHC), strict Role-Based Access Control (RBAC), revocable JWT access & refresh tokens, and tamper-evident audit logging.

---

## Architecture & Tenancy Model

### Geographic Multi-Tenancy

1. **Platform (Super Admin)**: Bypasses all geographic filtering, manages permissions and system-level operations.
2. **National**: National-level visibility across all states and districts.
3. **State**: Tenanted to `state_id`. Can access and manage entities within their designated state.
4. **District**: Tenanted to `district_id`. Users from District A (e.g. Ramgarh) are strictly prevented from querying or altering data in District B (e.g. Ranchi).
5. **PHC**: Tenanted to `facility_id` (PHC/CHC). Operators and Approvers can only manage inventory and operations within their facility.

### Security Guarantees

- **Access Tokens**: Short-lived (15 minutes), signed with HMAC-SHA256.
- **Refresh Tokens**: Long-lived (7 days), stored hashed (SHA-256) in the database, revocable immediately upon logout.
- **Password Security**: Passlib with bcrypt, minimum 8 characters.
- **Audit Logging**: Every login, logout, permission denial, and scoped data access is written to `audit_logs` without PII.
- **Permission Checking**: Strictly enforced via `Depends(require_permission('permission_name'))`.

---

## Backend Directory Structure (`app/`)

The backend follows a layered architecture. A request flows top-to-bottom through these layers, and each layer only talks to the one directly below it:

```
main.py            Controller entry  →  api/v1/*      Controllers (routes)
                                            ↓
                                        api/deps.py    Cross-cutting auth/RBAC guards
                                            ↓
                                        schemas/*      Request/response validation (DTOs)
                                            ↓
                                        services/*     Business logic ("what should happen")
                                            ↓
                                        repositories/*  Data access ("how to fetch/write it")
                                            ↓
                                        models/*        ORM tables (SQLAlchemy) → PostgreSQL
                                            ↑
                                        core/*          Config, DB engine, security primitives
                                            (used by every layer above)
```

| Directory / File                 | Purpose                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| :------------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `app/main.py`                    | Application entry point. Creates the `FastAPI` app, registers middleware (CORS), mounts versioned routers (`app.include_router`), and defines the `/health` liveness endpoint. This is what Uvicorn boots (`app.main:app`).                                                                                                                                                                                                                         |
| `app/core/`                      | Cross-cutting infrastructure shared by every layer — **not** business logic.                                                                                                                                                                                                                                                                                                                                                                        |
| `app/core/config.py`             | Loads and validates environment variables (`.env`) into a typed `Settings` object (DB/Redis credentials, JWT secret & expiry, rate limits). The single source of truth for configuration.                                                                                                                                                                                                                                                           |
| `app/core/database.py`           | Creates the SQLAlchemy `engine` and `SessionLocal` factory from `settings`, declares the declarative `Base` that every model inherits from, portable `GUID`/`JSONType` column types (Postgres vs SQLite), and the `get_db()` FastAPI dependency that yields one DB session per request.                                                                                                                                                             |
| `app/core/security.py`           | Cryptographic helpers only: password hashing/verification (bcrypt), JWT access-token creation/decoding, and refresh-token generation/hashing. No DB or FastAPI imports — pure functions.                                                                                                                                                                                                                                                            |
| `app/api/`                       | The **controller layer**. Turns HTTP requests into calls on the service layer and shapes the HTTP response. Contains no business rules or SQL.                                                                                                                                                                                                                                                                                                      |
| `app/api/deps.py`                | Reusable FastAPI `Depends()` guards: `get_current_user` (decodes the JWT and loads the `User`), `require_permission(...)`, `require_scope(...)`, `require_scope_tenancy(...)`. These enforce authentication, RBAC, and geographic multi-tenancy before a route body ever runs.                                                                                                                                                                      |
| `app/api/v1/auth.py`             | The auth controller. Declares the actual `/api/v1/auth/*` routes (`/login`, `/refresh`, `/logout`, `/me`, plus RBAC test routes). Each route only validates input via a schema, calls `AuthService`, and returns a response schema.                                                                                                                                                                                                                 |
| `app/schemas/`                   | **Pydantic DTOs** — define the JSON shape of API requests/responses (validation + serialization). Independent of the DB schema so the API contract can evolve separately from the tables.                                                                                                                                                                                                                                                           |
| `app/schemas/auth.py`            | `LoginRequest/Response`, `RefreshRequest/Response`, `LogoutRequest/Response`.                                                                                                                                                                                                                                                                                                                                                                       |
| `app/schemas/user.py`            | `UserCreate`, `UserResponse`, `UserProfileResponse` — what a "user" looks like over the wire.                                                                                                                                                                                                                                                                                                                                                       |
| `app/schemas/rbac.py`            | `RoleResponse`, `PermissionResponse` — read-only projections of RBAC data.                                                                                                                                                                                                                                                                                                                                                                          |
| `app/schemas/audit.py`           | `AuditLogCreate`, `AuditLogResponse` — input/output shape for audit events.                                                                                                                                                                                                                                                                                                                                                                         |
| `app/services/`                  | The **business logic layer**. Orchestrates one or more repositories, enforces business rules, and is the only place that decides _what_ should happen (e.g. "reject login if user inactive", "strip PII before logging"). Routes call services; services never import FastAPI/`Request` objects.                                                                                                                                                    |
| `app/services/auth_service.py`   | `AuthService.authenticate/refresh_access_token/logout` — verifies credentials, issues/rotates/revokes JWT + refresh-token pairs, and triggers audit logging.                                                                                                                                                                                                                                                                                        |
| `app/services/audit_service.py`  | `AuditService.log_event` — sanitizes metadata (removes email/name/phone keys) before persisting via `AuditRepository`.                                                                                                                                                                                                                                                                                                                              |
| `app/repositories/`              | The **data-access layer**. Wraps raw SQLAlchemy queries (`select`, `insert`, filters) for a given model. Exists so services don't write SQL directly and so query logic (e.g. geographic scope filtering) is defined once and reused everywhere. This is why it's separate from `models/` and `schemas/`: models define _what a table looks like_, schemas define _what the API looks like_, repositories define _how to query/persist_ the models. |
| `app/repositories/user_repo.py`  | CRUD for `User`/`RefreshToken`, `is_super_admin()`, and `apply_scope_filter()` (the shared multi-tenancy query filter).                                                                                                                                                                                                                                                                                                                             |
| `app/repositories/audit_repo.py` | Insert and list operations for `AuditLog`.                                                                                                                                                                                                                                                                                                                                                                                                          |
| `app/models/`                    | **SQLAlchemy ORM models** — the actual source of truth for the database schema. Each class here maps 1:1 to a Postgres table; Alembic reads `Base.metadata` (populated via `app/models/__init__.py`) to autogenerate migrations.                                                                                                                                                                                                                    |
| `app/models/user.py`             | `User` table + `ScopeLevelEnum` (platform/national/state/district/phc).                                                                                                                                                                                                                                                                                                                                                                             |
| `app/models/rbac.py`             | `Role`, `Permission` tables and their many-to-many junction tables (`role_permissions`, `user_roles`).                                                                                                                                                                                                                                                                                                                                              |
| `app/models/geography.py`        | `State` → `District` → `Facility` hierarchy that `scope_id` values point into.                                                                                                                                                                                                                                                                                                                                                                      |
| `app/models/token.py`            | `RefreshToken` table — stores only the SHA-256 hash of each refresh token.                                                                                                                                                                                                                                                                                                                                                                          |
| `app/models/audit.py`            | `AuditLog` table — append-only security/operational event log.                                                                                                                                                                                                                                                                                                                                                                                      |

### Where things live, at a glance

- **Table/schema definitions (DDL source of truth):** `app/models/*` (SQLAlchemy) → migrated to Postgres via `alembic/versions/*`.
- **DB connection & session lifecycle:** `app/core/database.py` (engine/session), configured from `app/core/config.py` (env vars).
- **Why repositories exist alongside models/schemas:** models describe table columns, schemas describe API JSON shape, repositories describe the _queries_ used to read/write those tables — keeping SQL out of services and controllers.

---

## Quickstart with Docker Compose

### 1. Configure Environment

```bash
cp .env.example .env
```

### 2. Launch Services

Run the API, PostgreSQL 16, and Redis 7 containers:

```bash
docker-compose up --build
```

This automatically runs Alembic migrations, executes `seed.py` (populating geography and 24 role accounts), and boots the Uvicorn server on port `8000`.

### 3. Interactive Documentation

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## Local Development (Without Docker)

### 1. Create Virtualenv & Install Dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Run Database Migrations

```bash
alembic upgrade head
```

### 3. Seed Database

```bash
python seed.py
# Or reset and reseed:
python seed.py --reset
```

### 4. Run Development Server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Running Automated Tests

Run the complete test suite covering all 10 RBAC and tenancy scenarios:

```bash
pytest -v tests/test_auth.py
```

---

## Pre-Seeded Test Credentials

All seeded users share the password: `Test@123`

| Role                  | Geographic Scope      | Email                              |
| :-------------------- | :-------------------- | :--------------------------------- |
| **Super Admin**       | Platform (Bypass)     | `superadmin@hsc.gov.in`            |
| **National Viewer**   | National              | `national.viewer@hsc.gov.in`       |
| **State Approver**    | Jharkhand (JH)        | `state.approver.jh@hsc.gov.in`     |
| **District Approver** | Ramgarh (JH)          | `district.approver.ram@hsc.gov.in` |
| **District Approver** | Ranchi (JH)           | `district.approver.ran@hsc.gov.in` |
| **PHC Operator**      | Patratu PHC (Ramgarh) | `phc.operator.pat_phc@hsc.gov.in`  |
| **PHC Approver**      | Patratu PHC (Ramgarh) | `phc.approver.pat_phc@hsc.gov.in`  |
