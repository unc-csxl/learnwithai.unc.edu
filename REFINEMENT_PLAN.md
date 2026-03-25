# Unified Async Jobs — Refinement Plan

> Based on investigation of `feature/unified-async-jobs` (merged at `67ed0d9`) vs `main` before it (`b31944b`).
> 45 files changed, +3,459 / −542 lines across all packages.

---

## 1. Clean Up `api/src/api/main.py`

### Problem

`main.py` currently inlines two supporting concerns that clutter the top-level composition:

1. **`_lifespan_context`** — 25 lines of async lifecycle management (JobUpdateManager setup, RabbitMQ consumer task start/cancel).
2. **`_generate_operation_id`** — minor but distracting utility.

`create_app` itself has no inline comments explaining the high-level composition.

### Proposed Refactoring

**Extract a `lifespan.py` module** (`api/src/api/lifespan.py`):

- Move `_lifespan_context` and its `asynccontextmanager` wrapping into this module.
- This module owns the `JobUpdateManager` creation, `ws_route_module.configure()` call, and the consumer background task start/cancel.
- Export a single `lifespan` object ready to pass to `FastAPI(lifespan=...)`.
- Add a module docstring explaining the lifecycle phases (startup → yield → shutdown) and what each phase does.

**Move `_generate_operation_id` to `api/src/api/openapi.py`** (which already owns `API_DESCRIPTION` and `OPENAPI_TAGS`):

- This keeps all OpenAPI customization together.

**Add intent comments to `create_app`**:

```python
def create_app(settings: Settings) -> FastAPI:
    """Creates and configures the FastAPI application."""
    # 1. Core application with OpenAPI metadata and lifecycle hooks
    application = FastAPI(...)

    # 2. Map domain authorization errors to 403 responses
    @application.exception_handler(AuthorizationError)
    async def authorization_error_handler(...): ...

    # 3. Mount REST API routes under /api
    for router in API_ROUTERS:
        application.include_router(router, prefix="/api")

    # 4. Mount WebSocket endpoint for real-time job updates
    application.include_router(ws_route_module.router, prefix="/api")

    # 5. Development-only routes (dev data seeding, utilities)
    if settings.is_development:
        application.include_router(dev_router, prefix="/api")

    # 6. Serve the Angular SPA for all non-API routes
    configure_spa(application, settings)
    return application
```

After this refactoring, `main.py` becomes ~35 lines of pure composition.

### Testing Impact

`test_main.py` already tests `_lifespan_context` and `_generate_operation_id` via the public app factory. Tests should continue working unchanged. Moving the lifespan to its own module may require updating import paths in `test_main.py`.

---

## 2. RabbitMQ Notification Layer — Simplify or Extract

### Current Architecture

Three bespoke modules handle the real-time notification pipeline:

| Module                                          | Role                                                                     | Lib Used   |
| ----------------------------------------------- | ------------------------------------------------------------------------ | ---------- |
| `learnwithai_jobqueue/rabbitmq_job_notifier.py` | Publishes `JobUpdate` to RabbitMQ fanout exchange (sync, `pika`)         | `pika`     |
| `api/job_update_consumer.py`                    | Consumes from fanout exchange, bridges to WebSockets (async, `aio-pika`) | `aio-pika` |
| `api/job_update_manager.py`                     | In-memory per-user WebSocket subscription + broadcast                    | None       |

Total: ~340 lines across three files.

### Library Investigation

| Library                          | What It Would Replace     | Assessment                                                                                                                                                  |
| -------------------------------- | ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **FastStream**                   | Both notifier + consumer  | Full framework for async messaging. Overkill — brings Kafka, Redis, NATS abstractions we don't need. Would replace Dramatiq's integration model. Too heavy. |
| **Kombu**                        | Notifier                  | Celery's transport abstraction. Adds a large dependency tree. Only useful if we were swapping transports. We are committed to RabbitMQ.                     |
| **aio-pika (already installed)** | Already used for consumer | Already in use. The consumer module is a thin 67-line wrapper around `aio-pika`. Not much to simplify further.                                              |
| **pika (already installed)**     | Already used for notifier | Already in use. The notifier is 82 lines of straightforward publish-with-reconnect.                                                                         |

**Verdict:** No off-the-shelf library provides a worthwhile reduction in complexity for our use case. The three modules are already thin wrappers around `pika` and `aio-pika`. Introducing FastStream or Kombu would add dependency weight and learning curve without reducing lines of code.

### Two Paths Forward

#### Path A: Keep In Place, Minor Polish (Recommended)

The current structure is already modular. The only refinement:

1. **Group consumer + manager into an `api/src/api/realtime/` sub-package** with `__init__.py`, `consumer.py`, and `manager.py`. This makes the "real-time delivery" concern a visible boundary in the project structure.
2. Rename `job_update_consumer.py` → `realtime/consumer.py` and `job_update_manager.py` → `realtime/manager.py`.
3. Add a sub-package docstring explaining the pipeline: Dramatiq worker → `RabbitMQJobNotifier` (sync publish) → RabbitMQ fanout → `consumer.py` (async subscribe) → `manager.py` (WebSocket fan-out).

#### Path B: Extract Into a Separate Package

Move consumer + manager into a new `packages/learnwithai-realtime/` workspace package. This would formally separate the real-time delivery concern from the HTTP API.

**Assessment:** Path B is premature. The consumer and manager are tightly coupled to FastAPI's `WebSocket` type and the API's lifespan management. Extracting into a separate package would require abstracting over the WebSocket type, which adds complexity for no clear benefit today.

**Recommendation: Path A.**

---

## 3. `BaseJobHandler` Flush vs. Commit — Educating on Transaction Visibility

### Current Behavior

In `BaseJobHandler.handle()`:

```
1. session opens
2. _set_processing() → sets PROCESSING, session.flush(), notify via RabbitMQ
3. _execute() → runs domain logic (may take seconds)
4. session.commit() → PROCESSING + domain changes become visible to other connections
5. _notify() → broadcasts final status
```

### The Key Insight

**`session.flush()` writes SQL to the database server but within the current transaction.** Other database connections cannot see these changes until `session.commit()`. This is standard PostgreSQL READ COMMITTED isolation behavior.

**However, the `_notify()` call after flush sends a RabbitMQ message immediately.** This means:

1. The WebSocket consumer receives "PROCESSING" status via RabbitMQ.
2. The frontend client receives the WebSocket push and may query the API for current job status.
3. The API query runs in a _different_ database session/transaction.
4. That query sees the _committed_ state — still `PENDING` — because the worker transaction hasn't committed yet.

**This is a race condition.** The frontend receives "PROCESSING" via WebSocket, but if it fetches the job via REST immediately, it might see "PENDING."

### Is This a Problem in Practice?

**Currently, no.** The frontend's `watchJobUpdate` only reacts to `completed` or `failed` statuses. It ignores `processing`. The intermediate PROCESSING notification is informational and the frontend doesn't fetch on it. The REST endpoint is only called after `completed`/`failed`, by which time the transaction has committed.

### Two Paths Forward

#### Path A: Accept Flush-Only (Recommended for Now)

The flush ensures that within the same session, `_notify()` reads back the correct `PROCESSING` state to build the `JobUpdate`. Without the flush, `_notify()` would see stale data. The flush is necessary _for notification accuracy_, not for external visibility.

Document this explicitly in the `_set_processing` docstring:

```python
def _set_processing(self, ...):
    """Transitions the job to PROCESSING, flushes, and notifies.

    The flush writes the status change to the database within the
    current transaction so the subsequent _notify() reads the
    correct state.  External database connections will not see
    PROCESSING until the handler commits after _execute() returns.
    This is intentional: the RabbitMQ notification provides an
    early signal, but the database state is only visible after
    the full operation succeeds.
    """
```

#### Path B: Commit PROCESSING Separately (If Needed Later)

If we later want the PROCESSING state to be reliably visible to REST queries _while the job is running_, we would need to commit the PROCESSING status in a **separate transaction** before starting `_execute`:

```python
def handle(self, job):
    engine = get_engine()
    # Phase 1: Mark PROCESSING in its own short transaction
    with Session(engine) as marking_session:
        self._set_processing(job.job_id, AsyncJobRepository(marking_session), ...)
        marking_session.commit()

    # Phase 2: Execute domain logic in a new transaction
    with Session(engine) as work_session:
        try:
            self._execute(work_session, job)
            work_session.commit()
            self._notify(...)
        except Exception:
            work_session.rollback()
            # Phase 3: Mark FAILED in a third transaction
            with Session(engine) as fail_session:
                self._mark_failed(job.job_id, AsyncJobRepository(fail_session))
                fail_session.commit()
                self._notify(...)
            raise
```

**Tradeoff:** This adds complexity and three separate transactions. If the process crashes between Phase 1 and Phase 2, the job stays stuck in PROCESSING. A reaper/timeout mechanism would then be needed.

**Recommendation: Path A for now.** The current behavior is correct and the race condition is benign. Upgrade to Path B only if we add UI that actively polls for PROCESSING status during long jobs.

---

## 4. Dependency Injection in Job Handlers

### Problem

`RosterUploadJobHandler._execute()` manually constructs repositories and services:

```python
def _execute(self, session, job):
    async_job_repo = AsyncJobRepository(session)
    user_repo = UserRepository(session)
    membership_repo = MembershipRepository(session)
    svc = RosterUploadService(async_job_repo, user_repo, membership_repo, ForbiddenJobQueue())
    svc.process_upload(job.job_id)
```

This is boilerplate that will grow with each new job type.

### Library Investigation

#### `fast-depends` (v3.0.8)

`fast-depends` is **the DI engine extracted from FastAPI itself**. It is a standalone library that provides `Depends()`-style injection without requiring a FastAPI application. It has **one transitive dependency** (itself lightweight).

This is the most natural fit because:

- Same `Annotated[..., Depends(...)]` pattern developers already know.
- Works with synchronous functions (Dramatiq workers are sync).
- Supports yield-based dependencies for session lifecycle.
- No global container state required.

Usage would look like:

```python
from fast_depends import inject, Depends

def get_session():
    engine = get_engine()
    with Session(engine) as session:
        yield session

def async_job_repo_factory(session = Depends(get_session)):
    return AsyncJobRepository(session)

def roster_upload_service_factory(
    async_job_repo = Depends(async_job_repo_factory),
    user_repo = Depends(user_repo_factory),
    membership_repo = Depends(membership_repo_factory),
):
    return RosterUploadService(async_job_repo, user_repo, membership_repo, ForbiddenJobQueue())

class RosterUploadJobHandler(BaseJobHandler[RosterUploadJob]):
    @inject
    def _execute(self, session, job, svc = Depends(roster_upload_service_factory)):
        svc.process_upload(job.job_id)
```

#### `fastapi-injectable` (v1.4.7)

This library provides a `@injectable` decorator that lets FastAPI dependencies be resolved outside of request context. However, it is designed as a FastAPI plugin and requires a running FastAPI app instance. This doesn't fit the Dramatiq worker context at all.

**Assessment: Not suitable.**

### Two Paths Forward

#### Path A: Adopt `fast-depends` (Higher Reward, Higher Risk)

**Pros:**

- Eliminates manual construction boilerplate in every handler.
- Reuses the `Depends()` mental model from FastAPI.
- Factory definitions can be shared between API DI and job handler DI.
- As new job types are added, they just declare dependencies.

**Cons:**

- New dependency (though very lightweight — extracted from FastAPI's own internals).
- The `BaseJobHandler` currently owns the session lifecycle. Integrating `fast-depends` requires rethinking who opens/closes the session and how the yield-based dependency interacts with the handler's commit/rollback logic.
- The API's `dependency_injection.py` factories use FastAPI-specific types (`Path()`, `Query()`, `HTTPBearer()`) that can't be reused directly. We'd need a shared "core" DI module with pure repository/service factories, and API-specific wrappers for HTTP concerns.

**What would need to move to core:**

- Pure repository factory functions (session → repository).
- Pure service factory functions (repos → service).
- Session yield dependency.

**What stays in API:**

- HTTP-specific dependencies (auth, path params, query params).
- API-specific type aliases (`AuthenticatedUserDI`, `CourseByCourseIDPathDI`).

**Migration plan:**

1. Add `fast-depends` to `learnwithai-core`'s dependencies.
2. Create `packages/learnwithai-core/src/learnwithai/di.py` with pure factory functions.
3. Refactor `api/src/api/dependency_injection.py` to import and wrap the core factories.
4. Refactor `BaseJobHandler` to use `@inject` with `Depends()` for `_execute`.
5. Simplify each handler's `_execute` to declare dependencies via parameters.
6. Update tests (mock at the dependency level rather than patching imports).

#### Path B: Simple Factory Registry (Lower Risk, Less Reward)

Keep DI manual but reduce boilerplate with a small factory pattern in core:

```python
# learnwithai/di.py
class ServiceContainer:
    """Constructs services for a given session."""

    def __init__(self, session: Session, job_queue: JobQueue):
        self._session = session
        self._job_queue = job_queue

    def async_job_repo(self) -> AsyncJobRepository:
        return AsyncJobRepository(self._session)

    def user_repo(self) -> UserRepository:
        return UserRepository(self._session)

    def membership_repo(self) -> MembershipRepository:
        return MembershipRepository(self._session)

    def roster_upload_service(self) -> RosterUploadService:
        return RosterUploadService(
            self.async_job_repo(), self.user_repo(),
            self.membership_repo(), self._job_queue,
        )
```

Then handlers become:

```python
class RosterUploadJobHandler(BaseJobHandler[RosterUploadJob]):
    def _execute(self, session, job):
        container = ServiceContainer(session, ForbiddenJobQueue())
        container.roster_upload_service().process_upload(job.job_id)
```

**Pros:** No new dependencies. Simple, explicit, easy to understand.
**Cons:** Still manual. Doesn't compose with FastAPI DI. Each new service requires a method on the container.

**Recommendation:** Path B is the pragmatic choice for now. It reduces boilerplate without introducing a new DI framework. Path A is worth revisiting when the number of job types justifies the investment. If you prefer Path A's elegance and are comfortable with the `fast-depends` dependency, it's a clean solution.

---

## 5. Code Review — Additional Simplifications

### 5a. Duplicated JWT Verification in `ws.py`

`routes/ws.py` lines 118–141 (`_authenticate_token`) re-implements JWT verification that already exists as `CSXLAuthService.verify_jwt()`:

```python
# ws.py — bespoke implementation
def _authenticate_token(token: str) -> int:
    settings = Settings()
    import jwt as pyjwt
    payload = pyjwt.decode(token, settings.jwt_secret, ...)
    return int(payload["sub"])
```

```python
# CSXLAuthService.verify_jwt — canonical implementation
def verify_jwt(self, token: str) -> int:
    payload = jwt.decode(token, self._settings.jwt_secret, ...)
    return int(payload["sub"])
```

These are functionally identical.

**Fix:** Replace `_authenticate_token` with a lightweight helper that constructs a `Settings` and calls `CSXLAuthService.verify_jwt()` — or better, extract JWT verification into a standalone function in core (since it doesn't need the full `CSXLAuthService` dependency graph). A simple `verify_jwt(token: str, settings: Settings) -> int` function in `learnwithai/auth.py` could serve both the HTTP DI layer and the WebSocket layer.

### 5b. Dead `mark_failed` on `RosterUploadService`

`RosterUploadService.mark_failed()` (lines 122–139) is now dead code. The `BaseJobHandler._mark_failed()` method handles failure marking in the handler lifecycle. The service method is no longer called anywhere.

**Fix:** Remove `RosterUploadService.mark_failed()` and its tests.

### 5c. `EchoJobHandler` Does Not Extend `BaseJobHandler`

`EchoJobHandler` implements `JobHandler[EchoJob]` directly with a bare `handle()` method (just prints). It doesn't extend `BaseJobHandler` because it has no `job_id` or database tracking. This is an inconsistency — `EchoJob` extends `Job` but not `TrackedJob`.

**Is this a problem?** No. The echo job is a diagnostic tool. It doesn't need database tracking. The `job_handler_map` correctly maps it. But it's worth a brief comment in `echo.py` explaining _why_ it doesn't use `BaseJobHandler`.

### 5d. Module-Level `_manager` Singleton in `ws.py`

`ws.py` uses a module-level `_manager: JobUpdateManager | None` with a `configure()` function and `_get_manager()` accessor. This is a pragmatic pattern for wiring WebSocket state, but it means:

- Module-level mutable state — functional purists would object.
- Tests must call `configure()` via fixture (which they do, via `_configure_manager` autouse).

**Assessment:** This is acceptable. The alternative (sub-application mounting or middleware injection) adds complexity without justification. **No change needed**, but the plan to extract a `realtime/` sub-package (item 2A) would naturally encapsulate this.

### 5e. `output_data` Access Pattern in Route Handler

In `routes/roster_uploads.py`:

```python
output = job.output_data or {}
return RosterUploadStatusResponse(
    ...
    created_count=output.get("created_count", 0),
    ...
)
```

This is fine but loosely typed — the dict keys are strings with no validation. If the service changes a key name, the route silently returns zeros.

**Optional improvement:** Add a `RosterUploadOutput` TypedDict in core that both the service (when writing `output_data`) and the API (when reading it) can reference. This provides static type checking across the boundary.

```python
# learnwithai/jobs/roster_upload.py
class RosterUploadOutput(TypedDict):
    created_count: int
    updated_count: int
    error_count: int
    error_details: str | None
```

### 5f. WebSocket `_authenticate_token` Creates `Settings()` Per Call

Each WebSocket connection creates a fresh `Settings()` instance. Since `Settings` reads from environment variables via Pydantic, this is fine functionally but wasteful. Consider caching or accepting settings as a parameter.

This is a minor nit — low priority.

---

## Summary — Recommended Action Items (Ordered by Priority)

| #   | Item                                                                                                  | Effort | Impact                                         |
| --- | ----------------------------------------------------------------------------------------------------- | ------ | ---------------------------------------------- |
| 1   | Extract `lifespan.py` and move `_generate_operation_id` to `openapi.py`; add comments to `create_app` | Small  | High readability improvement                   |
| 2   | Remove dead `RosterUploadService.mark_failed()`                                                       | Tiny   | Reduces confusion                              |
| 3   | Fix duplicated JWT verification in `ws.py`                                                            | Small  | Eliminates duplication, single source of truth |
| 4   | Group consumer + manager into `api/src/api/realtime/` sub-package (Path 2A)                           | Small  | Better code organization                       |
| 5   | Document flush-vs-commit behavior in `_set_processing` docstring (Path 3A)                            | Tiny   | Clarifies intent                               |
| 6   | Add comment to `EchoJobHandler` explaining why it doesn't use `BaseJobHandler`                        | Tiny   | Reduces confusion                              |
| 7   | Introduce `ServiceContainer` for job handler DI (Path 4B)                                             | Medium | Reduces handler boilerplate                    |
| 8   | Add `RosterUploadOutput` TypedDict for typed `output_data` access                                     | Small  | Better type safety                             |

### Decision Points for Your Input

1. **Item 4:** Path A (extract `realtime/` sub-package) vs. leave files at the top level of `api/src/api/`?
2. **Item 7:** Path A (`fast-depends` library) vs. Path B (simple `ServiceContainer`)? Path A is more elegant but adds a dependency; Path B is a couple dozen lines of code.
3. **Item 3:** Extract JWT verification to a standalone function in core, or just call `CSXLAuthService.verify_jwt()`?
4. **Item 8:** Add the `RosterUploadOutput` TypedDict, or accept the loose dict access?
