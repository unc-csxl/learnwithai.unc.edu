# Frontend Workspace

This workspace contains the Angular frontend for LearnWithAI. If you are new to frontend development, treat this app as the browser-facing layer of the system: it renders UI, responds to user interaction, and calls the API.

The frontend should not own backend business rules. It should present data, collect input, and coordinate with the API cleanly.

## What Lives Here

```text
frontend/
|- src/
|  |- main.ts                  Angular bootstrap entrypoint
|  `- app/
|     |- app.ts                Root shell component
|     |- app.routes.ts         Top-level lazy routes
|     |- auth.service.ts       Client-side auth integration
|     |- api/generated/        Auto-generated HTTP client and models
|     |- api/models.ts         Domain-friendly type aliases (Course, User, etc.)
|     |- home/                 Home route feature
|     `- jwt/                  JWT callback route feature
|- openapi.json                Exported OpenAPI spec (generated, do not edit)
|- ng-openapi-gen.json         Code generation configuration
|- public/                     Static public assets
|- .vscode/                    Frontend-specific tasks and launch configs
|- package.json                Frontend scripts and dependencies
```

## Current Application Shape

Today the app is intentionally small so it is easy to understand:

- The root shell is in `src/app/app.ts`
- Routes are declared in `src/app/app.routes.ts`
- The home screen is lazy loaded from `src/app/home/`
- The authentication callback route is lazy loaded from `src/app/jwt/`
- Auth-related client behavior lives in `src/app/auth.service.ts`
- API authentication headers are attached centrally by `src/app/auth-token.interceptor.ts` for requests to `/api/*`

That makes the frontend a good place to learn three ideas at once:

- Component-based UI
- Client-side routing
- Calling backend services from the browser

## How To Run The Frontend

From the `frontend/` directory:

```bash
pnpm install
pnpm start
```

Or in VS Code, run the `start` task from the `frontend` workspace.

Then open `http://localhost:4200`.

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
- **Promises, not Observables:** `Api.invoke` returns `Promise<T>`. Services return `Promise<T>` and components use `.then()` or `await`.
- Do not add or modify files inside `src/app/api/generated/`. They are overwritten on every regeneration.
- When new models are generated, add domain aliases to `src/app/api/models.ts`.
- Generated files are excluded from Prettier, ESLint, and coverage reporting.

## Frontend QA Commands

From the `frontend/` directory:

```bash
pnpm format:check
pnpm lint
pnpm test:ci
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

1. Start in `src/app/app.routes.ts`.
2. Open the route's component folder.
3. Check any supporting services such as `auth.service.ts`.
4. Follow network calls into the API workspace.

If you are adding a new screen:

1. Create a focused component or feature folder under `src/app/`.
2. Add a route in `app.routes.ts`.
3. Add or update tests near the changed code.
4. Validate with linting and frontend tests.

## VS Code Support In This Workspace

This workspace includes:

- A `start` task for the dev server
- A `test` task for watch-mode testing
- A `Frontend: serve` launch configuration
- A `Frontend: test (Vitest)` launch configuration

Those are useful when you are still learning the CLI and want repeatable entrypoints.

The frontend uses Angular's Vitest-based unit test runner. To run and debug tests from the VS Code Testing view, install the recommended `Vitest` extension for this workspace. The frontend folder now includes a local `vitest.config.ts` so the extension can discover tests directly.
