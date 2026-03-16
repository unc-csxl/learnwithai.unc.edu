# Migration Plan: Flutter → TypeScript/Angular Frontend

## Overview

The project was initially scaffolded with Flutter in mind for the client application.
The decision has been made to use a modern TypeScript stack (likely Angular) instead.
This plan removes all Flutter/Dart tooling and replaces it with Node.js/TypeScript
support in the devcontainer, workspace configuration, and CI scripts.

---

## Steps

### 1. Create a WIP branch

```bash
git checkout -b wip/flutter-to-typescript
```

### 2. Remove Flutter from the Dockerfile

**File:** `.devcontainer/Dockerfile`

- Remove the `FLUTTER_VERSION` build arg.
- Remove packages only needed for Flutter/Dart: `clang`, `cmake`, `libgtk-3-dev`,
  `libstdc++-12-dev`, `ninja-build`, `openjdk-17-jdk`, `pkg-config`, `xz-utils`.
- Remove the `git clone` of the Flutter SDK and `FLUTTER_HOME` / `PATH` entries.
- Remove the `flutter config` / `dart --disable-analytics` / `flutter doctor` warm-up.
- **Add** Node.js (LTS) installation via the NodeSource setup script or `nvm`.
- Install `npm` (comes with Node) and optionally `pnpm` or keep npm only.

### 3. Update `compose.yaml`

**File:** `.devcontainer/compose.yaml`

- Remove `FLUTTER_HOME`, `PUB_CACHE`, and Flutter `PATH` entries from `environment`.
- Remove the `learnwithai-pub-cache` volume (both the mount and the volume definition).
- Add a named volume for the npm/node_modules cache if desired.

### 4. Update `devcontainer.json`

**File:** `.devcontainer/devcontainer.json`

- Remove the `dart-code.flutter` extension.
- Add TypeScript/Angular extensions:
  - `dbaeumer.vscode-eslint`
  - `esbenp.prettier-vscode`
  - `angular.ng-template` (Angular Language Service)
- Forward port `4200` (Angular dev server default) and label it.
- Add Node/TS-friendly VS Code settings to the devcontainer customizations.

### 5. Update `post-create.sh`

**File:** `.devcontainer/post-create.sh`

- Remove the `pub-cache` ownership fix.
- Remove the `flutter pub get` block.
- Add: if `frontend/package.json` exists → `cd frontend && npm install`.

### 6. Update `.gitignore`

**File:** `.gitignore`

- Remove the "Flutter / Dart" section (`.dart_tool/`, `.flutter-plugins`, etc.).
- Remove `client/.android/`, `client/.ios/`, etc.
- Remove `coverage/` under "Dart / Flutter coverage" (keep if reused for TS coverage).
- Remove `.devcontainer/.dart_tool/`.
- Strengthen the "Node / web tooling" section:
  - Ensure `node_modules/`, `dist/`, `.angular/`, `.nx/` are listed.

### 7. Add the `frontend/` workspace root

- Create `frontend/` directory with a minimal scaffold:
  - `frontend/package.json` — empty project placeholder (name, version, private flag).
  - `frontend/tsconfig.json` — strict TypeScript config.
  - `frontend/.vscode/settings.json` — Node/TS developer niceties.
  - `frontend/.vscode/extensions.json` — recommended extensions for the root.
  - `frontend/README.md` — brief explanation that Angular project goes here.

### 8. Update the workspace file

**File:** `learnwithai.code-workspace`

- Add a `"frontend"` folder entry pointing to `frontend/`.
- Add Node/TS file exclusions (`node_modules/`, `dist/`, `.angular/`).

### 9. Update `scripts/qa.sh`

**File:** `scripts/qa.sh`

- Add a frontend lint/type-check step that runs only when `frontend/package.json` exists.
  (This keeps the script safe until Angular is actually scaffolded.)

### 10. Verify & commit

- Rebuild the devcontainer conceptually (verify the Dockerfile is valid).
- Run `scripts/qa.sh` to confirm Python side is unaffected.
- Make incremental commits along the way, then squash or keep as-is for review.

---

## Out of Scope

- Actually scaffolding the Angular application (`ng new`). That will happen
  after this branch merges.
- Changing any backend Python code.
- CI/CD pipeline changes (handled separately once Angular is in place).
