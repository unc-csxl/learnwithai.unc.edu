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

The first deploy now creates three OKD-side pieces for private-repository builds:

- a source clone secret that contains an SSH deploy key for GitHub
- webhook secrets for OKD build triggers
- a namespace-local role binding that allows webhook callers to trigger builds

The deploy script generates the SSH keypair for you, prints the public key, and pauses so you can add it to GitHub as a read-only deploy key before the first build runs.

### Updating After a Code Change

If CI/CD is configured (see below), pushing to `main` triggers automatic deployment. For manual rollouts:

```bash
./infra/scripts/rollout.sh <your-namespace>
```

The rollout script streams the local repository into the existing OKD BuildConfig. When the build finishes, OKD image stream triggers update the app and worker Deployments automatically.

### Resetting The Deployed Database

For developer resets in a deployment namespace, use:

```bash
./infra/scripts/reset_db.sh <your-namespace>
```

The reset workflow scales the app and worker down, drops and recreates the PostgreSQL database using the local `postgres` superuser inside the PostgreSQL container, creates a short-lived ConfigMap from the checked-out bootstrap script, runs a one-off bootstrap job from the app image with that script mounted in, and then restores the app and worker replicas. If any reset step fails, the script restores the previous replica counts before exiting.

The bootstrap logic lives in [packages/learnwithai-core/scripts/bootstrap_deployment_db.py](/workspaces/learnwithai/packages/learnwithai-core/scripts/bootstrap_deployment_db.py) so the seeded behavior is easy to audit and review, and the reset flow does not depend on the currently deployed image already containing the latest bootstrap file.

The dummy seeded user is:

- Name: `Demo User`
- Onyen: `demo`
- PID: `999999999`
- Email: `demo@example.com`

### Tearing Down A Deployment

To delete the LearnWithAI resources from a namespace with a confirmation prompt:

```bash
./infra/scripts/destroy.sh <your-namespace>
```

To skip prompts, pass `--yes`. To also remove the namespace itself, add `--delete-namespace`.

### Setting Up CI/CD

After the first successful `deploy.sh` run, save this GitHub Actions secret in the repository:

| Secret                    | Value |
|---------------------------|-------|
| `OKD_GENERIC_WEBHOOK_URL` | The full generic webhook URL printed by `deploy.sh` |

That webhook path is the only cluster credential GitHub Actions needs. The OKD cluster handles the Git clone itself by using the SSH deploy key stored in the namespace secret.

Optional: if you want GitHub to trigger OKD builds directly on repository push events outside the QA-gated workflow, `deploy.sh` also prints a GitHub-specific webhook URL that you can paste into GitHub Settings -> Webhooks. The default repository workflow in `.github/workflows/deploy.yml` uses the generic webhook instead so deployment still happens only after QA passes.

If the cluster requires the namespace-local webhook RBAC to be added manually, this is the resource `deploy.sh` applies:

```bash
NAMESPACE=<your-namespace> envsubst '${NAMESPACE}' < infra/manifests/webhook-rbac.yaml | oc apply -f -
```

## Directory Layout

```
infra/
├── DEPLOYMENT.md        # Full deployment plan and architecture diagram
├── Dockerfile           # Multi-stage production image (frontend + backend)
├── helm/                # Helm chart alternative and wrapper scripts
├── manifests/
│   ├── namespace.yaml   # OKD project/namespace
│   ├── secrets.yaml     # Template for production secrets
│   ├── postgres.yaml    # PostgreSQL Deployment + Service + PVC
│   ├── rabbitmq.yaml    # RabbitMQ Deployment + Service
│   ├── app.yaml         # BuildConfig + ImageStream + app Deployment + Service
│   ├── worker.yaml      # Dramatiq worker Deployment
│   ├── webhook-rbac.yaml # Namespace-local webhook access RoleBinding
│   └── route.yaml       # OKD Route (TLS edge termination)
└── scripts/
    ├── deploy.sh        # Guided first-time deployment + initial binary build
    ├── destroy.sh       # Tear down manifest-managed resources
    ├── reset_db.sh      # Reset deployed DB and seed demo data
    └── rollout.sh       # Binary build + rolling update (used by CI)
```

## Other Infrastructure

Developer infrastructure still lives in repository-level files:

- `.devcontainer/` — local development container (Dockerfile, compose.yaml)
- `.github/workflows/quality-gates.yml` — CI quality gates
- `.github/workflows/deploy.yml` — CD workflow that POSTs to the OKD generic webhook

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