#!/bin/bash
set -e

echo "Waiting for PostgreSQL and Redis..."
while ! pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -q 2>/dev/null; do
  sleep 1
done

echo "Starting Celery Beat scheduler..."
exec celery -A app.workers.celery_app beat --loglevel=info
