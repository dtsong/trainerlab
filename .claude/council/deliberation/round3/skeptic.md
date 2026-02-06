# Skeptic Final Position -- JP Archetype Pipeline Phase 2 Risk & Validation

## Revised Recommendation

Phase 1 delivered a sound foundation. The priority chain (`sprite_lookup` > `auto_derive` > `signature_card` > `text_label`) is architecturally correct. The sprite map has been expanded to ~51 entries (I counted 51 key-value lines in `SPRITE_ARCHETYPE_MAP`). The normalizer is wired to `load_db_sprites()` in the JP scrape path (`tournament_scrape.py:600`), and `seed_db_sprites()` is callable from the admin router (`admin.py:424`). Migration 023 adds the `confidence` column on `card_id_mappings`. Provenance fields (`raw_archetype`, `raw_archetype_sprites`, `archetype_detection_method`) are populated on every JP placement write (`tournament_scrape.py:719-721`).

**My risk assessment has shifted from "several critical gaps block reprocess" to "two remaining risks require validation gates within Phase 2."** The expanded sprite map, DB wiring, and golden dataset fixtures (2 real HTML files, 20 hand-validated placements) address most of my Round 2 concerns. What remains is the canary validation step and the `derive_name_from_key` hyphenation issue.

---

## Concessions Made

### 1. Dropped: "Wire normalizer to DB table before reprocess"

**Round 2 position:** The normalizer was hardcoded and must query the DB before reprocess.
**What changed:** I verified that `tournament_scrape.py:598-600` already creates an `ArchetypeNormalizer`, calls `load_db_sprites(self.session)`, and merges DB overrides into the instance's sprite map. The admin router exposes `seed_db_sprites()` to populate the DB from the in-code map. This is wired. I was wrong that it was disconnected.

### 2. Dropped: "SPRITE_ARCHETYPE_MAP has only 24 entries"

**Round 2 position:** 24 entries covers ~40-60% of JP meta.
**What changed:** The map now has ~51 entries including mega variants, current JP meta archetypes (grimmsnarl, noctowl, zoroark, ceruledge, flareon, joltik, alakazam, etc.), and VSTAR-era historical keys. This is materially better coverage.

### 3. Dropped: "Regex mismatch between limitless.py and normalizer"

**Round 2 position:** `_extract_archetype_and_sprites_from_images` used `[a-zA-Z_-]+` (no digits) while the normalizer used `[a-zA-Z0-9_-]+`.
**What changed:** `limitless.py:1339` now uses `r"/([a-zA-Z0-9_-]+)\.png"`, matching the normalizer's `_FILENAME_RE` at `archetype_normalizer.py:106`. Aligned.

### 4. Dropped: "Full forensic audit blocks everything"

**Round 2 position:** I shifted from sequential blocking to a canary gate within Phase 2.
**Unchanged in Round 3.** The canary-test-as-gate approach (10-20 tournaments, >95% accuracy) is the right balance between safety and velocity.

### 5. Dropped: "Golden dataset doesn't exist"

**Round 2 position:** No golden dataset tests existed.
**What changed:** `test_jp_golden_dataset.py` exists with 2 HTML fixtures (`city_league_tokyo_2025.html`, `city_league_osaka_2025.html`), 20 hand-validated placements across both, testing sprite extraction, archetype resolution, and detection method provenance. Plus `TestCinderaceRegression` as a targeted regression test. This is real end-to-end validation.

---

## Non-Negotiables

These are hard gates that MUST pass before running the historical reprocess on production data.

### Gate 1: Canary test on 10-20 recent JP tournaments (>95% accuracy)

**What:** Process 10-20 recent JP City League tournaments through the normalizer. Compare each placement's resolved archetype against the ground truth on Limitless (manual spot check or automated screenshot comparison).

**Pass criteria:**

- `sprite_lookup` resolves at least 70% of all placements.
- `auto_derive` resolves no more than 20% of placements.
- `text_label` resolves no more than 10% of placements.
- Total archetype accuracy (resolved name matches expected name) exceeds 95%.

**Why this is non-negotiable:** The golden dataset covers 20 placements from 2 fixtures. The canary test covers 200-600 placements from live data. If the normalizer breaks on a Limitless HTML variant we haven't seen, the canary will catch it. If we skip this, we are extrapolating from 20 data points to 10,000+.

### Gate 2: `derive_name_from_key` produces acceptable output for hyphenated names OR auto_derive is flagged low-confidence

**Current state:** `derive_name_from_key("chien-pao-baxcalibur")` produces `"Chien Pao Baxcalibur"` (wrong: should preserve the hyphen in "Chien-Pao"). This is at `archetype_normalizer.py:334`. The method splits ALL hyphens uniformly. It cannot distinguish `dragapult-pidgeot` (two Pokemon) from `chien-pao` (one Pokemon with a hyphenated name).

**Why this matters now:** The expanded sprite map covers `chien-pao` and `chien-pao-baxcalibur` via `sprite_lookup`, so `auto_derive` is bypassed for those keys TODAY. But the whole point of `auto_derive` is to handle NEW archetypes that are not yet in the map. When a new deck appears with a hyphenated Pokemon (e.g., `chien-pao-regidrago`), `auto_derive` will produce `"Chien Pao Regidrago"` instead of `"Chien-Pao Regidrago"`.

**Acceptable resolution (pick one):**

1. Fix `derive_name_from_key` to consult a set of known multi-part Pokemon names (`{"chien-pao", "iron-hands", "iron-valiant", "roaring-moon", "raging-bolt", ...}`) and preserve their hyphens.
2. OR: Accept the current behavior as "good enough" and ensure the canary test quantifies the error rate. If <5% of `auto_derive` results are hyphenated-name archetypes, the risk is tolerable.

**My concession here:** I originally said this MUST be fixed. I now accept option 2 if the canary data shows the error rate is low. But the canary must explicitly measure this.

### Gate 3: Backup before reprocess (backfill, not wipe)

**Council consensus:** Backfill in place, do not wipe. I agree.

**What this means in practice:**

- The reprocess endpoint should UPDATE existing `tournament_placements` rows, setting `archetype`, `raw_archetype`, `raw_archetype_sprites`, and `archetype_detection_method`.
- It should NOT delete and re-insert rows.
- Before the first production run, take a `pg_dump` of the `tournament_placements` table (or at minimum, run `SELECT id, archetype, archetype_detection_method INTO tournament_placements_backup FROM tournament_placements WHERE tournament_id IN (SELECT id FROM tournaments WHERE region = 'JP')`).
- This gives us a rollback path if the reprocess produces worse results.

---

## Implementation Notes

### Canary Test Script (pre-reprocess validation)

The canary test should produce a report like this:

```
=== JP Archetype Canary Report ===
Tournaments processed: 15
Total placements: 387

Detection method distribution:
  sprite_lookup:   72.4% (280)
  auto_derive:     18.3% (71)
  signature_card:   1.0% (4)
  text_label:       8.3% (32)

Hyphenated-name auto_derive results: 3 of 71 (4.2%)
  - "Chien Pao Baxcalibur" (expected: "Chien-Pao Baxcalibur")
  - "Iron Hands Forretress" (expected: "Iron Hands Forretress")
  - "Roaring Moon Greninja" (expected: "Roaring Moon Greninja")

Accuracy vs Limitless ground truth: 96.1%
  - 15 mismatches out of 387 placements
  - Most common mismatch: "Froslass" resolved as "Froslass ex" (5 cases)
```

### Queries to Run Before Reprocess

**1. Detection method distribution on existing data:**

```sql
SELECT archetype_detection_method, COUNT(*)
FROM tournament_placements tp
JOIN tournaments t ON t.id = tp.tournament_id
WHERE t.region = 'JP'
  AND tp.archetype_detection_method IS NOT NULL
GROUP BY archetype_detection_method
ORDER BY COUNT(*) DESC;
```

**2. Card mapping coverage for JP decklists:**

```sql
SELECT
  COUNT(DISTINCT jp_card_id) AS total_jp_cards,
  COUNT(DISTINCT CASE WHEN en_card_id IS NOT NULL THEN jp_card_id END) AS mapped_cards,
  ROUND(100.0 * COUNT(DISTINCT CASE WHEN en_card_id IS NOT NULL THEN jp_card_id END) / NULLIF(COUNT(DISTINCT jp_card_id), 0), 1) AS coverage_pct
FROM card_id_mappings;
```

**3. Scope of reprocess (how many JP placements exist):**

```sql
SELECT COUNT(*)
FROM tournament_placements tp
JOIN tournaments t ON t.id = tp.tournament_id
WHERE t.region = 'JP';
```

### Structured Logging Requirements

Before reprocess, upgrade the normalizer's logging from `logger.debug` to structured `logger.info` for the `archetype_resolved` event. Each resolved archetype should emit:

```python
logger.info(
    "archetype_resolved",
    extra={
        "tournament_id": str(tournament_id),
        "placement": placement.placement,
        "sprite_key": sprite_key,
        "archetype": archetype,
        "method": method,
        "raw_archetype": raw_archetype,
        "sprite_urls": sprite_urls,
    },
)
```

This gives us grep-able, queryable logs during the reprocess to diagnose any issues in near-real-time rather than after the fact.

### Golden Dataset Expansion

Current state: 2 fixtures, 20 placements. This is good for Phase 1 but thin for Phase 2.

Before reprocess:

- Add at least 3 more fixtures from different time periods (30, 60, 90 days ago) to verify historical HTML structure stability.
- Add at least 1 fixture from a JP Champions League (different page structure than City Leagues).
- Target: 5+ fixtures, 50+ placements, covering all 4 detection methods.

---

## Residual Risks I Am Accepting

These are risks I flagged in Round 2 that I am now accepting as tolerable, with reasons:

| Risk                                           | Severity | Why I Accept It                                                                                                                                                                                                                                                                             |
| ---------------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| New archetypes not in sprite map               | Medium   | `auto_derive` produces reasonable (if imperfect) names. The DB table allows runtime updates without deploys. Canary test will quantify the gap.                                                                                                                                             |
| Old Limitless pages may have different HTML    | Medium   | The canary test on 10-20 tournaments (including some older ones) will surface this if it exists. We do not need to solve it preemptively.                                                                                                                                                   |
| No dashboard for detection method distribution | Low      | The provenance column + SQL queries are sufficient for Phase 2. A real-time dashboard is a Phase 3 concern.                                                                                                                                                                                 |
| `auto_derive` losing "ex"/"VSTAR" suffixes     | Medium   | This is inherent to deriving from sprite filenames, which do not encode suffixes. The sprite map is the correct fix, and it covers the major archetypes. Residual `auto_derive` results without suffixes are acceptable as "best effort" labels that can be corrected later via DB updates. |

---

## Final Verdict

**Phase 2 is ready to begin, gated by the canary test.** The codebase is in materially better shape than I assessed in Round 2. The sprite map expansion (24 to ~51 entries), DB wiring (`load_db_sprites` in the scrape path), regex alignment, golden dataset (2 fixtures, 20 placements, 3 test classes), and provenance tracking collectively address my prior critical concerns.

The two remaining risks -- the `derive_name_from_key` hyphenation issue and untested coverage on live JP tournament diversity -- are both addressed by the canary test gate. If the canary passes at >95% accuracy with an acceptable detection method distribution, proceed to reprocess. If it fails, we have specific data on what to fix before retrying.

I am not blocking Phase 2. I am insisting on one checkpoint within it.
