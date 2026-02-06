# Strategist Final Position -- JP Archetype Pipeline Phase 2

## Revised Recommendation

**Ship the remaining MVP in 5 working days. Draw the line hard. Do not expand scope.**

The sprint velocity from Phase 1 (scoped at 2 weeks, shipped in ~1 day) and the interim fixes (sprite map 24 -> 49 entries, mega suffix keys, regex alignment, migration 023) mean the remaining work is smaller than it was in Round 2. The backlog has 7 items. Three of them are under 2 hours each. The rest are 0.5-2 day tasks gated behind a single validation step.

Timeline: **5 working days from start of Phase 2 execution** (target: ~Feb 14 if started Feb 7).

This leaves a full 8-week buffer before the April 10 Rotation. That buffer is for polish, fast-follows, and unforeseen issues -- not for backfilling scope.

## Concessions Made

Three concessions from my Round 2 position, all justified by council consensus:

1. **Backfill in place instead of wipe-and-rescrape.** Round 2 I proposed wiping JP placements and re-scraping from scratch. Every agent pushed back, and they were right. The normalizer can reprocess existing `raw_archetype` + `sprite_urls` data without re-hitting Limitless servers. This is faster (~minutes vs hours), cheaper (zero network cost), and lower risk (no dependency on Limitless uptime). Concession accepted.

2. **45-minute documentation prerequisite.** The Chronicler's request that CODEMAP.md and CLAUDE.md updates happen before Phase 2 starts. Small cost, high leverage -- any agent working on this codebase after us benefits. But I am capping it: 45 minutes max, and it is items 7a/7b in the backlog, not a gate on the canary test. Documentation runs in parallel with validation, not before it.

3. **Structured logging as a parallel track.** The Operator and Skeptic both want structured logging for the pipeline. I flagged it as a deferral in Round 2. Revised position: it can run as a non-blocking parallel workstream during the reprocess phase. It does not gate any MVP item, but if someone has slack time while waiting for the reprocess to finish, logging improvements are the highest-value use of that time.

## Non-Negotiables

These five scope boundaries must hold:

1. **Canary test is the gate, not a full forensic audit.** 10-20 recent JP tournaments, >95% archetype accuracy vs Limitless ground truth. If it passes, we proceed. No multi-day root-cause archaeology on the old CSS selector bug. The old code path is deleted. The new code path is tested (49 sprite map entries, 4-level priority chain, `archetype_detection_method` on every placement). The canary IS the validation.

2. **No new frontend surfaces in MVP.** The `/meta/japan` page, meta dashboard, and JP Signal badges already exist. They need correct data, not new widgets. Format Forecast, prediction confidence badges, and the prediction detail modal are all deferred to post-April 10. Zero new React components in this sprint.

3. **No ML or prediction infrastructure.** The Scout has validated that the JP meta data is directionally correct and useful even without predictive models. Clean historical data viewed as-is is the MVP value proposition. "What is the JP meta right now?" is the question we answer. "What will the EN meta look like after rotation?" is a Phase 3+ question.

4. **No shadow mode or staging dry run.** The reprocess is cheap (estimated $2.20 compute, ~minutes of wall time for in-place backfill), reversible (regression baseline captured first), and the normalizer is unit-tested. Shadow mode adds 1 week of calendar time for a one-time operation. Over-engineered.

5. **No scope additions during the sprint.** If something comes up that is not on the 7-item backlog below, it goes into a "post-MVP" list. The only exception is a canary test failure that reveals a bug requiring a fix. Everything else waits.

## Implementation Notes

### Prioritized Task Order

| #   | Item                                   | Effort   | Value    | Gate? | Notes                                                                                                                                                                                                                          |
| --- | -------------------------------------- | -------- | -------- | ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1   | **Canary validation**                  | 1 day    | Critical | YES   | Test normalizer on 10-20 recent JP tournaments. Compare our archetype labels to Limitless ground truth. Pass threshold: >95%. Fail at <90%: stop and debug.                                                                    |
| 2   | **Golden dataset fixtures**            | 0.5 day  | High     | No    | Capture 5-10 JP tournament expected outputs as regression test fixtures. These become the permanent safety net for future normalizer changes.                                                                                  |
| 3   | **Regression baseline capture**        | 2 hours  | High     | No    | Snapshot current JP meta shares (archetype distribution percentages) before reprocess. This is the "before" photo. Can be a simple SQL export.                                                                                 |
| 4   | **Historical JP reprocess (backfill)** | 1-2 days | Critical | No    | Reprocess existing JP tournament placements through the normalizer pipeline. In-place update using existing `raw_archetype` + `sprite_urls`. No re-scrape. Monitor `archetype_detection_method` distribution after completion. |
| 5   | **Meta recomputation for JP**          | 0.5 day  | Critical | No    | Re-run `compute_daily_snapshots` for JP region. Verify meta shares look correct against regression baseline. Spot-check top 5 archetypes.                                                                                      |
| 6   | **BO1 banner persistence fix**         | 0.5 day  | Medium   | No    | Make the BO1 context disclaimer non-dismissible on JP data views. Small UX trust signal.                                                                                                                                       |
| 7   | **CODEMAP.md + CLAUDE.md updates**     | 45 min   | Medium   | No    | Update current focus sections, add archetype detection notes. Runs in parallel with items 1-2.                                                                                                                                 |

**Total: ~5 working days.**

### Sequencing Rules

- Item 1 (canary) must pass before item 4 (reprocess) begins. This is the only hard gate.
- Items 2, 3, and 7 can run in parallel with item 1.
- Item 5 must follow item 4 (needs clean data).
- Item 6 is independent and can be done anytime.
- If item 1 fails at <90%: stop. Debug the sprite map or fallback logic. Fix. Re-run canary. Do not proceed to reprocess with broken detection.
- If item 1 lands at 90-95%: investigate the mismatches, add missing sprite map entries, re-run. Acceptable to spend 1 extra day here.

### Ship Criteria

Phase 2 is DONE when all of the following are true:

1. Canary test passes at >95% accuracy on 20 JP tournaments.
2. Historical JP placements have been reprocessed with new normalizer.
3. JP meta snapshots have been recomputed with clean data.
4. `archetype_detection_method` distribution shows <5% falling through to `text_label` (majority should be `sprite_lookup` or `auto_derive`).
5. Top 5 JP archetypes in meta dashboard match expected results from manual spot-check.
6. BO1 banner is persistent on JP views.

### What Success Looks Like

A competitive Pokemon TCG player visits `/meta/japan` on February 15 and sees:

- Accurate archetype names (not "Cinderace ex" artifacts or garbled text)
- Correct meta share percentages reflecting the real JP tournament landscape
- Sprite-based archetype display matching what they see on Limitless
- A BO1 context banner so they know to interpret the data correctly

That is the entire MVP. No predictions. No forecasts. No new dashboards. Just correct data in surfaces that already exist.

### Post-MVP Backlog (Ordered by Value)

| #   | Item                                      | Effort   | Target                 |
| --- | ----------------------------------------- | -------- | ---------------------- |
| 8   | Side-by-side JP vs EN meta comparison     | 2-3 days | Pre-April 10           |
| 9   | Lab Note: "Improved JP Meta Intelligence" | 1 day    | Pre-April 10           |
| 10  | Structured logging for pipeline           | 2-3 days | March                  |
| 11  | Cloud Run min_instances=0                 | 10 min   | Anytime (saves $62/mo) |
| 12  | Format Forecast widget                    | 5 days   | Post-April 10          |
| 13  | Prediction confidence system              | 5 days   | Post-April 10          |
| 14  | DATA_DICTIONARY.md + ADR                  | 2 days   | Post-April 10          |

### Current State Verification

As of this writing, the codebase confirms:

- `SPRITE_ARCHETYPE_MAP` has **49 entries** (up from 24), covering Mega variants, current JP meta, and historical VSTAR era (`/Users/danielsong/Development/tcg/trainerlab/apps/api/src/services/archetype_normalizer.py:36-104`).
- Priority chain is 4 levels: `sprite_lookup` -> `auto_derive` -> `signature_card` -> `text_label` (`archetype_normalizer.py:202-292`).
- `archetype_detection_method` is stored per placement for post-hoc audit.
- `archetype_sprites` DB table exists for runtime overrides with `seed_db_sprites` and `load_db_sprites` methods (`archetype_normalizer.py:124-200`).
- Migration 023 adds confidence column to `card_id_mappings` (`/Users/danielsong/Development/tcg/trainerlab/apps/api/alembic/versions/20260206_0001_023_add_card_mapping_confidence.py`).
- Pipeline router at `/Users/danielsong/Development/tcg/trainerlab/apps/api/src/routers/pipeline.py` has `discover-jp`, `process-tournament`, and `compute-meta` endpoints ready.
- No existing "reprocess" endpoint -- the backfill will need either a new admin endpoint or a script. This is the only net-new code required for Phase 2 and should be scoped as a management command, not a public API endpoint.

### The One Missing Piece

The pipeline has `discover-jp` (find new tournaments) and `process-tournament` (scrape a single tournament), but no "reprocess existing placements through the normalizer without re-scraping." The backfill task (item 4) will need a small script or management command that:

1. Queries existing JP placements with their `raw_archetype` and `sprite_urls`.
2. Runs each through `ArchetypeNormalizer.resolve()`.
3. Updates `archetype`, `archetype_detection_method` in place.
4. Commits in batches.

This is ~50-100 lines of Python. It is the only new code in the MVP. Everything else is validation, data operations, and configuration.

---

## Final Word

Phase 1 shipped in 1 day on a 2-week estimate. The remaining MVP is 5 days of focused work. The council is in universal agreement on the approach. The sprite map is 2x larger. The priority chain is proven. The schema supports auditability.

Ship the canary test. If it passes, reprocess. If it fails, fix and re-test. Do not add scope. Do not build new surfaces. Do not start prediction infrastructure. Get the data right, let it flow through existing pages, and move on to the April 10 fast-follows with 8 weeks of runway.

Every "yes" to a new feature right now is a "no" to shipping clean JP meta data sooner. The data is the product. Ship the data.
