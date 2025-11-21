#!/usr/bin/env bash
# Usage:
#   ALLOW_DB_DOWNGRADE=true \
#   DB_HOST=db DB_PORT=5432 DB_USER=swx_user DB_PASSWORD=changeme DB_NAME=swx_db \
#   docker compose run --rm backend /app/scripts/rollback_last_migration.sh

set -euo pipefail

export PYTHONPATH="/app:${PYTHONPATH:-$(pwd)}"

ENVIRONMENT_NAME="${ENVIRONMENT:-local}"

if [[ "${ENVIRONMENT_NAME}" == "production" && "${FORCE_ROLLBACK:-false}" != "true" ]]; then
  echo "Refusing to run alembic downgrade in production without FORCE_ROLLBACK=true" >&2
  exit 1
fi

if [[ "${ALLOW_DB_DOWNGRADE:-false}" != "true" ]]; then
  echo "Set ALLOW_DB_DOWNGRADE=true to acknowledge the rollback risk." >&2
  exit 1
fi

if [[ -z "${DATABASE_URL:-}" && -z "${SQLALCHEMY_DATABASE_URI:-}" ]]; then
  echo "DATABASE_URL or SQLALCHEMY_DATABASE_URI must be set." >&2
  exit 1
fi

echo "Rolling back the most recent Alembic migration..."
alembic downgrade -1
echo "Rollback complete."

