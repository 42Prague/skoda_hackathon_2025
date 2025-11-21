#!/usr/bin/env bash

set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

if ! command -v alembic >/dev/null 2>&1; then
  echo "alembic command not found in PATH." >&2
  exit 1
fi

versions_dir="migrations/versions"
before_snapshot="$(ls -1 "${versions_dir}" | sort || true)"

alembic revision --autogenerate -m "tmp_check" --head head >/tmp/alembic_tmp_check.log 2>&1 || {
  cat /tmp/alembic_tmp_check.log >&2
  exit 1
}

after_snapshot="$(ls -1 "${versions_dir}" | sort || true)"

new_file="$(comm -13 <(printf '%s\n' "${before_snapshot}") <(printf '%s\n' "${after_snapshot}") | tail -n 1 || true)"

if [[ -z "${new_file}" ]]; then
  echo "No schema differences detected."
  exit 0
fi

new_revision_path="${versions_dir}/${new_file}"

if grep -qE "(op\.|sa\.)" "${new_revision_path}"; then
  echo "Schema drift detected in ${new_revision_path}. Review and either apply the migration or align models." >&2
  exit_code=1
else
  echo "Autogenerate produced an empty revision; removing ${new_revision_path}."
  rm -f "${new_revision_path}"
  exit_code=0
fi

exit "${exit_code}"

