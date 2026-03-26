# learnwithai-core

`learnwithai-core` is the shared backend package for LearnWithAI. It contains the reusable logic that should not depend on FastAPI request handling or Angular UI code.

## What Belongs Here

- Configuration models and helpers
- Domain models and database tables
- Repositories and persistence logic
- Shared services and business logic
- Job definitions that can be queued by the worker

## Source Directory Roles

- `src/learnwithai/config.py` — application settings
- `src/learnwithai/db.py` — database engine and session helpers. `get_session` is a yield-based FastAPI dependency: it commits on normal return, rolls back on exception, and closes in `finally`. Route handlers must not call commit or rollback directly.
- `src/learnwithai/models/` — domain models (API facing)
- `src/learnwithai/tables/` — SQLModel table definitions (DB facing)
  - `user.py` — `User` table (PID integer primary key)
  - `course.py` — `Course` table (auto-increment integer PK)
  - `membership.py` — `Membership` join table linking users to courses with composite PK `(user_pid, course_id)`, role (`MembershipType`), and lifecycle state (`MembershipState`)
  - `async_job.py` — `AsyncJob` table for unified async job tracking. Stores `kind`, `status`, JSON `input_data`/`output_data`, and lifecycle timestamps. All background job types share this table.
- `src/learnwithai/repositories/` — data access layer
  - `user_repository.py` — user lookup and registration
  - `course_repository.py` — course CRUD
  - `membership_repository.py` — membership CRUD
  - `async_job_repository.py` — CRUD for `AsyncJob` records, including listing by course and kind
- `src/learnwithai/services/` — shared business logic
- `src/learnwithai/jobs/` — queueable job definitions
- `src/learnwithai/tools/` — self-contained feature packages for AI-powered tools
  - `jokes/` — joke generation tool (tables, repository, service, models, job handler)

## Test Directory Layout

Tests mirror the source package structure:

```
test/
  conftest.py                          # shared fixtures (settings cache, DB session)
  test_config.py
  test_db.py
  test_interfaces.py
  test_jobs.py
  repositories/
    test_user_repository.py
    test_course_repository.py
    test_membership_repository.py
    test_async_job_repository.py
  services/
    test_csxl_auth_service.py
    test_health.py
  tools/
    jokes/
      test_job.py
      test_models.py
      test_repository.py
      test_service.py
```

The `session` fixture in `test/conftest.py` is shared by all integration tests that need a database session. Do not duplicate this fixture in subdirectory `conftest.py` files.

## Development Notes

- Keep this package framework-light and reusable.
- Keep FastAPI-specific dependency metadata out of this package. Shared services and repositories should be instantiated directly by adapter layers.
- Keep worker dependency construction explicit inside handlers. Avoid a separate dependency injection layer in core.
- Prefer pure or narrowly scoped logic where possible.
- If a service is useful to both the API and the worker, it almost certainly belongs here.
- Repositories accept and return domain objects for non-lookup operations and for relationship-scoped queries.
- Raw scalar identifiers belong in explicit lookup methods such as `get_by_id()` and `get_by_pid()`.
- Services should operate on loaded domain models for non-lookup behavior. If an HTTP route receives raw ids, resolve them in the API layer first so the route can return the right `404` before calling the service.

## Service Design Conventions

Services are classes whose dependencies (repositories and infrastructure like `JobQueue`) are all injected through `__init__`. There are no module-level helper functions — parsing, formatting, and other private logic live as `_private` methods on the class.

Methods are ordered in **literate code style**: public methods (the big picture) come first, private helpers come last.

The `JobQueue` interface (`learnwithai.interfaces.JobQueue`) is defined in this package so services can accept it without importing `learnwithai-jobqueue`. When a context (such as a job handler) constructs a service that never needs to enqueue new jobs, pass `ForbiddenJobQueue()` from `learnwithai.jobs` to satisfy the constructor. `ForbiddenJobQueue` raises a `RuntimeError` if `enqueue` is ever called, surfacing unexpected job submission immediately. Do not make the dependency optional.

### Async Job Tracking

All background job types share a single `async_job` table (`AsyncJob` in `tables/async_job.py`) with a `kind` string discriminator and JSON `input_data`/`output_data` columns. This avoids schema changes when adding new job types.

The `JobNotifier` protocol (`learnwithai.interfaces.jobs`) defines how job handlers publish real-time status updates after commit. `NoOpJobNotifier` (from `learnwithai.jobs`) silently discards notifications and is used in tests. The `RabbitMQJobNotifier` (in `learnwithai-jobqueue`) publishes `JobUpdate` messages to the `job_updates` fanout exchange for the API's WebSocket consumer.

### SQLModel Relationship and Eager Loading Conventions

When a domain table has a foreign key to another table (e.g. `Joke.async_job_id → AsyncJob.id`), define a unidirectional `Relationship` on the owning side only:

```python
from sqlmodel import Relationship

class Joke(SQLModel, table=True):
    async_job_id: int | None = Field(default=None, foreign_key="async_job.id")
    async_job: Optional["AsyncJob"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[Joke.async_job_id]", "lazy": "select"},
    )
```

**Important:** Do not use `from __future__ import annotations` in files that define SQLModel `Relationship` fields. Postponed evaluation breaks SQLAlchemy's class registry resolver, which needs to evaluate forward-reference strings like `"AsyncJob"` at class-creation time. Use `Optional["AsyncJob"]` from `typing` instead of `AsyncJob | None` when the related class is a forward reference.

In repository queries, use SQLAlchemy `selectinload` to eagerly load the relationship instead of writing manual outer joins:

```python
from sqlalchemy.orm import selectinload

stmt = select(Joke).options(selectinload(Joke.async_job)).where(...)
```

This returns fully hydrated domain objects (`list[Joke]`) rather than tuples (`list[tuple[Joke, AsyncJob | None]]`), keeping the service and route layers simpler.

### Tool Package Pattern

Each AI tool lives in a self-contained package under `src/learnwithai/tools/` (e.g. `tools/jokes/`). A tool package contains its own:

- `tables.py` — SQLModel table definitions specific to the tool
- `repository.py` — data access layer
- `service.py` — business logic and job orchestration
- `models.py` — API-facing response models
- `job.py` — background job handler

This keeps tool-specific concerns isolated from the shared repository and service layers. A tool's table may reference shared tables (like `AsyncJob`) via foreign keys and relationships.

## Parameter Ordering Convention

Any service method that accepts a `subject` parameter (the authenticated user performing the action) must list `subject` **first**. Subsequent domain model parameters follow in order from most generic to most specific. Repositories and other infrastructure parameters come last.

```python
# Correct
def get_course_roster(self, subject: User, course: Course) -> list[Membership]: ...
def add_member(self, subject: User, course: Course, target_user: User, membership_type: MembershipType) -> Membership: ...

# Wrong
def get_course_roster(self, course: Course, subject: User) -> list[Membership]: ...
```

## Database Scripts

- `scripts/create_database.py` creates the configured development database tables.
- `scripts/reset_database.py` fully resets the configured development database by dropping and recreating it before rebuilding the tables.

Run them from `packages/learnwithai-core/` with:

```bash
uv run python scripts/create_database.py
uv run python scripts/reset_database.py
```

Run tests from the repository root with:

```bash
uv run pytest packages/learnwithai-core/test
```