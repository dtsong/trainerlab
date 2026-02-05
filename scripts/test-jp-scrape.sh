#!/bin/bash
# Quick test script to process a sample JP tournament directly

API_URL="${API_URL:-http://localhost:8080}"

echo "🧪 Testing JP Tournament Scraping"
echo "=================================="
echo ""

# Process a specific JP City League tournament
echo "📍 Processing JP City League tournament..."
curl -s -X POST "$API_URL/api/v1/pipeline/process-tournament" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Tokyo City League",
    "source_url": "https://limitlesstcg.com/tournaments/jp/3957",
    "tournament_date": "2026-01-25",
    "region": "JP",
    "game_format": "standard",
    "best_of": 1,
    "participant_count": 0
  }' | jq .

echo ""
echo "✅ Test complete!"
echo ""
echo "Checking database for imported data:"
docker-compose exec db psql -U postgres -d trainerlab -c "
SELECT
    t.name,
    t.date,
    COUNT(p.id) as placements,
    COUNT(p.id) FILTER (WHERE p.decklist IS NOT NULL) as with_decklists
FROM tournaments t
LEFT JOIN tournament_placements p ON t.id = p.tournament_id
WHERE t.region = 'JP'
GROUP BY t.id, t.name, t.date
ORDER BY t.date DESC
LIMIT 5;
"
