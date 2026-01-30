# TrainerLab - Implementation Spec

> Handoff document for Claude Code to build the initial MVP

**Domain:** trainerlab.io

---

## 1. Project Overview

### 1.1 What We're Building

**TrainerLab** — A competitive intelligence platform for Pokemon TCG trainers, coaches, content creators, and families. We help users make data-driven decisions about deck building, format preparation, and the hobby overall.

**Key differentiator:** Japanese metagame integration providing 2-3 month format preview, with proper BO1/BO3 context.

### 1.2 MVP Scope

**In scope for initial build:**

- Card database with search (keyword + semantic)
- Deck builder (create, save, load, export)
- Meta dashboard (archetype shares, trends)
- Japanese meta view (separate BO1 context)
- Basic user authentication

**Out of scope for MVP:**

- Card reveal ingestion pipeline
- Price tracking
- Social features
- Mobile app

### 1.3 Target User

Competitive Pokemon TCG players preparing for tournaments. Assume technical literacy but not developer skills.

---

## 2. Repository Structure

```
trainerlab/
├── README.md
├── docker-compose.yml           # Local dev (TCGdex, Postgres, Redis)
├── cloudbuild.yaml              # GCP Cloud Build CI/CD config
├── .env.example
├── .gitignore
│
├── apps/
│   ├── web/                     # Next.js frontend
│   │   ├── package.json
│   │   ├── next.config.js
│   │   ├── tailwind.config.js
│   │   ├── tsconfig.json
│   │   ├── .env.local.example
│   │   │
│   │   ├── src/
│   │   │   ├── app/             # App router
│   │   │   │   ├── layout.tsx
│   │   │   │   ├── page.tsx                    # Home/landing
│   │   │   │   ├── cards/
│   │   │   │   │   ├── page.tsx                # Card search
│   │   │   │   │   └── [id]/page.tsx           # Card detail
│   │   │   │   ├── decks/
│   │   │   │   │   ├── page.tsx                # My decks list
│   │   │   │   │   ├── new/page.tsx            # Deck builder
│   │   │   │   │   └── [id]/page.tsx           # Deck view/edit
│   │   │   │   ├── meta/
│   │   │   │   │   ├── page.tsx                # Meta dashboard
│   │   │   │   │   └── japan/page.tsx          # Japan-specific view
│   │   │   │   ├── api/                        # API routes (if needed)
│   │   │   │   └── auth/
│   │   │   │       └── [...nextauth]/route.ts
│   │   │   │
│   │   │   ├── components/
│   │   │   │   ├── ui/                         # shadcn/ui components
│   │   │   │   ├── cards/
│   │   │   │   │   ├── CardGrid.tsx
│   │   │   │   │   ├── CardImage.tsx
│   │   │   │   │   ├── CardSearch.tsx
│   │   │   │   │   └── CardDetail.tsx
│   │   │   │   ├── decks/
│   │   │   │   │   ├── DeckBuilder.tsx
│   │   │   │   │   ├── DeckList.tsx
│   │   │   │   │   ├── DeckStats.tsx
│   │   │   │   │   └── DeckExport.tsx
│   │   │   │   ├── meta/
│   │   │   │   │   ├── MetaChart.tsx
│   │   │   │   │   ├── ArchetypeCard.tsx
│   │   │   │   │   └── RegionFilter.tsx
│   │   │   │   └── layout/
│   │   │   │       ├── Header.tsx
│   │   │   │       ├── Sidebar.tsx
│   │   │   │       └── Footer.tsx
│   │   │   │
│   │   │   ├── lib/
│   │   │   │   ├── api.ts                      # API client
│   │   │   │   ├── utils.ts
│   │   │   │   └── constants.ts
│   │   │   │
│   │   │   └── types/
│   │   │       ├── card.ts
│   │   │       ├── deck.ts
│   │   │       └── meta.ts
│   │   │
│   │   └── public/
│   │       └── images/
│   │
│   └── api/                     # FastAPI backend
│       ├── pyproject.toml       # Using Poetry
│       ├── Dockerfile
│       ├── .env.example
│       │
│       └── src/
│           ├── main.py          # FastAPI app entry
│           ├── config.py        # Settings/env
│           │
│           ├── routers/
│           │   ├── __init__.py
│           │   ├── cards.py
│           │   ├── decks.py
│           │   ├── meta.py
│           │   └── health.py
│           │
│           ├── models/          # Pydantic models
│           │   ├── __init__.py
│           │   ├── card.py
│           │   ├── deck.py
│           │   └── meta.py
│           │
│           ├── db/
│           │   ├── __init__.py
│           │   ├── database.py  # Connection setup
│           │   ├── models.py    # SQLAlchemy models
│           │   └── migrations/  # Alembic
│           │
│           ├── services/
│           │   ├── __init__.py
│           │   ├── card_service.py
│           │   ├── deck_service.py
│           │   ├── meta_service.py
│           │   └── search_service.py
│           │
│           └── pipelines/
│               ├── __init__.py
│               ├── tcgdex_sync.py      # Card data sync
│               └── tournament_sync.py   # Tournament data (future)
│
├── packages/                    # Shared code (if needed)
│   └── shared-types/
│
├── scripts/
│   ├── setup-dev.sh             # Local dev environment setup
│   ├── seed-db.sh               # Seed database with test data
│   └── sync-cards.py            # Manual card sync trigger
│
├── terraform/                   # Infrastructure as Code (GCP)
│   ├── main.tf                  # All GCP resources
│   ├── variables.tf             # Variable definitions
│   ├── outputs.tf               # Output values
│   ├── README.md                # Terraform documentation
│   ├── .gitignore
│   ├── bootstrap/
│   │   └── main.tf              # State bucket setup (run first)
│   └── environments/
│       ├── dev.tfvars           # Development config
│       └── prod.tfvars          # Production config
│
└── docs/
    ├── SPEC.md                  # This file
    ├── API.md                   # API documentation
    └── DEPLOYMENT.md
```

---

## 3. Tech Stack

### 3.1 Frontend

| Technology     | Version | Purpose                         |
| -------------- | ------- | ------------------------------- |
| Next.js        | 14+     | React framework with App Router |
| TypeScript     | 5+      | Type safety                     |
| Tailwind CSS   | 3+      | Styling                         |
| shadcn/ui      | latest  | UI component library            |
| TanStack Query | 5+      | Data fetching/caching           |
| Zustand        | 4+      | Client state (deck builder)     |
| Recharts       | 2+      | Charts for meta dashboard       |

### 3.2 Backend

| Technology | Version | Purpose           |
| ---------- | ------- | ----------------- |
| Python     | 3.11+   | Runtime           |
| FastAPI    | 0.100+  | API framework     |
| SQLAlchemy | 2+      | ORM               |
| Alembic    | 1.12+   | Migrations        |
| Pydantic   | 2+      | Validation        |
| httpx      | 0.25+   | Async HTTP client |

### 3.3 Infrastructure (GCP)

| Technology    | GCP Service               | Purpose                  |
| ------------- | ------------------------- | ------------------------ |
| PostgreSQL 15 | Cloud SQL                 | Primary database         |
| pgvector      | Cloud SQL extension       | Vector similarity search |
| Redis         | Memorystore               | Caching                  |
| TCGdex        | Cloud Run (self-hosted)   | Card data source         |
| Auth          | Firebase Auth or Supabase | User authentication      |
| Secrets       | Secret Manager            | Environment variables    |
| CDN           | Cloud CDN                 | Static asset caching     |
| CI/CD         | Cloud Build               | Auto-deploy on push      |

### 3.4 Development

| Tool              | Purpose                      |
| ----------------- | ---------------------------- |
| Docker Compose    | Local dev environment        |
| pnpm              | Frontend package manager     |
| Poetry            | Python dependency management |
| ESLint + Prettier | Frontend linting             |
| Ruff              | Python linting               |

---

## 4. Database Schema

### 4.1 Core Tables

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Cards table
CREATE TABLE cards (
    id TEXT PRIMARY KEY,                    -- TCGdex ID (e.g., "swsh3-136")

    -- Names (multi-language)
    name_en TEXT NOT NULL,
    name_ja TEXT,

    -- Core attributes
    supertype TEXT NOT NULL,                -- "Pokemon", "Trainer", "Energy"
    subtypes TEXT[],                        -- ["Stage 2", "ex"]
    hp INTEGER,
    types TEXT[],                           -- ["Fire", "Water"]

    -- Set info
    set_id TEXT NOT NULL,
    set_name TEXT NOT NULL,
    number TEXT NOT NULL,                   -- Card number in set
    rarity TEXT,

    -- Game mechanics (stored as JSONB for flexibility)
    attacks JSONB,
    abilities JSONB,
    weaknesses JSONB,
    resistances JSONB,
    retreat_cost INTEGER,
    rules TEXT[],                           -- Rule box text

    -- Evolution
    evolves_from TEXT,
    evolves_to TEXT[],

    -- Images
    image_small TEXT,
    image_large TEXT,

    -- Legality
    legality_standard TEXT,                 -- "Legal", "Banned", "Not Legal"
    legality_expanded TEXT,
    regulation_mark TEXT,                   -- "G", "H", etc.

    -- Semantic search
    text_embedding vector(1536),            -- OpenAI ada-002 dimensions

    -- Metadata
    tcgdex_updated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_cards_name_en ON cards USING gin(to_tsvector('english', name_en));
CREATE INDEX idx_cards_name_ja ON cards (name_ja) WHERE name_ja IS NOT NULL;
CREATE INDEX idx_cards_set_id ON cards (set_id);
CREATE INDEX idx_cards_supertype ON cards (supertype);
CREATE INDEX idx_cards_types ON cards USING gin(types);
CREATE INDEX idx_cards_legality_standard ON cards (legality_standard);
CREATE INDEX idx_cards_embedding ON cards USING ivfflat (text_embedding vector_cosine_ops);

-- Sets table
CREATE TABLE sets (
    id TEXT PRIMARY KEY,                    -- TCGdex set ID
    name TEXT NOT NULL,
    series TEXT NOT NULL,                   -- "Sword & Shield", "Scarlet & Violet"

    total_cards INTEGER,
    release_date DATE,
    release_date_jp DATE,                   -- Japanese release (often earlier)

    -- Images
    logo_url TEXT,
    symbol_url TEXT,

    -- Legality
    legality_standard TEXT,
    legality_expanded TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Users table (basic, Supabase Auth handles most)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    display_name TEXT,

    -- Preferences (JSONB for flexibility)
    preferences JSONB DEFAULT '{}',

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Decks table
CREATE TABLE decks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,

    name TEXT NOT NULL,
    description TEXT,
    format TEXT NOT NULL DEFAULT 'standard',  -- "standard", "expanded"
    archetype TEXT,                            -- "Charizard ex", "Lugia VSTAR"

    -- Deck contents (JSONB array of {card_id, quantity})
    cards JSONB NOT NULL DEFAULT '[]',

    -- Computed stats (updated on save)
    pokemon_count INTEGER,
    trainer_count INTEGER,
    energy_count INTEGER,

    -- Sharing
    is_public BOOLEAN DEFAULT FALSE,
    share_code TEXT UNIQUE,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_decks_user_id ON decks (user_id);
CREATE INDEX idx_decks_archetype ON decks (archetype);
CREATE INDEX idx_decks_is_public ON decks (is_public) WHERE is_public = TRUE;

-- Tournaments table (for meta data)
CREATE TABLE tournaments (
    id TEXT PRIMARY KEY,                    -- Source ID
    source TEXT NOT NULL,                   -- "limitless", "rk9"

    name TEXT NOT NULL,
    date DATE NOT NULL,
    country TEXT,
    region TEXT,                            -- "NA", "EU", "JP", "LATAM", "APAC"

    format TEXT NOT NULL,                   -- "standard", "expanded"
    best_of INTEGER NOT NULL DEFAULT 3,     -- 1 for Japan, 3 for international

    player_count INTEGER,

    -- Metadata
    url TEXT,                               -- Link to source
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_tournaments_date ON tournaments (date DESC);
CREATE INDEX idx_tournaments_region ON tournaments (region);
CREATE INDEX idx_tournaments_format ON tournaments (format);

-- Tournament placements
CREATE TABLE tournament_placements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tournament_id TEXT REFERENCES tournaments(id) ON DELETE CASCADE,

    placement INTEGER NOT NULL,             -- 1, 2, 3, 4, 5-8, 9-16, etc.
    player_name TEXT,

    -- Deck info
    archetype TEXT NOT NULL,
    deck_list JSONB,                        -- Full deck list if available

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_placements_tournament ON tournament_placements (tournament_id);
CREATE INDEX idx_placements_archetype ON tournament_placements (archetype);

-- Meta snapshots (computed weekly)
CREATE TABLE meta_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    snapshot_date DATE NOT NULL,
    region TEXT NOT NULL,                   -- "global", "NA", "EU", "JP"
    format TEXT NOT NULL,                   -- "standard", "expanded"
    best_of INTEGER NOT NULL DEFAULT 3,     -- Separate JP BO1 snapshots

    -- Aggregated data
    archetype_shares JSONB NOT NULL,        -- {"Charizard ex": 0.15, ...}
    sample_size INTEGER NOT NULL,           -- Number of decks in sample

    -- Metadata
    tournaments_included TEXT[],            -- Tournament IDs used
    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(snapshot_date, region, format, best_of)
);

CREATE INDEX idx_meta_snapshots_date ON meta_snapshots (snapshot_date DESC);
CREATE INDEX idx_meta_snapshots_region ON meta_snapshots (region);
```

### 4.2 Views

```sql
-- Current standard meta (convenience view)
CREATE VIEW current_meta_standard AS
SELECT * FROM meta_snapshots
WHERE format = 'standard'
  AND snapshot_date = (
    SELECT MAX(snapshot_date) FROM meta_snapshots WHERE format = 'standard'
  );

-- Card inclusion rates (computed from tournament_placements)
CREATE VIEW card_inclusion_rates AS
SELECT
    card_id,
    archetype,
    COUNT(*) as times_included,
    AVG(quantity) as avg_quantity,
    COUNT(*) * 1.0 / (
        SELECT COUNT(*) FROM tournament_placements WHERE archetype = tp.archetype
    ) as inclusion_rate
FROM tournament_placements tp,
     jsonb_to_recordset(tp.deck_list) AS cards(card_id TEXT, quantity INTEGER)
GROUP BY card_id, archetype;
```

---

## 5. API Endpoints

### 5.1 Cards

```
GET  /api/v1/cards                    # List/search cards
     ?q=charizard                     # Text search
     ?supertype=Pokemon               # Filter by supertype
     ?types=Fire                      # Filter by type
     ?set_id=sv4                      # Filter by set
     ?legal_standard=true             # Only standard-legal
     ?page=1&limit=20                 # Pagination

GET  /api/v1/cards/{id}               # Get single card
GET  /api/v1/cards/{id}/usage         # Get usage stats for card
GET  /api/v1/cards/search/semantic    # Semantic search
     ?q=pokemon that discards energy
```

### 5.2 Decks

```
GET    /api/v1/decks                  # List user's decks
POST   /api/v1/decks                  # Create deck
GET    /api/v1/decks/{id}             # Get deck
PUT    /api/v1/decks/{id}             # Update deck
DELETE /api/v1/decks/{id}             # Delete deck

GET    /api/v1/decks/{id}/stats       # Get deck statistics
GET    /api/v1/decks/{id}/export      # Export deck (various formats)
       ?format=ptcgo                  # PTCGO format
       ?format=pokemoncard            # pokemoncard.io format
       ?format=text                   # Plain text

POST   /api/v1/decks/import           # Import deck from code/text
GET    /api/v1/decks/public           # Browse public decks
       ?archetype=Charizard%20ex
```

### 5.3 Meta

```
GET  /api/v1/meta/current             # Current meta snapshot
     ?region=global                   # Region filter
     ?format=standard                 # Format filter

GET  /api/v1/meta/history             # Meta history over time
     ?region=JP                       # Japan-specific
     ?start_date=2024-01-01
     ?end_date=2024-03-01

GET  /api/v1/meta/archetypes          # List known archetypes
GET  /api/v1/meta/archetypes/{name}   # Archetype details
     - Sample lists
     - Key cards
     - Matchup data (future)

GET  /api/v1/meta/tournaments         # Tournament results
     ?region=JP
     ?date_from=2024-01-01
```

### 5.4 Sets

```
GET  /api/v1/sets                     # List all sets
GET  /api/v1/sets/{id}                # Get set details
GET  /api/v1/sets/{id}/cards          # Get all cards in set
```

### 5.5 Health/Admin

```
GET  /api/v1/health                   # Health check
GET  /api/v1/health/db                # Database connectivity
POST /api/v1/admin/sync/cards         # Trigger card sync (admin only)
```

---

## 6. Key Implementation Details

### 6.1 TCGdex Integration

```python
# src/pipelines/tcgdex_sync.py

import httpx
from typing import AsyncGenerator

TCGDEX_BASE_URL = "http://localhost:3000"  # Self-hosted instance

async def fetch_all_cards(language: str = "en") -> AsyncGenerator[dict, None]:
    """Fetch all cards from TCGdex, paginated."""
    async with httpx.AsyncClient() as client:
        # Get all sets first
        sets_response = await client.get(f"{TCGDEX_BASE_URL}/{language}/sets")
        sets = sets_response.json()

        for set_data in sets:
            set_id = set_data["id"]
            # Get full set with cards
            set_detail = await client.get(
                f"{TCGDEX_BASE_URL}/{language}/sets/{set_id}"
            )
            set_info = set_detail.json()

            for card in set_info.get("cards", []):
                # Get full card detail
                card_detail = await client.get(
                    f"{TCGDEX_BASE_URL}/{language}/cards/{set_id}/{card['localId']}"
                )
                yield card_detail.json()

async def sync_cards_to_db():
    """Full sync of cards from TCGdex to our database."""
    # Fetch English
    async for card in fetch_all_cards("en"):
        await upsert_card(card, language="en")

    # Fetch Japanese names
    async for card in fetch_all_cards("ja"):
        await update_japanese_name(card["id"], card["name"])
```

### 6.2 Deck Builder State (Zustand)

```typescript
// src/lib/stores/deckStore.ts

import { create } from "zustand";
import { persist } from "zustand/middleware";

interface DeckCard {
  cardId: string;
  quantity: number;
}

interface DeckState {
  // Current deck being edited
  name: string;
  format: "standard" | "expanded";
  cards: DeckCard[];

  // Actions
  setName: (name: string) => void;
  addCard: (cardId: string) => void;
  removeCard: (cardId: string) => void;
  setQuantity: (cardId: string, quantity: number) => void;
  clearDeck: () => void;
  loadDeck: (deck: SavedDeck) => void;

  // Computed (these are getters)
  totalCards: () => number;
  pokemonCount: () => number;
  trainerCount: () => number;
  energyCount: () => number;
  isValidDeck: () => boolean;
}

export const useDeckStore = create<DeckState>()(
  persist(
    (set, get) => ({
      name: "Untitled Deck",
      format: "standard",
      cards: [],

      setName: (name) => set({ name }),

      addCard: (cardId) => {
        const cards = get().cards;
        const existing = cards.find((c) => c.cardId === cardId);

        if (existing) {
          if (existing.quantity < 4) {
            // Max 4 copies rule
            set({
              cards: cards.map((c) =>
                c.cardId === cardId ? { ...c, quantity: c.quantity + 1 } : c,
              ),
            });
          }
        } else {
          set({ cards: [...cards, { cardId, quantity: 1 }] });
        }
      },

      removeCard: (cardId) => {
        const cards = get().cards;
        const existing = cards.find((c) => c.cardId === cardId);

        if (existing && existing.quantity > 1) {
          set({
            cards: cards.map((c) =>
              c.cardId === cardId ? { ...c, quantity: c.quantity - 1 } : c,
            ),
          });
        } else {
          set({ cards: cards.filter((c) => c.cardId !== cardId) });
        }
      },

      setQuantity: (cardId, quantity) => {
        if (quantity <= 0) {
          set({ cards: get().cards.filter((c) => c.cardId !== cardId) });
        } else {
          set({
            cards: get().cards.map((c) =>
              c.cardId === cardId
                ? { ...c, quantity: Math.min(quantity, 4) }
                : c,
            ),
          });
        }
      },

      clearDeck: () => set({ name: "Untitled Deck", cards: [] }),

      loadDeck: (deck) =>
        set({
          name: deck.name,
          format: deck.format,
          cards: deck.cards,
        }),

      totalCards: () => get().cards.reduce((sum, c) => sum + c.quantity, 0),

      isValidDeck: () => get().totalCards() === 60,
    }),
    {
      name: "deck-builder-storage",
    },
  ),
);
```

### 6.3 Card Search with Semantic Fallback

```python
# src/services/search_service.py

from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
import openai

async def search_cards(
    db: AsyncSession,
    query: str,
    filters: dict = None,
    use_semantic: bool = True,
    limit: int = 20
) -> list[Card]:
    """
    Search cards with keyword + optional semantic search.
    Falls back to semantic when keyword results are poor.
    """
    # First, try keyword search
    keyword_results = await keyword_search(db, query, filters, limit)

    # If good results, return them
    if len(keyword_results) >= 5:
        return keyword_results

    # Otherwise, try semantic search
    if use_semantic and len(query.split()) >= 3:
        semantic_results = await semantic_search(db, query, filters, limit)

        # Merge and dedupe
        seen_ids = {r.id for r in keyword_results}
        for card in semantic_results:
            if card.id not in seen_ids:
                keyword_results.append(card)
                if len(keyword_results) >= limit:
                    break

    return keyword_results

async def keyword_search(
    db: AsyncSession,
    query: str,
    filters: dict = None,
    limit: int = 20
) -> list[Card]:
    """Full-text search on card names and text."""
    stmt = select(Card).where(
        or_(
            Card.name_en.ilike(f"%{query}%"),
            Card.name_ja.ilike(f"%{query}%"),
            func.to_tsvector('english', Card.name_en).match(query)
        )
    )

    if filters:
        if filters.get("supertype"):
            stmt = stmt.where(Card.supertype == filters["supertype"])
        if filters.get("types"):
            stmt = stmt.where(Card.types.contains([filters["types"]]))
        if filters.get("legal_standard"):
            stmt = stmt.where(Card.legality_standard == "Legal")

    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()

async def semantic_search(
    db: AsyncSession,
    query: str,
    filters: dict = None,
    limit: int = 20
) -> list[Card]:
    """Vector similarity search for natural language queries."""
    # Generate embedding for query
    embedding = await get_embedding(query)

    # Search by vector similarity
    stmt = select(Card).order_by(
        Card.text_embedding.cosine_distance(embedding)
    ).limit(limit)

    if filters:
        # Apply same filters as keyword search
        pass

    result = await db.execute(stmt)
    return result.scalars().all()

async def get_embedding(text: str) -> list[float]:
    """Get embedding from OpenAI."""
    response = await openai.embeddings.create(
        model="text-embedding-ada-002",
        input=text
    )
    return response.data[0].embedding
```

### 6.4 Meta Dashboard Data Aggregation

```python
# src/services/meta_service.py

from datetime import date, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

async def get_current_meta(
    db: AsyncSession,
    region: str = "global",
    format: str = "standard",
    best_of: int = 3
) -> dict:
    """Get current meta snapshot with archetype shares."""
    # Get most recent snapshot
    stmt = select(MetaSnapshot).where(
        MetaSnapshot.region == region,
        MetaSnapshot.format == format,
        MetaSnapshot.best_of == best_of
    ).order_by(MetaSnapshot.snapshot_date.desc()).limit(1)

    result = await db.execute(stmt)
    snapshot = result.scalar_one_or_none()

    if not snapshot:
        return {"error": "No meta data available"}

    return {
        "date": snapshot.snapshot_date,
        "region": snapshot.region,
        "format": snapshot.format,
        "best_of": snapshot.best_of,
        "archetypes": snapshot.archetype_shares,
        "sample_size": snapshot.sample_size,
    }

async def get_meta_history(
    db: AsyncSession,
    region: str,
    format: str,
    start_date: date,
    end_date: date,
    best_of: int = 3
) -> list[dict]:
    """Get meta evolution over time."""
    stmt = select(MetaSnapshot).where(
        MetaSnapshot.region == region,
        MetaSnapshot.format == format,
        MetaSnapshot.best_of == best_of,
        MetaSnapshot.snapshot_date >= start_date,
        MetaSnapshot.snapshot_date <= end_date
    ).order_by(MetaSnapshot.snapshot_date)

    result = await db.execute(stmt)
    snapshots = result.scalars().all()

    return [
        {
            "date": s.snapshot_date,
            "archetypes": s.archetype_shares,
            "sample_size": s.sample_size,
        }
        for s in snapshots
    ]

async def compute_meta_snapshot(
    db: AsyncSession,
    region: str,
    format: str,
    lookback_days: int = 30
) -> MetaSnapshot:
    """Compute a new meta snapshot from recent tournament data."""
    cutoff_date = date.today() - timedelta(days=lookback_days)

    # Determine best_of based on region
    best_of = 1 if region == "JP" else 3

    # Get placements from recent tournaments
    stmt = select(
        TournamentPlacement.archetype,
        func.count().label("count")
    ).join(
        Tournament
    ).where(
        Tournament.date >= cutoff_date,
        Tournament.format == format,
        Tournament.best_of == best_of,
        (Tournament.region == region) if region != "global" else True
    ).group_by(
        TournamentPlacement.archetype
    )

    result = await db.execute(stmt)
    archetype_counts = {row.archetype: row.count for row in result}

    total = sum(archetype_counts.values())
    archetype_shares = {
        archetype: count / total
        for archetype, count in archetype_counts.items()
    }

    # Create snapshot
    snapshot = MetaSnapshot(
        snapshot_date=date.today(),
        region=region,
        format=format,
        best_of=best_of,
        archetype_shares=archetype_shares,
        sample_size=total,
    )

    db.add(snapshot)
    await db.commit()

    return snapshot
```

---

## 7. Environment Variables

### 7.1 Frontend (.env.local for local dev)

```bash
# API
NEXT_PUBLIC_API_URL=http://localhost:8000

# Auth (Firebase or Supabase)
NEXT_PUBLIC_FIREBASE_API_KEY=your-firebase-key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
# OR
NEXT_PUBLIC_SUPABASE_URL=your-supabase-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key

# Optional: Analytics
NEXT_PUBLIC_GA_MEASUREMENT_ID=
```

### 7.2 Backend (.env for local dev)

```bash
# Database (local)
DATABASE_URL=postgresql://app_user:localdev@localhost:5432/trainerlab

# Database (Cloud SQL via proxy - for local dev against cloud)
# DATABASE_URL=postgresql://app_user:PASSWORD@localhost:5433/trainerlab

# Redis
REDIS_URL=redis://localhost:6379

# TCGdex
TCGDEX_URL=http://localhost:3000

# OpenAI (for embeddings)
OPENAI_API_KEY=sk-...

# Auth verification
FIREBASE_PROJECT_ID=your-project
# OR
SUPABASE_URL=your-supabase-url
SUPABASE_SERVICE_KEY=your-service-key

# Environment
ENVIRONMENT=development
DEBUG=true
GCP_PROJECT_ID=your-gcp-project
```

### 7.3 Production (via Secret Manager)

In production, secrets are injected via Cloud Run's Secret Manager integration:

```bash
# Cloud Run service config
--set-secrets="DATABASE_URL=database-url:latest"
--set-secrets="OPENAI_API_KEY=openai-key:latest"
--set-secrets="REDIS_URL=redis-url:latest"

# Non-secret env vars set directly
--set-env-vars="ENVIRONMENT=production"
--set-env-vars="GCP_PROJECT_ID=your-project"
--set-env-vars="TCGDEX_URL=https://tcgdex-xxxxx-uc.a.run.app"
```

### 7.4 Secret Manager Naming Convention

| Secret Name                | Description                              |
| -------------------------- | ---------------------------------------- |
| `database-url`             | Cloud SQL connection string              |
| `redis-url`                | Memorystore connection string            |
| `openai-key`               | OpenAI API key                           |
| `firebase-service-account` | Firebase admin SDK (if using Firebase)   |
| `supabase-service-key`     | Supabase service key (if using Supabase) |

---

## 8. Docker Compose (Local Development)

```yaml
# docker-compose.yml

version: "3.8"

services:
  # TCGdex card data API
  tcgdex:
    image: tcgdex/server:latest
    ports:
      - "3000:3000"
    environment:
      - PORT=3000

  # PostgreSQL with pgvector
  postgres:
    image: pgvector/pgvector:pg16
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: trainerlab
    volumes:
      - postgres_data:/var/lib/postgresql/data

  # Redis for caching
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

---

## 9. Implementation Order

### Phase 1: Foundation (Week 1)

**Day 1-2: Project Setup**

- [ ] Initialize monorepo structure
- [ ] Set up Next.js app with TypeScript, Tailwind, shadcn/ui
- [ ] Set up FastAPI project with Poetry
- [ ] Create docker-compose.yml
- [ ] Configure ESLint, Prettier, Ruff

**Day 3-4: Database**

- [ ] Create SQLAlchemy models
- [ ] Set up Alembic migrations
- [ ] Run initial migration
- [ ] Verify pgvector extension

**Day 5-7: Card Data Pipeline**

- [ ] Implement TCGdex sync script
- [ ] Run initial card sync (English + Japanese)
- [ ] Verify data in database
- [ ] Create basic card API endpoints

### Phase 2: Card Features (Week 2)

**Day 1-3: Card Search**

- [ ] Implement keyword search endpoint
- [ ] Create CardSearch component
- [ ] Create CardGrid component
- [ ] Create CardImage component
- [ ] Build /cards page

**Day 4-5: Card Detail**

- [ ] Create CardDetail component
- [ ] Build /cards/[id] page
- [ ] Show Japanese name when available

**Day 6-7: Semantic Search**

- [ ] Generate embeddings for cards
- [ ] Implement semantic search endpoint
- [ ] Add to search UI with fallback

### Phase 3: Deck Builder (Week 3)

**Day 1-2: Deck State**

- [ ] Create Zustand store
- [ ] Implement add/remove/quantity actions
- [ ] Persist to localStorage

**Day 3-5: Deck Builder UI**

- [ ] Create DeckBuilder component
- [ ] Create DeckList component (shows current deck)
- [ ] Create DeckStats component (counts, curve)
- [ ] Wire up card search to add cards

**Day 6-7: Deck Persistence**

- [ ] Create deck API endpoints
- [ ] Implement save/load
- [ ] Build /decks and /decks/[id] pages
- [ ] Add export functionality

### Phase 4: Meta Dashboard (Week 4)

**Day 1-2: Tournament Data**

- [ ] Manual import of sample tournament data
- [ ] Create meta snapshot computation
- [ ] Run initial snapshot

**Day 3-5: Meta UI**

- [ ] Create MetaChart component (pie/bar)
- [ ] Create ArchetypeCard component
- [ ] Create RegionFilter component
- [ ] Build /meta page

**Day 6-7: Japan View**

- [ ] Create Japan-specific snapshot (BO1)
- [ ] Build /meta/japan page
- [ ] Add BO1/tie rule context notices

### Phase 5: Polish (Week 5)

- [ ] Authentication (Supabase)
- [ ] User preferences
- [ ] Error handling
- [ ] Loading states
- [ ] Mobile responsiveness
- [ ] Basic tests
- [ ] Documentation

---

## 10. Code Style Guidelines

### 10.1 TypeScript/React

```typescript
// Use functional components with TypeScript
interface CardGridProps {
  cards: Card[];
  onCardClick?: (card: Card) => void;
  isLoading?: boolean;
}

export function CardGrid({ cards, onCardClick, isLoading = false }: CardGridProps) {
  if (isLoading) {
    return <CardGridSkeleton />;
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
      {cards.map((card) => (
        <CardImage
          key={card.id}
          card={card}
          onClick={() => onCardClick?.(card)}
        />
      ))}
    </div>
  );
}

// Use TanStack Query for data fetching
export function useCards(query: string, filters?: CardFilters) {
  return useQuery({
    queryKey: ['cards', query, filters],
    queryFn: () => api.searchCards(query, filters),
    enabled: query.length >= 2,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}
```

### 10.2 Python/FastAPI

```python
# Use type hints everywhere
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/cards", tags=["cards"])

@router.get("", response_model=PaginatedResponse[CardResponse])
async def list_cards(
    q: str | None = Query(None, description="Search query"),
    supertype: str | None = Query(None),
    types: list[str] | None = Query(None),
    legal_standard: bool | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[CardResponse]:
    """Search and filter cards."""
    cards, total = await card_service.search_cards(
        db,
        query=q,
        filters={
            "supertype": supertype,
            "types": types,
            "legal_standard": legal_standard,
        },
        page=page,
        limit=limit,
    )

    return PaginatedResponse(
        items=[CardResponse.from_orm(c) for c in cards],
        total=total,
        page=page,
        limit=limit,
    )
```

---

## 11. Testing Requirements

### 11.1 Backend Tests

```python
# tests/test_cards.py

import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_search_cards(client: AsyncClient):
    response = await client.get("/api/v1/cards", params={"q": "charizard"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) > 0
    assert "charizard" in data["items"][0]["name_en"].lower()

@pytest.mark.asyncio
async def test_get_card(client: AsyncClient):
    response = await client.get("/api/v1/cards/sv4-6")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "sv4-6"
```

### 11.2 Frontend Tests

```typescript
// __tests__/components/CardSearch.test.tsx

import { render, screen, fireEvent } from '@testing-library/react';
import { CardSearch } from '@/components/cards/CardSearch';

describe('CardSearch', () => {
  it('calls onSearch when typing', async () => {
    const onSearch = jest.fn();
    render(<CardSearch onSearch={onSearch} />);

    const input = screen.getByPlaceholderText(/search cards/i);
    fireEvent.change(input, { target: { value: 'charizard' } });

    // Debounced, so wait
    await new Promise(r => setTimeout(r, 500));

    expect(onSearch).toHaveBeenCalledWith('charizard');
  });
});
```

---

## 12. Deployment Architecture (GCP)

### 12.1 Why GCP

- Familiarity and comfort with the platform
- Goal: Match Vercel-like DX with full control
- Cost-effective at scale
- All services in one ecosystem

### 12.2 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              GCP ARCHITECTURE                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────┐                                                        │
│  │  Cloud DNS      │                                                        │
│  │  trainerlab.io    │                                                        │
│  └────────┬────────┘                                                        │
│           │                                                                  │
│           ▼                                                                  │
│  ┌─────────────────────────────────────────────┐                            │
│  │         Cloud Load Balancer (HTTPS)         │                            │
│  │         + Cloud CDN + Cloud Armor           │                            │
│  └──────────────────┬──────────────────────────┘                            │
│                     │                                                        │
│        ┌────────────┼────────────┐                                          │
│        │            │            │                                          │
│        ▼            ▼            ▼                                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                                    │
│  │ Cloud    │ │ Cloud    │ │ Cloud    │                                    │
│  │ Run      │ │ Run      │ │ Run      │                                    │
│  │ (Next.js)│ │ (FastAPI)│ │ (TCGdex) │                                    │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘                                    │
│       │            │            │                                           │
│       │            ▼            │                                           │
│       │     ┌──────────────┐    │                                          │
│       │     │ Cloud SQL    │◄───┘                                          │
│       │     │ (PostgreSQL) │                                                │
│       │     │ + pgvector   │                                                │
│       │     └──────────────┘                                                │
│       │            │                                                        │
│       │            ▼                                                        │
│       │     ┌──────────────┐                                               │
│       │     │ Memorystore  │                                               │
│       │     │ (Redis)      │                                               │
│       │     └──────────────┘                                               │
│       │                                                                     │
│       ▼                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                      │
│  │ Cloud        │  │ Secret       │  │ Cloud        │                      │
│  │ Storage      │  │ Manager      │  │ Scheduler    │                      │
│  │ (assets)     │  │ (env vars)   │  │ (cron jobs)  │                      │
│  └──────────────┘  └──────────────┘  └──────────────┘                      │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                     Cloud Build (CI/CD)                               │  │
│  │  GitHub Push → Build → Deploy to Cloud Run (preview or prod)          │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 12.3 Infrastructure as Code (Terraform)

All GCP infrastructure is managed via Terraform in the `/terraform` directory.

**Quick Start:**

```bash
# 1. Bootstrap state bucket (one-time)
cd terraform/bootstrap
terraform init
terraform apply -var="project_id=YOUR_PROJECT_ID"

# 2. Deploy infrastructure
cd ..
terraform init
terraform plan -var-file=environments/dev.tfvars
terraform apply -var-file=environments/dev.tfvars
```

**What Terraform Creates:**

| Resource                                          | Purpose                  |
| ------------------------------------------------- | ------------------------ |
| `google_cloud_run_v2_service.web`                 | Next.js frontend         |
| `google_cloud_run_v2_service.api`                 | FastAPI backend          |
| `google_cloud_run_v2_service.tcgdex`              | TCGdex card data         |
| `google_sql_database_instance.main`               | PostgreSQL with pgvector |
| `google_redis_instance.cache`                     | Redis cache              |
| `google_compute_network.vpc`                      | Private VPC              |
| `google_vpc_access_connector.connector`           | Cloud Run → VPC          |
| `google_secret_manager_secret.*`                  | All secrets              |
| `google_artifact_registry_repository.docker_repo` | Docker images            |
| `google_cloudbuild_trigger.deploy`                | CI/CD pipeline           |
| `google_cloud_scheduler_job.*`                    | Cron jobs                |
| `google_compute_*` (prod only)                    | Load balancer + CDN      |

**Environment Configurations:**

| Config        | Database         | Redis     | Cloud Run  | Load Balancer |
| ------------- | ---------------- | --------- | ---------- | ------------- |
| `dev.tfvars`  | db-f1-micro      | BASIC 1GB | Scale to 0 | None          |
| `prod.tfvars` | db-custom-1-3840 | HA 2GB    | Min 1      | Yes + CDN     |

See `/terraform/README.md` for full documentation.

### 12.4 CI/CD Pipeline (Cloud Build)

Cloud Build is configured via Terraform and uses `cloudbuild.yaml` in the repo root.

**Pipeline Flow:**

```
Push to GitHub
    ↓
Cloud Build Trigger (auto)
    ↓
Build Docker images (web + api)
    ↓
Push to Artifact Registry
    ↓
Deploy to Cloud Run
    ↓
(If main branch) → Production
(If feature branch) → Preview URL
```

**cloudbuild.yaml** handles:

- Detecting branch (main vs feature)
- Building both frontend and backend images
- Deploying to Cloud Run with correct env vars
- Creating preview deployments for PRs

### 12.5 Dockerfiles

Dockerfiles for each service are in their respective app directories:

- `apps/web/Dockerfile` - Next.js standalone build
- `apps/api/Dockerfile` - FastAPI with Poetry

### 12.6 Post-Terraform Setup

After running `terraform apply`, a few manual steps remain:

```bash
# 1. Set OpenAI API key
echo -n "sk-your-key" | gcloud secrets versions add openai-key --data-file=-

# 2. Enable pgvector in Cloud SQL
gcloud sql connect trainerlab-db-development --user=app_user --database=trainerlab
# Then in psql: CREATE EXTENSION IF NOT EXISTS vector;

# 3. Configure Docker auth
gcloud auth configure-docker us-central1-docker.pkg.dev

# 4. Connect GitHub repo to Cloud Build (via Console)
# https://console.cloud.google.com/cloud-build/triggers
```

### 12.7 Useful Commands

```bash
# View service URLs
terraform output web_url
terraform output api_url

# Connect to database
gcloud sql connect $(terraform output -raw database_instance_name) --user=app_user

# View logs
gcloud logging read 'resource.type="cloud_run_revision"' --limit=50

# Force redeploy
gcloud run services update trainerlab-api --region=us-central1 --image=LATEST_IMAGE
```

### 12.8 Environment Separation

| Environment | Terraform Config | Database         | Cloud Run  |
| ----------- | ---------------- | ---------------- | ---------- |
| Development | `dev.tfvars`     | db-f1-micro      | Scale to 0 |
| Production  | `prod.tfvars`    | db-custom-1-3840 | Min 1 + LB |

### 12.9 Cost Estimates

| Environment | Monthly Cost |
| ----------- | ------------ |
| Development | $50-100      |
| Production  | $150-250     |

Cloud Run scaling to zero is the biggest cost saver for dev environments.

---

## 13. Success Criteria for MVP

- [ ] User can search cards by name
- [ ] User can view card details including Japanese name
- [ ] User can build a 60-card deck
- [ ] User can save and load decks
- [ ] User can export deck in PTCGO format
- [ ] User can view current meta share percentages
- [ ] User can view Japan-specific meta with BO1 context
- [ ] Basic authentication works
- [ ] Site is responsive on mobile
- [ ] Page load times < 2 seconds

---

## 14. Future Considerations (Post-MVP)

- Card reveal ingestion pipeline
- LimitlessTCG partnership integration
- Price tracking
- Matchup data
- Deck comparison tools
- Social features (comments, ratings)
- API for third-party tools
- Mobile app (React Native)

---

_Last updated: January 2026_
_For Claude Code implementation_
