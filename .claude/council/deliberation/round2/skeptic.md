# Skeptic Round 2 -- Phase 1 Post-Mortem & Remaining Risk Assessment

## Status: Phase 1 merged (PR #312). The code exists. Now stress-test it.

---

## 1. Phase 1 Implementation: Specific Failure Modes in Shipped Code

I have read the actual implementation. The following are concrete risks in the merged code, not hypotheticals.

### CRITICAL: `derive_name_from_key` destroys multi-word Pokemon names

`ArchetypeNormalizer.derive_name_from_key()` at `/Users/danielsong/Development/tcg/trainerlab/apps/api/src/services/archetype_normalizer.py` line 140 splits on ALL hyphens and capitalizes each part:

```python
parts = sprite_key.split("-")
return " ".join(p.capitalize() for p in parts if p)
```

This means:

- `"raging-bolt"` produces `"Raging Bolt"` (correct)
- `"raging-bolt-ogerpon"` produces `"Raging Bolt Ogerpon"` (correct)
- `"chien-pao"` produces `"Chien Pao"` (WRONG -- should be `"Chien-Pao"`)
- `"iron-hands"` produces `"Iron Hands"` (WRONG -- should be `"Iron Hands ex"`)

The method has no way to distinguish a hyphen that separates two Pokemon (`dragapult-pidgeot`) from a hyphen that is part of a single Pokemon's name (`chien-pao`, `iron-valiant`, `roaring-moon`). This is masked today because all these names are in `SPRITE_ARCHETYPE_MAP` (Priority 1 catches them). But `auto_derive` (Priority 2) is the fallback for NEW archetypes -- the exact scenario where correctness matters most. When a new deck featuring `chien-pao-baxcalibur` appears, auto_derive will produce `"Chien Pao Baxcalibur"` instead of `"Chien-Pao Baxcalibur"`.

**Severity: HIGH.** Not critical today because the map covers current archetypes. Becomes critical the moment a new hyphenated-name archetype emerges outside the map.

**Mitigation required:** The auto_derive path needs a known-Pokemon-name dictionary to reconstruct multi-part names correctly, or this path should be flagged as low-confidence and logged for manual review.

### HIGH: The `SPRITE_ARCHETYPE_MAP` is a hardcoded dict, not using the DB table

The `ArchetypeNormalizer.__init__()` defaults to `SPRITE_ARCHETYPE_MAP` -- a Python dictionary with ~24 entries. Migration 022 created an `archetype_sprites` database table with the right schema. But the normalizer does not query the database at all. It uses a static Python dict.

This means:

- Adding a new archetype mapping requires a code deploy, not a data update.
- The DB table (`archetype_sprites`) created in migration 022 is currently unused by the normalizer.
- The Architect's design (Round 1) described a database-backed lookup with caching. What was shipped is a hardcoded constant.

**Severity: HIGH.** This is the exact same maintenance burden as the old `SIGNATURE_CARDS` dict. We replaced one hardcoded mapping with another. The DB table exists but is disconnected from the runtime path.

**Mitigation required:** Before historical reprocess, wire `ArchetypeNormalizer` to query `archetype_sprites` table with an in-memory cache. The current hardcoded map should seed the table, not be the production lookup.

### MEDIUM: `_extract_archetype_and_sprites_from_images` regex misses numeric suffixes

At line 1341 of `/Users/danielsong/Development/tcg/trainerlab/apps/api/src/clients/limitless.py`, the filename fallback regex is:

```python
filename_match = re.search(r"/([a-zA-Z_-]+)\.png", src)
```

This requires ONLY letters, underscores, and hyphens. It will NOT match filenames containing digits. If Limitless ever uses sprite filenames like `mewtwo2.png`, `charizard-ex.png`, or `gen9v2/dragapult.png`, the regex silently fails and we lose that sprite name. The `build_sprite_key` regex in the normalizer (`_FILENAME_RE`) does handle digits (`[a-zA-Z0-9_-]+`), so the two components have inconsistent extraction logic.

**Severity: MEDIUM.** Today Limitless uses clean alphabetic names. This is a latent mismatch that will bite when filenames evolve.

### MEDIUM: No observability on detection method distribution

The `archetype_detection_method` column is written to the DB but there is no monitoring, no dashboard query, and no alert if `auto_derive` or `text_label` suddenly spikes (which would indicate `SPRITE_ARCHETYPE_MAP` coverage has degraded). Without this signal, we cannot tell whether the normalizer is working well or silently degrading.

---

## 2. Challenging the Optimism: "Phase 1 is Done" is Premature Comfort

Several agents (Strategist, Architect, Craftsman) expressed relief that Phase 1 is shipped and suggested moving to historical reprocess. I want to name what is still fragile.

**The normalizer has 24 static entries and no learning mechanism.** The Pokemon TCG releases new sets roughly every 3 months. Each set can introduce 2-5 new competitive archetypes. The current map covers the established metagame but has zero coverage for:

- Post-rotation archetypes (April 10 rotation will shuffle the metagame)
- New set archetypes (any set released after today)
- Variant archetypes (e.g., if "Charizard Dusknoir" emerges as distinct from "Charizard Pidgeot")

The `auto_derive` fallback will handle SOME of these, but with the hyphenated-name bug described above, it will produce inconsistent naming for a meaningful subset.

**Historical reprocess will lock in current normalizer quality for ALL past data.** If we reprocess 3,000+ tournaments with the current 24-entry map, every placement that does not match the map will get an `auto_derive` or `text_label` classification. Those classifications become the archetype labels in our database. If we later discover they were wrong (e.g., "Chien Pao" should have been "Chien-Pao ex"), correcting them requires ANOTHER full reprocess or targeted bulk update.

**The Craftsman's golden dataset validation has not been built yet.** Phase 1 shipped 37 tests, but none are golden dataset tests against real Limitless HTML with hand-validated expected archetypes. The tests verify the code works mechanically; they do not verify it produces correct results for real-world data.

---

## 3. Response to Strategist and Operator: Parallel Validation

Both Strategist and Operator suggested that validation can run in parallel with root-cause analysis rather than sequentially. I will modify my Round 1 position on this.

**I agree with parallel execution, with one hard gate.**

The Strategist's phased approach (validation on 20 recent tournaments before touching historical data) is correct and addresses my core concern. The Operator's structured logging proposal would give us the observability we need to detect failures during reprocess.

**My revised position:** Root-cause analysis of the Cinderace bug and validation of the new normalizer CAN proceed in parallel. However, the historical reprocess MUST NOT begin until:

1. At least 10 recent JP tournaments have been processed with the new normalizer and spot-checked against Limitless ground truth.
2. The detection method distribution is known (what % sprite_lookup vs auto_derive vs text_label?).
3. If `auto_derive` is producing more than 15% of classifications, the hyphenated-name bug must be fixed first.

This is a gate, not a blocker. If validation passes quickly, reprocess can start within days. But "ship it and see" without the gate risks baking bad labels into the entire historical dataset.

---

## 4. Open Risk Register

### Risk 1: SPRITE_ARCHETYPE_MAP Coverage Gap (Severity: HIGH)

**Current state:** 24 entries covering ~20 distinct archetypes.
**Estimated JP meta archetypes in active play:** 40-60.
**Coverage estimate:** 40-60% of current metagame, assuming the top archetypes are mapped.
**Impact:** Every unmapped archetype falls through to `auto_derive`, which produces generic names without "ex"/"VSTAR" suffixes and mangles hyphenated Pokemon names.

**What must happen:** Before historical reprocess, scrape the current top 50 JP tournament archetypes from Limitless, count how many hit `sprite_lookup` vs `auto_derive`, and expand the map (or wire the DB table) accordingly. If coverage is below 80%, do not reprocess.

### Risk 2: Card Mapping Coverage for JP Decklists (Severity: HIGH)

**Current state:** The `card_id_mappings` table exists (migration 017) but its population is unknown. The normalizer's signature_card fallback (Priority 3) depends on JP card IDs being translated to EN card IDs. If the mapping table is sparse, Priority 3 is effectively dead for JP tournaments.

**What must happen:** Run a coverage query: what percentage of JP decklist card IDs in the last 90 days have a corresponding EN mapping? If coverage is below 85%, the signature_card fallback is unreliable and we are more dependent on sprite accuracy than we think.

### Risk 3: Historical Reprocess Data Integrity (Severity: HIGH)

**Specific failure scenario:** Reprocess deletes JP `meta_snapshots`, re-scrapes tournaments, and recomputes meta. If the normalizer produces worse labels than the old system for some archetypes (e.g., because a sprite URL format changed 6 months ago and old tournament pages have different HTML), we have replaced bad data with differently bad data. No net improvement, plus we have destroyed the original records.

**What must happen:**

1. **Backup before wipe.** Not just Cloud SQL automated backups -- a queryable snapshot (e.g., `tournament_placements_backup` table or pg_dump to Cloud Storage).
2. **Dry-run comparison.** Process 50 historical tournaments with the new normalizer, compare old archetype labels vs new, publish a diff report. Validate that changes are improvements, not regressions.
3. **Preserve `raw_archetype`/`raw_archetype_sprites` on every record.** This is already in the schema (migration 021), which is good. But confirm these fields are populated even during reprocess, not just for new tournaments.

### Risk 4: Limitless HTML Structure Drift for Old Pages (Severity: MEDIUM)

**Question nobody has asked:** Do old JP tournament pages on Limitless have the same HTML structure as current ones? Limitless may have redesigned their tournament detail pages over the past 90 days. If we re-fetch a tournament from November 2025 and the page layout has changed (e.g., they added new columns, changed sprite CDN paths), our parser may extract different data than what was on the page when the tournament was held.

**Mitigation:** Process a sample of old tournaments (30+, 60+, 90+ days old) and verify sprite extraction works. If old pages have different structure, we may need to accept that some historical data cannot be reliably re-extracted.

---

## 5. Non-Negotiable Pre-Reprocess Checklist

Before any historical data wipe/reprocess, the following MUST be verified:

1. **Wire the normalizer to the `archetype_sprites` DB table** so mappings can be updated without code deploys. The hardcoded `SPRITE_ARCHETYPE_MAP` should seed the table, not be the runtime source.

2. **Expand sprite coverage to at least 80% of active JP archetypes** by scraping recent Limitless meta pages and populating the mapping table.

3. **Fix the `derive_name_from_key` hyphenation bug** or mark `auto_derive` as low-confidence in the `archetype_detection_method` column so we can identify and fix these records later.

4. **Validate on 10+ recent tournaments** with spot-check comparison to Limitless ground truth. Publish detection method distribution (sprite_lookup %, auto_derive %, signature_card %, text_label %).

5. **Create a queryable backup** of current JP tournament_placements before wipe.

6. **Add a monitoring query** that reports detection method distribution weekly so degradation is caught proactively rather than by user reports.

---

## Summary of Position Shifts

| Round 1 Position                    | Round 2 Position                             | Reason                                                                                                  |
| ----------------------------------- | -------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| Root-cause analysis BEFORE any work | Validation can run parallel to analysis      | Strategist's phased gates address my concern without blocking progress                                  |
| Theoretical HTML fragility concerns | Specific code bugs in shipped implementation | Code review reveals concrete issues (hyphenation, regex mismatch, hardcoded map)                        |
| Need monitoring before deploy       | Need monitoring before REPROCESS             | Phase 1 for new tournaments is acceptable risk; historical reprocess is where data loss is irreversible |

## Concessions

- Phase 1 shipping is a genuine improvement. The sprite extraction and provenance columns are good architectural choices.
- The Operator's cost analysis shows reprocessing is cheap in infra terms. The cost is data quality, not dollars.
- The Strategist's 3-phase approach with value gates is sound. I am not blocking it. I am adding a gate within Phase 2.

## Non-Negotiables

- Do not reprocess until the normalizer is wired to the DB table (not the hardcoded dict).
- Do not reprocess until sprite coverage exceeds 80% on a recent sample.
- Do not reprocess without a queryable backup.
- The `auto_derive` hyphenation bug must be fixed or explicitly tracked before it generates thousands of records with malformed archetype names.
