#!/bin/bash
set -euo pipefail

# TrainerLab Production Pipeline Testing Script
# Usage: ./scripts/test-production-scrapers.sh [OPTIONS]
#
# This script manually triggers pipelines in the trainerlab-prod GCP environment
# via Cloud Scheduler jobs. This is the recommended way to test pipelines as it
# uses the same authentication path as production.

PROJECT_ID="trainerlab-prod"
REGION="us-west1"
SERVICE_NAME="trainerlab-api"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
CONFIRM=false
VERIFY=false
CHECK_LOGS=false
PIPELINE=""
RUN_ALL=false

usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Triggers Cloud Scheduler jobs to run pipeline tasks. This uses the scheduler's
service account authentication, which is the same path used in production.

Options:
    --pipeline=PIPELINE      Run specific pipeline (see list below)
    --all                    Run all pipelines concurrently
    --confirm                Confirm you want to write data to production database
    --verify                 Verify results after execution
    --check-logs             Check Cloud Logs for recent errors (no pipeline execution)
    -h, --help               Show this help message

Pipelines:
    discover-en              Discover new EN tournaments (daily)
    discover-jp              Discover new JP tournaments (daily)
    compute-meta             Compute daily meta snapshots (daily)
    compute-evolution        AI classification + predictions (daily)
    sync-cards               Sync card data from TCGdex (weekly)
    sync-card-mappings       Sync JP-to-EN card mappings (weekly)
    translate-pokecabook     Translate Pokecabook content (MWF)
    sync-jp-adoption         Sync JP card adoption rates (TTS)
    translate-tier-lists     Translate JP tier lists (weekly)
    monitor-card-reveals     Monitor JP card reveals (every 6h)
    cleanup-exports          Clean up expired export files (weekly)

Note: Cloud Scheduler jobs always run with their Terraform-configured parameters
      (dry_run=false). This will write real data to the production database.

Examples:
    # Run English discovery (requires --confirm)
    $0 --pipeline=discover-en --confirm

    # Run all pipelines
    $0 --all --confirm

    # Run and verify results
    $0 --pipeline=discover-en --confirm --verify

    # Check recent errors (no execution)
    $0 --check-logs

EOF
    exit 0
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check gcloud
    if ! command -v gcloud &> /dev/null; then
        log_error "gcloud CLI not found. Please install it first."
        exit 1
    fi

    # Check jq
    if ! command -v jq &> /dev/null; then
        log_error "jq not found. Please install it first (brew install jq)"
        exit 1
    fi

    # Check authentication
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
        log_error "Not authenticated. Run: gcloud auth login"
        exit 1
    fi

    # Set project
    gcloud config set project "$PROJECT_ID" --quiet

    log_success "Prerequisites check passed"
}

get_service_url() {
    log_info "Getting service URL..."

    # Get project number to construct URL in the format matching API's CLOUD_RUN_URL setting
    PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)' 2>/dev/null || echo "")

    if [ -z "$PROJECT_NUMBER" ]; then
        log_error "Failed to get project number."
        exit 1
    fi

    # Construct URL in the format: https://SERVICE-PROJECT_NUMBER.REGION.run.app
    SERVICE_URL="https://${SERVICE_NAME}-${PROJECT_NUMBER}.${REGION}.run.app"

    log_success "Service URL: $SERVICE_URL"
}

health_check() {
    log_info "Checking Cloud Run service status..."

    # Check if the service exists and is serving
    SERVICE_STATUS=$(gcloud run services describe "$SERVICE_NAME" \
        --region="$REGION" \
        --format='value(status.conditions[0].status)' 2>/dev/null || echo "")

    if [ "$SERVICE_STATUS" = "True" ]; then
        log_success "Cloud Run service is healthy"
    else
        log_warning "Cloud Run service status: $SERVICE_STATUS (may still be starting)"
    fi
}

run_pipeline() {
    local pipeline=$1
    local job_name="trainerlab-${pipeline}"

    log_info "Running pipeline: $pipeline via Cloud Scheduler job"
    echo -e "${BLUE}Job:${NC} $job_name"

    START_TIME=$(date +%s)

    # Trigger the scheduler job - this uses the scheduler SA's native token
    log_info "Triggering Cloud Scheduler job..."
    if ! gcloud scheduler jobs run "$job_name" --location="$REGION" 2>&1; then
        log_error "Failed to trigger scheduler job"
        return 1
    fi

    # Wait for the job to complete and check logs
    log_info "Job triggered, waiting for completion..."
    sleep 8

    # Check the most recent request to this pipeline
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))

    log_info "Checking Cloud Run logs for result..."
    RESULT=$(gcloud logging read \
        "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"$SERVICE_NAME\" AND httpRequest.requestUrl:\"/api/v1/pipeline/${pipeline}\"" \
        --limit=1 \
        --format='value(httpRequest.status)' \
        --freshness=2m \
        --project="$PROJECT_ID" 2>/dev/null || echo "")

    echo ""
    if [ "$RESULT" = "200" ]; then
        log_success "Pipeline completed successfully (HTTP $RESULT, took ${DURATION}s)"

        # Get detailed response from logs if available
        RESPONSE_LOG=$(gcloud logging read \
            "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"$SERVICE_NAME\" AND jsonPayload.message:\"Pipeline\"" \
            --limit=5 \
            --format='value(jsonPayload.message)' \
            --freshness=2m \
            --project="$PROJECT_ID" 2>/dev/null || echo "")

        if [ -n "$RESPONSE_LOG" ]; then
            log_info "Pipeline logs:"
            echo "$RESPONSE_LOG"
        fi

        return 0
    elif [ "$RESULT" = "401" ]; then
        log_error "Pipeline authentication failed (HTTP $RESULT)"
        log_error "Check scheduler service account permissions"
        return 1
    elif [ -n "$RESULT" ]; then
        log_error "Pipeline failed with HTTP $RESULT"
        return 1
    else
        log_warning "Could not determine result from logs (job may still be running)"
        log_info "Check logs manually: gcloud logging read 'resource.labels.service_name=\"$SERVICE_NAME\"' --freshness=5m"
        return 1
    fi
}

verify_results() {
    log_info "Verifying results via Cloud Logging..."

    # Check recent successful pipeline executions
    log_info "Recent pipeline executions:"
    gcloud logging read \
        "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"$SERVICE_NAME\" AND httpRequest.requestUrl:\"/api/v1/pipeline\"" \
        --limit=10 \
        --format='table(timestamp, httpRequest.status, httpRequest.requestUrl)' \
        --freshness=1h \
        --project="$PROJECT_ID" 2>/dev/null || log_warning "Could not fetch logs"
}

check_cloud_logs() {
    log_info "Checking Cloud Logs for recent errors..."

    # Check logs from the last hour
    LOGS=$(gcloud logging read \
        "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME AND severity>=ERROR" \
        --limit=20 \
        --format=json \
        --freshness=1h \
        --project="$PROJECT_ID" 2>/dev/null || echo "[]")

    ERROR_COUNT=$(echo "$LOGS" | jq '. | length')

    if [ "$ERROR_COUNT" -eq 0 ]; then
        log_success "No recent errors found in logs"
    else
        log_warning "Found $ERROR_COUNT recent errors:"
        echo ""
        echo "$LOGS" | jq -r '.[] | "\(.timestamp) - \(.textPayload // .jsonPayload.message // "No message")"' | head -10
    fi
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --pipeline=*)
            PIPELINE="${1#*=}"
            shift
            ;;
        --all)
            RUN_ALL=true
            shift
            ;;
        --confirm)
            CONFIRM=true
            shift
            ;;
        --verify)
            VERIFY=true
            shift
            ;;
        --check-logs)
            CHECK_LOGS=true
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

# Main execution
echo "╔════════════════════════════════════════════════════════════╗"
echo "║   TrainerLab Production Pipeline Testing                  ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Handle --check-logs separately
if [ "$CHECK_LOGS" = true ]; then
    check_prerequisites
    check_cloud_logs
    exit 0
fi

# Validate pipeline selection
if [ "$RUN_ALL" = false ] && [ -z "$PIPELINE" ]; then
    log_error "Must specify --pipeline or --all"
    usage
fi

# Require confirmation for pipeline execution
if [ "$CONFIRM" = false ]; then
    log_error "Pipeline execution writes to production database."
    log_error "Use --confirm to acknowledge this."
    exit 1
fi

# Run checks
check_prerequisites
get_service_url
health_check

echo ""
log_warning "⚠️  This will write data to the PRODUCTION database!"
log_warning "Press Ctrl+C to cancel, or wait 5 seconds to continue..."
sleep 5

# Run pipelines
if [ "$RUN_ALL" = true ]; then
    log_info "Running all pipelines concurrently..."
    echo ""

    # Trigger all scheduler jobs in parallel
    PIDS=()
    PIPELINES=(sync-cards sync-card-mappings discover-en discover-jp compute-meta compute-evolution translate-pokecabook sync-jp-adoption translate-tier-lists monitor-card-reveals cleanup-exports)

    for pipeline in "${PIPELINES[@]}"; do
        job_name="trainerlab-${pipeline}"
        log_info "Triggering $pipeline..."
        gcloud scheduler jobs run "$job_name" --location="$REGION" 2>&1 &
        PIDS+=($!)
    done

    # Wait for all triggers to complete
    log_info "Waiting for all jobs to be triggered..."
    for pid in "${PIDS[@]}"; do
        wait "$pid" 2>/dev/null || true
    done

    log_success "All jobs triggered, waiting for completion..."
    sleep 15  # sync-cards may take longer due to card data sync

    # Check results for all pipelines
    echo ""
    log_info "Checking results..."
    echo ""

    FAILED=0
    for pipeline in "${PIPELINES[@]}"; do
        RESULT=$(gcloud logging read \
            "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"$SERVICE_NAME\" AND httpRequest.requestUrl:\"/api/v1/pipeline/${pipeline}\"" \
            --limit=1 \
            --format='value(httpRequest.status)' \
            --freshness=2m \
            --project="$PROJECT_ID" 2>/dev/null || echo "")

        if [ "$RESULT" = "200" ]; then
            log_success "$pipeline: HTTP 200 OK"
        elif [ "$RESULT" = "401" ]; then
            log_error "$pipeline: HTTP 401 Unauthorized"
            FAILED=$((FAILED + 1))
        elif [ -n "$RESULT" ]; then
            log_error "$pipeline: HTTP $RESULT"
            FAILED=$((FAILED + 1))
        else
            log_warning "$pipeline: No result yet (may still be running)"
        fi
    done

    echo ""
    if [ "$FAILED" -eq 0 ]; then
        log_success "All pipelines completed successfully!"
    else
        log_warning "$FAILED pipeline(s) failed"
    fi
else
    run_pipeline "$PIPELINE"
fi

# Verify if requested
if [ "$VERIFY" = true ]; then
    echo ""
    verify_results
fi

echo ""
log_success "Script completed"
