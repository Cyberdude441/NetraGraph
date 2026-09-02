#!/bin/sh
# ============================================================
# NetraGraph Production Backend Entrypoint
# Validates database readiness, runs migrations, launches Uvicorn
# ============================================================
set -e

echo "==> [NetraGraph Backend Entrypoint] Initializing..."

# 1. Pre-flight database connectivity verification
if [ -n "$DATABASE_SYNC_URL" ] || [ -n "$DATABASE_URL" ]; then
    echo "==> [NetraGraph Database] Testing connection readiness..."
    python -c "
import sys, os, time
from app.auth.config import auth_config
from sqlalchemy import create_engine, text

sync_url = auth_config.DATABASE_SYNC_URL
if 'sqlite' in sync_url:
    print('==> [NetraGraph Database] SQLite mode active, skipping PostgreSQL probe.')
    sys.exit(0)

max_retries = int(os.getenv('DB_WAIT_RETRIES', '30'))
for i in range(max_retries):
    try:
        engine = create_engine(sync_url, connect_args={'connect_timeout': 3})
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        print('==> [NetraGraph Database] Database connection verified.')
        sys.exit(0)
    except Exception as e:
        print(f'==> [NetraGraph Database] Waiting for database readiness ({i+1}/{max_retries})...')
        time.sleep(2)

print('==> [NetraGraph Database] ERROR: Database failed to become ready within timeout.')
sys.exit(1)
"
fi

# 2. Run pending Alembic database schema migrations
if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
    echo "==> [NetraGraph Migrations] Applying pending Alembic migrations..."
    alembic -c alembic.ini upgrade head
    echo "==> [NetraGraph Migrations] Database schema migrations up to date."
fi

# 3. Launch Uvicorn Production Gateway
WORKERS=${WEB_CONCURRENCY:-1}
PORT=${PORT:-8000}
HOST=${HOST:-0.0.0.0}

echo "==> [NetraGraph Server] Launching Uvicorn on ${HOST}:${PORT} (workers=${WORKERS})..."
exec uvicorn main:app --host "$HOST" --port "$PORT" --workers "$WORKERS"
