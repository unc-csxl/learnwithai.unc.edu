# Infra Workspace

This workspace contains the files used to deploy LearnWithAI to an OKD cluster.

If you are new to deployment work, start with the scripts in `infra/scripts/`. They encode the expected workflow and are safer than assembling long `oc` commands by hand.

For the deeper architecture explanation, read `DEPLOYMENT.md` after this file.

## What Lives Here

```text
infra/
|- DEPLOYMENT.md              Deployment architecture and workflow notes
|- Dockerfile                 Production image build
|- manifests/
|  |- namespace.yaml          Namespace template
|  |- secrets.yaml            Checked-in secrets template
|  |- secrets.local.yaml      Local-only secrets file for real values
|  |- postgres.yaml           PostgreSQL resources
|  |- rabbitmq.yaml           RabbitMQ resources
|  |- app.yaml                App build and deployment resources
|  |- worker.yaml             Worker deployment resources
|  |- webhook-rbac.yaml       Webhook access binding
|  `- route.yaml              Public route
`- scripts/
   |- deploy.sh               First-time deploy helper
   |- rollout.sh              Rebuild and roll forward
   |- reset_db.sh             Reset deployed database and seed demo data
   `- destroy.sh              Tear down deployment resources
```

## First-Time Deployment

Replace `<your-namespace>` with your team's OKD namespace.

```bash
oc login https://your-cluster-api:6443
cp infra/manifests/secrets.yaml infra/manifests/secrets.local.yaml
# edit infra/manifests/secrets.local.yaml with real values
./infra/scripts/deploy.sh <your-namespace>
```

What `deploy.sh` does for you:

- creates or reuses the namespace
- creates OKD secrets for private-repository builds
- generates an SSH deploy key if needed
- prints the public key so you can add it to GitHub
- applies the manifests
- starts the first build
- prints the webhook URL used by GitHub Actions

## Common Operations

### Roll out a new version

```bash
./infra/scripts/rollout.sh <your-namespace>
```

### Reset deployed data

```bash
./infra/scripts/reset_db.sh <your-namespace>
```

This resets the deployed PostgreSQL database and reseeds demo data.

### Tear everything down

```bash
./infra/scripts/destroy.sh <your-namespace>
```

Add `--yes` to skip prompts and `--delete-namespace` if you also want to remove the namespace.

## CI And Webhooks

After the first successful deploy, store the webhook URL printed by `deploy.sh` in the GitHub Actions secret `OKD_GENERIC_WEBHOOK_URL`.

That webhook is enough for the repository deployment workflow. GitHub does not need direct cluster login credentials.

## Useful OKD Commands

Replace `<your-namespace>` with your namespace:

```bash
oc get pods -n <your-namespace>
oc logs -f deployment/learnwithai-app -n <your-namespace>
oc logs -f deployment/learnwithai-worker -n <your-namespace>
oc get route -n <your-namespace>
oc rollout undo deployment/learnwithai-app -n <your-namespace>
oc rollout undo deployment/learnwithai-worker -n <your-namespace>
```