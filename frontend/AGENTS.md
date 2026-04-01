Read the repository root `AGENTS.md` first. This file adds frontend-specific rules.

## Scope

This workspace owns browser UI, route composition, forms, and frontend-side coordination with the generated API client.

Keep reusable business rules out of this layer when they belong in the backend packages.

## Validation

- Add or update Angular tests for new or changed behavior.
- Run `pnpm format:check`, `pnpm lint`, and `pnpm test:ci` from `frontend/`.
- Finish with `./scripts/qa.sh --check` from the repository root.

## App Shell And Titles

- `Layout` owns the authenticated shell.
- Every routed component must call `PageTitleService.setTitle()`.
- Do not add page-title `<h1>` elements to routed pages. The toolbar already displays the page title.

## Generated API Client

- Do not edit `src/app/api/generated/`.
- Import domain types from `src/app/api/models.ts`.
- Use `Api.invoke(...)` with generated endpoint functions.
- If backend request or response shapes change, run `pnpm api:sync` and update affected frontend code.

## Frontend Conventions

- Keep TypeScript strict. Do not introduce `any` without a strong reason.
- Prefer signals for local state and `computed()` for derived state.
- Use `ChangeDetectionStrategy.OnPush` on components.
- Prefer Reactive Forms.
- Use native control flow (`@if`, `@for`, `@switch`) in templates.
- Keep theme usage on shared tokens through `ThemeService` and `src/theme.scss`. Do not hard-code brand colors.

## Real-Time Job Updates

`JobUpdateService` manages the WebSocket connection to `/api/ws/jobs`.

- Call `subscribe(courseId)` when entering a course context.
- Call `unsubscribe(courseId)` when leaving that context.
- Use `updatesForCourse(courseId)` or `updateForJob(jobId)` to read current status as signals.

## Post-Save UX

After a successful save:

1. Show a success snackbar with `SuccessSnackbarService`.
2. Navigate the user to the next useful page.

Do not leave users on the same page with an inline "saved" message.
