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
#   ./infra/scripts/deploy.sh
#
# This script is idempotent — you can safely re-run it.
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFESTS_DIR="$SCRIPT_DIR/../manifests"

# -- Colors / helpers ---------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }
fail()  { error "$@"; exit 1; }

# -- Pre-flight checks -------------------------------------------------------

command -v oc >/dev/null 2>&1 || fail "oc CLI not found. Install it first: https://docs.okd.io/latest/cli_reference/openshift_cli/getting-started-cli.html"

oc whoami >/dev/null 2>&1 || fail "Not logged into an OKD cluster. Run: oc login <cluster-url>"

info "Logged in as: $(oc whoami)"
info "Cluster: $(oc whoami --show-server)"
echo

# -- Check that secrets template has been filled in ---------------------------

if grep -q '<PLACEHOLDER>\|<DB_PASSWORD>\|<RABBITMQ_PASSWORD>\|<GENERATE_A_STRONG_SECRET>\|<PUBLIC_HOSTNAME>' "$MANIFESTS_DIR/secrets.yaml"; then
    fail "secrets.yaml still contains placeholder values. Edit it before deploying."
fi

# -- Apply manifests in order -------------------------------------------------

info "Step 1/6: Creating namespace..."
oc apply -f "$MANIFESTS_DIR/namespace.yaml"
echo

info "Step 2/6: Applying secrets..."
oc apply -f "$MANIFESTS_DIR/secrets.yaml"
echo

info "Step 3/6: Deploying PostgreSQL..."
oc apply -f "$MANIFESTS_DIR/postgres.yaml"
echo

info "Step 4/6: Deploying RabbitMQ..."
oc apply -f "$MANIFESTS_DIR/rabbitmq.yaml"
echo

info "Waiting for PostgreSQL to be ready..."
oc rollout status deployment/learnwithai-postgres -n learnwithai --timeout=120s

info "Waiting for RabbitMQ to be ready..."
oc rollout status deployment/learnwithai-rabbitmq -n learnwithai --timeout=120s
echo

info "Step 5/6: Deploying application..."
oc apply -f "$MANIFESTS_DIR/app.yaml"
oc apply -f "$MANIFESTS_DIR/worker.yaml"
echo

info "Step 6/6: Creating route..."
oc apply -f "$MANIFESTS_DIR/route.yaml"
echo

# -- Trigger initial build (if needed) ----------------------------------------

info "Starting initial image build..."
oc start-build learnwithai-app -n learnwithai --follow || warn "Build may already be running."
echo

# -- Wait for rollouts --------------------------------------------------------

info "Waiting for app deployment..."
oc rollout status deployment/learnwithai-app -n learnwithai --timeout=300s

info "Waiting for worker deployment..."
oc rollout status deployment/learnwithai-worker -n learnwithai --timeout=300s
echo

# -- Health check --------------------------------------------------------------

ROUTE_HOST=$(oc get route learnwithai -n learnwithai -o jsonpath='{.spec.host}' 2>/dev/null || echo "")
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
