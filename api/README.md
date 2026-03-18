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
|     |- courses.py            Course management endpoints
|     `- health.py             Health and queue demo endpoints
|- test/                       Pytest suite for the API adapter
|  `- routes/                  Route handler tests grouped by router
|- pyproject.toml              Package metadata and dependencies
```

## Current Entry Points

- `src/api/main.py` creates the `FastAPI` app and registers routers.
- `src/api/routes/health.py` exposes `/health` and `/queue`.
- `src/api/routes/auth.py` exposes the authentication flow under `/auth`.
- `src/api/routes/courses.py` exposes course creation, roster, and membership management.

## How To Run The API

Recommended from VS Code:

- Run the `api: run` task from the repository workspace.

Equivalent terminal command from the repository root:

```bash
uv run --package learnwithai-api uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Once it is running, check `http://localhost:8000/api/health`.

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
2. Keep the route focused on HTTP details. Use typed helpers in `src/api/dependency_injection.py` for shared request-scoped services and path-derived resource loading.
3. Declare request body models directly in the route signature. Prefer `Annotated[..., Body()]` when you want the body contract to be explicit at the API layer.
4. If a request body contains an identifier that requires a database lookup, do that lookup in the route logic and translate missing resources into the appropriate `404` response there instead of creating a body-driven DI helper.
5. Use dependency injection for settings, current user resolution, and shared services. Do **not** inject the session into a route handler directly — the session is managed automatically by `get_session` in `learnwithai-core` and reaches repositories through their own factories.
6. Move reusable logic into `learnwithai-core`.
7. Add or update tests in `api/test/`, placing route tests under `api/test/routes/`.

## Transaction Boundaries

`get_session` is a yield-based FastAPI dependency. It commits when a route returns normally and rolls back on any unhandled exception. Route handlers must never call `session.commit()`, `session.rollback()`, or `session.begin()`. This keeps persistence lifecycle concerns in the infrastructure layer and out of HTTP handlers.

## Good First Files To Read

- `src/api/main.py`
- `src/api/routes/health.py`
- `src/api/routes/auth.py`
- `src/api/dependency_injection.py`
- `test/test_main.py`
- `test/routes/test_routes_auth.py`

Read those before making large API changes.
