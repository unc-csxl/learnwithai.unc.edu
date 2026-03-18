#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE="${1:-fix}"

cd "$ROOT_DIR"

if [[ "$MODE" != "fix" && "$MODE" != "--check" ]]; then
  echo "Usage: $0 [fix|--check]" >&2
  exit 1
fi

if [[ "$MODE" == "fix" ]]; then
  uv run ruff format .
  uv run ruff check --fix .
fi

uv run ruff format --check .
uv run ruff check .
uv run pyright .
uv run pytest api/test packages/learnwithai-core/test packages/learnwithai-jobqueue/test

# ---- Frontend (TypeScript / Angular) ----
if [ -f "frontend/package.json" ] && grep -q '"test"' frontend/package.json; then
  echo ""
  echo "=== Frontend ==="
  if [[ "$MODE" == "fix" ]]; then
    (cd frontend && pnpm --if-present format && pnpm --if-present lint:fix)
  fi
  (cd frontend && pnpm --if-present format:check && pnpm --if-present lint && pnpm --if-present test:ci)
fi