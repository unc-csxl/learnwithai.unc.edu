# learnwithai-core

`learnwithai-core` is the shared backend package for LearnWithAI. It contains the reusable logic that should not depend on FastAPI request handling or Angular UI code.

## What Belongs Here

- Configuration models and helpers
- Domain models
- Repositories and persistence logic
- Shared services
- Job definitions that can be queued by the worker

## Typical Directory Roles

- `src/learnwithai/config.py`: application settings
- `src/learnwithai/db.py`: database helpers
- `src/learnwithai/models/`: domain entities and schemas
- `src/learnwithai/repositories/`: data access
- `src/learnwithai/services/`: shared business logic
- `src/learnwithai/jobs/`: queueable job definitions
- `test/`: package-focused pytest suite

## Development Notes

- Keep this package framework-light and reusable.
- Prefer pure or narrowly scoped logic where possible.
- If a service is useful to both the API and the worker, it almost certainly belongs here.

Run tests from the repository root with:

```bash
uv run pytest packages/learnwithai-core/test
```