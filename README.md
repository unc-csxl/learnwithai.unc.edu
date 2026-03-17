# LearnWithAI

LearnWithAI is a course project for COMP423: Foundations of Software Engineering. It is intentionally organized as a small full-stack system instead of a single app so you can practice working across service boundaries, shared packages, background jobs, and a modern frontend.

At a high level, the system has five moving parts:

- An Angular frontend in `frontend/`
- A FastAPI HTTP adapter in `api/`
- Shared Python domain code in `packages/learnwithai-core/`
- A Dramatiq worker in `packages/learnwithai-jobqueue/`
- Supporting development infrastructure in `.devcontainer/` and `infra/`

The repository is designed to work especially well in VS Code with the multi-root workspace file `learnwithai.code-workspace`.

## Quick Start

### Recommended setup: VS Code + Dev Container

1. Open `learnwithai.code-workspace` in VS Code.
2. Reopen the repository in the dev container when VS Code prompts you.
3. Wait for the post-create setup to finish. It installs Python dependencies with `uv` and frontend dependencies with `pnpm`.
4. Start the app stack:
   - Frontend: run the `start` task from the `frontend` workspace, or run `cd frontend && pnpm start`
   - API: run the `api: run` task from the repository workspace
   - Worker: run the `job queue: run` task from the repository workspace
5. Open the running services:
   - Frontend: `http://localhost:4200`
   - API health check: `http://localhost:8000/health`
   - RabbitMQ management UI: `http://localhost:15672`

The dev container also starts PostgreSQL and RabbitMQ for you through Docker Compose.

## QA Quick Start

The repository-level quality gate is `scripts/qa.sh`.

- Local autofix + validation: `./scripts/qa.sh`
- CI-equivalent non-mutating check: `./scripts/qa.sh --check`

What it runs:

- Ruff formatting and linting for Python
- Pyright type checking
- Pytest with coverage across the Python workspaces
- Prettier, ESLint, and Angular tests in the frontend workspace

If you are not sure whether your work is ready, run `./scripts/qa.sh --check`. That is the closest local match to the GitHub Actions workflow.

## How The Repository Is Organized

```text
.
|- api/                         FastAPI adapter layer
|- docs/                        Design notes and course-facing documentation
|- frontend/                    Angular application
|- infra/                       Infrastructure support files
|- packages/
|  |- learnwithai-core/         Shared domain logic, models, services, repositories
|  |- learnwithai-jobqueue/     Dramatiq broker and worker integration
|- scripts/                     Repository automation, including QA entrypoints
|- .devcontainer/               Recommended local development environment
|- .github/workflows/           CI workflows
|- learnwithai.code-workspace   VS Code multi-root workspace
```

### Architecture boundaries

- `frontend/` owns browser UI and user interaction.
- `api/` owns HTTP routes and request/response concerns.
- `packages/learnwithai-core/` owns shared business logic, configuration, data access, and jobs.
- `packages/learnwithai-jobqueue/` owns the queue adapter and worker bootstrapping.
- `scripts/` owns repeatable repository commands, especially QA.

When you add logic, try to put it in the deepest reusable layer that makes sense. For example, route handlers should stay thin, and shared business logic should usually live in `learnwithai-core` instead of in FastAPI route files.

## What Is Running Right Now?

Current source entrypoints are intentionally small so you can trace the system quickly:

- The API app is created in `api/src/api/main.py`
- Health and queue demo routes live in `api/src/api/routes/health.py`
- Authentication routes live in `api/src/api/routes/auth.py`
- Shared environment-backed settings live in `packages/learnwithai-core/src/learnwithai/config.py`
- The worker entrypoint is `packages/learnwithai-jobqueue/src/learnwithai_jobqueue/worker.py`
- The frontend router starts in `frontend/src/app/app.routes.ts`

That means you can usually understand a feature by following this path:

1. Start in the frontend route or component.
2. Find the API endpoint it calls.
3. Trace any domain logic into `learnwithai-core`.
4. If background work is involved, follow it into `learnwithai-jobqueue`.

## Working In VS Code

This repository is easiest to navigate through the multi-root workspace.

### Explorer

The workspace is split into focused folders:

- `frontend`: Angular app files and frontend VS Code tasks
- `api`: FastAPI adapter code
- `core`: shared Python package from `packages/learnwithai-core`
- `job_queue`: worker package from `packages/learnwithai-jobqueue`
- `infra`: infrastructure support files
- `repo`: repository-wide files like `.github/`, `.devcontainer/`, and `scripts/`

Use that split to decide where a change belongs before you start editing.

### Run Task

Useful task entrypoints include:

- `start` in the `frontend` workspace
- `test` in the `frontend` workspace
- `repo: uv sync` in the repository workspace
- `api: run` in the repository workspace
- `job queue: run` in the repository workspace

Tasks are a good default when you are new to the repo because they encode the expected working directory and command.

### Run And Debug

The repository includes launch configurations for:

- `Frontend: serve`
- `API: FastAPI`
- `Worker: Dramatiq`
- A workspace-level compound called `Debug Frontend + API + Worker`

If you want to understand how requests move through the system, running the debugger across all three services is a practical way to learn.

### Search And Navigation

Good first searches when you are exploring:

- Route paths in `frontend/src/app/`
- FastAPI routers in `api/src/api/routes/`
- Shared services and repositories in `packages/learnwithai-core/src/learnwithai/`
- Queue integration in `packages/learnwithai-jobqueue/src/learnwithai_jobqueue/`

## Common Development Workflows

### Frontend-only work

- Start in `frontend/src/app/`
- Run the frontend dev server
- Validate with `cd frontend && pnpm lint && pnpm test:ci`

### API or backend work

- Start in `api/src/api/` or `packages/learnwithai-core/src/learnwithai/`
- Run the API task, and the worker if your change touches background jobs
- Validate with targeted pytest runs, then `./scripts/qa.sh --check`

### Queue-related work

- Read the route or service that enqueues the job
- Read the job definition in `learnwithai-core`
- Read the broker and worker wiring in `learnwithai-jobqueue`
- Validate with worker tests and then full repo QA

### Cross-stack feature work

- Update the frontend route or component
- Update or add the API contract
- Move shared rules into `learnwithai-core`
- Add tests at every layer you changed

## Where To Read Next

After this README, the next documents to read are:

- `AGENTS.md` for contribution and agent expectations
- `api/README.md` for the FastAPI workspace
- `frontend/README.md` for the Angular workspace
- `packages/README.md` for shared package boundaries
- `scripts/README.md` for QA and automation commands

If you are brand new to the project, read them in that order.