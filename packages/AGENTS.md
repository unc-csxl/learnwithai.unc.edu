# AGENTS.md

Read the repository root `AGENTS.md` first. This file adds shared-package guidance.

## Scope

This workspace contains backend packages that should stay reusable and framework-light.

## Expectations

- Put shared logic in `learnwithai-core`.
- Put queue and broker integration in `learnwithai-jobqueue`.
- Keep FastAPI-specific behavior out of these packages.
- Use explicit Python type annotations on public interfaces.
- Write Google-style docstrings for maintained modules, classes, and public functions.
- Prefer focused tests close to the package being changed.

## Validation

- Core package tests: `uv run pytest packages/learnwithai-core/test`
- Job queue tests: `uv run pytest packages/learnwithai-jobqueue/test`
- Final repository validation: `./scripts/qa.sh --check`