#!/bin/bash
set -e

echo "Waiting for PostgreSQL..."
while ! pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -q 2>/dev/null; do
  sleep 1
done
echo "PostgreSQL is ready."

echo "Running database migrations..."
cd /app
alembic upgrade head

echo "Seeding default data..."
python -c "
import asyncio
from app.utils.init_db import init_db
asyncio.run(init_db())
" 2>/dev/null || echo "Seed skipped (already initialized or error)."

echo "Starting API server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
