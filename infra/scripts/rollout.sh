#!/usr/bin/env bash
# Copyright (c) 2026 Kris Jordan
# SPDX-License-Identifier: MIT

# =============================================================================
# rollout.sh — Build and roll out a new version of LearnWithAI
# =============================================================================
#
# This script streams the local repository to the OKD BuildConfig, waits for the
# build to complete, and then waits for the image stream triggers to update the
# app and worker Deployments.
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
    info "Building from the local repository at commit: $COMMIT"
else
    info "Building from the current local repository checkout"
fi

info "Starting build..."
oc start-build "$BUILD_NAME" -n "$NAMESPACE" --from-repo="$REPO_ROOT" --follow "${BUILD_ARGS[@]}"
echo

# -- Wait for image-triggered rollouts ----------------------------------------

info "Waiting for app deployment to pick up the new image..."
oc rollout status deployment/learnwithai-app -n "$NAMESPACE" --timeout=300s

info "Waiting for worker deployment to pick up the new image..."
oc rollout status deployment/learnwithai-worker -n "$NAMESPACE" --timeout=300s
echo

info "Rollout complete!"
