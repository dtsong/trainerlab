# Craftsman Position — Japanese Tournament Data Pipeline Overhaul

## Core recommendation

**Build a test-driven refactor with golden dataset validation.** This is a data pipeline rewrite, not a greenfield feature. We need archetype mapping tests with real JP→EN tournament samples, regression tests against existing data, and data quality gates before any production reprocess.

**Key argument:**

The current pipeline is 3151 lines across three tightly coupled components (`limitless.py`, `archetype_detector.py`, `tournament_scrape.py`). We're proposing to replace the core archetype detection logic (signature cards → Limitless sprites), fix card mapping bugs (Cinderace EX misidentification), and reprocess all historical data. Without systematic testing, we risk introducing silent data corruption that only surfaces months later when someone notices meta share discrepancies.

The codebase already demonstrates quality practices: 85% backend coverage, 1606 passing tests, HTML fixtures for scraper tests, pytest-asyncio patterns, and AsyncMock usage. But archetype detection is currently tested with 11 test cases focused on signature card matching — none validate the JP→EN card mapping flow that's breaking. We need:

1. **Golden datasets** — Snapshot real Limitless HTML for JP tournaments (with sprite-based archetypes), store expected archetype labels, and assert parsers produce correct results
2. **Card mapping validation** — Test suites that verify JP card IDs correctly map to EN equivalents (the Cinderace bug shows this is fragile)
3. **Data quality gates** — Pipeline tests that reject invalid archetype labels, catch unmapped cards, and flag suspicious meta share shifts
4. **Regression baselines** — Before reprocessing, capture current meta snapshots and deck counts per archetype to detect unintended changes

**Why this matters:** Data pipeline bugs are silent killers. A wrong archetype label propagates through meta share calculations, tier assignments, prediction models, and user-facing dashboards. By the time someone notices "Charizard ex dropped 15% overnight," you've lost data provenance. TDD for data pipelines means treating test cases as contracts: "This JP decklist with these sprites → this archetype label."

---

## Testing strategy

### 1. Archetype detection test pyramid

**Unit tests (existing + new):**

- ✅ Current: 11 test cases for signature card matching logic
- 🆕 Add: Limitless sprite-pair parsing tests (mock HTML with `<img class="pokemon">` tags)
- 🆕 Add: JP card ID normalization tests (case sensitivity, zero-padding variants)
- 🆕 Add: Archetype alias resolution tests (ensure sprite names map to canonical labels)

**Integration tests (new):**

- Parse full Limitless JP tournament HTML → validate all placements get correct archetypes
- Feed JP decklist JSON → verify archetype detector uses JP→EN mapping correctly
- Test edge cases: missing sprites, mixed JP/EN decklists, unreleased cards

**Golden dataset tests (critical for this project):**

```
tests/fixtures/
  jp_city_league_real_01.html       # Real Limitless page (anonymized)
  jp_city_league_real_01.json       # Expected output: archetypes, card mappings
  jp_official_tournament_real_02.html
  jp_official_tournament_real_02.json
```

Pattern: Capture 5-10 real-world JP tournament pages, hand-validate the correct archetype labels from Limitless sprites, store as fixtures, assert parser output matches expectations. This becomes the regression suite.

### 2. Card mapping validation

**Data integrity tests:**

- `test_jp_card_mappings_complete()` — Assert every card in `CardIdMapping` table has valid EN equivalent
- `test_jp_card_mapping_consistency()` — No JP card ID maps to multiple EN IDs (detect duplicates)
- `test_card_id_case_normalization()` — Ensure `SV7-18`, `sv7-18`, `SV7-018` all resolve to same mapping
- `test_unmapped_jp_cards_in_recent_tournaments()` — Query last 30 days of JP decks, flag any JP card IDs not in mapping table

**Cinderace regression test (the bug that started this):**

```python
def test_cinderace_ex_mapping():
    """JP Cinderace ex must map to sv6-95, not signature card mismatch."""
    jp_to_en = load_card_mapping_from_db()

    # The specific bug case
    assert jp_to_en.get("SV7-18") != "sv3-125"  # Should NOT map to Charizard
    assert "sv6" in jp_to_en.get("SV7-18", "")  # Should map to sv6 set
```

**Mapping coverage metrics:**

- Track % of JP tournament decks with 100% card mapping coverage
- Alert when new JP set released but mappings < 80% complete
- Dashboard showing unmapped card frequency (helps prioritize mapping work)

### 3. Data quality gates

**Pre-reprocess validation:**

```python
@pytest.fixture(scope="session")
def baseline_meta_snapshot():
    """Capture current meta state before reprocess."""
    return {
        "total_tournaments": query_tournament_count(),
        "archetypes": query_archetype_distribution(),
        "top_5_decks": query_top_5_decks_by_meta_share(),
        "average_deck_count_per_tournament": compute_avg_decks(),
    }

def test_reprocess_preserves_tournament_count(baseline_meta_snapshot):
    """Reprocessing should not lose tournaments."""
    reprocessed = run_reprocess_pipeline()
    assert reprocessed.total_tournaments >= baseline_meta_snapshot["total_tournaments"]
```

**Post-reprocess validation:**

- `test_no_unknown_archetypes()` — Assert < 5% "Unknown" archetype after sprite adoption
- `test_archetype_label_consistency()` — No mixed casing (e.g., "Charizard EX" vs "Charizard ex")
- `test_meta_share_sanity_bounds()` — Top archetype should be 10-40% (not 95% or 0.1%)
- `test_jp_vs_en_archetype_parity()` — Same archetype names used in both regions (localization check)

**Pipeline smoke tests:**

- Run scraper against Limitless staging/test tournament → assert decklist parses without errors
- Mock Cloud Tasks → verify tournament processing creates correct DB records
- Test error recovery: if decklist fetch fails, placement still saved with archetype="Unknown"

### 4. Migration safety

**Two-phase rollout strategy:**

1. **Shadow mode:** New sprite-based detector runs in parallel with old signature-card detector, logs differences, no DB writes
2. **Gradual cutover:** New detector writes to DB, but keep old data in archive table for 30 days

**Rollback plan:**

```sql
-- Archive current tournament placements before reprocess
CREATE TABLE tournament_placements_backup_2026_02_05 AS
SELECT * FROM tournament_placements;

-- Rollback script if reprocess fails
BEGIN;
  DELETE FROM tournament_placements WHERE updated_at > '2026-02-05';
  INSERT INTO tournament_placements SELECT * FROM tournament_placements_backup_2026_02_05;
COMMIT;
```

**Feature flags (if available):**

- `use_sprite_archetype_detection` — toggle between old/new detector
- `enable_jp_card_mapping_fallback` — if mapping lookup fails, try direct card ID

**Monitoring:**

- Alert if archetype detection takes > 2s per decklist (performance regression)
- Alert if > 10% of decks labeled "Unknown" after reprocess (mapping coverage issue)
- Track "archetype changed" count: how many existing placements got relabeled

---

## Code quality analysis

### Current state assessment

**Strengths:**

- ✅ Clean separation: scraper (`limitless.py`), detector (`archetype_detector.py`), orchestration (`tournament_scrape.py`)
- ✅ Type hints throughout (Python 3.11+ compatible)
- ✅ Pytest-asyncio patterns (`AsyncMock`, `spec=AsyncSession`)
- ✅ HTML fixtures for scraper tests (reproducible)
- ✅ Comprehensive docstrings with Args/Returns
- ✅ Error handling: LimitlessError hierarchy, retry logic with exponential backoff
- ✅ Rate limiting built into client (30 req/min, max 5 concurrent)

**Code smells in scraping layer:**

- 🔴 **2022-line monolith:** `limitless.py` handles 8 different Limitless page formats (EN tournaments, JP City Leagues, official tournaments, decklists from 2 domains). Needs decomposition.
- 🟡 **Brittle HTML parsing:** 15+ BeautifulSoup selectors like `soup.select("table.standings tbody tr")` with fallbacks. Limitless changes HTML → tests pass but scraper breaks in prod.
- 🟡 **Hard-coded set mappings:** `LIMITLESS_SET_MAPPING` dict with 50+ entries. New sets require code deploy. Consider set mapping as data (config file or DB table).
- 🟡 **No schema validation:** Scraped data goes straight to DB. If Limitless adds new archetype naming convention, we ingest garbage. Need Pydantic validation.

**Architecture issues in archetype detection:**

- 🔴 **Signature card dict is code:** 95-line `SIGNATURE_CARDS` dict in `src/data/signature_cards.py` requires code change for new archetypes. Moving to Limitless sprites solves this, but need data-driven approach (fetch sprite→archetype mappings from Limitless API or scrape their archetype page).
- 🟡 **JP→EN mapping is cached globally:** `TournamentScrapeService._jp_to_en_mapping` loaded once per service instance. If mapping updates mid-pipeline, uses stale data. Consider explicit cache invalidation.
- 🟡 **No validation of archetype labels:** Detector returns arbitrary strings. Should validate against known archetype enum or Limitless's official list.

**Testing gaps:**

- 🔴 **No end-to-end scraper tests:** No tests that hit real Limitless URLs (even in sandbox mode). Easy to miss breakage.
- 🔴 **No data quality tests:** No assertions about archetype distribution, no checks for "meta share adds up to 100%."
- 🟡 **Fixtures are minimal:** 12 HTML fixtures, but none for complex cases (JP decklist with mixed mapped/unmapped cards, tournaments with 0 decklists, etc.).

### Recommended refactoring (outside this project scope, but noted)

**Not urgent, but improves long-term maintainability:**

1. Split `limitless.py` into modules: `limitless/tournaments.py`, `limitless/decklists.py`, `limitless/jp_city_leagues.py`
2. Extract HTML parsing into `LimitlessParser` class with schema validation (Pydantic models for scraped data)
3. Move set mappings to config file (`data/limitless_set_mappings.json`) or DB table
4. Add Pydantic validation layer: `RawTournamentData` → validate → `Tournament` model
5. Introduce `ArchetypeRegistry` class that validates labels against Limitless's official archetype list

---

## Data validation patterns

### Golden dataset strategy

**Why golden datasets matter for scrapers:**
Scrapers parse HTML with dozens of edge cases (missing fields, layout changes, internationalization). Golden datasets are the source of truth: "This HTML should produce this JSON." Store real-world examples, hand-validate expected output, assert parser matches.

**Implementation:**

```python
# tests/test_jp_tournament_golden.py
import json
import pytest
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures" / "jp_tournaments"

@pytest.mark.parametrize("fixture_name", [
    "city_league_tokyo_2026_01_15",
    "official_tournament_osaka_2026_01_20",
    "champions_league_jp_2026_02_01",
])
def test_jp_tournament_golden_dataset(fixture_name):
    """Parse real JP tournament HTML, assert archetype labels match expected."""
    html = (FIXTURES / f"{fixture_name}.html").read_text()
    expected = json.loads((FIXTURES / f"{fixture_name}.json").read_text())

    # Parse with new sprite-based detector
    client = LimitlessClient()
    tournament = await client.fetch_jp_city_league_placements(html)

    # Assert archetype labels match hand-validated expected output
    actual_archetypes = [p.archetype for p in tournament.placements]
    expected_archetypes = [p["archetype"] for p in expected["placements"]]

    assert actual_archetypes == expected_archetypes, \
        f"Archetype mismatch in {fixture_name}"
```

**Golden dataset curation process:**

1. Scrape 5-10 real JP tournaments from last 30 days
2. Manually validate archetype labels by inspecting Limitless sprite images
3. Store anonymized HTML (replace player names with "Player 1", "Player 2")
4. Store expected JSON with correct archetype labels
5. Add to CI: if parser output != expected, test fails (catches regressions)

### Data quality metrics

**Pipeline observability:**

- **Archetype coverage:** % of decks with archetype != "Unknown"
  - Target: > 95% after sprite adoption
  - Alert if < 85% (indicates mapping gaps or parser breakage)

- **Card mapping coverage:** % of JP cards in decks with EN equivalent
  - Target: > 98% for sets released in last 6 months
  - Alert if new set released and coverage < 80% after 7 days

- **Meta share sanity:** Top archetype should be 10-40%, sum of all shares ≈ 100%
  - Alert if top archetype > 50% (likely labeling bug collapsed multiple decks into one)
  - Alert if sum of shares < 95% or > 105% (math error)

- **Archetype label consistency:**
  - Check for variants: "Charizard ex" vs "Charizard EX" vs "charizard ex"
  - Enforce canonical form: title case with "ex" lowercase

**Automated quality checks (pytest):**

```python
def test_meta_snapshot_archetype_distribution(db_session):
    """Meta snapshots should have sane archetype distributions."""
    snapshot = get_latest_meta_snapshot(db_session, region="JP")

    # Top archetype should be 10-40% meta share
    top_deck = max(snapshot.archetypes, key=lambda a: a.meta_share)
    assert 0.10 <= top_deck.meta_share <= 0.40, \
        f"Top deck {top_deck.name} has {top_deck.meta_share:.1%} share (suspicious)"

    # Sum of all shares should be ~100%
    total_share = sum(a.meta_share for a in snapshot.archetypes)
    assert 0.95 <= total_share <= 1.05, \
        f"Meta shares sum to {total_share:.1%} (should be ~100%)"

    # No more than 5% "Unknown"
    unknown_share = next(
        (a.meta_share for a in snapshot.archetypes if a.name == "Unknown"),
        0.0
    )
    assert unknown_share < 0.05, \
        f"Unknown archetype is {unknown_share:.1%} (too high)"
```

---

## Migration safety

### Reprocess plan (phased approach)

**Phase 1: Shadow mode (1 week)**

- Deploy new sprite-based detector
- Run in parallel with old detector
- Log differences to structured logs: `{"tournament_id": "...", "old_archetype": "Charizard ex", "new_archetype": "Charizard / Pidgeot", "confidence": 0.85}`
- Review logs daily: what % of decks changed labels? Are changes reasonable?
- Goal: < 10% churn in archetype labels (if > 10%, investigate before proceeding)

**Phase 2: Dry run reprocess (staging DB)**

- Clone production DB to staging
- Run full reprocess with new detector
- Generate before/after report:
  ```
  Total tournaments: 1,234 (unchanged)
  Archetypes relabeled: 156 (12.6%)
  Top changes:
    - "Unknown" → "Cinderace ex": 42 decks
    - "Charizard ex" → "Charizard / Pidgeot": 18 decks
  Meta share deltas:
    - Charizard ex: 18.5% → 16.2% (-2.3pp)
    - Cinderace ex: 0% → 3.4% (+3.4pp)
  ```
- Validate: Does this match expectations from Limitless's archetype distribution?

**Phase 3: Production reprocess (with rollback plan)**

- Backup current data: `tournament_placements_backup_YYYY_MM_DD`
- Run reprocess in maintenance window (low traffic)
- Monitor key metrics in real-time:
  - Total tournaments (should not decrease)
  - Archetype coverage (should increase)
  - Meta share sum (should be ~100%)
- If metrics look bad: ROLLBACK immediately
- If metrics look good: Let run for 24 hours, monitor user feedback

**Phase 4: Cleanup**

- Delete backup table after 30 days (if no issues reported)
- Archive old signature_cards.py for reference
- Update docs: "Archetypes now sourced from Limitless sprites, not manual mapping"

### Rollback strategy

**Database rollback (< 1 hour):**

```sql
-- Restore from backup
BEGIN;
  DELETE FROM tournament_placements;
  INSERT INTO tournament_placements
    SELECT * FROM tournament_placements_backup_2026_02_05;
  DELETE FROM meta_snapshots WHERE computed_at > '2026-02-05';
COMMIT;

-- Re-run meta computation with old data
CALL recompute_meta_snapshots();
```

**Code rollback (< 5 minutes):**

- Revert commit that replaced signature card detector with sprite detector
- Redeploy API (Cloud Run takes ~3 min)
- Re-run pipeline job to fetch new tournaments with old detector

**Feature flag fallback (instant):**
If feature flags available:

```python
if config.use_sprite_archetype_detection:
    detector = SpriteArchetypeDetector()
else:
    detector = SignatureCardDetector()  # Old reliable
```

Toggle flag → instant rollback, no deploy needed.

---

## Risks if ignored

1. **Silent data corruption at scale:**
   - Without golden dataset tests, sprite parser could misread Limitless HTML
   - Bug propagates through entire historical reprocess (1,000+ tournaments)
   - Meta share data becomes unreliable, users lose trust in platform
   - Recovery requires manual re-validation of all archetype labels

2. **Card mapping gaps create phantom archetypes:**
   - If Cinderace JP→EN mapping is wrong, all Cinderace decks labeled as different archetype
   - Meta share calculations fragment: "Cinderace ex" exists with 0% share, real decks labeled "Unknown"
   - Prediction models trained on bad data produce garbage forecasts

3. **No regression detection:**
   - Reprocess changes 12% of archetype labels, but no baseline to compare against
   - Can't distinguish "intentional relabeling" from "parser broke and everything is now Unknown"
   - Only discover problem when users report "meta dashboard looks weird"

---

## Dependencies on other agents

**Architect (System Design):**

- How should sprite→archetype mappings be stored? (DB table? Config file? Live scrape from Limitless?)
- Should we introduce a `ArchetypeMappingService` to centralize this logic?
- What's the schema for archetype labels? (String? Enum? Normalized form?)
- Caching strategy for JP→EN card mappings (Redis? In-memory with TTL?)

**Advocate (User Impact):**

- What user-facing metrics change after reprocess? (Meta dashboard, deck archetype labels, tier assignments)
- Do we need user communication? ("We improved archetype detection, some deck labels may have changed")
- What's the acceptable error rate? (< 5% Unknown archetypes? < 1%?)
- Should we expose archetype confidence scores in UI? ("Charizard ex: 85% confidence")

**Conductor (Project Planning):**

- Timeline: How long for golden dataset curation? (Estimate: 2-3 days to capture and validate 10 real tournaments)
- Phased rollout schedule: Shadow mode (1 week) → Staging reprocess (2 days) → Prod reprocess (1 day) → Monitor (1 week)
- Risk mitigation: Who has DB rollback permissions? Where's the runbook?
- Resource needs: Do we need a dedicated staging DB for dry run? Cloud Tasks quota for reprocessing 1K+ tournaments?

---

**Bottom line:** This is a data-critical project. Test coverage isn't optional — it's the only way to know the pipeline is working. Golden datasets lock in correctness, quality gates catch regressions, and phased rollout with rollback gives us confidence to reprocess historical data without destroying it.
