#!/bin/bash
# Deep JP City League Ingestion Script
# Usage: ./scripts/ingest-jp-deep.sh [OPTIONS]
#
# Performs comprehensive ingestion of Japanese City League tournaments
# from November 28, 2025 (MEGA Dream EX release) to present.

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

# Configuration
START_DATE="${START_DATE:-2025-11-28}"
END_DATE="${END_DATE:-$(date +%Y-%m-%d)}"
API_URL="${API_URL:-http://localhost:8080}"
AUTO_PROCESS="${AUTO_PROCESS:-true}"
MAX_AUTO_PROCESS="${MAX_AUTO_PROCESS:-200}"
DRY_RUN="${DRY_RUN:-false}"

# Counters
STEP=0

usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Deep ingestion of Japanese City League tournaments from $START_DATE to present.

Options:
    --start-date=DATE   Start date (default: 2025-11-28)
    --end-date=DATE     End date (default: today)
    --api-url=URL       API URL (default: http://localhost:8080)
    --max-process=N     Max tournaments to auto-process (default: 200)
    --dry-run           Simulate without saving to database
    -h, --help          Show this help message

Environment Variables:
    START_DATE          Start date for ingestion
    END_DATE            End date for ingestion
    API_URL             API base URL
    ANTHROPIC_API_KEY   For LLM translation fetching

Examples:
    $0                                    # Full ingestion
    $0 --start-date=2026-01-23           # From Nihil Zero release
    $0 --dry-run                         # Test mode

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
    STEP=$((STEP + 1))
    echo ""
    echo -e "${BOLD}[Step $STEP] $1${NC}"
    echo "────────────────────────────────────────"
}

# Calculate days between dates
days_between() {
    local start=$1
    local end=$2

    # Convert to epoch seconds (macOS and Linux compatible)
    if command -v gdate &> /dev/null; then
        # macOS with coreutils
        local start_epoch=$(gdate -d "$start" +%s)
        local end_epoch=$(gdate -d "$end" +%s)
    else
        # Linux
        local start_epoch=$(date -d "$start" +%s)
        local end_epoch=$(date -d "$end" +%s)
    fi

    echo $(( (end_epoch - start_epoch) / 86400 ))
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    if ! command -v curl &> /dev/null; then
        log_error "curl is required but not installed"
        exit 1
    fi

    if ! command -v jq &> /dev/null; then
        log_error "jq is required but not installed (brew install jq)"
        exit 1
    fi

    # Check if API is accessible
    if ! curl -s "$API_URL/api/v1/health" > /dev/null; then
        log_error "Cannot connect to API at $API_URL"
        log_info "Make sure the stack is running: ./tl start"
        exit 1
    fi

    log_success "Prerequisites OK"
}

# Make API call with error handling
api_call() {
    local endpoint=$1
    local data=$2
    local description=$3

    log_info "$description"

    local response
    local http_code

    response=$(curl -s -w "\n%{http_code}" \
        -X POST \
        -H "Content-Type: application/json" \
        -d "$data" \
        "$API_URL$endpoint" 2>&1)

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" -eq 200 ]; then
        echo "$body" | jq .
        return 0
    else
        log_error "HTTP $http_code: $body"
        return 1
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --start-date=*)
            START_DATE="${1#*=}"
            shift
            ;;
        --end-date=*)
            END_DATE="${1#*=}"
            shift
            ;;
        --api-url=*)
            API_URL="${1#*=}"
            shift
            ;;
        --max-process=*)
            MAX_AUTO_PROCESS="${1#*=}"
            shift
            ;;
        --dry-run)
            DRY_RUN="true"
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

# Calculate lookback days
LOOKBACK_DAYS=$(days_between "$START_DATE" "$END_DATE")

# Main execution
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║   Deep JP City League Ingestion                            ║"
echo "║                                                            ║"
echo "║   Period: $START_DATE to $END_DATE ($LOOKBACK_DAYS days)      ║"
echo "║   API: $API_URL                                            ║"
if [ "$DRY_RUN" = "true" ]; then
    echo "║   Mode: DRY RUN (no database changes)                      ║"
fi
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

check_prerequisites

# Step 1: Sync card mappings
log_step "Syncing card mappings from Limitless"
if [ "$DRY_RUN" = "true" ]; then
    log_info "DRY RUN: Would sync card mappings"
else
    api_call "/api/v1/pipeline/sync-card-mappings" \
        '{"recent_only": false}' \
        "Syncing JP to EN card ID mappings"
fi

# Step 2: Monitor unreleased cards
log_step "Fetching unreleased cards from Limitless"
if [ "$DRY_RUN" = "true" ]; then
    log_info "DRY RUN: Would fetch unreleased cards"
else
    api_call "/api/v1/pipeline/monitor-card-reveals" \
        '{"dry_run": false}' \
        "Monitoring for new card reveals"
fi

# Step 3: Generate placeholder mappings
log_step "Generating placeholder card mappings"
log_info "Creating placeholder EN card IDs for unreleased JP cards"
log_info "Set code: POR (Perfect Order), Official: ME03"
if [ "$DRY_RUN" = "true" ]; then
    log_info "DRY RUN: Would generate placeholder mappings"
else
    # This will be handled by the enhanced discover-jp pipeline
    log_info "Placeholder generation integrated into tournament processing"
fi

# Step 4: Discover and process JP City Leagues
log_step "Discovering and processing JP City Leagues"
if [ "$DRY_RUN" = "true" ]; then
    log_info "DRY RUN: Would discover and process tournaments"
    log_info "  - Lookback: $LOOKBACK_DAYS days"
    log_info "  - Max auto-process: $MAX_AUTO_PROCESS"
else
    api_call "/api/v1/pipeline/discover-jp" \
        "{
            \"lookback_days\": $LOOKBACK_DAYS,
            \"auto_process\": $AUTO_PROCESS,
            \"max_auto_process\": $MAX_AUTO_PROCESS,
            \"fetch_decklists\": true,
            \"min_placements\": 8,
            \"max_placements\": 32,
            \"generate_placeholders\": true
        }" \
        "Discovering JP tournaments from $START_DATE"
fi

# Step 5: Compute meta snapshots
log_step "Computing daily meta snapshots"
if [ "$DRY_RUN" = "true" ]; then
    log_info "DRY RUN: Would compute meta snapshots"
else
    api_call "/api/v1/pipeline/compute-meta" \
        '{
            "regions": ["JP"],
            "formats": ["standard"],
            "best_of": [1],
            "lookback_days": 90
        }' \
        "Computing JP meta snapshots (BO1 format)"
fi

# Step 6: Verification
log_step "Verifying data completeness"
if [ "$DRY_RUN" = "true" ]; then
    log_info "DRY RUN: Skipping verification"
else
    log_info "Tournament count:"
    ./scripts/db-local.sh -c "SELECT COUNT(*) FROM tournaments WHERE region = 'JP' AND date >= '$START_DATE';"

    log_info "Decklists with data:"
    ./scripts/db-local.sh -c "SELECT COUNT(*) FROM tournament_placements p JOIN tournaments t ON p.tournament_id = t.id WHERE t.region = 'JP' AND t.date >= '$START_DATE' AND p.decklist IS NOT NULL;"

    log_info "Placeholder cards:"
    ./scripts/db-local.sh -c "SELECT COUNT(*) FROM placeholder_cards WHERE is_unreleased = true;"

    log_info "Meta snapshots:"
    ./scripts/db-local.sh -c "SELECT COUNT(*) FROM meta_snapshots WHERE region = 'JP';"
fi

echo ""
echo "════════════════════════════════════════════════════════════"
if [ "$DRY_RUN" = "true" ]; then
    echo -e "${YELLOW}DRY RUN COMPLETE${NC} - No changes made to database"
else
    echo -e "${GREEN}✅ INGESTION COMPLETE${NC}"
fi
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Next steps:"
echo "  • Explore data: ./scripts/db-local.sh"
echo "  • Run verification: ./scripts/verify-local.sh"
echo "  • Export data: ./scripts/export-data.sh"
echo "  • View analysis: open http://localhost:8888 (Jupyter)"
echo ""
