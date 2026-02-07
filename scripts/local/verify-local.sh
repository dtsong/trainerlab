#!/bin/bash
# TrainerLab Data Quality Verification Script (Local Docker Version)
# Usage: ./scripts/verify-local.sh [OPTIONS]
#
# Validates data quality across all API endpoints in local docker-compose environment.

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Default values
API_URL="http://localhost:8080"
GROUP=""
NO_START=false

# Counters
PASSED=0
FAILED=0
WARNED=0
TOTAL=0

usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Deep data quality verification across all API endpoints in local environment.

Options:
    --group=NAME    Run specific group (cards, sets, tournaments, meta, japan, format, frontend, comparison, forecast, techcards, pipeline)
    --api-url=URL   Override API URL (default: http://localhost:8080)
    --no-start      Skip auto-starting docker-compose services
    -h, --help      Show this help message

Note:
    By default, the script will auto-start docker-compose services if
    the API is not reachable. Use --no-start to disable this behavior.

Groups:
    cards           Card listing + search
    sets            Set listing + required fields
    tournaments     Tournament listing, JP filter, freshness
    meta            Meta snapshot shape, archetype shares, diversity index
    japan           JP meta, innovation, new archetypes
    format          Format config + rotation impact
    frontend        Exact fields that frontend hooks destructure
    comparison      Phase 3: Meta comparison (JP vs Global)
    forecast        Phase 3: Format forecast from JP divergence
    techcards       Phase 3: Tech card insights for archetypes
    pipeline        Pipeline health (scrape, meta, archetype)

Examples:
    $0                        # Run all groups
    $0 --group=meta           # Run only meta group
    $0 --api-url=http://api:8080  # Use internal docker network

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
}

ensure_services() {
    # Quick-check: if the API is already healthy, nothing to do
    if curl -sf "${API_URL}/api/v1/health" > /dev/null 2>&1; then
        log_info "API is already running at ${API_URL}"
        return 0
    fi

    # Services aren't up — if --no-start was passed, bail out
    if [ "$NO_START" = true ]; then
        echo -e "${RED}[FAIL]${NC} Services are not running at ${API_URL} and --no-start was specified"
        exit 1
    fi

    # Find docker compose command
    local compose_cmd=""
    if docker compose version > /dev/null 2>&1; then
        compose_cmd="docker compose"
    else
        echo -e "${RED}[FAIL]${NC} docker compose not found. Please install Docker Desktop."
        exit 1
    fi

    # Detect project root (docker-compose.yml location)
    local script_dir
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local project_root="${script_dir}/../.."
    if [ ! -f "${project_root}/docker-compose.yml" ]; then
        echo -e "${RED}[FAIL]${NC} docker-compose.yml not found at ${project_root}"
        exit 1
    fi

    log_info "Starting PostgreSQL..."
    (cd "$project_root" && $compose_cmd up -d db)

    # Poll the health endpoint with a 120s timeout
    local timeout=120
    local interval=5
    local elapsed=0

    log_info "Waiting for API to become healthy (timeout: ${timeout}s)..."
    while [ $elapsed -lt $timeout ]; do
        if curl -sf "${API_URL}/api/v1/health" > /dev/null 2>&1; then
            log_info "API is healthy after ${elapsed}s"
            return 0
        fi
        sleep $interval
        elapsed=$((elapsed + interval))
        echo -ne "\r  Waiting... ${elapsed}s / ${timeout}s"
    done

    echo ""
    echo -e "${RED}[FAIL]${NC} API did not become healthy within ${timeout}s"
    echo -e "${YELLOW}[HINT]${NC} Start the stack with: ./tl start"
    exit 1
}

# Fetch an endpoint and store response body + HTTP status
# Sets global: RESP_BODY, RESP_CODE
fetch() {
    local endpoint=$1
    local url="${API_URL}${endpoint}"

    local raw
    raw=$(curl -s -w "\n%{http_code}" "$url" 2>/dev/null)

    RESP_CODE=$(echo "$raw" | tail -n1)
    RESP_BODY=$(echo "$raw" | sed '$d')
}

# Check that the last fetch returned HTTP 200
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
            local has_fields
            has_fields=$(echo "$RESP_BODY" | jq '[.items[0] | has("id", "name", "supertype", "set_id")] | all')
            if [ "$has_fields" = "true" ]; then
                log_pass "Card fields: id, name, supertype, set_id present"
            else
                log_fail "Card fields: missing required fields"
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
            log_warn "Card search: 'Charizard' returned 0 results"
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

        local first
        first=$(echo "$RESP_BODY" | jq 'if type == "array" then .[0] elif .items then .items[0] else {} end')
        local has_fields
        has_fields=$(echo "$first" | jq 'has("id") and has("name") and has("series")')
        if [ "$has_fields" = "true" ]; then
            log_pass "Set fields: id, name, series present"
        else
            log_fail "Set fields: missing required fields"
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
            log_warn "Tournaments: total is 0 (may need to run ingestion)"
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
            log_warn "JP tournaments: none found (may need to run JP ingestion)"
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
        local has_breakdown
        has_breakdown=$(echo "$RESP_BODY" | jq 'has("archetype_breakdown")')
        local has_snapshot_date
        has_snapshot_date=$(echo "$RESP_BODY" | jq 'has("snapshot_date")')
        local has_diversity
        has_diversity=$(echo "$RESP_BODY" | jq 'has("diversity_index")')

        if [ "$has_breakdown" = "true" ] && [ "$has_snapshot_date" = "true" ] && [ "$has_diversity" = "true" ]; then
            log_pass "Meta fields: archetype_breakdown, snapshot_date, diversity_index present"
        else
            log_fail "Meta fields: missing required fields"
        fi

        # Archetype count
        local arch_count
        arch_count=$(echo "$RESP_BODY" | jq '.archetype_breakdown | length')
        if [ "$arch_count" -ge 3 ]; then
            log_pass "Archetypes: $arch_count in breakdown (>= 3)"
        else
            log_warn "Archetypes: only $arch_count in breakdown (may need to compute meta)"
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

        # Diversity index between 0 and 1
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
            log_warn "JP meta snapshot: missing archetype_breakdown"
        fi
    fi

    # 5b — Innovation
    fetch "/api/v1/japan/innovation"
    if require_200 "GET /api/v1/japan/innovation"; then
        local inno_count
        inno_count=$(echo "$RESP_BODY" | jq 'if type == "array" then length elif .items then (.items | length) else 0 end')
        if [ "$inno_count" -gt 0 ]; then
            log_pass "Innovation: $inno_count items"
        else
            log_warn "Innovation: empty response (may need to run JP adoption sync)"
        fi
    fi

    # 5c — New archetypes
    fetch "/api/v1/japan/archetypes/new"
    if require_200 "GET /api/v1/japan/archetypes/new"; then
        local new_count
        new_count=$(echo "$RESP_BODY" | jq 'if type == "array" then length elif .items then (.items | length) else 0 end')
        if [ "$new_count" -gt 0 ]; then
            log_pass "New JP archetypes: $new_count items"
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
            log_fail "Card frontend fields: missing expected fields"
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
}

# ─── Group 8: Comparison (Phase 3) ──────────────────────────────────────────

verify_comparison() {
    log_group "COMPARISON" "Meta comparison: JP vs Global (Phase 3)"

    # 8a — Basic comparison
    fetch "/api/v1/meta/compare?region_a=JP"
    if require_200 "GET /api/v1/meta/compare?region_a=JP"; then
        local has_regions
        has_regions=$(echo "$RESP_BODY" | jq 'has("region_a") and has("region_b") and has("comparisons") and has("region_a_confidence") and has("region_b_confidence")')
        if [ "$has_regions" = "true" ]; then
            log_pass "Comparison fields: region_a, region_b, comparisons, confidence present"
        else
            log_fail "Comparison fields: missing required fields"
        fi

        local region_a
        region_a=$(echo "$RESP_BODY" | jq -r '.region_a')
        if [ "$region_a" = "JP" ]; then
            log_pass "Region A: JP"
        else
            log_fail "Region A: expected JP, got $region_a"
        fi

        local comp_count
        comp_count=$(echo "$RESP_BODY" | jq '.comparisons | length')
        if [ "$comp_count" -gt 0 ]; then
            log_pass "Comparisons: $comp_count archetypes"
        else
            log_warn "Comparisons: empty (may need to compute meta)"
        fi

        # Validate comparison entry fields
        if [ "$comp_count" -gt 0 ]; then
            local has_entry_fields
            has_entry_fields=$(echo "$RESP_BODY" | jq '
                [.comparisons[0] | has("archetype", "region_a_share", "region_b_share", "divergence")] | all
            ')
            if [ "$has_entry_fields" = "true" ]; then
                log_pass "Comparison entry fields: archetype, shares, divergence present"
            else
                log_fail "Comparison entry fields: missing required fields"
            fi

            # Shares in 0.0–1.0
            local shares_valid
            shares_valid=$(echo "$RESP_BODY" | jq '
                [.comparisons[0].region_a_share, .comparisons[0].region_b_share] |
                all(. >= 0.0 and . <= 1.0)
            ')
            if [ "$shares_valid" = "true" ]; then
                log_pass "Share ranges: first entry shares in 0.0–1.0"
            else
                log_fail "Share ranges: shares outside 0.0–1.0"
            fi

            # Divergence = a_share - b_share (spot check)
            local div_check
            div_check=$(echo "$RESP_BODY" | jq '
                (.comparisons[0].region_a_share - .comparisons[0].region_b_share - .comparisons[0].divergence) | fabs < 0.001
            ')
            if [ "$div_check" = "true" ]; then
                log_pass "Divergence math: a_share - b_share matches divergence"
            else
                log_warn "Divergence math: first entry divergence may not match shares"
            fi
        fi

        # Confidence indicator fields
        local has_conf_fields
        has_conf_fields=$(echo "$RESP_BODY" | jq '
            [.region_a_confidence | has("sample_size", "data_freshness_days", "confidence")] | all
        ')
        if [ "$has_conf_fields" = "true" ]; then
            log_pass "Confidence fields: sample_size, data_freshness_days, confidence present"
        else
            log_fail "Confidence fields: missing required fields"
        fi

        local conf_level
        conf_level=$(echo "$RESP_BODY" | jq -r '.region_a_confidence.confidence')
        case "$conf_level" in
            high|medium|low)
                log_pass "Confidence level: $conf_level (valid)"
                ;;
            *)
                log_fail "Confidence level: '$conf_level' (expected high/medium/low)"
                ;;
        esac
    fi
}

# ─── Group 9: Forecast (Phase 3) ───────────────────────────────────────────

verify_forecast() {
    log_group "FORECAST" "Format forecast from JP divergence (Phase 3)"

    # 9a — Default forecast
    fetch "/api/v1/meta/forecast"
    if require_200 "GET /api/v1/meta/forecast"; then
        local has_fields
        has_fields=$(echo "$RESP_BODY" | jq 'has("forecast_archetypes") and has("jp_snapshot_date") and has("en_snapshot_date") and has("jp_sample_size")')
        if [ "$has_fields" = "true" ]; then
            log_pass "Forecast fields: forecast_archetypes, dates, sample_size present"
        else
            log_fail "Forecast fields: missing required fields"
        fi

        local entry_count
        entry_count=$(echo "$RESP_BODY" | jq '.forecast_archetypes | length')
        if [ "$entry_count" -gt 0 ]; then
            log_pass "Forecast entries: $entry_count archetypes"
        else
            log_warn "Forecast entries: empty (may need JP + Global meta)"
        fi

        # Validate entry fields
        if [ "$entry_count" -gt 0 ]; then
            local has_entry_fields
            has_entry_fields=$(echo "$RESP_BODY" | jq '
                [.forecast_archetypes[0] | has("archetype", "jp_share", "tier", "trend_direction", "confidence")] | all
            ')
            if [ "$has_entry_fields" = "true" ]; then
                log_pass "Forecast entry fields: archetype, jp_share, tier, trend, confidence"
            else
                log_fail "Forecast entry fields: missing required fields"
            fi

            # All jp_share >= 0.01 (1% threshold)
            local all_above_threshold
            all_above_threshold=$(echo "$RESP_BODY" | jq '
                [.forecast_archetypes[].jp_share] | all(. >= 0.01)
            ')
            if [ "$all_above_threshold" = "true" ]; then
                log_pass "Forecast threshold: all jp_share >= 1%"
            else
                log_fail "Forecast threshold: some jp_share below 1%"
            fi

            # trend_direction valid values
            local trends_valid
            trends_valid=$(echo "$RESP_BODY" | jq '
                [.forecast_archetypes[].trend_direction] |
                all(. == "up" or . == "down" or . == "stable" or . == null)
            ')
            if [ "$trends_valid" = "true" ]; then
                log_pass "Forecast trends: all directions valid (up/down/stable/null)"
            else
                log_fail "Forecast trends: invalid trend_direction value"
            fi
        fi
    fi

    # 9b — top_n=3 limits results
    fetch "/api/v1/meta/forecast?top_n=3"
    if require_200 "GET /api/v1/meta/forecast?top_n=3"; then
        local limited_count
        limited_count=$(echo "$RESP_BODY" | jq '.forecast_archetypes | length')
        if [ "$limited_count" -le 3 ]; then
            log_pass "Forecast top_n=3: returned $limited_count entries (<= 3)"
        else
            log_fail "Forecast top_n=3: returned $limited_count entries (expected <= 3)"
        fi
    fi
}

# ─── Group 10: Tech Cards (Phase 3) ────────────────────────────────────────

verify_techcards() {
    log_group "TECHCARDS" "Tech card insights for archetypes (Phase 3)"

    # Discover a real archetype name from comparison endpoint
    fetch "/api/v1/meta/compare?region_a=JP&top_n=1"
    if ! require_200 "GET /api/v1/meta/compare?top_n=1 (discover archetype)"; then
        log_warn "Tech cards: cannot discover archetype, skipping"
        return
    fi

    local archetype_name
    archetype_name=$(echo "$RESP_BODY" | jq -r '.comparisons[0].archetype // ""')
    if [ -z "$archetype_name" ]; then
        log_warn "Tech cards: no archetype found in comparison, skipping"
        return
    fi

    log_info "Discovered archetype: $archetype_name"

    # URL-encode the archetype name
    local encoded_name
    encoded_name=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$archetype_name'))" 2>/dev/null || echo "$archetype_name")

    fetch "/api/v1/meta/archetypes/${encoded_name}"
    if require_200 "GET /api/v1/meta/archetypes/${archetype_name}"; then
        local has_key_cards
        has_key_cards=$(echo "$RESP_BODY" | jq 'has("key_cards")')
        if [ "$has_key_cards" = "true" ]; then
            local card_count
            card_count=$(echo "$RESP_BODY" | jq '.key_cards | length')
            log_pass "Key cards: $card_count cards for $archetype_name"

            if [ "$card_count" -gt 0 ]; then
                local has_card_fields
                has_card_fields=$(echo "$RESP_BODY" | jq '
                    [.key_cards[0] | has("card_id", "inclusion_rate")] | all
                ')
                if [ "$has_card_fields" = "true" ]; then
                    log_pass "Key card fields: card_id, inclusion_rate present"
                else
                    log_fail "Key card fields: missing required fields"
                fi

                # inclusion_rate in 0–1
                local rate_valid
                rate_valid=$(echo "$RESP_BODY" | jq '
                    .key_cards[0].inclusion_rate >= 0 and .key_cards[0].inclusion_rate <= 1
                ')
                if [ "$rate_valid" = "true" ]; then
                    log_pass "Inclusion rate: in 0–1 range"
                else
                    log_fail "Inclusion rate: outside 0–1 range"
                fi
            fi
        else
            log_warn "Key cards: field not present (may need archetype detail endpoint)"
        fi
    fi
}

# ─── Group 11: Pipeline Health ───────────────────────────────────────────────

verify_pipeline() {
    log_group "PIPELINE" "Pipeline health check (scrape, meta, archetype)"

    fetch "/api/v1/health/pipeline"
    if require_200 "GET /api/v1/health/pipeline"; then
        local overall
        overall=$(echo "$RESP_BODY" | jq -r '.status')

        case "$overall" in
            healthy)
                log_pass "Pipeline status: healthy"
                ;;
            degraded)
                log_warn "Pipeline status: degraded"
                ;;
            *)
                log_fail "Pipeline status: $overall"
                ;;
        esac

        # Scrape health
        local scrape_status
        scrape_status=$(echo "$RESP_BODY" | jq -r '.scrape.status')
        case "$scrape_status" in
            ok) log_pass "Scrape: $scrape_status" ;;
            stale) log_warn "Scrape: $scrape_status" ;;
            *) log_fail "Scrape: $scrape_status" ;;
        esac

        # Meta health
        local meta_status
        meta_status=$(echo "$RESP_BODY" | jq -r '.meta.status')
        case "$meta_status" in
            ok) log_pass "Meta: $meta_status" ;;
            stale) log_warn "Meta: $meta_status" ;;
            *) log_fail "Meta: $meta_status" ;;
        esac

        # Archetype health
        local arch_status
        arch_status=$(echo "$RESP_BODY" | jq -r '.archetype.status')
        case "$arch_status" in
            ok) log_pass "Archetype: $arch_status" ;;
            degraded) log_warn "Archetype: $arch_status" ;;
            *) log_fail "Archetype: $arch_status" ;;
        esac
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
        --no-start)
            NO_START=true
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
echo "║   TrainerLab Data Quality Verification (Local)             ║"
echo "║   API: $API_URL"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

check_prerequisites
ensure_services

run_group() {
    case $1 in
        cards)       verify_cards ;;
        sets)        verify_sets ;;
        tournaments) verify_tournaments ;;
        meta)        verify_meta ;;
        japan)       verify_japan ;;
        format)      verify_format ;;
        frontend)    verify_frontend ;;
        comparison)  verify_comparison ;;
        forecast)    verify_forecast ;;
        techcards)   verify_techcards ;;
        pipeline)    verify_pipeline ;;
        *)
            echo -e "${RED}[FAIL]${NC} Unknown group: $1"
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
    verify_comparison
    verify_forecast
    verify_techcards
    verify_pipeline
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
