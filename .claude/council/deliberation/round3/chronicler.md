# Chronicler Round 3 -- Final Converged Position

## 1. Revised Recommendation

### Documentation State Audit (Post-Phase 1)

CLAUDE.md has been partially updated -- the Archetype Detection section and Current Focus section now exist and are accurate. This addresses my most urgent Round 2 concern about AI agents operating on stale instructions. Credit where due: this was done promptly.

CODEMAP.md was updated on 2026-02-06 (header timestamp) but the actual content is severely stale. My audit reveals the following drift between CODEMAP.md and the real codebase:

| Section    | CODEMAP says | Actual   | Gap                      |
| ---------- | ------------ | -------- | ------------------------ |
| Models     | 15 files     | 33 files | 18 undocumented models   |
| Services   | 13 files     | 25 files | 12 undocumented services |
| Routers    | 12 files     | 19 files | 7 undocumented routers   |
| Schemas    | 12 files     | 19 files | 7 undocumented schemas   |
| Pipelines  | 3 files      | 9 files  | 6 undocumented pipelines |
| Migrations | 22           | 23       | 1 missing (023)          |

The CODEMAP.md is not just missing Phase 1 archetype content. It is missing entire subsystems: evolution tracking, translation, widgets, data exports, API keys, cloud tasks, admin, placeholder cards, and more. The "last updated: 2026-02-06" timestamp is misleading because the content predates many features.

**This changes my recommendation.** In Round 2 I proposed a 45-minute CODEMAP.md + CLAUDE.md update. CLAUDE.md is done. But a proper CODEMAP.md update is larger than 30 minutes because the file has drifted much further than the archetype system alone.

### Final Documentation Plan (Priority Order)

**Tier 1: Before Phase 2 code begins (1-2 hours)**

1. **CODEMAP.md full refresh** -- Not a patch; a regeneration. Update all tables (models, services, routers, schemas, pipelines) to reflect the 33/25/19/19/9 actual file counts. Add missing entries. Update migration count to 23. Update the core structure tree. This is now a 60-90 minute task, not 30 minutes, because the drift is systemic.

2. **Verify CLAUDE.md accuracy** -- Already done. The Archetype Detection section and Current Focus are accurate. No further changes needed unless Phase 2 changes the priority chain.

**Tier 2: During Phase 2 (not blocking code, but before Phase 2 PR review)**

3. **ADR-001: Sprite-based archetype detection** -- Brief ADR documenting the decision to adopt Limitless sprites as primary archetype source. File: `docs/adr/001-sprite-based-archetype-detection.md`. This should exist before the Phase 2 PR is reviewed so reviewers understand the design rationale.

4. **DATA_DICTIONARY.md (archetype scope only)** -- Minimum viable data dictionary covering: archetype detection methods (4 valid values), sprite key format, SPRITE_ARCHETYPE_MAP vs archetype_sprites table, TournamentPlacement provenance columns. File: `docs/DATA_DICTIONARY.md`.

**Tier 3: Post-Phase 2 (cleanup)**

5. **SPEC.md Section 7.2 update** -- Update the archetype detection specification to match reality. Low urgency because CLAUDE.md and CODEMAP.md are the primary agent-facing docs.

---

## 2. Concessions Made

1. **Full doc suite does not block Phase 2.** I accept the council's consensus that ADR, DATA_DICTIONARY.md, SPEC.md overhaul, and OPERATIONS.md should not gate Phase 2 code. The Strategist's timeline concern is valid -- we cannot spend a week on documentation before coding.

2. **Golden dataset tests are higher priority than comprehensive docs.** The Craftsman's argument that executable tests catch regressions that docs cannot is correct. A golden dataset test that validates `archetype_detection_method` values is more reliable than a data dictionary entry listing them.

3. **CODEMAP.md update is larger than I originally estimated.** My Round 2 claim of "30 minutes for CODEMAP.md" was wrong. The drift is systemic (18 missing models, 12 missing services, 6 missing pipelines). A proper update is 60-90 minutes. I accept this but maintain it is still a prerequisite.

4. **ADR can be written during Phase 2, not before.** The Operator and Strategist are right that the ADR does not block implementation. Developers already have the working code; the ADR captures rationale for posterity, not for immediate use.

---

## 3. Non-Negotiables

1. **CODEMAP.md must be fully refreshed before Phase 2 code is written.** This is the single document that CLAUDE.md points developers to ("Use /docs/CODEMAP.md for efficient code traversal"). It currently describes a codebase that is 55% smaller than reality. Every developer and AI agent session starts by reading this file. If it says there are 13 services and there are 25, the agent will have blind spots covering half the codebase. This is not cosmetic debt; it is a navigation failure that compounds with every feature added.

2. **No more partial updates with misleading timestamps.** If CODEMAP.md says "Last updated: 2026-02-06" then the content must actually reflect the codebase as of that date. The current file has a fresh timestamp but stale content, which is worse than an honestly-dated stale file because it creates false confidence.

---

## 4. Implementation Notes

### CODEMAP.md Full Refresh

**File:** `/Users/danielsong/Development/tcg/trainerlab/docs/CODEMAP.md`

**Sections requiring updates:**

#### Core Structure tree (lines 33-53)

Update the comment counts:

- `models/` -- change "15 files" to "33 files"
- `schemas/` -- change "12 files" to "19 files"
- `routers/` -- change "12 files" to "19 files" (add admin.py)
- `services/` -- change "13 files" to "25 files"
- `pipelines/` -- change "3 files" to "9 files"

#### Database Models table (lines 56-75)

Add missing models:

- `Adaptation` (`adaptation.py`) -- Deck adaptation tracking
- `ArchetypeEvolutionSnapshot` (`archetype_evolution_snapshot.py`) -- Evolution snapshots
- `ArchetypePrediction` (`archetype_prediction.py`) -- Archetype predictions
- `EvolutionArticle` (`evolution_article.py`) -- Generated evolution articles
- `EvolutionArticleSnapshot` (`evolution_article_snapshot.py`) -- Article snapshots
- `ApiKey` (`api_key.py`) -- API key management
- `ApiRequest` (`api_request.py`) -- API request logging
- `DataExport` (`data_export.py`) -- Data export records
- `JPCardAdoptionRate` (`jp_card_adoption_rate.py`) -- JP card adoption tracking
- `JPUnreleasedCard` (`jp_unreleased_card.py`) -- Unreleased JP cards
- `TranslatedContent` (`translated_content.py`) -- Translated content
- `TranslationTermOverride` (`translation_term_override.py`) -- Translation overrides
- `Widget` (`widget.py`) -- Embeddable widgets
- `WidgetView` (`widget_view.py`) -- Widget analytics
- `PlaceholderCard` (`placeholder_card.py`) -- Placeholder card data
- `CardIdMapping` (`card_id_mapping.py`) -- JP-EN card ID mappings
- `LabNoteRevision` (`lab_note_revision.py`) -- Lab note revision history
- `TournamentPlacement` (`tournament_placement.py`) -- already listed but verify provenance columns noted

#### API Routers table (lines 78-92)

Add missing routers:

- `admin.py` -- Admin panel endpoints
- `api_keys.py` -- API key management
- `exports.py` -- Data export endpoints
- `public_api.py` -- Public API for widgets
- `translations.py` -- Translation endpoints
- `widgets.py` -- Widget CRUD
- `evolution.py` -- Evolution tracking endpoints

#### Services table (lines 95-109)

Add missing services:

- `cloud_tasks.py` -- GCP Cloud Tasks integration
- `decklist_diff.py` -- Decklist comparison
- `evolution_service.py` -- Archetype evolution tracking
- `adaptation_classifier.py` -- Deck adaptation classification
- `prediction_engine.py` -- Meta prediction engine
- `api_key_service.py` -- API key management
- `data_export_service.py` -- Data export generation
- `evolution_article_generator.py` -- Evolution article generation
- `storage_service.py` -- GCS storage operations
- `translation_service.py` -- Translation orchestration
- `widget_service.py` -- Widget management
- `placeholder_service.py` -- Placeholder card generation

#### Pipelines table (lines 112-118)

Add missing pipelines:

- `compute_evolution.py` -- Compute archetype evolution snapshots
- `monitor_card_reveals.py` -- Monitor JP card reveals
- `sync_jp_adoption_rates.py` -- Sync JP card adoption rates
- `translate_pokecabook.py` -- Translate Pokecabook content
- `translate_tier_lists.py` -- Translate JP tier lists
- `sync_card_mappings.py` -- already listed, verify accurate

#### Migration count (line 129)

Update from "22 migrations" to "23 migrations"

#### Schemas

Add a schemas table or note (currently not enumerated). At minimum update the parenthetical count.

### CLAUDE.md -- No Changes Needed

The Archetype Detection section (lines 54-60) and Current Focus section (lines 74-77) are accurate as of today. The Key Decisions section (lines 46-52) includes the sprite-based detection note. No action required.

### ADR-001 (During Phase 2)

**File:** `docs/adr/001-sprite-based-archetype-detection.md`

```
# ADR-001: Sprite-Based Archetype Detection

## Status
Accepted (implemented in PR #311, #312)

## Context
- Signature card detection required manual curation of 95+ mappings
- Each new set/format required code changes to SIGNATURE_CARDS
- JP cards without EN mappings defaulted to "Rogue"
- Limitless already provides authoritative archetype identity via sprite images

## Decision
Adopt Limitless sprite filenames as primary archetype source via
ArchetypeNormalizer with priority chain:
sprite_lookup > auto_derive > signature_card > text_label

## Consequences
- Reduced maintenance for new archetypes (sprites auto-resolve)
- Dependency on Limitless HTML structure for sprite URL extraction
- SPRITE_ARCHETYPE_MAP needs seeding for known multi-sprite archetypes
- archetype_sprites DB table provides runtime override without code deploy
- archetype_detection_method on TournamentPlacement tracks provenance
```

### DATA_DICTIONARY.md (During Phase 2)

**File:** `docs/DATA_DICTIONARY.md`

Scope limited to archetype detection system:

1. **archetype_detection_method values:**
   - `sprite_lookup` -- Matched via SPRITE_ARCHETYPE_MAP or archetype_sprites table
   - `auto_derive` -- Derived from single sprite key (no map entry needed)
   - `signature_card` -- Matched via legacy SIGNATURE_CARDS fallback
   - `text_label` -- Raw text label from Limitless (no sprite data available)

2. **Sprite key format:** Lowercase, hyphen-joined Pokemon names extracted from Limitless sprite image filenames. Example: `charizard-pidgeot`, `lugia-vstar`.

3. **SPRITE_ARCHETYPE_MAP vs archetype_sprites table:**
   - `SPRITE_ARCHETYPE_MAP`: In-code dict in `archetype_normalizer.py`. Checked first. Covers ~24 known multi-sprite archetypes. Requires code deploy to update.
   - `archetype_sprites` table: DB table checked second. Runtime override. Managed via admin endpoints. No deploy needed.

4. **TournamentPlacement provenance columns:**
   - `raw_archetype` (String, nullable) -- Original archetype label from source
   - `raw_archetype_sprites` (JSONB, nullable) -- Array of sprite URL strings from Limitless
   - `archetype_detection_method` (String, nullable) -- Which strategy produced the final archetype label

---

## Summary

| Item                    | Priority | Timing                           | Estimated Effort |
| ----------------------- | -------- | -------------------------------- | ---------------- |
| CODEMAP.md full refresh | **MUST** | Before Phase 2 code              | 60-90 min        |
| CLAUDE.md verification  | **DONE** | Already complete                 | 0 min            |
| ADR-001                 | SHOULD   | During Phase 2, before PR review | 20 min           |
| DATA_DICTIONARY.md      | SHOULD   | During Phase 2, before PR review | 30 min           |
| SPEC.md Section 7.2     | NICE     | Post-Phase 2                     | 30 min           |

**Total blocking work: 60-90 minutes (CODEMAP.md only).**

The key insight from this round: the documentation gap is not limited to the archetype system. CODEMAP.md has drifted from reality by 18 models, 12 services, 7 routers, and 6 pipelines. A targeted patch for archetype content alone would leave the file misleading about half the codebase. The right move is a full refresh -- one pass, accurate counts, no partial fixes with false timestamps.
