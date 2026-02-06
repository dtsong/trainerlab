# Craftsman Round 2 -- Phase 1 Code Review & Phase 2 Priorities

## 1. Code Quality Assessment of Phase 1

Phase 1 is solid work. The implementation follows the codebase's existing patterns and the architecture is clean. Specific observations from the actual code:

**What landed well:**

- `ArchetypeNormalizer` at `/Users/danielsong/Development/tcg/trainerlab/apps/api/src/services/archetype_normalizer.py` is a focused 142-line class with clear single responsibility. The priority chain (sprite_lookup, auto_derive, signature_card, text_label) is explicit in the `resolve()` method and easy to follow. The return tuple `(archetype, raw_archetype, detection_method)` gives callers full provenance -- exactly what the Architect proposed.

- Dependency injection is done right: `ArchetypeNormalizer.__init__` accepts optional `detector` and `sprite_map`, making it trivially testable. The tests at `/Users/danielsong/Development/tcg/trainerlab/apps/api/tests/test_archetype_normalizer.py` exploit this with `MagicMock` detectors and custom sprite maps.

- `_extract_archetype_and_sprites_from_images()` in `/Users/danielsong/Development/tcg/trainerlab/apps/api/src/clients/limitless.py` (line 1313) returns both the text archetype AND sprite URLs, preserving backward compatibility via `_extract_archetype_from_images` wrapper. EN pipeline is unaffected -- the normalizer only activates for `tournament.region == "JP"` (line 598 of `tournament_scrape.py`).

- The DB model at `/Users/danielsong/Development/tcg/trainerlab/apps/api/src/models/tournament_placement.py` has a proper `CheckConstraint` on `archetype_detection_method` limiting values to `('sprite_lookup', 'auto_derive', 'signature_card', 'text_label')`. This is the pit of success: invalid detection methods are rejected at the database level.

**Concerns (actionable, not blocking):**

1. **`derive_name_from_key` destroys hyphenated Pokemon names.** `"chien-pao-baxcalibur"` becomes `"Chien Pao Baxcalibur"` -- three words, losing the hyphen in "Chien-Pao". The test at line 78 documents this behavior but it produces incorrect names. This is acceptable for auto_derive (it is a best-effort fallback) but should be documented as a known limitation. The real fix is adding these to `SPRITE_ARCHETYPE_MAP` when they appear.

2. **`SPRITE_ARCHETYPE_MAP` is in-memory code, not DB-backed.** The map has ~24 entries hardcoded in Python. Adding new entries requires a code deploy. This was a deliberate Phase 1 decision (the Architect's `archetype_sprites` DB table is Phase 2), and it is the right call for now -- ship the simple thing, migrate to data later. But the migration path needs to be clear.

3. **The `_parse_jp_placement_row` method (line 1603) calls `_extract_archetype_and_sprites_from_images` for the text archetype even when sprites produce a usable name.** This means `placement.archetype` is always the slash-joined text form (`"Grimmsnarl / Froslass"`), which only gets normalized downstream by `ArchetypeNormalizer`. This is fine architecturally (raw in, normalized out), but it means the `archetype` field on `LimitlessPlacement` is misleadingly named -- it holds the raw text, not a normalized archetype. A `raw_archetype_text` name would be clearer.

4. **No logging in `ArchetypeNormalizer.resolve()`.** When debugging production issues, we will want to know which priority step fired for each placement. A single `logger.debug` call per resolution would cost nothing and save hours later.

## 2. Test Coverage Gaps

The 37 new tests cover the critical happy paths well. The end-to-end test at `TestJPPipelineEndToEnd.test_full_pipeline_all_rows` (line 1094 of `test_limitless_scraper.py`) is particularly valuable -- it chains HTML fixture parsing through `ArchetypeNormalizer`, asserting the full pipeline produces correct results. This is exactly the pattern I advocated in Round 1.

**What is missing:**

- **No golden dataset from a real Limitless page.** The fixture at `/Users/danielsong/Development/tcg/trainerlab/apps/api/tests/fixtures/limitless_jp_standings.html` is a synthetic 4-row HTML file. It covers the key cases (r2 CDN URLs, old URL patterns, text-only rogue) but it does not represent real Limitless HTML with its full DOM structure, JavaScript-injected attributes, pagination, or edge cases like 3-sprite archetypes. Phase 2 must capture 3-5 real tournament pages (anonymized player names) as golden datasets.

- **No test for `normalizer.resolve()` when `sprite_urls` has URLs but none match the `_FILENAME_RE` regex.** For example, a URL like `https://example.com/images/sprite?name=charizard` would fail regex extraction, returning empty sprite_key, falling through to text_label. This silent degradation path needs a test.

- **No test for the `_create_placement` integration in `TournamentScrapeService`.** The code at lines 675-707 of `tournament_scrape.py` that wires `normalizer.resolve()` into the DB model creation is only tested indirectly via the end-to-end test. A targeted unit test for `_create_placement` with a mock normalizer would catch wiring bugs (e.g., wrong argument order, missing fields).

- **No regression test for the original Cinderace EX bug.** We fixed the sprite extraction, but there is no test that says "given a decklist containing JP Cinderace card IDs and these sprite URLs, the archetype must resolve to Cinderace ex, not Rogue." This specific regression test should be the first thing written in Phase 2.

- **Sprite URL format evolution.** The regex `_FILENAME_RE = re.compile(r"/([a-zA-Z0-9_-]+)\.png")` only matches `.png` files. If Limitless switches to `.webp` or adds query parameters (`?v=2`), extraction breaks silently. Need at least a comment documenting this assumption and a test for the edge case.

## 3. Challenges to Other Agents

### Skeptic: "Full audit before re-scrape"

**Their position:** Trace Cinderace EX through the entire pipeline before any reprocessing.
**My response:** Modify.

The Skeptic's instinct is right -- understand the failure before scaling the fix. But their Round 1 position was written before Phase 1 shipped. Phase 1 already addressed their core concern: sprite extraction now works, the priority chain has clear provenance tracking (`archetype_detection_method` column), and 37 tests validate the new path.

What remains valid from the Skeptic's position: canary testing on 10 real JP tournaments before full reprocess. This aligns with my golden dataset recommendation. What is no longer valid: the call for a full HTML structure audit. We have a working extractor with tests. The audit should happen _through testing_, not as a separate gating document.

Concrete proposal: the next PR should include a **shadow mode comparison** script that runs the new normalizer against the last 30 days of existing JP placements (reading, not writing) and produces a diff report: how many archetypes change, what the old vs new labels are, and which detection method fired. This satisfies the Skeptic's audit requirement with actual data, not speculation.

### Advocate: Frontend display needs

**Their position:** Sprite-first display, confidence badges, progressive disclosure.
**My response:** Defer (not yet actionable).

The Advocate's UX vision is compelling but depends on Phase 2 backend work: the `archetype_sprites` DB table with canonical names, sprite URLs for display, and confidence metadata. Phase 1 gives us `sprite_urls: list[str]` on placements and `archetype_detection_method`, which is sufficient for a basic sprite display component. But confidence scoring and the Format Forecast widget need the full normalization table.

What I need from Advocate now: a definitive answer on archetype naming convention. The current `SPRITE_ARCHETYPE_MAP` uses names like "Charizard ex" (with lowercase "ex"). Is this the convention users expect? "Lost Zone Giratina" vs "Giratina VSTAR" -- is the distinction clear to the target audience? This naming decision affects every downstream display and should be locked before Phase 2 seeds more data.

### Architect: Three-layer architecture

**Their position:** Ingestion, normalization, analysis as distinct layers.
**My response:** Maintain -- Phase 1 implemented exactly this.

The `LimitlessPlacement.sprite_urls` captures raw ingestion data. `ArchetypeNormalizer.resolve()` is the normalization layer. Analysis (MetaService) remains untouched. The Architect's design was sound and Phase 1 proves it works in practice. Phase 2 should complete the picture by making `SPRITE_ARCHETYPE_MAP` database-backed.

## 4. Key Testing Priorities for Phase 2

### Golden dataset capture

Process: use the existing `LimitlessClient` to fetch 5 real JP tournament standings pages. Save the raw HTML. Hand-verify each placement's archetype by inspecting the Limitless page visually. Store as `tests/fixtures/golden/jp_city_league_{id}.html` + `.json` expected output. Parametrize a single test function over all golden files. This becomes the regression suite -- any parser change that breaks golden output is a test failure.

Target: 5 tournaments minimum, covering at least one with 3-sprite archetype, one with all-known archetypes, one with mostly unknown archetypes, and one Champions League format.

### Shadow mode comparison

Implementation sketch (not a production feature, a one-off script):

```python
async def shadow_compare(session: AsyncSession, normalizer: ArchetypeNormalizer):
    """Compare current archetype labels vs normalizer output."""
    placements = await session.execute(
        select(TournamentPlacement)
        .join(Tournament)
        .where(Tournament.region == "JP")
        .where(Tournament.date >= date.today() - timedelta(days=30))
    )
    diffs = []
    for p in placements.scalars():
        new_archetype, _, method = normalizer.resolve(
            p.raw_archetype_sprites or [],
            p.raw_archetype or p.archetype,
        )
        if new_archetype != p.archetype:
            diffs.append({
                "tournament_id": p.tournament_id,
                "placement": p.placement,
                "old": p.archetype,
                "new": new_archetype,
                "method": method,
            })
    return diffs
```

This produces a concrete diff report. If >20% of archetypes change, we investigate before reprocessing. If <5% change, we are confident the normalizer is consistent with existing data.

### Reprocess validation

Before reprocess: capture a baseline snapshot of JP archetype distribution (archetype name, count, meta share). After reprocess: compare. Alert on any archetype that moves more than 10 percentage points. This is a data quality gate, not a test -- it runs as part of the reprocess pipeline, not CI.

## 5. Concrete Next PR (Phase 2a)

The next PR should contain exactly these items:

1. **Golden dataset fixtures** -- 3-5 real Limitless JP tournament HTML files + expected JSON, with parametrized tests.

2. **Cinderace regression test** -- specific test case reproducing the original bug with JP card IDs and asserting correct archetype resolution.

3. **Shadow comparison script** -- `apps/api/scripts/shadow_compare.py` that reads existing JP placements and produces a diff report (read-only, no writes).

4. **Logging in `ArchetypeNormalizer.resolve()`** -- single `logger.debug` line per resolution showing sprite_key, method, and result.

5. **Migrate `SPRITE_ARCHETYPE_MAP` to `archetype_sprites` DB table** -- seed with current 24 entries, add admin endpoint for CRUD. The normalizer falls back to the in-memory map if DB lookup fails (backward compatible).

6. **`.png` assumption documentation** -- add a comment on `_FILENAME_RE` noting the `.png` assumption, and a test for a non-.png URL to document graceful degradation.

Items 1-4 are testing infrastructure (low risk, high value). Items 5-6 are incremental improvements. This keeps the PR focused and reviewable.

**Non-negotiables for Phase 2:**

- Golden datasets must be captured before any production reprocess.
- Shadow comparison must show <20% label churn before proceeding.
- The Cinderace regression test must pass.
