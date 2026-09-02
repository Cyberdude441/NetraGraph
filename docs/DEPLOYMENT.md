# NetraGraph — Production Deployment & Operations Manual

This document provides complete instructions for deploying, managing, backing up, and upgrading NetraGraph in local containerized environments and production infrastructure.

---

## 1. System Requirements & Prerequisites

| Component | Minimum Specification | Recommended Production |
|---|---|---|
| **Operating System** | Linux (Ubuntu 22.04 LTS / Debian 12 / RHEL 9) / Windows Server 2022 | Ubuntu 22.04 LTS x86_64 |
| **CPU Architecture** | 4 Cores (x86_64) | 8+ Cores (x86_64) |
| **System Memory (RAM)** | 8 GB | 16 GB - 32 GB |
| **Storage** | 40 GB SSD | 100+ GB NVMe SSD |
| **Container Engine** | Docker Engine 24.0+ & Docker Compose v2.20+ | Docker Engine 26.0+ |
| **Reverse Proxy** | Nginx 1.27+ | Nginx 1.27+ with TLS 1.3 |
| **Relational Database** | PostgreSQL 16.x | PostgreSQL 16.x Managed / Containerized |
| **Graph Database** | Neo4j 5.20+ Community / Enterprise | Neo4j 5.20+ Enterprise |

---

## 2. Environment Variables Configuration

Copy `.env.example` to `.env` in the root workspace. **Never commit `.env` or production credentials to source control.**

```bash
cp .env.example .env
chmod 600 .env
```

### Essential Production Variables

```ini
# PostgreSQL Database Settings
POSTGRES_DB=netragraph
POSTGRES_USER=netragraph_admin
POSTGRES_PASSWORD=GENERATE_STRONG_RANDOM_PASSWORD_HERE
DATABASE_URL=postgresql+asyncpg://netragraph_admin:PASSWORD@postgres:5432/netragraph
DATABASE_SYNC_URL=postgresql://netragraph_admin:PASSWORD@postgres:5432/netragraph
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30

# JWT & Authentication Security
JWT_SECRET_KEY=GENERATE_64_CHAR_HEX_RANDOM_SECRET_KEY
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30

# OTP Delivery (Gmail SMTP)
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=netragraph.security@gmail.com
SMTP_PASSWORD="your_16_digit_app_password"
SMTP_FROM=netragraph.security@gmail.com
SMTP_FROM_NAME="NetraGraph Security Division"
SMTP_USE_TLS=True

# Browser Cookie & Session Flags
COOKIE_SECURE=True
COOKIE_SAMESITE=lax

# Neo4j Graph Database
NEO4J_AUTH=neo4j/GENERATE_STRONG_NEO4J_PASSWORD
NEO4J_URI=bolt://neo4j:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=GENERATE_STRONG_NEO4J_PASSWORD

# AI Intelligence Providers
NVIDIA_NEMOTRON_API_KEY=your_nvidia_api_key
GOOGLE_GEMINI_API_KEY=your_gemini_api_key
DEFAULT_AI_PROVIDER=nemotron
```

---

## 3. Local Containerized Deployment

To start the complete multi-container stack locally (PostgreSQL 16, Neo4j 5.x, Backend API, Frontend UI, Nginx Gateway):

```bash
# 1. Build and launch all services in detached mode
docker compose up -d --build

# 2. Monitor startup logs
docker compose logs -f

# 3. Verify service health
docker compose ps
```

### Local Access Points:
- **Unified Portal (via Nginx)**: `http://localhost`
- **Backend Healthcheck**: `http://localhost/health`
- **Database Healthcheck**: `http://localhost/health/db`
- **Readiness Probe**: `http://localhost/health/ready`
- **API Documentation**: `http://localhost/docs`
- **Neo4j Browser UI**: `http://localhost:7474`

---

## 4. Production Deployment (Hardened)

In production environments, direct container port bindings to host interfaces are closed. All traffic enters strictly through the Nginx reverse proxy over HTTPS.

```bash
# 1. Prepare SSL certificates in ./certs/
mkdir -p certs
# Place fullchain.pem and privkey.pem in ./certs/
chmod 600 certs/privkey.pem

# 2. Deploy with production overrides
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# 3. Verify all containers are healthy and non-root
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
```

---

## 5. Database Migration Execution Strategy

Alembic schema migrations execute automatically during backend container startup via `backend/entrypoint.sh`.

### Manual Migration Commands:

```bash
# Check current database revision
docker compose exec backend alembic -c alembic.ini current

# Run pending migrations
docker compose exec backend alembic -c alembic.ini upgrade head

# Rollback one migration (Emergency)
docker compose exec backend alembic -c alembic.ini downgrade -1
```

---

## 6. Backup & Restore Procedures

### PostgreSQL Relational & Auth Backup

```bash
# Create timestamped SQL dump
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
docker compose exec -T postgres pg_dump -U postgres -d netragraph -F c -b -v > "backup_netragraph_pg_${TIMESTAMP}.dump"

# Restore PostgreSQL from dump
docker compose exec -T postgres pg_restore -U postgres -d netragraph -c -v < "backup_netragraph_pg_${TIMESTAMP}.dump"
```

### Neo4j Knowledge Graph Backup

```bash
# Offline dump of neo4j data volume
docker compose stop neo4j
docker run --rm --volumes-from netragraph-neo4j -v $(pwd)/backups:/backup \
    alpine tar czf /backup/neo4j_data_backup.tar.gz /data
docker compose start neo4j
```

---

## 7. Zero-Downtime Upgrade & Rollback Strategy

### Rolling Application Upgrade:
1. Pull latest code from `main`.
2. Build new container images without tearing down running stack:
   ```bash
   docker compose build backend frontend
   ```
3. Restart backend (entrypoint will automatically apply non-destructive schema migrations):
   ```bash
   docker compose up -d --no-deps backend
   ```
4. Update frontend:
   ```bash
   docker compose up -d --no-deps frontend
   ```
5. Reload Nginx configuration:
   ```bash
   docker compose exec nginx nginx -s reload
   ```

### Emergency Rollback:
1. Revert to previous image tag or git revision:
   ```bash
   git checkout <PREVIOUS_STABLE_TAG>
   docker compose up -d --build
   ```
2. If schema rollback is required:
   ```bash
   docker compose exec backend alembic -c alembic.ini downgrade <TARGET_REVISION>
   ```

---

## 8. Security & Hardening Checklist

- [x] **Non-Root Container Execution**: Backend runs as `netragraph:10001`, Frontend as `nginx:101`.
- [x] **Network Isolation**: Postgres, Neo4j, Backend, and Frontend run on private bridge `netragraph-net`.
- [x] **No Hardcoded Secrets**: Zero passwords or JWT keys baked into Docker images or repository files.
- [x] **Security Headers**: HSTS, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`.
- [x] **Reverse Proxy Rate & Size Limits**: `client_max_body_size 50M`, 30s timeouts.
- [x] **Immutable ML Models**: Production Models A–E frozen in read-only image layers.
- [x] **Database Least-Privilege**: Relational database isolated from public internet access.
