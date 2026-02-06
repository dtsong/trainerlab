#!/bin/bash
# TrainerLab Phase 3 Deep Validation Script
# Usage: ./scripts/verify-phase3.sh [OPTIONS]
#
# Validates Phase 3 features: meta comparison, format forecast, and tech card insights.
# Tests data quality, calculation accuracy, confidence thresholds, and frontend contracts.

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Default values
API_URL="http://localhost:8080"
VERBOSE=false

# Counters
PASSED=0
FAILED=0
WARNED=0
TOTAL=0

usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Deep validation for Phase 3: meta comparison, format forecast, and tech card insights.

Options:
    --api-url=URL   Override API URL (default: http://localhost:8080)
    --verbose       Show response bodies for debugging
    -h, --help      Show this help message

Examples:
    $0                                    # Run against local API
    $0 --api-url=https://api.example.com  # Run against production
    $0 --verbose                          # Show all response data

Validation Groups:
    1. Comparison Data Quality      Divergence math, tier-share alignment, sprite URLs
    2. Lag Analysis                 Lag parameter handling and lagged_comparisons
    3. Forecast Logic               JP share threshold, sorting, trend directions
    4. Confidence Thresholds        Sample size and freshness validation
    5. Frontend Contract            Field presence and types for hooks
    6. Error Handling               Invalid inputs, edge cases
    7. Tech Cards                   Archetype key cards endpoint

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
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}[FAIL]${NC} python3 not found. Required for URL encoding."
        exit 1
    fi
}

# Fetch an endpoint and store response body + HTTP status
# Sets global: RESP_BODY, RESP_CODE
fetch() {
    local endpoint=$1
    local url="${API_URL}${endpoint}"

    if [ "$VERBOSE" = true ]; then
        log_info "Fetching: $url"
    fi

    local raw
    raw=$(curl -s -w "\n%{http_code}" "$url" 2>/dev/null)

    RESP_CODE=$(echo "$raw" | tail -n1)
    RESP_BODY=$(echo "$raw" | sed '$d')

    if [ "$VERBOSE" = true ]; then
        echo -e "${BLUE}Response ($RESP_CODE):${NC}"
        echo "$RESP_BODY" | jq '.' 2>/dev/null || echo "$RESP_BODY"
        echo ""
    fi
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

# Check sprite URL with HEAD request
check_sprite_url() {
    local url=$1
    local status
    status=$(curl -s -o /dev/null -w "%{http_code}" --head "$url" 2>/dev/null)
    if [ "$status" = "200" ]; then
        return 0
    else
        return 1
    fi
}

# ─── Group 1: Comparison Data Quality ────────────────────────────────────────

verify_comparison_quality() {
    log_group "1" "Comparison Data Quality"

    fetch "/api/v1/meta/compare?region_a=JP"
    if ! require_200 "GET /api/v1/meta/compare?region_a=JP"; then
        log_fail "Comparison endpoint: unavailable, skipping quality checks"
        return
    fi

    # Check required top-level fields
    local has_top_fields
    has_top_fields=$(echo "$RESP_BODY" | jq 'has("region_a") and has("region_b") and has("comparisons") and has("region_a_confidence") and has("region_b_confidence")')
    if [ "$has_top_fields" = "true" ]; then
        log_pass "Top-level fields: region_a, region_b, comparisons, confidence indicators present"
    else
        log_fail "Top-level fields: missing required fields"
        return
    fi

    local comp_count
    comp_count=$(echo "$RESP_BODY" | jq '.comparisons | length')

    if [ "$comp_count" -eq 0 ]; then
        log_warn "Comparisons array empty (may need to compute meta snapshots)"
        return
    fi

    log_info "Found $comp_count comparison entries"

    # 1a — Divergence math check (a_share - b_share = divergence)
    local divergence_errors
    divergence_errors=$(echo "$RESP_BODY" | jq '[
        .comparisons[] |
        select((.region_a_share - .region_b_share - .divergence) | fabs > 0.001)
    ] | length')

    if [ "$divergence_errors" -eq 0 ]; then
        log_pass "Divergence math: all entries match (a_share - b_share = divergence)"
    else
        log_fail "Divergence math: $divergence_errors entries have incorrect divergence calculation"
    fi

    # 1b — Tier-share alignment check
    # Tier S: >15%, A: 8-15%, B: 3-8%, C: 1-3%
    local tier_mismatches
    tier_mismatches=$(echo "$RESP_BODY" | jq '[
        .comparisons[] |
        select(
            (.region_a_tier == "S" and .region_a_share <= 0.15) or
            (.region_a_tier == "A" and (.region_a_share < 0.08 or .region_a_share > 0.15)) or
            (.region_a_tier == "B" and (.region_a_share < 0.03 or .region_a_share > 0.08)) or
            (.region_a_tier == "C" and (.region_a_share < 0.01 or .region_a_share > 0.03))
        )
    ] | length')

    if [ "$tier_mismatches" -eq 0 ]; then
        log_pass "Tier-share alignment: all region_a tiers match share thresholds"
    else
        log_fail "Tier-share alignment: $tier_mismatches entries have mismatched tier/share"
    fi

    # Check region_b tiers too
    tier_mismatches=$(echo "$RESP_BODY" | jq '[
        .comparisons[] |
        select(.region_b_tier != null) |
        select(
            (.region_b_tier == "S" and .region_b_share <= 0.15) or
            (.region_b_tier == "A" and (.region_b_share < 0.08 or .region_b_share > 0.15)) or
            (.region_b_tier == "B" and (.region_b_share < 0.03 or .region_b_share > 0.08)) or
            (.region_b_tier == "C" and (.region_b_share < 0.01 or .region_b_share > 0.03))
        )
    ] | length')

    if [ "$tier_mismatches" -eq 0 ]; then
        log_pass "Tier-share alignment: all region_b tiers match share thresholds"
    else
        log_fail "Tier-share alignment: $tier_mismatches region_b entries have mismatched tier/share"
    fi

    # 1c — Sprite URL spot-check (first 3 URLs)
    local first_entry_sprites
    first_entry_sprites=$(echo "$RESP_BODY" | jq -r '.comparisons[0].sprite_urls[]? // empty' | head -n 3)

    if [ -z "$first_entry_sprites" ]; then
        log_warn "Sprite URLs: no sprites in first entry (may be expected)"
    else
        local sprite_check_count=0
        local sprite_success_count=0

        while IFS= read -r sprite_url; do
            if [ -n "$sprite_url" ]; then
                sprite_check_count=$((sprite_check_count + 1))
                if check_sprite_url "$sprite_url"; then
                    sprite_success_count=$((sprite_success_count + 1))
                fi
            fi
        done <<< "$first_entry_sprites"

        if [ "$sprite_check_count" -gt 0 ]; then
            if [ "$sprite_success_count" -eq "$sprite_check_count" ]; then
                log_pass "Sprite URLs: $sprite_success_count/$sprite_check_count URLs reachable (HTTP 200)"
            elif [ "$sprite_success_count" -gt 0 ]; then
                log_warn "Sprite URLs: $sprite_success_count/$sprite_check_count URLs reachable"
            else
                log_fail "Sprite URLs: 0/$sprite_check_count URLs reachable"
            fi
        fi
    fi

    # 1d — Share value ranges (0.0-1.0)
    local invalid_shares
    invalid_shares=$(echo "$RESP_BODY" | jq '[
        .comparisons[] |
        select(.region_a_share < 0 or .region_a_share > 1 or .region_b_share < 0 or .region_b_share > 1)
    ] | length')

    if [ "$invalid_shares" -eq 0 ]; then
        log_pass "Share ranges: all shares in 0.0-1.0 range"
    else
        log_fail "Share ranges: $invalid_shares entries have shares outside 0.0-1.0"
    fi
}

# ─── Group 2: Lag Analysis ───────────────────────────────────────────────────

verify_lag_analysis() {
    log_group "2" "Lag Analysis"

    # 2a — Without lag_days parameter
    fetch "/api/v1/meta/compare?region_a=JP"
    if ! require_200 "GET /api/v1/meta/compare?region_a=JP (no lag)"; then
        return
    fi

    local has_lag_field
    has_lag_field=$(echo "$RESP_BODY" | jq 'has("lag_analysis")')
    local lag_is_null
    lag_is_null=$(echo "$RESP_BODY" | jq '.lag_analysis == null')

    if [ "$has_lag_field" = "true" ]; then
        if [ "$lag_is_null" = "true" ]; then
            log_pass "Lag analysis: null when lag_days not specified"
        else
            log_warn "Lag analysis: present without lag_days parameter"
        fi
    else
        log_warn "Lag analysis: field not present (may be by design)"
    fi

    # 2b — With lag_days=14 parameter
    fetch "/api/v1/meta/compare?region_a=JP&lag_days=14"
    if ! require_200 "GET /api/v1/meta/compare?region_a=JP&lag_days=14"; then
        return
    fi

    local lag_populated
    lag_populated=$(echo "$RESP_BODY" | jq '.lag_analysis != null')
    if [ "$lag_populated" = "true" ]; then
        log_pass "Lag analysis: populated when lag_days=14"
    else
        log_fail "Lag analysis: null despite lag_days=14 parameter"
        return
    fi

    # Check lag_analysis structure
    local has_lag_fields
    has_lag_fields=$(echo "$RESP_BODY" | jq '
        .lag_analysis | has("lag_days") and has("jp_snapshot_date") and has("en_snapshot_date") and has("lagged_comparisons")
    ')

    if [ "$has_lag_fields" = "true" ]; then
        log_pass "Lag analysis fields: lag_days, dates, lagged_comparisons present"
    else
        log_fail "Lag analysis fields: missing required fields"
        return
    fi

    local lag_days_value
    lag_days_value=$(echo "$RESP_BODY" | jq '.lag_analysis.lag_days')
    if [ "$lag_days_value" -eq 14 ]; then
        log_pass "Lag days value: 14 (matches parameter)"
    else
        log_fail "Lag days value: $lag_days_value (expected 14)"
    fi

    local lagged_comp_count
    lagged_comp_count=$(echo "$RESP_BODY" | jq '.lag_analysis.lagged_comparisons | length')
    if [ "$lagged_comp_count" -gt 0 ]; then
        log_pass "Lagged comparisons: $lagged_comp_count entries"
    else
        log_warn "Lagged comparisons: empty (may need historical data)"
    fi
}

# ─── Group 3: Forecast Logic ─────────────────────────────────────────────────

verify_forecast_logic() {
    log_group "3" "Forecast Logic"

    fetch "/api/v1/meta/forecast"
    if ! require_200 "GET /api/v1/meta/forecast"; then
        log_fail "Forecast endpoint: unavailable, skipping logic checks"
        return
    fi

    # Check required fields
    local has_fields
    has_fields=$(echo "$RESP_BODY" | jq 'has("forecast_archetypes") and has("jp_snapshot_date") and has("en_snapshot_date") and has("jp_sample_size")')
    if [ "$has_fields" = "true" ]; then
        log_pass "Forecast fields: forecast_archetypes, dates, sample_size present"
    else
        log_fail "Forecast fields: missing required fields"
        return
    fi

    local entry_count
    entry_count=$(echo "$RESP_BODY" | jq '.forecast_archetypes | length')

    if [ "$entry_count" -eq 0 ]; then
        log_warn "Forecast entries: empty (may need JP + Global meta computed)"
        return
    fi

    log_info "Found $entry_count forecast entries"

    # 3a — All entries have jp_share >= 0.01 (1% threshold)
    local below_threshold
    below_threshold=$(echo "$RESP_BODY" | jq '[
        .forecast_archetypes[] |
        select(.jp_share < 0.01)
    ] | length')

    if [ "$below_threshold" -eq 0 ]; then
        log_pass "JP share threshold: all entries >= 1%"
    else
        log_fail "JP share threshold: $below_threshold entries below 1%"
    fi

    # 3b — Sorted by jp_share descending
    local is_sorted
    is_sorted=$(echo "$RESP_BODY" | jq '
        [.forecast_archetypes[:-1], .forecast_archetypes[1:]] |
        transpose |
        all(.[0].jp_share >= .[1].jp_share)
    ')

    if [ "$is_sorted" = "true" ]; then
        log_pass "Forecast sorting: entries sorted by jp_share descending"
    else
        log_fail "Forecast sorting: entries not properly sorted"
    fi

    # 3c — trend_direction values are valid (up/down/stable/null)
    local invalid_trends
    invalid_trends=$(echo "$RESP_BODY" | jq '[
        .forecast_archetypes[].trend_direction |
        select(. != "up" and . != "down" and . != "stable" and . != null)
    ] | length')

    if [ "$invalid_trends" -eq 0 ]; then
        log_pass "Trend directions: all values valid (up/down/stable/null)"
    else
        log_fail "Trend directions: $invalid_trends entries have invalid values"
    fi

    # 3d — Tier values are valid (S/A/B/C/null)
    local invalid_tiers
    invalid_tiers=$(echo "$RESP_BODY" | jq '[
        .forecast_archetypes[].tier |
        select(. != "S" and . != "A" and . != "B" and . != "C" and . != null)
    ] | length')

    if [ "$invalid_tiers" -eq 0 ]; then
        log_pass "Tier values: all values valid (S/A/B/C/null)"
    else
        log_fail "Tier values: $invalid_tiers entries have invalid tiers"
    fi

    # 3e — Test top_n parameter
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

# ─── Group 4: Confidence Thresholds ──────────────────────────────────────────

verify_confidence_thresholds() {
    log_group "4" "Confidence Thresholds"

    fetch "/api/v1/meta/compare?region_a=JP"
    if ! require_200 "GET /api/v1/meta/compare?region_a=JP"; then
        return
    fi

    # 4a — Confidence structure for both regions
    local has_conf_a
    has_conf_a=$(echo "$RESP_BODY" | jq '
        .region_a_confidence | has("sample_size") and has("data_freshness_days") and has("confidence")
    ')
    local has_conf_b
    has_conf_b=$(echo "$RESP_BODY" | jq '
        .region_b_confidence | has("sample_size") and has("data_freshness_days") and has("confidence")
    ')

    if [ "$has_conf_a" = "true" ] && [ "$has_conf_b" = "true" ]; then
        log_pass "Confidence structure: both regions have sample_size, freshness_days, confidence"
    else
        log_fail "Confidence structure: missing required fields"
        return
    fi

    # 4b — Report actual values for operator assessment
    local sample_a
    sample_a=$(echo "$RESP_BODY" | jq '.region_a_confidence.sample_size')
    local fresh_a
    fresh_a=$(echo "$RESP_BODY" | jq '.region_a_confidence.data_freshness_days')
    local conf_a
    conf_a=$(echo "$RESP_BODY" | jq -r '.region_a_confidence.confidence')

    log_info "Region A: sample_size=$sample_a, freshness=$fresh_a days, confidence=$conf_a"

    local sample_b
    sample_b=$(echo "$RESP_BODY" | jq '.region_b_confidence.sample_size')
    local fresh_b
    fresh_b=$(echo "$RESP_BODY" | jq '.region_b_confidence.data_freshness_days')
    local conf_b
    conf_b=$(echo "$RESP_BODY" | jq -r '.region_b_confidence.confidence')

    log_info "Region B: sample_size=$sample_b, freshness=$fresh_b days, confidence=$conf_b"

    # 4c — Validate confidence level strings
    case "$conf_a" in
        high|medium|low)
            log_pass "Region A confidence: '$conf_a' (valid level)"
            ;;
        *)
            log_fail "Region A confidence: '$conf_a' (expected high/medium/low)"
            ;;
    esac

    case "$conf_b" in
        high|medium|low)
            log_pass "Region B confidence: '$conf_b' (valid level)"
            ;;
        *)
            log_fail "Region B confidence: '$conf_b' (expected high/medium/low)"
            ;;
    esac

    # 4d — Validate threshold logic (high: sample>=200 AND fresh<=3, medium: sample>=50 AND fresh<=7)
    # Note: We can't validate the calculation without seeing the raw data, but we can check consistency
    if [ "$conf_a" = "high" ]; then
        if [ "$sample_a" -ge 200 ] && [ "$fresh_a" -le 3 ]; then
            log_pass "Region A high confidence: meets threshold (sample>=200, fresh<=3)"
        else
            log_warn "Region A high confidence: sample=$sample_a fresh=$fresh_a (expected >=200, <=3)"
        fi
    fi

    if [ "$conf_b" = "high" ]; then
        if [ "$sample_b" -ge 200 ] && [ "$fresh_b" -le 3 ]; then
            log_pass "Region B high confidence: meets threshold (sample>=200, fresh<=3)"
        else
            log_warn "Region B high confidence: sample=$sample_b fresh=$fresh_b (expected >=200, <=3)"
        fi
    fi
}

# ─── Group 5: Frontend Contract ──────────────────────────────────────────────

verify_frontend_contract() {
    log_group "5" "Frontend Contract"

    # 5a — useMetaComparison hook expects:
    # region_a, region_b, comparisons[], region_a_confidence, region_b_confidence, lag_analysis
    fetch "/api/v1/meta/compare?region_a=JP"
    if require_200 "GET /api/v1/meta/compare?region_a=JP (frontend)"; then
        local has_all_fields
        has_all_fields=$(echo "$RESP_BODY" | jq '
            has("region_a") and
            has("region_b") and
            has("comparisons") and
            has("region_a_confidence") and
            has("region_b_confidence") and
            has("lag_analysis")
        ')

        if [ "$has_all_fields" = "true" ]; then
            log_pass "useMetaComparison fields: all required fields present"
        else
            log_fail "useMetaComparison fields: missing expected fields"
        fi

        # Check comparison entry structure (archetype, shares, divergence, tiers, sprite_urls)
        local comp_count
        comp_count=$(echo "$RESP_BODY" | jq '.comparisons | length')
        if [ "$comp_count" -gt 0 ]; then
            local has_entry_fields
            has_entry_fields=$(echo "$RESP_BODY" | jq '
                [.comparisons[0] |
                 has("archetype") and
                 has("region_a_share") and
                 has("region_b_share") and
                 has("divergence") and
                 has("region_a_tier") and
                 has("region_b_tier") and
                 has("sprite_urls")
                ] | all
            ')

            if [ "$has_entry_fields" = "true" ]; then
                log_pass "Comparison entry fields: archetype, shares, divergence, tiers, sprites"
            else
                log_fail "Comparison entry fields: missing expected fields"
            fi
        fi
    fi

    # 5b — useFormatForecast hook expects:
    # forecast_archetypes[], jp_snapshot_date, en_snapshot_date, jp_sample_size
    fetch "/api/v1/meta/forecast"
    if require_200 "GET /api/v1/meta/forecast (frontend)"; then
        local has_all_fields
        has_all_fields=$(echo "$RESP_BODY" | jq '
            has("forecast_archetypes") and
            has("jp_snapshot_date") and
            has("en_snapshot_date") and
            has("jp_sample_size")
        ')

        if [ "$has_all_fields" = "true" ]; then
            log_pass "useFormatForecast fields: all required fields present"
        else
            log_fail "useFormatForecast fields: missing expected fields"
        fi

        # Check forecast entry structure (archetype, jp_share, en_share, divergence, tier, trend_direction, sprite_urls, confidence)
        local entry_count
        entry_count=$(echo "$RESP_BODY" | jq '.forecast_archetypes | length')
        if [ "$entry_count" -gt 0 ]; then
            local has_entry_fields
            has_entry_fields=$(echo "$RESP_BODY" | jq '
                [.forecast_archetypes[0] |
                 has("archetype") and
                 has("jp_share") and
                 has("tier") and
                 has("trend_direction") and
                 has("sprite_urls") and
                 has("confidence")
                ] | all
            ')

            if [ "$has_entry_fields" = "true" ]; then
                log_pass "Forecast entry fields: archetype, jp_share, tier, trend, sprites, confidence"
            else
                log_fail "Forecast entry fields: missing expected fields"
            fi
        fi
    fi

    # 5c — Type checking (strings, numbers, arrays, objects)
    fetch "/api/v1/meta/compare?region_a=JP"
    if require_200 "GET /api/v1/meta/compare (type check)"; then
        local types_valid
        types_valid=$(echo "$RESP_BODY" | jq '
            (.region_a | type) == "string" and
            (.region_b | type) == "string" and
            (.comparisons | type) == "array" and
            (.region_a_confidence | type) == "object" and
            (.region_b_confidence | type) == "object"
        ')

        if [ "$types_valid" = "true" ]; then
            log_pass "Comparison types: correct types for all fields"
        else
            log_fail "Comparison types: incorrect field types"
        fi
    fi

    fetch "/api/v1/meta/forecast"
    if require_200 "GET /api/v1/meta/forecast (type check)"; then
        local types_valid
        types_valid=$(echo "$RESP_BODY" | jq '
            (.forecast_archetypes | type) == "array" and
            (.jp_snapshot_date | type) == "string" and
            (.en_snapshot_date | type) == "string" and
            (.jp_sample_size | type) == "number"
        ')

        if [ "$types_valid" = "true" ]; then
            log_pass "Forecast types: correct types for all fields"
        else
            log_fail "Forecast types: incorrect field types"
        fi
    fi
}

# ─── Group 6: Error Handling ─────────────────────────────────────────────────

verify_error_handling() {
    log_group "6" "Error Handling"

    # 6a — Invalid region parameter
    fetch "/api/v1/meta/compare?region_a=XX"
    if [ "$RESP_CODE" = "200" ] || [ "$RESP_CODE" = "404" ] || [ "$RESP_CODE" = "422" ]; then
        log_pass "Invalid region: endpoint handles gracefully (HTTP $RESP_CODE)"
    else
        log_warn "Invalid region: unexpected status code $RESP_CODE"
    fi

    # 6b — top_n=0 should return error
    fetch "/api/v1/meta/forecast?top_n=0"
    if [ "$RESP_CODE" = "422" ]; then
        log_pass "Forecast top_n=0: rejected with 422"
    elif [ "$RESP_CODE" = "400" ]; then
        log_pass "Forecast top_n=0: rejected with 400"
    elif [ "$RESP_CODE" = "200" ]; then
        log_warn "Forecast top_n=0: accepted (may want to enforce minimum)"
    else
        log_warn "Forecast top_n=0: unexpected status $RESP_CODE"
    fi

    # 6c — lag_days=100 (excessive value)
    fetch "/api/v1/meta/compare?region_a=JP&lag_days=100"
    if [ "$RESP_CODE" = "422" ]; then
        log_pass "Excessive lag_days=100: rejected with 422"
    elif [ "$RESP_CODE" = "400" ]; then
        log_pass "Excessive lag_days=100: rejected with 400"
    elif [ "$RESP_CODE" = "200" ]; then
        log_warn "Excessive lag_days=100: accepted (may want to enforce maximum)"
    else
        log_warn "Excessive lag_days=100: unexpected status $RESP_CODE"
    fi

    # 6d — Negative lag_days
    fetch "/api/v1/meta/compare?region_a=JP&lag_days=-7"
    if [ "$RESP_CODE" = "422" ]; then
        log_pass "Negative lag_days: rejected with 422"
    elif [ "$RESP_CODE" = "400" ]; then
        log_pass "Negative lag_days: rejected with 400"
    elif [ "$RESP_CODE" = "200" ]; then
        log_warn "Negative lag_days: accepted (should reject)"
    else
        log_warn "Negative lag_days: unexpected status $RESP_CODE"
    fi

    # 6e — Negative top_n
    fetch "/api/v1/meta/forecast?top_n=-5"
    if [ "$RESP_CODE" = "422" ]; then
        log_pass "Negative top_n: rejected with 422"
    elif [ "$RESP_CODE" = "400" ]; then
        log_pass "Negative top_n: rejected with 400"
    elif [ "$RESP_CODE" = "200" ]; then
        log_warn "Negative top_n: accepted (should reject)"
    else
        log_warn "Negative top_n: unexpected status $RESP_CODE"
    fi
}

# ─── Group 7: Tech Cards ─────────────────────────────────────────────────────

verify_tech_cards() {
    log_group "7" "Tech Cards (Archetype Key Cards)"

    # Discover a real archetype name from comparison endpoint
    fetch "/api/v1/meta/compare?region_a=JP"
    if ! require_200 "GET /api/v1/meta/compare (discover archetype)"; then
        log_warn "Tech cards: cannot discover archetype, skipping"
        return
    fi

    local archetype_name
    archetype_name=$(echo "$RESP_BODY" | jq -r '.comparisons[0].archetype // ""')

    if [ -z "$archetype_name" ] || [ "$archetype_name" = "null" ]; then
        log_warn "Tech cards: no archetype found in comparison, skipping"
        return
    fi

    log_info "Testing with archetype: $archetype_name"

    # URL-encode the archetype name
    local encoded_name
    encoded_name=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$archetype_name'))" 2>/dev/null)

    if [ -z "$encoded_name" ]; then
        log_warn "Tech cards: failed to encode archetype name, skipping"
        return
    fi

    # Fetch archetype details
    fetch "/api/v1/meta/archetypes/${encoded_name}"
    if ! require_200 "GET /api/v1/meta/archetypes/$archetype_name"; then
        log_fail "Tech cards: archetype endpoint failed (HTTP $RESP_CODE)"
        return
    fi

    # Check for key_cards field
    local has_key_cards
    has_key_cards=$(echo "$RESP_BODY" | jq 'has("key_cards")')
    if [ "$has_key_cards" != "true" ]; then
        log_fail "Tech cards: key_cards field not present"
        return
    fi

    local card_count
    card_count=$(echo "$RESP_BODY" | jq '.key_cards | length')
    log_pass "Tech cards: $card_count key cards for $archetype_name"

    if [ "$card_count" -gt 0 ]; then
        # Validate key card entry structure
        local has_card_fields
        has_card_fields=$(echo "$RESP_BODY" | jq '
            [.key_cards[0] | has("card_id") and has("inclusion_rate")] | all
        ')

        if [ "$has_card_fields" = "true" ]; then
            log_pass "Key card fields: card_id, inclusion_rate present"
        else
            log_fail "Key card fields: missing required fields"
        fi

        # Validate inclusion_rate range (0-1)
        local rate_valid
        rate_valid=$(echo "$RESP_BODY" | jq '
            [.key_cards[].inclusion_rate] | all(. >= 0 and . <= 1)
        ')

        if [ "$rate_valid" = "true" ]; then
            log_pass "Inclusion rates: all values in 0-1 range"
        else
            log_fail "Inclusion rates: some values outside 0-1 range"
        fi

        # Check if sorted by inclusion_rate descending
        local is_sorted
        is_sorted=$(echo "$RESP_BODY" | jq '
            if (.key_cards | length) <= 1 then true
            else
                [.key_cards[:-1], .key_cards[1:]] |
                transpose |
                all(.[0].inclusion_rate >= .[1].inclusion_rate)
            end
        ')

        if [ "$is_sorted" = "true" ]; then
            log_pass "Key cards sorting: sorted by inclusion_rate descending"
        else
            log_warn "Key cards sorting: not sorted by inclusion_rate"
        fi
    fi
}

# ─── Argument Parsing ────────────────────────────────────────────────────────

while [[ $# -gt 0 ]]; do
    case $1 in
        --api-url=*)
            API_URL="${1#*=}"
            shift
            ;;
        --verbose)
            VERBOSE=true
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
echo "║   TrainerLab Phase 3 Deep Validation                      ║"
echo "║   API: $API_URL"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

check_prerequisites

verify_comparison_quality
verify_lag_analysis
verify_forecast_logic
verify_confidence_thresholds
verify_frontend_contract
verify_error_handling
verify_tech_cards

# ─── Summary ─────────────────────────────────────────────────────────────────

echo ""
echo "════════════════════════════════════════════════════════════"
echo -e "  Results: ${GREEN}${PASSED} passed${NC}, ${RED}${FAILED} failed${NC}, ${YELLOW}${WARNED} warned${NC} (${TOTAL} total)"
echo "════════════════════════════════════════════════════════════"
echo ""

if [ "$FAILED" -gt 0 ]; then
    echo -e "${RED}FAILED${NC}"
    echo ""
    echo "Action items:"
    echo "  1. Review failed checks above"
    echo "  2. Run with --verbose to see response bodies"
    echo "  3. Check API logs for detailed error messages"
    echo "  4. Verify meta snapshots are computed (JP and Global)"
    echo "  5. Ensure tournament data is fresh (<14 days)"
    echo ""
    exit 1
elif [ "$WARNED" -gt 0 ]; then
    echo -e "${YELLOW}PASSED WITH WARNINGS${NC}"
    echo ""
    echo "Warnings detected (review above):"
    echo "  - May indicate missing data (compute meta snapshots)"
    echo "  - May indicate stale data (run ingestion)"
    echo "  - May indicate optional features not implemented"
    echo ""
    exit 0
else
    echo -e "${GREEN}ALL CHECKS PASSED${NC}"
    echo ""
    echo "Phase 3 validation complete. All systems operational."
    echo ""
    exit 0
fi
