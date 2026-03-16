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