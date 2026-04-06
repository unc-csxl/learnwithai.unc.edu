#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE="${1:-fix}"
DEFAULT_TEST_DB_URL="postgresql+psycopg://postgres:postgres@postgres:5432/learnwithai_test"
TEST_DB_URL="${TEST_DATABASE_URL:-$DEFAULT_TEST_DB_URL}"

# Ignore any activated per-package virtualenv from the parent shell.
unset VIRTUAL_ENV

cd "$ROOT_DIR"

if [[ "$MODE" != "fix" && "$MODE" != "--check" ]]; then
  echo "Usage: $0 [fix|--check]" >&2
  exit 1
fi

if [[ "$MODE" == "fix" ]]; then
  uv run ruff format .
  uv run ruff check --fix .
fi

export ENVIRONMENT="test"
export TEST_DATABASE_URL="$TEST_DB_URL"
export DATABASE_URL="$TEST_DB_URL"

uv run ruff format --check .
uv run ruff check .
uv run pyright .
uv run python -c "from learnwithai.db import reset_db_and_tables; reset_db_and_tables()"
uv run pytest \
  --cov=api \
  --cov=learnwithai \
  --cov=learnwithai_jobqueue \
  --cov-report=term-missing \
  --cov-config=.coveragerc \
  --cov-fail-under=100 \
  api/test packages/learnwithai-core/test packages/learnwithai-jobqueue/test

# ---- Frontend (TypeScript / Angular) ----
if [ -f "frontend/package.json" ] && grep -q '"test"' frontend/package.json; then
  echo ""
  echo "=== Frontend ==="
  if [[ "$MODE" == "fix" ]]; then
    (cd frontend && pnpm --if-present format && pnpm --if-present lint:fix)
  fi
  (cd frontend && pnpm --if-present format:check && pnpm --if-present lint && pnpm --if-present test:ci)
fi