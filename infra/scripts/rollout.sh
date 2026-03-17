#!/usr/bin/env bash
# =============================================================================
# rollout.sh — Build and roll out a new version of LearnWithAI
# =============================================================================
#
# This script uploads the checked-out working tree to an OKD binary build, waits
# for it to complete, then rolls out the new image to the app and worker
# deployments.
#
# Prerequisites:
#   1. `oc` CLI installed and on your PATH
#   2. You are logged into the OKD cluster
#   3. The initial deploy.sh has already been run
#
# Usage:
#   ./infra/scripts/rollout.sh <namespace>          # build from latest main
#   ./infra/scripts/rollout.sh <namespace> abc123   # build from a specific commit
#
# Example:
#   ./infra/scripts/rollout.sh comp423-25s-ta-krissemern
#   ./infra/scripts/rollout.sh comp423-25s-ta-krissemern abc123
#
# =============================================================================

set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Usage: $0 <namespace> [commit]" >&2
    echo "Example: $0 comp423-25s-ta-krissemern" >&2
    exit 1
fi

NAMESPACE="$1"
BUILD_NAME="learnwithai-app"
COMMIT="${2:-}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

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
    info "Building from local working tree at commit: $COMMIT"
else
    info "Building from the current local working tree"
fi

info "Starting build..."
oc start-build "$BUILD_NAME" -n "$NAMESPACE" --from-dir="$REPO_ROOT" --follow "${BUILD_ARGS[@]}"
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
