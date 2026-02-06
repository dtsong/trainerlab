# PRD: JP Archetype Data Pipeline — Phase 2

## Overview

Phase 2 validates and deploys the sprite-based archetype normalizer (built in Phase 1) against historical JP tournament data. The goal is accurate archetype labels across all JP placements, correct meta snapshots, and a small frontend improvement to surface sprite visuals and BO1 context. No ML, no predictions, no new surfaces — just correct data in existing pages.

## Goals

- Achieve >95% archetype labeling accuracy for JP tournaments
- Backfill all existing JP placements with correct archetypes via ArchetypeNormalizer
- Recompute JP meta snapshots with clean data
- Add sprite visuals and persistent BO1 context to the Japan meta page
- Maintain 85%+ backend test coverage

## Non-Goals

- ML-based meta share forecasting
- Format Forecast homepage widget
- Prediction confidence system
- New API endpoints for predictions
- Historical accuracy tracking
- Full limitless.py decomposition
- Staging environment or shadow mode

## Quality Gates

- `uv run pytest` — All tests pass (including new golden dataset + edge case tests)
- `uv run ruff check src` — Linting passes
- `uv run ruff format --check src` — Formatting passes
- `pnpm build` — Frontend builds
- `pnpm test` — Frontend tests pass
- Canary test: >95% accuracy on 10-20 recent JP tournaments
- sprite_lookup rate >70%, auto_derive <20%, text_label <10%

---

## User Stories

### US-001: Add composite sprite keys and sort sprite names

**Description:** As a developer, I want composite sprite keys (multi-sprite archetypes) in SPRITE_ARCHETYPE_MAP and sorted sprite names in `build_sprite_key` so that 97%+ of JP meta resolves via sprite_lookup.
**Agent:** Scout / Architect
**Acceptance Criteria:**

- [ ] Add `absol-mega-kangaskhan-mega` → "Mega Absol Box", `noctowl-ogerpon-wellspring` → "Tera Box", `joltik-pikachu` → "Joltik Box", `ho-oh-armarouge` → "Ho-Oh Armarouge"
- [ ] Add `lopunny-mega` → "Mega Lopunny ex"
- [ ] Sort sprite names alphabetically in `build_sprite_key` before joining
- [ ] Add `lucario-mega` → "Mega Lucario ex" proactively
- [ ] Tests for composite key resolution and sort-order independence

### US-002: Upgrade normalizer logging to structured INFO

**Description:** As an operator, I want INFO-level structured logs from ArchetypeNormalizer.resolve() so that every archetype resolution is auditable in Cloud Logging.
**Agent:** Operator / Architect
**Acceptance Criteria:**

- [ ] `auto_derive` resolutions logged at INFO (these need human review)
- [ ] `sprite_lookup` and `text_label` remain at DEBUG (high volume, low signal)
- [ ] Summary log after each tournament: "Normalized {n} placements: {sprite_lookup: x, auto_derive: y, ...}"
- [ ] All log entries include structured `extra` fields: sprite_key, archetype, method, raw_archetype

### US-003: Capture real golden dataset fixtures

**Description:** As a developer, I want 3-5 real Limitless JP tournament HTML files as test fixtures so that regression tests validate against actual HTML structure.
**Agent:** Craftsman
**Acceptance Criteria:**

- [ ] 3-5 real HTML files from Limitless saved in `tests/fixtures/golden/`
- [ ] Each with hand-validated `expected.json` (placement, archetype, detection_method, sprite_count)
- [ ] Parametrized pytest covering all fixtures
- [ ] At least 1 tournament with composite-key archetypes
- [ ] At least 1 from different time period (30+ days old)

### US-004: Add edge case tests

**Description:** As a developer, I want tests for known edge cases so that silent regressions are caught.
**Agent:** Craftsman
**Acceptance Criteria:**

- [ ] Test: `.webp` URL not matched by `.png` regex (document limitation)
- [ ] Test: URL with query params (`?v=2`) still extracts correctly
- [ ] Test: unmatched sprite URLs fall through to text_label
- [ ] Test: 3-sprite key produces correct composite
- [ ] Comment on `_FILENAME_RE` documenting the `.png`-only assumption

### US-005: Build shadow comparison script

**Description:** As a developer, I want a read-only script that compares current archetype labels against normalizer output for recent JP placements.
**Agent:** Craftsman
**Acceptance Criteria:**

- [ ] Script at `apps/api/scripts/shadow_compare.py`
- [ ] Read-only (no writes)
- [ ] Accepts `--days` flag (default 30)
- [ ] Outputs JSON report: total, changed count, detection method transitions
- [ ] Go/no-go threshold documented: <5% = proceed, >20% = investigate

### US-006: Build reprocess-archetypes pipeline endpoint

**Description:** As an operator, I want a paginated reprocess endpoint that updates existing JP placements through the normalizer without re-scraping.
**Agent:** Architect / Operator
**Acceptance Criteria:**

- [ ] `POST /api/v1/pipeline/reprocess-archetypes` endpoint
- [ ] Request: region, batch_size, cursor, force, dry_run
- [ ] Response: processed, updated, skipped, errors, next_cursor, total_remaining
- [ ] For placements with `raw_archetype_sprites`: resolve from stored sprites
- [ ] For placements without sprites: re-fetch standings HTML, extract sprites
- [ ] Respects Limitless rate limit (2s delay between tournament fetches)
- [ ] Dry-run mode logs changes without writing
- [ ] Unit tests with mocked DB and HTTP

### US-007: Execute canary validation

**Description:** As a developer, I want to validate the normalizer against 10-20 recent JP tournaments before bulk reprocess.
**Agent:** Skeptic / Strategist
**Acceptance Criteria:**

- [ ] Process 10-20 recent JP tournaments through normalizer
- [ ] Report: detection method distribution, accuracy vs Limitless ground truth
- [ ] Pass: >95% accuracy, sprite_lookup >70%, auto_derive <20%
- [ ] Fail action documented: fix sprite map, re-run canary
- [ ] Hyphenated name error rate quantified

### US-008: Execute historical backfill

**Description:** As an operator, I want to reprocess all JP tournament placements with the new normalizer pipeline.
**Agent:** Operator
**Acceptance Criteria:**

- [ ] Dry-run completes without errors
- [ ] Production reprocess updates all JP placements
- [ ] archetype_detection_method populated on every row
- [ ] No placements deleted (backfill in place only)
- [ ] Cloud SQL PITR available as rollback

### US-009: Recompute JP meta snapshots

**Description:** As a developer, I want JP meta snapshots recomputed with clean archetype data.
**Agent:** Architect
**Acceptance Criteria:**

- [ ] `compute_daily_snapshots(regions=["JP"])` runs for all affected dates
- [ ] Top 5 JP archetypes match expected results from spot-check
- [ ] "Rogue"/"Unknown" rate <10% across all JP placements
- [ ] Meta shares within 3% of Limitless for top archetypes

### US-010: CODEMAP.md full refresh

**Description:** As a developer, I want CODEMAP.md to accurately reflect the codebase so that navigation is reliable.
**Agent:** Chronicler
**Acceptance Criteria:**

- [ ] All 33 models documented (currently 15)
- [ ] All 25 services documented (currently 13)
- [ ] All 19 routers documented (currently 12)
- [ ] All 19 schemas documented (currently 12)
- [ ] All 9 pipelines documented (currently 3)
- [ ] Migration count updated to 23

### US-011: ArchetypeSprites frontend component

**Description:** As a user, I want to see Pokemon sprite images next to archetype names so I can visually identify decks.
**Agent:** Advocate
**Acceptance Criteria:**

- [ ] `ArchetypeSprites` component at `/apps/web/src/components/meta/ArchetypeSprites.tsx`
- [ ] Props: `spriteUrls: string[]`, `archetypeName: string`, `size?: "sm" | "md"`
- [ ] Renders 1-3 sprites inline, lazy-loaded, with explicit width/height
- [ ] Falls back to no image on load error (not broken icon)
- [ ] Alt text with archetype name for accessibility
- [ ] Integrated into MetaPieChart legend, MetaDivergenceComparison rows
- [ ] `sprite_urls` added to `ApiArchetype` in shared-types

### US-012: BO1 banner persistence + section reorder

**Description:** As a user, I want BO1 context that persists across visits and divergence data above raw data.
**Agent:** Advocate
**Acceptance Criteria:**

- [ ] BO1 banner dismissal stored in localStorage
- [ ] "(BO1)" labels on all Japan page section headers
- [ ] MetaDivergenceComparison moved from Section 4 to Section 1
- [ ] No layout regressions on mobile

---

## Technical Notes

### Architecture decisions

- ArchetypeNormalizer priority chain: sprite_lookup → auto_derive → signature_card → text_label
- Sprite map: hybrid storage (code seeds DB, DB overrides code at runtime)
- Reprocess: paginated via Cloud Tasks, ~150 batches at 200 placements each
- No Terraform changes needed

### Data model (existing, no changes)

- `tournament_placements`: raw_archetype, raw_archetype_sprites (JSONB), archetype_detection_method
- `archetype_sprites`: sprite_key (unique), archetype_name, sprite_urls, pokemon_names
- `card_id_mappings`: confidence column (migration 023)

### Dependencies

- Limitless HTML structure (sprites at `r2.limitlesstcg.net/pokemon/gen9/{name}.png`)
- Cloud Tasks queue for batch orchestration
- Cloud SQL PITR for rollback safety
