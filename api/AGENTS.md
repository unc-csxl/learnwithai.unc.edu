# AGENTS.md

Read the repository root `AGENTS.md` first. This file adds API-specific guidance.

## Scope

This workspace owns FastAPI request handling, routing, dependency wiring, and HTTP responses.

## Expectations

- Keep route handlers thin.
- Put reusable business logic in `packages/learnwithai-core/`.
- Use dependency injection for settings, auth helpers, and shared services.
- Define HTTP-specific DI types and factories in `src/api/di.py`. Worker handlers in `learnwithai-core` should construct their own dependencies directly.
- Keep request body models explicit in route signatures with `Annotated[..., Body()]` when you need body metadata or want to signal API-layer ownership clearly.
- Do not add DI aliases or helper dependencies that derive values from request bodies. If a body field requires a database lookup, perform that lookup in the route logic and translate missing resources into the appropriate HTTP response there.
- Add Google-style docstrings to maintained Python modules and public functions.
- Keep type annotations explicit on public APIs.

## Service Factory Conventions

Service DI factories in `di.py` are responsible for composing API-only dependencies like `JobQueue` and instantiating repositories and services inside FastAPI `Depends` wrappers. Route handlers must not receive `JobQueueDI` as a parameter.

## Parameter Ordering Convention

In every route handler and service method that takes a `subject` parameter (the authenticated user), `subject` must be the **first** parameter. After `subject`, list additional domain model parameters in order from most generic to most specific (for example, `course` before `target_user`). Body inputs come after domain models. Service and repository parameters come last.

```python
# Correct
def create_course(subject: AuthenticatedUserDI, body: Annotated[CreateCourseRequest, Body()], course_svc: CourseServiceDI) -> CourseResponse: ...
def get_course_roster(subject: AuthenticatedUserDI, course: CourseByCourseIDPathDI, course_svc: CourseServiceDI) -> list[MembershipResponse]: ...

# Wrong — subject buried after domain models
def create_course(body: ..., subject: ..., course_svc: ...) -> ...: ...
```

This same ordering applies to service methods in `learnwithai-core`. Consistent ordering makes authorization intent visible at every call site and prevents confusion when reading or reviewing code.

## Transaction Management

The `get_session` dependency in `learnwithai-core` is a yield-based FastAPI dependency that owns the full transaction lifecycle:

- It commits automatically when a route handler returns normally.
- It rolls back automatically when any exception propagates out of the handler.
- It closes the session in a `finally` block regardless of outcome.

**Route handlers must never call `session.commit()`, `session.rollback()`, or `session.begin()`.** These are the job of the infrastructure layer, not the HTTP layer. Routes should generally not declare `session: SessionDI` at all — the session reaches repositories transitively through their own DI factories.

This means a route composed of multiple service calls is automatically atomic. If the second call fails, the first call's pending writes are rolled back along with it.

## Testing And Validation

- Add or update tests in `api/test/` for route behavior and adapter logic.
- Run targeted tests with `uv run pytest api/test`.
- Before finishing, run `./scripts/qa.sh --check` from the repository root.