#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"

uv run ruff format .
uv run ruff format --check .
uv run ruff check --fix .
uv run ruff check .
uv run pyright .
# Explicitly limit coverage measurement to source packages so test files are omitted
uv run pytest api/test packages/learnwithai-core/test packages/learnwithai-jobqueue/test \
	--cov=api --cov=learnwithai --cov=learnwithai_jobqueue --cov-report=term-missing

# ---- Frontend (TypeScript / Angular) ----
if [ -f "frontend/package.json" ] && grep -q '"test"' frontend/package.json; then
  echo ""
  echo "=== Frontend ==="
  (cd frontend && pnpm --if-present lint && pnpm --if-present test --watch=false)
fi