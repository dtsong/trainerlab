# Pokemon TCG Competitive Intelligence Platform

> **Document Purpose:** Exploration, ideation, and pre-specification document for a competitive Pokemon TCG tools platform. Intended to evolve into formal specs for Claude Code implementation.

> **Last Updated:** January 2025

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Problem Space](#problem-space)
3. [Target Personas](#target-personas)
4. [Project Context & Constraints](#project-context--constraints)
5. [Feature Ideas & Prioritization](#feature-ideas--prioritization)
6. [Technical Architecture Vision](#technical-architecture-vision)
7. [Data Strategy](#data-strategy)
8. [LLM Integration Strategy](#llm-integration-strategy)
9. [Go-to-Market Approach](#go-to-market-approach)
10. [Creator/Coach Pitch Materials](#creatorcoach-pitch-materials)
11. [MVP Definition](#mvp-definition)
12. [Open Questions & Research Needed](#open-questions--research-needed)
13. [Appendix: Resources & References](#appendix-resources--references)

---

## Executive Summary

### Vision Statement

Build a unified platform that aggregates, analyzes, and presents competitive Pokemon TCG data in ways that help players at all levels make better decisions about deck building, testing, and tournament preparation—reducing the time and cognitive overhead currently required to compete effectively.

### Core Value Proposition

**For players:** Stop spending hours piecing together information from LimitlessTCG, YouTube videos, Discord discussions, and podcasts. Get actionable insights in one place.

**For coaches/creators:** Tools to demonstrate concepts visually, collaborate with students remotely, and create content more efficiently.

**For the ecosystem:** Raise the floor of competitive knowledge, making the game more accessible without diminishing the skill ceiling.

### Project Status

**Phase:** Early ideation and validation  
**Timeline:** Side project, iterative development  
**Team:** Solo developer (backend/infrastructure background) + AI coding agents

---

## Problem Space

### The Current State

Competitive Pokemon TCG players face a fragmented information landscape:

| Information Need | Current Sources | Pain Points |
|-----------------|-----------------|-------------|
| Tournament results & decklists | LimitlessTCG | Great data, limited analysis tools |
| Meta analysis & predictions | YouTube creators, podcasts | Time-consuming to consume, opinions vary |
| Matchup knowledge | Articles, videos, Discord | Scattered, inconsistent depth, quickly outdated |
| Personal performance tracking | Training Court, spreadsheets | Manual entry, limited insights |
| Deck building guidance | Experience, netdecking | Trial and error, hard to evaluate tech choices |
| Rules/interactions | Judges, forums, official docs | Hard to search, inconsistent answers |

### The Opportunity

1. **Aggregation:** Bring data together from multiple sources into unified views
2. **Analysis:** Surface insights that aren't obvious from raw data (trends, correlations, patterns)
3. **Accessibility:** Lower the barrier to competitive knowledge for newcomers
4. **Efficiency:** Save experienced players time in their preparation workflow
5. **Collaboration:** Enable remote coaching and testing when in-person isn't possible

### Why Now?

- LLMs enable natural language interfaces to complex data
- Vision models can parse board states from images
- The competitive scene is growing (larger Regionals, more content creators)
- Remote play (PTCG Live) has normalized digital tools in the workflow
- No dominant platform has captured this space yet

---

## Target Personas

### Primary Personas

#### 1. The Aspiring Competitor ("Alex")

**Profile:**
- 1-2 years into competitive play
- Has attended locals, maybe 1-2 Regionals
- Wants to make Day 2 / earn CP toward Worlds invite
- Budget-conscious but willing to invest in improvement

**Goals:**
- Understand the meta well enough to make informed deck choices
- Learn matchups without losing 50 games first
- Track progress and see improvement over time
- Find practice partners and resources

**Current Workflow:**
1. Watch 2-3 YouTube videos about "best decks" before a tournament
2. Copy a list from LimitlessTCG, maybe swap 1-2 cards
3. Play games on PTCG Live, often unsure why they lost
4. Attend tournament, go 4-4, feel like they "got unlucky"

**What Success Looks Like:**
- Confident deck choice with understanding of matchup spread
- Clear practice plan focused on weak matchups
- Ability to identify misplays in their own games
- Steady CP accumulation toward goals

---

#### 2. The Grinder ("Jordan")

**Profile:**
- 3+ years competitive experience
- Multiple Day 2s, maybe some Top 32/Top 8 finishes
- Actively pursuing Worlds invite
- Has a testing group, maybe works with a coach

**Goals:**
- Optimize deck choices and lists for expected meta
- Efficiently test matchups (time is limited)
- Identify edges others might miss
- Track performance to identify patterns

**Current Workflow:**
1. Deep dive into LimitlessTCG data before events
2. Test extensively with group, track results in spreadsheet
3. Consume multiple content creators' opinions, synthesize
4. Iterate on list up until registration deadline

**What Success Looks Like:**
- Data-backed deck and tech choices
- Clear matchup game plans before sitting down
- Performance analytics that reveal improvement areas
- Time savings in research phase

---

#### 3. The Content Creator / Coach ("Sam")

**Profile:**
- Produces YouTube videos, streams, or offers coaching
- Has competitive experience (Top 32+)
- Monetizes through content, Metafy, or direct coaching
- Needs tools to differentiate and demonstrate value

**Goals:**
- Create compelling, differentiated content
- Efficiently research and prepare content
- Demonstrate concepts visually to students
- Manage remote coaching sessions effectively

**Current Workflow:**
1. Manual research on LimitlessTCG, cross-reference with experience
2. Create slides/diagrams manually for explanations
3. Screen share PTCG Live for coaching (limited annotation tools)
4. Track student progress informally

**What Success Looks Like:**
- Embeddable visualizations for content
- Interactive board state tool for coaching
- Data-backed content that's hard to replicate
- Streamlined coaching session workflow

---

### Secondary Personas

#### 4. The Judge ("Morgan")

**Needs:** Quick ruling lookups, interaction searches, errata tracking  
**Priority:** Lower (smaller audience, but high loyalty if served well)

#### 5. The Supportive Parent ("Casey")

**Needs:** Simplified explanations, tournament logistics, coach evaluation  
**Priority:** Lower initially (less technical, more content-focused)

---

## Project Context & Constraints

### Developer Context

| Factor | Reality | Implication |
|--------|---------|-------------|
| Team size | Solo + AI agents | Must scope aggressively, automate everything possible |
| Technical strength | Backend/infrastructure | API-first architecture, frontend iteratively improved |
| Frontend skill | Improving (vibe coding) | Start simple, lean on component libraries, iterate |
| Time availability | Side project | Ship incrementally, validate before investing deeply |
| Funding | None currently | Free tier essential, monetization must be sustainable |

### Strategic Constraints

1. **Scope discipline:** Can't build everything—must pick highest-impact features first
2. **Validation-first:** Talk to users before building, not after
3. **Incremental value:** Each release should be useful standalone
4. **Ecosystem-friendly:** Partner, don't compete (LimitlessTCG, Training Court)
5. **Sustainable:** Costs must be manageable; can't subsidize forever

### Assets & Advantages

1. **Community connections:** Direct access to coaches, creators, local players for feedback
2. **Technical depth:** Can build robust backend, APIs, data pipelines
3. **AI leverage:** Claude Code and agents can accelerate development significantly
4. **Domain knowledge:** Understanding of competitive play informs product decisions
5. **No legacy baggage:** Can build with modern stack, clean architecture

### Legal Considerations

- **Pokemon Company stance:** Generally permissive of fan tools that enhance the ecosystem
- **Guidelines to follow:**
  - Don't host copyrighted card images directly (use official APIs or link to official sources)
  - Don't misrepresent as official Pokemon product
  - Don't enable piracy or circumvent official digital products
  - Credit sources appropriately
- **Upside scenario:** If tools demonstrably improve player experience at events, could lead to official recognition or partnership

---

## Feature Ideas & Prioritization

### Prioritization Framework

**Impact:** How much value does this deliver to users?  
**Feasibility:** How hard is this to build given constraints?  
**Differentiation:** Does this exist elsewhere? Can we do it better?  
**Foundation:** Does this enable other features?

### Feature Matrix

| Feature | Impact | Feasibility | Differentiation | Foundation | Priority |
|---------|--------|-------------|-----------------|------------|----------|
| Meta Dashboard | High | High | Medium | High | **P0** |
| Smart Deck Builder | High | Medium | High | High | **P0** |
| Card Search (NL) | Medium | High | Medium | High | **P0** |
| **Japanese Meta Integration** | High | Medium | **Very High** | Medium | **P0** |
| Personal Stats Tracker | Medium | Medium | Low* | Medium | **P1** |
| Matchup Guides | High | Low** | High | Low | **P1** |
| Format Forecast Reports | High | Medium | **Very High** | Low | **P1** |
| Board State Simulator | High | Low | High | Medium | **P2** |
| Coaching Collaboration | High | Low | High | Low | **P2** |
| Judge Reference | Medium | Medium | Medium | Low | **P2** |
| Tournament Prep Wizard | Medium | Medium | High | Low | **P2** |
| Creator Embed Tools | Medium | Medium | High | Low | **P2** |
| Parent's Guide | Low | High | Medium | Low | **P3** |

*Training Court exists but could integrate/extend  
**Content creation is the bottleneck, not tech

### Key Differentiator: Japanese Data

The Japanese metagame integration is elevated to **P0** because:

1. **Unique value:** Few Western resources consistently cover Japanese meta
2. **Competitive advantage:** Early format research is genuinely useful
3. **Data exists:** LimitlessTCG already captures it, we're adding analysis
4. **Content engine:** Drives regular "Format Forecast" content
5. **Pro tier justification:** Deep Japanese analysis as premium feature

**BO1 vs BO3 caveat** must be clearly communicated:
- Japanese meta (BO1) ≠ International meta (BO3)
- Show data separately, explain the differences
- Users should understand why lists may differ

### P0 Features (MVP)

#### Meta Dashboard

**What:** Visual representation of the competitive metagame

**Core functionality:**
- Archetype meta share (pie/bar chart)
- Meta share over time (line chart)
- Regional breakdown (NA/EU/APAC/LATAM)
- Recent tournament results with deck breakdowns
- Archetype "cards in common" view

**Data sources:** LimitlessTCG (primary), supplementary community data

**Differentiation:** LimitlessTCG shows data; we show *insights* (trends, shifts, regional variation)

---

#### Smart Deck Builder

**What:** Deck building tool that advises, not just stores

**Core functionality:**
- Card database with search (including natural language)
- Archetype templates (skeleton lists to start from)
- Card inclusion rates ("Iono is in 98% of Charizard lists")
- Consistency metrics (supporter count, search density, energy curve)
- Diff view against reference lists
- Tech card suggestions based on expected meta

**Data sources:** Card database API, LimitlessTCG for inclusion rates

**Differentiation:** Most builders are just card databases; this one helps you understand *why* cards are included and *what* you might be missing

---

#### Natural Language Card Search

**What:** Search for cards by describing what they do, not just by name

**Core functionality:**
- "Find all supporters that draw cards"
- "Pokemon that do damage to the bench"
- "Items that search for basic Pokemon"
- "Cards that punish large benches"

**Implementation:** Embed card text, use semantic search

**Differentiation:** Current search is keyword-based; this understands intent

---

### P1 Features (Post-MVP)

#### Personal Performance Tracker

**What:** Log games, track results, surface patterns

**Core functionality:**
- Game logging (matchup, result, notes, key moments)
- Win rate by archetype, by matchup
- Pattern analysis ("You're 2-7 vs Lugia, here's what to focus on")
- Goal tracking (CP progress, conversion rates)
- Integration with Training Court if possible

---

#### Interactive Matchup Guides

**What:** Dynamic, explorable guides for specific matchups

**Core functionality:**
- Decision trees for common game states
- Opening hand evaluation by matchup
- Prize mapping scenarios
- Key cards to track
- Community contributions + expert curation

**Challenge:** Content creation is the bottleneck—need creator partnerships or community contribution system

---

### P2 Features (Future)

- **Board State Simulator:** Set up and analyze game states, calculate outs
- **Coaching Collaboration:** Shared board state, voice/video, annotation tools
- **Judge Reference:** Ruling lookup, interaction search
- **Tournament Prep Wizard:** Guided pre-tournament preparation
- **Creator Embed Tools:** Widgets for content creators

---

## Technical Architecture Vision

### Guiding Principles

1. **API-first:** Build robust APIs; frontends are consumers
2. **Data pipeline focus:** Clean, reliable data ingestion is the foundation
3. **Incremental complexity:** Start simple, add sophistication as needed
4. **Cost-conscious:** Design for low operational costs
5. **AI-augmented development:** Leverage Claude Code for implementation

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│  Web App (Next.js)  │  Mobile (Future)  │  Embeds (Creators)   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         API LAYER                                │
├─────────────────────────────────────────────────────────────────┤
│  REST API (FastAPI/Node)  │  GraphQL (Optional)  │  WebSocket   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                       SERVICE LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│  Meta Analysis  │  Deck Builder  │  Card Search  │  User Data   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        DATA LAYER                                │
├─────────────────────────────────────────────────────────────────┤
│  PostgreSQL     │  Vector DB      │  Redis Cache  │  File Store │
│  (Structured)   │  (Embeddings)   │  (Hot data)   │  (Images)   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     INGESTION LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│  Card Data Sync  │  Tournament Scraper  │  Community Input      │
│  (API pulls)     │  (LimitlessTCG)      │  (User submissions)   │
└─────────────────────────────────────────────────────────────────┘
```

### Suggested Tech Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| Frontend | Next.js 14+ (App Router) | SSR, good DX, easy deployment |
| Styling | Tailwind + shadcn/ui | Fast iteration, consistent design |
| Charts | Recharts or Chart.js | Good React integration |
| Backend | FastAPI (Python) | Fast, type-safe, good for data work |
| Database | PostgreSQL (Supabase) | Managed, includes auth, generous free tier |
| Vector DB | Supabase pgvector | Avoid separate service, good enough for scale |
| Cache | Redis (Upstash) | Serverless, pay-per-use |
| Auth | Supabase Auth | Integrated with DB, free tier |
| Hosting | Vercel (frontend), Railway (backend) | Easy deployment, reasonable costs |
| LLM | Claude API | Quality, vision capabilities |
| Search | Meilisearch or Algolia | Fast, typo-tolerant |

### Cost Estimates (Side Project Scale)

| Service | Free Tier | Estimated Monthly (Growing) |
|---------|-----------|----------------------------|
| Vercel | 100GB bandwidth | $0-20 |
| Supabase | 500MB DB, 50K auth users | $0-25 |
| Railway | $5 credit | $5-20 |
| Upstash Redis | 10K commands/day | $0-10 |
| Claude API | Pay per use | $10-50 (depends on usage) |
| Domain | N/A | $12/year |
| **Total** | | **$15-125/month** |

---

## Data Strategy

### Strategic Data Advantage: Japanese Metagame

#### Why Japanese Data Matters

Japan receives new Pokemon TCG sets **2-3 months before international release**. This creates a valuable window where:

1. **Japanese City Leagues and Champions Leagues** establish early meta patterns
2. **International players** can research upcoming formats before they hit
3. **Content creators** can produce forward-looking content
4. **Coaches** can prepare students for format shifts

**This is an underutilized competitive advantage.** Most Western players don't actively track Japanese results, creating an opportunity for those who do.

#### Japanese Tournament Structure

| Tournament Type | Format | Size | Frequency | Data Value |
|-----------------|--------|------|-----------|------------|
| City League | Best of 1 | 32-128 | Weekly across Japan | High volume, early meta signals |
| Champions League | Best of 1 | 5,000-6,000 | ~4/year | Massive sample size, meta-defining |
| Japan Championships | Best of 1 | Qualified | Annual | Peak Japanese meta |

**Key Differences from International:**
- **Best of 1 (BO1):** Changes optimal deck building (consistency > techs, aggro favored)
- **Massive scale:** Champions Leagues dwarf international Regionals (5K+ vs 2,400 cap)
- **Different meta pressures:** BO1 meta can differ significantly from BO3

#### Data Source

**Primary:** LimitlessTCG Japanese coverage
- URL: https://limitlesstcg.com/tournaments/jp
- Coverage includes City Leagues, Champions Leagues
- Archetype classification consistent with international

**Considerations:**
- Same partnership/access conversation as international data
- Japanese card names may differ (need mapping)
- Set release timing offset needs tracking

#### Analysis Opportunities

**1. Early Format Preview**
> "Here's what the Japanese meta looks like with [New Set]. Expect these archetypes when it releases internationally."

**2. BO1 vs BO3 Meta Comparison**
> "This deck performs better in BO1 (Japanese) than BO3 (International). Here's why and what it means for your testing."

**3. Card Performance Tracking**
> "This new card is seeing X% play in Japan. Historical data suggests similar cards see Y% adoption internationally."

**4. Archetype Evolution Tracking**
> "Watch how [Archetype] evolved in Japan over 2 months—this is likely where international lists will land."

#### Feature Integration

**Meta Dashboard Additions:**
- Japan tab alongside NA/EU/APAC/LATAM
- "Upcoming Format Preview" section
- BO1 vs BO3 meta comparison view

**Deck Builder Additions:**
- Japanese inclusion rates (with BO1 caveat)
- "Cards not yet legal internationally" indicators
- Set release timeline visualization

**Pro Tier Differentiation:**
- Deep Japanese meta analysis could be Pro-only
- "Format forecast" reports
- Japanese list translations/breakdowns

#### Implementation Notes

```
// Japanese-specific data model additions

Card {
  // ... existing fields
  japaneseReleaseDate: date?  // When available in Japan
  internationalReleaseDate: date?  // When legal internationally
  japaneseCardId: string?  // For cross-reference
}

Tournament {
  // ... existing fields
  bestOf: 1 | 3  // Important for meta analysis
  region: "NA" | "EU" | "APAC" | "LATAM" | "JP"  // Add Japan
}

MetaSnapshot {
  // ... existing fields
  bestOfFormat: 1 | 3  // Distinguish BO1 vs BO3 meta
  formatPreview: boolean  // Is this data for an upcoming international format?
}
```

#### Content Opportunities

**Regular content series:**
- "Japan Meta Report" (weekly/bi-weekly)
- "Format Forecast" (when new set drops in Japan)
- "BO1 vs BO3: What Changes" (educational)

**This is differentiated content** that few Western sources produce consistently.

---

### Data Sources

#### Primary: Card Database

**Source:** [pokemontcg.io](https://pokemontcg.io/) API  
**Update frequency:** Per set release (~4x/year major, more with promos)  
**Data points:** Card name, text, types, HP, attacks, abilities, set, rarity, images (linked)

**Considerations:**
- API is free and well-maintained
- Rate limits exist; implement caching
- Images are hosted externally (respect their bandwidth)

#### Primary: Tournament Data

**Source:** [LimitlessTCG](https://limitlesstcg.com/)  
**Update frequency:** After each tournament (weekly during season)  
**Data points:** Tournament results, decklists, player standings, archetype classifications

**Considerations:**
- No official API; would need scraping or partnership
- **Action item:** Reach out to Limitless team about data partnership
- Fallback: Respectful scraping with caching, attribution

#### Secondary: Official Pokemon Sources

- [pokemon.com](https://www.pokemon.com/us/pokemon-tcg) for official card database
- Tournament rules and formats
- Ban list and rotation announcements

#### Tertiary: Community Data

- User-submitted game logs
- Community-reported matchup data
- Crowdsourced tech card suggestions

### Data Models (Draft)

```
// Core entities

Card {
  id: string (official ID)
  name: string
  supertype: "Pokemon" | "Trainer" | "Energy"
  subtypes: string[]
  hp: number?
  types: string[]
  attacks: Attack[]
  abilities: Ability[]
  weaknesses: Weakness[]
  resistances: Resistance[]
  retreatCost: number
  rules: string[]
  set: SetReference
  rarity: string
  imageUrl: string
  textEmbedding: vector? // For semantic search
}

Archetype {
  id: string
  name: string
  primaryCards: CardReference[] // Cards that define the archetype
  format: Format
  firstAppearance: date
  description: string
}

Tournament {
  id: string
  name: string
  date: date
  location: string
  region: "NA" | "EU" | "APAC" | "LATAM"
  format: Format
  tier: "Regional" | "International" | "Worlds" | "League Cup" | "League Challenge"
  attendance: number
}

TournamentResult {
  id: string
  tournament: TournamentReference
  player: PlayerReference
  decklist: Decklist
  archetype: ArchetypeReference
  placement: number
  record: { wins: number, losses: number, ties: number }
}

Decklist {
  id: string
  cards: { card: CardReference, count: number }[]
  archetype: ArchetypeReference
  format: Format
}

// User entities

User {
  id: string
  username: string
  tier: "free" | "pro" | "creator"
  createdAt: timestamp
}

UserDecklist {
  id: string
  user: UserReference
  decklist: Decklist
  name: string
  notes: string
  isPublic: boolean
}

GameLog {
  id: string
  user: UserReference
  date: timestamp
  myDeck: ArchetypeReference
  opponentDeck: ArchetypeReference
  result: "win" | "loss" | "tie"
  wentFirst: boolean
  notes: string
  keyMoments: string[]
  tournamentContext: string? // "League Cup Round 3", etc.
}
```

---

## LLM Integration Strategy

### Where LLMs Add Clear Value

| Use Case | Implementation | Why LLM? |
|----------|---------------|----------|
| Natural language card search | Embed card text + attacks + abilities, semantic search | Users think in concepts, not keywords |
| Explain card interactions | RAG over rulings + card text | Natural language explanations |
| Game note analysis | Summarize patterns across logs | Unstructured text understanding |
| Matchup guide drafts | Generate initial content from data | Speed up content creation |
| Coaching Q&A | Answer situational questions | Flexible, contextual responses |

### Where LLMs Are Not the Answer

| Task | Better Approach | Why? |
|------|-----------------|------|
| Calculate meta percentages | SQL aggregation | Exact math required |
| Validate deck legality | Rule engine | Deterministic, must be 100% accurate |
| Display tournament results | Database query | Structured data retrieval |
| Swiss pairing simulation | Monte Carlo | Probabilistic math |
| Consistency calculations | Hypergeometric math | Precise probability needed |

### Implementation Approach

**Phase 1 (MVP):** Natural language card search only
- Embed all card text using Claude or open-source model
- Store in pgvector
- Simple semantic search endpoint

**Phase 2:** Expand to explanations and analysis
- RAG for ruling questions
- Game log pattern analysis
- Matchup insight generation

**Phase 3:** Interactive coaching assistant
- Contextual Q&A during deck building
- Board state analysis from images
- Practice recommendations

### Cost Management

- Cache common queries aggressively
- Use smaller models where possible (embeddings don't need Claude)
- Rate limit LLM features for free tier
- Batch processing for analysis tasks (not real-time)

---

## Monetization Strategy

### Context & Constraints

**Audience Demographics:**
- **Juniors (under 13):** Limited/no spending power, parents control purchases
- **Seniors (13-17):** Some discretionary spending, often parent-subsidized
- **Masters (18+):** Full range from college students to working professionals
- **Parents:** Often willing to invest in their child's hobby/development

**Existing Spending Patterns:**
| Category | Typical Spend | Notes |
|----------|--------------|-------|
| Cards/Product | $50-500+/month | Highly variable, whales exist |
| Tournament Entry | $25-50/event | Regionals, ICs |
| Travel | $200-2000/event | Hotels, flights for major events |
| Coaching (Metafy) | $30-100/hour | 1:1 sessions |
| Patreon/Memberships | $5-25/month | Creator subscriptions |
| PTCG Live | $0-20/month | Digital product purchases |

**Key Insight:** Players already allocate budget to improvement. The question is whether a tools platform captures part of that spend or monetizes differently.

### Revenue Model Options

#### Option 1: Freemium Subscription

**How it works:** Core features free, premium tier unlocks advanced features

**Pricing:**
- **Free:** Meta dashboard (limited history), deck builder (3 saved decks), basic search
- **Pro ($5-8/month):** Full history, unlimited decks, advanced analytics, Japanese data, no ads
- **Creator ($15-20/month):** API access, embeddable widgets, white-label options

**Pros:**
- Predictable recurring revenue
- Aligns incentives (we succeed when users get value)
- Common model users understand

**Cons:**
- Conversion rates typically 2-5% for tools
- Need significant free user base to generate meaningful revenue
- Younger users may not convert

**Revenue projection (optimistic):**
- 10,000 free users → 300-500 Pro subscribers → $1,500-4,000/month

---

#### Option 2: Advertising + Sponsorships

**How it works:** Display ads, sponsored content, affiliate partnerships

**Ad Types:**
- **Display ads:** Banner ads from ad networks (low CPM but passive)
- **Sponsored content:** "This meta snapshot brought to you by [Card Shop]"
- **Affiliate links:** Link to TCGPlayer/eBay for card purchases (3-5% commission)
- **Event sponsorships:** Tournament organizers promoting events

**Potential Partners:**
- Online card retailers (TCGPlayer, Card Cavern, Full Grip Games)
- Local game stores (LGS directory/promotion)
- Sleeve/accessory brands (Ultra Pro, Dragon Shield, KMC)
- Tournament organizers
- Content creators (cross-promotion)

**Pros:**
- Keeps core product free (accessibility)
- Scales with traffic
- Affiliate links provide value (users want to buy cards anyway)

**Cons:**
- Ads can degrade UX
- Need significant traffic for meaningful ad revenue
- Sponsor relationships require sales effort

**Revenue projection:**
- 50,000 monthly pageviews × $5 CPM = $250/month (display ads)
- Affiliate: 1,000 clicks/month × 5% conversion × $50 avg order × 4% commission = $100/month
- Sponsorships: $200-500/month per sponsor (highly variable)

---

#### Option 3: Hybrid Model (Recommended)

**How it works:** Combine freemium with tasteful advertising/affiliates

**Structure:**
- **Free tier:** Full access to core features, sees non-intrusive ads, affiliate links
- **Pro tier ($5/month):** Ad-free experience, advanced features, Japanese data deep-dive
- **Sponsorships:** Integrated naturally (meta snapshots, tournament coverage)

**Why this works:**
- Free tier is genuinely useful (drives adoption)
- Ads provide baseline revenue without paywalling content
- Pro tier for users who want premium experience
- Sponsorships scale with credibility/traffic

**Ad placement guidelines (to preserve UX):**
- No interstitials or pop-ups
- No auto-playing video
- Clearly labeled sponsored content
- Ads don't interrupt core workflows
- One ad unit per page maximum

---

#### Option 4: Creator Revenue Share

**How it works:** Platform takes cut of coach/creator transactions

**Mechanics:**
- Coaches list services on platform
- Students book/pay through platform
- Platform takes 10-15% (vs Metafy's ~20%)

**Pros:**
- High-value transactions
- Aligns with coach success
- Natural extension of platform value prop

**Cons:**
- Competes with established players (Metafy)
- Requires payment infrastructure
- Trust/safety considerations
- More complex to build

**Timeline:** Phase 2 or later—only pursue if coach partnerships develop

---

#### Option 5: Data/API Licensing

**How it works:** Sell API access to other developers, researchers, or businesses

**Potential customers:**
- Other Pokemon TCG tool developers
- Content creators needing data
- Academic researchers studying game theory
- Card pricing/inventory services

**Pricing:** $50-200/month for API access

**Pros:**
- B2B revenue is more stable
- Leverages data infrastructure investment

**Cons:**
- Small market
- Need robust API and documentation
- Support burden

**Timeline:** Long-term option once data infrastructure is mature

---

### Recommended Monetization Roadmap

**Phase 1 (MVP - Month 0-6):** Free + Donations
- Everything free, no ads
- "Buy me a coffee" / GitHub Sponsors link
- Goal: Build user base and credibility
- Revenue target: $0-100/month (not the point)

**Phase 2 (Growth - Month 6-12):** Introduce Ads + Affiliates
- Add non-intrusive ad placements
- Integrate TCGPlayer affiliate links in deck builder
- Approach 1-2 sponsors for meta content
- Revenue target: $200-500/month

**Phase 3 (Sustainability - Month 12-18):** Launch Pro Tier
- Define clear Pro feature set
- Price at $5-8/month (accessible)
- Maintain strong free tier (don't gut it)
- Revenue target: $500-1,500/month

**Phase 4 (Scale - Month 18+):** Expand Revenue Streams
- Creator tools and potential marketplace
- API licensing for developers
- Premium sponsorship packages
- Revenue target: $2,000+/month

---

### Ethical Considerations

**Protecting younger users:**
- No predatory monetization (loot boxes, gambling mechanics)
- Ads must be appropriate for all ages
- Don't exploit FOMO or social pressure
- Parental consent considerations for payments

**Maintaining trust:**
- Sponsored content clearly labeled
- Editorial independence from sponsors
- Don't let monetization compromise data integrity
- Transparent about what's free vs. paid

**Fair value exchange:**
- Free tier must be genuinely useful (not crippled)
- Pro tier should feel worth it, not extractive
- Don't paywall information that should be accessible

---

### Competitor Monetization Reference

| Platform | Model | Notes |
|----------|-------|-------|
| LimitlessTCG | Free (donations?) | Appears volunteer-run, community goodwill |
| Training Court | Free (open source) | No monetization, passion project |
| Metafy | Transaction fee (20%) | Takes cut of coaching sessions |
| TCGPlayer | Marketplace fees | 10-15% of card sales |
| Pokemon content creators | Ads, Patreon, sponsors | YouTube/Twitch + membership |
| Untap.in (MTG) | Patreon + ads | Similar tools, different game |

---

## Go-to-Market Approach

### Phase 0: Validation (Current)

**Goals:**
- Validate problem and solution assumptions
- Build relationships with potential early users
- Refine feature priorities

**Actions:**
1. Share vision doc with trusted coaches/creators (2-3 people)
2. Get feedback on feature priorities
3. Identify 5-10 potential beta testers across personas
4. Lurk in Discord/Reddit to understand pain points better

**Deliverables:**
- Refined feature priorities
- Committed beta tester list
- Creator partnership interest

### Phase 1: MVP Launch (Target: 2-3 months)

**Goals:**
- Ship usable MVP to beta testers
- Gather feedback and iterate
- Build initial content (meta snapshots, maybe 1 matchup guide)

**MVP Features:**
- Meta dashboard (archetype share, trends, regional breakdown)
- Smart deck builder (templates, inclusion rates, diff view)
- Natural language card search
- Basic user accounts

**Launch approach:**
- Private beta with committed testers
- Weekly feedback calls/async Discord
- Iterate based on real usage

### Phase 2: Public Launch (Target: 4-6 months)

**Goals:**
- Open to public
- Establish presence in community
- Begin monetization experiments

**Actions:**
1. Announce in Pokemon TCG communities (Reddit, Discord, Twitter)
2. Partner with 1-2 creators for exposure
3. Launch free tier with limited features
4. Introduce Pro tier ($5-10/month)

**Pro Tier Features:**
- Full historical data access
- Unlimited saves/exports
- Personal analytics
- Priority support

### Phase 3: Expansion (6-12 months)

**Depends on traction, but potential paths:**
- Matchup guides (community + curated)
- Board state simulator
- Coaching tools
- Creator embed tools
- Coach marketplace (revenue share model)

### Community Building

**Discord Server:**
- Feature announcements
- Feedback collection
- Community meta discussion
- Beta tester coordination

**Content Strategy:**
- Monthly "State of the Meta" posts
- Tournament preview articles
- Feature highlight posts
- Creator spotlights (relationship building)

---

## Creator/Coach Pitch Materials

### Pitch Deck Outline

**Slide 1: The Problem**
> Your students spend hours piecing together information from 10 different sources before they even sit down to test. What if that research was done for them?

**Slide 2: The Vision**
> A unified platform that gives competitive Pokemon TCG players the data, insights, and tools to make better decisions—faster.

**Slide 3: For You (Creator/Coach)**
- Visual tools to demonstrate concepts
- Data to fuel content creation
- Collaboration features for remote coaching
- Embeddable widgets for your content

**Slide 4: What We're Building (MVP)**
- Meta dashboard with trends and regional breakdown
- Smart deck builder with inclusion rates and consistency metrics
- Natural language card search

**Slide 5: What's Next**
- Interactive matchup guides (partnership opportunity!)
- Board state simulator for coaching
- Personal performance tracking

**Slide 6: How You Can Help**
- Early feedback on designs and features
- Beta testing with your students
- Content partnership (guides, reviews)
- Spread the word when we launch

**Slide 7: What You Get**
- Early access to all features
- Input on roadmap priorities
- Creator tier (free) with embed tools
- Credit and attribution in the platform

### Conversation Starters

**For coaches:**
> "I'm building a tool that could save your students hours of pre-tournament research. What do you wish they came to sessions already knowing?"

**For content creators:**
> "I'm working on embeddable meta charts and deck comparison tools. Would something like that be useful for your videos/streams?"

**For experienced players:**
> "What's the most tedious part of your tournament prep? I'm building tools to automate the boring stuff."

### Key Messages

1. **This helps the whole ecosystem:** More informed players = better tournaments = healthier competitive scene
2. **We're building with the community:** Your feedback shapes what we build
3. **Complement, not compete:** This makes your coaching/content more valuable, not less
4. **Open to partnership:** If you want to create content for the platform, let's talk

---

## MVP Definition

### Scope

**In scope:**
- Meta dashboard (read-only, data visualization)
- Smart deck builder (create, save, analyze decks)
- Natural language card search
- User accounts (basic auth)
- Free tier (limited features)

**Out of scope for MVP:**
- Personal performance tracking
- Matchup guides
- Board state simulator
- Coaching features
- Mobile app
- Paid tiers (ship free, add later)

### User Stories

#### Meta Dashboard

```
As a competitive player,
I want to see current meta share percentages,
So that I can understand what decks I'm likely to face.

As a competitive player,
I want to see how meta share has changed over time,
So that I can identify rising and falling archetypes.

As a competitive player,
I want to filter meta data by region,
So that I can prepare for my specific tournament's expected meta.

As a competitive player,
I want to see recent tournament results,
So that I can find successful lists to reference.
```

#### Smart Deck Builder

```
As a player building a deck,
I want to start from an archetype template,
So that I don't have to start from scratch.

As a player building a deck,
I want to see how often each card appears in successful lists,
So that I can understand what's core vs. flexible.

As a player building a deck,
I want to see consistency metrics (supporter count, etc.),
So that I can evaluate if my list is consistent enough.

As a player building a deck,
I want to compare my list to top-performing lists,
So that I can see what I might be missing.

As a player building a deck,
I want to save my lists to my account,
So that I can access them later.
```

#### Natural Language Card Search

```
As a player,
I want to search for cards by describing their effect,
So that I can find cards I don't know by name.

As a player,
I want to search for "cards that draw" or "bench damage",
So that I can discover options I might have missed.
```

### Success Criteria

**Quantitative:**
- 50+ beta users registered
- 20+ weekly active users
- 100+ decklists saved
- <3 second page load times
- <1% error rate

**Qualitative:**
- Positive feedback from 3+ coaches/creators
- Users report saving time in tournament prep
- Feature requests indicate engagement (people want more)

### Technical Requirements

- Mobile-responsive web design
- Works on modern browsers (Chrome, Firefox, Safari, Edge)
- Page load <3 seconds
- API response <500ms (p95)
- 99% uptime
- Daily data refresh for meta information

---

## Open Questions & Research Needed

### Data & Partnerships

- [ ] **LimitlessTCG partnership:** Reach out about data access (API or partnership)
- [ ] **pokemontcg.io reliability:** Test API thoroughly, understand limits
- [ ] **Data freshness:** How quickly does LimitlessTCG update after tournaments?

### Technical

- [ ] **Embedding model:** Claude vs. open-source for card embeddings (cost/quality tradeoff)
- [ ] **Hosting costs at scale:** Model out costs at 1K, 10K, 100K users
- [ ] **Offline capability:** Is PWA/offline support important for tournament use?

### Product

- [ ] **Training Court integration:** Reach out about partnership/integration vs. building own tracker
- [ ] **Monetization validation:** Would players pay $5-10/month? Survey needed
- [ ] **Feature priority validation:** Survey target users on most-wanted features

### Legal

- [ ] **Terms of service:** What ToS do we need?
- [ ] **Card images:** Confirm we can link to official/pokemontcg.io images
- [ ] **Data attribution:** What attribution does LimitlessTCG require?

### Community

- [ ] **Discord server setup:** When to launch, how to moderate
- [ ] **Content calendar:** What regular content should we produce?
- [ ] **Creator partnerships:** Who are the best 2-3 to approach first?

---

## Appendix: Resources & References

### Existing Resources in the Ecosystem

#### Data Sources
- [LimitlessTCG](https://limitlesstcg.com/) - Tournament results, decklists, player data
- [pokemontcg.io](https://pokemontcg.io/) - Card database API
- [Trainer Hill Tools](https://www.trainerhill.com/tools) - Various community tools
- [Training Court](https://www.trainingcourt.app/home) - Game logging app ([GitHub](https://github.com/jlgrimes/training-court))

#### Content Creators (YouTube)
- [AzulGG](https://www.youtube.com/@AzulGG)
- [LittleDarkFury](https://www.youtube.com/@LittleDarkFury) / [LDF TCG](https://www.youtube.com/@ldftcg)
- [Tablemon](https://www.youtube.com/@tablemon)
- [ZapdosTCG](https://www.youtube.com/@ZapdosTCG)
- [Celio's Network](https://www.youtube.com/@CeliosNetwork)
- [Ciaran TCG](https://www.youtube.com/@CiaranTCG)
- [Rahul Reddy](https://www.youtube.com/@RahulReddy)
- [Danny Phantump](https://www.youtube.com/@DannyPhantump)
- [Tricky Gym](https://www.youtube.com/@TrickyGym)

#### Podcasts
- [Uncommon Energy](https://www.youtube.com/@UncommonEnergyPodcast)
- [Shift Gear Podcast](https://www.youtube.com/@ShiftGearPodcast)

### Technical References

- [Next.js Documentation](https://nextjs.org/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Supabase Documentation](https://supabase.com/docs)
- [shadcn/ui Components](https://ui.shadcn.com/)
- [Recharts](https://recharts.org/)
- [Claude API Documentation](https://docs.anthropic.com/)

### Spec-Driven Development

- [GitHub Spec-Kit](https://github.com/github/spec-kit) - Specification-driven development framework
- Consider adopting for formal specs after exploration phase

---

## Document History

| Date | Author | Changes |
|------|--------|---------|
| Jan 2025 | Initial | Created exploration document |

---

## Next Steps

1. **Immediate:** Review this document, identify gaps
2. **This week:** Share pitch with 2-3 trusted coaches/creators
3. **Next week:** Begin technical exploration (API testing, prototype)
4. **2 weeks:** Refine MVP scope based on feedback
5. **Ongoing:** Evolve this doc into formal specs for Claude Code
