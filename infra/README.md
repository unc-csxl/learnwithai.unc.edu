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
|  |- secrets.example.yaml    Checked-in secrets template
|  `- secrets.yaml            Local-only secrets file with real values
|  |- postgres.yaml           PostgreSQL resources
|  |- rabbitmq.yaml           RabbitMQ resources
|  |- app.yaml                App build and deployment resources
|  |- worker.yaml             Worker deployment resources
|  |- webhook-rbac.yaml       Webhook access binding
|  `- route.yaml              Public route
`- scripts/
   |- deploy.sh               First-time deploy helper
   |- update_secrets.sh       Apply updated runtime secrets and restart workloads
   |- rollout.sh              Rebuild and roll forward
   |- reset_db.sh             Reset deployed database and seed demo data
   `- destroy.sh              Tear down deployment resources
```

## First-Time Deployment

Replace `<your-namespace>` with your team's OKD namespace.

```bash
oc login https://your-cluster-api:6443
cp infra/manifests/secrets.example.yaml infra/manifests/secrets.yaml
# edit infra/manifests/secrets.yaml with real values
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

## Azure OpenAI Secrets

The deployed app and worker both read AI configuration from the `learnwithai-secrets` secret.

Provide these values in `infra/manifests/secrets.yaml` before running `deploy.sh`:

- `OPENAI_API_KEY`: Azure subscription key for the configured endpoint
- `OPENAI_MODEL`: Azure deployment name used by AI-backed jobs
- `OPENAI_ENDPOINT`: Azure endpoint host, for example `https://azureaiapi.cloud.unc.edu`
- `OPENAI_API_VERSION`: Azure API version, for example `2025-04-01-preview`

The backend also accepts `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_DEPLOYMENT`, `AZURE_OPENAI_ENDPOINT`, and `AZURE_OPENAI_API_VERSION`, but the checked-in manifest templates use the `OPENAI_*` names for consistency with the rest of the repository.

If the worker logs `401 Access denied due to invalid subscription key`, the app is reaching Azure correctly and the secret value itself is wrong for that endpoint or subscription.

## Common Operations

### Roll out a new version

```bash
./infra/scripts/rollout.sh <your-namespace>
```

### Update deployed secrets

```bash
./infra/scripts/update_secrets.sh <your-namespace>
```

This reapplies `infra/manifests/secrets.yaml` and restarts PostgreSQL, RabbitMQ, the app, and the worker so the new values take effect.

Use `--dry-run` to validate the manifest against the cluster without changing anything.

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