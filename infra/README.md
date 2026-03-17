# Infra Workspace

This workspace holds everything needed to deploy LearnWithAI to an OKD cluster.

## Quick Start

See [DEPLOYMENT.md](DEPLOYMENT.md) for the full deployment plan and architecture.

### First-Time Deployment

```bash
# 1. Log into your OKD cluster
oc login https://your-cluster-api:6443

# 2. Edit secrets with real values (never commit real secrets)
cp infra/manifests/secrets.yaml infra/manifests/secrets.local.yaml
# ... edit secrets.local.yaml with real passwords ...

# 3. Run the deployment script
./infra/scripts/deploy.sh
```

### Updating After a Code Change

If CI/CD is configured (see below), pushing to `main` triggers automatic deployment. For manual rollouts:

```bash
./infra/scripts/rollout.sh
```

### Setting Up CI/CD

Add these GitHub Actions secrets to your repository:

| Secret       | Value                                      |
|--------------|--------------------------------------------|
| `OKD_SERVER` | OKD API server URL (e.g. `https://api.cloud.unc.edu:6443`) |
| `OKD_TOKEN`  | Service account token with deploy permissions |

To create a service account token:

```bash
oc create serviceaccount deployer -n learnwithai
oc policy add-role-to-user edit -z deployer -n learnwithai
oc create token deployer -n learnwithai --duration=8760h
```

## Directory Layout

```
infra/
├── DEPLOYMENT.md        # Full deployment plan and architecture diagram
├── Dockerfile           # Multi-stage production image (frontend + backend)
├── manifests/
│   ├── namespace.yaml   # OKD project/namespace
│   ├── secrets.yaml     # Template for production secrets
│   ├── postgres.yaml    # PostgreSQL Deployment + Service + PVC
│   ├── rabbitmq.yaml    # RabbitMQ Deployment + Service
│   ├── app.yaml         # BuildConfig + ImageStream + app Deployment + Service
│   ├── worker.yaml      # Dramatiq worker Deployment
│   └── route.yaml       # OKD Route (TLS edge termination)
└── scripts/
    ├── deploy.sh        # Guided first-time deployment
    └── rollout.sh       # Build + rolling update (used by CI)
```

## Other Infrastructure

Developer infrastructure still lives in repository-level files:

- `.devcontainer/` — local development container (Dockerfile, compose.yaml)
- `.github/workflows/quality-gates.yml` — CI quality gates
- `.github/workflows/deploy.yml` — CD deployment pipeline

## Useful OKD Commands

```bash
# View running pods
oc get pods -n learnwithai

# Tail application logs
oc logs -f deployment/learnwithai-app -n learnwithai

# Tail worker logs
oc logs -f deployment/learnwithai-worker -n learnwithai

# Check route URL
oc get route -n learnwithai

# Rollback to previous version
oc rollout undo deployment/learnwithai-app -n learnwithai
oc rollout undo deployment/learnwithai-worker -n learnwithai

# Open a shell in the app pod
oc rsh deployment/learnwithai-app -n learnwithai
```