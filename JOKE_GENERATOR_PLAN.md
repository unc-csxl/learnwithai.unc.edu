# Instructor Tools: Joke Generator & Real-Time Job Updates

## Overview

This plan introduces two interlocking capabilities:

1. **A unified async job tracking system with WebSocket-based real-time updates** — replacing the current polling pattern used by roster uploads and serving as the foundation for all future background work.
2. **A "Joke Generator" instructor tool** — the first feature built on this infrastructure, calling the OpenAI API asynchronously and streaming results back to the frontend.

The design prioritizes simplicity: one WebSocket connection per authenticated session, one generic job table with a JSON payload column, and one pub/sub channel pattern over RabbitMQ that all job types share.

---

## Part 1: Unified Job Tracking & Real-Time Updates

### 1.1 Database Model — `async_job` Table

Replace the per-feature job tables (like `roster_upload_job`) with a single, unified `async_job` table. The `RosterUploadJob` table will be migrated into this scheme.

```
async_job
├── id: int (PK, auto-increment)
├── course_id: int (FK → course.id, nullable=False)
├── created_by_pid: int (nullable=False)
├── kind: str (e.g. "roster_upload", "joke_generation")
├── status: enum (PENDING, PROCESSING, COMPLETED, FAILED)
├── input_data: JSON (request payload — the CSV text, the joke prompt, etc.)
├── output_data: JSON | null (result payload — counts, joke list, etc.)
├── error_message: str | null
├── created_at: datetime (server default now())
├── completed_at: datetime | null
```

**Why a single table instead of class-hierarchy inheritance?**

- Keeps the schema dead simple — one table, one repository, one set of status transitions.
- The `kind` column discriminates job type. `input_data` and `output_data` are JSON columns whose shape is determined by `kind`. Pydantic models handle (de)serialization at the service layer.
- Adding a new job type requires zero schema changes — just a new `kind` value and Pydantic models for its input/output shapes.
- If we ever need indexed queries on job-specific fields, we can add optional computed/generated columns or a secondary table later. For now, JSON is the simplest approach.

**Migration from `roster_upload_job`:**

The existing `roster_upload_job` table will be dropped and its responsibilities absorbed into `async_job`:

- `csv_data` → `input_data` (as `{"csv_text": "..."}`)
- `created_count`, `updated_count`, `error_count`, `error_details` → `output_data` (as `{"created_count": N, ...}`)
- `uploaded_by_pid` → `created_by_pid`

Since there are no production migrations (tables are recreated via `create_db_and_tables()`), this is a clean swap.

### 1.2 Repository — `AsyncJobRepository`

**Location:** `packages/learnwithai-core/src/learnwithai/repositories/async_job_repository.py`

Standard CRUD following the existing repository pattern:

```python
class AsyncJobRepository:
    def __init__(self, session: Session): ...
    def create(self, job: AsyncJob) -> AsyncJob: ...
    def get_by_id(self, job_id: int) -> AsyncJob | None: ...
    def list_by_course_and_kind(self, course_id: int, kind: str) -> list[AsyncJob]: ...
    def update(self, job: AsyncJob) -> AsyncJob: ...
    def delete(self, job: AsyncJob) -> None: ...
```

### 1.3 Job Completion Notifications via RabbitMQ Pub/Sub

When a background job completes (or fails), the handler publishes a lightweight notification to RabbitMQ so that connected WebSocket clients can react immediately.

**Channel design:**

- A single RabbitMQ **fanout exchange** named `job_updates`.
- Each API server instance creates a **temporary, exclusive queue** bound to this exchange on startup.
- When a job finishes, the handler publishes a small JSON message to the exchange:

```json
{
  "job_id": 42,
  "course_id": 7,
  "kind": "joke_generation",
  "status": "completed"
}
```

- Each API server instance consumes from its own queue and dispatches the update to any locally-connected WebSocket clients that are subscribed to that `job_id`.

**Why fanout + temporary queues?**

- With multiple API server instances, we don't know which instance holds the WebSocket for a given user. Fanout ensures every instance receives every update, and each instance filters locally.
- Temporary queues auto-delete when the API server disconnects — no cleanup needed.
- This is the simplest pub/sub pattern RabbitMQ supports. It introduces no new Dramatiq concepts; we use `pika` (already a transitive dependency of `dramatiq[rabbitmq]`) directly for the pub/sub layer.

### 1.4 Notification Publisher — `JobNotifier` Protocol & Implementation

**Core interface** (`packages/learnwithai-core/src/learnwithai/interfaces/jobs.py`):

```python
class JobUpdate(BaseModel):
    """Lightweight notification published when a job's status changes."""
    job_id: int
    course_id: int
    kind: str
    status: str

@runtime_checkable
class JobNotifier(Protocol):
    """Publishes job status changes to interested listeners."""
    def notify(self, update: JobUpdate) -> None: ...
```

**RabbitMQ implementation** (`packages/learnwithai-jobqueue/`):

```python
class RabbitMQJobNotifier(JobNotifier):
    """Publishes job updates to the RabbitMQ fanout exchange."""
    def __init__(self, rabbitmq_url: str): ...
    def notify(self, update: JobUpdate) -> None:
        # Publish JSON to the `job_updates` fanout exchange
```

**No-op implementation** for tests:

```python
class NoOpJobNotifier(JobNotifier):
    def notify(self, update: JobUpdate) -> None:
        pass
```

Job handlers will receive a `JobNotifier` and call `notifier.notify(...)` after updating the job status in the database and committing. This keeps the notification decoupled from the job processing logic.

### 1.5 WebSocket Endpoint

**Location:** `api/src/api/routes/ws.py`

A single WebSocket endpoint that authenticated clients connect to for receiving real-time job updates.

```
GET /api/ws/jobs
```

**Connection lifecycle:**

1. Client connects with bearer token as a query parameter: `/api/ws/jobs?token=<jwt>`.
   - WebSocket connections cannot use the `Authorization` header from browsers, so the token is passed as a query param.
   - The server validates the JWT immediately on connect. Invalid tokens result in an immediate close with code 4401.

2. Client sends **subscribe** messages to indicate which jobs it cares about:
   ```json
   {"action": "subscribe", "job_ids": [42, 43]}
   ```

3. Server pushes update messages when subscribed jobs change status:
   ```json
   {"job_id": 42, "status": "completed"}
   ```

4. Client can send **unsubscribe** messages:
   ```json
   {"action": "unsubscribe", "job_ids": [42]}
   ```

**Authorization enforcement:**

- On subscribe, the server verifies the authenticated user is a member of the course associated with each requested `job_id`. Unauthorized subscriptions are silently ignored (or return an error frame).
- The server only forwards updates for jobs the user is authorized to see.

**Implementation approach:**

FastAPI supports WebSocket routes natively. The endpoint will:

1. Authenticate via JWT from query param.
2. Maintain an in-memory map of `job_id → set[WebSocket]` subscriptions on each API instance.
3. Consume from the instance's temporary RabbitMQ queue in a background `asyncio` task.
4. When a message arrives from RabbitMQ, look up which local WebSockets are subscribed to that `job_id` and send the update.

**In-process connection manager:**

```python
class JobUpdateManager:
    """Manages WebSocket subscriptions and dispatches job updates."""
    def __init__(self): ...
    def subscribe(self, ws: WebSocket, job_id: int) -> None: ...
    def unsubscribe(self, ws: WebSocket, job_id: int) -> None: ...
    def disconnect(self, ws: WebSocket) -> None: ...
    async def broadcast(self, update: JobUpdate) -> None: ...
```

This is a simple in-memory structure. It lives for the lifetime of the API process. No persistence needed.

### 1.6 RabbitMQ Consumer Background Task

On API server startup, a background task connects to RabbitMQ, declares the fanout exchange and a temporary queue, and enters a consume loop:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Connect to RabbitMQ, declare exchange, bind temp queue
    # Start asyncio task that consumes messages and calls manager.broadcast()
    yield
    # Clean up connection
```

Since `pika` is synchronous, we'll use `aio-pika` (the async RabbitMQ client) in the API process to avoid blocking the event loop. This is one new dependency for the `api` package only.

**Alternative considered:** Using `pika` with `run_in_executor`. This works but `aio-pika` is cleaner for async consumers and is a lightweight dependency.

### 1.7 Frontend WebSocket Service

**Location:** `frontend/src/app/job-update.service.ts`

A singleton Angular service that manages a single WebSocket connection per session.

```typescript
@Injectable({ providedIn: 'root' })
export class JobUpdateService {
  private socket: WebSocket | null = null;
  private subscriptions = new Map<number, WritableSignal<string>>();

  /** Connect (if not already) and subscribe to updates for a job. Returns a signal of job status. */
  subscribe(jobId: number): Signal<string> { ... }

  /** Unsubscribe from a job and clean up if no subscriptions remain. */
  unsubscribe(jobId: number): void { ... }
}
```

**Key behaviors:**

- Lazily opens the WebSocket on first `subscribe()` call.
- Reads the JWT from `AuthTokenService` and appends it as `?token=...`.
- Maintains a `Map<number, WritableSignal<string>>` that maps job IDs to Angular signals.
- When the WebSocket receives an update message, it calls `.set()` on the corresponding signal, triggering Angular change detection via signals (no zone/polling needed).
- Automatically reconnects with exponential backoff if the connection drops.
- Closes the connection when the last subscription is removed.
- The WebSocket URL is derived from the current page origin, replacing `http` with `ws` (and `https` with `wss`). The proxy config will be extended to forward `/api/ws/` to the API server.

This gives components a clean, reactive interface: subscribe to a job ID and get a signal that updates in real time.

### 1.8 Migrate Roster Upload to the Unified System

The existing roster upload feature will be migrated:

1. **Drop** `RosterUploadJob` table and `RosterUploadRepository`.
2. **Replace** with `AsyncJob` (kind=`"roster_upload"`), `AsyncJobRepository`.
3. **Update** `RosterUploadService` to work with the new table. The `input_data` JSON stores `{"csv_text": "..."}`. The `output_data` JSON stores `{"created_count": N, "updated_count": N, "error_count": N, "error_details": "..."}`.
4. **Update** the roster upload job handler to call `JobNotifier.notify()` after completion.
5. **Update** API routes and response models.
6. **Update** the frontend roster component to optionally use the WebSocket service instead of polling (or keep polling for now and migrate later as a fast follow).

---

## Part 2: Joke Generator Feature

### 2.1 Instructor Tools Landing Page

**Route:** `/courses/:id/tools`

Transform the current placeholder `Tools` component into a card-based landing page listing available instructor tools. Each card has an icon, title, description, and routes to the tool's primary interface.

```
┌─────────────────────────────────┐
│  🎭 Joke Generator              │
│  Add humor to your course       │
│  content with AI-generated      │
│  joke ideas.                    │
│                          [Open] │
└─────────────────────────────────┘
```

The tools component will use an external template and its `tools` route will become a parent with child routes:

```typescript
// In app.routes.ts, the 'tools' route becomes:
{
  path: 'tools',
  children: [
    {
      path: '',
      loadComponent: () =>
        import('./courses/course-detail/tools/tools.component').then((m) => m.Tools),
    },
    {
      path: 'jokes',
      loadComponent: () =>
        import('./courses/course-detail/tools/joke-generator/joke-generator.component')
          .then((m) => m.JokeGenerator),
    },
  ],
},
```

### 2.2 Joke Generator UI

**Route:** `/courses/:id/tools/jokes`

**Layout:**

```
┌─────────────────────────────────────────┐
│  Joke Generator                         │  ← PageTitleService
├─────────────────────────────────────────┤
│                                         │
│  Describe the content you'd like        │
│  joke ideas for:                        │
│  ┌─────────────────────────────────┐    │
│  │                                 │    │
│  │  (textarea)                     │    │
│  │                                 │    │
│  └─────────────────────────────────┘    │
│                         [Generate] btn  │
│                                         │
├─────────────────────────────────────────┤
│  Previous Requests                      │
│                                         │
│  ┌─ "Jokes about recursion" ──────────┐ │
│  │  ⏳ Generating...                  │ │  ← spinner while PENDING/PROCESSING
│  │                            [Delete] │ │
│  └────────────────────────────────────┘ │
│                                         │
│  ┌─ "Jokes about linked lists" ───────┐ │
│  │  1. Why did the linked list...     │ │  ← jokes displayed when COMPLETED
│  │  2. A linked list walks into...    │ │
│  │  3. ...                            │ │
│  │                            [Delete] │ │
│  └────────────────────────────────────┘ │
│                                         │
│  ┌─ "Jokes about Big O" ─────────────┐ │
│  │  ❌ Generation failed.             │ │  ← error state for FAILED
│  │                            [Delete] │ │
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

**Component behaviors:**

- On load, fetches all joke generation jobs for the course via the API.
- Displays each job as a card showing the prompt, status, and (if completed) the generated jokes.
- On submit, calls the create endpoint (returns `202 Accepted`), adds the new job to the list in PENDING state, and subscribes to the job via `JobUpdateService`.
- When the WebSocket delivers a status update, the component re-fetches the specific job to get the full output data and updates the signal.
- Delete button calls the delete endpoint and removes the card from the list.

**Component structure:**

```
tools/joke-generator/
├── joke-generator.component.ts
├── joke-generator.component.html
├── joke-generator.component.scss
├── joke-generator.component.spec.ts
├── joke-generator.service.ts
├── joke-generator.service.spec.ts
```

### 2.3 Joke Generator Angular Service

**Location:** `frontend/src/app/courses/course-detail/tools/joke-generator/joke-generator.service.ts`

```typescript
@Injectable({ providedIn: 'root' })
export class JokeGeneratorService {
  private api = inject(Api);

  /** Creates a joke generation request (returns 202). */
  create(courseId: number, prompt: string): Promise<JokeRequest> { ... }

  /** Lists all joke generation requests for a course. */
  list(courseId: number): Promise<JokeRequest[]> { ... }

  /** Gets a single joke generation request by ID. */
  get(courseId: number, jobId: number): Promise<JokeRequest> { ... }

  /** Deletes a joke generation request. */
  delete(courseId: number, jobId: number): Promise<void> { ... }
}
```

### 2.4 Backend API — Joke Generation Routes

**Location:** `api/src/api/routes/joke_generation.py`

```
POST   /api/courses/{course_id}/jokes       → Create joke request (202)
GET    /api/courses/{course_id}/jokes       → List joke requests
GET    /api/courses/{course_id}/jokes/{id}  → Get single joke request
DELETE /api/courses/{course_id}/jokes/{id}  → Delete joke request
```

**Authorization:** All endpoints require the subject to be an instructor of the course. Uses `course_svc.authorize_instructor(subject, course)`.

**Create endpoint:**

1. Validates the prompt (non-empty, reasonable length).
2. Creates an `AsyncJob` with `kind="joke_generation"` and `input_data={"prompt": "..."}`.
3. Enqueues a `JokeGenerationJobPayload` to the Dramatiq job queue.
4. Returns the job summary with `202 Accepted`.

**Response models:**

```python
class JokeRequestResponse(BaseModel):
    id: int
    status: str  # pending, processing, completed, failed
    prompt: str
    jokes: list[str] | None  # null until completed
    error_message: str | None
    created_at: datetime

class JokeRequestListResponse(BaseModel):
    items: list[JokeRequestResponse]
```

The route handler extracts `prompt` from `input_data` and `jokes` from `output_data` to build the response — the generic `AsyncJob` table structure is hidden behind clean, domain-specific response models.

### 2.5 Core Service — `JokeGenerationService`

**Location:** `packages/learnwithai-core/src/learnwithai/services/joke_generation_service.py`

```python
class JokeGenerationService:
    def __init__(self, async_job_repo: AsyncJobRepository, job_queue: JobQueue):
        self._async_job_repo = async_job_repo
        self._job_queue = job_queue

    def create_request(self, subject: User, course_id: int, prompt: str) -> AsyncJob:
        """Creates a joke generation job and enqueues it for processing."""
        job = self._async_job_repo.create(AsyncJob(
            course_id=course_id,
            created_by_pid=subject.pid,
            kind="joke_generation",
            status=AsyncJobStatus.PENDING,
            input_data={"prompt": prompt},
        ))
        assert job.id is not None
        self._job_queue.enqueue(JokeGenerationJobPayload(job_id=job.id))
        return job

    def list_requests(self, course_id: int) -> list[AsyncJob]:
        """Returns all joke generation jobs for a course."""
        return self._async_job_repo.list_by_course_and_kind(course_id, "joke_generation")

    def get_request(self, job_id: int) -> AsyncJob | None:
        """Returns a single joke generation job."""
        return self._async_job_repo.get_by_id(job_id)

    def delete_request(self, job_id: int) -> None:
        """Deletes a joke generation job."""
        job = self._async_job_repo.get_by_id(job_id)
        if job is None:
            raise ValueError(f"Job {job_id} not found")
        self._async_job_repo.delete(job)
```

### 2.6 Background Job Handler — `JokeGenerationJobHandler`

**Location:** `packages/learnwithai-core/src/learnwithai/jobs/joke_generation.py`

```python
class JokeGenerationJobPayload(Job):
    type: Literal["joke_generation"] = "joke_generation"
    job_id: int

class JokeGenerationJobHandler(JobHandler[JokeGenerationJobPayload]):
    def handle(self, job: JokeGenerationJobPayload) -> None:
        # 1. Open a session (same pattern as RosterUploadJobHandler)
        # 2. Load the AsyncJob record, set status=PROCESSING, commit
        # 3. Extract prompt from input_data
        # 4. Call OpenAI API (see §2.7)
        # 5. Store jokes in output_data, set status=COMPLETED, commit
        # 6. Publish notification via JobNotifier
        # On failure: set status=FAILED, store error_message, commit, notify
```

### 2.7 OpenAI Integration

**Location:** `packages/learnwithai-core/src/learnwithai/services/openai_service.py`

A thin wrapper around the official `openai` Python library:

```python
class OpenAIService:
    """Thin wrapper for OpenAI Chat Completions API calls."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self._client = openai.OpenAI(api_key=api_key)
        self._model = model

    def generate_jokes(self, prompt: str, count: int = 5) -> list[str]:
        """Generates joke ideas for the given course content description."""
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": JOKE_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        return self._parse_jokes(response.choices[0].message.content, count)
```

**Configuration additions to `Settings`:**

```python
openai_api_key: str | None = None
openai_model: str = "gpt-4o-mini"
```

The key is required only when joke generation jobs run. The job handler reads it from settings at handle time.

**Dependency:** Add `openai>=1.0,<2` to `learnwithai-core`'s `pyproject.toml`.

---

## Part 3: Implementation Sequence

This is ordered to build foundations first, then layer features on top, with tests at every step.

### Phase 1: Unified Job Infrastructure (Backend)

| Step | What | Where |
|------|------|-------|
| 1.1 | Create `AsyncJob` table model with `kind`, `status`, JSON `input_data`/`output_data` | `learnwithai-core/tables/` |
| 1.2 | Create `AsyncJobRepository` | `learnwithai-core/repositories/` |
| 1.3 | Write `AsyncJobRepository` tests | `learnwithai-core/test/repositories/` |
| 1.4 | Define `JobUpdate` model and `JobNotifier` protocol in interfaces | `learnwithai-core/interfaces/` |
| 1.5 | Implement `RabbitMQJobNotifier` | `learnwithai-jobqueue/` |
| 1.6 | Implement `NoOpJobNotifier` for tests | `learnwithai-core/jobs/` |

### Phase 2: Migrate Roster Upload

| Step | What | Where |
|------|------|-------|
| 2.1 | Update `RosterUploadService` to use `AsyncJob` + `AsyncJobRepository` | `learnwithai-core/services/` |
| 2.2 | Update `RosterUploadJobHandler` to use new table + call `JobNotifier` | `learnwithai-core/jobs/` |
| 2.3 | Remove `RosterUploadJob` table and `RosterUploadRepository` | `learnwithai-core/` |
| 2.4 | Update roster upload API routes and response models | `api/routes/`, `api/models/` |
| 2.5 | Update DI factories for new repository/service signatures | `api/dependency_injection.py` |
| 2.6 | Update all roster upload tests | `api/test/`, `learnwithai-core/test/` |

### Phase 3: WebSocket Infrastructure

| Step | What | Where |
|------|------|-------|
| 3.1 | Add `aio-pika` dependency to `api/pyproject.toml` | `api/` |
| 3.2 | Implement `JobUpdateManager` (in-memory subscription tracker) | `api/src/api/` |
| 3.3 | Implement WebSocket endpoint with JWT auth from query param | `api/src/api/routes/ws.py` |
| 3.4 | Implement RabbitMQ consumer background task on API startup | `api/src/api/` |
| 3.5 | Register WebSocket route in the app | `api/src/api/routes/__init__.py`, `main.py` |
| 3.6 | Add `/api/ws` proxy config for WebSocket upgrade | `frontend/proxy.conf.json` |
| 3.7 | Write WebSocket endpoint tests | `api/test/` |

### Phase 4: Frontend WebSocket Service

| Step | What | Where |
|------|------|-------|
| 4.1 | Create `JobUpdateService` (singleton, manages WS connection + signals) | `frontend/src/app/` |
| 4.2 | Write `JobUpdateService` unit tests | `frontend/src/app/` |

### Phase 5: Joke Generator Feature

| Step | What | Where |
|------|------|-------|
| 5.1 | Add `openai` dependency to `learnwithai-core` | `pyproject.toml` |
| 5.2 | Add `openai_api_key`/`openai_model` to `Settings` | `learnwithai-core/config.py` |
| 5.3 | Create `OpenAIService` | `learnwithai-core/services/` |
| 5.4 | Create `JokeGenerationService` | `learnwithai-core/services/` |
| 5.5 | Create `JokeGenerationJobPayload` + `JokeGenerationJobHandler` | `learnwithai-core/jobs/` |
| 5.6 | Register job in `jobs/__init__.py` (add to union, handler map) | `learnwithai-core/jobs/` |
| 5.7 | Write service + handler tests | `learnwithai-core/test/` |
| 5.8 | Create API response/request models for jokes | `api/src/api/models/` |
| 5.9 | Create joke generation routes (CRUD) | `api/src/api/routes/` |
| 5.10 | Wire DI factories for joke generation service | `api/dependency_injection.py` |
| 5.11 | Register joke routes in the app | `api/routes/__init__.py` |
| 5.12 | Write API route tests | `api/test/routes/` |
| 5.13 | Run `pnpm api:sync` to regenerate frontend API client | `frontend/` |
| 5.14 | Add domain aliases to `frontend/src/app/api/models.ts` | `frontend/` |

### Phase 6: Frontend Joke Generator UI

| Step | What | Where |
|------|------|-------|
| 6.1 | Transform `Tools` component into card-based landing page with external template | `frontend/src/app/courses/course-detail/tools/` |
| 6.2 | Add `tools/jokes` child route in app.routes.ts | `frontend/src/app/app.routes.ts` |
| 6.3 | Create `JokeGeneratorService` (API calls) | `frontend/.../tools/joke-generator/` |
| 6.4 | Create `JokeGenerator` component (prompt form + request list) | `frontend/.../tools/joke-generator/` |
| 6.5 | Integrate `JobUpdateService` for real-time status updates | component wiring |
| 6.6 | Write component + service tests | `frontend/.../tools/joke-generator/` |

### Phase 7: Validation & Cleanup

| Step | What | Where |
|------|------|-------|
| 7.1 | Run full backend test suite | `uv run pytest` |
| 7.2 | Run frontend lint + tests | `pnpm lint && pnpm test:ci` |
| 7.3 | Run `./scripts/qa.sh --check` | repo root |
| 7.4 | Update dev_data.py if seed data needs joke examples | `learnwithai-core/` |
| 7.5 | Update documentation (README, AGENTS.md if patterns changed) | repo root |

---

## Part 4: Key Design Decisions & Tradeoffs

### Single `async_job` table with JSON columns vs. table-per-job-type

**Chosen:** Single table with JSON `input_data`/`output_data`.

- **Pro:** Zero schema changes for new job types. One repository, one set of queries.
- **Pro:** All jobs share the same status lifecycle, creation/completion timestamps, and authorization model (course membership).
- **Con:** Cannot index or query on job-specific fields inside JSON without extra work.
- **Tradeoff accepted:** We don't need to query on job internals yet. If we do, we add a computed column or a view.

### WebSocket vs. Server-Sent Events (SSE)

**Chosen:** WebSocket.

- **Pro:** Bidirectional — client can subscribe/unsubscribe to specific jobs dynamically.
- **Pro:** Single persistent connection — no reconnection overhead per subscription.
- **Con:** Slightly more complex than SSE.
- **Tradeoff accepted:** WebSockets are the standard for real-time web apps and Angular has no built-in SSE support, while the native `WebSocket` API is straightforward.

### `aio-pika` vs. `pika` with `run_in_executor`

**Chosen:** `aio-pika` for the API consumer.

- **Pro:** Native async/await integration with FastAPI's event loop.
- **Pro:** No thread pool overhead or blocking concerns.
- **Con:** One additional dependency (API package only).
- **Tradeoff accepted:** `aio-pika` is lightweight and purpose-built for this use case.

### Token in WebSocket query parameter vs. first-message auth

**Chosen:** Query parameter (`?token=<jwt>`).

- **Pro:** Authentication happens during the HTTP upgrade handshake — rejected connections never fully open.
- **Pro:** Simpler client code.
- **Con:** Token appears in server access logs (mitigated: JWTs are short-lived, 24h, and we control the server).
- **Tradeoff accepted:** This is the standard pattern for WebSocket auth in SPAs.

### Single fanout exchange vs. per-course/per-job routing

**Chosen:** Single fanout exchange, client-side filtering.

- **Pro:** Simplest possible RabbitMQ topology. One exchange, auto-deleting queues.
- **Con:** Every API instance receives every job update, even if no local client cares.
- **Tradeoff accepted:** At our scale (single digits of API instances, low job throughput), the filtering cost is negligible. If scale demands it, we can switch to a topic exchange with `course_id` routing keys later.

### Notification happens after commit, not inside the transaction

**Chosen:** Job handlers commit the status change, then call `notifier.notify()`.

- **Pro:** Clients never receive a notification for a status change that hasn't been persisted.
- **Con:** If the notification fails, the client won't know until it polls or reconnects. The job data is still correct in the database.
- **Tradeoff accepted:** "At most once" notification is fine because the client can always fall back to fetching the current state via the REST API. The WebSocket update is an optimization, not a source of truth.

---

## Part 5: File Inventory

### New Files

| File | Package |
|------|---------|
| `tables/async_job.py` | `learnwithai-core` |
| `repositories/async_job_repository.py` | `learnwithai-core` |
| `services/joke_generation_service.py` | `learnwithai-core` |
| `services/openai_service.py` | `learnwithai-core` |
| `jobs/joke_generation.py` | `learnwithai-core` |
| `jobs/noop_job_notifier.py` | `learnwithai-core` |
| `interfaces/jobs.py` (extend with `JobUpdate`, `JobNotifier`) | `learnwithai-core` |
| `rabbitmq_job_notifier.py` | `learnwithai-jobqueue` |
| `routes/ws.py` | `api` |
| `routes/joke_generation.py` | `api` |
| `models/joke_generation.py` | `api` |
| `job_update_manager.py` | `api` |
| `job-update.service.ts` | `frontend/src/app/` |
| `tools/tools.component.html` (new external template) | `frontend` |
| `tools/joke-generator/joke-generator.component.ts` | `frontend` |
| `tools/joke-generator/joke-generator.component.html` | `frontend` |
| `tools/joke-generator/joke-generator.component.scss` | `frontend` |
| `tools/joke-generator/joke-generator.service.ts` | `frontend` |
| + corresponding `.spec.ts` test files for all frontend files | `frontend` |
| + corresponding `test_*.py` files for all backend files | various |

### Modified Files

| File | Change |
|------|--------|
| `tables/__init__.py` | Add `AsyncJob`, remove `RosterUploadJob` |
| `jobs/__init__.py` | Add `JokeGenerationJobPayload` to union + handler map |
| `services/roster_upload_service.py` | Use `AsyncJob` + `AsyncJobRepository` |
| `jobs/roster_upload.py` | Use `AsyncJob`, call `JobNotifier` |
| `config.py` | Add `openai_api_key`, `openai_model` |
| `api/dependency_injection.py` | Add `AsyncJobRepository`, `JokeGenerationService`, `OpenAIService` DI |
| `api/routes/__init__.py` | Register new routers |
| `api/routes/roster_uploads.py` | Use `AsyncJob` responses |
| `api/models/roster_upload.py` | Update response models for unified job table |
| `api/main.py` | Add lifespan for RabbitMQ consumer, WebSocket route |
| `api/pyproject.toml` | Add `aio-pika` dependency |
| `core/pyproject.toml` | Add `openai` dependency |
| `frontend/proxy.conf.json` | Add `/api/ws` WebSocket proxy entry |
| `frontend/src/app/app.routes.ts` | Add `tools` children routes (jokes) |
| `frontend/src/app/courses/course-detail/tools/tools.component.ts` | Card-based landing page |
| `frontend/src/app/api/models.ts` | Add joke generation model aliases |
| `dev_data.py` | Optional: add sample joke jobs for dev seeding |
| Various test files | Update for new table/service signatures |

### Deleted Files

| File | Reason |
|------|--------|
| `tables/roster_upload_job.py` | Replaced by `async_job.py` |
| `repositories/roster_upload_repository.py` | Replaced by `async_job_repository.py` |
