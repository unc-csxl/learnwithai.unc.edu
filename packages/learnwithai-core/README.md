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
- `src/learnwithai/repositories/` — data access layer
  - `user_repository.py` — user lookup and registration
  - `course_repository.py` — course CRUD
  - `membership_repository.py` — membership CRUD
- `src/learnwithai/services/` — shared business logic
- `src/learnwithai/jobs/` — queueable job definitions

## Test Directory Layout

Tests mirror the source package structure:

```
test/
  conftest.py                          # global fixtures (settings cache)
  test_config.py
  test_db.py
  test_interfaces.py
  test_jobs.py
  repositories/
    conftest.py                        # shared session fixture for DB tests
    test_user_repository.py
    test_course_repository.py
    test_membership_repository.py
  services/
    test_csxl_auth_service.py
    test_health.py
```

## Development Notes

- Keep this package framework-light and reusable.
- Prefer pure or narrowly scoped logic where possible.
- If a service is useful to both the API and the worker, it almost certainly belongs here.
- Repositories accept and return domain objects for non-lookup operations and for relationship-scoped queries.
- Raw scalar identifiers belong in explicit lookup methods such as `get_by_id()` and `get_by_pid()`.
- Services should operate on loaded domain models for non-lookup behavior. If an HTTP route receives raw ids, resolve them in the API layer first so the route can return the right `404` before calling the service.

## Service Design Conventions

Services are classes whose dependencies (repositories and infrastructure like `JobQueue`) are all injected through `__init__`. There are no module-level helper functions — parsing, formatting, and other private logic live as `_private` methods on the class.

Methods are ordered in **literate code style**: public methods (the big picture) come first, private helpers come last.

The `JobQueue` interface (`learnwithai.interfaces.JobQueue`) is defined in this package so services can accept it without importing `learnwithai-jobqueue`. When a context (such as a job handler) constructs a service that never needs to enqueue new jobs, pass `ForbiddenJobQueue()` from `learnwithai.jobs` to satisfy the constructor. `ForbiddenJobQueue` raises a `RuntimeError` if `enqueue` is ever called, surfacing unexpected job submission immediately. Do not make the dependency optional.

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