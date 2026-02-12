-- Explain plan for /api/v1/japan/card-count-evolution aggregate query
-- Usage:
--   psql "$DATABASE_URL" -f scripts/local/explain-card-count-evolution.sql

EXPLAIN (ANALYZE, BUFFERS)
SELECT tp.tournament_id, tp.decklist, t.date
FROM tournament_placements tp
JOIN tournaments t ON tp.tournament_id = t.id
WHERE tp.archetype = 'Charizard ex'
  AND t.region = 'JP'
  AND t.best_of = 1
  AND t.date >= CURRENT_DATE - INTERVAL '90 days'
  AND tp.decklist IS NOT NULL
ORDER BY t.date;
