# API Workspace

This workspace contains the FastAPI adapter for LearnWithAI. It is responsible for HTTP concerns such as routing, request parsing, dependency wiring, and response shaping.

The API layer should stay thin. If logic could reasonably be reused outside HTTP, it probably belongs in `packages/learnwithai-core/` instead of here.

## What Lives Here

```text
api/
|- src/api/
|  |- main.py                  FastAPI application entrypoint
|  |- context.py               Request/application context helpers
|  |- dependency_injection.py  Shared DI definitions for routes
|  `- routes/
|     |- auth.py               Authentication endpoints
|     `- health.py             Health and queue demo endpoints
|- test/                       Pytest suite for the API adapter
|- pyproject.toml              Package metadata and dependencies
```

## Current Entry Points

- `src/api/main.py` creates the `FastAPI` app and registers routers.
- `src/api/routes/health.py` exposes `/health` and `/queue`.
- `src/api/routes/auth.py` exposes the authentication flow under `/auth`.

## How To Run The API

Recommended from VS Code:

- Run the `api: run` task from the repository workspace.

Equivalent terminal command from the repository root:

```bash
uv run --package learnwithai-api uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Once it is running, check `http://localhost:8000/health`.

## How To Test The API

Run the API-focused tests from the repository root:

```bash
uv run pytest api/test
```

Before finishing broader backend work, run the repository QA check:

```bash
./scripts/qa.sh --check
```

## How To Add Or Change An Endpoint

Use this mental model:

1. Put the route in `src/api/routes/`.
2. Keep the route focused on HTTP details.
3. Use dependency injection for settings, sessions, current user resolution, and shared services.
4. Move reusable logic into `learnwithai-core`.
5. Add or update tests in `api/test/`.

## Good First Files To Read

- `src/api/main.py`
- `src/api/routes/health.py`
- `src/api/routes/auth.py`
- `src/api/dependency_injection.py`
- `test/test_main.py`
- `test/test_routes_auth.py`

Read those before making large API changes.
