# Infra Workspace

This workspace is reserved for infrastructure-related assets.

Right now, most active infrastructure configuration lives outside this folder in repository-level files such as:

- `.devcontainer/devcontainer.json`
- `.devcontainer/compose.yaml`
- `.devcontainer/Dockerfile`
- `.github/workflows/quality-gates.yml`

That means `infra/` is currently lightweight, but it still matters as the natural home for future infrastructure code such as deployment manifests, local environment helpers, or cloud-specific configuration.

## How To Think About Infrastructure In This Repository

There are two main categories today:

- Developer infrastructure: the dev container, local Docker Compose services, forwarded ports, and editor setup
- CI infrastructure: GitHub Actions workflows that install dependencies and run QA

## Current Local Services

The recommended dev container stack provides:

- PostgreSQL on port `5432`
- RabbitMQ on port `5672`
- RabbitMQ management UI on port `15672`
- The app container where you run `uv`, `pnpm`, and editor tasks

## When To Put Something Here

Add files to `infra/` when they primarily exist to provision, configure, or operate environments rather than implement application features.

Examples:

- Deployment manifests
- Environment bootstrap helpers
- Infrastructure module documentation
- Service topology notes that do not belong in the root README