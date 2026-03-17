# Deployment Plan: LearnWithAI on OKD

This document describes how to deploy LearnWithAI to an OKD (OpenShift-origin) cluster with continuous delivery from GitHub Actions.

## Goals

1. **Minimal tooling** — use plain Kubernetes/OKD YAML manifests, a small shell script, and `oc` (installed in the devcontainer for operator convenience).
2. **Foolproof initial setup** — a single `infra/scripts/deploy.sh` walks first-time operators through initial cluster deployment.
3. **Continuous deployment** — a push to `main` that passes QA triggers a GitHub Actions workflow that uploads the checked-out repository as a binary build source, builds container images in OKD, and rolls out the new version.
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

| Component   | Image / Source              | Replicas | Persistent Storage |
|-------------|-----------------------------|----------|--------------------|
| **app**     | Custom Dockerfile (multi-stage) via binary build | 1 | None |
| **worker**  | Same image as app           | 1        | None               |
| **postgres**| `quay.io/sclorg/postgresql-16-c9s` | 1 | PVC (1 Gi)         |
| **rabbitmq**| `rabbitmq:3-management`     | 1        | None               |

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
- **rabbitmq.yaml** — Deployment, Service for RabbitMQ.
- **app.yaml** — BuildConfig, ImageStream, Deployment, and Service for the app container.
- **worker.yaml** — Deployment for the Dramatiq worker (same image, different command).
- **route.yaml** — OKD Route with TLS edge termination.

### Step 4: Create deployment scripts

- **`infra/scripts/deploy.sh`** — guided first-time deployment. Takes the target namespace as a required argument, substitutes `${NAMESPACE}` placeholders in manifests via `envsubst`, checks prerequisites (`oc` logged in), applies manifests in order, uploads the local repository checkout as the initial binary build source, waits for rollouts, and runs a health check.
- **`infra/scripts/rollout.sh`** — takes namespace as the first argument, uploads the checked-out repository via `oc start-build --from-repo`, waits for the build, then triggers a rollout. Used by CI, can also be run manually.

### Step 5: Create the GitHub Actions CD workflow

A new workflow `.github/workflows/deploy.yml` that:

1. Triggers on push to `main` (only after QA passes by depending on the existing `qa` job).
2. Logs into the OKD cluster using a service account token stored as a GitHub secret.
3. Triggers the build and rollout via `oc` commands against the checked-out workflow commit.

### Step 6: Install `oc` in the devcontainer

Add `oc` CLI installation to `.devcontainer/Dockerfile` so developers can interact with the cluster for debugging, log tailing, and manual operations.

### Step 7: Update documentation

- Update `infra/README.md` with deployment instructions.
- Update root `README.md` with a deployment section.
- Add first-time setup instructions for operators.

## Environment Variables for Production

| Variable               | Required | Notes                                  |
|------------------------|----------|----------------------------------------|
| `ENVIRONMENT`          | Yes      | Set to `production`                    |
| `DATABASE_URL`         | Yes      | Full PostgreSQL connection string      |
| `RABBITMQ_URL`         | Yes      | Full AMQP connection string            |
| `JWT_SECRET`           | Yes      | Strong random secret (≥32 chars)       |
| `HOST`                 | Yes      | Public URL (e.g. `learnwithai.apps.unc.edu`) |
| `UNC_AUTH_SERVER_HOST`             | No       | Defaults to `csxl.unc.edu`            |
| `LOG_LEVEL`            | No       | Defaults to `INFO`                     |

## Security Notes

- Secrets are stored in OKD `Secret` resources, never committed to the repository.
- The `secrets.yaml` manifest is a *template* — it contains placeholder values and comments explaining each field.
- The GitHub Actions workflow authenticates to OKD using a service account token stored as a GitHub Actions secret.
- The production image runs as a non-root user.
- TLS is terminated at the OKD Route level (edge termination).

## Rollback

Rolling back is a single command (replace `<your-namespace>`):

```bash
oc rollout undo deployment/learnwithai-app -n <your-namespace>
oc rollout undo deployment/learnwithai-worker -n <your-namespace>
```

OKD retains previous ReplicaSets by default, making rollback instant.
