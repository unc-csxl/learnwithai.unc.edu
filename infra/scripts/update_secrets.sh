#!/usr/bin/env bash
# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

# =============================================================================
# update_secrets.sh — Apply updated runtime secrets to an existing deployment
# =============================================================================
#
# Usage:
#   ./infra/scripts/update_secrets.sh <namespace>
#   ./infra/scripts/update_secrets.sh <namespace> --dry-run
#   ./infra/scripts/update_secrets.sh <namespace> --file infra/manifests/secrets.yaml
#
# This script reapplies the runtime Secret objects and restarts the dependent
# deployments so updated environment values take effect.
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFESTS_DIR="$SCRIPT_DIR/../manifests"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }
fail()  { error "$@"; exit 1; }

usage() {
    cat <<'EOF'
Usage:
  ./infra/scripts/update_secrets.sh <namespace> [options]

Options:
  --file <path>   Use a specific secrets manifest instead of the default lookup.
  --dry-run       Validate the manifest against the cluster without changing anything.
  --yes           Skip the confirmation prompt.
  -h, --help      Show this help text.
EOF
}

resolve_runtime_secrets_file() {
    if [ -f "$MANIFESTS_DIR/secrets.yaml" ]; then
        echo "$MANIFESTS_DIR/secrets.yaml"
        return
    fi

    if [ -f "$MANIFESTS_DIR/secrets.local.yaml" ]; then
        warn "Using legacy runtime secret file secrets.local.yaml. Rename it to secrets.yaml when convenient."
        echo "$MANIFESTS_DIR/secrets.local.yaml"
        return
    fi

    fail "Expected $MANIFESTS_DIR/secrets.yaml. Copy infra/manifests/secrets.example.yaml to secrets.yaml and fill in real values first."
}

restart_and_wait() {
    local deployment_name="$1"

    info "Restarting deployment/$deployment_name..."
    oc rollout restart "deployment/$deployment_name" -n "$NAMESPACE" >/dev/null
    oc rollout status "deployment/$deployment_name" -n "$NAMESPACE" --timeout=300s
}

confirm() {
    local response

    if [ "$ASSUME_YES" = true ]; then
        return
    fi

    read -r -p "Update secrets in namespace $NAMESPACE and restart the dependent deployments? [y/N] " response
    case "$response" in
        y|Y|yes|YES)
            ;;
        *)
            fail "Secret update cancelled."
            ;;
    esac
}

if [ $# -lt 1 ]; then
    usage
    exit 1
fi

NAMESPACE=""
SECRETS_FILE=""
DRY_RUN=false
ASSUME_YES=false

while [ $# -gt 0 ]; do
    case "$1" in
        --file)
            SECRETS_FILE="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --yes)
            ASSUME_YES=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        -*)
            fail "Unknown option: $1"
            ;;
        *)
            if [ -z "$NAMESPACE" ]; then
                NAMESPACE="$1"
                shift
            else
                fail "Unexpected argument: $1"
            fi
            ;;
    esac
done

[ -n "$NAMESPACE" ] || fail "Usage: $0 <namespace> [options]"

command -v oc >/dev/null 2>&1 || fail "oc CLI not found. Install it first."
command -v envsubst >/dev/null 2>&1 || fail "envsubst not found. Install gettext-base."
oc whoami >/dev/null 2>&1 || fail "Not logged into an OKD cluster. Run: oc login <cluster-url>"

if [ -z "$SECRETS_FILE" ]; then
    SECRETS_FILE="$(resolve_runtime_secrets_file)"
fi

[ -f "$SECRETS_FILE" ] || fail "Secrets file not found: $SECRETS_FILE"

if grep -q '<PLACEHOLDER>\|<DB_PASSWORD>\|<RABBITMQ_PASSWORD>\|<GENERATE_A_STRONG_SECRET>\|<PUBLIC_HOSTNAME>' "$SECRETS_FILE"; then
    fail "$(basename "$SECRETS_FILE") still contains placeholder values. Edit it before updating the deployment."
fi

export NAMESPACE

info "Target namespace: $NAMESPACE"
info "Using secrets manifest: $SECRETS_FILE"
info "Logged in as: $(oc whoami)"
info "Cluster: $(oc whoami --show-server)"

if [ "$DRY_RUN" = true ]; then
    info "Validating runtime secrets with server-side dry run..."
    envsubst '${NAMESPACE}' < "$SECRETS_FILE" | oc apply --dry-run=server -f -
    info "Dry run succeeded. No resources were changed."
    exit 0
fi

confirm

info "Applying runtime secrets..."
envsubst '${NAMESPACE}' < "$SECRETS_FILE" | oc apply -f -

info "Restarting workloads to load the updated secret values..."
restart_and_wait learnwithai-postgres
restart_and_wait learnwithai-rabbitmq
restart_and_wait learnwithai-app
restart_and_wait learnwithai-worker

echo
info "Secret update complete."