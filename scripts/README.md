# Scripts

This directory contains small repository-wide helper scripts.

If you are new to the repo, this is the only script directory you need to know at the root level.

## What Lives Here

- `qa.sh` — the main repository quality gate
- `export_openapi.py` — exports the FastAPI OpenAPI spec to `frontend/openapi.json`

## `qa.sh`

Run this from the repository root.

```bash
./scripts/qa.sh
```

That command applies local autofixes where supported and then runs the repository checks.

If you want the CI-style, non-mutating version, run:

```bash
./scripts/qa.sh --check
```

At a high level, `qa.sh` runs:

- Python formatting and linting
- Python type checking
- backend tests with coverage
- frontend formatting, linting, and unit tests

## `export_openapi.py`

Run this from the repository root when the frontend API client needs a fresh OpenAPI spec:

```bash
uv run python scripts/export_openapi.py
```

Most frontend contributors will use the wrapper command instead:

```bash
cd frontend && pnpm api:sync
```
