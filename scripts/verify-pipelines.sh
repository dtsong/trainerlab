#!/bin/bash
set -euo pipefail

# TrainerLab Pipeline Verification Script
# Usage: ./scripts/verify-pipelines.sh [OPTIONS]
#
# Triggers each pipeline via Cloud Scheduler, waits for completion, then
# verifies data via authenticated GET endpoints.

PROJECT_ID="trainerlab-prod"
REGION="us-west1"
SERVICE_NAME="trainerlab-api"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Default values
STEP=""
VERIFY_ONLY=false
SERVICE_URL=""
TOKEN=""

# Poll settings
POLL_INTERVAL=10
POLL_TIMEOUT=600  # 10 minutes

usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Triggers each pipeline via Cloud Scheduler, waits for completion, then
verifies data via authenticated GET endpoints.

Options:
    --step=N           Run specific step (1-4)
    --verify-only      Skip triggers, just check data
    -h, --help         Show this help message

Steps:
    1  sync-cards     — Sync card database from TCGdex
    2  discover-en    — Discover & enqueue English tournaments
    3  discover-jp    — Discover & enqueue Japanese tournaments
    4  compute-meta   — Compute meta archetypes

Examples:
    $0                   # Run all steps
    $0 --step=1          # Run only sync-cards
    $0 --verify-only     # Skip triggers, just check data

EOF
    exit 0
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $1"
}

log_step() {
    echo ""
    echo -e "${BOLD}[STEP $1] $2${NC}"
    echo "────────────────────────────────────────"
}

check_prerequisites() {
    log_info "Checking prerequisites..."

    if ! command -v gcloud &> /dev/null; then
        log_error "gcloud CLI not found. Please install it first."
        exit 1
    fi

    if ! command -v jq &> /dev/null; then
        log_error "jq not found. Please install it first (brew install jq)"
        exit 1
    fi

    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
        log_error "Not authenticated. Run: gcloud auth login"
        exit 1
    fi

    gcloud config set project "$PROJECT_ID" --quiet

    log_success "Prerequisites OK"
}

setup_auth() {
    log_info "Getting service URL and auth token..."

    SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
        --region="$REGION" \
        --format='value(status.url)')

    if [ -z "$SERVICE_URL" ]; then
        log_error "Failed to get service URL"
        exit 1
    fi

    TOKEN=$(gcloud auth print-identity-token 2>/dev/null || echo "")

    if [ -z "$TOKEN" ]; then
        log_error "Failed to get identity token. Run: gcloud auth login"
        exit 1
    fi

    log_info "Service: $SERVICE_URL"
}

# Trigger a Cloud Scheduler job and poll until AttemptFinished
trigger_and_wait() {
    local job_name=$1

    log_info "Trigger: gcloud scheduler jobs run $job_name"
    if ! gcloud scheduler jobs run "$job_name" --location="$REGION" 2>&1; then
        log_error "Failed to trigger scheduler job: $job_name"
        return 1
    fi
    log_info "Trigger: OK"

    # Poll scheduler logs for AttemptFinished
    log_info "Waiting for completion (polling every ${POLL_INTERVAL}s, timeout ${POLL_TIMEOUT}s)..."

    local elapsed=0
    local status=""

    while [ "$elapsed" -lt "$POLL_TIMEOUT" ]; do
        sleep "$POLL_INTERVAL"
        elapsed=$((elapsed + POLL_INTERVAL))

        # Check Cloud Run logs for the pipeline request result
        status=$(gcloud logging read \
            "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"$SERVICE_NAME\" AND httpRequest.requestUrl:\"/api/v1/pipeline/${job_name#trainerlab-}\"" \
            --limit=1 \
            --format='value(httpRequest.status)' \
            --freshness=5m \
            --project="$PROJECT_ID" 2>/dev/null || echo "")

        if [ -n "$status" ]; then
            break
        fi

        printf "  ... %ds elapsed\n" "$elapsed"
    done

    if [ -z "$status" ]; then
        log_warning "Scheduler: Timed out waiting for result"
        return 1
    fi

    echo -e "  Scheduler: HTTP ${status}"

    if [ "$status" != "200" ]; then
        log_error "Scheduler job returned HTTP $status"
        return 1
    fi

    return 0
}

# Query a verification endpoint and check the response
verify_endpoint() {
    local endpoint=$1
    local check_fn=$2  # jq expression that returns "pass" or "fail"
    local summary_fn=$3  # jq expression for human-readable summary

    local url="${SERVICE_URL}${endpoint}"

    local response
    response=$(curl -s -w "\n%{http_code}" \
        -H "Authorization: Bearer $TOKEN" \
        "$url" 2>/dev/null)

    local http_code
    http_code=$(echo "$response" | tail -n1)
    local body
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" != "200" ]; then
        log_error "Verify: HTTP $http_code from $endpoint"
        return 1
    fi

    local result
    result=$(echo "$body" | jq -r "$check_fn" 2>/dev/null || echo "fail")

    local summary
    summary=$(echo "$body" | jq -r "$summary_fn" 2>/dev/null || echo "no summary")

    if [ "$result" = "pass" ]; then
        log_success "Verify: $summary — PASS"
        return 0
    else
        log_error "Verify: $summary — FAIL"
        return 1
    fi
}

# ─── Pipeline Steps ──────────────────────────────────────────────────────────

run_step_1() {
    log_step 1 "sync-cards"

    if [ "$VERIFY_ONLY" = false ]; then
        trigger_and_wait "trainerlab-sync-cards" || true
    fi

    verify_endpoint \
        "/api/v1/cards?limit=1" \
        'if .total > 0 then "pass" else "fail" end' \
        '"\(.total) cards found"'
}

run_step_2() {
    log_step 2 "discover-en"

    if [ "$VERIFY_ONLY" = false ]; then
        trigger_and_wait "trainerlab-discover-en" || true
    fi

    verify_endpoint \
        "/api/v1/tournaments?limit=5" \
        'if .total > 0 then "pass" else "fail" end' \
        '"\(.total) tournaments found"'
}

run_step_3() {
    log_step 3 "discover-jp"

    if [ "$VERIFY_ONLY" = false ]; then
        trigger_and_wait "trainerlab-discover-jp" || true
    fi

    verify_endpoint \
        "/api/v1/tournaments?region=JP&limit=5" \
        'if .total > 0 then "pass" else "fail" end' \
        '"\(.total) JP tournaments found"'
}

run_step_4() {
    log_step 4 "compute-meta"

    if [ "$VERIFY_ONLY" = false ]; then
        trigger_and_wait "trainerlab-compute-meta" || true
    fi

    verify_endpoint \
        "/api/v1/meta/current" \
        'if .archetype_breakdown and (.archetype_breakdown | length) > 0 then "pass" else "fail" end' \
        '"meta response with \(.archetype_breakdown | length) archetypes"'
}

# ─── Argument Parsing ────────────────────────────────────────────────────────

while [[ $# -gt 0 ]]; do
    case $1 in
        --step=*)
            STEP="${1#*=}"
            shift
            ;;
        --verify-only)
            VERIFY_ONLY=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            ;;
    esac
done

# ─── Main ────────────────────────────────────────────────────────────────────

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║   TrainerLab Pipeline Verification                        ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

if [ "$VERIFY_ONLY" = true ]; then
    log_info "Mode: verify-only (skipping triggers)"
else
    log_info "Mode: trigger + verify"
fi

check_prerequisites
setup_auth

PASSED=0
FAILED=0
TOTAL=0

run_and_track() {
    TOTAL=$((TOTAL + 1))
    if "$@"; then
        PASSED=$((PASSED + 1))
    else
        FAILED=$((FAILED + 1))
    fi
}

if [ -n "$STEP" ]; then
    case $STEP in
        1) run_and_track run_step_1 ;;
        2) run_and_track run_step_2 ;;
        3) run_and_track run_step_3 ;;
        4) run_and_track run_step_4 ;;
        *) log_error "Invalid step: $STEP (must be 1-4)"; exit 1 ;;
    esac
else
    run_and_track run_step_1
    run_and_track run_step_2
    run_and_track run_step_3
    run_and_track run_step_4
fi

# ─── Summary ─────────────────────────────────────────────────────────────────

echo ""
echo "════════════════════════════════════════════════════════════"
echo -e "  Results: ${GREEN}${PASSED} passed${NC}, ${RED}${FAILED} failed${NC} (${TOTAL} total)"
echo "════════════════════════════════════════════════════════════"
echo ""

if [ "$FAILED" -gt 0 ]; then
    log_info "Next step: check Cloud Run app logs for errors during the pipeline run"
    log_info "  gcloud logging read 'resource.labels.service_name=\"$SERVICE_NAME\" AND severity>=ERROR' --freshness=10m"
    exit 1
fi
