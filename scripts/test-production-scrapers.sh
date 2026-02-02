#!/bin/bash
set -euo pipefail

# TrainerLab Production Scraper Testing Script
# Usage: ./scripts/test-production-scrapers.sh [OPTIONS]
#
# This script manually triggers scrapers in the trainerlab-prod GCP environment
# and verifies their execution.

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
DRY_RUN=true
VERIFY=false
CHECK_LOGS=false
PIPELINE=""
RUN_ALL=false
LOOKBACK_DAYS=7
GAME_FORMAT="all"

usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Options:
    --pipeline=PIPELINE    Run specific pipeline: scrape-en, scrape-jp, compute-meta, sync-cards
    --all                  Run all pipelines (dry-run mode)
    --no-dry-run           Execute live run (writes data to database)
    --verify               Verify results after execution
    --check-logs           Check Cloud Logs for recent errors
    --lookback-days=N      Number of days to look back (default: 7)
    --format=FORMAT        Game format: standard, expanded, or all (default: all)
    -h, --help             Show this help message

Examples:
    # Dry run of English scraper (safe, default)
    $0 --pipeline=scrape-en

    # All pipelines in dry-run mode
    $0 --all

    # Live run with verification
    $0 --pipeline=scrape-en --no-dry-run --verify

    # Check recent Cloud Logs for errors
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
    SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
        --region="$REGION" \
        --format='value(status.url)' 2>/dev/null || echo "")

    if [ -z "$SERVICE_URL" ]; then
        log_error "Failed to get service URL. Check that trainerlab-api is deployed."
        exit 1
    fi

    log_success "Service URL: $SERVICE_URL"
}

get_auth_token() {
    log_info "Getting authentication token..."
    TOKEN=$(gcloud auth print-identity-token --audiences="$SERVICE_URL" 2>/dev/null || echo "")

    if [ -z "$TOKEN" ]; then
        log_error "Failed to get authentication token."
        exit 1
    fi

    log_success "Authentication token acquired"
}

health_check() {
    log_info "Running health checks..."

    # API health check
    API_HEALTH=$(curl -s -H "Authorization: Bearer $TOKEN" "$SERVICE_URL/api/v1/health" || echo "")

    if echo "$API_HEALTH" | jq -e '.status == "healthy"' > /dev/null 2>&1; then
        log_success "API health check passed"
    else
        log_error "API health check failed"
        echo "$API_HEALTH" | jq '.' 2>/dev/null || echo "$API_HEALTH"
        exit 1
    fi

    # Database health check
    DB_STATUS=$(echo "$API_HEALTH" | jq -r '.database // "unknown"')
    if [ "$DB_STATUS" == "connected" ]; then
        log_success "Database health check passed"
    else
        log_warning "Database status: $DB_STATUS"
    fi
}

warn_live_run() {
    log_warning "⚠️  LIVE RUN MODE - This will write data to the production database!"
    log_warning "Press Ctrl+C to cancel, or wait 5 seconds to continue..."
    sleep 5
}

run_pipeline() {
    local pipeline=$1
    local endpoint=""
    local params=""

    case $pipeline in
        scrape-en)
            endpoint="/api/v1/pipeline/scrape-en"
            params="{\"dry_run\": $DRY_RUN, \"lookback_days\": $LOOKBACK_DAYS, \"game_format\": \"$GAME_FORMAT\"}"
            ;;
        scrape-jp)
            endpoint="/api/v1/pipeline/scrape-jp"
            params="{\"dry_run\": $DRY_RUN, \"lookback_days\": $LOOKBACK_DAYS, \"game_format\": \"$GAME_FORMAT\"}"
            ;;
        compute-meta)
            endpoint="/api/v1/pipeline/compute-meta"
            params="{\"dry_run\": $DRY_RUN, \"lookback_days\": $LOOKBACK_DAYS}"
            ;;
        sync-cards)
            endpoint="/api/v1/pipeline/sync-cards"
            params="{\"dry_run\": $DRY_RUN}"
            ;;
        *)
            log_error "Unknown pipeline: $pipeline"
            return 1
            ;;
    esac

    log_info "Running pipeline: $pipeline (dry_run=$DRY_RUN)"
    echo -e "${BLUE}Endpoint:${NC} $endpoint"
    echo -e "${BLUE}Parameters:${NC} $params"

    START_TIME=$(date +%s)

    RESPONSE=$(curl -s -X POST \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "$params" \
        "$SERVICE_URL$endpoint")

    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))

    echo ""
    log_info "Response (took ${DURATION}s):"
    echo "$RESPONSE" | jq '.' 2>/dev/null || echo "$RESPONSE"
    echo ""

    # Check for success
    if echo "$RESPONSE" | jq -e '.success == true' > /dev/null 2>&1; then
        log_success "Pipeline completed successfully"

        # Show key metrics
        case $pipeline in
            scrape-en|scrape-jp)
                TOURNAMENTS=$(echo "$RESPONSE" | jq -r '.tournaments_saved // 0')
                PLACEMENTS=$(echo "$RESPONSE" | jq -r '.placements_saved // 0')
                ERRORS=$(echo "$RESPONSE" | jq -r '.errors // []')

                log_info "Tournaments saved: $TOURNAMENTS"
                log_info "Placements saved: $PLACEMENTS"

                if [ "$ERRORS" != "[]" ]; then
                    log_warning "Errors encountered:"
                    echo "$ERRORS" | jq '.'
                fi
                ;;
            compute-meta)
                SNAPSHOTS=$(echo "$RESPONSE" | jq -r '.snapshots_saved // 0')
                log_info "Snapshots saved: $SNAPSHOTS"
                ;;
            sync-cards)
                CARDS=$(echo "$RESPONSE" | jq -r '.cards_synced // 0')
                SETS=$(echo "$RESPONSE" | jq -r '.sets_synced // 0')
                log_info "Cards synced: $CARDS"
                log_info "Sets synced: $SETS"
                ;;
        esac

        return 0
    else
        log_error "Pipeline failed"
        ERROR_MSG=$(echo "$RESPONSE" | jq -r '.error // "Unknown error"')
        log_error "Error: $ERROR_MSG"
        return 1
    fi
}

verify_results() {
    log_info "Verifying results..."

    TOURNAMENTS=$(curl -s -H "Authorization: Bearer $TOKEN" \
        "$SERVICE_URL/api/v1/tournaments?limit=10&sort_by=date&order=desc")

    if echo "$TOURNAMENTS" | jq -e '.items | length > 0' > /dev/null 2>&1; then
        COUNT=$(echo "$TOURNAMENTS" | jq '.items | length')
        log_success "Found $COUNT recent tournaments in database"

        echo ""
        log_info "Recent tournaments:"
        echo "$TOURNAMENTS" | jq -r '.items[] | "\(.date) - \(.name) (\(.format))"' | head -5
    else
        log_warning "No tournaments found in database"
    fi
}

check_cloud_logs() {
    log_info "Checking Cloud Logs for recent errors..."

    # Check logs from the last hour
    LOGS=$(gcloud logging read \
        "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME AND severity>=ERROR" \
        --limit=20 \
        --format=json \
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
        --no-dry-run)
            DRY_RUN=false
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
        --lookback-days=*)
            LOOKBACK_DAYS="${1#*=}"
            shift
            ;;
        --format=*)
            GAME_FORMAT="${1#*=}"
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
echo "║   TrainerLab Production Scraper Testing                   ║"
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

# Run checks
check_prerequisites
get_service_url
get_auth_token
health_check

echo ""

# Warn if live run
if [ "$DRY_RUN" = false ]; then
    warn_live_run
fi

# Run pipelines
if [ "$RUN_ALL" = true ]; then
    log_info "Running all pipelines in dry-run mode..."
    echo ""

    for pipeline in scrape-en scrape-jp sync-cards compute-meta; do
        run_pipeline "$pipeline" || log_warning "Pipeline $pipeline failed, continuing..."
        echo ""
        echo "────────────────────────────────────────────────────────────"
        echo ""
    done
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
