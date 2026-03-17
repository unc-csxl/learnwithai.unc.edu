# Docs Workspace

This workspace stores project documentation that does not belong inside a single code package. Think of it as the place for design notes, migration plans, architecture decisions, and course-facing engineering context.

## What Lives Here

Current documents include:

- `flutter-to-typescript-migration.md`: notes from the transition into the current frontend stack
- `frontend-auth-plan.md`: planning material for frontend authentication work

## When To Put Something In `docs/`

Use this folder for documents that answer questions like:

- Why was this architectural decision made?
- What is the rollout plan for a larger change?
- What tradeoffs were considered?
- What should another engineer read before continuing a workstream?

Do not use `docs/` for information that should be the first thing every contributor sees. That belongs in the root `README.md` or a workspace-specific `README.md`.

## Writing Guidance

- Write for future students and early career engineers.
- Prefer concrete repository paths and commands.
- State assumptions clearly.
- Update docs when the related code changes enough to make the old explanation misleading.

## Recommended Reading Order

If you are new to the project:

1. Read the root `README.md`.
2. Read the relevant workspace `README.md`.
3. Read design notes in `docs/` for the feature area you are about to change.