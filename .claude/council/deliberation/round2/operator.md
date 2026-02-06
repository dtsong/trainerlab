# Operator Round 2 — JP Archetype Pipeline: Post-Phase-1 Operational Assessment

## Context Shift: Phase 1 Is Merged

PR #312 delivered the foundational code: fixed sprite parsing, `ArchetypeNormalizer` with the four-step priority chain, migrations 021 and 022, and 37 new tests. The question is no longer "should we build this?" but "how do we safely deploy, validate, and then reprocess historical data?" Several Round 1 positions were written before Phase 1 landed and need recalibration.

---

## 1. Migration Deployment Plan

**Migration chain integrity: verified.** The chain is `019 -> 020 -> 021 -> 022`. Migration 020 (`add_placeholder_cards`) is the prerequisite for 021 (`add_archetype_metadata` -- adds `raw_archetype`, `raw_archetype_sprites`, `archetype_detection_method` columns to `tournament_placements`), and 022 (`add_archetype_sprites` -- creates the `archetype_sprites` lookup table).

**Deployment order:**

1. Run `alembic upgrade head` against Cloud SQL. All three columns in 021 are nullable, so this is a non-breaking additive migration. No existing queries break. The new `archetype_sprites` table in 022 is standalone. Zero downtime.
2. Deploy the updated API image (with `ArchetypeNormalizer` and updated `TournamentScrapeService`). The normalizer auto-creates for JP tournaments (`if tournament.region == "JP" and normalizer is None`), so EN processing is completely unaffected.
3. Verify: run `discover-jp` and `process-tournament` for one JP City League. Check that `raw_archetype`, `raw_archetype_sprites`, and `archetype_detection_method` are populated.

**Risks:**

- **LOW:** Migration 021 adds a CHECK constraint (`ck_placement_detection_method`). If any future code writes an unlisted detection method string, the INSERT fails. The constraint allows NULL, so existing rows are safe. The four allowed values match `ArchetypeNormalizer.resolve()` output exactly.
- **LOW:** The `archetype_sprites` table starts empty. `SPRITE_ARCHETYPE_MAP` is an in-code dict with 23 entries. The table is for future DB-driven lookups; the code does not query it yet. No operational dependency on seeding it before deploy.

**Rollback:** `alembic downgrade 020` drops the three new columns and the lookup table cleanly. The downgrade functions are implemented correctly.

**Action item:** Run migrations in a maintenance window (even though zero-downtime, doing it off-peak is good hygiene for the first production run). Cloud SQL point-in-time recovery is enabled with 14-day retention -- that is our safety net.

---

## 2. Reprocessing Infrastructure

There is **no reprocess endpoint today.** The pipeline router (`/apps/api/src/routers/pipeline.py`) has `discover-*`, `process-tournament`, and `compute-meta`, but nothing to re-run normalization on existing placements without re-scraping from Limitless.

**What we need (in order of priority):**

### 2a. Reprocess endpoint (required)

A new pipeline endpoint: `POST /api/v1/pipeline/reprocess-archetypes`. This should:

- Query `tournament_placements` where `archetype_detection_method IS NULL` (legacy data without provenance) or where a `force` flag is set.
- For each placement: load `raw_archetype_sprites` (if available) or re-extract sprites from the associated tournament's standing page.
- Run `ArchetypeNormalizer.resolve()` and update `archetype`, `raw_archetype`, `archetype_detection_method`.
- Process in batches of 100-200 to avoid Cloud Run timeout (see below).
- Return progress: `{"processed": 1500, "updated": 342, "errors": 3}`.

### 2b. Cloud Run timeout (required before bulk reprocess)

The Terraform Cloud Run module (`/terraform/modules/cloud_run/main.tf`) does **not** set `timeout` on the service. Cloud Run v2 defaults to 300 seconds. For a bulk reprocess that iterates over thousands of placements with potential Limitless re-fetches, 300s is tight. Two options:

- **Option A (preferred):** Make reprocess paginated/resumable. Each call processes one batch (e.g., 200 placements), returns a cursor, Cloud Tasks enqueues the next batch. Stays within 300s easily.
- **Option B:** Add `timeout = "600s"` to the Cloud Run template in Terraform. Simple but masks architectural issues.

I recommend Option A. It works with the existing Cloud Tasks queue (0.5 tasks/sec, max 2 concurrent). Estimated reprocess for 3000 tournaments at 10 placements each = 30,000 placements. At 200 per batch = 150 Cloud Tasks. At 0.5/sec = 5 minutes of queue time plus processing. Total wall time under 30 minutes.

### 2c. Backup before reprocess (required)

Before the first production reprocess, take a manual Cloud SQL export or rely on the automated daily backup. The 14-day PITR window in Terraform covers rollback. No need to create a manual `tournament_placements_backup` table -- that is operational noise we do not need when Cloud SQL PITR exists.

**Cost estimate for full reprocess:** Same as Round 1: under $3 in Cloud Run compute. Negligible.

---

## 3. Challenges to Other Agents

### Skeptic: "Full audit before re-scrape"

**Their position:** Trace the Cinderace EX error end-to-end before changing anything. No re-scrape until root cause documented.

**My response: Modify.** Skeptic's position was written before Phase 1 landed. The root cause IS documented -- `_parse_jp_placement_row()` used a broken CSS selector (`img.pokemon`) that never matched JP tournament HTML, so sprite extraction returned nothing. PR #312 replaced it with `_extract_archetype_and_sprites_from_images()` which works against real fixture HTML. The fix is merged with 37 tests proving it.

That said, Skeptic's canary testing proposal is operationally sound: test the new normalizer on 10 recent JP tournaments and compare output to Limitless ground truth BEFORE touching historical data. This is cheap (10 Cloud Tasks, 5 minutes), gives us a validation gate, and can run in parallel with other work. We should do this as step 3 of the deploy plan (above), not as a blocking prerequisite for the deploy itself.

**Non-negotiable from ops perspective:** We instrument first, then reprocess. Not the other way around.

### Craftsman: "Shadow mode" (run old and new detectors in parallel)

**Their position:** Deploy new sprite-based detector in shadow mode, log differences, review for 1 week before switching.

**My response: Defer.** Shadow mode is a sound idea for a system with heavy production traffic and unclear failure modes. Our situation is different:

- We are in closed beta. Traffic is minimal.
- The old detector (signature cards) is still the fallback in the normalizer's priority chain (step 3 of 4).
- The normalizer already provides full provenance tracking via `archetype_detection_method` column -- we can query which method was used for every single placement.
- Shadow mode requires running two codepaths, logging diffs, building a comparison dashboard, and someone reviewing the logs daily. That is 3-5 days of engineering for a beta product.

**Counter-proposal:** Instead of shadow mode, add a simple SQL query to the post-deploy validation:

```sql
SELECT archetype_detection_method, COUNT(*)
FROM tournament_placements
WHERE tournament_id IN (
    SELECT id FROM tournaments WHERE region = 'JP' AND date >= '2026-01-15'
)
GROUP BY archetype_detection_method;
```

If >20% of placements hit `text_label` (the worst fallback), investigate before reprocessing historical data. This gives us the same signal as shadow mode at zero infrastructure cost.

### Architect: Three-layer pipeline (ingestion/normalization/analysis)

**Their position:** Full three-layer refactor with versioned normalization.

**My response: Maintain for target state, but Phase 1 already achieves the operational goal.** The code as merged stores `raw_archetype` and `archetype_detection_method`, which gives us data provenance and reprocessability. The `archetype_sprites` table exists for future DB-driven lookups. We do not need to add `archetype_version` columns or A/B normalization infrastructure right now. Ship what we have, instrument it, then iterate.

### Strategist: Phase timeline

**Their position:** Phase 1 (weeks 1-2), Phase 2 (weeks 3-4), Phase 3 (weeks 5-6).

**My response: Maintain, accelerate.** Phase 1 code is already merged. That compresses the timeline. We should be running reprocess (their Phase 2) within days of deploying the migration, not weeks. The April 10 deadline gives us margin but not unlimited margin.

---

## 4. Monitoring Gaps

Phase 1 code exists but has zero production observability. Here is what we need before reprocessing historical data:

### Must-have (before reprocess)

1. **Detection method distribution metric.** After each `compute-meta` run, log the breakdown of `archetype_detection_method` values for JP placements processed in that batch. Alert if `text_label` (the weakest fallback) exceeds 15% of placements. Implementation: add 5 lines of logging to `save_tournament()` in `tournament_scrape.py`.

2. **Sprite extraction success rate.** In `_extract_archetype_and_sprites_from_images()`, log when sprite extraction returns an empty list for a JP placement that has an archetype cell. This detects Limitless HTML changes (the exact failure mode that caused the Cinderace bug). Implementation: add `logger.warning` when `sprite_urls` is empty but `archetype_cell` is not empty.

3. **Normalizer resolution audit log.** Log every `ArchetypeNormalizer.resolve()` call with structured fields: `tournament_id`, `sprite_key`, `resolved_archetype`, `detection_method`. Use Cloud Logging's JSON payload for queryability. This is the single most important observability addition -- it lets us audit every archetype decision after the fact.

### Nice-to-have (post-reprocess)

4. **Archetype drift alert.** Compare daily JP meta shares to a 7-day rolling average. Alert if any single archetype moves more than 10 percentage points in one day. This likely indicates a data quality issue, not a real meta shift.

5. **SPRITE_ARCHETYPE_MAP coverage tracking.** Log when `auto_derive` is used (meaning the sprite key was not in the hardcoded map). Track which new sprite keys appear -- these are archetypes we should add to the map or the `archetype_sprites` DB table.

6. **Cloud SQL connection pool monitoring during reprocess.** The current setup uses SQLAlchemy async pool (default pool_size=5) with max 10 Cloud Run instances = 50 max connections against Cloud SQL's 100 connection limit. During bulk reprocess, monitor `pg_stat_activity` for connection count. If it exceeds 80, back off the Cloud Tasks dispatch rate.

---

## 5. Concrete Ops Tasks (Ordered)

This is the deploy-and-reprocess runbook. Each step must complete before the next begins.

**Step 1: Deploy migrations to Cloud SQL (30 minutes)**

- Run `alembic upgrade head` via Cloud Run job or SSH tunnel to Cloud SQL.
- Verify: `\d tournament_placements` shows new columns; `\d archetype_sprites` exists.
- Rollback: `alembic downgrade 020`.

**Step 2: Deploy updated API image (15 minutes)**

- Push new image via CI/CD (GitHub Actions -> Artifact Registry -> Cloud Run).
- Verify: health check passes, `GET /api/v1/health` returns 200.
- Rollback: redeploy previous image tag from Artifact Registry (10 images retained per cleanup policy).

**Step 3: Canary validation -- process 10 new JP tournaments (30 minutes)**

- Trigger `POST /api/v1/pipeline/discover-jp` and let Cloud Tasks process the new tournaments.
- Query:
  ```sql
  SELECT archetype, archetype_detection_method, raw_archetype
  FROM tournament_placements tp
  JOIN tournaments t ON tp.tournament_id = t.id
  WHERE t.region = 'JP' AND t.date >= CURRENT_DATE - INTERVAL '7 days'
  ORDER BY t.date DESC;
  ```
- Validate: sprite_lookup and auto_derive methods are producing correct archetype names. Compare against Limitless website manually for 5 tournaments.
- Decision gate: If >95% of placements have a reasonable archetype (not "Unknown", not all "text_label"), proceed.

**Step 4: Add structured logging to normalizer (1-2 hours of dev work)**

- Add JSON-structured log lines to `ArchetypeNormalizer.resolve()` and `save_tournament()`.
- Deploy updated image.

**Step 5: Build reprocess-archetypes endpoint (4-8 hours of dev work)**

- Paginated endpoint that updates existing placements using the normalizer.
- Uses Cloud Tasks for batch orchestration (Option A from section 2b).
- Includes dry-run mode that logs changes without writing.

**Step 6: Dry-run reprocess (1 hour)**

- Run reprocess in dry-run mode against all JP placements.
- Review the log output: how many archetypes change? Which ones?
- Generate before/after summary (can be a SQL query joining old archetype vs new).

**Step 7: Production reprocess (2-3 hours wall time)**

- Run reprocess for real.
- Monitor Cloud Run instances, Cloud SQL connections, Cloud Tasks queue depth.
- After completion, run `compute-meta` for JP region to regenerate meta snapshots.

**Step 8: Post-reprocess validation (30 minutes)**

- Verify meta shares look reasonable (no single archetype > 40%, Unknown < 5%).
- Spot-check 5 known tournaments against Limitless website.
- Check frontend: JP meta dashboard displays correct data.

**Total estimated time: 2-3 days of calendar time, 1-2 days of dev effort.**

---

## Infrastructure Gaps Summary

| Gap                                     | Severity | Effort  | When                                                    |
| --------------------------------------- | -------- | ------- | ------------------------------------------------------- |
| Run migrations 021+022 on Cloud SQL     | Critical | 30 min  | Before deploy                                           |
| Add structured logging to normalizer    | High     | 2 hrs   | Before reprocess                                        |
| Build reprocess-archetypes endpoint     | High     | 4-8 hrs | Before historical reprocess                             |
| Cloud Run explicit timeout in Terraform | Medium   | 15 min  | Optional if using paginated reprocess                   |
| Seed archetype_sprites DB table         | Low      | 1 hr    | After validation, when switching from in-code map to DB |
| Archetype drift alerting                | Low      | 2 hrs   | Post-reprocess                                          |

The infrastructure is sound for this work. Cloud Run, Cloud Tasks, and Cloud SQL are correctly sized. No Terraform changes are required for the reprocess itself if we use the paginated approach. The main gaps are operational: logging, the reprocess endpoint, and validation queries.
