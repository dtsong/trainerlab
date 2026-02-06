# Architect Final Position -- JP Archetype Data Pipeline Phase 2

## Revised Recommendation

Phase 2 is a **surgical data correction** followed by **meta recomputation**. The architecture is already in place from Phase 1 (ArchetypeNormalizer, priority chain, provenance columns, archetype_sprites table). Phase 2 wires the remaining connections and runs the first historical backfill. There is no new schema to design, no new service to build from scratch -- just plumbing, validation, and execution.

The work decomposes into six ordered steps, each with a hard gate before proceeding to the next:

1. Fix the latent `derive_name_from_key` hyphenation bug
2. Upgrade logging from debug to info in the normalizer
3. Capture golden dataset fixtures (5+ real HTML files)
4. Canary-validate 10-20 recent JP tournaments (>95% accuracy gate)
5. Build and execute `reprocess-archetypes` pipeline endpoint
6. Recompute JP meta snapshots for affected date ranges

---

## Concessions Made

1. **Dropped `archetype_version` column.** My Round 1 proposal included a version integer for tracking normalization rule changes. Phase 1 proved the in-memory `SPRITE_ARCHETYPE_MAP` dict is sufficient. If normalization rules change frequently enough to warrant versioning, we can add it later. The `archetype_detection_method` column provides adequate provenance without a separate version field.

2. **Dropped shadow mode.** My Round 1 mentioned a parallel-run approach where the new normalizer ran alongside the legacy detector. With 37+ tests passing, the priority chain validated end-to-end, and a canary test gate before bulk execution, shadow mode adds complexity without commensurate risk reduction.

3. **Dropped 5-phase migration plan.** My Round 1 envisioned a multi-migration sequence (archetype_version, confidence, sprite_urls expansion, etc.). Phase 1 delivered the essential schema (migrations 021, 022) and migration 023 added the `confidence` column. No further schema changes are needed for Phase 2.

4. **Accepted structured logging over Prometheus metrics.** The Operator is right -- for a closed beta with <10 users, JSON structured logs to Cloud Logging are sufficient. Prometheus metrics are infrastructure we do not need yet.

5. **Accepted canary test as the validation gate (not full forensic audit).** The Skeptic's concern about data quality is valid, but the right tool is a targeted canary test of 10-20 recent tournaments with a >95% accuracy threshold, not a week-long parallel analysis.

---

## Non-Negotiables

### 1. Do NOT delete existing tournament data

**Rationale:** The `tournament_placements` table has ~2000-3000 JP rows with associated decklists that took significant scraping effort to collect. Deleting and re-scraping would re-incur Limitless rate limits (~3000 pages at 0.5 req/sec = 100 minutes just for standings, plus decklist fetches). More importantly, deletion destroys data provenance -- we lose the ability to diff old vs new archetype labels for validation.

**What we do instead:** Backfill in place. For each JP tournament:

1. Re-fetch the standings HTML page only (lightweight, no decklist re-scraping).
2. Extract sprite URLs, populate `raw_archetype_sprites`.
3. Re-run `ArchetypeNormalizer.resolve()`, update `archetype` + `archetype_detection_method`.
4. Preserve the original `raw_archetype` value for audit trail.

### 2. Golden dataset fixtures before bulk backfill

The canary test (below) validates the normalizer against _real_ tournament data. But the golden dataset is the regression safety net that persists across future code changes. Without it, the next developer who modifies the priority chain or adds a new sprite map entry has no way to know if they broke something.

**Minimum bar:**

- 5 real JP tournament HTML files saved as test fixtures
- Each with a hand-validated `expected.json` containing: `sprite_key`, `expected_archetype`, `expected_detection_method`
- Test assertions verify all three fields, not just the archetype string

### 3. Canary test gate before bulk reprocess

Before running the reprocess endpoint against all ~200 JP tournaments, run it against 10-20 recent ones with known outcomes. The gate threshold is:

| Metric                    | Threshold | Fail action                         |
| ------------------------- | --------- | ----------------------------------- |
| sprite_lookup accuracy    | >= 95%    | Fix SPRITE_ARCHETYPE_MAP gaps       |
| Unknown archetype rate    | < 5%      | Investigate failing HTML extraction |
| auto_derive fallback rate | < 20%     | Add missing curated entries         |

If any threshold fails, fix the root cause and re-run the canary. Do not proceed to bulk reprocess until all three pass.

---

## Implementation Notes

### Step 1: Fix `derive_name_from_key` hyphenation bug

**Current code** (`archetype_normalizer.py:322-335`):

```python
@staticmethod
def derive_name_from_key(sprite_key: str) -> str:
    parts = sprite_key.split("-")
    return " ".join(p.capitalize() for p in parts if p)
```

**Bug:** "chien-pao-baxcalibur" -> "Chien Pao Baxcalibur" (splits on all hyphens). This is currently masked because `SPRITE_ARCHETYPE_MAP` has a curated entry for `chien-pao-baxcalibur` -> "Chien-Pao ex", so it hits `sprite_lookup` (priority 1) before reaching `auto_derive`. But any _new_ hyphenated Pokemon name that is not in the map will produce a wrong auto-derived name.

**Severity:** Latent. Not actively producing wrong data because all known hyphenated names are in the sprite map. However, the next Limitless meta shift could introduce an un-curated hyphenated sprite key (e.g. a new Chien-Pao variant), and the auto-derive fallback would silently produce a wrong name.

**Recommendation:** This is an inherently ambiguous problem -- `derive_name_from_key` cannot distinguish between "chien-pao" (one Pokemon, hyphenated name) and "charizard-pidgeot" (two Pokemon, hyphen-joined). The correct architectural answer is: **the auto-derive path is intentionally a rough fallback.** The fix is not smarter parsing but a process guarantee:

1. Add structured logging at INFO level when `auto_derive` fires, including the sprite key and derived name.
2. Review the auto_derive log regularly (weekly or after each canary).
3. Curate any new hyphenated entries into `SPRITE_ARCHETYPE_MAP` / `archetype_sprites` table.

If we want a code-level mitigation, maintain a `HYPHENATED_POKEMON` set containing known multi-word Pokemon names ("chien-pao", "iron-hands", "iron-valiant", "raging-bolt", "roaring-moon", etc.) and reconstruct those as units before joining. But this is minor and optional -- the curated map is the real defense.

### Step 2: Upgrade normalizer logging

**Current state:** All `archetype_resolved` log entries in `ArchetypeNormalizer.resolve()` use `logger.debug()` (lines 229, 244, 272, 284). These are invisible in production Cloud Logging at the default INFO level.

**Change:** Promote key log entries to `logger.info()`:

- Promote the `archetype_resolved` entry when `method == "auto_derive"` (these are the entries that need human review).
- Keep `sprite_lookup` and `text_label` at debug (high volume, low signal).
- Add a summary log at the end of `save_tournament()` in `tournament_scrape.py`: "Normalized {n} placements: {sprite_lookup: x, auto_derive: y, signature_card: z, text_label: w}".

This gives operational visibility without flooding logs.

### Step 3: Golden dataset capture

**Location:** `apps/api/tests/fixtures/jp_tournaments/`

**Capture process:**

1. Manually fetch 5+ JP City League standings pages from Limitless.
2. Save the raw HTML as `.html` files.
3. For each, manually verify the sprite URLs and expected archetype resolutions.
4. Create an `expected.json` alongside each HTML file:

```json
{
  "tournament_url": "https://play.limitlesstcg.com/tournament/...",
  "tournament_date": "2026-01-28",
  "placements": [
    {
      "placement": 1,
      "sprite_urls": ["https://r2.limitlesstcg.net/.../charizard.png", "..."],
      "expected_sprite_key": "charizard-pidgeot",
      "expected_archetype": "Charizard ex",
      "expected_method": "sprite_lookup"
    }
  ]
}
```

5. Write a parametrized pytest that loads each fixture, runs the full extraction + normalization pipeline, and asserts all three fields.

### Step 4: Canary validation

**Process:** Build a dry-run mode for the reprocess endpoint that:

1. Fetches standings HTML for the most recent 10-20 JP tournaments already in the DB.
2. Extracts sprites, runs normalizer.
3. Compares the _new_ archetype label against the _existing_ label in `tournament_placements.archetype`.
4. Reports a diff: `{matched: N, changed: M, details: [{placement_id, old_archetype, new_archetype, method}]}`.

The report lets us inspect every change before committing it. If >95% match or the changes are clearly improvements (e.g., "Unknown" -> "Charizard ex"), proceed to bulk.

### Step 5: Build reprocess-archetypes endpoint

**New endpoint:** `POST /api/v1/pipeline/reprocess-archetypes`

**Schema:**

```python
class ReprocessArchetypesRequest(PipelineRequest):
    region: str = "JP"
    batch_size: int = Field(default=10, ge=1, le=50)
    rate_limit_delay: float = Field(default=2.0, ge=0.5, le=10.0)

class ReprocessArchetypesResult(BaseModel):
    tournaments_processed: int
    placements_updated: int
    placements_unchanged: int
    detection_method_counts: dict[str, int]
    errors: list[str]
    success: bool
```

**Implementation approach:**

1. Query `tournaments WHERE region = 'JP' ORDER BY date DESC`.
2. For each tournament, paginated in batches of `batch_size`:
   a. Re-fetch the standings HTML page from Limitless (single HTTP GET).
   b. Extract sprite URLs from the HTML using the existing `_extract_archetype_and_sprites_from_images()` method.
   c. For each placement in the tournament:
   - Update `raw_archetype_sprites` with the extracted sprite URLs.
   - Run `ArchetypeNormalizer.resolve()` with the new sprites.
   - Update `archetype`, `archetype_detection_method`, `raw_archetype`.
     d. Commit the batch.
     e. Sleep `rate_limit_delay` seconds between tournaments (respect Limitless rate limits).
3. After all tournaments are processed, return the summary result.

**Estimated scale:** ~200 JP tournaments, each requiring 1 HTTP GET for the standings page. At 0.5 req/sec (2s delay), this completes in ~7 minutes. Under $3 compute on Cloud Run.

**Key architectural decisions:**

- This is a pipeline endpoint, not a one-off script. It can be re-run safely (idempotent -- re-extracting and re-normalizing produces the same result).
- It operates within the existing `TournamentScrapeService` session pattern, not a raw SQL script.
- It uses the existing `ArchetypeNormalizer` with `load_db_sprites()` called once at the start of the batch.
- Rate limiting is built into the endpoint, not delegated to Cloud Tasks. The total runtime (~7 min) fits within a single Cloud Run request timeout (15 min default).

### Step 6: Recompute JP meta snapshots

After the backfill completes, recompute meta snapshots for the affected date range:

1. Call the existing `compute_daily_snapshots()` with `regions=["JP"]` for each date in the affected range (or use the existing `compute-meta` pipeline endpoint with the appropriate parameters).
2. The snapshot computation already filters by `region` and `best_of`, so it will pick up the corrected archetype labels automatically.
3. No new code needed -- this is just an invocation of the existing pipeline.

**Ordering matters:** Meta snapshots depend on correct archetype labels, so this must run _after_ the backfill is fully committed.

---

## Architecture Diagram -- Phase 2 Data Flow

```
Step 5: Reprocess Endpoint
    |
    v
[1] Query JP tournaments (DB)
    |
    v
[2] For each tournament:
    |-- Fetch standings HTML (Limitless HTTP GET, 0.5 req/sec)
    |-- Extract sprite URLs (_extract_archetype_and_sprites_from_images)
    |-- For each placement:
    |    |-- build_sprite_key(sprite_urls)
    |    |-- ArchetypeNormalizer.resolve(sprite_urls, raw_archetype, decklist)
    |    |-- UPDATE tournament_placements SET
    |    |     archetype = resolved_archetype,
    |    |     raw_archetype_sprites = sprite_urls,
    |    |     archetype_detection_method = method
    |    v
    |-- COMMIT batch
    v
[3] compute_daily_snapshots(regions=["JP"]) -> Updated meta snapshots
```

---

## Files to Create or Modify

| File                                             | Action | Purpose                               |
| ------------------------------------------------ | ------ | ------------------------------------- |
| `apps/api/src/services/archetype_normalizer.py`  | Modify | Promote auto_derive logging to INFO   |
| `apps/api/src/services/tournament_scrape.py`     | Modify | Add detection method summary log      |
| `apps/api/src/pipelines/reprocess_archetypes.py` | Create | Reprocess pipeline (Step 5)           |
| `apps/api/src/routers/pipeline.py`               | Modify | Add reprocess-archetypes endpoint     |
| `apps/api/src/schemas/pipeline.py`               | Modify | Add ReprocessArchetypesRequest/Result |
| `apps/api/tests/fixtures/jp_tournaments/`        | Create | Golden dataset HTML + expected JSON   |
| `apps/api/tests/test_reprocess_archetypes.py`    | Create | Reprocess pipeline tests              |
| `docs/CODEMAP.md`                                | Modify | Add reprocess pipeline entry          |

**No new migrations required.** All necessary columns exist (migrations 021, 022, 023).

---

## Risk Register

| Risk                                                                          | Likelihood | Impact | Mitigation                                                                                                                                  |
| ----------------------------------------------------------------------------- | ---------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------- |
| Limitless HTML structure changes between original scrape and re-fetch         | Low        | Medium | Golden dataset tests cover current HTML structure. If extraction fails for a tournament, skip it and log the error.                         |
| Rate limiting from Limitless during bulk re-fetch                             | Medium     | Low    | 2s delay between requests (0.5 req/sec). Total runtime ~7 min for 200 tournaments. Well under any reasonable rate limit.                    |
| Archetype label changes break downstream consumers (frontend, meta snapshots) | Low        | Medium | Canary test validates accuracy before bulk run. Meta snapshots are recomputed afterward. Frontend reads from snapshots, not raw placements. |
| New sprite keys appear that are not in the curated map                        | Certain    | Low    | auto_derive fallback produces reasonable names. INFO-level logging flags new keys for curation.                                             |

---

## What This Explicitly Does NOT Include

1. **ML-based archetype prediction.** Ship descriptive intelligence first.
2. **Format Forecast widget.** Deferred to post-April 10 (Advocate conceded).
3. **`reprocessing_batch` tracking table.** Progress is trackable via `archetype_detection_method IS NULL` query.
4. **`archetype_version` column.** Over-engineering for a system that changes normalization rules ~monthly.
5. **Full Limitless client decomposition.** The 1700-line `limitless.py` works. Refactoring it is a separate concern.
6. **BO1 vs BO3 correction factors.** Needs 2-3 months of clean data first.
7. **Frontend changes.** The small sprites + BO1 persistence PR can run in parallel but is not gated by or gating Phase 2 backend work.
