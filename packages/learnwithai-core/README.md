# learnwithai-core

`learnwithai-core` is the main shared backend package for LearnWithAI.

If you are trying to understand how the system behaves, this is usually the most important backend package to read first. It contains the reusable logic that should work the same way no matter whether it is called from the API or the worker.

## What This Package Owns

Put code here when it answers questions like these:

- What rules does the product follow?
- How is data stored and loaded?
- What service should run when a feature is triggered?
- What background job should be created?

That usually means:

- configuration and environment helpers
- database setup and session helpers
- SQLModel tables and domain models
- repositories
- services
- shared job definitions
- feature-specific tool packages under `tools/`

## Start Here

If you are new to this package, read these files in order:

1. `src/learnwithai/config.py`
2. `src/learnwithai/db.py`
3. `src/learnwithai/services/`
4. `src/learnwithai/repositories/`
5. `src/learnwithai/jobs/`
6. `src/learnwithai/tools/`

## Directory Map

```text
src/learnwithai/
|- config.py            Settings and environment parsing
|- db.py                Database engine and session helpers
|- models/              API-facing and shared domain models
|- tables/              SQLModel table definitions
|- repositories/        Data access layer
|- services/            Shared business logic
|- jobs/                Queueable job definitions and shared job helpers
|- interfaces/          Shared protocols used across packages
`- tools/               Self-contained feature packages
```

Current tool packages live under `tools/`. For example, `tools/jokes/` keeps the joke-generation feature's tables, repository, service, models, and job handler together.

## How This Package Fits The System

Most backend requests follow this path:

1. A FastAPI route in `api/` receives the request.
2. The route loads any path-based resources it needs.
3. The route calls a service in `learnwithai-core`.
4. The service uses repositories and models from this package.
5. If work should happen later, the service enqueues a job defined here.

If a piece of logic would be useful in both the API and the worker, it probably belongs in this package.

## Important Conventions

### Keep this package framework-light

Do not put FastAPI request or response details here. The API workspace should translate HTTP into calls into this package.

### Services own behavior

Services are classes. Their dependencies are injected through `__init__`. Public methods come first, and private helper methods come after them.

### Repositories own persistence

Repositories should handle database loading and saving. Services should not build SQL queries directly.

### `subject` comes first

When a service method accepts the authenticated user, the `subject` parameter must be first.

```python
def get_course_roster(self, subject: User, course: Course) -> list[Membership]: ...
```

### Use explicit job queue guards

The `JobQueue` interface lives in this package. If a service needs a queue dependency but a caller should never enqueue jobs, pass `ForbiddenJobQueue()` instead of making the dependency optional.

### Prefer relationship loading over manual joins

When loading related SQLModel objects in repositories, prefer eager loading with `selectinload` instead of returning manual tuple-shaped join results.

## Tests

Tests mirror the package structure and live in `test/`.

Important areas include:

- `test/repositories/`
- `test/services/`
- `test/tools/`
- `test_jobs.py`

The shared database fixtures live in `test/conftest.py`. Reuse them instead of redefining them in subdirectories.

Run tests from the repository root:

```bash
uv run pytest packages/learnwithai-core/test
```

## Helpful Scripts

From `packages/learnwithai-core/`:

```bash
uv run python scripts/create_database.py
uv run python scripts/reset_database.py
```

- `create_database.py` creates the configured development database tables.
- `reset_database.py` drops and recreates the configured development database, then rebuilds the tables.
