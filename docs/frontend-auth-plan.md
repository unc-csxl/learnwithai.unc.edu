# Frontend Authentication — Implementation Plan

## Overview

Implement end-to-end login flow for the Angular frontend, connecting to the existing API auth system. Unauthenticated users see a welcome/login gate; authenticated users see a greeting with their name.

## Auth Flow

1. User clicks "Login" → browser navigates to `/auth/onyen` (API)
2. API redirects to UNC CSXL auth server
3. CSXL auth server redirects back to `/auth?token=...` (API)
4. API verifies token, registers/retrieves user, issues JWT
5. API redirects to `/jwt?token=<jwt>` (Angular route)
6. Angular captures the JWT from the query param, stores in `localStorage`
7. Angular loads the authenticated user's profile from a new API endpoint
8. Authenticated view shows "Hello, {name}"

## Steps

### Step 1: Backend — Add `/auth/me` API Endpoint

Add a new route `GET /auth/me` that:
- Reads the `Authorization: Bearer <token>` header
- Decodes the JWT to extract the user ID (`sub` claim)
- Looks up the user in the database via the `UserRepository`
- Returns the user's profile as JSON (`id`, `name`, `pid`, `onyen`, `email`)

This requires:
- A new dependency injection helper for extracting the authenticated user from a JWT
- A new route in `api/src/api/routes/auth.py`
- Full test coverage (unit + integration) in `api/test/test_routes_auth.py`
- Update `api/test/test_main.py` to assert the new route is registered

### Step 2: Backend — JWT Verification Service in Core

Add a `verify_jwt` method to `CSXLAuthService` (or a standalone function) that:
- Decodes a JWT using the configured secret/algorithm
- Returns the user ID from the `sub` claim
- Raises `AuthenticationException` on invalid/expired tokens

Add to `dependency_injection.py`:
- A `get_current_user` dependency that reads the `Authorization` header, verifies the JWT, and returns the `User` from the database

Full test coverage for the new service method and the DI helper.

### Step 3: Frontend — Auth Service

Create `src/app/auth.service.ts`:
- Singleton service (`providedIn: 'root'`)
- Uses `inject()` for dependencies
- Manages JWT token in `localStorage`
- Exposes a signal `user` (type `User | null`) for the current user
- Exposes a computed signal `isAuthenticated` based on whether `user()` is non-null
- `login()` method: navigates the browser to `/api/auth/onyen`
- `logout()` method: clears token from `localStorage`, sets `user` to `null`
- `handleToken(token: string)` method: stores token, then fetches user profile
- `fetchProfile()` method: calls `GET /api/auth/me` with Bearer token, sets `user` signal
- On initialization, if a token exists in `localStorage`, attempt to load the profile

Create `src/app/user.model.ts`:
- `User` interface: `{ id: string; name: string; pid: string; onyen: string; email: string | null }`

### Step 4: Frontend — JWT Callback Route

Create `src/app/jwt/jwt.ts` component:
- Route: `/jwt`
- Reads `token` query parameter
- Calls `AuthService.handleToken(token)`
- Redirects to `/` after storing

### Step 5: Frontend — Welcome/Login Gate Component

Create `src/app/home/home.ts` component:
- Route: `/` (default)
- Uses `AuthService` to check `isAuthenticated` signal
- If not authenticated: shows welcome message + "Login" button that calls `AuthService.login()`
- If authenticated: shows "Hello, {user.name}"

### Step 6: Frontend — App Routing & Proxy Configuration

Update `src/app/app.routes.ts`:
- Add route `/` → `HomeComponent`
- Add route `/jwt` → `JwtComponent`

Update `src/app/app.html`:
- Replace placeholder content with just `<router-outlet />`

Update `src/app/app.ts`:
- Remove the title signal (not needed)

Configure Angular dev server proxy:
- Add proxy config so `/api/**` requests are forwarded to `http://localhost:8000`
- This maps `/api/auth/onyen` → `http://localhost:8000/auth/onyen`, etc.

### Step 7: Frontend — provideHttpClient

Update `src/app/app.config.ts`:
- Add `provideHttpClient()` to providers

### Step 8: Full Test Coverage

**Backend tests:**
- `test_routes_auth.py`: Tests for `GET /auth/me` (success, missing token, invalid token, user not found)
- `test_csxl_auth_service.py`: Test for `verify_jwt` method

**Frontend tests:**
- `auth.service.spec.ts`: Tests for all `AuthService` methods
- `jwt.spec.ts`: Tests for JWT callback component
- `home.spec.ts`: Tests for authenticated/unauthenticated views
- Update `app.spec.ts` for the new app structure

### Step 9: Verify QA

Run `./scripts/qa.sh` and ensure:
- All Python tests pass with 100% coverage
- All Angular tests pass
- Linting/formatting passes

## File Changes Summary

### New files:
- `frontend/src/app/auth.service.ts`
- `frontend/src/app/auth.service.spec.ts`
- `frontend/src/app/user.model.ts`
- `frontend/src/app/jwt/jwt.ts`
- `frontend/src/app/jwt/jwt.spec.ts`
- `frontend/src/app/home/home.ts`
- `frontend/src/app/home/home.spec.ts`
- `frontend/proxy.conf.json`

### Modified files:
- `api/src/api/routes/auth.py` — Add `GET /auth/me`
- `api/src/api/dependency_injection.py` — Add JWT verification DI
- `api/test/test_routes_auth.py` — Tests for `/auth/me`
- `api/test/test_main.py` — Assert new route registered
- `packages/learnwithai-core/src/learnwithai/services/csxl_auth_service.py` — Add `verify_jwt`
- `packages/learnwithai-core/test/test_csxl_auth_service.py` — Test `verify_jwt`
- `frontend/src/app/app.config.ts` — Add `provideHttpClient()`
- `frontend/src/app/app.routes.ts` — Add routes
- `frontend/src/app/app.html` — Replace placeholder
- `frontend/src/app/app.ts` — Simplify
- `frontend/src/app/app.spec.ts` — Update tests
- `frontend/angular.json` — Add proxy config
