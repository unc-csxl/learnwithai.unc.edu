# Infra Workspace

This workspace holds everything needed to deploy LearnWithAI to an OKD cluster.

## Quick Start

See [DEPLOYMENT.md](DEPLOYMENT.md) for the full deployment plan and architecture.

### First-Time Deployment

Replace `<your-namespace>` below with the OKD project name your sysadmin assigned to your team (e.g. `comp423-25s-ta-krissemern`).

```bash
# 1. Log into your OKD cluster
oc login https://your-cluster-api:6443

# 2. Edit secrets with real values (never commit real secrets)
cp infra/manifests/secrets.yaml infra/manifests/secrets.local.yaml
# ... edit secrets.local.yaml with real passwords ...

# 3. Run the deployment script with your namespace
./infra/scripts/deploy.sh <your-namespace>
```

If the namespace already exists and your account only has project-level permissions, the deploy script reuses that namespace instead of trying to modify cluster-scoped namespace metadata.

The OKD image build uses the checked-out repository as a binary source archive, so the cluster does not need direct clone access to a private GitHub repository.

### Updating After a Code Change

If CI/CD is configured (see below), pushing to `main` triggers automatic deployment. For manual rollouts:

```bash
./infra/scripts/rollout.sh <your-namespace>
```

### Tearing Down A Deployment

To delete the LearnWithAI resources from a namespace with a confirmation prompt:

```bash
./infra/scripts/destroy.sh <your-namespace>
```

To skip prompts, pass `--yes`. To also remove the namespace itself, add `--delete-namespace`.

### Setting Up CI/CD

Add these GitHub Actions secrets to your repository:

| Secret          | Value                                      |
|-----------------|--------------------------------------------|
| `OKD_SERVER`    | OKD API server URL (e.g. `https://api.cloud.unc.edu:6443`) |
| `OKD_TOKEN`     | Service account token with deploy permissions |
| `OKD_NAMESPACE` | OKD project/namespace to deploy into       |

To create a service account token (replace `<your-namespace>`):

```bash
oc create serviceaccount deployer -n <your-namespace>
oc policy add-role-to-user edit -z deployer -n <your-namespace>
oc create token deployer -n <your-namespace> --duration=8760h
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
    ├── deploy.sh        # Guided first-time deployment + initial binary build
    ├── destroy.sh       # Tear down manifest-managed resources
    └── rollout.sh       # Binary build + rolling update (used by CI)
```

## Other Infrastructure

Developer infrastructure still lives in repository-level files:

- `.devcontainer/` — local development container (Dockerfile, compose.yaml)
- `.github/workflows/quality-gates.yml` — CI quality gates
- `.github/workflows/deploy.yml` — CD deployment pipeline

## Useful OKD Commands

Replace `<your-namespace>` with your team's OKD project name.

```bash
# View running pods
oc get pods -n <your-namespace>

# Tail application logs
oc logs -f deployment/learnwithai-app -n <your-namespace>

# Tail worker logs
oc logs -f deployment/learnwithai-worker -n <your-namespace>

# Check route URL
oc get route -n <your-namespace>

# Rollback to previous version
oc rollout undo deployment/learnwithai-app -n <your-namespace>
oc rollout undo deployment/learnwithai-worker -n <your-namespace>

# Open a shell in the app pod
oc rsh deployment/learnwithai-app -n <your-namespace>
```