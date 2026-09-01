# NetraGraph — PostgreSQL Database & Gmail OTP Authentication Architecture
**Version**: 2.5.0 (Production-Grade Security & Relational Storage Layer)  
**Date**: 2026-09-01  
**Status**: VALIDATED & OPERATIONAL  
**Core Guarantee**: Production Models A–E Untouched | Zero Model Weights Modified | Zero Hardcoded Secrets

---

## 1. System Architecture Overview

NetraGraph integrates a production-grade PostgreSQL relational database and cryptographic Gmail OTP authentication layer alongside its Neo4j knowledge graph engine.

```mermaid
flowchart TD
    subgraph Client ["Frontend Client (React/Vite)"]
        UI[Officer Login Screen]
        Dash[Command Center / Dashboard]
    end

    subgraph AuthLayer ["Authentication & Gateway"]
        AuthAPI["POST /api/auth/request-otp\nPOST /api/auth/verify-otp\nPOST /api/auth/refresh\nPOST /api/auth/logout"]
        Dep["RBAC Middleware & JWT Verifier"]
    end

    subgraph Services ["Core Security Services"]
        OTPService["OtpService (Crypto SHA-256 + Salt)"]
        AuthService["AuthService (JWT + Refresh Rotation)"]
        EmailProv["EmailProvider (SMTP / Gmail TLS)"]
    end

    subgraph Storage ["Persistent Data Layer"]
        PG[(PostgreSQL Database)]
        Neo[(Neo4j Knowledge Graph)]
    end

    UI -->|1. Submit Gmail| AuthAPI
    AuthAPI -->|2. Check Rate Limits| OTPService
    OTPService -->|3. Dispatch Code| EmailProv
    EmailProv -->|4. Deliver Single-Use Code| UI
    UI -->|5. Submit 6-Digit OTP| AuthAPI
    AuthAPI -->|6. Verify & Issue Tokens| AuthService
    AuthService -->|7. Persist User & Session| PG
    AuthService -->|8. Issue JWT Access & HttpOnly Cookie| Dash
    Dash -->|9. Authenticated API Access| Dep
    Dep -->|10. Authorize Role| PG
    Dep -->|11. Graph Analytics| Neo
```

---

## 2. PostgreSQL Relational Database Schema

### Logical Entities & Tables

```mermaid
erDiagram
    USERS ||--o{ USER_ROLES : has
    ROLES ||--o{ USER_ROLES : assigned_to
    USERS ||--o{ AUTH_SESSIONS : owns
    USERS ||--o{ REFRESH_TOKENS : owns
    AUTH_SESSIONS ||--o{ REFRESH_TOKENS : creates
    USERS ||--o{ AUDIT_LOGS : logs

    USERS {
        uuid id PK
        string email UK
        boolean email_verified
        string display_name
        string avatar_url
        string status
        timestamp created_at
        timestamp updated_at
        timestamp last_login_at
    }

    ROLES {
        uuid id PK
        string name UK
        string description
    }

    USER_ROLES {
        uuid user_id FK
        uuid role_id FK
        timestamp assigned_at
    }

    OTP_VERIFICATIONS {
        uuid id PK
        string email
        string otp_hash
        string salt
        timestamp expires_at
        int attempts_count
        int max_attempts
        boolean is_used
        string ip_address
        timestamp created_at
    }

    AUTH_SESSIONS {
        uuid id PK
        uuid user_id FK
        string session_token_hash UK
        string ip_address
        string user_agent
        timestamp expires_at
        boolean is_revoked
        timestamp created_at
        timestamp last_accessed_at
    }

    REFRESH_TOKENS {
        uuid id PK
        uuid user_id FK
        uuid session_id FK
        string token_hash UK
        timestamp expires_at
        boolean is_revoked
        string replaced_by_token_hash
        timestamp created_at
    }

    LOGIN_ATTEMPTS {
        uuid id PK
        string email
        string ip_address
        boolean success
        timestamp attempted_at
    }

    AUDIT_LOGS {
        uuid id PK
        uuid user_id FK
        string event_type
        string ip_address
        string user_agent
        json metadata_json
        timestamp created_at
    }
```

---

## 3. Passwordless Gmail OTP Flow & Security Guarantees

1. **Email Domain Filtering**:
   - Accepts `@gmail.com` and `@googlemail.com` by default (configurable via `ALLOWED_EMAIL_DOMAINS`).
   - Normalizes email addresses (lowercasing, whitespace trimming).
2. **Cryptographic OTP Generation**:
   - Generated via Python `secrets.choice("0123456789")` (CSPRNG, zero PRNG bias).
   - 6-digit numeric code.
   - Salted with 16-byte random salt and hashed with SHA-256 before storage.
   - **Never stored in plaintext, never logged, never returned in API responses**.
3. **Single-Use & Invalidation**:
   - When a new OTP is requested, all prior active OTPs for that email are marked `is_used = True`.
   - Verified OTP is immediately marked `is_used = True` inside an atomic transaction.
4. **Rate Limiting & Abuse Prevention**:
   - 60-second cooldown between consecutive OTP requests for the same email.
   - 15 requests/hour cap per IP address.
   - Maximum 5 verification attempts per OTP code before lockout.
   - Generic response for non-existent/invalid accounts: *"If eligible, an authentication OTP has been dispatched to your email."*

---

## 4. Role-Based Access Control (RBAC)

Pre-seeded roles in the database:
- **`ADMIN`**: Full administrative access to dockets, system telemetry, audit logs, and user roles.
- **`INVESTIGATOR`**: Lead Cyber Investigator with case docket management and Section 65B electronic evidence clearance.
- **`ANALYST`**: Intelligence Analyst with graph exploration and link query clearance.
- **`VIEWER`**: Read-only access to operational dashboards.

FastAPI Dependency Usage:
```python
from app.auth.dependencies import get_current_user, require_role

# Requires any active authenticated officer
@router.get("/cases")
async def get_cases(user = Depends(get_current_user)):
    ...

# Requires INVESTIGATOR or ADMIN role
@router.post("/cases")
async def create_case(user = Depends(require_role(["INVESTIGATOR", "ADMIN"]))):
    ...
```

---

## 5. Environment Variables Reference

A template is provided in [`.env.example`](file:///c:/Users/KIIT/Desktop/NetraGraph/.env.example):

| Variable | Description | Default / Example |
|---|---|---|
| `DATABASE_URL` | PostgreSQL Async Connection String | `postgresql+asyncpg://postgres:PASSWORD@localhost:5432/netragraph` |
| `DATABASE_SYNC_URL` | PostgreSQL Synchronous Connection String (Alembic) | `postgresql://postgres:PASSWORD@localhost:5432/netragraph` |
| `DB_POOL_SIZE` | SQLAlchemy connection pool size | `10` |
| `DB_MAX_OVERFLOW` | Maximum overflow connections | `20` |
| `JWT_SECRET_KEY` | Secret key for signing JWT tokens | Strong 32-byte secret |
| `JWT_ALGORITHM` | JWT signing algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifespan | `60` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Rotating refresh token lifespan | `30` |
| `OTP_EXPIRY_SECONDS` | OTP lifespan | `300` (5 minutes) |
| `OTP_COOLDOWN_SECONDS` | Cooldown between OTP requests | `60` |
| `OTP_MAX_ATTEMPTS` | Maximum failed verification attempts | `5` |
| `ALLOWED_EMAIL_DOMAINS` | Allowed email domains (comma-separated) | `gmail.com,googlemail.com` |
| `EMAIL_PROVIDER` | Email backend (`smtp`, `console`, `mock`) | `smtp` |
| `SMTP_HOST` | SMTP server host | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP server port | `587` |
| `SMTP_USERNAME` | Gmail service account address | `officer.service@gmail.com` |
| `SMTP_PASSWORD` | Gmail 16-character App Password | `xxxx xxxx xxxx xxxx` |
| `SMTP_FROM` | Sender address | `netragraph-security@gmail.com` |
| `COOKIE_SECURE` | Set True for HTTPS production environments | `False` (dev) / `True` (prod) |

---

## 6. Local Development & PostgreSQL Setup

### Starting PostgreSQL with Docker
```bash
docker run --name netragraph-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=netragraph \
  -p 5432:5432 -d postgres:16-alpine
```

### Running Alembic Database Migrations
```bash
# Apply migrations to PostgreSQL
cd backend
alembic upgrade head
```

### Starting the Backend
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Running Test Suites
```bash
# 1. Auth & Database Security Tests (22/22)
python -m pytest backend/tests/test_auth_and_database.py -v

# 2. Core Regression Tests (14/14)
python scripts/test_regression.py

# 3. Full Backend Tests (112/112)
python -m pytest backend/tests/

# 4. ML & Research Validation Tests (166/166)
python -m pytest training/
```
