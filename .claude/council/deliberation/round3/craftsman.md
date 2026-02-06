# Craftsman Final Position -- JP Archetype Pipeline Phase 2

## Revised Recommendation

Phase 1 shipped clean, well-structured code. Phase 2's testing strategy should capitalize on the strong foundation rather than rebuild it. The highest-leverage work is replacing synthetic fixtures with real Limitless HTML, adding targeted edge-case tests for known blind spots (`.webp` URLs, query-param URLs, unmatched sprites), and upgrading `resolve()` logging from `debug` to `info` so production issues are diagnosable without reconfiguring log levels. A shadow comparison script gives us a data-driven go/no-go signal before reprocessing historical data.

Golden datasets, the Cinderace regression suite, and the shadow comparison script must all land and pass before any production reprocess touches JP data.

## Concessions Made

1. **Dropped full shadow mode (1 week parallel run).** Round 2 I proposed running old and new pipelines in parallel for a week. I now accept that a read-only comparison script against the last 30 days of data is sufficient -- it provides the same insight at a fraction of the cost. The canary test (>95% match on 10 tournaments) plus the shadow diff script replaces the full shadow mode.

2. **Dropped the `raw_archetype_text` rename.** In Round 2, I noted that `LimitlessPlacement.archetype` holds raw text, not a normalized archetype, and suggested renaming to `raw_archetype_text`. This is a cosmetic concern that adds churn without reducing risk. The field semantics are clear from the `resolve()` call site.

3. **Accepted Strategist's phasing.** Golden datasets and canary validation gate the reprocess, not the other way around. This is the right order.

## Non-Negotiables

These quality gates **must pass** before any historical reprocess:

### 1. Real Golden Datasets (not synthetic)

The current fixtures at `apps/api/tests/fixtures/jp_tournaments/` are hand-written HTML. They exercise the parser but they do not represent the real Limitless DOM structure (JavaScript-injected attributes, pagination hints, edge-case formatting).

**Requirement:** Capture 3-5 real JP tournament HTML pages from Limitless. Store at `apps/api/tests/fixtures/golden/`. Hand-verify each placement against the live page. Store expected output as JSON alongside each HTML file.

**Coverage targets for golden dataset:**

- At least 1 tournament with a 3-sprite archetype (if they exist in real data)
- At least 1 tournament with mostly-known archetypes (high sprite_lookup rate)
- At least 1 tournament with several unknown/rogue archetypes (auto_derive and text_label paths)
- At least 1 Champions League format (different structure from City League)

### 2. Cinderace Regression Suite

The existing `TestCinderaceRegression` class at `apps/api/tests/test_jp_golden_dataset.py:135` is good -- it covers single Cinderace, Cinderace+partner, and Cinderace-in-golden-dataset. This is already landed. **Non-negotiable: this test class must remain green through all Phase 2 changes.** Any refactoring of `resolve()` or `SPRITE_ARCHETYPE_MAP` that breaks Cinderace detection is a blocker.

### 3. Shadow Comparison Script with Clear Threshold

A read-only script that runs `ArchetypeNormalizer.resolve()` against the last 30 days of JP placements and reports:

- Total placements evaluated
- Number/percentage of archetype label changes
- Breakdown by detection method (how many shift from text_label to sprite_lookup, etc.)
- Top 10 specific label changes (old -> new)

**Go/no-go threshold:** If >20% of archetypes change, investigate before proceeding. If <5% change, proceed with confidence. Between 5-20%, review the specific changes and make a judgment call.

### 4. Canary Test (>95% Accuracy)

Run the full pipeline against 10 real JP tournaments. At least 95% of placements must resolve to the correct archetype (verified against Limitless page visuals). This tests the entire chain: HTTP fetch, HTML parsing, sprite extraction, `build_sprite_key`, sprite map lookup, `resolve()` priority chain.

## Implementation Notes

### Test Files and Patterns

**New test file:** `apps/api/tests/test_archetype_edge_cases.py`

```python
class TestBuildSpriteKeyEdgeCases:
    """Edge cases in sprite key extraction."""

    def test_webp_url_not_matched(self) -> None:
        """Verify .webp URLs are handled (currently ignored by .png regex)."""
        urls = ["https://r2.limitlesstcg.net/pokemon/gen9/charizard.webp"]
        key = ArchetypeNormalizer.build_sprite_key(urls)
        # Document current behavior: .webp is NOT extracted
        assert key == ""

    def test_url_with_query_params(self) -> None:
        """Verify query params don't break extraction."""
        urls = ["https://r2.limitlesstcg.net/pokemon/gen9/charizard.png?v=2"]
        key = ArchetypeNormalizer.build_sprite_key(urls)
        # Current regex handles this correctly (stops at .png)
        assert key == "charizard"

    def test_resolve_unmatched_sprites_falls_to_text(self) -> None:
        """When sprite URLs exist but none match regex, fall to text_label."""
        normalizer = ArchetypeNormalizer()
        archetype, raw, method = normalizer.resolve(
            ["https://example.com/mystery-image"],  # no .png
            "Charizard ex",
        )
        assert method == "text_label"
        assert archetype == "Charizard ex"

    def test_three_sprite_url_key(self) -> None:
        """Three sprites produce a three-part key."""
        urls = [
            "https://example.com/a.png",
            "https://example.com/b.png",
            "https://example.com/c.png",
        ]
        key = ArchetypeNormalizer.build_sprite_key(urls)
        assert key == "a-b-c"
```

These tests document known limitations (`.webp` gap) and verify graceful degradation paths. When Limitless migrates to `.webp`, the first test will tell us to update `_FILENAME_RE`.

**Existing test files to preserve:**

- `/Users/danielsong/Development/tcg/trainerlab/apps/api/tests/test_archetype_normalizer.py` -- 37 tests covering core functionality, sprite map, DB sprites
- `/Users/danielsong/Development/tcg/trainerlab/apps/api/tests/test_jp_golden_dataset.py` -- Parametrized golden tests + Cinderace regression suite

**Golden dataset fixture format:**

```
apps/api/tests/fixtures/golden/
  jp_city_league_001.html     # Real HTML from Limitless
  jp_city_league_001.json     # Expected results
  jp_city_league_002.html
  jp_city_league_002.json
  ...
  README.md                   # How to capture and verify new golden files
```

Each JSON follows the existing `expected_results.json` schema:

```json
[
  {
    "placement": 1,
    "archetype": "Charizard ex",
    "detection_method": "sprite_lookup",
    "sprite_count": 2
  }
]
```

### Logging Upgrade

Current state: `resolve()` logs at `logger.debug` level (lines 229, 244, 270, 283 in `archetype_normalizer.py`). Production log level is typically `INFO`, which means these lines are invisible.

**Recommendation:** Upgrade the final resolution log in each priority path from `debug` to `info`. Keep intermediate/fallthrough logs at `debug`. This means you get one `info`-level log per placement processed, showing the final archetype and method, without flooding logs with every fallthrough step.

Specific change: the `archetype_resolved` log at lines 229, 244, 270, 283 should be `logger.info`. The `sprite_url_no_match` warning at line 316 is already correct.

### Shadow Comparison Script

Location: `apps/api/scripts/shadow_compare.py`

Key design decisions:

- Read-only (no writes to DB)
- Outputs JSON report to stdout (pipe to file for review)
- Accepts `--days` argument (default 30)
- Uses the same `ArchetypeNormalizer` instance the pipeline uses (including DB sprite loading)
- Groups changes by detection method transition (e.g., "text_label -> sprite_lookup: 145 placements")

### DB Migration for `archetype_sprites` Table

The `ArchetypeSprite` model and `seed_db_sprites` classmethod already exist. What remains:

- Alembic migration to create the table
- Admin endpoint for CRUD (follows existing admin router patterns)
- Wire `load_db_sprites()` into the pipeline startup (call once before processing batch)
- Ensure `ArchetypeNormalizer` falls back gracefully to in-memory map on DB failure (already implemented at line 147)

### `.png` Regex Documentation

Add a comment to `_FILENAME_RE` at line 106 of `archetype_normalizer.py`:

```python
# Only matches .png sprite URLs. If Limitless migrates to .webp or another
# format, this regex must be updated. See test_archetype_edge_cases.py for
# the documented limitation test.
_FILENAME_RE = re.compile(r"/([a-zA-Z0-9_-]+)\.png")
```

## Summary: Phase 2 PR Checklist

| Item                                                       | Risk   | Value    | Status                        |
| ---------------------------------------------------------- | ------ | -------- | ----------------------------- |
| Real golden dataset fixtures (3-5 tournaments)             | Low    | **High** | Not started                   |
| Edge case tests (`.webp`, query params, unmatched sprites) | Low    | Medium   | Not started                   |
| Shadow comparison script                                   | Low    | **High** | Not started                   |
| Upgrade `resolve()` logging to `info`                      | Low    | Medium   | Not started                   |
| `_FILENAME_RE` comment + `.webp` limitation test           | Low    | Low      | Not started                   |
| `archetype_sprites` DB migration + admin CRUD              | Medium | **High** | Partially done (model exists) |
| Cinderace regression suite                                 | Low    | **High** | **Done**                      |
| SPRITE_ARCHETYPE_MAP expansion to ~47 entries              | Low    | **High** | **Done**                      |
| `resolve()` debug logging                                  | Low    | Medium   | **Done**                      |

Items marked "Done" were completed between Phase 1 merge and this deliberation. The remaining items form the Phase 2a PR scope.
