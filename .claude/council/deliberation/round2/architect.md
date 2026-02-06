# Architect Round 2 — Challenge & Synthesis

## 1. What Phase 1 Changed From My Round 1 Position

Phase 1 (PR #312) implemented roughly 70% of my Round 1 schema and service design. Here is the precise delta.

### Implemented (matches my Round 1 proposal)

- **Migration 021**: `raw_archetype`, `raw_archetype_sprites` (JSONB), `archetype_detection_method` columns on `tournament_placements` -- matches my proposed schema almost exactly.
- **Migration 022**: `archetype_sprites` lookup table with `sprite_key`, `archetype_name`, `sprite_urls`, `pokemon_names` -- simpler than my proposed schema (no `version`, `is_active`, `first_seen_date`, `first_en_date`, `notes` columns), but structurally sound.
- **`ArchetypeNormalizer` service**: Priority chain (sprite_lookup -> auto_derive -> signature_card -> text_label) matches my proposed 4-strategy flow. The implementation is synchronous and in-memory rather than async+DB-backed, which is a good simplification for now.
- **`SPRITE_ARCHETYPE_MAP`**: ~24 entries seeded in code. This is the in-memory equivalent of my proposed `archetype_sprites` DB table seeding.
- **`sprite_urls: list[str]` on `LimitlessPlacement`**: Extraction plumbing from HTML to dataclass is complete.
- **`_extract_archetype_and_sprites_from_images()`**: Replaces the broken `img.pokemon` CSS selector.

### Not yet implemented (Phase 2 work)

1. **DB-backed sprite lookups**: `ArchetypeNormalizer` reads from `SPRITE_ARCHETYPE_MAP` dict, not from the `archetype_sprites` DB table. The table exists but is unused at runtime.
2. **`archetype_version` column**: My Round 1 proposed a version integer for tracking normalization rule changes. Not added -- and I now think this was over-engineering. Defer.
3. **`confidence` column on `card_id_mappings`**: Not added. Still needed for Phase 2.
4. **Historical data reprocessing**: No backfill of `raw_archetype` or `raw_archetype_sprites` for existing placements.
5. **Meta snapshot recomputation**: Downstream analysis still runs on mixed old/new archetype labels.

**Assessment**: The Phase 1 implementation made smart simplifications. The in-memory `SPRITE_ARCHETYPE_MAP` was the right call over DB lookups for a first pass -- it keeps the blast radius small and the code testable without DB fixtures. The DB table exists as infrastructure for when we need admin-editable mappings.

---

## 2. Challenges to Other Agents

### Strategist: "Wipe JP data and re-scrape" is the wrong approach

The Strategist proposed:

> DELETE FROM tournament_placements WHERE tournament_id IN (SELECT id FROM tournaments WHERE region = 'JP');

I maintain my Round 1 position: **do not wipe raw data.** Phase 1 gave us `raw_archetype` and `raw_archetype_sprites` columns. The correct Phase 2 approach is:

1. **Backfill** `raw_archetype_sprites` for existing JP placements by re-fetching standings pages (HTML only, not full re-scrape with decklists).
2. **Re-normalize** existing placements using `ArchetypeNormalizer.resolve()` and update `archetype` + `archetype_detection_method` in place.
3. **Recompute** meta snapshots from the corrected archetype labels.

This preserves decklists (expensive to re-fetch), avoids Limitless rate-limit risk from 3000+ full tournament scrapes, and lets us diff old vs new labels for validation. The Strategist's DELETE approach destroys data provenance -- we lose the ability to answer "what did we previously think this deck was?"

**Compromise**: If a specific tournament's HTML has changed such that sprite extraction is impossible from a re-fetch, then and only then re-scrape that tournament fully. Estimate: <5% of tournaments need full re-scrape.

### Skeptic: Root cause analysis is done -- stop blocking on it

The Skeptic demanded:

> Root cause analysis BEFORE re-scrape: Trace the Cinderace EX error end-to-end.

Phase 1 already traced and fixed the root cause: the `img.pokemon` CSS selector was broken, producing empty sprite lists, which cascaded into signature-card fallback failures for JP decks with unmapped card IDs. The new `_extract_archetype_and_sprites_from_images()` method is tested against real HTML fixtures (37 new tests). The Cinderace-class failure mode is structurally eliminated: sprite extraction now works, and the normalizer falls through to text_label rather than producing "Rogue" when everything else fails.

The Skeptic's demand for "validation gates at every layer" is reasonable but must be scoped. I support:

- Golden dataset tests (Craftsman's proposal) -- 5-10 real JP tournament fixtures.
- Post-reprocess sanity checks (meta share bounds, Unknown% < 5%).

I reject:

- Shadow mode running in parallel for a week. The new code IS the production code now. Shadow mode adds complexity for a system that already has 37 test cases validating the priority chain.
- Prometheus metrics for scraping success rate. We are in closed beta with <10 users. Structured logs (Operator's proposal) are sufficient.

### Craftsman: Golden datasets are the right investment

I fully endorse the Craftsman's golden dataset strategy. This is the single highest-value testing investment for Phase 2. Specific agreement:

```
tests/fixtures/jp_tournaments/
  city_league_real_01.html       # Real standings HTML
  city_league_real_01.json       # Expected: sprite_key, archetype, detection_method
```

The `expected.json` schema should include the detection method so we can assert not just that the archetype is correct, but that the normalizer used the right priority level. If sprite_lookup returns "Charizard ex" but we expected auto_derive, that signals a `SPRITE_ARCHETYPE_MAP` entry we did not intend.

### Scout: TCGdex shared card IDs do not solve the mapping problem

The Scout stated:

> TCGdex API: Multi-language API with **shared card IDs across languages** -- same card has same ID regardless of language.

This is misleading for our use case. TCGdex uses a single ID per card, but Limitless decklists use Limitless-internal IDs (e.g., `SV7-018`), not TCGdex IDs. The mapping problem is Limitless-JP-ID -> Limitless-EN-ID -> TCGdex-ID, and TCGdex cannot solve the first hop. We still need `card_id_mappings` for the Limitless-specific translation layer.

### Advocate: Prediction confidence is a Phase 3+ concern

The Advocate proposed a 3-tier confidence system (High/Medium/Low) for predictions. This requires:

- Historical accuracy data (we have none yet)
- BO1 vs BO3 correction factors (not modeled)
- Sample size thresholds (not defined)

This is all valid future work but depends on having 2-3 months of clean archetype data flowing through the pipeline first. Do not design confidence UX until the underlying data is trustworthy. The Strategist is right that premature predictions damage credibility.

---

## 3. Responses to Challenges Aimed at Me

### Skeptic: "Where do we store sprite-pair combos? New table or JSONB column?"

**Answer**: Both, and Phase 1 already implemented this.

- `tournament_placements.raw_archetype_sprites` (JSONB) stores the per-placement sprite list. This is the immutable record of what Limitless showed for that specific placement.
- `archetype_sprites` table stores the curated sprite-key -> archetype-name mappings. This is the normalization lookup table.

These serve different purposes. The JSONB column is raw data provenance. The table is configuration data. They should not be conflated.

### Craftsman: "How should sprite -> archetype mappings be stored? DB table? Config file? Live scrape?"

**Answer**: Hybrid, phasing from code to DB.

- **Now (Phase 1, done)**: `SPRITE_ARCHETYPE_MAP` dict in code. 24 entries. Deployable, testable, no DB dependency.
- **Phase 2**: Seed `archetype_sprites` DB table from the dict. Add admin endpoint to manage mappings. `ArchetypeNormalizer` reads from DB with in-memory cache (TTL 1 hour).
- **Never**: Live scrape from Limitless for mappings. We do not want runtime dependency on Limitless for normalization.

The migration path is:

```python
# Phase 2: ArchetypeNormalizer gains DB backend
class ArchetypeNormalizer:
    def __init__(self, session: AsyncSession | None = None, ...):
        self._db_cache: dict[str, str] = {}
        self._session = session

    async def _lookup_sprite(self, sprite_key: str) -> str | None:
        if sprite_key in self._db_cache:
            return self._db_cache[sprite_key]
        # Fallback to in-memory SPRITE_ARCHETYPE_MAP if no session
        if self._session is None:
            return SPRITE_ARCHETYPE_MAP.get(sprite_key)
        result = await self._session.execute(
            select(ArchetypeSprite.archetype_name)
            .where(ArchetypeSprite.sprite_key == sprite_key)
        )
        name = result.scalar_one_or_none()
        if name:
            self._db_cache[sprite_key] = name
        return name
```

### Operator: "Need `reprocessing_batch` table design for bulk operation progress tracking"

**Answer**: I do not think we need a dedicated table. The reprocessing operation is:

1. Query `tournament_placements WHERE raw_archetype_sprites IS NULL AND tournament.region = 'JP'` to find un-backfilled rows.
2. For each tournament, re-fetch standings HTML, extract sprites, update placements.
3. Run `ArchetypeNormalizer.resolve()` on all JP placements with sprites.
4. Recompute affected meta snapshots.

Progress tracking can use the existing `tournament_placements.archetype_detection_method` column: rows with `NULL` method are unprocessed, rows with a value are done. A simple `SELECT count(*) ... WHERE archetype_detection_method IS NULL` gives progress. Adding a `reprocessing_batch` table is infrastructure for a problem we do not have yet.

---

## 4. Key Tensions -- My Positions

### Historical data: wipe+re-scrape vs shadow mode vs backfill-in-place

**Position: Backfill-in-place.** Three-step process:

1. Re-fetch JP tournament standings HTML (lightweight, just the table page).
2. Extract sprites, populate `raw_archetype_sprites` and `raw_archetype`.
3. Re-run normalizer, update `archetype` and `archetype_detection_method`.

This is neither wipe nor shadow. It is surgical correction of existing rows. Estimated scope: ~2000-3000 JP placements across ~200 tournaments. At 0.5 req/sec rate limit, fetching 200 standings pages takes ~7 minutes.

### Archetype naming: auto-derive vs manual curation

**Position: Both, with a clear escalation path.** The current `derive_name_from_key` produces "Dragapult Pidgeot" from `dragapult-pidgeot`. This is reasonable but loses context (is it "Dragapult ex"? "Dragapult VSTAR"?). The priority chain already handles this correctly:

1. If `SPRITE_ARCHETYPE_MAP` has a curated entry -> use it (e.g., "dragapult-pidgeot" -> "Dragapult ex").
2. If not -> auto-derive "Dragapult Pidgeot" and log it.
3. Human reviews auto-derived names in the `archetype_sprites` table and corrects as needed.

The auto-derive names are acceptable defaults. They will not confuse users -- "Dragapult Pidgeot" communicates the deck identity even if it is not the community's preferred name. Curation is additive polish, not blocking work.

### Card mapping confidence: what is the schema?

**Position: Add `confidence` column to `card_id_mappings` in Phase 2 migration.**

```sql
ALTER TABLE card_id_mappings
ADD COLUMN confidence REAL DEFAULT 1.0
CHECK (confidence >= 0.0 AND confidence <= 1.0);

COMMENT ON COLUMN card_id_mappings.confidence IS
'1.0 = exact Limitless cross-reference, 0.8 = name+set match, 0.5 = heuristic';
```

This is a single column addition, no data migration needed (all existing rows default to 1.0). It enables two Phase 2 features:

- Filtering low-confidence mappings out of archetype detection (only use mappings with confidence >= 0.8 for signature card matching).
- Surfacing mapping quality in admin views for manual review.

---

## 5. Concrete Phase 2 Implementation Plan

Given Phase 1 is merged, Phase 2 should deliver three things in priority order:

### P0: Backfill existing JP placements (3-4 days)

1. **Migration 023**: Add `confidence` column to `card_id_mappings`.
2. **Backfill script** (`pipelines/backfill_jp_sprites.py`):
   - Fetch standings HTML for all JP tournaments where placements lack `raw_archetype_sprites`.
   - Extract sprites, update placement rows.
   - Run `ArchetypeNormalizer.resolve()` for each updated placement.
   - Log before/after archetype diff for validation.
3. **Recompute JP meta snapshots** for all affected date ranges.
4. **Golden dataset fixtures**: Capture 5 real JP tournament HTML files with hand-validated expected output.

### P1: DB-backed normalizer (2 days)

1. **Seed script**: Populate `archetype_sprites` table from `SPRITE_ARCHETYPE_MAP`.
2. **Admin endpoint**: `POST /api/v1/admin/archetype-sprites` for CRUD on mappings.
3. **Update `ArchetypeNormalizer`**: Add optional `AsyncSession` parameter, fall back to in-memory map when no session provided (keeps tests simple).

### P2: Observability (1 day)

1. **Structured logging**: Add JSON-formatted log entries for sprite extraction results (tournament_id, sprite_count, detection_method).
2. **Post-backfill validation query**: SQL script that reports archetype distribution before/after, flags any archetype with >50% meta share or >10% Unknown.

### Explicitly deferred to Phase 3+

- Prediction confidence UX (Advocate)
- BO1 vs BO3 correction factors (Scout)
- `reprocessing_batch` table (Operator)
- `archetype_version` column (my own Round 1 over-engineering)
- Format Forecast homepage widget (Advocate)
- Full `limitless.py` decomposition into submodules (Craftsman)

---

## Non-Negotiables

1. **Do not DELETE existing tournament data.** Backfill in place. Data provenance is a first-class architectural concern.
2. **Golden dataset tests before bulk backfill.** The Craftsman is right -- 5 fixtures with hand-validated expected output is the minimum bar before touching production data.
3. **`card_id_mappings.confidence` column in Phase 2.** Without it, we cannot distinguish exact mappings from heuristic guesses, and the Cinderace-class failure will repeat for the next ambiguous card.

## Concessions

1. I drop `archetype_version` and the version-based reprocessing infrastructure. Phase 1 proved that a simpler in-memory map works. We can add versioning if normalization rules change frequently enough to warrant it.
2. I drop shadow mode. The Skeptic's caution was warranted pre-Phase 1, but with 37 tests passing and the priority chain validated, the risk profile has changed.
3. I accept that `archetype_sprites` DB table usage is Phase 2, not Phase 1. The in-memory `SPRITE_ARCHETYPE_MAP` is sufficient for now.
