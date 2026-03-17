# Packages Workspace

This workspace contains shared Python packages that sit underneath the API adapter.

The goal of the `packages/` directory is separation of concerns:

- `learnwithai-core` contains reusable domain and application logic
- `learnwithai-jobqueue` contains background job and broker integration

Keeping these packages separate makes the system easier to test, reason about, and reuse.

## Workspace Layout

```text
packages/
|- learnwithai-core/
|  |- src/learnwithai/         Shared configuration, models, repositories, services, jobs
|  `- test/                    Tests for the core package
`- learnwithai-jobqueue/
   |- src/learnwithai_jobqueue/ Broker wiring and worker entrypoints
   `- test/                     Tests for queue integration
```

## `learnwithai-core`

This package is where shared backend logic should usually go first.

It currently contains areas such as:

- `config.py` for environment-backed settings
- `db.py` for database support
- `models/` for domain models
- `repositories/` for persistence access
- `services/` for application and integration logic
- `jobs/` for job definitions that can be queued

If you are tempted to put domain logic into a FastAPI route, stop and consider whether it belongs here instead.

## `learnwithai-jobqueue`

This package connects the core job abstractions to Dramatiq and the message broker.

It currently contains:

- `broker.py` for broker setup
- `dramatiq_job_queue.py` for queue adapter wiring
- `worker.py` for the worker process entrypoint

## How To Work In This Workspace

Run focused tests from the repository root:

```bash
uv run pytest packages/learnwithai-core/test
uv run pytest packages/learnwithai-jobqueue/test
```

When you finish backend package work, run:

```bash
./scripts/qa.sh --check
```

## Good First Files To Read

- `learnwithai-core/src/learnwithai/config.py`
- `learnwithai-core/src/learnwithai/services/`
- `learnwithai-core/src/learnwithai/jobs/`
- `learnwithai-jobqueue/src/learnwithai_jobqueue/dramatiq_job_queue.py`
- `learnwithai-jobqueue/src/learnwithai_jobqueue/worker.py`