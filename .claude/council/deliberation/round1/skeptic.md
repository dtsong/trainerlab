# Skeptic Position — Japanese Tournament Data Pipeline Overhaul

## Core recommendation

**CRITICAL RISK: Data integrity corruption at three failure points.** Before any archetype labeling changes, we must trace and document the Cinderace EX false positive through the entire pipeline—scraping → card mapping → signature detection. The root cause isn't just "broken mappings," it's a cascade of three brittle dependencies that will fail again when Limitless changes HTML structure or releases new JP cards.

**Mitigation:** Full audit trail with validation gates at each layer. No "wipe and re-scrape" until we understand why the current system failed and can prove the new system won't repeat it.

## Key argument

The Cinderace EX issue reveals a **systemic data quality problem**, not just a mapping bug:

1. **Scraping layer (2023 lines of brittle HTML parsing)**: `limitless.py` uses fragile CSS selectors like `.pokemon`, `.deck-card`, `table.standings` with multiple fallbacks. When Limitless changes class names or HTML structure, we silently extract wrong data. The `_extract_archetype_from_images()` method (line 1304) scrapes Pokemon names from image alt text—but what if Limitless starts using lazy-loaded images or changes alt format? **We have no validation that scraped archetype names match reality.**

2. **Card mapping layer (JP→EN translation)**: `sync_card_mappings.py` fetches equivalents by scraping individual card detail pages at `/cards/jp/{SET}/{NUMBER}` looking for an "Int. Prints" section (line 1954 in `limitless.py`). This is:
   - **Slow**: N+1 queries (one per card in a set)
   - **Fragile**: Breaks if Limitless changes section headers or link formats
   - **Incomplete**: If Limitless doesn't list an EN equivalent, we store no mapping—resulting in JP card IDs that never match signature cards
   - **Zero validation**: No check that mapped EN card ID actually exists in TCGdex

3. **Signature card matching layer**: `archetype_detector.py` (192 lines) relies on hardcoded `SIGNATURE_CARDS` dict (95 entries, 100+ aliases). This requires manual updates when:
   - New archetypes emerge
   - Card IDs change between sets (reprints)
   - Limitless introduces new archetype naming conventions

**The Cinderace EX false positive could occur via multiple paths:**

- **Path A (Card mapping failure)**: JP decklist contains "SV6-95" (Cinderace ex). Mapping pipeline fails to find EN equivalent. Archetype detector gets unmapped "SV6-95", doesn't match signature card "sv6-95" (case mismatch), falls back to Limitless-scraped archetype name, which was corrupted during HTML parsing.

- **Path B (Signature card gap)**: Cinderace ex signature card exists ("sv6-95" at line 26 of `signature_cards.py`), but JP decklist uses a different card number (e.g., promo version). No mapping → no match → labeled as "emerging archetype" when it's actually a known deck with wrong card ID.

- **Path C (Scraping corruption)**: Limitless JP page HTML changed, and `_extract_archetype_from_images()` now pulls wrong Pokemon names from image filenames instead of alt text (line 1324-1331). Decklist correctly mapped, but archetype label from scraper is garbage.

**We cannot "adopt Limitless sprite-pair archetype system" without understanding:**

- Where exactly does Limitless store sprite-pair combos in their HTML? (Not found in current scraper code)
- How do we validate that scraped sprite pairs match actual deck composition?
- What happens when Limitless uses different Pokemon images for same archetype (regional variants, alternative art)?

## Data integrity risks

### CRITICAL

1. **Silent data corruption when Limitless changes HTML**: No automated tests scrape live Limitless pages. CSS selector changes fail silently, returning empty strings or wrong values. We only discover corruption when users report "meta shares don't match Limitless."

2. **Card mapping black holes**: When `fetch_card_equivalents()` fails to find an EN equivalent (404, HTML change, missing section), we silently skip the card (line 1899). JP decklists with unmapped cards produce wrong archetype labels, polluting meta calculations.

3. **Case sensitivity landmines**: Signature card lookup is case-sensitive ("sv6-95" vs "SV6-95"). Card mapping variants generator (line 92-121 in `tournament_scrape.py`) attempts normalization, but doesn't cover all edge cases (e.g., "sv6-095" with zero-padding).

### HIGH

4. **Duplicate tournament detection via URL**: `tournament_exists()` checks `source_url` uniqueness. If Limitless changes URL structure (e.g., adds query params, redirects), we re-scrape and duplicate tournaments.

5. **JP-only cards break archetype detection**: Cards released in Japan but not yet in English have no EN equivalent. These appear as "Rogue" or "Unknown" until manual mapping to placeholder card IDs.

6. **BO1 vs BO3 data contamination**: If region detection fails (line 588 in `tournament_scrape.py`), JP tournaments might get `best_of=3` instead of `best_of=1`, corrupting BO1 meta analysis.

### MEDIUM

7. **Rate limiting failures cascade**: `LimitlessClient` has retry logic (line 389-437) but only 3 retries with exponential backoff. If Limitless rate limits us during a full re-scrape, we lose partial data and have to restart.

8. **Archetype alias drift**: `ARCHETYPE_ALIASES` dict (line 99-193 in `signature_cards.py`) contains hardcoded JP names like "エースバーンex". If Limitless starts using different romanization or abbreviations, aliases become stale.

## Scraping fragility analysis

**Severity: CRITICAL**

The Limitless scraper has **zero defensive validation**. Every parsing method has this pattern:

```python
rows = soup.select("table.standings tbody tr")
if not rows:
    rows = soup.select("table.standings tr")  # Fallback #1
if not rows:
    rows = soup.select("table.striped tbody tr")  # Fallback #2
if not rows:
    rows = soup.select(".standings-row")  # Fallback #3
```

**This hides failures.** If all fallbacks return empty, we log nothing and continue. The calling code gets an empty list, stores a tournament with zero placements, and we never know data is missing.

**Limitless HTML changes that will break us:**

- Change `table.standings` to `table.results` → fallback chain exhausted → no placements
- Add lazy-loaded React components → BeautifulSoup parses pre-hydration HTML → wrong data
- Move to client-side rendering → HTML contains skeleton, real data fetched via JSON API → we scrape placeholders
- Change Pokemon image format from `<img alt="Charizard">` to `<img data-pokemon="charizard">` → archetype extraction fails

**No official API exists.** We're screen-scraping a user-facing website. Limitless has no obligation to maintain HTML structure. They could redesign tomorrow.

**Evidence of brittleness:**

- 8 different CSS selector patterns for tournament rows (line 469-473, lines 641-647)
- 3 different decklist parsing formats (official site, play site, text fallback)
- Manual date parsing with 7 different format attempts (line 148-165)
- Country-to-region mapping with 50+ hardcoded country codes (line 1118-1169)

**Impact when HTML changes:**

- Scraper silently returns partial data
- Missing placements → biased meta shares (only top placements scraped)
- Wrong archetype labels → "Cinderace ex" labeled as emerging when it's top tier
- Database accumulates corrupt records that pollute all downstream analysis

## Card mapping failure modes

**Severity: HIGH**

`sync_card_mappings.py` can fail in 6 ways:

1. **Limitless card detail page structure changes** (line 1932 `_fetch_single_card_equivalent`): If "Int. Prints" section renamed to "International Versions" or moved to a different div, regex match fails → no mapping stored.

2. **Set code misalignment**: `LIMITLESS_SET_MAPPING` dict (line 169-217) maps Limitless codes (e.g., "TWM") to TCGdex IDs (e.g., "sv6"). If Limitless introduces a new set code before we update the dict, `map_set_code()` returns the raw code unchanged → wrong card ID format → no TCGdex match.

3. **Card number zero-padding inconsistency**: Limitless might use "SV7-018" while TCGdex uses "sv7-18". The variants generator (line 92-121) attempts to handle this, but only creates a fixed set of variants (2-digit, 3-digit). If actual padding is 4 digits, no match.

4. **HTTP 404 on card detail page**: Limitless might not have created detail pages for all cards yet (newly released sets). We catch the error (line 1935) but store nothing → silent mapping gap.

5. **Stale mappings**: If Limitless updates an EN equivalent (e.g., fixes a mistake), we don't detect changes unless we re-run the entire mapping sync. No "updated_at" timestamp comparison.

6. **Database constraint failures**: `jp_card_id` must be unique (line 33 in `card_id_mapping.py`). If Limitless changes a card ID format mid-season, we can't store the new mapping without deleting the old one → manual intervention required.

**What happens when mapping fails:**

- JP decklist card "SV7-18" → lookup in `jp_to_en_mapping` → not found → passed as-is to archetype detector
- Archetype detector looks up "SV7-18" in `SIGNATURE_CARDS` → not found (signature cards use lowercase "sv7-18")
- Detector returns "Rogue"
- Tournament placement saved with archetype="Rogue"
- Meta calculation: "95% Rogue" meta reported for Japan → false signal

## Risks if ignored

- **DATA CORRUPTION AT SCALE**: Re-scraping all JP tournaments without fixing root causes will import thousands of corrupt records. The Cinderace EX error pattern will repeat for every archetype with mapping/scraping issues. Database becomes unreliable for meta analysis.

- **PIPELINE FAILURE DURING APRIL ROTATION**: When format rotates April 10, archetype composition changes. If we deploy a broken pipeline before rotation, we have no reliable data for post-rotation meta—exactly when users need it most.

- **CASCADING ANALYSIS FAILURES**: Meta snapshots, JP signals, tier rankings, and predictions all depend on archetype labels. Corrupt labels → corrupt tiers → corrupt predictions → users make bad deck choices → platform loses credibility.

## Dependencies on other agents' domains

**From Architect:**

- **Archetype truth source design**: Where do we store Limitless sprite-pair combos? New `archetype_sprites` table? JSONB column on `tournament_placement`? Need schema before we can scrape it.
- **Validation gate architecture**: Where do we checkpoint data quality? After scrape? After mapping? Before meta compute? Need clear boundaries.
- **Rollback strategy**: If bad data imported, how do we revert? Need transaction boundaries or soft-delete pattern.

**From Craftsman:**

- **Scraper resilience patterns**: How to validate scraped data before storage? Need contract tests against known-good HTML snapshots.
- **Card mapping retry logic**: When mapping fails, do we retry? Queue for manual review? Need error handling strategy.
- **Archetype detection fallback**: When signature cards don't match, use Limitless label or mark as "Unknown"? Need decision tree.

**From Conductor:**

- **Phased rollout plan**: Can we test new pipeline on subset of tournaments before full re-scrape? Need staging environment strategy.
- **Data migration order**: Do we wipe old data first or keep it for comparison? Need rollback window defined.
- **Validation metrics**: How do we know the new data is better? Need acceptance criteria (e.g., "Rogue % drops below 20%", "Top 5 archetype shares match Limitless within 5%").

---

**Non-negotiables:**

1. **Root cause analysis BEFORE re-scrape**: Trace the Cinderace EX error end-to-end with specific tournament URL, decklist, and database records. Document exact failure point.

2. **Validation gates at every layer**: Scraper must validate parsed data against known patterns (e.g., archetype names match regex, placement numbers are sequential). Card mapper must verify EN card ID exists in TCGdex. Archetype detector must log confidence scores.

3. **Canary testing**: Test new pipeline on 10 recent JP tournaments, compare results to Limitless ground truth, achieve >95% archetype label accuracy before full deployment.

4. **Rollback plan**: Preserve current data in separate schema or timestamp-based soft delete. If new pipeline produces worse results, we can revert.

5. **Monitoring**: Add Prometheus metrics for scraping success rate, mapping coverage, archetype match rate. Alert if any metric degrades >10% from baseline.
