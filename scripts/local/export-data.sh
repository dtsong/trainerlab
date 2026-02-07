#!/bin/bash
# Export data from local database for analysis
# Usage: ./scripts/export-data.sh [START_DATE] [END_DATE] [FORMAT] [OUTPUT_DIR]
#
# Examples:
#   ./scripts/export-data.sh                                    # Export all data as JSON
#   ./scripts/export-data.sh 2026-01-23 2026-02-05 csv          # Date range + CSV format
#   ./scripts/export-data.sh 2026-01-23 2026-02-05 json ./data  # Custom output dir

set -e

# Colors
BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m'

# Arguments
START_DATE="${1:-2025-11-28}"
END_DATE="${2:-$(date +%Y-%m-%d)}"
FORMAT="${3:-json}"
OUTPUT_DIR="${4:-./exports}"
API_URL="${API_URL:-http://localhost:8080}"

# Validate format
if [ "$FORMAT" != "json" ] && [ "$FORMAT" != "csv" ]; then
    echo "Error: Format must be 'json' or 'csv'"
    exit 1
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo -e "${BLUE}[INFO]${NC} Exporting data from $START_DATE to $END_DATE"
echo -e "${BLUE}[INFO]${NC} Format: $FORMAT"
echo -e "${BLUE}[INFO]${NC} Output: $OUTPUT_DIR"
echo ""

# Export decklists
echo "📋 Exporting decklists..."
curl -s "$API_URL/api/v1/exports/decklists?start_date=$START_DATE&end_date=$END_DATE&region=JP&format=$FORMAT" \
    > "$OUTPUT_DIR/jp_decklists_${START_DATE}_to_${END_DATE}.$FORMAT"
echo -e "${GREEN}✓${NC} Decklists saved"

# Export card usage
echo "📊 Exporting card usage statistics..."
curl -s "$API_URL/api/v1/exports/card-usage?start_date=$START_DATE&end_date=$END_DATE&group_by=day&format=$FORMAT" \
    > "$OUTPUT_DIR/jp_card_usage_${START_DATE}_to_${END_DATE}.$FORMAT"
echo -e "${GREEN}✓${NC} Card usage saved"

# Export placeholder cards
echo "🏷️  Exporting placeholder cards..."
./scripts/db-local.sh -c "
COPY (
    SELECT
        pc.en_card_id,
        pc.name_en,
        pc.name_jp,
        pc.jp_card_id,
        pc.set_code,
        pc.supertype,
        pc.types,
        pc.hp,
        pc.is_unreleased,
        pc.source,
        pc.source_account,
        pc.created_at
    FROM placeholder_cards pc
    WHERE pc.is_unreleased = true
    ORDER BY pc.created_at DESC
) TO STDOUT WITH CSV HEADER;
" > "$OUTPUT_DIR/placeholder_cards.csv"
echo -e "${GREEN}✓${NC} Placeholder cards saved"

# Export tournament summary
echo "🏆 Exporting tournament summary..."
./scripts/db-local.sh -c "
COPY (
    SELECT
        t.date,
        t.name,
        t.region,
        t.participant_count,
        COUNT(p.id) as placements,
        COUNT(p.id) FILTER (WHERE p.decklist IS NOT NULL) as decklists_with_data
    FROM tournaments t
    LEFT JOIN tournament_placements p ON t.id = p.tournament_id
    WHERE t.region = 'JP'
      AND t.date >= '$START_DATE'
      AND t.date <= '$END_DATE'
    GROUP BY t.id, t.date, t.name, t.region, t.participant_count
    ORDER BY t.date DESC
) TO STDOUT WITH CSV HEADER;
" > "$OUTPUT_DIR/tournament_summary.csv"
echo -e "${GREEN}✓${NC} Tournament summary saved"

echo ""
echo "════════════════════════════════════════════════════════════"
echo -e "${GREEN}✅ Export complete!${NC}"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Files created:"
ls -lh "$OUTPUT_DIR/"
echo ""
