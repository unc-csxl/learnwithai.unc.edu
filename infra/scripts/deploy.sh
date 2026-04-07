#!/usr/bin/env bash
# =============================================================================
# deploy.sh — First-time deployment of LearnWithAI to an OKD cluster
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFESTS_DIR="$SCRIPT_DIR/../manifests"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BUILD_NAME="learnwithai-app"
GIT_SOURCE_SECRET_NAME="learnwithai-git-source"
GITHUB_WEBHOOK_SECRET_NAME="learnwithai-github-webhook"
GENERIC_WEBHOOK_SECRET_NAME="learnwithai-generic-webhook"
TMP_DIR="$(mktemp -d)"

cleanup() {
    rm -rf "$TMP_DIR"
}
trap cleanup EXIT

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
  ./infra/scripts/deploy.sh <namespace> [options]

Options:
  --repo-url <url>               Git repository URL for OKD to clone.
  --git-ref <ref>                Git branch or ref to build from. Default: main.
  --key-path <path>              Private SSH key path for the OKD source clone secret.
  --rotate-deploy-key            Generate a fresh GitHub deploy key even if one exists.
  --github-webhook-secret <val>  Override the GitHub webhook secret value.
  --generic-webhook-secret <val> Override the generic webhook secret value.
  --non-interactive              Skip the prompt that waits for the GitHub deploy key to be added.
  -h, --help                     Show this help message.

Examples:
  ./infra/scripts/deploy.sh comp423-example
  ./infra/scripts/deploy.sh comp423-example --git-ref main
EOF
}

require_command() {
    command -v "$1" >/dev/null 2>&1 || fail "$1 not found."
}

random_secret() {
    openssl rand -hex 24
}

normalize_repo_url() {
    local value="$1"

    case "$value" in
        https://github.com/*.git)
            value="git@github.com:${value#https://github.com/}"
            ;;
        https://github.com/*)
            value="git@github.com:${value#https://github.com/}.git"
            ;;
        ssh://git@github.com/*)
            value="git@github.com:${value#ssh://git@github.com/}"
            ;;
    esac

    echo "$value"
}

extract_repo_host() {
    local value="$1"

    case "$value" in
        git@*:* )
            echo "${value#git@}" | cut -d: -f1
            ;;
        ssh://git@*/*)
            echo "${value#ssh://git@}" | cut -d/ -f1
            ;;
        https://*/*)
            echo "${value#https://}" | cut -d/ -f1
            ;;
        http://*/*)
            echo "${value#http://}" | cut -d/ -f1
            ;;
        *)
            echo "github.com"
            ;;
    esac
}

apply_manifest() {
    envsubst '${NAMESPACE} ${GIT_REPO_URL} ${GIT_REF}' < "$1" | oc apply -f -
}

resolve_runtime_secrets_file() {
    if [ -f "$MANIFESTS_DIR/secrets.yaml" ]; then
        echo "$MANIFESTS_DIR/secrets.yaml"
        return
    fi

    if [ -f "$MANIFESTS_DIR/secrets.local.yaml" ]; then
        echo "$MANIFESTS_DIR/secrets.local.yaml"
        return
    fi

    fail "Expected $MANIFESTS_DIR/secrets.yaml. Copy infra/manifests/secrets.example.yaml to secrets.yaml and fill in real values first."
}

ensure_namespace() {
    if oc get namespace "$NAMESPACE" >/dev/null 2>&1; then
        warn "Namespace $NAMESPACE already exists. Reusing it without modifying cluster-scoped metadata."
        return
    fi

    envsubst '${NAMESPACE}' < "$MANIFESTS_DIR/namespace.yaml" | oc create -f -
}

ensure_deploy_key() {
    local key_dir

    if [ -z "$KEY_PATH" ]; then
        key_dir="${HOME}/.config/learnwithai/okd"
        mkdir -p "$key_dir"
        KEY_PATH="$key_dir/${NAMESPACE}-github-deploy-key"
    fi

    if [ "$ROTATE_DEPLOY_KEY" -eq 1 ]; then
        rm -f "$KEY_PATH" "$KEY_PATH.pub"
    fi

    if [ ! -f "$KEY_PATH" ]; then
        info "Generating an OKD source-clone deploy key at $KEY_PATH"
        ssh-keygen -q -t ed25519 -N "" -C "learnwithai-okd-${NAMESPACE}" -f "$KEY_PATH"
    else
        info "Reusing existing deploy key at $KEY_PATH"
    fi

    ssh-keyscan "$SOURCE_HOST" > "$TMP_DIR/known_hosts" 2>/dev/null
    if [ ! -s "$TMP_DIR/known_hosts" ]; then
        fail "Could not fetch host keys for $SOURCE_HOST with ssh-keyscan."
    fi
}

prompt_for_github_deploy_key() {
    echo
    info "Add this public key as a read-only deploy key in your GitHub repository before the first build runs:"
    info "Repository: $GIT_REPO_URL"
    info "Suggested title: learnwithai-okd-$NAMESPACE"
    echo
    cat "$KEY_PATH.pub"
    echo

    if [ "$NON_INTERACTIVE" -eq 0 ]; then
        read -r -p "Press Enter after the deploy key has been added to GitHub..." _
    fi
}

ensure_build_secrets() {
    info "Creating or updating OKD build secrets..."

    oc create secret generic "$GIT_SOURCE_SECRET_NAME" \
        -n "$NAMESPACE" \
        --from-file=ssh-privatekey="$KEY_PATH" \
        --from-file=known_hosts="$TMP_DIR/known_hosts" \
        --type=kubernetes.io/ssh-auth \
        --dry-run=client \
        -o yaml | oc apply -f -

    oc create secret generic "$GITHUB_WEBHOOK_SECRET_NAME" \
        -n "$NAMESPACE" \
        --from-literal=WebHookSecretKey="$GITHUB_WEBHOOK_SECRET" \
        --dry-run=client \
        -o yaml | oc apply -f -

    oc create secret generic "$GENERIC_WEBHOOK_SECRET_NAME" \
        -n "$NAMESPACE" \
        --from-literal=WebHookSecretKey="$GENERIC_WEBHOOK_SECRET" \
        --dry-run=client \
        -o yaml | oc apply -f -
}

print_webhook_summary() {
    local server generic_url github_url

    server="$(oc whoami --show-server)"
    generic_url="${server%/}/apis/build.openshift.io/v1/namespaces/${NAMESPACE}/buildconfigs/${BUILD_NAME}/webhooks/${GENERIC_WEBHOOK_SECRET}/generic"
    github_url="${server%/}/apis/build.openshift.io/v1/namespaces/${NAMESPACE}/buildconfigs/${BUILD_NAME}/webhooks/${GITHUB_WEBHOOK_SECRET}/github"

    echo
    info "Save this GitHub Actions secret in the repository:"
    info "  OKD_GENERIC_WEBHOOK_URL=$generic_url"
    echo
    info "Optional direct GitHub repository webhook URL:"
    info "  $github_url"
    info "Use content type application/json and push events only if you enable it in GitHub."
}

NAMESPACE=""
GIT_REPO_URL="${GIT_REPO_URL:-}"
GIT_REF="${GIT_REF:-main}"
KEY_PATH="${OKD_DEPLOY_KEY_PATH:-}"
GITHUB_WEBHOOK_SECRET="${GITHUB_WEBHOOK_SECRET:-}"
GENERIC_WEBHOOK_SECRET="${GENERIC_WEBHOOK_SECRET:-}"
ROTATE_DEPLOY_KEY=0
NON_INTERACTIVE=0
SOURCE_HOST=""
SECRETS_FILE=""

while [ $# -gt 0 ]; do
    case "$1" in
        --repo-url)
            GIT_REPO_URL="$2"
            shift 2
            ;;
        --git-ref|--ref)
            GIT_REF="$2"
            shift 2
            ;;
        --key-path)
            KEY_PATH="$2"
            shift 2
            ;;
        --rotate-deploy-key)
            ROTATE_DEPLOY_KEY=1
            shift
            ;;
        --github-webhook-secret)
            GITHUB_WEBHOOK_SECRET="$2"
            shift 2
            ;;
        --generic-webhook-secret)
            GENERIC_WEBHOOK_SECRET="$2"
            shift 2
            ;;
        --non-interactive)
            NON_INTERACTIVE=1
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

require_command oc
require_command envsubst
require_command curl
require_command git
require_command openssl
require_command ssh-keygen
require_command ssh-keyscan

oc whoami >/dev/null 2>&1 || fail "Not logged into an OKD cluster. Run: oc login <cluster-url>"

if [ -z "$GIT_REPO_URL" ]; then
    GIT_REPO_URL="$(git -C "$REPO_ROOT" config --get remote.origin.url || true)"
fi

[ -n "$GIT_REPO_URL" ] || fail "Could not determine the repository URL. Pass --repo-url explicitly."
GIT_REPO_URL="$(normalize_repo_url "$GIT_REPO_URL")"
SOURCE_HOST="$(extract_repo_host "$GIT_REPO_URL")"

if [ -z "$GITHUB_WEBHOOK_SECRET" ]; then
    GITHUB_WEBHOOK_SECRET="$(random_secret)"
fi

if [ -z "$GENERIC_WEBHOOK_SECRET" ]; then
    GENERIC_WEBHOOK_SECRET="$(random_secret)"
fi

export NAMESPACE
export GIT_REPO_URL
export GIT_REF

info "Target namespace: $NAMESPACE"
info "Git source: $GIT_REPO_URL @ $GIT_REF"
info "Logged in as: $(oc whoami)"
info "Cluster: $(oc whoami --show-server)"
echo

SECRETS_FILE="$(resolve_runtime_secrets_file)"

if grep -q '<PLACEHOLDER>\|<DB_PASSWORD>\|<RABBITMQ_PASSWORD>\|<GENERATE_A_STRONG_SECRET>\|<PUBLIC_HOSTNAME>' "$SECRETS_FILE"; then
    fail "$(basename "$SECRETS_FILE") still contains placeholder values. Edit it before deploying."
fi

ensure_deploy_key
prompt_for_github_deploy_key

info "Step 1/7: Creating namespace..."
ensure_namespace
echo

info "Step 2/7: Applying runtime secrets from $(basename "$SECRETS_FILE")..."
envsubst '${NAMESPACE}' < "$SECRETS_FILE" | oc apply -f -
echo

info "Step 3/7: Creating build + webhook secrets..."
ensure_build_secrets
echo

info "Step 4/7: Enabling webhook access in the namespace..."
apply_manifest "$MANIFESTS_DIR/webhook-rbac.yaml"
echo

info "Step 5/7: Deploying PostgreSQL and RabbitMQ..."
apply_manifest "$MANIFESTS_DIR/postgres.yaml"
apply_manifest "$MANIFESTS_DIR/rabbitmq.yaml"

info "Waiting for PostgreSQL to be ready..."
oc rollout status deployment/learnwithai-postgres -n "$NAMESPACE" --timeout=120s

info "Waiting for RabbitMQ to be ready..."
oc rollout status deployment/learnwithai-rabbitmq -n "$NAMESPACE" --timeout=120s
echo

info "Step 6/7: Deploying application resources..."
apply_manifest "$MANIFESTS_DIR/app.yaml"
apply_manifest "$MANIFESTS_DIR/worker.yaml"
apply_manifest "$MANIFESTS_DIR/route.yaml"
echo

info "Step 7/7: Starting the initial image build from the local checkout..."
oc start-build "$BUILD_NAME" -n "$NAMESPACE" --from-repo="$REPO_ROOT" --follow
echo

info "Waiting for app deployment..."
oc rollout status deployment/learnwithai-app -n "$NAMESPACE" --timeout=300s

info "Waiting for worker deployment..."
oc rollout status deployment/learnwithai-worker -n "$NAMESPACE" --timeout=300s

ROUTE_HOST=$(oc get route learnwithai -n "$NAMESPACE" -o jsonpath='{.spec.host}' 2>/dev/null || echo "")
if [ -n "$ROUTE_HOST" ]; then
    info "Route: https://$ROUTE_HOST"
    info "Running health check..."
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "https://$ROUTE_HOST/api/health" --max-time 10 || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
        info "Health check passed! (HTTP $HTTP_CODE)"
    else
        warn "Health check returned HTTP $HTTP_CODE. The app may still be starting."
    fi
else
    warn "Could not determine route hostname."
fi

print_webhook_summary

echo
info "Deployment complete."
info "Useful commands:"
info "  ./infra/scripts/rollout.sh $NAMESPACE"
info "  oc get pods -n $NAMESPACE"
info "  oc logs -f deployment/learnwithai-app -n $NAMESPACE"
info "  oc logs -f deployment/learnwithai-worker -n $NAMESPACE"
info "  oc get route -n $NAMESPACE"
