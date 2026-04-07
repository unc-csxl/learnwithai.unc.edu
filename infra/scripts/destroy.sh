#!/usr/bin/env bash
# =============================================================================
# destroy.sh — Tear down a LearnWithAI deployment from an OKD cluster
# =============================================================================
#
# Usage:
#   ./infra/scripts/destroy.sh <namespace>
#   ./infra/scripts/destroy.sh <namespace> --yes
#   ./infra/scripts/destroy.sh <namespace> --delete-namespace
#   ./infra/scripts/destroy.sh <namespace> --yes --delete-namespace
#
# By default, this deletes the resources managed by the infra manifests while
# leaving the namespace in place. Pass --delete-namespace to also remove the
# namespace itself after the managed resources are deleted.
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

if [ $# -lt 1 ]; then
    fail "Usage: $0 <namespace> [--yes] [--delete-namespace]"
fi

export NAMESPACE="$1"
shift

ASSUME_YES=false
DELETE_NAMESPACE=false

while [ $# -gt 0 ]; do
    case "$1" in
        --yes)
            ASSUME_YES=true
            ;;
        --delete-namespace)
            DELETE_NAMESPACE=true
            ;;
        *)
            fail "Unknown option: $1"
            ;;
    esac
    shift
done

command -v oc >/dev/null 2>&1 || fail "oc CLI not found. Install it first."
command -v envsubst >/dev/null 2>&1 || fail "envsubst not found. Install gettext-base."
oc whoami >/dev/null 2>&1 || fail "Not logged into an OKD cluster. Run: oc login <cluster-url>"

delete_manifest() {
    envsubst '${NAMESPACE}' < "$1" | oc delete --ignore-not-found=true -f -
}

delete_secret() {
    oc delete secret "$@" -n "$NAMESPACE" --ignore-not-found=true >/dev/null
}

confirm() {
    local prompt="$1"
    local response

    if [ "$ASSUME_YES" = true ]; then
        return
    fi

    read -r -p "$prompt [y/N] " response
    case "$response" in
        y|Y|yes|YES)
            ;;
        *)
            fail "Teardown cancelled."
            ;;
    esac
}

info "Target namespace: $NAMESPACE"
info "Logged in as: $(oc whoami)"
info "Cluster: $(oc whoami --show-server)"

if ! oc get namespace "$NAMESPACE" >/dev/null 2>&1; then
    warn "Namespace $NAMESPACE does not exist. Nothing to tear down."
    exit 0
fi

confirm "Delete LearnWithAI resources from namespace $NAMESPACE?"

if [ "$DELETE_NAMESPACE" = true ]; then
    confirm "Also delete namespace $NAMESPACE?"
fi

echo
info "Deleting route..."
delete_manifest "$MANIFESTS_DIR/route.yaml"

info "Deleting worker..."
delete_manifest "$MANIFESTS_DIR/worker.yaml"

info "Deleting app resources..."
delete_manifest "$MANIFESTS_DIR/app.yaml"

info "Deleting RabbitMQ..."
delete_manifest "$MANIFESTS_DIR/rabbitmq.yaml"

info "Deleting PostgreSQL..."
delete_manifest "$MANIFESTS_DIR/postgres.yaml"

info "Deleting runtime secrets..."
delete_secret learnwithai-secrets learnwithai-postgres-credentials learnwithai-rabbitmq-credentials

if [ "$DELETE_NAMESPACE" = true ]; then
    info "Deleting namespace $NAMESPACE..."
    oc delete namespace "$NAMESPACE" --ignore-not-found=true
else
    info "Leaving namespace $NAMESPACE in place."
fi

echo
info "Teardown complete!"