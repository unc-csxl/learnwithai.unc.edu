#!/usr/bin/env bash
# =============================================================================
# rollout.sh — Build and roll out a new version of LearnWithAI
# =============================================================================
#
# This script triggers an OKD build from the Git repository, waits for it to
# complete, then rolls out the new image to the app and worker deployments.
#
# Prerequisites:
#   1. `oc` CLI installed and on your PATH
#   2. You are logged into the OKD cluster
#   3. The initial deploy.sh has already been run
#
# Usage:
#   ./infra/scripts/rollout.sh          # build from latest main
#   ./infra/scripts/rollout.sh abc123   # build from a specific commit
#
# =============================================================================

set -euo pipefail

NAMESPACE="learnwithai"
BUILD_NAME="learnwithai-app"
COMMIT="${1:-}"

# -- Colors / helpers ---------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }
fail()  { error "$@"; exit 1; }

# -- Pre-flight ---------------------------------------------------------------

command -v oc >/dev/null 2>&1 || fail "oc CLI not found."
oc whoami >/dev/null 2>&1 || fail "Not logged into OKD. Run: oc login <cluster-url>"

# -- Start build --------------------------------------------------------------

BUILD_ARGS=()
if [ -n "$COMMIT" ]; then
    BUILD_ARGS+=(--commit="$COMMIT")
    info "Building from commit: $COMMIT"
else
    info "Building from latest main branch"
fi

info "Starting build..."
oc start-build "$BUILD_NAME" -n "$NAMESPACE" --follow "${BUILD_ARGS[@]}"
echo

# -- Roll out -----------------------------------------------------------------

info "Rolling out app deployment..."
oc rollout restart deployment/learnwithai-app -n "$NAMESPACE"
oc rollout status deployment/learnwithai-app -n "$NAMESPACE" --timeout=300s

info "Rolling out worker deployment..."
oc rollout restart deployment/learnwithai-worker -n "$NAMESPACE"
oc rollout status deployment/learnwithai-worker -n "$NAMESPACE" --timeout=300s
echo

info "Rollout complete!"
