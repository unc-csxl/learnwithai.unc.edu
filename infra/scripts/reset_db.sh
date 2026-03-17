#!/usr/bin/env bash
# =============================================================================
# reset_db.sh — Reset the deployed LearnWithAI database in an OKD namespace
# =============================================================================
#
# This workflow is intentionally developer-focused. It:
#   1. scales the app and worker deployments down to 0
#   2. drops and recreates the application database in PostgreSQL
#   3. runs a one-off bootstrap Job from the app image with a mounted bootstrap
#      script from the local checkout that creates SQLModel tables and inserts
#      a dummy user
#   4. restores the app and worker replica counts
#
# Usage:
#   ./infra/scripts/reset_db.sh <namespace>
#   ./infra/scripts/reset_db.sh <namespace> --yes
#
# Prerequisites:
#   1. `oc` CLI installed and logged into the target cluster
#   2. A successful deployment already exists in the namespace
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }
fail()  { error "$@"; exit 1; }

if [ $# -lt 1 ]; then
    fail "Usage: $0 <namespace> [--yes]"
fi

NAMESPACE="$1"
shift

ASSUME_YES=false
while [ $# -gt 0 ]; do
    case "$1" in
        --yes)
            ASSUME_YES=true
            ;;
        *)
            fail "Unknown option: $1"
            ;;
    esac
    shift
done

command -v oc >/dev/null 2>&1 || fail "oc CLI not found. Install it first."
oc whoami >/dev/null 2>&1 || fail "Not logged into OKD. Run: oc login <cluster-url>"

APP_REPLICAS="0"
WORKER_REPLICAS="0"
RESTORE_REPLICAS=false
BOOTSTRAP_CONFIGMAP=""
JOB_MANIFEST=""

restore_replicas() {
    if [ "$RESTORE_REPLICAS" != true ]; then
        return
    fi

    info "Restoring app and worker replica counts..."
    oc scale deployment/learnwithai-app -n "$NAMESPACE" --replicas="$APP_REPLICAS" >/dev/null 2>&1 || true
    oc scale deployment/learnwithai-worker -n "$NAMESPACE" --replicas="$WORKER_REPLICAS" >/dev/null 2>&1 || true
}

cleanup() {
    local exit_code=$?

    if [ $exit_code -ne 0 ]; then
        warn "Database reset failed. Restoring app and worker replica counts."
    fi

    if [ -n "$BOOTSTRAP_CONFIGMAP" ]; then
        oc delete configmap "$BOOTSTRAP_CONFIGMAP" -n "$NAMESPACE" --ignore-not-found=true >/dev/null 2>&1 || true
    fi

    if [ -n "$JOB_MANIFEST" ]; then
        rm -f "$JOB_MANIFEST" >/dev/null 2>&1 || true
    fi

    restore_replicas
    exit $exit_code
}

trap cleanup EXIT

confirm() {
    local response

    if [ "$ASSUME_YES" = true ]; then
        return
    fi

    read -r -p "Reset database in namespace $NAMESPACE? This will destroy deployed data. [y/N] " response
    case "$response" in
        y|Y|yes|YES)
            ;;
        *)
            fail "Database reset cancelled."
            ;;
    esac
}

secret_value() {
    local secret_name="$1"
    local key="$2"

    oc get secret "$secret_name" -n "$NAMESPACE" -o "go-template={{index .data \"$key\"}}" | base64 -d
}

wait_for_scaledown() {
    local label="$1"

    oc wait --for=delete pod -l "$label" -n "$NAMESPACE" --timeout=180s >/dev/null 2>&1 || true
}

get_replicas() {
    local deployment_name="$1"
    oc get deployment "$deployment_name" -n "$NAMESPACE" -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "0"
}

confirm

info "Target namespace: $NAMESPACE"

APP_REPLICAS="$(get_replicas learnwithai-app)"
WORKER_REPLICAS="$(get_replicas learnwithai-worker)"

POSTGRESQL_USER="$(secret_value learnwithai-postgres-credentials POSTGRESQL_USER)"
POSTGRESQL_DATABASE="$(secret_value learnwithai-postgres-credentials POSTGRESQL_DATABASE)"

BOOTSTRAP_JOB="learnwithai-db-bootstrap-$(date +%s)"
BOOTSTRAP_CONFIGMAP="${BOOTSTRAP_JOB}-script"
BOOTSTRAP_IMAGE="image-registry.openshift-image-registry.svc:5000/${NAMESPACE}/learnwithai-app:latest"
BOOTSTRAP_SCRIPT_LOCAL="$REPO_ROOT/packages/learnwithai-core/scripts/bootstrap_deployment_db.py"
BOOTSTRAP_SCRIPT_MOUNT_PATH="/bootstrap/bootstrap_deployment_db.py"

[ -f "$BOOTSTRAP_SCRIPT_LOCAL" ] || fail "Bootstrap script not found at $BOOTSTRAP_SCRIPT_LOCAL"

info "Scaling app and worker down..."
RESTORE_REPLICAS=true
oc scale deployment/learnwithai-app deployment/learnwithai-worker -n "$NAMESPACE" --replicas=0
wait_for_scaledown 'app.kubernetes.io/name=learnwithai-app'
wait_for_scaledown 'app.kubernetes.io/name=learnwithai-worker'

info "Dropping and recreating database $POSTGRESQL_DATABASE..."
oc exec deployment/learnwithai-postgres -n "$NAMESPACE" -- sh -lc "psql -v ON_ERROR_STOP=1 -U postgres -d postgres -c \"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$POSTGRESQL_DATABASE' AND pid <> pg_backend_pid();\" -c \"DROP DATABASE IF EXISTS \\\"$POSTGRESQL_DATABASE\\\";\" -c \"CREATE DATABASE \\\"$POSTGRESQL_DATABASE\\\" OWNER \\\"$POSTGRESQL_USER\\\";\""

info "Running SQLModel bootstrap job $BOOTSTRAP_JOB..."
oc delete job "$BOOTSTRAP_JOB" -n "$NAMESPACE" --ignore-not-found=true >/dev/null 2>&1 || true
oc delete configmap "$BOOTSTRAP_CONFIGMAP" -n "$NAMESPACE" --ignore-not-found=true >/dev/null 2>&1 || true
oc create configmap "$BOOTSTRAP_CONFIGMAP" -n "$NAMESPACE" --from-file="bootstrap_deployment_db.py=$BOOTSTRAP_SCRIPT_LOCAL"
JOB_MANIFEST="$(mktemp)"
cat > "$JOB_MANIFEST" <<EOF
{
    "apiVersion": "batch/v1",
    "kind": "Job",
    "metadata": {
        "name": "$BOOTSTRAP_JOB",
        "namespace": "$NAMESPACE"
    },
    "spec": {
        "backoffLimit": 0,
        "template": {
            "metadata": {
                "labels": {
                    "app.kubernetes.io/name": "$BOOTSTRAP_JOB"
                }
            },
            "spec": {
                "restartPolicy": "Never",
                "volumes": [
                    {
                        "name": "bootstrap-script",
                        "configMap": {
                            "name": "$BOOTSTRAP_CONFIGMAP"
                        }
                    }
                ],
                "containers": [
                    {
                        "name": "bootstrap",
                        "image": "$BOOTSTRAP_IMAGE",
                        "imagePullPolicy": "Always",
                        "command": [
                            "/app/.venv/bin/python",
                            "$BOOTSTRAP_SCRIPT_MOUNT_PATH"
                        ],
                        "envFrom": [
                            {
                                "secretRef": {
                                    "name": "learnwithai-secrets"
                                }
                            }
                        ],
                        "env": [
                            {
                                "name": "ENVIRONMENT",
                                "value": "production"
                            }
                        ],
                        "volumeMounts": [
                            {
                                "name": "bootstrap-script",
                                "mountPath": "/bootstrap",
                                "readOnly": true
                            }
                        ]
                    }
                ]
            }
        }
    }
}
EOF
oc apply -f "$JOB_MANIFEST"
rm -f "$JOB_MANIFEST"
JOB_MANIFEST=""

oc wait --for=condition=complete "job/$BOOTSTRAP_JOB" -n "$NAMESPACE" --timeout=180s
oc logs "job/$BOOTSTRAP_JOB" -n "$NAMESPACE"
oc delete job "$BOOTSTRAP_JOB" -n "$NAMESPACE" --ignore-not-found=true >/dev/null 2>&1 || true
oc delete configmap "$BOOTSTRAP_CONFIGMAP" -n "$NAMESPACE" --ignore-not-found=true >/dev/null 2>&1 || true
BOOTSTRAP_CONFIGMAP=""

restore_replicas
RESTORE_REPLICAS=false

if [ "$APP_REPLICAS" != "0" ]; then
    oc rollout status deployment/learnwithai-app -n "$NAMESPACE" --timeout=300s
fi

if [ "$WORKER_REPLICAS" != "0" ]; then
    oc rollout status deployment/learnwithai-worker -n "$NAMESPACE" --timeout=300s
fi

echo
info "Database reset complete."