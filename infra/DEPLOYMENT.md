# Deployment Plan: LearnWithAI on OKD

This document describes how LearnWithAI is deployed to an OKD (OpenShift-origin) cluster today, including the current manifest-based workflow, operational scripts, and a Helm-based alternative.

## Goals

1. **Minimal tooling** — use plain Kubernetes/OKD YAML manifests, a small shell script, and `oc` (installed in the devcontainer for operator convenience).
2. **Foolproof initial setup** — a single `infra/scripts/deploy.sh` walks first-time operators through initial cluster deployment.
3. **Continuous deployment** — a push to `main` that passes QA triggers a GitHub Actions workflow that POSTs to an OKD webhook. OKD clones the private repository with its own deploy key, builds the image in-cluster, and rolls the app and worker forward through image stream triggers.
4. **Production-ready architecture** — FastAPI serves both the API and the pre-built Angular static assets behind a single Route, with PostgreSQL and RabbitMQ running as separate pods.

## Production Architecture

```
                ┌────────────────────────────────┐
                │         OKD Route (TLS)        │
                │   learnwithai.apps.example.com │
                └──────────────┬─────────────────┘
                               │
                   ┌───────────▼───────────┐
                   │    app (Deployment)    │
                   │ FastAPI + static files │
                   │    port 8000           │
                   └──┬──────────────┬──────┘
                      │              │
          ┌───────────▼──┐   ┌──────▼──────────┐
          │  PostgreSQL  │   │    RabbitMQ      │
          │ (Deployment) │   │  (Deployment)    │
          │  port 5432   │   │  port 5672       │
          └──────────────┘   └──────┬───────────┘
                                    │
                        ┌───────────▼───────────┐
                        │  worker (Deployment)   │
                        │  Dramatiq consumer     │
                        └────────────────────────┘
```

### Components

| Component    | Image / Source                                   | Replicas | Persistent Storage |
| ------------ | ------------------------------------------------ | -------- | ------------------ |
| **app**      | Custom Dockerfile (multi-stage) via BuildConfig  | 1        | None               |
| **worker**   | Same image as app                                | 1        | None               |
| **postgres** | `quay.io/sclorg/postgresql-16-c9s`               | 1        | PVC (1 Gi)         |
| **rabbitmq** | `rabbitmq:3-management`                          | 1        | None               |

Current operational profile:

- The app and worker use the same built image from the internal OpenShift registry.
- Standard Kubernetes Deployments are annotated with OpenShift image triggers so a fresh image stream tag automatically causes a rollout.
- PostgreSQL uses the OpenShift-compatible `quay.io/sclorg/postgresql-16-c9s` image.
- RabbitMQ uses TCP-based startup, readiness, and liveness probes so it can become Ready before the worker connects.
- Resource requests and limits are tuned for a modest single-developer namespace, not a production multi-user workload.

### How Requests Are Routed

In development, the Angular dev server proxies `/api/*` requests to FastAPI on port 8000, stripping the `/api` prefix. In production, we reproduce this behavior inside FastAPI itself:

- FastAPI mounts a `StaticFiles` handler at `/` to serve the pre-built Angular `browser/` output.
- API routes are mounted under `/api` (not at the root).
- The catch-all static handler returns `index.html` for any path that isn't a known file or API route, enabling Angular's client-side routing.

This means the production image is self-contained: one container serves both the SPA and the API with no external reverse proxy needed beyond the OKD Route.

## File Layout

```
infra/
├── DEPLOYMENT.md          ← this document
├── Dockerfile             ← multi-stage build (frontend + backend)
├── manifests/
│   ├── namespace.yaml     ← OKD project/namespace
│   ├── secrets.yaml       ← template for production secrets
│   ├── postgres.yaml      ← PostgreSQL Deployment + Service + PVC
│   ├── rabbitmq.yaml      ← RabbitMQ Deployment + Service
│   ├── app.yaml           ← BuildConfig + ImageStream + app Deployment + Service
│   ├── worker.yaml        ← Worker Deployment
│   └── route.yaml         ← OKD Route (TLS edge)
└── scripts/
    ├── deploy.sh          ← initial cluster deployment helper
    ├── destroy.sh         ← teardown helper with confirmation
    ├── reset_db.sh        ← developer DB reset + seed helper
    └── rollout.sh         ← image update + rollout (used by CI)
```

## Step-by-Step Plan

### Step 1: Make FastAPI serve static files in production

Modify `api/src/api/main.py` to:

- Prefix all API routes under `/api`.
- In production, mount a `StaticFiles` instance at `/` pointing at the built Angular assets.
- Add a catch-all HTML fallback so Angular routing works.

This keeps the development experience unchanged (Angular dev server still proxies `/api/*` to the root-mounted FastAPI routes) while enabling the single-container production story.

### Step 2: Create the multi-stage Dockerfile

A single `infra/Dockerfile` that:

1. **Stage 1 (frontend-build):** Installs pnpm, copies `frontend/`, runs `pnpm install --frozen-lockfile && pnpm build`.
2. **Stage 2 (backend):** Installs uv, copies Python workspace, runs `uv sync --no-dev`, copies the built frontend assets into the image, and sets the entrypoint to `uvicorn`.

The same image is used by both the `app` and `worker` Deployments with different commands.

### Step 3: Write OKD manifests

Plain YAML manifests using standard Kubernetes resources plus the OKD `Route` kind. No Helm, no Kustomize — just `oc apply -f`.

- **namespace.yaml** — creates the OKD project. The namespace is parameterized via `${NAMESPACE}` — scripts substitute the actual value at deploy time.
- **secrets.yaml** — a documented template with placeholder values that operators fill in before applying. Contains `DATABASE_URL`, `RABBITMQ_URL`, `JWT_SECRET`, etc.
- **postgres.yaml** — Deployment, Service, PVC for an OpenShift-compatible PostgreSQL 16 image.
- **rabbitmq.yaml** — Deployment and Service for RabbitMQ, using TCP startup/readiness/liveness probes to avoid readiness deadlock during broker startup.
- **app.yaml** — BuildConfig, ImageStream, webhook triggers, Deployment, and Service for the app container.
- **worker.yaml** — Deployment for the Dramatiq worker (same image, different command).
- **webhook-rbac.yaml** — namespace-local RoleBinding that grants `system:unauthenticated` the `system:webhook` role needed for inbound webhook calls.
- **route.yaml** — OKD Route with TLS edge termination.

### Step 4: Create deployment scripts

- **`infra/scripts/deploy.sh`** — guided first-time deployment. Takes the target namespace as a required argument, generates an SSH deploy key for OKD, pauses so the operator can add the public key to GitHub as a read-only deploy key, creates OKD source clone and webhook secrets, applies manifests in order, starts the initial build from the local checkout, waits for image-triggered rollouts, and prints the generic webhook URL to store in GitHub Actions.
- **`infra/scripts/rollout.sh`** — takes namespace as the first argument, streams the current local Git checkout into the existing BuildConfig with `oc start-build --from-repo`, waits for the build, and then waits for the app and worker Deployments to roll via image stream triggers.
- **`infra/scripts/destroy.sh`** — deletes the manifest-managed resources in reverse order with a confirmation prompt, and can optionally delete the namespace as well.
- **`infra/scripts/reset_db.sh`** — developer-oriented database reset workflow that scales app and worker to zero, drops and recreates the deployed database via the local PostgreSQL `postgres` superuser, mounts an audited bootstrap script from the local checkout into a one-off Job that uses the app image to create SQLModel tables and insert a dummy user, and restores the app and worker deployments even if an intermediate step fails.

### Step 5: Create the GitHub Actions CD workflow

A new workflow `.github/workflows/deploy.yml` that:

1. Triggers on push to `main` (only after QA passes by depending on the existing `qa` job).
2. Calls the OKD generic webhook URL stored as a GitHub Actions secret.
3. Passes the tested branch ref and commit SHA in the webhook payload so OKD builds the exact QA-approved revision.

### Step 6: Install `oc` in the devcontainer

Add `oc` CLI installation to `.devcontainer/Dockerfile` so developers can interact with the cluster for debugging, log tailing, and manual operations.

### Step 7: Update documentation

- Update `infra/README.md` with deployment instructions.
- Update root `README.md` with a deployment section.
- Add first-time setup instructions for operators.

## Current Operational Workflows

### Deploy

```bash
./infra/scripts/deploy.sh <your-namespace>
```

What it does:

- reuses the namespace if it already exists
- applies secrets and manifests
- builds the app image from the local working tree via `oc start-build --from-dir`
- waits for PostgreSQL, RabbitMQ, app, and worker rollouts

### Rollout

```bash
./infra/scripts/rollout.sh <your-namespace>
```

What it does:

- rebuilds the app image from the current working tree
- restarts the app and worker deployments
- waits for both rollouts

### Destroy

```bash
./infra/scripts/destroy.sh <your-namespace>
```

Optional flags:

- `--yes` to skip prompts
- `--delete-namespace` to remove the namespace too

### Reset Database

```bash
./infra/scripts/reset_db.sh <your-namespace>
```

What it does:

- scales app and worker to zero
- drops and recreates the configured PostgreSQL database
- creates a short-lived ConfigMap from `packages/learnwithai-core/scripts/bootstrap_deployment_db.py`
- runs a one-off bootstrap Job from the app image with that mounted script
- creates SQLModel tables
- inserts a dummy user for developer testing
- scales app and worker back to their previous replica counts

Dummy seeded user:

- `name`: `Demo User`
- `onyen`: `demo`
- `pid`: `999999999`
- `email`: `demo@example.com`

## Environment Variables for Production

| Variable               | Required | Notes                                        |
| ---------------------- | -------- | -------------------------------------------- |
| `ENVIRONMENT`          | Yes      | Set to `production`                          |
| `DATABASE_URL`         | Yes      | Full PostgreSQL connection string            |
| `RABBITMQ_URL`         | Yes      | Full AMQP connection string                  |
| `JWT_SECRET`           | Yes      | Strong random secret (≥32 chars)             |
| `HOST`                 | Yes      | Public URL (e.g. `learnwithai.apps.unc.edu`) |
| `UNC_AUTH_SERVER_HOST` | No       | Defaults to `csxl.unc.edu`                   |
| `LOG_LEVEL`            | No       | Defaults to `INFO`                           |

## Security Notes

- Secrets are stored in OKD `Secret` resources, never committed to the repository.
- The `secrets.yaml` manifest is a _template_ — it contains placeholder values and comments explaining each field.
- The GitHub Actions workflow does not need cluster login credentials. It only needs the OKD generic webhook URL.
- The OKD BuildConfig authenticates to GitHub using an SSH deploy key stored as a namespace secret.
- The production image runs as a non-root user.
- TLS is terminated at the OKD Route level (edge termination).

## Rollback

Rolling back is a single command (replace `<your-namespace>`):

```bash
oc rollout undo deployment/learnwithai-app -n <your-namespace>
oc rollout undo deployment/learnwithai-worker -n <your-namespace>
```

OKD retains previous ReplicaSets by default, making rollback instant.
