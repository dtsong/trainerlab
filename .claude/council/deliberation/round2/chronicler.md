# Chronicler Round 2 -- JP Archetype Data Pipeline Overhaul

## Documentation Debt from Phase 1: The Situation Is Worse Than I Predicted

PR #312 shipped real architectural changes. The codebase now contains:

- `ArchetypeNormalizer` service (`/apps/api/src/services/archetype_normalizer.py`) with a four-strategy priority chain
- `ArchetypeSprite` model (`/apps/api/src/models/archetype_sprite.py`) as a new ORM entity
- `SPRITE_ARCHETYPE_MAP` with ~24 known mappings baked into code
- `TournamentPlacement` model with three new columns: `raw_archetype`, `raw_archetype_sprites`, `archetype_detection_method`
- Two new Alembic migrations: 021 (archetype provenance) and 022 (archetype_sprites table)
- `sprite_urls: list[str]` added to the `LimitlessPlacement` dataclass

**None of this is documented.** Here is what the docs currently say:

- **CODEMAP.md** (last updated 2026-02-02): Lists `archetype_detector.py` as "Detect deck archetype from signature cards." No mention of `archetype_normalizer.py`, `ArchetypeSprite` model, or the provenance columns. The migration count says "~14" when there are now 22. The services table lists 12 services; there are now at least 13.
- **CLAUDE.md**: Current Focus section still reads "Building card database + search / Next: deck builder MVP." This is months out of date.
- **SPEC.md**: Section 7.2 still describes signature card detection as the primary system. No mention of sprite-based extraction.

A developer (human or AI) reading these docs will build on the wrong mental model. They will call `ArchetypeDetector.detect()` directly instead of routing through `ArchetypeNormalizer`. They will not know that `TournamentPlacement.archetype_detection_method` exists and should be populated. They will add new archetypes to `SIGNATURE_CARDS` instead of `SPRITE_ARCHETYPE_MAP`.

This is not theoretical. It is the exact scenario that will happen in the next sprint when Phases 2-3 begin.

---

## Challenges to Other Agents

### Strategist: "Docs after implementation" is how knowledge dies

The Strategist's phased plan (Sprint 1-3, 6 weeks, hard April 10 cutoff) is sensible for sequencing features. But the implicit assumption is that documentation follows implementation -- Phase 4 cleanup territory. This is the pattern that created the current mess.

Phase 1 is done. Phase 2 (historical reprocess) starts next. Every developer touching the pipeline in Phase 2 will need to understand:

1. What is the priority chain in `ArchetypeNormalizer`? (sprite_lookup, auto_derive, signature_card, text_label)
2. What columns on `TournamentPlacement` are new and what do they store?
3. What is `SPRITE_ARCHETYPE_MAP` and how does it differ from `SIGNATURE_CARDS`?

Without updated docs, the Phase 2 implementer will reverse-engineer this from code. That is expensive and error-prone. Documentation is not Phase 4 polish; it is Phase 2 prerequisite.

**My position: Update CODEMAP.md and CLAUDE.md before Phase 2 starts. This is a 30-minute task, not a multi-day effort.**

### Architect: Your schema proposal is already partially stale

The Architect's Round 1 position proposed `archetype_sprites` table and `archetype_detection_method` column with values `('sprite', 'signature_card', 'manual', 'unknown')`. Phase 1 shipped different values: `('sprite_lookup', 'auto_derive', 'signature_card', 'text_label')`. The `archetype_sprites` table shipped with columns `sprite_key`, `archetype_name`, `sprite_urls`, `pokemon_names` -- not the proposed `sprite_order`, `version`, `is_active`, `first_seen_date`, etc.

This divergence between plan and reality is normal. But it means the Architect's Round 1 document is now a misleading reference. Phase 2 implementers must not treat it as the source of truth for the current schema.

**My position: The data dictionary should document what was actually shipped, not what was proposed.**

### Craftsman: Golden datasets need documented schema

The Craftsman's golden dataset testing strategy is excellent. But golden datasets are useless without a data dictionary. What does a correct `archetype_detection_method` look like? What values are valid? What does `raw_archetype_sprites` contain -- Pokemon names or full URLs? (Answer: it is a JSONB array of strings, but the content depends on the scraper implementation.)

The Craftsman needs the data dictionary to write correct assertions. This is a dependency I flagged in Round 1 and it remains unresolved.

### Skeptic: Your risk analysis validates my urgency

The Skeptic's analysis of silent data corruption and cascading failures is correct. I add one risk the Skeptic missed: **documentation-driven corruption**. When an AI agent reads CODEMAP.md, sees "Detect deck archetype from signature cards," and generates code that bypasses the normalizer, it introduces the exact class of bugs the Skeptic is worried about. Stale docs are not just annoying -- they are a vector for production bugs.

---

## Minimum Viable Data Dictionary

The Architect and Craftsman both need a data dictionary. Here is the minimum viable version covering only what Phase 1 shipped. This is not the full dictionary I proposed in Round 1; this is the subset needed to unblock Phase 2.

**Scope:** Archetype detection system only. Card ID mapping, tier calculations, and placeholder cards are documented later.

The dictionary should cover:

1. **Archetype detection methods** -- the four valid values for `archetype_detection_method` and when each is used
2. **Sprite key format** -- lowercase, hyphen-joined Pokemon names from Limitless sprite URLs (e.g., `charizard-pidgeot`)
3. **SPRITE_ARCHETYPE_MAP** -- what it is, where it lives, how to add entries
4. **TournamentPlacement provenance columns** -- `raw_archetype`, `raw_archetype_sprites`, `archetype_detection_method`
5. **ArchetypeSprite table** -- columns, purpose, relationship to the in-code `SPRITE_ARCHETYPE_MAP`

---

## Concrete Documentation Plan

### 1. CODEMAP.md updates (MUST do before Phase 2)

**File:** `/Users/danielsong/Development/tcg/trainerlab/docs/CODEMAP.md`

Changes needed:

- **Database Models table:** Add `ArchetypeSprite` row (`archetype_sprite.py` / "Sprite-key to archetype mapping")
- **Services table:** Add `archetype_normalizer.py` row ("Archetype normalization with priority chain: sprite_lookup > auto_derive > signature_card > text_label"). Update `archetype_detector.py` description to "Signature card detection (fallback for ArchetypeNormalizer)"
- **Migration count:** Update from "~14 migrations" to "22 migrations"
- **Key Algorithms section:** Update "Archetype Detection" to reference `ArchetypeNormalizer` priority chain instead of just signature card scanning
- **Data section:** Update description from "Static data (signature cards)" to "Static data (signature cards, sprite archetype map)"

### 2. CLAUDE.md updates (MUST do before Phase 2)

**File:** `/Users/danielsong/Development/tcg/trainerlab/CLAUDE.md`

Changes needed:

- **Current Focus section:** Replace stale content with:

  ```
  - JP archetype data pipeline overhaul (sprite-based detection, historical reprocess)
  - Next: Phase 2 historical reprocess + meta recomputation
  ```

- **Key Decisions section:** Add:

  ```
  - Archetype detection: Sprite-based (from Limitless) with signature card fallback
  - Archetype naming: Follows LimitlessTCG sprite conventions
  ```

- **Add new section "Archetype Detection"** after Key Decisions:

  ```
  ## Archetype Detection

  - Primary: ArchetypeNormalizer (src/services/archetype_normalizer.py)
  - Priority chain: sprite_lookup > auto_derive > signature_card > text_label
  - Sprite map: SPRITE_ARCHETYPE_MAP in archetype_normalizer.py (~24 entries)
  - Legacy: ArchetypeDetector (src/services/archetype_detector.py) is fallback only
  - DB: archetype_sprites table maps sprite keys to canonical names
  - Provenance: TournamentPlacement.archetype_detection_method tracks which strategy produced the label
  ```

### 3. ADR for sprite adoption decision (SHOULD do this week)

**File:** `/Users/danielsong/Development/tcg/trainerlab/docs/adr/001-sprite-based-archetype-detection.md`

Brief format:

- **Status:** Accepted (implemented in PR #312)
- **Context:** Signature card detection required manual curation of 95+ card-to-archetype mappings. Each new set required code changes. JP cards without EN mappings produced "Rogue" labels. Limitless already provides authoritative archetype identity via sprite images.
- **Decision:** Adopt Limitless sprite filenames as primary archetype source. Use `ArchetypeNormalizer` with priority chain. Keep signature card detection as fallback.
- **Consequences:** Reduced maintenance burden for new archetypes. Dependency on Limitless HTML structure for sprite URLs. In-code `SPRITE_ARCHETYPE_MAP` needs manual seeding for known mappings. New `archetype_sprites` DB table provides runtime override.

### 4. DATA_DICTIONARY.md minimum viable version (SHOULD do this week)

**File:** `/Users/danielsong/Development/tcg/trainerlab/docs/DATA_DICTIONARY.md`

Phase 1 scope only:

- **Archetype Detection Methods:** Table of four valid values with descriptions
- **Sprite Key Format:** Definition, examples, extraction regex
- **SPRITE_ARCHETYPE_MAP vs archetype_sprites table:** When each is consulted, how they interact
- **TournamentPlacement Provenance Columns:** Column name, type, nullable, description for `raw_archetype`, `raw_archetype_sprites`, `archetype_detection_method`

Full data dictionary (card IDs, tier calculations, BO1 semantics, placeholder lifecycle) deferred to Phase 2-3.

---

## Priority Ordering

**If we can only do 2 doc updates this week:**

1. **CODEMAP.md** -- This is the primary navigation document referenced by CLAUDE.md. Every developer and AI agent reads it first. It is currently factually wrong about the archetype system and missing a model and a service. 30 minutes of work.

2. **CLAUDE.md** -- This is the instruction set for AI agent sessions. The "Current Focus" section tells agents what we are working on. The missing "Archetype Detection" section means agents will not know the normalizer exists. 15 minutes of work.

These two updates cost 45 minutes total and prevent the most likely class of errors: developers building on top of stale knowledge about how archetype detection works.

The ADR and DATA_DICTIONARY.md are important but deferrable by days, not weeks. They should be completed before Phase 2 code review, not necessarily before Phase 2 begins.

---

## Concessions

- I concede to Strategist that the full documentation suite (SPEC.md overhaul, SCRAPER_ARCHITECTURE.md update, operations runbook) should not block Phase 2 work.
- I concede to Craftsman that golden dataset tests are a higher priority than comprehensive docs for pipeline correctness.
- I do not concede that documentation can wait until after Phase 2 ships. CODEMAP.md and CLAUDE.md updates are 45 minutes of work that prevent hours of confusion.

## Non-Negotiables

1. **CODEMAP.md must reflect the `ArchetypeNormalizer` service and `ArchetypeSprite` model before any Phase 2 code is written.** This is the single most likely source of knowledge errors in the next sprint.
2. **CLAUDE.md Current Focus must be updated.** An AI agent reading "Building card database + search" will not understand the codebase context for any archetype-related work.
