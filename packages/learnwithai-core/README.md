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
- `src/learnwithai/db.py` — database engine and session helpers
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
- Repositories accept and return domain objects. Use `session.get()` for primary key lookups.

Run tests from the repository root with:

```bash
uv run pytest packages/learnwithai-core/test
```