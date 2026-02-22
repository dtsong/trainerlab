# TrainerLab - Implementation Spec v3.0

> Competitive intelligence platform for Pokemon TCG

**Domain:** trainerlab.io

---

## 1. Project Overview

### 1.1 What We're Building

**TrainerLab** — A competitive intelligence platform for Pokemon TCG trainers, coaches, content creators, and families. We help users make data-driven decisions about deck building, format preparation, and the hobby overall.

**Key differentiators:**

- Japanese metagame integration providing 2-3 month format preview
- Progressive disclosure design (Editorial → Hybrid → Terminal)
- JP Signal system highlighting meta divergence
- Commerce integration for deck building

### 1.2 Target Users

| User Type           | Primary Need                                          |
| ------------------- | ----------------------------------------------------- |
| Competitive Players | Meta analysis, deck building, tournament prep         |
| Coaches             | Student progress, meta teaching, deck recommendations |
| Content Creators    | Data for articles/videos, trending topics             |
| Parents             | Understanding the hobby, budget-conscious decisions   |

### 1.3 MVP Scope (v3.0)

**Completed (Phases 1-4):**

- Card database with search (keyword + fuzzy)
- Deck builder (create, save, load, export)
- Meta dashboard (archetype shares, trends)
- Japanese meta view (separate BO1 context)

**In Progress (Phase 5):**

- NextAuth.js + Google OAuth authentication
- User preferences
- Loading states, error handling
- Mobile responsiveness
- Tests

**New in v3.0 (Phases 6-14):**

- Design system overhaul
- Home page redesign
- Meta dashboard with archetype panels
- From Japan page with predictions
- Tournament archive
- Lab Notes content system
- Commerce integration
- Data pipeline (scrapers)

---

## 2. Design System

### 2.1 Progressive Disclosure Layers

TrainerLab uses three visual layers that reveal increasing data density:

| Layer | Name      | Typography       | Use Case                     |
| ----- | --------- | ---------------- | ---------------------------- |
| 1     | Editorial | Playfair Display | Headlines, hero, marketing   |
| 2     | Hybrid    | DM Sans          | Body text, navigation, cards |
| 3     | Terminal  | JetBrains Mono   | Data tables, panels, stats   |

### 2.2 Color Palette

#### Primary Colors

```css
/* Teal - Primary brand color */
--teal-50: #f0fdfa;
--teal-100: #ccfbf1;
--teal-200: #99f6e4;
--teal-300: #5eead4;
--teal-400: #2dd4bf;
--teal-500: #14b8a6; /* Primary */
--teal-600: #0d9488;
--teal-700: #0f766e;
--teal-800: #115e59;
--teal-900: #134e4a;
--teal-950: #042f2e;

/* Amber - Accent/Warning */
--amber-50: #fffbeb;
--amber-500: #f59e0b;
--amber-600: #d97706;

/* Parchment - Editorial backgrounds */
--parchment-50: #fefdfb;
--parchment-100: #fdf9f3;
--parchment-200: #f5efe6;
```

#### Terminal Colors

```css
--terminal-bg: #0f1419;
--terminal-surface: #1a1f26;
--terminal-border: #2d333b;
--terminal-text: #e6edf3;
--terminal-muted: #7d8590;
--terminal-accent: #14b8a6;
```

#### Archetype Colors

```css
--archetype-fire: #ef4444;
--archetype-water: #3b82f6;
--archetype-lightning: #eab308;
--archetype-psychic: #a855f7;
--archetype-fighting: #f97316;
--archetype-darkness: #6366f1;
--archetype-metal: #6b7280;
--archetype-grass: #22c55e;
--archetype-dragon: #8b5cf6;
--archetype-colorless: #a1a1aa;
--archetype-fairy: #ec4899;
```

#### Tier Colors

```css
--tier-s: #fbbf24; /* Gold */
--tier-a: #14b8a6; /* Teal */
--tier-b: #3b82f6; /* Blue */
--tier-c: #6b7280; /* Gray */
--tier-rogue: #8b5cf6; /* Purple */
```

#### Signal Colors

```css
--signal-up: #22c55e;
--signal-down: #ef4444;
--signal-stable: #6b7280;
--signal-jp: #f43f5e; /* JP divergence */
```

### 2.3 Typography

#### Font Families

```css
--font-display: "Playfair Display", Georgia, serif;
--font-body: "DM Sans", system-ui, sans-serif;
--font-mono: "JetBrains Mono", "Fira Code", monospace;
```

#### Type Scale

| Name    | Size | Line Height | Weight | Font      |
| ------- | ---- | ----------- | ------ | --------- |
| display | 48px | 56px        | 700    | Playfair  |
| h1      | 36px | 44px        | 600    | Playfair  |
| h2      | 24px | 32px        | 600    | DM Sans   |
| h3      | 18px | 28px        | 500    | DM Sans   |
| body    | 16px | 24px        | 400    | DM Sans   |
| small   | 14px | 20px        | 400    | DM Sans   |
| mono    | 14px | 20px        | 400    | JetBrains |
| mono-sm | 12px | 16px        | 400    | JetBrains |

### 2.4 Components

#### Base Components (Phase 6)

| Component     | Description                 |
| ------------- | --------------------------- |
| PillToggle    | Filter bar toggle group     |
| SectionLabel  | Mono label + icon + divider |
| TierBadge     | S/A/B/C/Rogue color badge   |
| TrendArrow    | Up/down/stable indicator    |
| JPSignalBadge | Red JP divergence badge     |
| StatBlock     | Large mono number + label   |
| PanelOverlay  | Dark overlay for slide-outs |

---

## 3. Navigation

### 3.1 Desktop Top Bar

```
[Flask Logo] [Meta] [From Japan] [Tournaments] [Lab Notes]     [Investigate] [User]
```

- Fixed at top, 64px height
- White background with shadow on scroll
- Active link: teal underline
- Investigate: teal CTA button

### 3.2 Mobile Bottom Tabs

```
[Home] [Meta] [JP] [Events] [More]
```

- Fixed at bottom, 56px height
- Active tab: teal icon + label
- More: opens drawer with additional links
- Safe area padding for iOS

---

## 4. Pages

### 4.1 Home Page

**URL:** `/`

**Sections (in order):**

1. **Hero Section**
   - Headline: "Data-Driven Deck Building" (Playfair)
   - Subheadline: Value proposition
   - Card fan: 3-5 featured cards with CSS transforms
   - Stats bar: "47 tournaments analyzed this week"
   - CTA: "Explore the Meta" → /meta

2. **JP Alert Banner** (conditional)
   - Shows when significant JP divergence detected
   - Red/rose background, dismissible
   - Links to /meta/japan
   - Dismisses for 24h (localStorage)

3. **Meta Snapshot**
   - Top 5 archetypes with signature cards
   - Meta share %, trend arrows
   - "Build It" commerce links
   - Horizontal scroll on mobile

4. **Evolution Preview**
   - Featured archetype journey
   - Mini line chart of meta share
   - 2-3 adaptation steps with dates
   - "Read the full story →" (Phase 2)

5. **Content Grid** (3 columns)
   - Lab Notes: Latest 3 articles
   - Recent Tournaments: Last 5 events
   - Upcoming Events: Next 3 major events

6. **JP Preview**
   - Side-by-side JP vs EN top 3
   - JP Signal badges for divergent decks
   - Prediction callout

7. **Why TrainerLab**
   - 3 value props with icons
   - Data-Driven, Japan Insights, All-in-One

8. **Research Pass Waitlist**
   - Email capture form
   - Teal background section
   - Premium features teaser

9. **Trainer's Toolkit**
   - Links to community resources
   - Limitless, PTCGO, PokemonCard.io, Reddit

### 4.2 Meta Dashboard

**URL:** `/meta`

**Sections:**

1. **Sticky Filter Bar**
   - Format: Standard | Expanded
   - Region: Global | NA | EU | JP | LATAM | APAC
   - Period: Week | Month | Season
   - Dark slate background (#1e293b)

2. **Meta Health Indicators** (4 cards)
   - Diversity Index (0-100)
   - Top Deck Share (%)
   - Biggest Mover (+/- %)
   - JP Signal (overall divergence)

3. **Tier List**
   - Grouped by tier (S/A/B/C/Rogue)
   - Each row: Signature card, Name, Share %, Trend, JP badge
   - Click row → opens Archetype Panel
   - Keyboard navigation (arrow keys)

4. **Build It Banner**
   - Context-aware: "Build [Selected Archetype]" or "Build the top deck"
   - DoubleHolo (primary) + TCGPlayer (secondary) buttons

5. **Archetype Panel** (slide-out, 480px)
   - Terminal dark theme
   - Sections:
     1. Header: Name, card, share, tier badge
     2. Trend Chart: Line chart over time
     3. Key Cards: Top 8 with inclusion rates
     4. Build Variants: 2-3 options with differences
     5. Matchup Spread: vs top 5 opponents
     6. Recent Results: Last 5 placements
     7. Commerce CTA: Build buttons

### 4.3 From Japan

**URL:** `/meta/japan`

**Sections:**

1. **Hero**
   - "From Japan" title
   - BO1 format context explanation

2. **Meta Comparison**
   - Two columns: Japan | International
   - Top 10 archetypes each
   - JP Signal badges for differences

3. **Prediction Tracker**
   - Historical predictions with outcomes
   - Status: Correct (green) | Incorrect (red) | Pending (gray)
   - Credibility building

4. **Latest Results**
   - Last 5-10 JP tournaments
   - Expandable with top 8 archetypes
   - Links to Limitless

5. **Meta History Timeline**
   - Horizontal timeline
   - JP → EN flow visualization
   - 2-3 month typical lag

6. **Upcoming Cards**
   - JP-exclusive cards
   - Translated names/effects
   - Impact rating (High/Medium/Low)

### 4.4 Tournaments

**URL:** `/tournaments`

**Sections:**

1. **Season Overview Chart**
   - Stacked area chart
   - Meta share over time
   - Archetype colors

2. **Tournament Browser**
   - Filterable table
   - Columns: Date, Name, Region, Format, Tier, Players, Winner
   - Filters: Date range, Format, Region, Tier
   - Sortable, paginated

**Detail Page:** `/tournaments/[id]`

- Tournament header with metadata
- Meta breakdown pie chart
- Top 8 decklists (expandable)
- External link to Limitless

### 4.5 Lab Notes

**URL:** `/lab-notes`

**Content Types:**

- Weekly Report
- JP Dispatch
- Deck Spotlight
- Format Analysis

**List Page:**

- Type filter pills
- Card grid of articles
- Title, excerpt, date, type badge

**Article Page:** `/lab-notes/[slug]`

- Playfair headline
- Date, author, type badge
- Markdown content
- Related articles

**RSS Feed:** `/feed.xml`

### 4.6 Cards & Decks (Existing)

Retain existing functionality:

- `/cards` - Card search
- `/cards/[id]` - Card detail
- `/decks` - User's decks
- `/decks/new` - Deck builder
- `/decks/[id]` - Deck view/edit

---

## 5. Commerce Integration

### 5.1 Partners

| Partner    | Priority  | Use Case            |
| ---------- | --------- | ------------------- |
| DoubleHolo | Primary   | Singles marketplace |
| TCGPlayer  | Secondary | Price comparison    |

### 5.2 Affiliate Links

```typescript
function generateAffiliateLink(
  partner: "doubleholo" | "tcgplayer",
  context: { archetype?: string; page: string },
): string {
  const params = new URLSearchParams({
    utm_source: "trainerlab",
    utm_medium: "referral",
    utm_campaign: context.page,
    utm_content: context.archetype || "general",
  });
  // Partner-specific URL construction
}
```

### 5.3 Price Estimates

MVP: Hardcoded average prices per archetype
Phase 2: API integration for live prices

### 5.4 Analytics

Track events:

- `commerce_link_click`: partner, archetype, page, estimated_value

---

## 6. JP Signal System

### 6.1 Calculation

```python
def calculate_jp_signal(jp_share: float, en_share: float, threshold: float = 0.05):
    diff = jp_share - en_share
    if abs(diff) < threshold:
        return {"has_signal": False}
    return {
        "has_signal": True,
        "direction": "rising" if diff > 0 else "falling",
        "difference": diff,
        "jp_share": jp_share,
        "en_share": en_share
    }
```

### 6.2 Display Rules

- Badge only appears when `|diff| > threshold` (default 5%)
- Rising (JP > EN): Deck is bigger in Japan, may rise in EN
- Falling (JP < EN): Deck is smaller in Japan, may decline in EN

### 6.3 Tier Assignment

| Tier  | Meta Share |
| ----- | ---------- |
| S     | > 15%      |
| A     | 8-15%      |
| B     | 3-8%       |
| C     | 1-3%       |
| Rogue | < 1%       |

---

## 7. Data Pipeline

### 7.1 Scrapers

**Limitless EN Scraper:**

- Source: `https://limitlesstcg.com/tournaments`
- Daily at 6am UTC
- Extracts tournaments, placements, decklists
- Stores in PostgreSQL

**Limitless JP Scraper:**

- Source: `https://limitlesstcg.com/tournaments/jp`
- Daily at 7am UTC
- Same data, marks `best_of=1`
- Handles Japanese text

#### 7.1.1 JP Tournament Data Sources

| #   | Source                | URL                                       | Status                 |
| --- | --------------------- | ----------------------------------------- | ---------------------- |
| 1   | Limitless TCG JP      | `https://limitlesstcg.com/tournaments/jp` | Active (primary)       |
| 2   | Pokecabook            | `https://pokecabook.com`                  | Active (supplementary) |
| 3   | Pokekameshi           | `https://pokekameshi.com`                 | Active (supplementary) |
| 4   | Official Players Club | `https://players.pokemon-card.com`        | Planned                |

### 7.2 Archetype Detection

```python
SIGNATURE_CARDS = {
    "sv4-125": "Charizard ex",
    "sv1-208": "Lugia VSTAR",
    "sv2-86": "Gardevoir ex",
    # ... more mappings
}

def detect_archetype(decklist: list[dict]) -> str:
    for card in decklist:
        if card["id"] in SIGNATURE_CARDS:
            return SIGNATURE_CARDS[card["id"]]
    return "Rogue"
```

### 7.3 Meta Snapshot Computation

- Daily at 8am UTC (after scrapers)
- Computes archetype shares by region/format
- Calculates JP Signals
- Assigns tiers
- Computes diversity index: `1 - sum(share^2)` normalized

### 7.4 Scheduler

Cloud Scheduler jobs:
| Job | Schedule | Target |
|-----|----------|--------|
| discover-en | `0 6 * * *` | POST /api/v1/pipeline/discover-en |
| discover-jp | `0 7 * * *` | POST /api/v1/pipeline/discover-jp |
| compute-meta | `0 8 * * *` | POST /api/v1/pipeline/compute-meta |
| compute-evolution | `0 9 * * *` | POST /api/v1/pipeline/compute-evolution |
| sync-cards | `0 3 * * 0` | POST /api/v1/pipeline/sync-cards |
| sync-jp-cards | `30 3 * * 0` | POST /api/v1/pipeline/sync-jp-cards |
| sync-card-mappings | `0 4 * * 0` | POST /api/v1/pipeline/sync-card-mappings |
| sync-events | `0 11 * * 1` | POST /api/v1/pipeline/sync-events |
| translate-pokecabook | `0 9 * * 1,3,5` | POST /api/v1/pipeline/translate-pokecabook |
| sync-jp-adoption | `0 10 * * 2,4,6` | POST /api/v1/pipeline/sync-jp-adoption |
| translate-tier-lists | `0 10 * * 0` | POST /api/v1/pipeline/translate-tier-lists |
| monitor-card-reveals | `0 */6 * * *` | POST /api/v1/pipeline/monitor-card-reveals |
| reprocess-archetypes | `0 5 1 * *` | POST /api/v1/pipeline/reprocess-archetypes |
| cleanup-exports | `0 3 * * 0` | POST /api/v1/pipeline/cleanup-exports |

---

## 8. API Endpoints

### 8.1 Existing Endpoints

```
GET  /api/v1/cards                    # Search cards
GET  /api/v1/cards/{id}               # Get card
GET  /api/v1/sets                     # List sets
GET  /api/v1/sets/{id}                # Get set

GET  /api/v1/decks                    # User's decks
POST /api/v1/decks                    # Create deck
GET  /api/v1/decks/{id}               # Get deck
PUT  /api/v1/decks/{id}               # Update deck
DELETE /api/v1/decks/{id}             # Delete deck

GET  /api/v1/meta/current             # Current meta
GET  /api/v1/meta/history             # Meta over time
GET  /api/v1/meta/archetypes          # Archetype list
GET  /api/v1/meta/tournaments         # Tournament results

GET  /api/v1/health                   # Health check
```

### 8.2 New Endpoints (v3.0)

```
# Waitlist
POST /api/v1/waitlist                 # Add email to waitlist
  Body: { "email": "...", "source": "home_page" }

# Matchups
GET  /api/v1/matchups                 # Matchup data
  ?archetype=Charizard%20ex
  ?format=standard
  ?limit=10

# Tournaments (enhanced)
GET  /api/v1/tournaments              # Filtered list
  ?format=standard
  ?region=NA,EU
  ?tier=regionals
  ?date_from=2024-01-01
  ?date_to=2024-12-31
  ?page=1
  ?limit=20

GET  /api/v1/tournaments/{id}         # Tournament detail

# Lab Notes
GET  /api/v1/lab-notes                # List notes
  ?type=weekly-report
  ?page=1
  ?limit=10

GET  /api/v1/lab-notes/{slug}         # Get note by slug

# Pipeline (admin)
POST /api/v1/pipeline/discover-en     # Discover + enqueue EN tournaments
POST /api/v1/pipeline/discover-jp     # Discover + enqueue JP tournaments
POST /api/v1/pipeline/process-tournament # Process single tournament (Cloud Tasks)
POST /api/v1/pipeline/compute-meta    # Compute snapshots
POST /api/v1/pipeline/compute-evolution # Compute evolution intelligence
POST /api/v1/pipeline/compute-jp-intelligence # Compute JP intelligence
POST /api/v1/pipeline/sync-cards      # Sync cards from TCGdex
POST /api/v1/pipeline/sync-jp-cards   # Sync Japanese cards from TCGdex
POST /api/v1/pipeline/sync-card-mappings # Sync JP↔EN card ID mappings
POST /api/v1/pipeline/sync-events     # Sync upcoming events
POST /api/v1/pipeline/translate-pokecabook # Translate JP articles
POST /api/v1/pipeline/sync-jp-adoption # Sync JP adoption rates
POST /api/v1/pipeline/translate-tier-lists # Translate JP tier lists
POST /api/v1/pipeline/monitor-card-reveals # Monitor new JP card reveals
POST /api/v1/pipeline/reprocess-archetypes # Reprocess placement archetypes
POST /api/v1/pipeline/rescrape-jp     # Rescrape JP tournaments
POST /api/v1/pipeline/cleanup-exports # Cleanup expired export files
```

### 8.3 Freshness Semantics (Cadence-Based)

Core intelligence responses include a `freshness` object with:

- `status`: `fresh | stale | partial | no_data`
- `cadence_profile`: `jp_daily_cadence | grassroots_daily_cadence | tpci_event_cadence | default_cadence`
- `snapshot_date`, `sample_size`, `staleness_days`, optional `source_coverage`, optional `message`

Cadence rules:

- `tpci_event_cadence` evaluates against major-event timing in UTC.
  - Target operational window: updated by Tuesday UTC after major-event weekend.
  - Completeness thresholds: `partial >= 8`, `fresh >= 64` placements.
- `jp_daily_cadence` and `grassroots_daily_cadence` use tighter daily staleness windows.
- `default_cadence` is a safety fallback when context-specific cadence is unavailable.

---

## 9. Database Schema

### 9.1 New Tables (v3.0)

```sql
-- Waitlist for Research Pass
CREATE TABLE waitlist_emails (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    source TEXT DEFAULT 'home_page',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_waitlist_email ON waitlist_emails (email);

-- Lab Notes content
CREATE TABLE lab_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    excerpt TEXT,
    content TEXT NOT NULL,  -- Markdown
    type TEXT NOT NULL,     -- 'weekly-report', 'jp-dispatch', etc.
    tags TEXT[],
    author TEXT,
    published_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_lab_notes_slug ON lab_notes (slug);
CREATE INDEX idx_lab_notes_type ON lab_notes (type);
CREATE INDEX idx_lab_notes_published ON lab_notes (published_at DESC);

-- Archetype metadata (for colors, names, etc.)
CREATE TABLE archetypes (
    id TEXT PRIMARY KEY,            -- e.g., "charizard-ex"
    name TEXT NOT NULL,             -- "Charizard ex"
    signature_cards TEXT[],         -- Card IDs that identify this archetype
    color TEXT,                     -- CSS color value
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Matchup data (future, placeholder for now)
CREATE TABLE matchups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    archetype_a TEXT NOT NULL,
    archetype_b TEXT NOT NULL,
    win_rate DECIMAL(5,4),          -- 0.0000 to 1.0000
    sample_size INTEGER,
    format TEXT NOT NULL,
    computed_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(archetype_a, archetype_b, format)
);
```

### 9.2 Schema Updates

Add to `meta_snapshots`:

```sql
ALTER TABLE meta_snapshots
ADD COLUMN diversity_index DECIMAL(5,4),
ADD COLUMN tier_assignments JSONB;  -- {"Charizard ex": "S", ...}
```

Add to `tournaments`:

```sql
ALTER TABLE tournaments
ADD COLUMN tier TEXT;  -- 'regionals', 'internationals', 'special'
```

---

## 10. Implementation Phases

### Phase 5: Polish & Auth (In Progress)

25 open issues - NextAuth.js + Google OAuth, loading states, mobile responsive, tests

### Phase 6: Design System

9 issues (#204-212)

- Color tokens, typography, terminal theme
- PillToggle, SectionLabel, TierBadge, TrendArrow, JPSignalBadge, StatBlock

### Phase 7: Navigation

4 issues (#213-216)

- Desktop top bar, mobile bottom tabs
- Scroll-to-top, layout updates

### Phase 8: Home Page

10 issues (#217-226)

- Hero, JP Alert, Meta Snapshot, Evolution Preview
- Content Grid, JP Preview, Why TrainerLab
- Waitlist, Trainer's Toolkit

### Phase 9: Meta Dashboard

10 issues (#227-236)

- Filter bar, health indicators
- Tier list redesign, archetype panel
- Matchup spread, commerce banner

### Phase 10: From Japan

6 issues (#237-242)

- Page layout, meta comparison
- Prediction tracker, latest results
- Meta timeline, upcoming cards

### Phase 11: Tournaments

5 issues (#243-247)

- Page layout, season charts
- Browser table, detail page

### Phase 12: Lab Notes

6 issues (#248-253)

- List page, article page
- API endpoints, database model
- RSS feed

### Phase 13: Data Pipeline

5 issues (#254-258)

- Limitless EN/JP scrapers
- Archetype detection
- Meta computation, scheduler

### Phase 14: Commerce

4 issues (#259-262)

- BuildDeckCTA component
- Affiliate links, price estimates
- Click tracking

---

## 11. Sprint Plan

### Sprint 1: Foundation

- Design tokens (colors, typography, terminal)
- Base components
- Navigation (top bar, mobile tabs)

### Sprint 2: Home + Commerce

- Home page redesign (all sections)
- Commerce components
- Waitlist functionality

### Sprint 3: Meta Dashboard

- Filter bar + health indicators
- Tier list with JP badges
- Archetype panel (terminal)
- Matchup spread

### Sprint 4: JP + Tournaments

- From Japan page
- Tournament archive
- Scrapers (parallel work)

### Sprint 5: Lab Notes + Polish

- Lab Notes system
- Mobile responsive polish
- Tests, bug fixes

---

## 12. Success Criteria

### MVP (v3.0)

- [ ] New design system implemented
- [ ] Home page drives engagement
- [ ] Meta dashboard shows JP Signals
- [ ] Archetype panel provides deep analysis
- [ ] From Japan page delivers unique value
- [ ] Tournament archive is browsable
- [ ] Commerce links generate clicks
- [ ] Data pipeline runs automatically

### Quality Gates

- [ ] Lighthouse score > 90 (performance, accessibility)
- [ ] Core Web Vitals pass
- [ ] Test coverage > 70%
- [ ] No P0 bugs in production

---

## 13. Open Questions

1. **DoubleHolo API**: What's the affiliate link format? Need partner docs.
2. **TCGPlayer affiliate**: Need affiliate program details.
3. **AI translation**: Claude API for JP→EN content in Phase 2.
4. **Card images CDN**: Continue using pokemontcg.io directly for MVP. Cloud Storage caching in Phase 2.
5. **Archetype accent colors**: Unknown archetypes get random color from extended palette.

---

_Last updated: February 2026_
_SPEC v3.0 for Claude Code implementation_
