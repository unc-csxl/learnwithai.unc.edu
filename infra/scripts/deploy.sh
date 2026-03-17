#!/usr/bin/env bash
# =============================================================================
# deploy.sh — First-time deployment of LearnWithAI to an OKD cluster
# =============================================================================
#
# Prerequisites:
#   1. `oc` CLI installed and on your PATH
#   2. You are logged into the OKD cluster: oc login <cluster-url>
#   3. You have edited infra/manifests/secrets.yaml with real values
#
# Usage:
#   ./infra/scripts/deploy.sh <namespace>
#
# Example:
#   ./infra/scripts/deploy.sh comp423-25s-ta-krissemern
#
# The namespace is the OKD project your sysadmin gave you. Every manifest
# uses the placeholder ${NAMESPACE} which this script substitutes at apply
# time. Nothing is written to disk — the checked-in YAML stays generic.
#
# This script is idempotent — you can safely re-run it.
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFESTS_DIR="$SCRIPT_DIR/../manifests"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# -- Colors / helpers ---------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }
fail()  { error "$@"; exit 1; }

# -- Namespace argument -------------------------------------------------------

if [ $# -lt 1 ]; then
    fail "Usage: $0 <namespace>\n       Example: $0 comp423-25s-ta-krissemern"
fi

export NAMESPACE="$1"
info "Target namespace: $NAMESPACE"

# Helper: substitute ${NAMESPACE} in a manifest and pipe to oc apply
apply_manifest() {
    envsubst '${NAMESPACE}' < "$1" | oc apply -f -
}

ensure_namespace() {
    if oc get namespace "$NAMESPACE" >/dev/null 2>&1; then
        warn "Namespace $NAMESPACE already exists. Reusing it without modifying cluster-scoped metadata."
        return
    fi

    envsubst '${NAMESPACE}' < "$MANIFESTS_DIR/namespace.yaml" | oc create -f -
}

# -- Pre-flight checks -------------------------------------------------------

command -v oc >/dev/null 2>&1 || fail "oc CLI not found. Install it first: https://docs.okd.io/latest/cli_reference/openshift_cli/getting-started-cli.html"
command -v envsubst >/dev/null 2>&1 || fail "envsubst not found. Install gettext: apt-get install gettext-base"

oc whoami >/dev/null 2>&1 || fail "Not logged into an OKD cluster. Run: oc login <cluster-url>"

info "Logged in as: $(oc whoami)"
info "Cluster: $(oc whoami --show-server)"
echo

# -- Check that secrets template has been filled in ---------------------------

if grep -q '<PLACEHOLDER>\|<DB_PASSWORD>\|<RABBITMQ_PASSWORD>\|<GENERATE_A_STRONG_SECRET>\|<PUBLIC_HOSTNAME>' "$MANIFESTS_DIR/secrets.local.yaml"; then
    fail "secrets.local.yaml still contains placeholder values. Edit it before deploying."
fi

# -- Apply manifests in order -------------------------------------------------

info "Step 1/6: Creating namespace..."
ensure_namespace
echo

info "Step 2/6: Applying secrets..."
apply_manifest "$MANIFESTS_DIR/secrets.local.yaml"
echo

info "Step 3/6: Deploying PostgreSQL..."
apply_manifest "$MANIFESTS_DIR/postgres.yaml"
echo

info "Step 4/6: Deploying RabbitMQ..."
apply_manifest "$MANIFESTS_DIR/rabbitmq.yaml"
echo

info "Waiting for PostgreSQL to be ready..."
oc rollout status deployment/learnwithai-postgres -n "$NAMESPACE" --timeout=120s

info "Waiting for RabbitMQ to be ready..."
oc rollout status deployment/learnwithai-rabbitmq -n "$NAMESPACE" --timeout=120s
echo

info "Step 5/6: Deploying application..."
apply_manifest "$MANIFESTS_DIR/app.yaml"
apply_manifest "$MANIFESTS_DIR/worker.yaml"
echo

info "Step 6/6: Creating route..."
apply_manifest "$MANIFESTS_DIR/route.yaml"
echo

# -- Trigger initial build (if needed) ----------------------------------------

info "Starting initial image build from the local working tree..."
oc start-build learnwithai-app -n "$NAMESPACE" --from-dir="$REPO_ROOT" --follow || warn "Build may already be running."
echo

# -- Wait for rollouts --------------------------------------------------------

info "Waiting for app deployment..."
oc rollout status deployment/learnwithai-app -n "$NAMESPACE" --timeout=300s

info "Waiting for worker deployment..."
oc rollout status deployment/learnwithai-worker -n "$NAMESPACE" --timeout=300s
echo

# -- Health check --------------------------------------------------------------

ROUTE_HOST=$(oc get route learnwithai -n "$NAMESPACE" -o jsonpath='{.spec.host}' 2>/dev/null || echo "")
if [ -n "$ROUTE_HOST" ]; then
    info "Route: https://$ROUTE_HOST"
    info "Running health check..."
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "https://$ROUTE_HOST/api/health" --max-time 10 || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
        info "Health check passed! (HTTP $HTTP_CODE)"
    else
        warn "Health check returned HTTP $HTTP_CODE — the app may still be starting."
    fi
else
    warn "Could not determine route hostname."
fi

echo
info "Deployment complete!"
info ""
info "Useful commands:"
info "  oc get pods -n learnwithai              # List running pods"
info "  oc logs -f deployment/learnwithai-app    # Tail app logs"
info "  oc logs -f deployment/learnwithai-worker # Tail worker logs"
info "  oc get route -n learnwithai              # Show route URL"
