# Technical Specification Outline

> This document provides a structured specification outline for Claude Code implementation.
> Each section can be expanded into detailed specs as development progresses.

---

## Project Overview

**Project Name:** Pokemon TCG Competitive Intelligence Platform (working title)
**Type:** Web application
**Primary Stack:** Next.js (frontend), FastAPI (backend), PostgreSQL (database)
**Deployment:** Vercel (frontend), Railway (backend), Supabase (database + auth)

---

## Repository Structure

```
pokemon-tcg-platform/
├── apps/
│   ├── web/                    # Next.js frontend
│   │   ├── app/                # App router pages
│   │   ├── components/         # React components
│   │   ├── lib/                # Utilities, API clients
│   │   └── styles/             # Global styles
│   └── api/                    # FastAPI backend
│       ├── routers/            # API route handlers
│       ├── services/           # Business logic
│       ├── models/             # Pydantic models
│       ├── db/                 # Database models, migrations
│       └── tasks/              # Background tasks (data sync)
├── packages/
│   └── shared/                 # Shared types, constants
├── docs/                       # Documentation
│   ├── PLATFORM_EXPLORATION.md
│   ├── CREATOR_PITCH.md
│   └── specs/                  # Detailed feature specs
├── scripts/                    # Dev and deployment scripts
└── data/                       # Seed data, fixtures
```

---

## MVP Feature Specs

### Feature 1: Meta Dashboard

**Spec ID:** `FEAT-001`
**Priority:** P0
**Status:** Not started

#### Overview

Display current competitive metagame data with visualizations showing archetype popularity, trends over time, and regional variations.

#### User Stories

- As a player, I want to see current meta share percentages
- As a player, I want to see meta trends over time
- As a player, I want to filter by region (NA/EU/APAC/LATAM)
- As a player, I want to see recent tournament results

#### Data Requirements

- Tournament results from LimitlessTCG
- Archetype classifications
- Regional tournament mapping
- Historical data (at least 3 months)

#### API Endpoints

```
GET /api/meta/current
  Query: format (standard|expanded), region? (na|eu|apac|latam)
  Response: { archetypes: [{ name, share, count, trend }] }

GET /api/meta/history
  Query: format, startDate, endDate, archetype?
  Response: { dataPoints: [{ date, archetypes: [{ name, share }] }] }

GET /api/tournaments/recent
  Query: format, region?, limit (default 10)
  Response: { tournaments: [{ id, name, date, region, topCut: [...] }] }

GET /api/tournaments/{id}
  Response: { tournament, standings: [...] }
```

#### UI Components

- `MetaShareChart` - Pie or bar chart of current meta
- `MetaTrendChart` - Line chart of meta over time
- `RegionSelector` - Filter by region
- `TournamentList` - Recent tournaments with results
- `TournamentDetail` - Full results for a tournament

#### Acceptance Criteria

- [ ] Meta share displays correctly for current format
- [ ] Historical data shows at least 3 months of trends
- [ ] Region filter works correctly
- [ ] Page loads in <3 seconds
- [ ] Mobile responsive

---

### Feature 2: Smart Deck Builder

**Spec ID:** `FEAT-002`
**Priority:** P0
**Status:** Not started

#### Overview

Deck building tool with card database, archetype templates, inclusion rate data, and consistency metrics.

#### User Stories

- As a player, I want to search for cards by name or effect
- As a player, I want to start from an archetype template
- As a player, I want to see how often cards appear in successful lists
- As a player, I want to see consistency metrics for my deck
- As a player, I want to save decks to my account

#### Data Requirements

- Complete card database (TCGdex - self-hosted, multi-language)
- Archetype templates with core cards
- Card inclusion rates (derived from LimitlessTCG data)
- Format legality data

#### API Endpoints

```
GET /api/cards/search
  Query: q (text query), types?, supertype?, set?, format?
  Response: { cards: [...], total, page }

GET /api/cards/semantic-search
  Query: q (natural language)
  Response: { cards: [...], relevanceScores: [...] }

GET /api/cards/{id}
  Response: { card details }

GET /api/archetypes
  Query: format
  Response: { archetypes: [{ id, name, coreCards, description }] }

GET /api/archetypes/{id}/template
  Response: { decklist, flexSlots, techOptions }

GET /api/archetypes/{id}/inclusion-rates
  Response: { cards: [{ card, rate, avgCount, range }] }

POST /api/decks
  Body: { name, cards: [{ cardId, count }], format, notes? }
  Response: { deck }

GET /api/decks/analyze
  Body: { cards: [...] }
  Response: { consistency: {...}, archetype?, suggestions: [...] }
```

#### UI Components

- `CardSearch` - Search input with filters
- `CardGrid` - Display search results
- `CardDetail` - Modal with full card info
- `DeckEditor` - Main deck building interface
- `DeckList` - Display current deck contents
- `ArchetypeSelector` - Choose starting template
- `InclusionRateDisplay` - Show card popularity
- `ConsistencyMetrics` - Supporter count, energy curve, etc.
- `DeckDiff` - Compare to reference lists

#### Acceptance Criteria

- [ ] Card search returns results in <500ms
- [ ] Natural language search finds relevant cards
- [ ] Archetype templates load correctly
- [ ] Inclusion rates display for relevant archetypes
- [ ] Consistency metrics calculate correctly
- [ ] Decks save and load for authenticated users
- [ ] Mobile responsive

---

### Feature 3: Natural Language Card Search

**Spec ID:** `FEAT-003`
**Priority:** P0
**Status:** Not started

#### Overview

Enable users to search for cards by describing effects in natural language rather than exact text matches.

#### User Stories

- As a player, I want to find "cards that draw cards"
- As a player, I want to find "Pokemon that damage the bench"
- As a player, I want to find "items that search for basic Pokemon"

#### Technical Approach

1. Embed all card text using text embedding model
2. Store embeddings in vector database (pgvector)
3. At query time, embed the search query
4. Return cards with highest cosine similarity

#### Data Requirements

- All card text, attacks, abilities embedded
- Vector storage with efficient similarity search

#### API Endpoints

```
GET /api/cards/semantic-search
  Query: q (natural language query), limit (default 20), format?
  Response: {
    cards: [...],
    relevanceScores: [...],
    interpretedQuery: string?
  }
```

#### Implementation Notes

- Consider caching common queries
- Embed card text including: name, abilities, attacks, rules
- May need to experiment with embedding model choice
- Rate limit for free tier users

#### Acceptance Criteria

- [ ] "Cards that draw cards" returns Iono, Professor's Research, etc.
- [ ] "Bench damage" returns spread attackers
- [ ] Response time <1 second
- [ ] Results feel relevant to query intent

---

### Feature 4: User Authentication

**Spec ID:** `FEAT-004`
**Priority:** P0
**Status:** Not started

#### Overview

Basic user authentication for saving decks and preferences.

#### User Stories

- As a user, I want to create an account
- As a user, I want to sign in with email/password or OAuth
- As a user, I want my decks saved to my account

#### Technical Approach

Use Supabase Auth for simplicity:

- Email/password authentication
- Google OAuth (optional for MVP)
- Session management via Supabase client

#### API Endpoints

Handled by Supabase client library, but backend needs:

```
GET /api/users/me
  Auth: Required
  Response: { user profile }

PATCH /api/users/me
  Auth: Required
  Body: { username?, preferences? }
  Response: { updated user }
```

#### Acceptance Criteria

- [ ] Users can sign up with email/password
- [ ] Users can sign in and out
- [ ] Sessions persist appropriately
- [ ] Protected routes require authentication
- [ ] User can update profile

---

## Data Pipeline Specs

### Pipeline 1: Card Data Sync

**Spec ID:** `PIPE-001`
**Frequency:** On new set release + daily check

#### Overview

Sync card database from TCGdex API (self-hosted Docker instance).

#### Process

1. Check for new/updated cards since last sync
2. Fetch card data from API
3. Transform to internal schema
4. Generate embeddings for new cards
5. Upsert to database
6. Log sync results

#### Error Handling

- Retry failed API calls with exponential backoff
- Alert on repeated failures
- Continue sync for other cards if one fails

---

### Pipeline 2: Tournament Data Sync

**Spec ID:** `PIPE-002`
**Frequency:** Daily

#### Overview

Sync tournament results from LimitlessTCG, including both international and Japanese tournaments.

#### Process

1. Check for new tournaments since last sync
2. Fetch tournament data (approach TBD - API or scrape)
3. Parse and classify archetypes
4. Tag with region and format (BO1 vs BO3)
5. Calculate meta share statistics (separate for JP BO1 vs International BO3)
6. Upsert to database
7. Invalidate relevant caches

#### Japanese Data Handling

- Japanese tournaments tagged with `region: "JP"` and `bestOf: 1`
- Card name mapping: Japanese → International (for archetype consistency)
- Set legality tracking: Some cards legal in JP but not yet international
- Meta snapshots separated by format type (BO1 vs BO3)

#### Considerations

- Need to respect LimitlessTCG rate limits
- May need partnership discussion
- Archetype classification may need manual curation initially
- Japanese Champions Leagues are massive (5K+ players)—affects how we weight data

---

## Database Schema (Draft)

```sql
-- Cards
CREATE TABLE cards (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  japanese_name TEXT,  -- For Japanese card reference
  supertype TEXT NOT NULL,
  subtypes TEXT[],
  hp INTEGER,
  types TEXT[],
  attacks JSONB,
  abilities JSONB,
  weaknesses JSONB,
  resistances JSONB,
  retreat_cost INTEGER,
  rules TEXT[],
  set_id TEXT NOT NULL,
  set_name TEXT NOT NULL,
  rarity TEXT,
  image_url TEXT,
  text_embedding VECTOR(1536),
  japanese_release_date DATE,  -- When legal in Japan
  international_release_date DATE,  -- When legal internationally
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Archetypes
CREATE TABLE archetypes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL UNIQUE,
  format TEXT NOT NULL,
  core_cards TEXT[],
  description TEXT,
  first_seen DATE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tournaments
CREATE TABLE tournaments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  external_id TEXT UNIQUE,
  name TEXT NOT NULL,
  date DATE NOT NULL,
  location TEXT,
  region TEXT NOT NULL,  -- "NA" | "EU" | "APAC" | "LATAM" | "JP"
  format TEXT NOT NULL,
  tier TEXT,
  best_of INTEGER DEFAULT 3,  -- 1 for Japanese, 3 for International
  attendance INTEGER,
  source TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tournament Results
CREATE TABLE tournament_results (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tournament_id UUID REFERENCES tournaments(id),
  player_name TEXT,
  placement INTEGER,
  record_wins INTEGER,
  record_losses INTEGER,
  record_ties INTEGER,
  archetype_id UUID REFERENCES archetypes(id),
  decklist JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Users
CREATE TABLE users (
  id UUID PRIMARY KEY REFERENCES auth.users(id),
  username TEXT UNIQUE,
  tier TEXT DEFAULT 'free',
  preferences JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- User Decklists
CREATE TABLE user_decklists (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  name TEXT NOT NULL,
  format TEXT NOT NULL,
  cards JSONB NOT NULL,
  archetype_id UUID REFERENCES archetypes(id),
  notes TEXT,
  is_public BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Meta Snapshots (pre-calculated)
CREATE TABLE meta_snapshots (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  date DATE NOT NULL,
  format TEXT NOT NULL,
  region TEXT,  -- NULL for "all regions"
  best_of INTEGER,  -- 1 or 3, NULL for combined
  data JSONB NOT NULL,
  is_format_preview BOOLEAN DEFAULT FALSE,  -- True for JP data before intl release
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(date, format, region, best_of)
);

-- Card Name Mappings (Japanese to International)
CREATE TABLE card_name_mappings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  japanese_name TEXT NOT NULL,
  international_name TEXT,  -- NULL if not yet released internationally
  card_id TEXT REFERENCES cards(id),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(japanese_name)
);

-- Indexes
CREATE INDEX idx_cards_name ON cards(name);
CREATE INDEX idx_cards_japanese_name ON cards(japanese_name);
CREATE INDEX idx_cards_supertype ON cards(supertype);
CREATE INDEX idx_cards_types ON cards USING GIN(types);
CREATE INDEX idx_cards_embedding ON cards USING ivfflat(text_embedding vector_cosine_ops);
CREATE INDEX idx_cards_release_dates ON cards(japanese_release_date, international_release_date);
CREATE INDEX idx_tournaments_date ON tournaments(date);
CREATE INDEX idx_tournaments_region ON tournaments(region);
CREATE INDEX idx_tournaments_best_of ON tournaments(best_of);
CREATE INDEX idx_tournament_results_archetype ON tournament_results(archetype_id);
CREATE INDEX idx_user_decklists_user ON user_decklists(user_id);
CREATE INDEX idx_meta_snapshots_lookup ON meta_snapshots(date, format, region, best_of);
```

---

## Environment Variables

```
# Database
DATABASE_URL=postgresql://...
DIRECT_URL=postgresql://... (for migrations)

# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://...
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...

# External APIs
POKEMON_TCG_API_KEY=... (if needed)
CLAUDE_API_KEY=...

# App Config
NEXT_PUBLIC_APP_URL=https://...
NODE_ENV=development|production
```

---

## Development Milestones

### Milestone 1: Foundation (Week 1-2)

- [ ] Repository setup with monorepo structure
- [ ] Database schema and migrations
- [ ] Basic Next.js app with Tailwind + shadcn
- [ ] FastAPI skeleton with health check
- [ ] Supabase auth integration
- [ ] Card data sync pipeline (TCGdex self-hosted)

### Milestone 2: Core Features (Week 3-4)

- [ ] Card search (keyword)
- [ ] Card database UI
- [ ] Deck builder basic functionality
- [ ] Save/load decks

### Milestone 3: Meta Dashboard (Week 5-6)

- [ ] Tournament data ingestion (manual or automated)
- [ ] Meta share calculations
- [ ] Dashboard UI with charts
- [ ] Regional filtering

### Milestone 4: Smart Features (Week 7-8)

- [ ] Card embeddings and semantic search
- [ ] Inclusion rate calculations
- [ ] Consistency metrics
- [ ] Archetype templates

### Milestone 5: Polish & Launch (Week 9-10)

- [ ] UI polish and mobile responsiveness
- [ ] Error handling and edge cases
- [ ] Performance optimization
- [ ] Beta testing with community
- [ ] Bug fixes from feedback

---

## Open Technical Questions

1. **Embedding model:** Claude API vs. open-source (cost/quality)
2. **LimitlessTCG data access:** API, partnership, or scraping?
3. **Hosting budget:** Validate costs at expected scale
4. **Rate limiting:** What limits for free tier?
5. **Caching strategy:** Redis vs. in-memory vs. CDN?

---

## References

- [Next.js App Router Docs](https://nextjs.org/docs/app)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Supabase Docs](https://supabase.com/docs)
- [TCGdex API](https://tcgdex.dev/) - Primary card data (self-hosted)
- [TCGdex GitHub](https://github.com/tcgdex/cards-database)
- [pokemontcg.io API](https://docs.pokemontcg.io/) - Fallback reference
- [pgvector](https://github.com/pgvector/pgvector)
- [shadcn/ui](https://ui.shadcn.com/)
