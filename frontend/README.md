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
|     |- home/                 Home route feature
|     `- jwt/                  JWT callback route feature
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
- A `Frontend: test` launch configuration

Those are useful when you are still learning the CLI and want repeatable entrypoints.
