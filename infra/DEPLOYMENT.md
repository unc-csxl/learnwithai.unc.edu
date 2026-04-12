# LearnWithAI Deployment On OKD

This document explains how deployment works today. It is meant to help a new engineer answer three questions quickly:

1. What gets deployed?
2. Which files control that deployment?
3. Which script should I run for the job in front of me?

## High-Level Architecture

LearnWithAI is deployed as four main runtime pieces behind a single OKD route:

- `learnwithai-app` — serves the FastAPI API and the built Angular app
- `learnwithai-worker` — runs Dramatiq background jobs
- PostgreSQL — stores application data
- RabbitMQ — carries queued jobs and realtime job-update messages

The app and worker use the same container image. They differ only in how OKD starts them.

## Request Flow

In production, FastAPI serves both the API and the built frontend:

- API routes live under `/api`
- the Angular build is served for non-API routes
- the OKD Route exposes the app publicly over TLS

This keeps deployment simple: one public route, one app image, one worker image stream consumer.

## Files That Matter Most

```text
infra/
|- Dockerfile                 Production image build
|- manifests/
|  |- app.yaml                App build and deployment resources
|  |- worker.yaml             Worker deployment resources
|  |- postgres.yaml           PostgreSQL resources
|  |- rabbitmq.yaml           RabbitMQ resources
|  |- route.yaml              Public route
|  |- secrets.example.yaml    Template secrets file
|  `- secrets.yaml            Local-only secrets file with real values
|  `- webhook-rbac.yaml       Webhook access binding
`- scripts/
    |- deploy.sh               First-time deployment
    |- update_secrets.sh       Apply updated runtime secrets
    |- rollout.sh              Rebuild and roll forward
    |- reset_db.sh             Reset deployed data
    `- destroy.sh              Tear down deployment resources
```

## Normal Operator Workflows

### First deployment

Use this when the namespace is not set up yet:

```bash
./infra/scripts/deploy.sh <your-namespace>
```

`deploy.sh` handles the full first-time setup:

- creates or reuses the namespace
- prepares source-clone and webhook secrets
- generates an SSH deploy key if needed
- pauses so you can add the public key to GitHub
- applies manifests
- starts the first build
- prints the OKD webhook URL used by GitHub Actions

Before the first deploy, create the local runtime secret manifest:

```bash
cp infra/manifests/secrets.example.yaml infra/manifests/secrets.yaml
```

### Deploy a new revision

Use this after the initial deployment exists:

```bash
./infra/scripts/rollout.sh <your-namespace>
```

This streams the current repository checkout to the existing OKD BuildConfig, waits for the build, and then waits for the app and worker rollouts.

### Update deployed secrets

Use this after editing `infra/manifests/secrets.yaml`:

```bash
./infra/scripts/update_secrets.sh <your-namespace>
```

This reapplies the three OKD Secret objects defined in the manifest and restarts the dependent deployments so the new environment values are loaded.

### Reset deployed data

Use this when you need a clean deployment database for testing:

```bash
./infra/scripts/reset_db.sh <your-namespace>
```

This script:

- scales the app and worker down
- drops and recreates the deployed database
- runs an inline bootstrap command to create SQLModel tables
- restores the previous replica counts

Demo user seeded by the bootstrap flow:

- name: `Demo User`
- onyen: `demo`
- pid: `999999999`
- email: `demo@example.com`

### Tear down deployment resources

```bash
./infra/scripts/destroy.sh <your-namespace>
```

Useful flags:

- `--yes` to skip prompts
- `--delete-namespace` to remove the namespace too

## CI And Webhooks

The repository deployment workflow does not log into OKD directly. Instead, GitHub Actions calls the generic webhook URL printed by `deploy.sh`.

Store that value in the repository secret:

- `OKD_GENERIC_WEBHOOK_URL`

The OKD cluster handles the build by cloning the repository with the deploy key stored in the namespace.

## Production Notes

- The production image is built from `infra/Dockerfile`.
- PostgreSQL uses persistent storage.
- RabbitMQ does not use persistent storage in this setup.
- TLS terminates at the OKD Route.
- The production image runs as a non-root user.

## Azure OpenAI In Deployment

AI-backed jobs run in the worker and use the same secret-backed configuration as the API process.

Set these keys in `learnwithai-secrets`:

- `OPENAI_API_KEY`: Azure subscription key for the endpoint
- `OPENAI_MODEL`: Azure deployment name
- `OPENAI_ENDPOINT`: Azure endpoint host
- `OPENAI_API_VERSION`: Azure API version

Operational guidance:

- A `404 Resource not found` error usually means the endpoint or deployment path is wrong.
- A `401 invalid subscription key` error means the endpoint was reached but the credential was rejected.
- The deployment name must match the Azure deployment configured on the target service. A model family name is not enough unless the deployment was created with the same name.

## Useful OKD Commands

```bash
oc get pods -n <your-namespace>
oc logs -f deployment/learnwithai-app -n <your-namespace>
oc logs -f deployment/learnwithai-worker -n <your-namespace>
oc get route -n <your-namespace>
oc rollout undo deployment/learnwithai-app -n <your-namespace>
oc rollout undo deployment/learnwithai-worker -n <your-namespace>
```
