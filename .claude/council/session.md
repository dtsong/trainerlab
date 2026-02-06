# Council Session: JP Archetype Data Pipeline Overhaul

Date: 2026-02-05
Phase: planning-complete
Slug: jp-archetype-data-pipeline-overhaul

## Phase 1 Implementation Status (COMPLETED)

PR #312 merged. Delivered:

- Fixed `_parse_jp_placement_row()` broken CSS selector
- Added `sprite_urls` field to `LimitlessPlacement`
- Created `ArchetypeNormalizer` service (sprite_lookup → auto_derive → signature_card → text_label)
- DB migrations 021/022 (archetype provenance columns + archetype_sprites table)
- Integrated normalizer into `TournamentScrapeService` (JP auto-creates, EN unaffected)
- 37 new tests (1643 total passing)

## Round 2 Deliberation (COMPLETED)

All 8 agents delivered challenge responses. Full synthesis: `deliberation/round2/SYNTHESIS.md`

### Key Outcomes

- **Bugs found:** hyphenation in `derive_name_from_key`, regex mismatch scraper vs normalizer, Mega `-mega` suffix, 13 missing archetypes in sprite map
- **Consensus:** Backfill in place (don't wipe), canary test 10-20 tournaments (>95% gate), golden datasets before reprocess, wire DB table, expand sprite map to 40+
- **Deferred:** Format Forecast widget, ML predictions, shadow mode, full doc suite
- **Timeline:** Phase 2 ~1.5-2 weeks → ship by ~Feb 21, buffer until April 10

### Concrete Bugs to Fix Before Phase 2

1. Align regex `[a-zA-Z0-9_-]+` in scraper (limitless.py:1341) to match normalizer
2. Expand `SPRITE_ARCHETYPE_MAP` from 24 → 40+ entries (cover >80% JP meta)
3. Add `-mega` suffix sprite keys (Mega Absol, Mega Kangaskhan, etc.)
4. Wire `ArchetypeNormalizer` to `archetype_sprites` DB table
5. Add structured logging to `resolve()`
6. Update CODEMAP.md + CLAUDE.md (45 min prerequisite)
