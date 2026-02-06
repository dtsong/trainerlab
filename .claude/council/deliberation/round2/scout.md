# Scout Round 2 -- JP Archetype Pipeline: Evidence-Based Challenges

## 1. Sprite Map Completeness: 24 Entries vs. the Actual Meta

The current `SPRITE_ARCHETYPE_MAP` in `/Users/danielsong/Development/tcg/trainerlab/apps/api/src/services/archetype_normalizer.py` has 24 entries (counting order-variant duplicates like `comfey-sableye` / `sableye-comfey`). Cross-referencing against the live Limitless JP meta (3-month view, fetched 2026-02-06), here is what is **missing**:

### Archetypes with >0.5% JP meta share NOT in the sprite map

| Sprite key (from Limitless URL) | JP Meta Share | Current map status                                                      |
| ------------------------------- | ------------- | ----------------------------------------------------------------------- |
| `absol-mega`                    | 7.24%         | MISSING                                                                 |
| `grimmsnarl`                    | 5.18%         | MISSING                                                                 |
| `noctowl` (Tera Box)            | 2.28%         | MISSING                                                                 |
| `zoroark` (N's Zoroark ex)      | 1.70%         | MISSING                                                                 |
| `ceruledge`                     | 1.69%         | MISSING                                                                 |
| `flareon`                       | 1.53%         | MISSING                                                                 |
| `joltik` (Joltik Box)           | 1.47%         | MISSING                                                                 |
| `kangaskhan-mega`               | 1.28%         | MISSING                                                                 |
| `alakazam`                      | 0.91%         | MISSING                                                                 |
| `pidgeot` (Control)             | 0.88%         | mapped as Pidgeot ex Control via signature cards, but NOT in sprite map |
| `crustle`                       | 0.83%         | MISSING                                                                 |
| `greninja`                      | 0.65%         | MISSING                                                                 |
| `froslass` (Froslass Munkidori) | 0.65%         | MISSING                                                                 |

**Impact assessment:** The 24 existing entries cover 4 of the top 7 JP archetypes (Dragapult 19.28%, Gardevoir 19.26%, Gholdengo 18.39%, Charizard 10.48%). But archetypes #5 through #13 (totaling roughly 22% of the JP meta) will ALL fall through to `auto_derive`, producing names like "Absol Mega", "Kangaskhan Mega", "Noctowl" instead of the community-standard names "Mega Absol Box", "Mega Kangaskhan ex", and "Tera Box".

**The `-mega` suffix is a critical problem.** Limitless uses `absol-mega.png` and `kangaskhan-mega.png` for Mega Evolution archetypes. The current `build_sprite_key` will produce `absol-mega` and `kangaskhan-mega` as keys. The `derive_name_from_key` will then split on hyphens and produce "Absol Mega" -- which is wrong. The community name is "Mega Absol Box". This is a systemic naming issue for the entire Mega Evolution era (which is the current JP format).

**Recommendation:** Add at minimum these 13 entries to `SPRITE_ARCHETYPE_MAP` before any reprocess. The Mega Evolution era means `-mega` suffixed sprites will be common going forward. Consider a special case in `derive_name_from_key` that detects `-mega` and reorders to "Mega {Name} ex".

### Entries that may be stale

Several entries in the map reference VSTAR-era archetypes (Lugia VSTAR, Palkia VSTAR, Giratina VSTAR, Arceus VSTAR) that have rotated out of the current JP Standard format. They are not harmful (they simply will not match any current sprites) but they inflate the apparent coverage. The effective coverage for the current JP meta is closer to 10-12 unique entries mapping to ~67% of meta share, with the remaining ~33% falling to auto_derive or worse.

## 2. URL Pattern Analysis

Based on direct observation of Limitless tournament pages (City League Kanagawa 02/03, plus the JP decks meta page):

**All sprite URLs follow a single pattern:** `https://r2.limitlesstcg.net/pokemon/gen9/{name}.png`

No instances of the `limitlesstcg.com/img/pokemon` pattern were observed on current JP tournament pages. The codebase handles both patterns defensively (the `_FILENAME_RE` regex `/([a-zA-Z0-9_-]+)\.png` will match either), which is correct. However:

- **The `gen9` directory may change.** When Limitless eventually starts a new generational directory (gen10 or similar), the regex will still work since it only matches the filename, not the path. This is a good design.
- **The `-mega` suffix is a new convention** not seen in gen9 base sprites. It appears Limitless added `absol-mega.png`, `kangaskhan-mega.png`, `froslass-mega.png`, `starmie-mega.png` for the Mega Evolution expansion. This suffix was not anticipated in the original SPRITE_ARCHETYPE_MAP seeding.
- **No alternative CDN domains were observed.** All sprites come from `r2.limitlesstcg.net`. The `limitless3.nyc3.cdn.digitaloceanspaces.com` domain is used for logos, not Pokemon sprites.

**Assessment:** The URL parsing is robust. The gap is not in extraction but in the mapping layer downstream.

## 3. Challenge Responses

### Challenge to Architect -- Naming Granularity

**Their position:** Three-layer architecture (ingestion, normalization, analysis) with versioned normalization. Store `raw_archetype` immutably, normalize separately.

**My response:** Maintain with modification.

The three-layer design is sound. However, the Architect's examples assume sprite names cleanly map to community conventions. The real Limitless data shows this assumption is fragile:

- `noctowl.png` does NOT mean "Noctowl ex" -- it means "Tera Box" (a toolbox deck where Noctowl is the engine, not the archetype identity).
- `grimmsnarl.png` does NOT mean "Grimmsnarl ex" -- it means "Marnie's Grimmsnarl ex" (a trainer-Pokemon pairing specific to the Mega Dream expansion).
- `froslass.png` paired with `munkidori.png` means "Froslass Munkidori" -- the `auto_derive` output "Froslass Munkidori" is actually correct here, but "Froslass" alone would be wrong.

The Architect's `_sprite_to_canonical` method (appending " ex" by default) will misname many decks. The auto_derive fallback in the actual implementation (Phase 1 code) does not append " ex", which is better, but it still produces generic names for decks with community-specific branding (Tera Box, Lost Zone Box, etc.).

**Concrete recommendation:** The `archetype_sprites` DB table should be the primary normalization source, not the in-code `SPRITE_ARCHETYPE_MAP`. Seed it with 40+ entries covering current JP meta AND current EN meta. Make it editable via admin panel. The in-code map is a useful bootstrap cache but should not be the source of truth for production.

### Challenge to Skeptic -- Root-Cause Analysis Scope

**Their position:** Full audit trail of Cinderace failure before any re-scrape. Trace end-to-end with specific tournament URL.

**My response:** Partially defer.

The Skeptic is right that understanding failure modes matters, but Phase 1 (PR #312) has already shipped the fix for the scraper-level issue (broken CSS selector). The Cinderace-specific bug was a **scraping failure** (wrong CSS selector `img.pokemon` that returned nothing), not a card mapping failure. The sprite extraction now works.

The remaining card mapping issues (JP card IDs not matching EN equivalents) are real but are a **separate concern** from the archetype labeling pipeline. With sprite-based archetype detection as the primary method, card mapping errors no longer cascade into archetype misclassification. They only affect deck-level analysis (tech card counting, card inclusion rates).

The Skeptic's demand for "full root-cause analysis BEFORE re-scrape" would delay Phase 2 by 1-2 weeks for diminishing returns. The sprite-based approach inherently bypasses the failure path they are tracing. I recommend proceeding with the Strategist's phased timeline while documenting card mapping gaps as a parallel workstream.

## 4. Card Mapping Intelligence: JP-Exclusive Cards

### Current JP-EN Card Gap

The primary gap is between JP sets that have been released and their EN equivalents:

- **Nihil Zero** (JP release: Jan 23, 2026) -- No EN equivalent yet. EN set "Perfect Order" expected March 27, 2026.
- **Black Bolt / White Flare** (JP release: June 2025) -- These were the final Scarlet & Violet era sets. Cards may have been folded into EN sets differently.
- **JP promos** -- Japan has a significantly larger promo card pool. Many promo cards are alternate art versions of existing cards (which map fine for archetype purposes) but some are functionally unique.

### Impact on Signature Card Detection

JP-exclusive cards that define new archetypes (like the Mega Evolution cards from Mega Dream ex / Nihil Zero) will NOT have EN signature card entries because those sets have not released in English yet. This is exactly why sprite-based detection is superior: Limitless uses the same sprites regardless of card set origin.

For decklist-level analysis specifically:

- Cards from Mega Dream ex largely correspond to EN Ascended Heroes (released Jan 30, 2026), so card mappings should be largely available.
- Cards from Nihil Zero have no EN equivalent until Perfect Order (March 27). These are the primary gap.
- JP promo cards used competitively (Extra Battle Day promos, pre-order bonuses) typically have EN functional equivalents but different card IDs.

**Practical impact:** For the ~33% of the JP meta running Nihil Zero cards (rough estimate based on Mega Absol, Mega Kangaskhan, and other new archetypes using Nihil Zero cards), card-level analysis will be incomplete until March 27. Archetype-level analysis via sprites will work fine regardless.

### Recommendation

Do not block Phase 2 (historical reprocess) on card mapping completeness. The sprite-based archetype system is specifically designed to be independent of card-level translation. Card mapping is a separate, ongoing maintenance task.

## 5. Prediction Feasibility Assessment

### Data Quality Threshold for Divergence-Based Predictions

Given Phase 1 improvements, here is my assessment of prediction viability:

**What works now (no ML needed):**

- Simple JP meta share snapshots (e.g., "Dragapult is 19% of JP meta") -- works as soon as archetype labels are correct
- JP vs EN meta share comparison (e.g., "Dragapult is 19% in JP, 14% in EN") -- works with correct archetype mapping across regions
- Trend direction (e.g., "Gholdengo rose from 10% to 18% over 60 days") -- works with 60+ days of clean data

**What requires minimum data quality:**

- Divergence-based leading indicator ("JP meta 60 days ago predicted EN meta today") requires:
  - At minimum 90 days of clean JP data (currently compromised, needs reprocess)
  - Archetype label consistency across JP and EN (sprite-based normalization solves this)
  - BO1 correction factor for control/stall archetypes (Pidgeot Control, Snorlax Stall are inflated or deflated in JP BO1 data)
  - Sample size: JP City Leagues produce roughly 3000-5000 top placements per month. This is statistically sufficient for top-10 archetype tracking.

**What does NOT work yet:**

- Quantitative meta share forecasting ("Dragapult will be X% in EN after April 10") -- insufficient historical validation data. We have zero completed prediction cycles to calibrate against.
- Confidence intervals on predictions -- need at least 2-3 set release cycles with clean data to build a statistical model.

**My recommendation aligns with the Strategist:** Ship descriptive JP intelligence (comparisons, trends, divergences) for April 10. Defer quantitative forecasting until we have one complete prediction cycle (April 10 rotation) to validate against. The Advocate's "Format Forecast" widget should use qualitative confidence levels (High/Medium/Low) based on sample size and archetype familiarity, not computed prediction intervals.

### Minimum viable prediction quality

For the April 10 moment, TrainerLab needs:

1. Accurate JP meta shares (requires Phase 1 + Phase 2 reprocess)
2. Correct archetype name parity between JP and EN (requires expanded SPRITE_ARCHETYPE_MAP)
3. BO1 flagging on control archetypes (already implemented in existing code)
4. Simple divergence display: "This archetype is X% more popular in JP than EN"

This is achievable within the Strategist's 4-week timeline (Phase 1 + Phase 2) without any ML infrastructure.

## Summary of Non-Negotiable Recommendations

1. **Expand SPRITE_ARCHETYPE_MAP immediately** from 24 to 40+ entries, covering all archetypes above 0.5% JP meta share. Prioritize the Mega Evolution `-mega` suffix handling.
2. **Move the sprite map to the `archetype_sprites` DB table** as the primary source, with in-code map as bootstrap-only fallback.
3. **Do not block on card mapping completeness** for the archetype pipeline. Sprite-based detection is independent of card translation.
4. **Ship descriptive JP intelligence for April 10**, defer quantitative forecasting.
5. **Handle the `-mega` suffix** in `derive_name_from_key` or expand the map. The current Mega Evolution era makes this a top-priority correctness issue.

---

Sources:

- [LimitlessTCG JP Decks Meta (3-month)](https://limitlesstcg.com/decks?time=3months&format=japanese)
- [LimitlessTCG JP Tournaments](https://limitlesstcg.com/tournaments/jp)
- [City League Kanagawa 02/03](https://limitlesstcg.com/tournaments/jp/3957)
- [2026 LAIC Power Rankings (Pokemon.com)](https://www.pokemon.com/us/pokemon-news/2026-latin-america-international-championships-pokemon-tcg-power-rankings)
- [JustInBasil Standard Meta](https://www.justinbasil.com/guide/meta)
- [PokeBeach SV-era Unreleased Cards](https://www.pokebeach.com/forums/threads/list-of-scarlet-violet-era-unreleased-exclusive-cards.154137/)
- [Upcoming Pokemon TCG Sets 2026](https://boundbyflame.com/upcoming-pokemon-tcg-sets/)
