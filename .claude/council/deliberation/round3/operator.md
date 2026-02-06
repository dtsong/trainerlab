# Operator Final Position -- JP Archetype Pipeline Phase 2

## Revised Recommendation

Deploy the Phase 2 reprocess through the existing CI/CD pipeline (GitHub Actions -> Artifact Registry -> Cloud Run) with a paginated `reprocess-archetypes` endpoint orchestrated via the existing Cloud Tasks queue. No Terraform changes required. No new infrastructure. The current stack -- Cloud Run (300s default timeout, 1 vCPU / 1 GiB, 1-10 instances), Cloud Tasks (0.5 dispatches/sec, 2 concurrent), Cloud SQL (PITR enabled, 14-day retention) -- handles this workload without modification. Add structured logging to the normalizer before any production reprocess, and gate on a canary test of 10-20 recent JP tournaments with >95% sprite-based accuracy.

## Concessions Made

1. **Prometheus metrics -> structured logging.** Cloud Logging JSON payloads are sufficient for a closed-beta product with one operator (Daniel). Prometheus adds infrastructure we would need to maintain. Structured logs are queryable via Cloud Logging's log-based metrics if we ever need dashboards.

2. **Manual Cloud SQL backup before reprocess -> PITR.** The Terraform config already has `point_in_time_recovery = true` with `backup_retention_days = 14` for prod (`terraform/main.tf:237-238`). A manual `pg_dump` or backup table is operational noise. PITR gives us sub-minute rollback granularity.

3. **Shadow mode -> canary test + detection method column.** The `archetype_detection_method` column in migration 021 provides the same observability as shadow mode. We can query the distribution after any run. No parallel codepath infrastructure needed.

## Non-Negotiables

These must be in place before triggering a production reprocess:

1. **Structured logging in `ArchetypeNormalizer.resolve()`.** Every resolution must emit a JSON log line with: `tournament_id` (when available), `sprite_key`, `resolved_archetype`, `detection_method`, `raw_archetype`. This is the audit trail. Without it, we cannot debug misclassifications after the fact. Implementation: upgrade existing `logger.debug` calls in `apps/api/src/services/archetype_normalizer.py:229-292` to `logger.info` with structured `extra` fields.

2. **Canary validation gate passes (>95% accuracy).** Run `validate_jp_pipeline.py` (`apps/api/scripts/validate_jp_pipeline.py`) against 20 recent tournaments. If sprite-based methods (sprite_lookup + auto_derive) resolve <95% of placements, stop and fix the sprite map. Do NOT proceed to historical reprocess on a failing canary.

3. **Reprocess endpoint uses pagination via Cloud Tasks.** Each invocation processes one batch (100-200 placements), returns progress, and enqueues the next batch. This keeps every request within the 300s Cloud Run default timeout. No need to modify the Cloud Run module or Terraform config. The existing Cloud Tasks queue (`terraform/modules/cloud_tasks/main.tf`) with its rate limits (0.5 dispatches/sec, 2 concurrent, 5 retries) handles orchestration.

4. **Dry-run mode on the reprocess endpoint.** Before touching production data, run the endpoint with `dry_run=true`. Log what WOULD change. Review the output. Only then flip to real writes.

5. **`compute-meta` rerun after reprocess completes.** Changed archetypes mean the meta snapshots are stale. After the reprocess finishes, trigger `POST /api/v1/pipeline/compute-meta` for JP region to regenerate snapshots.

## Implementation Notes

### Reprocess Endpoint Design

**Path:** `POST /api/v1/pipeline/reprocess-archetypes`
**Auth:** Same `verify_scheduler_auth` dependency as other pipeline endpoints (scheduler SA or ops SA via OIDC).

**Request schema:**

```python
class ReprocessArchetypesRequest(PipelineRequest):
    region: str = "JP"           # Which region to reprocess
    batch_size: int = 200        # Placements per batch
    cursor: str | None = None    # Opaque pagination cursor (placement UUID)
    force: bool = False          # Re-run even if detection_method is populated
```

**Response schema:**

```python
class ReprocessArchetypesResult(BaseModel):
    processed: int               # Placements processed this batch
    updated: int                 # Placements whose archetype changed
    skipped: int                 # Placements unchanged
    errors: list[str]
    next_cursor: str | None      # None means done
    total_remaining: int         # Approximate remaining placements
    success: bool
```

**Behavior:**

1. Query `tournament_placements tp JOIN tournaments t ON tp.tournament_id = t.id WHERE t.region = :region AND (tp.archetype_detection_method IS NULL OR :force)`, ordered by `tp.id`, limited to `batch_size`, offset by `cursor`.
2. For each placement, load sprite URLs from `raw_archetype_sprites` (stored in migration 021 column). If null, skip (no sprite data to work with -- these came from before Phase 1).
3. Run `normalizer.resolve(sprite_urls, raw_archetype, decklist=None)`.
4. Compare result to current `archetype`. If different, update. Log the change.
5. Return `next_cursor` (the last processed placement ID) and `total_remaining`.
6. If `next_cursor` is not None, the caller (Cloud Tasks or manual) enqueues the next batch.

**Why no re-scrape from Limitless:** The `raw_archetype_sprites` column (populated by Phase 1 for any tournament processed after PR #312) stores the sprite URLs. For truly old placements that have `raw_archetype_sprites = NULL` (pre-Phase-1 data), the reprocess endpoint should re-fetch the standings page from Limitless to extract sprites. This is the only Limitless fetch required -- it is a GET request per tournament, not per placement. Cache the result per tournament.

### Deployment Runbook (8 Steps)

**Step 1: Merge Phase 2 PR to `main`** (~0 min)

- PR contains: reprocess endpoint, structured logging, bug fixes (regex alignment, sprite map expansion), golden dataset tests.
- CI runs: ruff, ty, pytest (1606 backend tests must pass), Vitest (1786 frontend tests).
- Merging to `main` triggers `deploy-api.yml` automatically.

**Step 2: GitHub Actions deploys** (~10 min, automatic)

- Build stage: Docker build with Buildx + GHA cache.
- Migrate stage: `gcloud run jobs execute migrate-db`. Runs migration 023 (`add_card_mapping_confidence`). Migration 021/022 should already be applied from Phase 1 deploy; if not, they run here too. All are additive, zero-downtime.
- Deploy stage: Updates Cloud Run service with new image (digest-pinned, not `:latest`). Verify step checks service health.
- **Gate:** If any stage fails, the pipeline stops. No partial deploy.

**Step 3: Verify fresh JP tournament processing** (~15 min)

- Trigger: `POST /api/v1/pipeline/discover-jp` with `{ "dry_run": false, "lookback_days": 7 }` via ops SA.
- Wait for Cloud Tasks to process a few tournaments.
- Verify with SQL:
  ```sql
  SELECT tp.archetype, tp.archetype_detection_method, tp.raw_archetype,
         tp.raw_archetype_sprites, t.name
  FROM tournament_placements tp
  JOIN tournaments t ON tp.tournament_id = t.id
  WHERE t.region = 'JP' AND t.created_at >= NOW() - INTERVAL '1 hour'
  ORDER BY t.date DESC
  LIMIT 50;
  ```
- **Gate:** >95% of placements have `archetype_detection_method IN ('sprite_lookup', 'auto_derive')`. If not, investigate and do NOT proceed.

**Step 4: Run validation script** (~5 min)

```bash
uv run python apps/api/scripts/validate_jp_pipeline.py --tournaments 20 --output json
```

- **Gate:** `passed: true` in JSON output. This requires >95% sprite accuracy and 0 Cinderace regressions.

**Step 5: Seed `archetype_sprites` DB table** (~2 min)

- Trigger: `POST /api/v1/admin/archetype-sprites/seed` via ops SA.
- Verify: response `{"inserted": N}` where N matches the SPRITE_ARCHETYPE_MAP size.

**Step 6: Dry-run reprocess** (~30 min)

- Trigger: `POST /api/v1/pipeline/reprocess-archetypes` with `{ "dry_run": true, "region": "JP", "batch_size": 200 }`.
- Enqueue batches manually or via a simple loop (the endpoint returns `next_cursor`).
- Review Cloud Logging for the structured log output. Check:
  - How many archetypes change?
  - Are any changing to "Unknown" or "Rogue"?
  - Is the `text_label` fallback rate acceptable (<15%)?
- **Gate:** Review dry-run output. If >10% of placements are changing to "Unknown" or "Rogue", investigate.

**Step 7: Production reprocess** (~30-60 min wall time)

- Trigger: Same endpoint with `{ "dry_run": false, ... }`.
- Monitor during run:
  - Cloud Run instance count (Cloud Console > Cloud Run > Metrics)
  - Cloud Tasks queue depth (Cloud Console > Cloud Tasks)
  - Cloud SQL connections: `SELECT count(*) FROM pg_stat_activity;` (should stay under 50)
- Estimated: ~30,000 placements at 200/batch = 150 batches at 0.5/sec dispatch = ~5 min queue time + ~25 min processing.
- **Cost:** Under $3 in Cloud Run compute (150 requests _ ~10s each _ 1 vCPU).

**Step 8: Post-reprocess validation** (~20 min)

- Recompute meta: `POST /api/v1/pipeline/compute-meta` with `{ "dry_run": false, "lookback_days": 365 }`.
- Verify detection method distribution:
  ```sql
  SELECT archetype_detection_method, COUNT(*) as count,
         ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) as pct
  FROM tournament_placements tp
  JOIN tournaments t ON tp.tournament_id = t.id
  WHERE t.region = 'JP'
  GROUP BY archetype_detection_method
  ORDER BY count DESC;
  ```
- Verify meta shares are reasonable:
  ```sql
  SELECT archetype, meta_share
  FROM meta_snapshots
  WHERE region = 'JP' AND snapshot_date = CURRENT_DATE
  ORDER BY meta_share DESC
  LIMIT 20;
  ```
- Spot-check: Compare top 5 JP archetypes against Limitless website.
- Check frontend: Load the JP meta page and verify correct archetypes display.

### Monitoring After Launch

**Immediate (add to Phase 2 PR):**

- Structured JSON log on every `ArchetypeNormalizer.resolve()` call (upgrade from DEBUG to INFO).
- `logger.warning` when sprite extraction returns empty for a JP placement that has an archetype cell.

**First week post-reprocess (manual checks):**

- Daily: Run detection method distribution query (above) on Cloud SQL. Compare to baseline.
- Daily: Scan Cloud Logging for `text_label` entries with filter: `jsonPayload.method="text_label" resource.type="cloud_run_revision"`. If count spikes vs. previous day, investigate.

**Automated (add when cadence justifies it, not now):**

- Cloud Monitoring alert on error rate > 5% for `/api/v1/pipeline/process-tournament` endpoint.
- Log-based metric on `sprite_url_no_match` log entries (detects Limitless HTML changes).

### Infrastructure Cost Impact

No change to monthly cost (~$80-85/month). The reprocess is a one-time event estimated at under $3 in compute. Ongoing daily pipeline runs process ~10-20 new JP tournaments per day, which is well within the existing Cloud Tasks rate limits and Cloud Run scaling parameters.

### Rollback Procedures

- **Bad reprocess data:** Cloud SQL PITR. Restore to timestamp before reprocess started. All mutations are timestamped.
- **Bad API deploy:** Redeploy previous image from Artifact Registry. 10 images retained per cleanup policy (`terraform/main.tf:90-96`). `gcloud run services update-traffic trainerlab-api --region=us-west1 --to-revisions=PREVIOUS_REVISION=100`.
- **Bad migration:** `alembic downgrade 022` drops the confidence column. `alembic downgrade 020` removes all Phase 1 columns. Both downgrade functions are implemented and tested.

### What We Are NOT Doing (and Why)

| Decision                  | Rationale                                                                                                  |
| ------------------------- | ---------------------------------------------------------------------------------------------------------- |
| No Terraform changes      | Cloud Run defaults (300s timeout, scaling 1-10) are sufficient for paginated reprocess                     |
| No new Cloud Tasks queue  | Existing `tournament-scrape` queue handles reprocess batches at the same rate limits                       |
| No Prometheus/Grafana     | Structured Cloud Logging is queryable and free within GCP logging quota                                    |
| No staging environment    | One-time reprocess on a beta product with PITR does not justify a $40/month staging DB                     |
| No Docker Compose changes | Reprocess endpoint is a standard FastAPI route, works in local dev like all others                         |
| No Kubernetes             | We are running a single Cloud Run service. Kubernetes would be 10x the operational burden for zero benefit |
