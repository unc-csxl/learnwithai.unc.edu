# AGENTS.md

This file is the repository-wide contribution guide for both human contributors and generative agents.

## Start Here

Before making changes:

1. Read `README.md` in the repository root.
2. Read the workspace-level `README.md` for the area you are touching.
3. Read the nearest `AGENTS.md` file for local rules.

If guidance conflicts, the more local `AGENTS.md` wins.

## Repository Expectations

- Keep architecture boundaries clear.
- Put shared business logic in `packages/learnwithai-core/`.
- Keep API route handlers thin and focused on HTTP concerns.
- In the API layer, use dependency injection for shared request-scoped services and path-derived resource loading, not for values derived from request bodies.
- Transaction lifecycle (commit/rollback/close) is owned by the `get_session` yield dependency in `learnwithai-core`. Route handlers must never call `session.commit()`, `session.rollback()`, or `session.begin()`.
- Keep queue wiring in `packages/learnwithai-jobqueue/`.
- Keep frontend components focused on UI concerns.
- Update documentation when behavior, architecture, commands, or workflows change.

## Service Design Conventions

Services in `learnwithai-core` are classes that declare all their dependencies (repositories, `JobQueue`, etc.) in `__init__`.

Write services in **literate code style**: public methods first (big picture), private helpers last (details). This means readers encounter the entry points before the implementation details.

The `JobQueue` protocol lives in `learnwithai/interfaces/jobs.py` so core services can accept it without importing from `learnwithai-jobqueue`. When a job handler constructs a service that does not need to submit jobs, it should use `ForbiddenJobQueue` (from `learnwithai.jobs`) to satisfy the constructor. `ForbiddenJobQueue` raises a `RuntimeError` if `enqueue` is ever called, which immediately surfaces any unexpected job submission instead of silently discarding it. Never make infrastructure dependencies optional in the constructor to work around this, provide an explicit guard instead.

## Parameter Ordering Convention

Whenever `subject` (the authenticated user) appears as a parameter in a service method or route handler, it must always come first. After `subject`, list additional domain model parameters in order from most generic to most specific (e.g., `course` before `target_user`). Service and repository parameters come last.

Correct: `def get_course_roster(self, subject: User, course: Course) -> ...`
Incorrect: `def get_course_roster(self, course: Course, subject: User) -> ...`

This applies uniformly to service methods in `learnwithai-core` and to FastAPI route handler signatures. Consistent ordering makes authorization intent immediately visible at every call site.

## Code Quality Rules

- Use explicit type annotations in Python for public functions, methods, and important variables when inference is not obvious.
- Keep TypeScript strict. Do not introduce `any` unless there is a documented and unavoidable reason.
- Prefer small, composable functions and services over large mixed-responsibility files.
- Write Google-style docstrings for Python modules, classes, and functions that are part of the maintained codebase.
- Keep comments high signal. Explain why or clarify non-obvious behavior, not line-by-line mechanics.

## SQLModel and Relationship Rules

- **Do not** use `from __future__ import annotations` in any file that defines a SQLModel `Relationship`. Postponed evaluation prevents SQLAlchemy from resolving forward-reference strings at class-creation time. Use `Optional["RelatedModel"]` from `typing` for forward references instead of `RelatedModel | None`.
- Repository methods that load related objects via eager loading should return domain objects directly (`list[Model]`).

## Testing Expectations

- New and changed behavior must be covered by automated tests.
- The repository target is full confidence, not minimal smoke coverage.
- Python changes should maintain the repository's 100% coverage expectation.
- Frontend changes should include or update Angular tests when behavior changes.
- Prefer targeted tests while developing, then run the full repository QA check before you complete a task.
- Keep shared test fixtures (like DB session fixtures) in the nearest common `conftest.py`. Do not duplicate fixtures across subdirectory conftest files.

## Validation Workflow

Use this order unless the task specifically requires something else:

1. Run targeted tests for the files or workspace you changed.
2. Run any local formatters or linters that apply.
3. Run `./scripts/qa.sh --check` before considering the task complete.

When you want local autofixes first, run:

```bash
./scripts/qa.sh
```

The final check before finishing a task is still:

```bash
./scripts/qa.sh --check
```

## Documentation Expectations

- Write for early career engineers, not only for experts.
- Explain intent and boundaries before details.
- Prefer concrete paths, commands, and examples over abstract descriptions.
- When a change affects setup, QA, architecture, or developer workflow, update the related README or AGENTS file in the same branch.

## Agent-Specific Guidance

- Do not guess how the repository works when a file can answer the question.
- Prefer the existing task, script, and workspace entrypoints over inventing new commands.
- Do not finish a task with unvalidated changes if the relevant QA commands can be run.
- If you touch multiple workspaces, check the documentation and AGENTS guidance for each one.
