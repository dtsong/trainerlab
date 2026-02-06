# Scout Position — Japanese Tournament Pipeline Fix

## Core Recommendation

Adopt Limitless sprite-based archetype system as the canonical archetype source of truth, replace signature-card-based archetype detection with sprite URL parsing, and implement TCGdex API + Limitless card page cross-referencing for robust JP↔EN card mapping. Do not reinvent archetype classification — Limitless has already solved this problem with visual sprites.

## Key Argument

Limitless TCG is the de-facto competitive Pokemon TCG data platform with a proven archetype classification system that uses 1-2 Pokemon sprite images per deck as visual archetype identifiers. My HTML analysis reveals that sprites follow a predictable URL pattern (`https://r2.limitlesstcg.net/pokemon/gen9/{pokemon-name}.png`) and are embedded directly in tournament result pages, making them trivial to extract. The current TrainerLab archetype detection system (`src/services/archetype_detector.py`) relies on signature card matching and JP-to-EN card ID translation, which is fragile and produces incorrect labels. By switching to sprite-based archetype extraction, we eliminate the dependency on card-level matching accuracy and inherit Limitless's expert curation of deck archetypes. The sprites are the same across JP and EN tournaments, solving the JP→EN translation problem at the archetype level.

## Research Findings

### 1. LimitlessTCG HTML Structure

**Tournament Listing Page (`/tournaments/jp`):**

- Table layout with Date, Prefecture, Shop, Winner columns
- Winner identified by Pokemon sprites (not text archetype labels)
- Sprite format: `[![dragapult](https://r2.limitlesstcg.net/pokemon/gen9/dragapult.png)](https://limitlesstcg.com/decks/list/jp/60085)`
- URL pattern is predictable: lowercase Pokemon name, hyphen for variants (e.g., `froslass-mega.png`)
- Pagination: 25/50/100 entries per page, up to 159 pages for JP

**Tournament Detail Page (`/tournaments/jp/3959`):**

- Ranked table: Placement | Player Name | Deck Archetype (sprites) | Deck List Link
- Multiple sprites per deck (typically 1-2 Pokemon representing archetype)
- Sprite source: `r2.limitlesstcg.net/pokemon/gen9/{name}.png`
- Deck list links: `/decks/list/jp/[ID]`
- No alt text on sprites (must rely on URL extraction)

**Card Pool Page (`/cards`):**

- Organized by set code (e.g., ASC, MEG, BLK)
- Advanced search with language filters (EN, DE, FR, ES, IT, PT)
- Each set shows release date, card count, USD/EUR pricing
- Individual card pages cross-reference JP equivalents: "Ascended Heroes #127" ↔ "Mega Dream ex #103"

**Extraction Strategy:**

- Parse sprite `<img src="...">` tags from tournament result tables
- Extract Pokemon names from URL paths: `gen9/{name}.png` → `name`
- Map sprite pairs to archetype labels (e.g., `["dragapult", "dusknoir"]` → "Dragapult Box")
- This requires building/scraping a sprite-to-archetype mapping table from Limitless

**Reference:** [LimitlessTCG JP Tournaments](https://limitlesstcg.com/tournaments/jp), [Tournament Example](https://limitlesstcg.com/tournaments/jp/3959)

### 2. Card Mapping Sources

**TCGdex API (Primary Recommendation):**

- Multi-language API supporting 14 languages including Japanese and English
- **Shared card IDs across languages** — same card has same ID regardless of language
- REST + GraphQL APIs with Python SDK available (`tcgdex/python-sdk`)
- 130k+ total cards indexed
- Status tracker available at tcgdex.dev/status
- Latest release: v2.43.0 (January 29, 2026)
- TrainerLab already uses TCGdex as primary card source (`src/clients/tcgdex.py`)

**Limitless Card Pages (Secondary):**

- Individual card pages cross-reference JP/EN versions
- Example: `/cards/ASC/127` shows "JP. Prints: Mega Dream ex #103"
- Reverse works: `/cards/jp/M2a/103` shows "EN: Ascended Heroes #127"
- No public API — requires HTML scraping
- Useful for validation/backfill when TCGdex mapping is incomplete

**Bulbapedia (Tertiary):**

- Comprehensive expansion lists with JP/EN correspondence
- "List of Japanese Pokémon Trading Card Game expansions" and "List of Pokémon Trading Card Game expansions" pages provide set-level mapping
- Expansion codes documented for Scarlet & Violet era and beyond
- Useful for set-level metadata but not card-level IDs
- Community-maintained (risk of lag or errors)

**Current Implementation Gap:**
TrainerLab has a `CardIdMapping` database table and sync pipeline (`pipelines/sync_card_mappings.py`), suggesting existing JP↔EN mapping infrastructure. However, archetype detection failure suggests mapping coverage is incomplete or sprite extraction is not being used.

**Recommendation:**

1. Use TCGdex API as primary mapping source (already integrated)
2. Scrape Limitless card pages to backfill missing mappings
3. Store mappings in `CardIdMapping` table
4. Use sprites for archetype labels, not card-level translation

**References:** [TCGdex API](https://tcgdex.dev/), [TCGdex GitHub](https://github.com/tcgdex/cards-database), [Bulbapedia Japanese Expansions](https://bulbapedia.bulbagarden.net/wiki/List_of_Japanese_Pok%C3%A9mon_Trading_Card_Game_expansions), [Limitless Card Database](https://limitlesstcg.com/cards)

### 3. Predictive Modeling for TCG Metas

**Existing Research:**

- **Q-DeckRec** (arXiv:1806.09771): Fast deck recommendation for collectible card games using ML
- **Drafting in CCGs via RL**: Deep reinforcement learning for deck-building in self-play environments (SBGames 2020, Legends of Code and Magic)
- **Evolutionary Algorithms for Hearthstone**: GA-based deck creation tested against human-designed decks
- **Card representations**: Research shows generalized input representation (numerical, nominal, text, card images, meta usage) improves performance on unseen cards
- **Human decision prediction**: Models aim to predict human choices (draft picks, deck building), not perfect play (inherent variability)

**Relevant Precedent:**

- **Yu-Gi-Oh! Meta** and **Road of the King**: Track top-performing decks from multiple tournaments, tabulate OCG format trends, publish weekly tier lists via Top Player Council
- **MTG Arena Zone**: Maintains BO1 and BO3 tier lists updated monthly based on competitive data
- **No formal forecasting tools found** — most "prediction" is expert-driven tier list curation, not computational models

**Gap Analysis:**
The research focuses on deck _building_ (drafting, card selection) rather than meta _forecasting_ (predicting which archetypes will dominate). No public tools found that predict TCG meta shifts using time-series or ML models. This is likely because:

1. Small sample sizes per format (dozens of archetypes, hundreds of tournaments)
2. High variance from metagaming (rock-paper-scissors dynamics)
3. External shocks (bans, new releases, tech discoveries)

**Implication for TrainerLab:**
Rather than building a predictive model from scratch (high complexity, uncertain ROI), adopt a **signals-based approach**:

- Track JP meta share vs. EN meta share (already implemented in `meta_service.py`)
- Flag archetypes with significant JP→EN divergence (JP leads EN by 3-6 months)
- Use JP tournament data as a **leading indicator** for EN meta shifts
- Surface new archetypes appearing in JP but not yet in EN

This matches the existing TrainerLab architecture (`jp_card_innovation.py`, `jp_new_archetype.py`, `jp_set_impact.py`).

**References:** [Q-DeckRec Paper](https://arxiv.org/pdf/1806.09771), [Drafting in CCGs via RL](https://www.sbgames.org/proceedings2020/ComputacaoFull/209690.pdf), [Hearthstone Evolutionary Algorithm](https://www.researchgate.net/publication/324767888_Automated_Playtesting_in_Collectible_Card_Games_using_Evolutionary_Algorithms_a_Case_Study_in_HearthStone), [Yu-Gi-Oh! Meta](https://www.yugiohmeta.com/), [Road of the King](https://roadoftheking.com/)

### 4. BO1 vs BO3 Meta Differences

**Key Findings from Magic: The Gathering (2025-2026):**

**Best-of-1 Characteristics:**

- **Aggro-favored**: No sideboard access means control decks cannot adjust for creature-based strategies
- **Consistency prioritized**: Decks need reliable early game with hard-to-stop win conditions
- **Surprise value amplified**: Unique sets and unpredictable strategies gain large advantages
- **Less centralized**: More diverse pool of viable decks and strategies vs. BO3
- **Top archetypes (MTG Arena BO1 Jan 2026)**: Mono-Red Aggro, Boros Auras, Izzet Prowess dominate after Leyline of Resonance ban

**Best-of-3 Characteristics:**

- **More centralized**: Smaller pool of top-tier decks
- **Skill-testing**: Sideboard construction and game 2/3 adaptation reward expertise
- **Control more viable**: Sideboard contains anti-aggro tools (sweepers, lifegain)
- **Surprises still valuable** but less impactful than BO1

**Pokemon TCG Context:**

- **Regional Championships**: BO3 (50-minute matches)
- **Cups**: May be BO1 in Swiss, BO3 in Top 8
- **Japanese City Leagues**: Typically BO1 with tie = double loss rule (unique to JP format)

**VGC (Video Game) Parallel:**
The VGC (Pokemon competitive battling) research confirms similar patterns: BO3 is more centralized, BO1 features more diverse teams and rewards surprises.

**Implication for JP→EN Predictions:**
Japanese BO1 City League results may not directly translate to EN BO3 Regional performance. Control-heavy or sideboard-dependent decks may underperform in JP BO1 data but be strong in EN BO3. Aggro/consistency decks overperform in JP BO1 relative to EN BO3.

**Mitigation:**

- Filter by tournament tier (`tier` column in `Tournament` table: "major", "premier", "league")
- Weight JP BO3 tournaments more heavily for EN predictions
- Flag archetypes with BO1/BO3 performance divergence

**References:** [MTG Arena BO1 Meta](https://mtgazone.com/standard-bo1-metagame-tier-list/), [BO1 vs BO3 Metagame Differences](https://www.vgcguide.com/approaching-best-of-1-vs-best-of-3), [Pokemon TCG Regionals Guide](https://flipsidegaming.com/blogs/pokemon-blog/preparing-for-pokemon-regionals-and-other-irl-tournaments)

### 5. Existing Tools/Libraries

**Python Libraries for Limitless Scraping:**

**TCG-scraper** (Adam1400/TCG-scraper):

- Retrieves and saves Pokemon TCG deck lists from Limitless
- Supports both sanctioned and unsanctioned tournaments
- Output: txt files separated by format
- 30 commits total, created April 2021
- **Maintenance status unclear** (no commit recency visible)

**pokemon-tcg-metagame-simulator** (leonid-dalin):

- Evolutionary game theory simulator for long-term meta evolution
- `scraper.py` converts HTML matchup data from Limitless to JSON
- Identifies stable equilibriums and key archetypes
- Shows precedent for Limitless HTML scraping + game-theoretic meta analysis

**pokemon-tcg-deck-scraper-api** (n1ru4l):

- Endpoints for retrieving deck data from Limitless tournaments
- Suggests API wrapper approach over raw scraping

**pokemon-tcg-api** (Oskar1504):

- Scrapes limitlesstcg.com and parses into JSON files
- Express.js API to deliver files
- Another precedent for Limitless scraping

**Official Pokemon TCG SDK (PokemonTCG/pokemon-tcg-sdk-python):**

- Python SDK for pokemontcg.io API
- Focuses on card data, not tournament results
- Does not cover Limitless data

**Assessment:**
Multiple community projects scrape Limitless, but none are production-grade libraries. TrainerLab already has a custom `LimitlessClient` (`src/clients/limitless.py`) for scraping — the issue is not tooling availability but incorrect archetype extraction logic.

**Card Translation Resources:**

- **Limitless Translations Page** (`/translations`): Provides translations for unreleased JP cards
- **JustInBasil Translations**: Community-driven translation resource for competitive players
- No dedicated Twitter/X or Bluesky accounts found for 2026 — translation happens on these dedicated pages

**Recommendation:**

- Enhance existing `LimitlessClient` to extract sprites instead of text archetype labels
- Do not adopt third-party scrapers (maintenance risk, not actively developed)
- Use Limitless `/translations` page for future-only JP cards (April 10 rotation focus)

**References:** [TCG-scraper](https://github.com/Adam1400/TCG-scraper), [pokemon-tcg-metagame-simulator](https://github.com/leonid-dalin/pokemon-tcg-metagame-simulator), [Limitless Translations](https://limitlesstcg.com/translations), [JustInBasil Translations](https://www.justinbasil.com/translations)

## Risks If Ignored

- **Archetype misclassification compounds** — Current signature-card approach is brittle and produces incorrect labels. Without switching to sprite-based extraction, JP tournament data will continue to pollute the meta analysis pipeline.
- **Reinventing solved problems** — Limitless has invested years into archetype curation via sprites. Building a parallel signature-card classification system requires maintaining a card database that duplicates (and diverges from) Limitless's expert knowledge.
- **JP→EN prediction accuracy suffers** — BO1 vs BO3 meta differences mean raw JP data is not directly transferable to EN predictions. Without tier-based filtering and format weighting, the "From Japan" intelligence will mislead users preparing for Regionals.
- **User expectations unmet** — Competitive players already use Limitless as the canonical source. If TrainerLab shows different archetype labels than Limitless, users will distrust the platform.

## Dependencies on Other Domains

- **Architect (Implementation):** Needs to design sprite-to-archetype mapping table structure (static data file vs. database table vs. scraped cache). Decision on whether to scrape sprite mappings once or maintain a live sync.
- **Cartographer (Data Pipeline):** Scraping flow must be updated to extract sprite URLs from HTML instead of text archetype labels. Requires HTML parsing strategy (BeautifulSoup selector patterns) and error handling for missing sprites.
- **Advocate (UX):** If archetype labels change after sprite adoption, existing user-facing displays (meta dashboard, tournament browser) may show unfamiliar names. Need migration plan or label normalization (e.g., "Dragapult Box" vs "Dragapult/Dusknoir").
- **Curator (Data Quality):** Sprite-based approach requires validation that sprite pairs map to consistent archetypes. Some decks may have ambiguous sprite combinations (e.g., 3+ sprites, variant sprites). Need fallback logic for edge cases.

---

## Sources

- [LimitlessTCG API/Website](https://limitlesstcg.com/)
- [LimitlessTCG JP Tournaments](https://limitlesstcg.com/tournaments/jp)
- [LimitlessTCG Translations](https://limitlesstcg.com/translations)
- [LimitlessTCG Card Database](https://limitlesstcg.com/cards)
- [TCGdex API](https://tcgdex.dev/)
- [TCGdex GitHub](https://github.com/tcgdex)
- [TCGdex Cards Database](https://github.com/tcgdex/cards-database)
- [TCGdex Python SDK](https://github.com/tcgdex/python-sdk)
- [Bulbapedia - Japanese Pokemon TCG Expansions](https://bulbapedia.bulbagarden.net/wiki/List_of_Japanese_Pok%C3%A9mon_Trading_Card_Game_expansions)
- [Bulbapedia - Pokemon TCG Expansions](https://bulbapedia.bulbagarden.net/wiki/List_of_Pok%C3%A9mon_Trading_Card_Game_expansions)
- [Q-DeckRec: Fast Deck Recommendation](https://arxiv.org/pdf/1806.09771)
- [Drafting in CCGs via Reinforcement Learning](https://www.sbgames.org/proceedings2020/ComputacaoFull/209690.pdf)
- [Automated Playtesting in Hearthstone](https://www.researchgate.net/publication/324767888_Automated_Playtesting_in_Collectible_Card_Games_using_Evolutionary_Algorithms_a_Case_Study_in_HearthStone)
- [Yu-Gi-Oh! Meta](https://www.yugiohmeta.com/)
- [Road of the King](https://roadoftheking.com/)
- [MTG Arena Zone BO1 Tier List](https://mtgazone.com/standard-bo1-metagame-tier-list/)
- [VGC Guide: BO1 vs BO3](https://www.vgcguide.com/approaching-best-of-1-vs-best-of-3)
- [Preparing for Pokemon Regionals](https://flipsidegaming.com/blogs/pokemon-blog/preparing-for-pokemon-regionals-and-other-irl-tournaments)
- [TCG-scraper GitHub](https://github.com/Adam1400/TCG-scraper)
- [pokemon-tcg-metagame-simulator GitHub](https://github.com/leonid-dalin/pokemon-tcg-metagame-simulator)
- [JustInBasil Translations](https://www.justinbasil.com/translations)
