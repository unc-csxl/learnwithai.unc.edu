# JOB_NOTIFICATION_FIXES.md

Refinement plan for the `feature/unified-async-jobs` branch. This file is **not committed**.

---

## Problem Summary

Three refinement areas identified after Part 1 implementation:

1. **Literate programming style violations** — `main.py` contains too much implementation detail (RabbitMQ consumer, message parsing). It should stay high-level.
2. **Frontend roster upload still polls** — The `Roster` component uses `setTimeout` polling instead of the new `JobUpdateService` WebSocket. Backend notifications only fire after final commit, not during progress.
3. **RosterUploadJobHandler has too much boilerplate** — Every future job handler would duplicate session/notifier setup, commit/rollback, and notification logic. This should be extracted into a reusable base.

---

## Step 1: Extract RabbitMQ consumer from `main.py` into its own module

**Goal**: `main.py` stays high-level (lifespan orchestration). Implementation details live in a dedicated module.

### Changes

- **New file**: `api/src/api/job_update_consumer.py`
  - Move `_handle_job_update_message()` and `_consume_job_updates()` here.
  - Rename to `handle_job_update_message()` and `consume_job_updates()` (public API).
- **Edit**: `api/src/api/main.py`
  - Remove the two moved functions.
  - Import from `api.job_update_consumer`.
  - `_lifespan` becomes a slim orchestrator: create manager → configure WS → start consumer task → yield → cancel.
- **Move tests**: `api/test/test_handle_job_update_message.py` → imports from new module.

### Commit boundary
`refactor: extract job update consumer from main.py`

---

## Step 2: Extract a reusable `BaseJobHandler` to reduce handler boilerplate

**Goal**: Session lifecycle, commit/rollback, and notification are handled once. Future handlers only implement `_execute()`.

### Changes

- **New file**: `packages/learnwithai-core/src/learnwithai/jobs/base_job_handler.py`
  ```python
  class BaseJobHandler(JobHandler[JobT]):
      """Reusable handler that owns session lifecycle and notification."""
      
      def handle(self, job: JobT) -> None:
          # Opens session, calls _execute(session, job), commits,
          # notifies on success. On failure: rollback, mark_failed,
          # commit, notify, re-raise.
      
      @abstractmethod
      def _execute(self, session: Session, job: JobT) -> None:
          """Subclasses implement their domain logic here."""
      
      def _build_notifier(self, settings: Settings) -> JobNotifier: ...
      def _notify(self, notifier, job_id, async_job_repo): ...
  ```

- **Edit**: `packages/learnwithai-core/src/learnwithai/jobs/roster_upload.py`
  - `RosterUploadJobHandler` extends `BaseJobHandler[RosterUploadJob]`.
  - Only implements `_execute()` which constructs repos, service, and calls `process_upload`.
  - All session/notifier/commit/rollback logic removed from this file.

- **Edit**: `packages/learnwithai-core/src/learnwithai/jobs/__init__.py`
  - Export `BaseJobHandler`.

- **Update tests**: `packages/learnwithai-core/test/test_jobs.py`
  - Adjust to test the base handler pattern.
  - Ensure commit/rollback/notify behavior is tested at the base level.

### Commit boundary
`refactor: extract BaseJobHandler to reduce job handler boilerplate`

---

## Step 3: Wire frontend roster upload to use WebSocket instead of polling

**Goal**: The `Roster` component subscribes to `JobUpdateService` on init, watches for job completion via signals, and stops polling.

### Changes

- **Edit**: `frontend/src/app/courses/course-detail/roster/roster.component.ts`
  - Inject `JobUpdateService`.
  - On init: `jobUpdateService.subscribe(this.courseId)`.
  - On destroy: `jobUpdateService.unsubscribe(this.courseId)`.
  - After `uploadRoster()` succeeds, create a computed signal via `jobUpdateService.updateForJob(jobId)` and use an `effect()` to watch for `completed`/`failed` status.
  - Remove `pollUploadStatus()` method and `pollTimer`.
  - Remove `POLL_INTERVAL_MS` constant.
  - Keep `getRosterUploadStatus()` call to fetch full status with counts when WS signals completion (the WS update only has `status`, not the full output data).

- **Edit**: `frontend/src/app/courses/course-detail/roster/roster.component.spec.ts`
  - Replace polling tests with WebSocket signal-based tests.
  - Mock `JobUpdateService` and simulate signal updates.

- **Edit (if needed)**: `frontend/src/app/courses/course.service.ts`
  - Keep `getRosterUploadStatus()` — still needed for fetching full result data after WS notification.

### Commit boundary
`feat: wire roster upload to WebSocket updates, remove polling`

---

## Step 4: Audit and fix backend notification during job progress

**Goal**: Currently notifications only fire after final `session.commit()`. The `process_upload` service method sets `PROCESSING` status via `_async_job_repo.update(job)` but the handler doesn't notify at that point. Add a `PROCESSING` notification so the frontend can show progress state.

### Changes

- **Edit**: `packages/learnwithai-core/src/learnwithai/jobs/base_job_handler.py`
  - The base handler should already own the notification lifecycle. Add a `PROCESSING` notification right before calling `_execute()`, after the session flush that persists the PROCESSING status change.
  - Actually, the service sets PROCESSING inside `_execute`. The cleanest approach: the base handler can accept a callback or be designed so that the service calls a notifier directly.
  - **Revised approach**: Since `process_upload()` already calls `self._async_job_repo.update(job)` to set PROCESSING, we can have the base handler do a mid-execution commit + notify after the status is set to PROCESSING. But this breaks atomicity.
  - **Simpler approach**: Accept that PROCESSING notification happens at the service level. Pass the notifier into the service so it can notify when it transitions to PROCESSING. This is cleaner — the service knows when it transitions states.

- **Edit**: `packages/learnwithai-core/src/learnwithai/services/roster_upload_service.py`
  - Add `notifier: JobNotifier` as an optional dependency (or add a `set_notifier()` method).
  - Actually, simplest: add `notifier: JobNotifier | None = None` param to `__init__`.
  - In `process_upload()`, after setting PROCESSING and calling `update()`, flush the session and call `notifier.notify()` if present.
  - Wait — the service doesn't own the session commit. The handler does. So we can't flush from the service without coupling it to session management.
  - **Final approach**: The base handler does a `session.flush()` + `notifier.notify(PROCESSING)` before calling `_execute()`, and then `_execute()` handles the domain logic. But `_execute()` is where PROCESSING gets set...
  - **Cleanest approach**: The base handler sets the job to PROCESSING status before calling `_execute()`, then notifies. The service's `process_upload()` no longer sets PROCESSING — the handler does it. This keeps notification ownership in the handler where session lifecycle lives.

### Revised Design

In `BaseJobHandler.handle()`:
1. Open session, load the AsyncJob
2. Set status = PROCESSING, flush, notify PROCESSING
3. Call `_execute(session, job)` — service does domain work, sets COMPLETED + output_data
4. Commit, notify final status
5. On error: rollback, mark_failed, commit, notify, re-raise

In `RosterUploadService.process_upload()`:
- Remove the `job.status = AsyncJobStatus.PROCESSING` line (handler does it)
- Keep the COMPLETED status + output_data setting

### Changes

- **Edit**: `packages/learnwithai-core/src/learnwithai/jobs/base_job_handler.py`
  - Load job, set PROCESSING, flush, notify, call `_execute`, commit, notify.
- **Edit**: `packages/learnwithai-core/src/learnwithai/services/roster_upload_service.py`
  - Remove the PROCESSING status transition from `process_upload()`.
- **Update tests** for both files.

### Commit boundary
Combined with Step 2 since they're tightly coupled:
`refactor: extract BaseJobHandler, add PROCESSING notification`

---

## Step 5: E2E test for WebSocket-based roster upload

**Goal**: Verify the end-to-end flow works with WebSocket delivery.

### Changes

- **Edit**: `frontend/e2e/roster.spec.ts`
  - The existing CSV upload e2e test should already work if the frontend properly uses WebSocket + fallback to status API for full data.
  - Verify test passes with the new WebSocket-based flow.
  - The test waits for the "Upload Results" dialog which now appears via WS notification + status fetch.

### Commit boundary
Part of the WebSocket wiring commit or a separate test fix commit if needed.

---

## Step 6: Code review for literate programming style across all branch files

**Goal**: Ensure all files on this branch follow literate style (public methods first, private helpers last).

### Files to audit
- `api/src/api/main.py` — After Step 1, should be clean
- `api/src/api/job_update_manager.py` — Already good (public methods first)
- `api/src/api/job_update_consumer.py` — New file, write it right
- `api/src/api/routes/ws.py` — Audit order
- `packages/learnwithai-core/src/learnwithai/jobs/roster_upload.py` — After Step 2, should be clean
- `packages/learnwithai-core/src/learnwithai/jobs/base_job_handler.py` — New file, write it right
- `packages/learnwithai-core/src/learnwithai/services/roster_upload_service.py` — Already mostly good
- `packages/learnwithai-core/src/learnwithai/repositories/async_job_repository.py` — Audit
- `packages/learnwithai-jobqueue/src/learnwithai_jobqueue/rabbitmq_job_notifier.py` — Audit
- `frontend/src/app/job-update.service.ts` — Audit order

### Commit boundary
`style: enforce literate programming style across branch files`

---

## Step 7: Final validation

1. Run `uv run pytest api/test` — all API tests pass
2. Run `uv run pytest packages/learnwithai-core/test` — all core tests pass
3. Run `uv run pytest packages/learnwithai-jobqueue/test` — all jobqueue tests pass
4. Run `pnpm test:ci` from `frontend/` — all frontend tests pass
5. Run `pnpm lint` from `frontend/` — no lint errors
6. Run `./scripts/qa.sh --check` — full QA green
7. Run e2e tests — roster upload flow works end-to-end

---

## Execution Order

| Order | Step | Commit |
|-------|------|--------|
| 1 | Extract consumer from main.py | `refactor: extract job update consumer from main.py` |
| 2 | Extract BaseJobHandler + PROCESSING notification | `refactor: extract BaseJobHandler, add PROCESSING notification` |
| 3 | Wire frontend to WebSocket | `feat: wire roster upload to WebSocket updates, remove polling` |
| 4 | Literate style review | `style: enforce literate programming style across branch files` |
| 5 | E2E + final QA | (no commit if tests already pass, or fix commit) |
