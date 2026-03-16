#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"

uv run ruff format --check .
uv run ruff check .
uv run pyright .
uv run pytest api/test packages/learnwithai-core/test packages/learnwithai-jobqueue/test --cov --cov-report=term-missing