# Health Supply Chain Platform — RBAC & Authentication Backend

Multi-tenant health supply chain backend for India built with **Python 3.11+**, **FastAPI**, **SQLAlchemy 2.x**, **Pydantic v2**, **PostgreSQL 16**, **Redis 7**, and **Alembic**.

Provides multi-tenant geographic isolation (National, State, District, PHC), strict Role-Based Access Control (RBAC), revocable JWT access & refresh tokens, and tamper-evident audit logging.

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

| Role | Geographic Scope | Email |
| :--- | :--- | :--- |
| **Super Admin** | Platform (Bypass) | `superadmin@hsc.gov.in` |
| **National Viewer** | National | `national.viewer@hsc.gov.in` |
| **State Approver** | Jharkhand (JH) | `state.approver.jh@hsc.gov.in` |
| **District Approver** | Ramgarh (JH) | `district.approver.ram@hsc.gov.in` |
| **District Approver** | Ranchi (JH) | `district.approver.ran@hsc.gov.in` |
| **PHC Operator** | Patratu PHC (Ramgarh) | `phc.operator.pat_phc@hsc.gov.in` |
| **PHC Approver** | Patratu PHC (Ramgarh) | `phc.approver.pat_phc@hsc.gov.in` |
