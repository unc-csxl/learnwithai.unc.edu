# Packages Workspace

This workspace contains the shared Python packages that sit underneath the API layer.

If you are new to the repository, this is where most reusable backend logic lives.

## What Lives Here

```text
packages/
|- learnwithai-core/
|  |- src/learnwithai/          Shared config, models, repositories, services, jobs, and tools
|  `- test/                     Tests for shared backend logic
`- learnwithai-jobqueue/
   |- src/learnwithai_jobqueue/ RabbitMQ and Dramatiq integration
   `- test/                     Tests for queue wiring
```

## Which Package Owns What?

### `learnwithai-core`

Put code here when it is shared backend logic and should not depend on FastAPI request handling.

Common examples:

- settings and environment handling
- database session helpers
- domain models and tables
- repositories
- services
- job definitions
- AI tool packages

If you find yourself writing business logic directly in an API route, stop and check whether it belongs here instead.

### `learnwithai-jobqueue`

Put code here when it connects shared jobs to infrastructure.

Common examples:

- Dramatiq broker setup
- queue adapter implementations
- RabbitMQ-based job notifications
- worker process entrypoints

## A Simple Rule Of Thumb

- If the code explains what the system does, it usually belongs in `learnwithai-core`.
- If the code explains how a background job gets delivered or executed, it usually belongs in `learnwithai-jobqueue`.

## How To Work In This Workspace

Run package-focused tests from the repository root:

```bash
uv run pytest packages/learnwithai-core/test
uv run pytest packages/learnwithai-jobqueue/test
```

When you finish backend package work, run:

```bash
./scripts/qa.sh --check
```

## Good First Files To Read

- `learnwithai-core/README.md`
- `learnwithai-core/src/learnwithai/config.py`
- `learnwithai-core/src/learnwithai/services/`
- `learnwithai-core/src/learnwithai/jobs/`
- `learnwithai-jobqueue/README.md`
- `learnwithai-jobqueue/src/learnwithai_jobqueue/worker.py`
