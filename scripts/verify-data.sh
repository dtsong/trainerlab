#!/bin/bash
set -euo pipefail

# TrainerLab Data Quality Verification Script
# Usage: ./scripts/verify-data.sh [OPTIONS]
#
# Deep data quality verification across all API endpoints.
# Validates response shapes, field presence, data ranges,
# and cross-entity consistency.

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
GROUP=""
API_URL=""
LOCAL=false
TOKEN=""

# Counters
PASSED=0
FAILED=0
WARNED=0
TOTAL=0

usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Deep data quality verification across all API endpoints. Validates response
shapes, field presence, data ranges, and cross-entity consistency.

Options:
    --group=NAME    Run specific group (cards, sets, tournaments, meta, japan, format, frontend)
    --api-url=URL   Override API URL (default: auto-detect from Cloud Run)
    --local         Use localhost:8000 (no auth)
    -h, --help      Show this help message

Groups:
    cards           Card listing + search
    sets            Set listing + required fields
    tournaments     Tournament listing, JP filter, freshness
    meta            Meta snapshot shape, archetype shares, diversity index
    japan           JP meta, innovation, new archetypes
    format          Format config + rotation impact
    frontend        Exact fields that frontend hooks destructure

Examples:
    $0                        # Run all groups against production
    $0 --local                # Run all groups against local dev
    $0 --group=meta           # Run only meta group against production
    $0 --group=meta --local   # Run only meta group against local dev

EOF
    exit 0
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    PASSED=$((PASSED + 1))
    TOTAL=$((TOTAL + 1))
}

log_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    FAILED=$((FAILED + 1))
    TOTAL=$((TOTAL + 1))
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    WARNED=$((WARNED + 1))
    TOTAL=$((TOTAL + 1))
}

log_group() {
    echo ""
    echo -e "${BOLD}[$1] $2${NC}"
    echo "────────────────────────────────────────"
}

check_prerequisites() {
    if ! command -v jq &> /dev/null; then
        echo -e "${RED}[FAIL]${NC} jq not found. Please install it first (brew install jq)"
        exit 1
    fi

    if [ "$LOCAL" = false ] && [ -z "$API_URL" ]; then
        if ! command -v gcloud &> /dev/null; then
            echo -e "${RED}[FAIL]${NC} gcloud CLI not found. Use --local or install gcloud."
            exit 1
        fi
    fi
}

setup_api() {
    if [ "$LOCAL" = true ]; then
        API_URL="http://localhost:8000"
        TOKEN=""
        log_info "Target: $API_URL (local, no auth)"
        return
    fi

    if [ -z "$API_URL" ]; then
        log_info "Auto-detecting Cloud Run URL..."
        API_URL=$(gcloud run services describe "$SERVICE_NAME" \
            --region="$REGION" \
            --project="$PROJECT_ID" \
            --format='value(status.url)' 2>/dev/null || echo "")

        if [ -z "$API_URL" ]; then
            echo -e "${RED}[FAIL]${NC} Failed to get service URL. Use --api-url or --local."
            exit 1
        fi
    fi

    TOKEN=$(gcloud auth print-identity-token 2>/dev/null || echo "")
    if [ -z "$TOKEN" ]; then
        echo -e "${RED}[FAIL]${NC} Failed to get identity token. Run: gcloud auth login"
        exit 1
    fi

    log_info "Target: $API_URL (authenticated)"
}

# ─── HTTP Helper ──────────────────────────────────────────────────────────────

# Fetch an endpoint and store response body + HTTP status.
# Sets global: RESP_BODY, RESP_CODE
fetch() {
    local endpoint=$1
    local url="${API_URL}${endpoint}"

    local raw
    if [ -n "$TOKEN" ]; then
        raw=$(curl -s -w "\n%{http_code}" \
            -H "Authorization: Bearer $TOKEN" \
            "$url" 2>/dev/null)
    else
        raw=$(curl -s -w "\n%{http_code}" "$url" 2>/dev/null)
    fi

    RESP_CODE=$(echo "$raw" | tail -n1)
    RESP_BODY=$(echo "$raw" | sed '$d')
}

# Check that the last fetch returned HTTP 200. Logs FAIL and returns 1 otherwise.
require_200() {
    local label=$1
    if [ "$RESP_CODE" != "200" ]; then
        log_fail "$label — HTTP $RESP_CODE"
        return 1
    fi
    return 0
}

# ─── Group 1: Cards ──────────────────────────────────────────────────────────

verify_cards() {
    log_group "CARDS" "Card listing and search"

    # 1a — Paginated card list
    fetch "/api/v1/cards?limit=5"
    if require_200 "GET /api/v1/cards?limit=5"; then
        local total
        total=$(echo "$RESP_BODY" | jq -r '.total // 0')
        if [ "$total" -gt 0 ]; then
            log_pass "Card list: $total cards total"
        else
            log_fail "Card list: total is 0"
        fi

        local items_count
        items_count=$(echo "$RESP_BODY" | jq '.items | length')
        if [ "$items_count" -gt 0 ]; then
            # Check required fields on first item
            local has_fields
            has_fields=$(echo "$RESP_BODY" | jq '[.items[0] | has("id", "name", "supertype", "set_id")] | all')
            if [ "$has_fields" = "true" ]; then
                log_pass "Card fields: id, name, supertype, set_id present"
            else
                log_fail "Card fields: missing required fields (id, name, supertype, set_id)"
            fi
        else
            log_fail "Card list: items array is empty"
        fi
    fi

    # 1b — Fuzzy search
    fetch "/api/v1/cards/search?q=Charizard&limit=3"
    if require_200 "GET /api/v1/cards/search?q=Charizard&limit=3"; then
        local search_count
        search_count=$(echo "$RESP_BODY" | jq '.items | length // 0')
        if [ "$search_count" -gt 0 ]; then
            log_pass "Card search: 'Charizard' returned $search_count results"
        else
            log_fail "Card search: 'Charizard' returned 0 results"
        fi
    fi
}

# ─── Group 2: Sets ───────────────────────────────────────────────────────────

verify_sets() {
    log_group "SETS" "Set listing and required fields"

    fetch "/api/v1/sets"
    if require_200 "GET /api/v1/sets"; then
        local count
        count=$(echo "$RESP_BODY" | jq 'if type == "array" then length elif .items then (.items | length) else 0 end')
        if [ "$count" -gt 0 ]; then
            log_pass "Sets: $count sets found"
        else
            log_fail "Sets: empty response"
            return
        fi

        # Check required fields on first set
        local first
        first=$(echo "$RESP_BODY" | jq 'if type == "array" then .[0] elif .items then .items[0] else {} end')
        local has_fields
        has_fields=$(echo "$first" | jq 'has("id") and has("name") and has("series")')
        if [ "$has_fields" = "true" ]; then
            log_pass "Set fields: id, name, series present"
        else
            log_fail "Set fields: missing required fields (id, name, series)"
        fi
    fi
}

# ─── Group 3: Tournaments ────────────────────────────────────────────────────

verify_tournaments() {
    log_group "TOURNAMENTS" "Tournament listing, JP filter, freshness"

    # 3a — Paginated list
    fetch "/api/v1/tournaments?limit=10"
    if require_200 "GET /api/v1/tournaments?limit=10"; then
        local total
        total=$(echo "$RESP_BODY" | jq -r '.total // 0')
        if [ "$total" -gt 0 ]; then
            log_pass "Tournaments: $total total"
        else
            log_fail "Tournaments: total is 0"
        fi

        local items_count
        items_count=$(echo "$RESP_BODY" | jq '.items | length')
        if [ "$items_count" -gt 0 ]; then
            local has_fields
            has_fields=$(echo "$RESP_BODY" | jq '[.items[0] | has("id", "name", "date", "region")] | all')
            if [ "$has_fields" = "true" ]; then
                log_pass "Tournament fields: id, name, date, region present"
            else
                log_fail "Tournament fields: missing required fields"
            fi
        fi
    fi

    # 3b — JP filter
    fetch "/api/v1/tournaments?region=JP&limit=5"
    if require_200 "GET /api/v1/tournaments?region=JP&limit=5"; then
        local jp_total
        jp_total=$(echo "$RESP_BODY" | jq -r '.total // 0')
        if [ "$jp_total" -gt 0 ]; then
            log_pass "JP tournaments: $jp_total found"
        else
            log_fail "JP tournaments: none found"
        fi
    fi

    # 3c — Freshness: at least 1 tournament from last 14 days
    fetch "/api/v1/tournaments?limit=1"
    if require_200 "GET /api/v1/tournaments?limit=1 (freshness)"; then
        local latest_date
        latest_date=$(echo "$RESP_BODY" | jq -r '.items[0].date // ""')
        if [ -n "$latest_date" ]; then
            local cutoff
            cutoff=$(date -v-14d +%Y-%m-%d 2>/dev/null || date -d "14 days ago" +%Y-%m-%d 2>/dev/null || echo "")
            if [ -n "$cutoff" ] && [[ "$latest_date" > "$cutoff" || "$latest_date" == "$cutoff" ]]; then
                log_pass "Freshness: latest tournament is $latest_date (within 14 days)"
            else
                log_warn "Freshness: latest tournament is $latest_date (older than 14 days)"
            fi
        else
            log_warn "Freshness: could not determine latest tournament date"
        fi
    fi
}

# ─── Group 4: Meta Snapshots ─────────────────────────────────────────────────

verify_meta() {
    log_group "META" "Meta snapshot shape, archetype shares, diversity"

    # 4a — Current meta snapshot
    fetch "/api/v1/meta/current"
    if require_200 "GET /api/v1/meta/current"; then
        # Required top-level fields
        local has_breakdown
        has_breakdown=$(echo "$RESP_BODY" | jq 'has("archetype_breakdown")')
        local has_snapshot_date
        has_snapshot_date=$(echo "$RESP_BODY" | jq 'has("snapshot_date")')
        local has_diversity
        has_diversity=$(echo "$RESP_BODY" | jq 'has("diversity_index")')

        if [ "$has_breakdown" = "true" ] && [ "$has_snapshot_date" = "true" ] && [ "$has_diversity" = "true" ]; then
            log_pass "Meta fields: archetype_breakdown, snapshot_date, diversity_index present"
        else
            log_fail "Meta fields: missing one of archetype_breakdown, snapshot_date, diversity_index"
        fi

        # Archetype count
        local arch_count
        arch_count=$(echo "$RESP_BODY" | jq '.archetype_breakdown | length')
        if [ "$arch_count" -ge 3 ]; then
            log_pass "Archetypes: $arch_count in breakdown (>= 3)"
        else
            log_fail "Archetypes: only $arch_count in breakdown (expected >= 3)"
        fi

        # Shares sum to ~1.0
        local share_sum
        share_sum=$(echo "$RESP_BODY" | jq '[.archetype_breakdown[].share] | add // 0')
        local in_range
        in_range=$(echo "$share_sum" | jq '. >= 0.95 and . <= 1.05')
        if [ "$in_range" = "true" ]; then
            log_pass "Share sum: $share_sum (within 0.95–1.05)"
        else
            log_fail "Share sum: $share_sum (outside 0.95–1.05)"
        fi

        # Diversity index between 0 and 1 (nullable — null means not yet computed)
        local diversity_null
        diversity_null=$(echo "$RESP_BODY" | jq '.diversity_index == null')
        if [ "$diversity_null" = "true" ]; then
            log_warn "Diversity index: null (not yet computed)"
        else
            local diversity
            diversity=$(echo "$RESP_BODY" | jq '.diversity_index')
            local div_ok
            div_ok=$(echo "$diversity" | jq '. >= 0 and . <= 1')
            if [ "$div_ok" = "true" ]; then
                log_pass "Diversity index: $diversity (in 0–1)"
            else
                log_fail "Diversity index: $diversity (outside 0–1)"
            fi
        fi

        # Tier assignments
        local has_tiers
        has_tiers=$(echo "$RESP_BODY" | jq 'has("tier_assignments") and .tier_assignments != null and (.tier_assignments | length) > 0')
        if [ "$has_tiers" = "true" ]; then
            local tier_count
            tier_count=$(echo "$RESP_BODY" | jq '.tier_assignments | length')
            log_pass "Tier assignments: $tier_count present"
        else
            log_warn "Tier assignments: missing or empty"
        fi
    fi

    # 4b — Archetypes list
    fetch "/api/v1/meta/archetypes"
    if require_200 "GET /api/v1/meta/archetypes"; then
        local arch_list_len
        arch_list_len=$(echo "$RESP_BODY" | jq 'if type == "array" then length elif .items then (.items | length) else 0 end')
        if [ "$arch_list_len" -gt 0 ]; then
            log_pass "Archetype list: $arch_list_len archetypes"
        else
            log_fail "Archetype list: empty"
        fi
    fi
}

# ─── Group 5: Japan Intelligence ─────────────────────────────────────────────

verify_japan() {
    log_group "JAPAN" "JP meta, innovation, new archetypes"

    # 5a — JP meta snapshot
    fetch "/api/v1/meta/current?region=JP&best_of=1"
    if require_200 "GET /api/v1/meta/current?region=JP&best_of=1"; then
        local has_breakdown
        has_breakdown=$(echo "$RESP_BODY" | jq 'has("archetype_breakdown")')
        if [ "$has_breakdown" = "true" ]; then
            log_pass "JP meta snapshot: archetype_breakdown present"
        else
            log_fail "JP meta snapshot: missing archetype_breakdown"
        fi
    fi

    # 5b — Innovation
    fetch "/api/v1/japan/innovation"
    if require_200 "GET /api/v1/japan/innovation"; then
        local inno_count
        inno_count=$(echo "$RESP_BODY" | jq 'if type == "array" then length elif .items then (.items | length) else 0 end')
        if [ "$inno_count" -gt 0 ]; then
            log_pass "Innovation: $inno_count items"

            # Check adoption_rate in 0–1
            local first_item
            first_item=$(echo "$RESP_BODY" | jq 'if type == "array" then .[0] elif .items then .items[0] else {} end')
            local rate
            rate=$(echo "$first_item" | jq '.adoption_rate // -1')
            local rate_ok
            rate_ok=$(echo "$rate" | jq '. >= 0 and . <= 1')
            if [ "$rate_ok" = "true" ]; then
                log_pass "Innovation adoption_rate: $rate (in 0–1)"
            else
                log_fail "Innovation adoption_rate: $rate (outside 0–1)"
            fi
        else
            log_warn "Innovation: empty response"
        fi
    fi

    # 5c — New archetypes
    fetch "/api/v1/japan/archetypes/new"
    if require_200 "GET /api/v1/japan/archetypes/new"; then
        local new_count
        new_count=$(echo "$RESP_BODY" | jq 'if type == "array" then length elif .items then (.items | length) else 0 end')
        if [ "$new_count" -gt 0 ]; then
            log_pass "New JP archetypes: $new_count items"

            local first_item
            first_item=$(echo "$RESP_BODY" | jq 'if type == "array" then .[0] elif .items then .items[0] else {} end')
            local share
            share=$(echo "$first_item" | jq '.jp_meta_share // -1')
            local share_ok
            share_ok=$(echo "$share" | jq '. >= 0 and . <= 1')
            if [ "$share_ok" = "true" ]; then
                log_pass "JP meta share: $share (in 0–1)"
            else
                log_fail "JP meta share: $share (outside 0–1)"
            fi
        else
            log_warn "New JP archetypes: empty response"
        fi
    fi
}

# ─── Group 6: Format & Rotation ──────────────────────────────────────────────

verify_format() {
    log_group "FORMAT" "Format config and rotation impact"

    # 6a — Current format
    fetch "/api/v1/format/current"
    if require_200 "GET /api/v1/format/current"; then
        log_pass "Format config: returned successfully"
    fi

    # 6b — Rotation impact (requires transition param from format config)
    local transition
    transition=$(echo "$RESP_BODY" | jq -r '.transition // empty' 2>/dev/null || echo "")
    if [ -n "$transition" ]; then
        fetch "/api/v1/rotation/impact?transition=${transition}"
        if [ "$RESP_CODE" = "200" ]; then
            log_pass "Rotation impact: returned successfully (transition=$transition)"
        elif [ "$RESP_CODE" = "404" ]; then
            log_warn "Rotation impact: 404 (no data for transition=$transition)"
        else
            log_fail "Rotation impact: HTTP $RESP_CODE (transition=$transition)"
        fi
    else
        log_warn "Rotation impact: skipped (no transition in format config)"
    fi
}

# ─── Group 7: Frontend Smoke ─────────────────────────────────────────────────

verify_frontend() {
    log_group "FRONTEND" "Exact fields that frontend hooks destructure"

    # 7a — Card fields for frontend
    fetch "/api/v1/cards?limit=1"
    if require_200 "GET /api/v1/cards?limit=1 (frontend fields)"; then
        local has_fe_fields
        has_fe_fields=$(echo "$RESP_BODY" | jq '[.items[0] | has("id", "name", "image_small", "set_id")] | all')
        if [ "$has_fe_fields" = "true" ]; then
            log_pass "Card frontend fields: id, name, image_small, set_id"
        else
            log_fail "Card frontend fields: missing one of id, name, image_small, set_id"
        fi
    fi

    # 7b — Meta fields for frontend
    fetch "/api/v1/meta/current"
    if require_200 "GET /api/v1/meta/current (frontend fields)"; then
        local has_snapshot
        has_snapshot=$(echo "$RESP_BODY" | jq 'has("snapshot_date") and has("diversity_index")')
        local has_arch_fields
        has_arch_fields=$(echo "$RESP_BODY" | jq '
            if (.archetype_breakdown | length) > 0
            then (.archetype_breakdown[0] | has("name") and has("share"))
            else false
            end
        ')
        if [ "$has_snapshot" = "true" ] && [ "$has_arch_fields" = "true" ]; then
            log_pass "Meta frontend fields: snapshot_date, diversity_index, archetype_breakdown[].name, .share"
        else
            log_fail "Meta frontend fields: missing expected fields"
        fi
    fi

    # 7c — Tournament fields for frontend
    fetch "/api/v1/tournaments?limit=1"
    if require_200 "GET /api/v1/tournaments?limit=1 (frontend fields)"; then
        local has_tourney_fields
        has_tourney_fields=$(echo "$RESP_BODY" | jq '[.items[0] | has("id", "name", "date", "region", "top_placements")] | all')
        if [ "$has_tourney_fields" = "true" ]; then
            log_pass "Tournament frontend fields: id, name, date, region, top_placements"
        else
            log_fail "Tournament frontend fields: missing one of id, name, date, region, top_placements"
        fi
    fi
}

# ─── Argument Parsing ────────────────────────────────────────────────────────

while [[ $# -gt 0 ]]; do
    case $1 in
        --group=*)
            GROUP="${1#*=}"
            shift
            ;;
        --api-url=*)
            API_URL="${1#*=}"
            shift
            ;;
        --local)
            LOCAL=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo -e "${RED}[FAIL]${NC} Unknown option: $1"
            usage
            ;;
    esac
done

# ─── Main ────────────────────────────────────────────────────────────────────

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║   TrainerLab Data Quality Verification                     ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

check_prerequisites
setup_api

run_group() {
    case $1 in
        cards)       verify_cards ;;
        sets)        verify_sets ;;
        tournaments) verify_tournaments ;;
        meta)        verify_meta ;;
        japan)       verify_japan ;;
        format)      verify_format ;;
        frontend)    verify_frontend ;;
        *)
            echo -e "${RED}[FAIL]${NC} Unknown group: $1 (valid: cards, sets, tournaments, meta, japan, format, frontend)"
            exit 1
            ;;
    esac
}

if [ -n "$GROUP" ]; then
    run_group "$GROUP"
else
    verify_cards
    verify_sets
    verify_tournaments
    verify_meta
    verify_japan
    verify_format
    verify_frontend
fi

# ─── Summary ─────────────────────────────────────────────────────────────────

echo ""
echo "════════════════════════════════════════════════════════════"
echo -e "  Results: ${GREEN}${PASSED} passed${NC}, ${RED}${FAILED} failed${NC}, ${YELLOW}${WARNED} warned${NC} (${TOTAL} total)"
echo "════════════════════════════════════════════════════════════"
echo ""

if [ "$FAILED" -gt 0 ]; then
    exit 1
fi
