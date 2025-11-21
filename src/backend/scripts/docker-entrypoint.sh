#!/usr/bin/env bash

set -euo pipefail

export PYTHONPATH="/app:${PYTHONPATH:-}"

python /app/scripts/verify_cpu_only.py

MIGRATIONS_DIR="${ALEMBIC_MIGRATIONS_DIR:-/app/migrations}"
ALEMBIC_CACHE_FILE="${ALEMBIC_CACHE_FILE:-/tmp/.alembic_checksum}"
DB_WAIT_INTERVAL="${DB_WAIT_INTERVAL:-2}"
DB_WAIT_ATTEMPTS="${DB_WAIT_ATTEMPTS:-30}"

log() {
  printf '%s %s\n' "$(date -Iseconds)" "$*"
}

wait_for_database() {
  local attempt=1
  while (( attempt <= DB_WAIT_ATTEMPTS )); do
    if python - <<'PY'
import asyncio
import os
import sys
import asyncpg

async def _probe():
    host = os.getenv('DB_HOST', 'db')
    port = int(os.getenv('DB_PORT', 5432))
    user = os.getenv('DB_USER', 'swx_user')
    password = os.getenv('DB_PASSWORD', 'changeme')
    database = os.getenv('DB_NAME', 'swx_db')
    conn = await asyncpg.connect(host=host, port=port, user=user, password=password, database=database)
    await conn.close()

try:
    asyncio.run(_probe())
except Exception as exc:  # noqa: BLE001
    print(exc, file=sys.stderr)
    raise SystemExit(1)
PY
    then
      return 0
    fi
    log "database not ready (attempt ${attempt}/${DB_WAIT_ATTEMPTS}); retrying..."
    attempt=$((attempt + 1))
    sleep "${DB_WAIT_INTERVAL}"
  done

  log "database did not become ready after ${DB_WAIT_ATTEMPTS} attempts"
  exit 1
}

checksum_migrations() {
  if [ ! -d "${MIGRATIONS_DIR}" ]; then
    return 1
  fi

  python - "$MIGRATIONS_DIR" <<'PY'
import hashlib
import os
import sys

root = sys.argv[1]
if not os.path.isdir(root):
    raise SystemExit(1)

hasher = hashlib.sha256()
for dirpath, _, filenames in os.walk(root):
    for filename in sorted(filenames):
        path = os.path.join(dirpath, filename)
        rel_path = os.path.relpath(path, root).encode()
        hasher.update(rel_path)
        with open(path, "rb") as file_handle:
            hasher.update(file_handle.read())

print(hasher.hexdigest())
PY
}

run_migrations_if_needed() {
  if [ ! -d "${MIGRATIONS_DIR}" ]; then
    log "migrations directory missing at ${MIGRATIONS_DIR}; refusing to continue"
    exit 1
  fi

  local current_checksum previous_checksum
  current_checksum="$(checksum_migrations || true)"
  if ! previous_checksum="$(cat "${ALEMBIC_CACHE_FILE}" 2>/dev/null)"; then
    previous_checksum=""
  fi

  if [ -z "${current_checksum}" ]; then
    log "unable to compute migrations checksum; running alembic to be safe"
  fi

  if [ "${current_checksum}" = "${previous_checksum}" ] && [ -n "${current_checksum}" ]; then
    log "no migration changes detected; skipping alembic"
    return
  fi

  log "detected migration changes; running alembic upgrade head"
  alembic upgrade head
  log "alembic upgrade completed"

  if [ -n "${current_checksum}" ]; then
    echo "${current_checksum}" > "${ALEMBIC_CACHE_FILE}"
  fi
}

wait_for_database
run_migrations_if_needed

log "starting application: $*"
exec "$@"
