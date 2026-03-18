# AGENTS.md

Read the repository root `AGENTS.md` first. This file adds API-specific guidance.

## Scope

This workspace owns FastAPI request handling, routing, dependency wiring, and HTTP responses.

## Expectations

- Keep route handlers thin.
- Put reusable business logic in `packages/learnwithai-core/`.
- Use dependency injection for sessions, settings, auth helpers, and shared services.
- Define DI types and factories in `src/api/dependency_injection.py`.
- Keep request body models explicit in route signatures with `Annotated[..., Body()]` when you need body metadata or want to signal API-layer ownership clearly.
- Do not add DI aliases or helper dependencies that derive values from request bodies. If a body field requires a database lookup, perform that lookup in the route logic and translate missing resources into the appropriate HTTP response there.
- Add Google-style docstrings to maintained Python modules and public functions.
- Keep type annotations explicit on public APIs.

## Testing And Validation

- Add or update tests in `api/test/` for route behavior and adapter logic.
- Run targeted tests with `uv run pytest api/test`.
- Before finishing, run `./scripts/qa.sh --check` from the repository root.