# Architect Position — Japanese Tournament Data Pipeline Redesign

## Core recommendation

**Replace manual signature card detection with sprite-pair extraction as the primary archetype source of truth, refactor the pipeline into three distinct layers (ingestion → normalization → analysis), and implement zero-downtime data reprocessing with archetype versioning.**

## Key argument

The current architecture conflates three concerns: data ingestion (LimitlessClient), identity mapping (ArchetypeDetector + SIGNATURE_CARDS), and meta computation (MetaService). This tight coupling creates cascading correctness issues — a single wrong card mapping (Cinderace EX → JP set mismatch) pollutes all downstream meta shares, tier assignments, and JP signals.

**The fundamental architectural problem is treating archetype detection as a mapping problem when it's actually a multi-stage data normalization pipeline.** Limitless already provides authoritative archetype labels via sprite-pair filenames (e.g., `dragapult-charizard.png`), but we're ignoring this ground truth in favor of brittle heuristic detection.

The solution is a **three-layer data architecture**:

1. **Layer 1 — Raw Ingestion**: Extract sprite pairs from Limitless HTML as immutable archetype identifiers. Store them verbatim (e.g., `"dragapult-charizard"`) with full decklist JSONB in `tournament_placements.raw_archetype` field.

2. **Layer 2 — Normalization**: Map sprite pairs → canonical archetype names via versioned lookup table (`archetype_sprites` table). Backfill `tournament_placements.archetype` from `raw_archetype` using current normalization rules. This decouples scraping from naming conventions.

3. **Layer 3 — Analysis**: Compute meta shares, JP signals, and predictive models from normalized `archetype` field. All analysis layers reference the same clean names.

This architecture enables:

- **Reprocessable history**: Change normalization rules without re-scraping (raw data persists)
- **Auditable corrections**: Compare `raw_archetype` vs `archetype` to detect mapping drift
- **A/B testing archetypes**: Run parallel normalization strategies on same raw data
- **Incremental rollout**: Backfill clean data without blocking new scrapes

## Proposed schema changes

### 1. Add raw archetype storage to placements

```sql
ALTER TABLE tournament_placements
ADD COLUMN raw_archetype TEXT NULL,           -- Sprite-based ID from Limitless
ADD COLUMN raw_archetype_sprites JSONB NULL,  -- ["dragapult", "charizard"] ordered
ADD COLUMN archetype_version INT DEFAULT 1;   -- Normalization version applied

CREATE INDEX idx_placements_raw_archetype
ON tournament_placements(raw_archetype)
WHERE raw_archetype IS NOT NULL;

COMMENT ON COLUMN tournament_placements.raw_archetype IS
'Immutable sprite-pair identifier from Limitless (e.g., "dragapult-charizard")';
COMMENT ON COLUMN tournament_placements.archetype IS
'Normalized canonical archetype name (e.g., "Dragapult Charizard ex")';
```

### 2. Create archetype normalization table

```sql
CREATE TABLE archetype_sprites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sprite_key TEXT NOT NULL UNIQUE,          -- "dragapult-charizard"
    canonical_name TEXT NOT NULL,             -- "Dragapult Charizard ex"
    sprite_order TEXT[] NOT NULL,             -- ["dragapult", "charizard"]
    version INT NOT NULL DEFAULT 1,           -- Normalization schema version
    is_active BOOLEAN DEFAULT TRUE,

    -- Metadata
    first_seen_date DATE,                     -- First JP tournament appearance
    first_en_date DATE,                       -- First EN tournament appearance
    notes TEXT,                               -- Human notes on naming decisions

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_archetype_sprites_canonical ON archetype_sprites(canonical_name);
CREATE INDEX idx_archetype_sprites_version ON archetype_sprites(version);
```

### 3. Deprecate SIGNATURE_CARDS in favor of card mappings

**Do not delete** `src/data/signature_cards.py` immediately — use it as **validation fallback** during transition. New flow:

1. Primary: Sprite-pair → canonical name (from `archetype_sprites`)
2. Fallback: If sprite parse fails, use signature card detection on decklist
3. Validation: Log warnings when sprite-based != signature-based archetype

Add tracking:

```sql
ALTER TABLE tournament_placements
ADD COLUMN archetype_detection_method TEXT CHECK (
    archetype_detection_method IN ('sprite', 'signature_card', 'manual', 'unknown')
) DEFAULT 'unknown';
```

### 4. Card ID mapping enhancements

Current `card_id_mappings` table is sound, but needs index improvements for JP decklist translation:

```sql
-- Already exists, just add composite index for JOIN performance
CREATE INDEX idx_card_mappings_jp_set_card
ON card_id_mappings(jp_set_id, jp_card_id);

-- Add mapping confidence for fuzzy matches
ALTER TABLE card_id_mappings
ADD COLUMN confidence DECIMAL(3,2) DEFAULT 1.0
CHECK (confidence >= 0.0 AND confidence <= 1.0);

COMMENT ON COLUMN card_id_mappings.confidence IS
'Mapping confidence: 1.0 = exact match, 0.8 = fuzzy name match, 0.5 = heuristic';
```

## Data pipeline redesign

### Current flow (problematic)

```
Limitless HTML
  → LimitlessClient._parse_placement_row()
    → Extracts text archetype OR calls _extract_archetype_from_images()
      → Returns "Grimmsnarl / Froslass" (not normalized)
  → TournamentScrapeService.process_tournament()
    → ArchetypeDetector.detect_from_existing_archetype(decklist, existing_label)
      → Falls back to existing_label if no signature cards found
  → Saves to tournament_placements.archetype (dirty mixed data)
  → MetaService.compute_meta_snapshot()
    → Aggregates dirty archetypes into meta_snapshots
```

**Issues:**

- Archetype names vary: "Grimmsnarl / Froslass", "Froslass Grimmsnarl", "grimmsnarl-froslass"
- No way to fix past data without re-scraping
- Signature card gaps cause "Rogue" misclassification even when Limitless has correct label

### New flow (robust)

#### Phase 1: Ingestion (LimitlessClient)

```python
# In LimitlessClient._parse_placement_row()
# NEW: Extract sprite-pair metadata
def _extract_sprite_pair(self, archetype_cell: Tag) -> dict:
    """Extract sprite pair from archetype cell images."""
    sprites = []
    for img in archetype_cell.select("img"):
        src = img.get("src", "")
        # Extract: /sprites/pokemon/dragapult.png → "dragapult"
        match = re.search(r"/sprites/pokemon/([a-z0-9-]+)\.png", src)
        if match:
            sprites.append(match.group(1))

    if not sprites:
        return {"raw_archetype": None, "sprites": []}

    # Canonical ordering: alphabetical (or keep Limitless order)
    sprite_key = "-".join(sprites)  # "charizard-dragapult"
    return {
        "raw_archetype": sprite_key,
        "sprites": sprites
    }

# In placement parsing, store BOTH
placement = LimitlessPlacement(
    placement=placement_num,
    player_name=player_name,
    country=country,
    archetype="Unknown",  # Will be normalized in Phase 2
    raw_archetype=sprite_data["raw_archetype"],
    raw_archetype_sprites=sprite_data["sprites"],
    decklist_url=decklist_url
)
```

#### Phase 2: Normalization (TournamentScrapeService)

```python
# NEW: ArchetypeNormalizer service
class ArchetypeNormalizer:
    def __init__(self, session: AsyncSession):
        self.session = session
        self._sprite_cache: dict[str, str] = {}  # sprite_key → canonical_name

    async def normalize(self,
                       raw_archetype: str | None,
                       decklist: list[dict] | None,
                       jp_card_mapping: dict[str, str] | None = None
                       ) -> tuple[str, str]:
        """Normalize archetype from sprite or decklist.

        Returns:
            (canonical_name, detection_method)
        """
        # Strategy 1: Sprite lookup (primary)
        if raw_archetype:
            canonical = await self._lookup_sprite(raw_archetype)
            if canonical:
                return canonical, "sprite"

        # Strategy 2: Signature card detection (fallback)
        if decklist:
            detector = ArchetypeDetector(jp_to_en_mapping=jp_card_mapping)
            detected = detector.detect(decklist)
            if detected != "Rogue":
                return detected, "signature_card"

        # Strategy 3: Accept raw label if parseable
        if raw_archetype:
            # Auto-generate canonical from sprite
            canonical = self._sprite_to_canonical(raw_archetype)
            await self._create_sprite_mapping(raw_archetype, canonical)
            return canonical, "sprite"

        return "Rogue", "unknown"

    async def _lookup_sprite(self, sprite_key: str) -> str | None:
        """Look up canonical name from sprite key."""
        if sprite_key in self._sprite_cache:
            return self._sprite_cache[sprite_key]

        result = await self.session.execute(
            select(ArchetypeSprite.canonical_name)
            .where(
                ArchetypeSprite.sprite_key == sprite_key,
                ArchetypeSprite.is_active == True
            )
        )
        canonical = result.scalar_one_or_none()
        if canonical:
            self._sprite_cache[sprite_key] = canonical
        return canonical

    def _sprite_to_canonical(self, sprite_key: str) -> str:
        """Convert sprite key to canonical name heuristically.

        Examples:
            "dragapult-charizard" → "Dragapult Charizard ex"
            "lugia-vstar" → "Lugia VSTAR"
        """
        # Title case, add " ex" suffix if modern era
        parts = sprite_key.split("-")
        canonical_parts = [p.title() for p in parts]

        # Check for V-era suffixes
        if canonical_parts[-1] in ("Vstar", "Vmax", "V"):
            canonical_parts[-1] = canonical_parts[-1].upper()
            return " ".join(canonical_parts)

        # Default: assume modern ex era
        return " ".join(canonical_parts) + " ex"

# In TournamentScrapeService.process_tournament()
async def process_tournament(self, tournament_data: dict):
    normalizer = ArchetypeNormalizer(self.session)
    jp_mapping = await self._get_jp_to_en_mapping() if is_jp else None

    for placement_data in tournament_data["placements"]:
        decklist = await self.client.fetch_decklist(placement_data["decklist_url"])

        canonical_name, method = await normalizer.normalize(
            raw_archetype=placement_data.get("raw_archetype"),
            decklist=decklist.cards if decklist else None,
            jp_card_mapping=jp_mapping
        )

        placement = TournamentPlacement(
            raw_archetype=placement_data.get("raw_archetype"),
            raw_archetype_sprites=placement_data.get("raw_archetype_sprites"),
            archetype=canonical_name,
            archetype_detection_method=method,
            archetype_version=1,  # Current normalization version
            decklist=decklist.cards if decklist else None,
            ...
        )
        self.session.add(placement)
```

#### Phase 3: Analysis (MetaService — unchanged interface)

```python
# MetaService.compute_meta_snapshot() uses normalized archetype field
# NO CHANGES NEEDED — clean separation of concerns

# New: Validation query to surface normalization issues
async def validate_archetype_quality(self) -> dict:
    """Check for normalization anomalies."""
    query = select(
        TournamentPlacement.raw_archetype,
        TournamentPlacement.archetype,
        TournamentPlacement.archetype_detection_method,
        func.count().label("count")
    ).group_by(
        TournamentPlacement.raw_archetype,
        TournamentPlacement.archetype,
        TournamentPlacement.archetype_detection_method
    ).having(func.count() > 5)

    # Returns: raw → canonical mappings with frequency
    # Allows data team to spot "dragapult-charizard" mapped to
    # multiple different canonical names
```

### Migration strategy (zero-downtime)

**Phase 1: Shadow writes (Week 1)**

- Deploy updated LimitlessClient that extracts sprite pairs
- Write to `raw_archetype` + `raw_archetype_sprites` fields
- Keep existing `archetype` field behavior unchanged
- Monitor: % of placements with successful sprite extraction

**Phase 2: Backfill raw data (Week 2)**

```python
# One-time backfill script
async def backfill_raw_archetypes():
    """Re-fetch tournament standings pages to extract sprites."""
    placements = await session.execute(
        select(TournamentPlacement)
        .where(TournamentPlacement.raw_archetype.is_(None))
        .where(TournamentPlacement.decklist_source.isnot(None))
        .limit(1000)
    )

    for placement in placements.scalars():
        # Re-parse the standings page for this tournament
        standings_url = placement.tournament.source_url + "/standings"
        sprites = await client.extract_sprites_from_standings(
            standings_url,
            placement.placement
        )
        if sprites:
            placement.raw_archetype = sprites["key"]
            placement.raw_archetype_sprites = sprites["sprites"]

    await session.commit()
```

**Phase 3: Normalization cutover (Week 3)**

- Seed `archetype_sprites` table with top 50 archetypes (manual or scripted)
- Deploy ArchetypeNormalizer to production
- Switch to sprite-primary normalization
- Compare new `archetype` vs old for discrepancies
- Fix mappings, not code

**Phase 4: Full reprocess (Week 4)**

```python
# Recompute all meta_snapshots using clean archetype data
async def recompute_all_snapshots():
    """Delete and recompute meta snapshots."""
    await session.execute(delete(MetaSnapshot))  # Wipe computed data

    # Re-run compute_meta for each date/region/format combo
    dates = await get_all_tournament_dates()
    for snapshot_date in dates:
        for region in [None, "NA", "EU", "JP", "LATAM", "OCE"]:
            for format in ["standard", "expanded"]:
                for best_of in [1, 3]:
                    snapshot = await meta_service.compute_enhanced_meta_snapshot(
                        snapshot_date=snapshot_date,
                        region=region,
                        game_format=format,
                        best_of=best_of
                    )
                    await meta_service.save_snapshot(snapshot)
```

**Phase 5: Validation & rollout (Week 5)**

- Compare old vs new meta shares for top 10 archetypes
- Fix Cinderace EX and other known errors via `card_id_mappings` corrections
- Monitor frontend for user-visible changes
- Document archetype naming conventions

## Risks if ignored

- **Data quality death spiral**: Each bad card mapping creates bad archetype labels → bad meta shares → bad JP signals → bad predictions. Users lose trust when "Cinderace EX" shows as emerging archetype.

- **Technical debt accumulation**: Manual SIGNATURE_CARDS dict (214 lines) will grow to 500+ lines as new sets release. Every new card requires code deploy. Hotfixes break tests. Eventually unmaintainable.

- **Lost opportunity cost**: Current architecture cannot support requested features:
  - Deck-level tech card analysis (needs clean archetype grouping)
  - Predictive modeling (needs historical time series without noise)
  - Retrospective format analysis (can't reprocess old data)
  - User-submitted decklists (no confidence scoring for archetype assignment)

## Dependencies on other domains

**From Advocate (UX/Product)**:

- Confirm archetype naming conventions (e.g., "Dragapult Charizard ex" vs "Charizard Dragapult ex")
- Define user-visible error states when sprite extraction fails
- Approval for data reprocessing window (meta dashboard may show different numbers)

**From Craftsman (Implementation)**:

- Review migration SQL for indexing strategy (BRIN vs B-tree for date columns)
- Validate JSONB query performance for `raw_archetype_sprites` array matching
- Implement sprite extraction regex with test coverage (brittle HTML parsing)

**From Guide (Context/Process)**:

- Prioritize: Sprite extraction → Card mapping fixes → Full reprocess? Or parallel?
- Coordinate with user feedback on "Cinderace EX" bug (quick fix vs correct fix trade-off)
- Schedule data reprocessing during low-traffic window (Sunday 2am UTC?)

---

**Appendix A: Example sprite extraction**

From Limitless HTML:

```html
<td>
  <a href="/decks/abc123">
    <img src="/sprites/pokemon/dragapult.png" alt="Dragapult" />
    <img src="/sprites/pokemon/charizard.png" alt="Charizard" />
  </a>
</td>
```

Extracted:

```json
{
  "raw_archetype": "charizard-dragapult",
  "raw_archetype_sprites": ["charizard", "dragapult"],
  "canonical_name": "Charizard Dragapult ex"
}
```

**Appendix B: Card mapping correction example**

Current error:

```python
# card_id_mappings table
jp_card_id: "sv7-018"  # Cinderace EX in JP
en_card_id: "sv6-095"  # WRONG — this is Cinderace (not ex)
# Should be: "sv6-095" → Cinderace ex (correct card)
```

Fix:

```sql
UPDATE card_id_mappings
SET en_card_id = 'sv6-095',  -- Correct EN ID for Cinderace ex
    confidence = 1.0,
    updated_at = NOW()
WHERE jp_card_id = 'sv7-018';
```

After fix, all historical JP tournaments with Cinderace EX decklists will:

1. Keep raw decklist unchanged (immutable)
2. Translate JP card IDs correctly during normalization
3. Detect "Cinderace ex" archetype via signature cards
4. Recompute meta shares without "Rogue" pollution
