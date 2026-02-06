# Scout Final Position -- JP Archetype Data Pipeline Phase 2

## Revised Recommendation

The expanded `SPRITE_ARCHETYPE_MAP` (47 entries, up from 24) resolves most of the single-sprite coverage gap I flagged in Round 2. The regex mismatch between scraper and normalizer is also fixed -- both now use `r"/([a-zA-Z0-9_-]+)\.png"`. However, **three significant data quality issues remain** that must be addressed before the historical reprocess can meet the >95% accuracy gate:

1. **Multi-sprite composite keys are not mapped.** Archetypes using two sprites (a defining feature of JP meta) produce composite keys that miss the map entirely.
2. **Several archetype names in the map do not match Limitless community names.** This produces technically-functional but user-confusing labels.
3. **One new Mega Evolution archetype (Mega Lopunny ex, 0.51%) is missing from the `-mega` entries.**

## Evidence: Live Coverage Audit (2026-02-06)

I fetched the live Limitless JP meta (3-month view at `limitlesstcg.com/decks?time=3months&format=japanese`) and cross-referenced every archetype against the current `SPRITE_ARCHETYPE_MAP`.

### Coverage by sprite_lookup (single-sprite matches)

These archetypes have single-sprite keys that match entries in the map. They resolve via `sprite_lookup` and represent **88.72% of the JP meta by share**:

| Archetype          | Share  | Sprite Key           | Map Entry                            |
| ------------------ | ------ | -------------------- | ------------------------------------ |
| Dragapult ex       | 19.28% | `dragapult`          | `"Dragapult ex"`                     |
| Gardevoir ex       | 19.26% | `gardevoir`          | `"Gardevoir ex"`                     |
| Gholdengo ex       | 18.39% | `gholdengo`          | `"Gholdengo ex"`                     |
| Charizard ex       | 10.48% | `charizard`          | `"Charizard ex"`                     |
| Grimmsnarl ex      | 5.18%  | `grimmsnarl`         | `"Grimmsnarl ex"` -- see naming note |
| Raging Bolt ex     | 3.54%  | `raging-bolt`        | `"Raging Bolt ex"`                   |
| N's Zoroark ex     | 1.70%  | `zoroark`            | `"Zoroark ex"` -- see naming note    |
| Ceruledge ex       | 1.69%  | `ceruledge`          | `"Ceruledge ex"`                     |
| Flareon ex         | 1.53%  | `flareon`            | `"Flareon ex"`                       |
| Mega Kangaskhan ex | 1.28%  | `kangaskhan-mega`    | `"Mega Kangaskhan ex"`               |
| Alakazam           | 0.91%  | `alakazam`           | `"Alakazam ex"` -- see naming note   |
| Pidgeot Control    | 0.88%  | `pidgeot`            | `"Pidgeot ex Control"`               |
| Crustle            | 0.83%  | `crustle`            | `"Crustle ex"` -- see naming note    |
| Greninja ex        | 0.65%  | `greninja`           | `"Greninja ex"`                      |
| Froslass Munkidori | 0.65%  | `froslass-munkidori` | `"Froslass Munkidori"`               |

**Total single-sprite coverage: 86.25% of JP meta share.**

### Gaps: Multi-sprite composite keys (auto_derive fallback)

These archetypes use TWO sprites. `build_sprite_key` joins them with hyphens, producing composite keys that are NOT in the map. They fall to `auto_derive`:

| Archetype (Limitless name) | Share | Composite Key                | auto_derive Output           |
| -------------------------- | ----- | ---------------------------- | ---------------------------- |
| Mega Absol Box             | 7.24% | `absol-mega-kangaskhan-mega` | "Absol Mega Kangaskhan Mega" |
| Tera Box                   | 2.28% | `noctowl-ogerpon-wellspring` | "Noctowl Ogerpon Wellspring" |
| Joltik Box                 | 1.47% | `joltik-pikachu`             | "Joltik Pikachu"             |
| Ho-Oh Armarouge            | 0.24% | `ho-oh-armarouge`            | "Ho Oh Armarouge"            |

**Total multi-sprite gap: 11.23% of JP meta share.**

The `auto_derive` output is not terrible (it produces recognizable names) but fails to match community conventions. "Absol Mega Kangaskhan Mega" is clearly wrong -- the community name is "Mega Absol Box". "Noctowl Ogerpon Wellspring" is recognizable but the community calls it "Tera Box".

### Gap: Missing Mega Evolution entry

| Archetype       | Share | Sprite Key     | Status                                          |
| --------------- | ----- | -------------- | ----------------------------------------------- |
| Mega Lopunny ex | 0.51% | `lopunny-mega` | NOT in map. auto_derive produces "Lopunny Mega" |

### Summary: Total Coverage

- **sprite_lookup**: 86.25% of JP meta (correct archetype name via map)
- **auto_derive (acceptable)**: ~11.23% (recognizable but non-standard names)
- **auto_derive (wrong)**: ~0.51% (Mega Lopunny missing from map)
- **Total recognizable**: ~97.99% (sprite_lookup + auto_derive combined)

This **exceeds the >95% accuracy gate** for recognizability, but does NOT meet it for naming accuracy. The multi-sprite composite keys produce non-standard names for 11.23% of the meta.

## Naming Accuracy Issues

The following entries in the map use names that differ from Limitless community conventions:

| Sprite Key   | Current Map Name  | Limitless Community Name        | Impact                    |
| ------------ | ----------------- | ------------------------------- | ------------------------- |
| `grimmsnarl` | `"Grimmsnarl ex"` | `"Marnie's Grimmsnarl ex"`      | Loses trainer association |
| `zoroark`    | `"Zoroark ex"`    | `"N's Zoroark ex"`              | Loses trainer association |
| `alakazam`   | `"Alakazam ex"`   | `"Alakazam Powerful Hand"`      | Loses variant identifier  |
| `crustle`    | `"Crustle ex"`    | `"Crustle Mysterious Rock Inn"` | Loses variant identifier  |
| `noctowl`    | `"Noctowl Box"`   | `"Tera Box"`                    | Wrong primary identity    |

These naming mismatches are not blocking for Phase 2 reprocess (the archetypes are correctly identified, just named slightly differently). However, for user-facing display and cross-referencing with Limitless, the names should be aligned. The `archetype_sprites` DB table is the right place to fix these post-reprocess.

## Concessions Made

1. **Dropped: "DB table must be runtime source before reprocess."** I said this in Round 2, and still believe it long-term. However, the expanded in-code map achieves 86%+ sprite_lookup coverage, which is sufficient for the initial reprocess. The DB table wiring can happen in parallel as Task #4 from the synthesis plan. Pragmatism wins.

2. **Dropped: special-case `-mega` handling in `derive_name_from_key`.** With 8 explicit `-mega` entries in the map, the `auto_derive` fallback for Mega archetypes only matters for future archetypes we have not mapped. Adding all known Mega sprites to the map is sufficient. The `derive_name_from_key` method does not need special Mega logic.

3. **Dropped: "40+ entries required."** The map has 47 entries. I asked for 40+. Delivered. The remaining coverage gap is not about missing single-sprite entries but about multi-sprite composites, which is a different problem.

## Non-Negotiables

1. **Add multi-sprite composite keys for the top 3 composite archetypes before reprocess.** These three entries would close the 11% gap:
   - `"absol-mega-kangaskhan-mega"` -> `"Mega Absol Box"` (7.24%)
   - `"noctowl-ogerpon-wellspring"` -> `"Tera Box"` (2.28%)
   - `"joltik-pikachu"` -> `"Joltik Box"` (1.47%)

   Without these, 11% of the JP meta gets auto_derive names that differ from community conventions. This is the single highest-impact improvement remaining.

2. **Add `lopunny-mega` to the map.** Simple one-liner: `"lopunny-mega": "Mega Lopunny ex"`. This covers the only Mega archetype currently missing.

3. **Canary test must verify composite-key resolution.** The canary test (Task #8 from synthesis) must include at least one tournament where "Mega Absol Box" appears in the top 8, to confirm the composite key `absol-mega-kangaskhan-mega` resolves correctly after the map additions.

4. **Fix naming mismatches in the DB table (post-reprocess).** The 5 naming mismatches identified above should be corrected in the `archetype_sprites` DB table once it is wired. This is not a blocker for the initial reprocess but should be tracked.

## Implementation Notes

### Multi-sprite composite keys to add to SPRITE_ARCHETYPE_MAP

```python
# --- Multi-sprite composites (JP meta >0.5%) ---
"absol-mega-kangaskhan-mega": "Mega Absol Box",
"noctowl-ogerpon-wellspring": "Tera Box",
"joltik-pikachu": "Joltik Box",
"ho-oh-armarouge": "Ho-Oh Armarouge",
```

These are the composite keys produced by `build_sprite_key` when a placement has two sprite images. The key is the hyphen-joined lowercase filenames in image order.

**Key risk with composite keys:** The order of sprites in the HTML may vary (Limitless does not guarantee sprite order). For example, `absol-mega-kangaskhan-mega` might also appear as `kangaskhan-mega-absol-mega`. The current `build_sprite_key` implementation preserves HTML order. Options:

- Add both orderings to the map (brute force, 2x entries per composite)
- Sort the sprite names before joining (cleaner, but requires a code change to `build_sprite_key`)

I recommend sorting sprite names alphabetically before joining. This is a 1-line change in `build_sprite_key` (`names.sort()` before `"-".join(names)`) and eliminates the ordering ambiguity entirely. Without this, every 2-sprite archetype needs 2 map entries, and every 3-sprite archetype needs 6.

### Missing Mega entry

```python
"lopunny-mega": "Mega Lopunny ex",
```

### Archetypes to monitor (emerging, <0.5% share)

These archetypes appeared in the live JP meta below 0.5% and may grow:

| Sprite Key           | Limitless Name         | Current Share |
| -------------------- | ---------------------- | ------------- |
| `lucario-mega`       | Mega Lucario ex        | 0.22%         |
| `ursaluna-bloodmoon` | Bloodmoon Ursaluna     | 0.21%         |
| `typhlosion`         | Ethan's Typhlosion     | 0.17%         |
| `conkeldurr`         | Conkeldurr Gutsy Swing | 0.17%         |

The `lucario-mega` entry should be added proactively (already in the Mega cluster). The others can be added if they cross 0.5%.

### Regex alignment: VERIFIED

Both files now use identical regex patterns:

- `archetype_normalizer.py:106`: `_FILENAME_RE = re.compile(r"/([a-zA-Z0-9_-]+)\.png")`
- `limitless.py:1339`: `re.search(r"/([a-zA-Z0-9_-]+)\.png", src)`

The Round 2 synthesis flagged a regex mismatch, but examining the current codebase confirms both patterns include digits (`0-9`). This bug is either already fixed or was a misread in Round 2. No action needed.

### URL pattern: CONFIRMED

All JP sprite URLs observed on the live Limitless site use `https://r2.limitlesstcg.net/pokemon/gen9/{name}.png`. No alternative domains or path structures observed. The filename-only regex is robust against any future path changes.

### Card mapping gaps: NOT BLOCKING

As stated in Round 2, card mapping gaps (Nihil Zero cards without EN equivalents until March 27) do NOT affect sprite-based archetype detection. Card mapping is a parallel workstream for deck-level analysis. The sprite map is the source of truth for archetype labeling.

---

Sources:

- [LimitlessTCG JP Decks Meta (3-month, fetched 2026-02-06)](https://limitlesstcg.com/decks?time=3months&format=japanese)
- `SPRITE_ARCHETYPE_MAP` in `/Users/danielsong/Development/tcg/trainerlab/apps/api/src/services/archetype_normalizer.py:36-104` (47 entries)
- `_FILENAME_RE` in `/Users/danielsong/Development/tcg/trainerlab/apps/api/src/services/archetype_normalizer.py:106`
- `_extract_archetype_and_sprites_from_images` regex in `/Users/danielsong/Development/tcg/trainerlab/apps/api/src/clients/limitless.py:1339`
- `build_sprite_key` in `/Users/danielsong/Development/tcg/trainerlab/apps/api/src/services/archetype_normalizer.py:294-320`
