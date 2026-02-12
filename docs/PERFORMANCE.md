# Performance Targets

## Issue #339: Decklist JSONB Aggregate Reads

### Target Endpoint

- `GET /api/v1/japan/card-count-evolution`

### p95 SLO

- **p95 <= 350ms** for `days=90` and `top_cards=20`
- Test profile: seeded local dataset with >= 10k JP placement rows containing decklists

### Query Plan Expectations

After migration `031`, Postgres should prefer index-assisted access paths:

- `ix_tournaments_region_bestof_date`
- `ix_tp_archetype_tournament_with_decklist`
- `ix_tp_decklist_gin`

Use `EXPLAIN (ANALYZE, BUFFERS)` to confirm index usage and reduced total plan cost
versus pre-migration baseline.

### Validation Commands

1. Apply migration

```bash
uv run alembic upgrade head
```

2. Capture query plan

```bash
psql "$DATABASE_URL" -f scripts/local/explain-card-count-evolution.sql
```

3. Benchmark endpoint latency

```bash
scripts/local/benchmark-card-count-evolution.sh
```

### Rollback Guidance

- Roll back migration `031` if regression is detected:

```bash
uv run alembic downgrade 030
```

This drops only the optimization indexes and leaves application data unchanged.
