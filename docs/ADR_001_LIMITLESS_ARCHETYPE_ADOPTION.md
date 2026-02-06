# ADR-001: Adopt Limitless Sprite-Based Archetype Naming

## Status

Accepted (2026-02-06)

## Context

TrainerLab needs to identify and label deck archetypes from tournament placement data. Previously, archetype detection relied on a hand-maintained signature card map (`ArchetypeDetector`), which required manual updates whenever new sets were released or meta shifts introduced new archetypes.

Limitless TCG, the primary tournament data source, assigns sprite-based identifiers to archetypes (e.g., `charizard-ex-obsidian-flames` maps to a set of Pokemon sprites). These identifiers are widely recognized in the competitive community and update automatically with new tournament data.

## Decision

Adopt Limitless sprite-based archetype naming as the primary detection method via `ArchetypeNormalizer`.

**Priority chain:**

1. **sprite_lookup** - Match sprite keys from Limitless data against `SPRITE_ARCHETYPE_MAP` and `archetype_sprites` DB table
2. **auto_derive** - Derive archetype name from sprite Pokemon names
3. **signature_card** - Fallback to signature card matching (legacy `ArchetypeDetector`)
4. **text_label** - Use raw text label from Limitless as last resort

**Storage:**

- `SPRITE_ARCHETYPE_MAP` in `archetype_normalizer.py` for static mappings
- `archetype_sprites` DB table for runtime/curated overrides (admin-editable)
- `TournamentPlacement.archetype_detection_method` tracks provenance

## Consequences

### Positive

- Automatic coverage of new archetypes as Limitless adds them
- Visual consistency: sprite images from Limitless CDN can be displayed alongside archetype names
- Community familiarity: players recognize the sprite-based naming from Limitless
- Reduced maintenance burden vs. hand-curated signature card maps

### Negative

- Dependency on Limitless naming conventions; if they change sprite formats, we need to update
- Some edge cases (very new or fringe archetypes) may fall through to less reliable detection methods
- Historical data requires reprocessing to apply new detection (implemented via `/api/v1/admin/reprocess-archetypes` endpoint)

### Mitigations

- Admin CRUD for `archetype_sprites` table allows manual corrections
- Provenance tracking (`archetype_detection_method`) enables quality monitoring
- Reprocess endpoint enables bulk historical correction
