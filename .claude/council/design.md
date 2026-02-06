# Design Document: JP Archetype Data Pipeline — Phase 2

**Date:** 2026-02-06
**Council Session:** jp-archetype-data-pipeline-overhaul
**Agents:** Architect, Skeptic, Scout, Strategist, Craftsman, Advocate, Operator, Chronicler

---

## Overview

Phase 1 (PR #312) delivered the ArchetypeNormalizer service, sprite extraction from Limitless HTML, provenance columns on tournament_placements, and the archetype_sprites lookup table. Phase 2 is a **surgical data correction**: validate the normalizer against real JP tournaments, backfill existing placements with correct archetype labels, recompute meta snapshots, and ship a small frontend PR with sprite display and UX improvements.

The council reached **unanimous convergence** on: backfill in place (no data wipe), canary test gate (>95% accuracy), golden dataset fixtures before reprocess, structured logging before reprocess, and deferring ML predictions and the Format Forecast widget to post-April 10.

**Timeline:** 5 working days (~Feb 14 target). 8-week buffer before April 10 rotation.

---

## Architecture

### Data Flow (Phase 2 Reprocess)

```
[1] Query JP tournaments from DB
    |
    v
[2] For each tournament (paginated, 0.5 req/sec):
    |-- Re-fetch standings HTML from Limitless (1 GET per tournament)
    |-- Extract sprite URLs via _extract_archetype_and_sprites_from_images()
    |-- For each placement:
    |    |-- build_sprite_key(sprite_urls) → e.g. "charizard-pidgeot"
    |    |-- ArchetypeNormalizer.resolve(sprite_urls, raw_archetype)
    |    |-- UPDATE tournament_placements SET archetype, raw_archetype_sprites,
    |    |     archetype_detection_method
    |-- COMMIT batch
    v
[3] compute_daily_snapshots(regions=["JP"]) → Updated meta snapshots
```

### Key Design Decisions

- **Backfill in place, not wipe.** Preserves decklists (expensive to re-fetch), maintains data provenance, enables old-vs-new label diffing for validation.
- **No new migrations.** All columns exist (021: provenance, 022: archetype_sprites, 023: confidence).
- **Paginated reprocess.** Each batch processes 100-200 placements within Cloud Run's 300s timeout. Cloud Tasks orchestrates batches at 0.5 req/sec.
- **Reprocess endpoint, not one-off script.** Idempotent, re-runnable, with dry-run mode.

### New Code

| File                                    | Action | Purpose                             |
| --------------------------------------- | ------ | ----------------------------------- |
| `src/pipelines/reprocess_archetypes.py` | Create | Paginated reprocess pipeline        |
| `src/routers/pipeline.py`               | Modify | Add `reprocess-archetypes` endpoint |
| `src/schemas/pipeline.py`               | Modify | Add request/response schemas        |
| `src/services/archetype_normalizer.py`  | Modify | Upgrade logging, add composite keys |
| `src/services/tournament_scrape.py`     | Modify | Detection method summary log        |

---

## Risk Assessment

### Pre-Reprocess Gates (Skeptic — Non-negotiable)

| Gate                                   | Threshold | Fail Action                  |
| -------------------------------------- | --------- | ---------------------------- |
| Canary accuracy (10-20 JP tournaments) | >95%      | Fix sprite map gaps, re-test |
| sprite_lookup rate                     | >70%      | Expand SPRITE_ARCHETYPE_MAP  |
| auto_derive fallback rate              | <20%      | Add missing curated entries  |
| text_label fallback rate               | <10%      | Investigate HTML extraction  |
| Hyphenated name errors in auto_derive  | <5%       | Fix or accept as tolerable   |

### Residual Risks (Accepted)

| Risk                                          | Likelihood | Impact | Mitigation                                                |
| --------------------------------------------- | ---------- | ------ | --------------------------------------------------------- |
| Limitless HTML structure changes on old pages | Low        | Medium | Canary test covers current structure; skip failures       |
| Rate limiting from Limitless                  | Medium     | Low    | 2s delay between requests; ~7 min total                   |
| New sprite keys not in map                    | Certain    | Low    | auto_derive fallback + INFO logging for curation          |
| `derive_name_from_key` hyphenation bug        | Medium     | Low    | Masked by expanded sprite map; log auto_derive for review |

### Rollback

- **Bad reprocess:** Cloud SQL PITR (14-day retention, sub-minute granularity)
- **Bad deploy:** Redeploy previous image from Artifact Registry
- **Bad migration:** `alembic downgrade` functions implemented

---

## Data Quality — Sprite Map Coverage (Scout)

### Current State: 86.25% sprite_lookup coverage

The expanded SPRITE_ARCHETYPE_MAP (47 entries) covers the top single-sprite archetypes. The remaining gap is **multi-sprite composite keys** (11.23% of JP meta):

| Archetype       | Share | Composite Key                | Needs Map Entry |
| --------------- | ----- | ---------------------------- | --------------- |
| Mega Absol Box  | 7.24% | `absol-mega-kangaskhan-mega` | YES             |
| Tera Box        | 2.28% | `noctowl-ogerpon-wellspring` | YES             |
| Joltik Box      | 1.47% | `joltik-pikachu`             | YES             |
| Ho-Oh Armarouge | 0.24% | `ho-oh-armarouge`            | YES             |

**Required fix:** Add composite keys + sort sprite names in `build_sprite_key` to eliminate order-dependence (1-line change: `names.sort()` before join).

**Also missing:** `lopunny-mega` → "Mega Lopunny ex" (0.51%).

### Naming Mismatches (fix post-reprocess in DB table)

| Key          | Current         | Community Name                |
| ------------ | --------------- | ----------------------------- |
| `grimmsnarl` | "Grimmsnarl ex" | "Marnie's Grimmsnarl ex"      |
| `zoroark`    | "Zoroark ex"    | "N's Zoroark ex"              |
| `alakazam`   | "Alakazam ex"   | "Alakazam Powerful Hand"      |
| `crustle`    | "Crustle ex"    | "Crustle Mysterious Rock Inn" |
| `noctowl`    | "Noctowl Box"   | "Tera Box"                    |

---

## Quality Strategy (Craftsman)

### 4 Quality Gates Before Reprocess

1. **Real golden datasets** — 3-5 actual Limitless HTML pages (not synthetic), hand-validated, stored in `tests/fixtures/golden/`
2. **Cinderace regression suite** — Existing 3 tests must remain green through all changes
3. **Shadow comparison script** — Read-only diff of last 30 days. <5% change = proceed, >20% = investigate
4. **Canary test** — Full pipeline on 10-20 real JP tournaments, >95% accuracy

### New Tests

- `test_archetype_edge_cases.py` — `.webp` URLs, query-param URLs, unmatched sprites, 3-sprite keys
- Document `.png`-only regex limitation with comment + canary test

---

## User Experience (Advocate)

### 3 Frontend Deliverables (Parallel with Backend)

1. **`ArchetypeSprites` component** — 24-32px inline sprite images next to archetype names. Used in MetaPieChart legend, MetaDivergenceComparison rows, CityLeagueResultsFeed badges. Falls back gracefully to no image.

2. **BO1 banner persistence** — Store dismissal in `localStorage` instead of `useState`. Add persistent "(BO1)" labels to all Japan page section headers.

3. **Japan page section reorder** — Move JP vs EN Divergence from Section 4 to Section 1. Lead with "what's different" (insight), follow with "here's the numbers" (evidence).

### Backend Requirement

`ApiArchetype` response must include `sprite_urls: string[]`. Join through `archetype_sprites` table or aggregate from recent placements.

### Not Included

- No Format Forecast widget (post-April 10)
- No prediction confidence badges
- No homepage changes
- No new API endpoints for predictions

---

## Operations (Operator)

### Deployment: 8-Step Runbook

1. **Merge PR** → CI auto-deploys via GitHub Actions
2. **Verify deploy** → Health check, migration status
3. **Canary: process 10-20 fresh JP tournaments** → Verify detection method distribution
4. **Run validation script** → `validate_jp_pipeline.py --tournaments 20`
5. **Seed archetype_sprites DB table** → `POST /admin/archetype-sprites/seed`
6. **Dry-run reprocess** → Review what WOULD change
7. **Production reprocess** → ~150 batches, ~30 min wall time, <$3 compute
8. **Post-reprocess validation** → Recompute meta, spot-check top 5 archetypes

### Infrastructure: No Changes

- Cloud Run: 300s timeout, 1-10 instances (sufficient for paginated reprocess)
- Cloud Tasks: 0.5/sec, 2 concurrent (handles batch orchestration)
- Cloud SQL: PITR enabled, 14-day retention (rollback safety net)
- Cost: ~$80-85/month ongoing, ~$3 one-time reprocess

---

## Documentation (Chronicler)

### Before Phase 2 Code (60-90 min)

- **CODEMAP.md full refresh** — File has drifted to 55% coverage (15/33 models, 13/25 services documented). Full regeneration, not patch.
- **CLAUDE.md** — Already updated. No changes needed.

### During Phase 2 (before PR review)

- **ADR-001**: Sprite-based archetype detection decision record (20 min)
- **DATA_DICTIONARY.md**: Archetype detection methods, sprite key format, provenance columns (30 min)

### Post-Phase 2

- **SPEC.md** Section 7.2 update

---

## Tension Resolutions

| Tension               | Agents                                     | Resolution                                               | Reasoning                                          |
| --------------------- | ------------------------------------------ | -------------------------------------------------------- | -------------------------------------------------- |
| Wipe vs backfill      | Strategist vs Architect+Skeptic+Operator   | Backfill in place                                        | Faster, cheaper, preserves provenance              |
| Full audit vs canary  | Skeptic vs Strategist                      | Canary gate within Phase 2                               | Phase 1 already fixed root cause; canary validates |
| Shadow mode vs canary | Craftsman vs Architect+Operator+Strategist | Canary + provenance column                               | Shadow mode overengineered for closed beta         |
| Doc timing            | Chronicler vs Strategist                   | CODEMAP.md (60-90 min) before code; ADR/DATA_DICT during | Minimum viable, maximum leverage                   |
| Frontend timing       | Advocate vs Strategist                     | Small parallel PR (sprites + BO1 + reorder)              | No new endpoints; uses existing Phase 1 data       |
| Format Forecast       | Advocate vs Strategist                     | Deferred to post-April 10                                | Requires prediction infra that doesn't exist       |
| Composite sprite keys | Scout finding                              | Add 4 composite entries + sort sprite names              | Closes 11.23% coverage gap                         |

## Decision Log

| Decision                 | Options Considered                                | Chosen                               | Reasoning                                       |
| ------------------------ | ------------------------------------------------- | ------------------------------------ | ----------------------------------------------- |
| Historical data approach | Wipe+re-scrape, shadow mode, backfill in place    | Backfill in place                    | Preserves decklists, enables diffing, faster    |
| Validation approach      | Full forensic audit, shadow mode, canary test     | Canary test (10-20 tournaments)      | Right balance of safety and velocity            |
| Monitoring               | Prometheus, structured logging, log-based metrics | Structured logging                   | Sufficient for closed beta, no infra overhead   |
| Sprite map storage       | Code-only, DB-only, hybrid                        | Hybrid (code seeds DB)               | Code for testing, DB for runtime overrides      |
| Reprocess infrastructure | One-off script, admin endpoint, pipeline endpoint | Pipeline endpoint (paginated)        | Idempotent, re-runnable, fits Cloud Tasks model |
| Frontend scope           | Full redesign, new widgets, minimal PR            | Minimal PR (sprites + BO1 + reorder) | Maximum user value for minimum scope            |
| Timeline                 | 6 weeks, 4 weeks, 1 week                          | 5 working days                       | Phase 1 velocity proves team executes fast      |
