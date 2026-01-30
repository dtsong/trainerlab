# Japanese Pokemon TCG Metagame: Data Sources & Translation Strategy

> Research document for building Japanese metagame coverage into the platform

---

## Executive Summary

**The opportunity:** Japan gets Pokemon TCG sets 2-3 months before international release. Whoever provides accurate, timely Japanese meta insights to English-speaking players has a genuine competitive advantage.

**The challenge:** Language barrier, cultural context, and ensuring insights aren't "lost in translation" when terminology, strategy nuance, and metagame reasoning cross from Japanese to English.

**The solution:** A multi-layered approach combining:
1. Primary Japanese data sources (structured data - easier to work with)
2. LLM-powered translation for content/insights (unstructured - requires more care)
3. Community validation partnerships with bilingual players
4. Clear communication of BO1 vs BO3 meta differences

---

## Japanese Data Source Ecosystem

### Tier 1: Primary Data Sources (Structured/Semi-Structured)

#### 1. LimitlessTCG Japanese Coverage
**URL:** https://limitlesstcg.com/tournaments/jp  
**Data available:**
- City League results (weekly across Japan)
- Champions League results (4-5 per year, 5K+ players each)
- Deck lists with card counts
- Archetype classification (consistent with international naming)
- Player standings

**Advantages:**
- Already translated/normalized to English card names
- Consistent data structure with international data
- Single source for both regions

**Considerations:**
- Same partnership/access conversation as international data
- They likely source from official/community Japanese sources

**Priority:** HIGH - This should be primary source if partnership secured

---

#### 2. Pokecabook (ポケカブック)
**URL:** https://pokecabook.com  
**Twitter:** @pokeca_book

**Data available:**
- シティリーグ (City League) results - comprehensive coverage
- ジムバトル (Gym Battle) results - daily local events
- チャンピオンズリーグ (Champions League) coverage
- 環境デッキランキング (Meta deck rankings/Tier list)
- カード採用率分析 (Card adoption rate analysis) - **valuable unique data**
- デッキレシピ (Deck recipes) organized by archetype

**Site structure (for scraping consideration):**
```
/archives/category/tournament/city-league  - City League results
/archives/category/tournament/jim-battle   - Gym Battle results
/archives/category/tournament/champions    - Champions League
/archives/26148                            - Tier list / meta rankings
/card-adoption-rate                        - Card adoption rates
/deckshow                                  - Deck recipe search
```

**Advantages:**
- Very comprehensive Japanese coverage
- Card adoption rates are differentiated data
- Tier lists provide Japanese player perspective
- Active daily updates

**Considerations:**
- All content in Japanese (translation required)
- Would need translation pipeline
- Scraping ethics - should reach out for partnership

**Priority:** HIGH - Unique data (adoption rates) worth pursuing

---

#### 3. Official Pokemon Japan Players Site
**URL:** https://players.pokemon-card.com  
**Official results page visible in Twitter links:** `players.pokemon-card.com/event/detail/{id}/result`

**Data available:**
- Official City League results
- Official tournament standings
- Player decklist codes (links to official deck viewer)

**Advantages:**
- Authoritative source
- Deck codes link to official card database
- Most accurate/official data

**Considerations:**
- May have access restrictions
- Data structure unknown without deeper exploration
- Japanese language

**Priority:** MEDIUM-HIGH - Worth exploring for official data validation

---

#### 4. ポケカ飯 (Pokeka-meshi)
**URL:** https://pokekameshi.com  
**Twitter:** @pokekameshi

**Data available:**
- City League results aggregation
- Tier tables with statistics
- Win rates, meta share percentages
- Links to official tournament results

**Unique features:**
- Publishes statistical breakdowns:
  - CSP (Championship Points) totals by archetype
  - 入賞シェア率 (top finish share rate)
  - 前週比 (week-over-week changes)

**Advantages:**
- Statistical focus aligns with our platform goals
- Pre-calculated meta percentages
- Active community engagement

**Priority:** MEDIUM-HIGH - Good supplementary statistical source

---

#### 5. Pokemoncard.io Weekly Japanese Reports
**URL:** https://pokemoncard.io (search for "Weekly Japanese Tournament Result")
**Author:** arelios

**Data available:**
- Weekly aggregation of Japanese tournament results
- Already translated to English
- Organized by deck variant
- Covers both City League and daily shop tournaments

**Advantages:**
- Already in English!
- Organized analysis, not just raw data
- Regular weekly cadence

**Considerations:**
- One person's interpretation/aggregation
- May lag behind real-time

**Priority:** MEDIUM - Useful for validation and English terminology reference

---

### Tier 2: Japanese Content Creators (Insights/Analysis)

These sources provide **qualitative insights** rather than just data - strategy explanations, card evaluations, metagame reasoning.

#### YouTube Channels

| Channel | Focus | Subscribers | Notes |
|---------|-------|-------------|-------|
| ポケモンカードチャンネル (Pokemon Card Channel) | Official Pokemon TCG Japan | 269K | Official source, new card reveals, tournament streams |
| @305 (Daichi Shimada) | Top player gameplay | 106K | World Championship competitor, high-level gameplay |
| Shintaro Ito | Pro player | ~30K | Another Worlds-level player |
| @PokecaCH | Community content | ~100K+ | Japanese news, meta overview, gameplay |

**Value:** These channels show how Japanese players actually pilot decks, their decision-making, sequencing, and strategic reasoning - things that don't translate from just looking at deck lists.

---

#### Twitter/X Accounts

| Account | Focus |
|---------|-------|
| @pokeca_book | Pokecabook official - daily results |
| @pokekameshi | Statistical meta analysis |
| @ggrui_Pokeka | In-depth City League analysis reports |
| @pokecamatomeru | News aggregation |

---

### Tier 3: Supplementary Resources

#### Card Databases with Japanese Support

| Resource | Japanese Support | Notes |
|----------|-----------------|-------|
| TCGdex API | 14 languages including Japanese | Potential card name mapping source |
| pokemontcg.io | Limited Japanese | Primary for English |
| Official pokemon-card.com | Full Japanese | Authoritative card text |

#### Other Analysis Sites

- **ポケカードラボ (Pokecardlab):** https://pokecardlab.com - Deck recipes and analysis
- **PTCGStats:** http://www.ptcgstats.com - Champions League coverage with VOD links
- **PTCG Legends:** https://www.ptcglegends.com - Historical data including Japanese events

---

## Translation Strategy

### The Core Challenge

Pokemon TCG translation isn't just language translation—it requires:

1. **Card name mapping:** Japanese card names → English equivalents
2. **Terminology consistency:** Game terms (ワザ = Attack, 特性 = Ability, etc.)
3. **Strategic nuance:** Why a card is good, not just what it does
4. **Cultural context:** Japanese player perspectives and preferences
5. **BO1 vs BO3 implications:** Understanding why Japanese meta differs

### Recommended Multi-Layer Approach

```
┌─────────────────────────────────────────────────────────────────┐
│                    TRANSLATION PIPELINE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Layer 1: Structured Data (Card names, deck lists)               │
│  ├── Use pre-built card name mapping table                       │
│  ├── Japanese card ID → English card ID lookup                   │
│  └── No LLM needed - deterministic mapping                       │
│                                                                  │
│  Layer 2: Semi-Structured (Tournament results, meta stats)       │
│  ├── Template-based translation                                  │
│  ├── Known patterns: "優勝" = "Winner", "準優勝" = "Runner-up"   │
│  └── LLM for edge cases only                                     │
│                                                                  │
│  Layer 3: Unstructured Content (Analysis, strategy, insights)    │
│  ├── LLM translation (Claude/GPT-4 for Japanese → English)       │
│  ├── TCG terminology glossary as context                         │
│  ├── Review by bilingual community member (spot check)           │
│  └── Flag uncertainty for human review                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Layer 1: Card Name Mapping (Deterministic)

**Build a card mapping table:**

```
card_mappings:
  japanese_name: "ピカチュウex"
  english_name: "Pikachu ex"
  card_id: "sv4-001"
  set_jp: "レイジングサーフ"
  set_en: "Raging Surf / Paradox Rift"
```

**Sources for mapping:**
- Bulbapedia has comprehensive Japanese ↔ English card mappings
- TCGdex API supports multiple languages
- Can be built incrementally as cards are encountered

**For unreleased cards (Japan-only):**
- Keep Japanese name with romanization
- Add English translation of effect
- Flag as "Not yet released internationally"

---

### Layer 2: TCG Terminology Glossary

Build a glossary of Pokemon TCG-specific terms:

| Japanese | Romaji | English | Context |
|----------|--------|---------|---------|
| ポケモンカード / ポケカ | Pokeka | Pokemon TCG | Game name |
| 環境 | Kankyō | Meta/Environment | Metagame |
| デッキ | Dekki | Deck | - |
| ワザ | Waza | Attack | - |
| 特性 | Tokusei | Ability | - |
| エネルギー | Enerugī | Energy | - |
| トレーナーズ | Torēnāzu | Trainer | Card type |
| サポート | Sapōto | Supporter | Card type |
| グッズ | Guzzu | Item | Card type |
| スタジアム | Sutajiamu | Stadium | Card type |
| 優勝 | Yūshō | Winner/Champion | Tournament |
| 準優勝 | Jun-yūshō | Runner-up | Tournament |
| ベスト4 | Besuto 4 | Top 4 | Tournament |
| ベスト8 | Besuto 8 | Top 8 | Tournament |
| シティリーグ | Shitī Rīgu | City League | Tournament |
| チャンピオンズリーグ | Chanpionzu Rīgu | Champions League | Tournament |
| ジムバトル | Jimu Batoru | Gym Battle | Local event |
| 採用率 | Saiyō-ritsu | Adoption/Inclusion rate | Card usage |
| Tier表 | Tier hyō | Tier list | Meta ranking |

---

### Layer 3: LLM Translation Strategy

**When to use LLM translation:**
- Strategy analysis articles
- Player interviews
- Card evaluation content
- Metagame commentary

**Best practices:**

1. **Provide TCG context in system prompt:**
```
You are translating Pokemon TCG content from Japanese to English.
Use these term mappings consistently:
- 環境 → "meta" or "metagame"
- 採用率 → "inclusion rate" or "play rate"
- [include full glossary]

The content discusses competitive Pokemon TCG in Japan, which plays
Best-of-1 format. Keep strategic nuance intact.
```

2. **Use Claude or GPT-4 for Japanese:**
   - Research shows Claude 3.5 and GPT-4 are top performers for Japanese translation
   - DeepL's new Japanese LLM is 1.7x better than classic for JP↔EN
   - For critical content, use multiple and compare

3. **Post-translation validation:**
   - Check that card names map correctly
   - Verify TCG terms are consistent
   - Flag anything that seems strategically off

4. **Preserve uncertainty:**
   - If translation is ambiguous, show both interpretations
   - Note when cultural context may affect meaning

---

### Community Validation Partnership

**The best translation is validated translation.**

**Strategy:** Partner with 1-2 bilingual competitive players who can:
- Spot-check LLM translations for accuracy
- Provide cultural/strategic context
- Correct terminology errors
- Flag nuances that machines miss

**Where to find bilingual players:**
- Japanese players who compete internationally
- English speakers living in Japan
- Players who follow both metas actively

**Incentive structure:**
- Free Pro tier access
- Credit as "Translation Advisor"
- Early access to Japanese features
- Small stipend if sustainable

---

## BO1 vs BO3: Critical Context

### Why Japanese Meta Differs

| Factor | Japanese (BO1) | International (BO3) |
|--------|---------------|---------------------|
| Sideboard | None | N/A (no sideboard in PTCG, but game 2/3 knowledge matters) |
| Consistency premium | Very high | High but can recover |
| Aggro viability | Higher | Medium |
| Tech cards | Lower value | Higher value (can adjust play) |
| Matchup spread | Less important | Very important |
| Donk potential | Matters more | Averaged over 3 games |
| Comeback potential | Low | Higher (games 2, 3) |
| **Tie rules** | **Double game loss** | **Ties less punishing** |

### The Tie Rule: A Massive Meta Shaper

**This is often overlooked but critically important:**

In Japanese tournaments, **if a game ends in a tie, BOTH players receive a game loss.** This fundamentally changes deck selection incentives:

**Decks that are FAVORED in Japanese meta:**
- Fast, aggressive strategies that win or lose quickly
- Linear game plans with clear, fast win conditions
- Decks that close games before time becomes a factor
- High damage output, proactive strategies

**Decks that are PENALIZED in Japanese meta:**
- Control decks aiming to deck out opponents
- Slow, methodical strategies
- Decks relying on late-game comeback chains (Counter Catcher + Iono)
- Multi-prize knockout strategies that require setup time
- Stall/mill strategies

### Practical Implications

**Example: Control decks**
A deck focused on decking out the opponent (making them unable to draw for turn) is risky in Japan because:
1. Games go long → higher tie risk
2. If you tie, you effectively lost
3. Even winning slowly means you might not finish in time

**Example: Comeback decks**
Strategies that fall behind early, then chain Iono + Counter Catcher to steal games late are weaker because:
1. Requires the game to go long
2. More decision points = slower play = tie risk
3. Japanese players actively avoid these lines

**Example: Charizard ex**
A deck like Charizard ex might show different play patterns:
- In Japan: More aggressive builds, faster energy acceleration priorities
- Internationally: Can afford slower, more controlling variants
- Japanese lists may cut late-game cards that international lists keep

### How to Present This to Users

**Always contextualize Japanese data with tie rule implications:**

> "Control and mill strategies show lower representation in Japanese City Leagues (5%) compared to international Regionals (12%). This is largely due to Japan's tie = double loss rule, which penalizes slower strategies. These archetypes may perform better in international BO3 play where ties are less punishing and you have multiple games to execute your gameplan."

**Deck archetype tags should include:**

```typescript
interface ArchetypeMetadata {
  name: string;
  // ... other fields
  
  // BO1 vs BO3 relevance
  game_speed: "fast" | "medium" | "slow";
  tie_risk: "low" | "medium" | "high";
  bo1_viability: "favored" | "neutral" | "unfavored";
  bo3_viability: "favored" | "neutral" | "unfavored";
  
  // Explanatory notes
  format_notes?: string;  // "Tie rules hurt this deck in Japan"
}
```

**UI callouts:**

For decks with high tie risk showing in Japanese data:
> ⚠️ **Format Note:** This deck shows X% in Japan but may underperform due to tie rules. International results may differ.

For aggressive decks overrepresented in Japan:
> 📊 **Format Note:** Fast decks like this are favored by Japan's tie = double loss rule. Expect slightly lower meta share internationally.

### Analytical Opportunities

**"BO1 Tax" Analysis:**
Track which archetypes are systematically over/under-represented in Japan vs International:

| Archetype | Japan Meta % | International Meta % | Difference | Likely Cause |
|-----------|-------------|---------------------|------------|--------------|
| Aggro Deck X | 18% | 12% | +6% | Tie rule favors speed |
| Control Deck Y | 3% | 9% | -6% | Tie rule penalizes |
| Midrange Deck Z | 15% | 14% | +1% | Neutral |

This becomes **differentiated analysis content** that helps players understand what Japanese data actually means for their format.

### Content Ideas

**Educational content:**
- "Why Japanese Meta Looks Different: The Tie Rule Explained"
- "Which Japanese Trends Will (and Won't) Transfer Internationally"
- "The BO1 Tax: Decks That Are Better Than Japan Shows"

**Regular analysis:**
- Include "BO1 adjustment" notes in Format Forecast reports
- Track "Japan vs International delta" for each archetype
- Highlight decks that might be "sleepers" internationally

---

## Implementation Roadmap

### Phase 1: Foundation (MVP)

**Data:**
- [ ] Integrate LimitlessTCG Japanese data (same pipeline as international)
- [ ] Build initial card name mapping table (top 200 cards)
- [ ] Create TCG terminology glossary

**UI:**
- [ ] Add "Japan" to region selector in meta dashboard
- [ ] Add "Best-of-1" indicator for Japanese data
- [ ] Simple Japanese meta share display

**Translation:**
- [ ] No LLM translation in MVP
- [ ] Rely on LimitlessTCG's already-normalized data

### Phase 2: Enhanced Coverage

**Data:**
- [ ] Explore Pokecabook data integration (card adoption rates)
- [ ] Build automated scraping pipeline (with partnership if possible)
- [ ] Expand card mapping to comprehensive coverage

**UI:**
- [ ] BO1 vs BO3 comparison view
- [ ] "Format Forecast" section for upcoming international formats
- [ ] Card adoption rate display (unique from Pokecabook)

**Translation:**
- [ ] Implement LLM translation pipeline for analysis content
- [ ] Build glossary-enhanced prompts
- [ ] Partner with 1 bilingual validator

### Phase 3: Deep Insights

**Data:**
- [ ] Integrate Japanese YouTube/content analysis
- [ ] Track Japanese player opinions on new cards
- [ ] Build historical trend data for format transitions

**Content:**
- [ ] Regular "Japan Meta Report" (weekly/bi-weekly)
- [ ] "Format Forecast" analysis when new sets drop in Japan
- [ ] "BO1 vs BO3: What Transfers" educational content

**Translation:**
- [ ] Scale validation partnership
- [ ] Consider community translation contributions
- [ ] Build confidence scoring for translations

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Translation errors embarrass platform | Medium | High | Validator partnership, uncertainty flags |
| Japanese sources change/block access | Low | High | Multiple sources, partnership approach |
| BO1 meta misleads international players | Medium | Medium | Clear labeling, educational content |
| LLM costs for translation too high | Low | Medium | Cache aggressively, translate only high-value content |
| Bilingual validator unavailable | Medium | Medium | Build relationship with 2-3 candidates |

---

## Open Questions

1. **LimitlessTCG partnership scope:** Do they have Japanese data API, or is it the same scraping situation as international?

2. **Pokecabook outreach:** Is there an English-speaking contact, or need Japanese outreach?

3. **Official Pokemon Japan data:** What's accessible from players.pokemon-card.com? Worth exploring.

4. **Community interest validation:** Ask in English-speaking communities: "Would regular Japan meta reports be valuable to you?"

5. **Bilingual player identification:** Who in the community follows both metas and could help validate?

---

## Research Tasks Checklist

### Data Source Exploration

- [ ] Test LimitlessTCG Japanese page structure
- [ ] Explore Pokecabook site structure for scraping feasibility
- [ ] Check if players.pokemon-card.com has accessible data
- [ ] Research TCGdex API for Japanese card names
- [ ] Find existing Japanese ↔ English card mapping resources

### Translation Infrastructure

- [ ] Build initial TCG terminology glossary (50+ terms)
- [ ] Test Claude/GPT-4 on sample Japanese TCG content
- [ ] Compare LLM vs DeepL for TCG-specific text
- [ ] Identify 2-3 bilingual player candidates for validation partnership

### Community Validation

- [ ] Post in r/pkmntcg asking about Japanese meta interest
- [ ] Ask in Discord communities about Japan meta consumption
- [ ] Talk to coaches about how they use Japanese data currently

### Content Strategy

- [ ] Research existing "Japan meta report" content (competitors)
- [ ] Draft sample "Format Forecast" article structure
- [ ] Plan BO1 vs BO3 educational content

---

## References

### Card Reveal Translation Sources

Early access to card translations during reveal season is crucial for theorycrafting. Here are the key sources:

#### Primary Translation Sources

| Source | Platform | Focus | Speed | Data Quality |
|--------|----------|-------|-------|--------------|
| **LimitlessTCG /translations** | Web | Comprehensive set translations | Fast (usually within hours of JP reveal) | Very high - structured data |
| **JustInBasil.com** | Web | Set translations with visual proxies | Fast | High |
| **PokeBeach** | Web + X | News + translations | Very fast | High |
| **PokeGuardian** | Web + X | Card reveals + news | Fast | Medium-High |

#### Social Media Translation Accounts (X/Twitter)

| Account | Handle | Notes |
|---------|--------|-------|
| PokeBeach | @pokebeach | 22+ years of coverage, works with translators |
| PokeGuardian | @PokeGuardian | Card reveals with images |
| JustInBasil | @justinbasiltcg | Translations + visual proxies |
| Pokecabook | @pokeca_book | Japanese source with translations |

#### Bluesky Accounts
- JustInBasil is also on Bluesky (@justinbasil.com)
- PokeBeach community presence
- Growing TCG community on Bluesky

### LimitlessTCG Translation Page Structure

LimitlessTCG's `/translations` page is particularly valuable because:

1. **Organized by set**: Main expansions and side products separated
2. **Complete coverage**: "All translated unreleased cards" view available
3. **Structured URLs**: 
   - `/cards/jp/M3` - Set page (Nihil Zero)
   - `/cards/jp?translate=en&q=is:unreleased` - All unreleased cards in English
4. **Count tracking**: Shows "X new cards" and "X translated" for each set
5. **API potential**: URL structure suggests queryable data

**Current sets tracked (as of Jan 2026):**
- M3 Nihil Zero (80 cards)
- M2a Mega Dream ex (87 cards)
- MC Starter Decks 100 Battle Collection (68 cards)
- Various promotional cards

---

## Card Reveal Ingestion Pipeline

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                   CARD REVEAL INGESTION PIPELINE                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │   Sources   │───▶│   Ingest    │───▶│   Process   │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│        │                  │                   │                  │
│        ▼                  ▼                   ▼                  │
│  - LimitlessTCG    - Poll/webhook      - Validate card data     │
│  - PokeBeach       - Parse HTML/API    - Map to internal schema │
│  - Social feeds    - Extract card data - Generate embeddings    │
│  - Official JP     - Deduplicate       - Flag as "unreleased"   │
│                                                                  │
│                          │                                       │
│                          ▼                                       │
│                   ┌─────────────┐                               │
│                   │   Store &   │                               │
│                   │   Notify    │                               │
│                   └─────────────┘                               │
│                          │                                       │
│                          ▼                                       │
│  - Add to card database (flagged as JP-only)                    │
│  - Update "Upcoming Cards" section                              │
│  - Trigger alerts for subscribed users                          │
│  - Queue for meta impact analysis                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Data Sources Priority

**Tier 1: Structured (Primary)**
```
LimitlessTCG /translations
├── High data quality
├── Already structured
├── Consistent naming
└── Partnership conversation already planned
```

**Tier 2: Semi-Structured (Supplementary)**
```
JustInBasil.com /translations
├── Excellent visual proxies
├── Well-organized by set
└── Good for validation/cross-reference
```

**Tier 3: Real-time (Speed)**
```
Social Media (X/Bluesky)
├── Fastest for breaking reveals
├── May need cleanup/validation
├── Good for alerting, not primary storage
└── Consider firehose vs targeted follows
```

### Ingestion Strategies

#### Strategy 1: Poll-Based (MVP)

**How it works:**
- Periodic polling of LimitlessTCG translations page
- Check for new cards every 1-4 hours
- Parse page, compare to known cards, ingest new ones

**Pros:**
- Simple to implement
- No partnership required initially
- Reliable

**Cons:**
- Latency (hours, not minutes)
- Wasteful polling
- Could be rate-limited

**Implementation:**
```python
# Pseudocode for poll-based ingestion
async def poll_limitless_translations():
    page = await fetch("https://limitlesstcg.com/translations")
    sets = parse_sets_from_page(page)
    
    for set in sets:
        cards_url = f"https://limitlesstcg.com/cards/jp/{set.id}?translate=en"
        cards = await fetch_and_parse_cards(cards_url)
        
        for card in cards:
            if not card_exists_in_db(card):
                card.status = "jp_only_unreleased"
                card.source = "limitless"
                card.ingested_at = now()
                await save_card(card)
                await notify_subscribers(card)
```

#### Strategy 2: Social Media Monitoring (Real-time)

**How it works:**
- Monitor X/Bluesky for specific accounts and keywords
- Parse card reveals from tweets/posts
- Use LLM to extract structured card data from images/text
- Cross-reference with LimitlessTCG for validation

**Pros:**
- Near real-time (minutes)
- Catches breaking news
- Good for alerts

**Cons:**
- Noisy - needs filtering
- Unstructured - needs LLM processing
- API costs/limits (X API is expensive)

**Implementation considerations:**
- Bluesky API is free and more accessible
- Consider using RSS feeds where available
- LLM vision to parse card images is possible but expensive

#### Strategy 3: Partnership API (Ideal)

**How it works:**
- Formal partnership with LimitlessTCG
- Access to structured API or data feed
- Webhook notifications for new cards

**Pros:**
- Cleanest data
- Real-time possible
- Sustainable long-term

**Cons:**
- Requires partnership negotiation
- May have costs or obligations

### Card Data Model for Unreleased Cards

```typescript
interface UnreleasedCard {
  // Core identification
  id: string;                      // Generated ID until official
  japanese_id?: string;            // Japanese set ID (e.g., "M3-001")
  name_en: string;                 // Translated English name
  name_jp: string;                 // Original Japanese name
  
  // Card details
  supertype: "Pokemon" | "Trainer" | "Energy";
  subtypes: string[];
  hp?: number;
  types?: string[];
  attacks?: Attack[];
  abilities?: Ability[];
  rules?: string[];
  
  // Set information
  set_jp: string;                  // Japanese set name
  set_jp_code: string;             // e.g., "M3"
  set_en_expected?: string;        // Expected English set
  
  // Release tracking
  jp_release_date: Date;
  en_release_date_expected?: Date;
  status: "revealed" | "jp_released" | "en_released";
  
  // Source tracking
  source: "limitless" | "pokebeach" | "social" | "official";
  source_url?: string;
  first_seen_at: Date;
  last_updated_at: Date;
  
  // Translation metadata
  translation_confidence: "official" | "community" | "machine";
  translation_notes?: string;
  
  // Platform features
  text_embedding?: number[];       // For semantic search
  competitive_notes?: string;      // Early analysis
}
```

### Notification System

When new cards are ingested, notify relevant users:

```typescript
interface CardRevealNotification {
  card: UnreleasedCard;
  relevance: {
    // Why this card might matter to the user
    affects_archetypes: string[];    // ["Charizard ex", "Gardevoir ex"]
    is_staple_candidate: boolean;    // Likely to see wide play
    is_tech_option: boolean;         // Potential counter/tech
    meta_impact_estimate: "low" | "medium" | "high";
  };
  delivery: {
    in_app: boolean;
    email: boolean;                  // Pro tier only
    push: boolean;                   // Future mobile
  };
}
```

### Meta Impact Analysis

When new cards are revealed, automatically analyze potential meta impact:

```typescript
async function analyzeMetaImpact(card: UnreleasedCard): Promise<MetaImpactAnalysis> {
  // Use LLM to analyze card's potential impact
  const prompt = `
    Analyze this new Pokemon TCG card for competitive impact:
    ${JSON.stringify(card)}
    
    Current meta archetypes: ${await getCurrentMetaArchetypes()}
    
    Consider:
    1. Does this card strengthen any existing archetypes?
    2. Does this card enable new archetypes?
    3. Does this card counter any existing top decks?
    4. What existing cards does this synergize with?
    5. BO1 vs BO3 implications?
    
    Respond with structured analysis.
  `;
  
  return await llm.analyze(prompt);
}
```

---

## Implementation Roadmap for Card Reveals

### Phase 1: Basic Ingestion (MVP)

**Scope:**
- [ ] Poll LimitlessTCG /translations page every 4 hours
- [ ] Parse and store unreleased card data
- [ ] Display "Upcoming Cards" section on platform
- [ ] Basic card detail view with translation

**UI:**
- [ ] "Upcoming Sets" page listing JP-only sets
- [ ] Card browser filtered to unreleased cards
- [ ] "Japan-only" badge on cards not yet international

### Phase 2: Enhanced Features

**Scope:**
- [ ] Reduce poll interval (1-2 hours)
- [ ] Add social media monitoring for speed alerts
- [ ] Implement notification system for new reveals
- [ ] Add LLM-powered meta impact analysis

**UI:**
- [ ] "New Reveals" feed on homepage
- [ ] Subscription to specific archetypes/card types
- [ ] "Meta Impact" badge on high-impact reveals

### Phase 3: Real-time & Analysis

**Scope:**
- [ ] Partnership API access (if secured)
- [ ] Real-time webhook notifications
- [ ] Deep meta impact analysis with trends
- [ ] "Format Forecast" automated reports

**UI:**
- [ ] Real-time reveal notifications
- [ ] Theorycraft deck builder with unreleased cards
- [ ] "What this means for your deck" personalized analysis

---

## References

### Japanese Sources
- Pokecabook: https://pokecabook.com
- ポケカ飯: https://pokekameshi.com
- Official JP site: https://www.pokemon-card.com
- Pokemon Card Channel (YouTube): https://www.youtube.com/@PokemonCardChannel

### English Aggregators of Japanese Data
- LimitlessTCG Japan: https://limitlesstcg.com/tournaments/jp
- Pokemoncard.io Weekly Reports: https://pokemoncard.io (search "Weekly Japanese")
- PTCG Legends: https://www.ptcglegends.com

### Translation Research
- Claude/GPT-4 consistently top performers for JP↔EN (Lokalise study, WMT24)
- DeepL next-gen LLM: 1.7x improvement for Japanese
- TCGdex: Multi-language card database API

### Community Analysis
- Ecency post on Pokecabook: https://ecency.com/pokemontcg/@dkmathstats/pokecabook-site-for-japan-pokemon
- JustInBasil external resources: https://www.justinbasil.com/external
