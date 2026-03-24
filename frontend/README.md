# Frontend Workspace

This workspace contains the Angular frontend for LearnWithAI. If you are new to frontend development, treat this app as the browser-facing layer of the system: it renders UI, responds to user interaction, and calls the API.

The frontend should not own backend business rules. It should present data, collect input, and coordinate with the API cleanly.

## What Lives Here

```text
frontend/
|- src/
|  |- main.ts                  Angular bootstrap entrypoint
|  |- theme.scss               UNC Chapel Hill Material theme (light + dark)
|  |- styles.css               Global styles and Tailwind utilities
|  `- app/
|     |- app.component.ts      Root component (<router-outlet>)
|     |- app.routes.ts         Top-level lazy routes
|     |- auth.service.ts       Client-side auth integration
|     |- page-title.service.ts Signal-based toolbar/browser title service
|     |- theme.service.ts      Light/dark/system theme toggle
|     |- layout/               App shell (toolbar, sidenav, responsive layout)
|     |- courses/              Course feature routes (list, detail, create, etc.)
|     |- jwt/                  JWT callback route feature
|     |- api/generated/        Auto-generated HTTP client and models
|     `- api/models.ts         Domain-friendly type aliases (Course, User, etc.)
|- openapi.json                Exported OpenAPI spec (generated, do not edit)
|- ng-openapi-gen.json         Code generation configuration
|- public/                     Static public assets
|- package.json                Frontend scripts and dependencies
```

## Current Application Shape

The frontend uses Angular Material for UI components and Tailwind CSS (v4) for layout utilities. Theming follows the UNC Chapel Hill brand palette.

### App Shell

The `Layout` component in `src/app/layout/` provides a responsive shell:

- **Desktop**: A full-width toolbar on top with page title, theme toggle, and auth controls. A 240 px side-nav sits below the toolbar alongside the main content area.
- **Mobile**: The toolbar shows a hamburger menu, page title, and controls. The side-nav opens as an overlay when toggled.

### Page Titles

`PageTitleService` is a signal-based singleton that components call to set the toolbar heading and browser tab title. Every routed component calls `setTitle()` in its constructor (or after loading data) to keep the toolbar and tab in sync.

### Routes

Routes are declared in `src/app/app.routes.ts`. The default (`/`) redirects to `/courses`. Authenticated routes sit inside the `Layout` shell:

- `/courses` — course list (lazy loaded)
- `/courses/create` — create a new course
- `/courses/:id` — course detail with child tabs (roster, activities, tools)
- `/courses/:id/add-member` — add a member to a course
- `/jwt` — authentication callback

### Key Services

- `AuthService` — client-side auth integration
- `ThemeService` — light / dark / system theme toggle
- `PageTitleService` — reactive toolbar title and browser tab title
- `CourseService` — course API calls via generated client
- `SuccessSnackbarService` — shared helper that shows a success snackbar for 5 seconds. Use this instead of injecting `MatSnackBar` directly in components that save forms.
- `AuthTokenInterceptor` — attaches auth headers to `/api/*` requests

### Post-Save UX Pattern

After a form saves successfully, always:

1. Call `SuccessSnackbarService.open(message)` to show a 5-second success notification.
2. Navigate the user to the next useful destination (e.g. course dashboard after saving course settings, courses list after saving a profile).

Do **not** leave the user on the same page with an inline "saved" message.

## How To Run The Frontend

From the `frontend/` directory:

```bash
pnpm install
pnpm start
```

Or in VS Code, run the `start` task from the `frontend` workspace.

Then open `http://localhost:4200`.

## Playwright UI Testing

The frontend includes a Playwright end-to-end test harness rooted in `e2e/`.

### Running Playwright tests

From the `frontend/` directory:

```bash
pnpm test:e2e
pnpm test:e2e:headed
pnpm test:e2e:ui
```

The shared dev container installs Chromium for Playwright during post-create setup.

The default Playwright config starts the Angular dev server automatically when one is not already running and writes artifacts to `test-results/` and `playwright-report/`.

## MCP Servers

The repository now shares workspace MCP configuration for frontend agent workflows through `.vscode/mcp.json` at the repository root and in `frontend/.vscode/mcp.json` for folder-only usage.

The configured servers are:

- `angular-cli` for Angular-aware project tooling via `ng mcp`
- `playwright` for browser automation and agent-driven UI interaction

In the dev container, VS Code is configured with `chat.mcp.autoStart` so these servers are ready to start as soon as the workspace is trusted.

## API Client Code Generation

Frontend TypeScript models and HTTP client functions are auto-generated from the FastAPI OpenAPI specification using [ng-openapi-gen](https://github.com/cyclosproject/ng-openapi-gen). The generated code lives in `src/app/api/generated/` and should never be edited by hand.

### Regenerating the client

When the backend API changes (new routes, modified request/response models), regenerate the frontend client:

```bash
pnpm api:sync
```

This runs two steps:

1. `pnpm api:export` — exports the OpenAPI spec from the FastAPI app to `openapi.json`
2. `pnpm api:gen` — runs ng-openapi-gen to produce TypeScript models and service functions

After regenerating, update any frontend services or components that reference changed models and run the existing QA checks.

### How it works

- The API produces an OpenAPI 3.1 spec with clean operation IDs (e.g. `create_course`, not `create_course_api_courses_post`).
- `scripts/export_openapi.py` imports the FastAPI app and writes its spec to `frontend/openapi.json` without running the server.
- ng-openapi-gen reads `openapi.json` and writes type-safe Angular services and interfaces to `src/app/api/generated/`.
- Frontend services use the generated `Api` service's `invoke(fn, params)` method, which accepts generated endpoint functions (e.g. `listMyCourses`, `createCourse`) and returns `Promise<T>`.

### Conventions

- **Domain types:** Import domain types from `api/models` (e.g. `Course`, `User`, `Membership`), not from `api/generated/models/`. The barrel file `src/app/api/models.ts` maps generated names (`CourseResponse`, `UserProfile`) to clean domain names.
- **Service methods:** Use `this.api.invoke(generatedFn, params)` instead of manual `HttpClient` calls. This ensures URL paths, parameter shapes, and body types stay in sync with the backend spec.
- **Promises, not Observables:** `Api.invoke` returns `Promise<T>`. Services return `Promise<T>` and components use `async`/`await`. The `promises` option in ng-openapi-gen (default `true`) controls this; individual generated endpoint functions still use Observables internally, but `Api.invoke` converts via `firstValueFrom`.
- Do not add or modify files inside `src/app/api/generated/`. They are overwritten on every regeneration.
- When new models are generated, add domain aliases to `src/app/api/models.ts`.
- Generated files are excluded from Prettier, ESLint, and coverage reporting.

## Frontend QA Commands

From the `frontend/` directory:

```bash
pnpm format:check
pnpm lint
pnpm test:ci
pnpm test:e2e
```

If you want local autofixes first:

```bash
pnpm format
pnpm lint:fix
```

The repository-level final check is still run from the root:

```bash
./scripts/qa.sh --check
```

## How To Navigate This App

If you are tracing a frontend feature:

1. Start in `src/app/app.routes.ts` to find the route.
2. Open the route's component folder (e.g. `src/app/courses/course-list/`).
3. Check any supporting services (`course.service.ts`, `page-title.service.ts`).
4. Follow network calls into the API workspace.

If you are adding a new screen:

1. Create a focused component or feature folder under `src/app/`.
2. Add a route in `app.routes.ts` (inside the `Layout` children for authenticated pages).
3. Call `PageTitleService.setTitle()` from the new component to set the toolbar and tab title.
4. Add or update tests near the changed code.
5. Validate with linting and frontend tests.

## VS Code Support In This Workspace

This workspace includes:

- A `start` task for the dev server
- A `test` task for watch-mode testing
- A `Frontend: serve` launch configuration
- A `Frontend: test (Vitest)` launch configuration

Those are useful when you are still learning the CLI and want repeatable entrypoints.

The frontend uses Angular's Vitest-based unit test runner. To run and debug tests from the VS Code Testing view, install the recommended `Vitest` extension for this workspace. The frontend folder now includes a local `vitest.config.ts` so the extension can discover tests directly.
