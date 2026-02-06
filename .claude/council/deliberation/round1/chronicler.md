# Chronicler Position — Japanese Meta Pipeline Overhaul

## Core recommendation

Adopt LimitlessTCG's archetype naming system and create a comprehensive data dictionary documenting the new pipeline, archetype detection rules, card ID formats, and Japanese-to-English mapping conventions to ensure this critical infrastructure remains maintainable across AI agent sessions and human developers.

## Key argument

This pipeline overhaul touches the foundational knowledge layer of TrainerLab: how we identify, label, and track decks across two languages and two formats (BO1 vs BO3). The existing documentation (CODEMAP.md, SPEC.md, SCRAPER_ARCHITECTURE.md) describes the current system, but this overhaul will invalidate significant portions of that knowledge. Without updated documentation:

1. **Future AI agents will hallucinate the old system** — CLAUDE.md and agent memory will reference outdated archetype detection logic, signature card mappings, and pipeline flows
2. **Human developers will misunderstand data provenance** — Without a data dictionary, engineers won't know which archetype names come from Limitless vs. our detection, or how JP card IDs map to EN
3. **The "why" will be lost** — This is the second archetype system (moving from signature cards to Limitless names). An ADR capturing this decision prevents future flip-flopping
4. **Bus factor = 1** — If you leave this project, the next person needs to understand: What are "signature cards"? Why did we change? How does the JP→EN card mapping work? What's the difference between `decklist` and `decklist_enriched`?

## Documentation gaps

After examining the codebase, these gaps will emerge or worsen after the overhaul:

### Archetype Detection Knowledge

- **Current:** `/apps/api/src/data/signature_cards.py` contains 95 hardcoded card→archetype mappings
- **Gap:** No documentation explaining the detection algorithm, why specific cards were chosen, or how to add new archetypes
- **Post-overhaul:** Will switch to Limitless's naming system — need ADR explaining why, and new detection logic docs

### Card ID Format Documentation

- **Current:** CODEMAP.md mentions "TCGdex format: `{set_id}-{card_number}`" but doesn't document:
  - How JP card IDs differ (e.g., `SV10-15` vs `sv7-144`)
  - The `POR-XXX` placeholder format for unreleased JP cards
  - How `CardIdMapping` table works (JP↔EN)
  - When to use `card_id` vs `jp_card_id` in decklist structures
- **Post-overhaul:** JP_CITY_LEAGUE_INGESTION.md introduces `PlaceholderCard` model but doesn't integrate into main docs

### Data Dictionary (Missing)

No single document explains:

- **Archetype taxonomy:** What constitutes an archetype? How granular (e.g., "Charizard ex" vs "Charizard ex Pidgeot")?
- **Decklist schema evolution:** `decklist` (original JP IDs) → `decklist_enriched` (with card details) → `decklist_source` (Limitless URL)
- **Region codes:** NA, EU, JP, LATAM, APAC, OCE — which Limitless pages map to which regions?
- **BO1 vs BO3 semantics:** What does `best_of=1` mean for meta share calculations? Why does it matter?
- **Tier calculation:** S/A/B/C/Rogue thresholds (15%, 8%, 3%, 1%) — where are these documented outside SPEC.md?

### Pipeline Flow Documentation

- **Current:** SCRAPER_ARCHITECTURE.md and DATA_PIPELINE.md describe the flow, but:
  - Don't explain the three time horizons (current, future, retrospective)
  - Don't document the new predictive analysis capabilities
  - Don't explain how full data reprocessing will work
  - Cloud Scheduler job frequencies are in SPEC.md, but not synchronized with actual terraform code comments

### CLAUDE.md Staleness

- **Current Focus section:** Still says "Building card database + search" and "Next: deck builder MVP" — these are done
- **Missing:** No mention of Japanese meta analysis, archetype detection systems, placeholder cards, or data pipeline
- **Post-overhaul:** Will need sections on:
  - How to add new archetype mappings (Limitless names vs signature cards)
  - Where to find card ID mapping tables
  - How to trigger pipeline jobs locally vs in Cloud Run
  - Common data analysis patterns (e.g., "How do I query JP-only archetypes?")

## Update plan

### 1. Create `/docs/DATA_DICTIONARY.md`

New canonical reference containing:

- **Archetype Naming Conventions** (LimitlessTCG adoption rationale + examples)
- **Card ID Formats** (TCGdex, JP variants, POR-XXX placeholders, reprints)
- **Decklist Schema Evolution** (original → enriched → flattened for export)
- **Region Taxonomy** (codes, BO format, Limitless source URLs)
- **Tier System** (thresholds, calculation formula, BO1 adjustments)
- **Meta Time Horizons** (current, future, retrospective analysis windows)
- **Placeholder Cards** (lifecycle: unreleased → LLM translation → released → merged)

### 2. Update `/docs/CODEMAP.md`

- Add new models: `PlaceholderCard`, `JPCardInnovation`, `JPNewArchetype`, `JPSetImpact`
- Update services section: new archetype detection logic (Limitless names, not signature cards)
- Update data pipeline section: three time horizons, predictive analysis
- Add reference to DATA_DICTIONARY.md for terminology

### 3. Update `/docs/SPEC.md`

- Section 7.2 (Archetype Detection): Replace signature card logic with LimitlessTCG adoption
- Add new section: "Predictive Intelligence" (JP signals → future EN meta)
- Update Section 9 (Database Schema): Add `PlaceholderCard`, enhanced `TournamentPlacement`
- Add ADR-style note explaining archetype system migration

### 4. Update `/docs/SCRAPER_ARCHITECTURE.md`

- Add "Archetype Naming Philosophy" section (why we adopted Limitless names)
- Document the new `decklist_enriched` field structure
- Add flowchart for JP card → placeholder → EN card lifecycle
- Explain three analysis time horizons (current/future/retrospective)

### 5. Update `/docs/architecture/DATA_PIPELINE.md`

- Add mermaid diagram: JP card reveal → LLM translation → placeholder creation → decklist enrichment
- Document full data reprocessing strategy (backfill vs incremental)
- Add "Predictive Analysis" section with new `compute-meta` capabilities

### 6. Update `/CLAUDE.md`

**Current Focus section (lines 64-69):**

Replace with:

```markdown
## Current Focus

- Japanese meta pipeline overhaul (archetype naming, card mapping, predictive analysis)
- Full data reprocessing for historical accuracy
- LimitlessTCG archetype adoption (replacing signature card detection)
```

**Add new section after "Key Decisions" (after line 50):**

```markdown
## Archetype Detection

- **System:** LimitlessTCG archetype names (adopted February 2026)
- **Fallback:** Signature card detection for unrecognized decks
- **Data location:** `/apps/api/src/data/signature_cards.py` (legacy), Limitless API (primary)
- **Mapping table:** `card_id_mappings` (JP↔EN), `placeholder_cards` (unreleased JP cards)

## Data Pipeline

- **Discovery jobs:** `discover-en` (6am UTC), `discover-jp` (7am UTC)
- **Processing:** Cloud Tasks queue → `process-tournament` → archetype detection
- **Meta computation:** `compute-meta` (8am UTC) calculates shares, tiers, JP signals
- **Card sync:** Weekly (Sunday 3am/4am UTC) for TCGdex + card mappings

See `/docs/DATA_DICTIONARY.md` for terminology and `/docs/architecture/DATA_PIPELINE.md` for flow diagrams.
```

### 7. Update `/AGENTS.md`

Add context for AI agents (if this file contains agent-specific instructions):

- Link to DATA_DICTIONARY.md as required reading
- Explain the archetype naming change and where to find current system
- Document common queries (e.g., "How to add a new placeholder card?")

### 8. Create `/docs/ADR_001_LIMITLESS_ARCHETYPE_ADOPTION.md`

Architecture Decision Record capturing:

- **Problem:** Signature card detection is brittle, requires manual curation, diverges from community naming
- **Options considered:** (1) Keep signature cards, (2) Adopt Limitless names, (3) LLM-based naming
- **Decision:** Adopt LimitlessTCG naming with signature card fallback
- **Consequences:** Simpler maintenance, community alignment, easier external data integration, but dependency on Limitless API

### 9. Update `/docs/JP_CITY_LEAGUE_INGESTION.md`

This document is detailed but not integrated:

- Add cross-references to DATA_DICTIONARY.md for terminology
- Add "Integration with Main Pipeline" section linking to SCRAPER_ARCHITECTURE.md
- Add "For AI Agents" callout box with common tasks (add translation, query JP meta, export data)

### 10. Add `/docs/OPERATIONS.md` section

If OPERATIONS.md exists, add:

- **"Data Reprocessing Runbook"** — how to trigger full pipeline rerun
- **"Archetype Mapping Updates"** — how to add/modify Limitless→signature card fallback
- **"Placeholder Card Lifecycle"** — LLM translation → verification → release promotion

## AI agent knowledge

### Update CLAUDE.md strategy

The current CLAUDE.md is too high-level for a complex data pipeline. AI agents need:

1. **Terminology anchor:** "Always consult `/docs/DATA_DICTIONARY.md` for data model definitions before making assumptions"
2. **Pipeline trigger patterns:** "To test archetype detection locally: `uv run pytest tests/unit/test_archetype_detector.py -k 'test_limitless_naming'`"
3. **Common data queries:** Example SQL/code snippets for "Show me all JP-exclusive archetypes" or "Find placeholders that got released"
4. **Change protocol:** "When modifying archetype detection, update: (1) code, (2) tests, (3) DATA_DICTIONARY.md, (4) this file's examples"

### Memory bank pattern

Add to `/Users/danielsong/.claude/projects/-Users-danielsong-Development-tcg-trainerlab/memory/MEMORY.md`:

```markdown
## Archetype Detection (as of 2026-02-05)

- **Primary system:** LimitlessTCG API names (adopted to match community conventions)
- **Fallback:** Signature card detection from `/apps/api/src/data/signature_cards.py`
- **JP cards:** Use `CardIdMapping` (jp_card_id → en_card_id) + `PlaceholderCard` for unreleased
- **Data dictionary:** `/docs/DATA_DICTIONARY.md` is the canonical reference for terminology

## Data Pipeline (as of 2026-02-05)

- Three analysis horizons: current (today's meta), future (JP preview of EN), retrospective (historical trends)
- JP pipeline creates `PlaceholderCard` entries for unreleased cards (POR-XXX format)
- Full data reprocessing: update archetype labels for all historical tournaments
- See `/docs/architecture/DATA_PIPELINE.md` for flow diagrams
```

## Data dictionary

### Priority sections

A complete data dictionary needs these sections (ordered by dependency):

1. **Card Identification**
   - TCGdex ID format (`{set_id}-{card_number}`)
   - Japanese vs English ID differences
   - Placeholder format (`POR-XXX` for Perfect Order unreleased cards)
   - Reprint handling (same card, multiple IDs)

2. **Archetype Taxonomy**
   - Naming authority (LimitlessTCG primary, signature cards fallback)
   - Granularity rules (e.g., "Charizard ex" vs "Charizard ex Pidgeot Control")
   - Special cases: "Rogue", "Lost Zone Box", "Ancient Box"
   - Alias mapping (JP image extraction → normalized EN names)

3. **Tournament Metadata**
   - Region codes and coverage
   - BO1 vs BO3 format implications
   - Tier hierarchy (Regionals > City Leagues > Grassroots)
   - Limitless source URL patterns

4. **Decklist Schema**
   - `decklist` (original, with jp_card_id)
   - `decklist_enriched` (with card details, is_placeholder flag)
   - `decklist_source` (Limitless URL)
   - Card quantity, set code, supertype

5. **Meta Calculation**
   - Share calculation formula (placements / total decks)
   - Tier assignment thresholds (S/A/B/C/Rogue)
   - JP Signal detection (threshold = 5% difference)
   - Time window for snapshots (default 90 days)

6. **Placeholder Card Lifecycle**
   - States: unreleased → LLM translated → manually verified → released → merged to TCGdex
   - Source types: limitless, llm_x, llm_bluesky, manual
   - Synthetic ID generation (POR-001 through POR-999)
   - Promotion to real card (when TCGdex adds EN release)

### Example entry format

````markdown
## Term: `jp_card_id`

**Type:** String field in `CardIdMapping` and `TournamentPlacement.decklist`

**Format:** `{set_code}-{number}` (e.g., `SV10-15`)

**Description:** Japanese card identifier from Limitless tournament decklists. Maps to `en_card_id` via `CardIdMapping` table. If no mapping exists and card is unreleased, pipeline generates `PlaceholderCard` with synthetic `POR-XXX` ID.

**Related fields:** `en_card_id`, `placeholder_card_id`, `is_synthetic`

**Usage example:**

```sql
-- Find EN equivalent for JP card
SELECT en_card_id
FROM card_id_mappings
WHERE jp_card_id = 'SV10-15';
```
````

**See also:** DATA_DICTIONARY.md § Card Identification

```

## Risks if ignored

- **Knowledge fragmentation across 6+ docs** — Developers will find contradictory information about archetype detection (SPEC.md says signature cards, CODEMAP.md says Limitless API, code does something else)
- **AI agents will confidently use the wrong system** — Without updated CLAUDE.md, future Claude sessions will reference signature_cards.py and miss the Limitless adoption, generating broken code
- **"Why did we do this?" amnesia** — In 6 months, someone will ask "Why did we abandon signature card detection?" and rebuild it because there's no ADR explaining the tradeoffs
- **Unmaintainable data exports** — Without a data dictionary, external researchers won't understand `is_placeholder=true`, `decklist_enriched` vs `decklist`, or why some archetype names are in Japanese

## Dependencies on other agents' domains

### Architect
- **Database schema changes:** Need to know final structure of `PlaceholderCard`, `TournamentPlacement.decklist_enriched`, enhanced `CardIdMapping`
- **API endpoint contracts:** New endpoints for placeholder card CRUD, enhanced `discover-jp` parameters
- **Migration strategy:** Full data reprocess vs incremental backfill — affects documentation of "how to run this safely"

### Craftsman
- **Archetype detection implementation:** Need to document the actual algorithm (Limitless API call → fallback to signature cards → "Rogue")
- **Card mapping logic:** How does `sync_card_mappings.py` work? When does it create synthetic mappings?
- **Decklist enrichment flow:** Step-by-step: original decklist → lookup mapping → fetch card details → flag placeholders → save enriched

### Oracle
- **Data quality thresholds:** What's the acceptable match rate for JP→EN card mapping? When do we alert on low match rates?
- **Archetype confidence scoring:** If we keep signature card fallback, how do we indicate "low confidence" archetype labels?
- **Pipeline monitoring:** What metrics should be documented in OPERATIONS.md for data health?

### Pragmatist
- **Phased rollout:** If we migrate archetype naming incrementally, need to document "Current state: 50% Limitless, 50% signature cards"
- **Backfill strategy:** Should we reprocess all historical data immediately or in phases? Affects OPERATIONS.md runbook

### Advocate
- **Data export formats:** Need clear documentation of CSV/JSON export schemas for external researchers (column names, placeholder flags, archetype name format)
- **API changelog:** Breaking change communication if `archetype` field values change after Limitless adoption
```
