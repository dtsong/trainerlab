# TrainerLab Codemap

> Last updated: 2026-02-06
> Purpose: Quick reference for code navigation and token-efficient context

---

## Repository Structure

```
trainerlab/
├── tl                # Developer CLI (./tl --help)
├── apps/
│   ├── api/          # FastAPI backend (Python)
│   └── web/          # Next.js frontend (TypeScript)
├── packages/
│   └── shared-types/ # Shared TypeScript types
├── scripts/          # Bash developer scripts (called via ./tl)
├── terraform/        # Infrastructure as code
└── docs/             # Project documentation
```

---

## 1. Backend (apps/api/)

**Tech Stack:** FastAPI, SQLAlchemy, PostgreSQL, pgvector, NextAuth.js JWT

### Entry Point

- `src/main.py` - FastAPI app initialization, middleware, router registration

### Core Structure

```
apps/api/src/
├── main.py                    # App entry, CORS, rate limiting, security headers
├── config.py                  # Settings via pydantic-settings
├── core/
│   └── jwt.py                # HS256 JWT verification (NextAuth.js)
├── db/
│   ├── database.py           # SQLAlchemy engine, session factory
│   └── base.py               # Declarative base
├── dependencies/
│   ├── auth.py               # JWT token verification dependency
│   ├── admin.py              # Admin authorization dependency
│   ├── api_key_auth.py       # API key authentication dependency
│   ├── creator.py            # Creator role authorization dependency
│   └── scheduler_auth.py     # Cloud Scheduler auth dependency
├── models/                   # SQLAlchemy ORM models (33 files)
├── schemas/                  # Pydantic request/response schemas (19 files + 1 subpackage)
├── routers/                  # API endpoint definitions (19 files)
├── services/                 # Business logic (25 files)
├── pipelines/                # Data pipeline jobs (9 files)
├── clients/                  # External API clients (5 files)
├── data/                     # Static data (signature cards, sprite archetype map, card reprints, TCG glossary)
└── fixtures/                 # Test data
```

### Database Models (`models/`)

| Model                      | File                              | Purpose                                   |
| -------------------------- | --------------------------------- | ----------------------------------------- |
| User                       | `user.py`                         | User accounts                             |
| Deck                       | `deck.py`                         | User decks                                |
| Card                       | `card.py`                         | TCG card data                             |
| Set                        | `set.py`                          | Card sets                                 |
| Tournament                 | `tournament.py`                   | Tournament metadata                       |
| TournamentPlacement        | `tournament_placement.py`         | Tournament results                        |
| MetaSnapshot               | `meta_snapshot.py`                | Meta share aggregations                   |
| LabNote                    | `lab_note.py`                     | Content articles                          |
| LabNoteRevision            | `lab_note_revision.py`            | Lab note revision tracking                |
| Waitlist                   | `waitlist.py`                     | Email signups                             |
| FormatConfig               | `format_config.py`                | Format rotation dates                     |
| RotationImpact             | `rotation_impact.py`              | Card rotation analysis                    |
| JPCardInnovation           | `jp_card_innovation.py`           | Japanese card tracking                    |
| JPNewArchetype             | `jp_new_archetype.py`             | New JP archetypes                         |
| JPSetImpact                | `jp_set_impact.py`                | JP set impact predictions                 |
| JPCardAdoptionRate         | `jp_card_adoption_rate.py`        | JP meta card adoption rates               |
| JPUnreleasedCard           | `jp_unreleased_card.py`           | JP cards not yet released internationally |
| ArchetypeSprite            | `archetype_sprite.py`             | Sprite-key → archetype mapping            |
| Prediction                 | `prediction.py`                   | Meta predictions                          |
| ArchetypePrediction        | `archetype_prediction.py`         | Archetype performance forecasts           |
| ArchetypeEvolutionSnapshot | `archetype_evolution_snapshot.py` | Archetype performance over time           |
| Adaptation                 | `adaptation.py`                   | Changes between archetype snapshots       |
| EvolutionArticle           | `evolution_article.py`            | Archetype evolution content articles      |
| EvolutionArticleSnapshot   | `evolution_article_snapshot.py`   | Join table: articles ↔ snapshots          |
| CardIdMapping              | `card_id_mapping.py`              | JP ↔ EN card ID mappings                  |
| PlaceholderCard            | `placeholder_card.py`             | Placeholder cards for unreleased JP cards |
| TranslatedContent          | `translated_content.py`           | Translated content from JP sources        |
| TranslationTermOverride    | `translation_term_override.py`    | Custom translation glossary overrides     |
| ApiKey                     | `api_key.py`                      | Creator API key management                |
| ApiRequest                 | `api_request.py`                  | API request usage tracking                |
| DataExport                 | `data_export.py`                  | User data export requests                 |
| Widget                     | `widget.py`                       | Embeddable creator widgets                |
| WidgetView                 | `widget_view.py`                  | Widget analytics tracking                 |

### API Routers (`routers/`)

| Router            | Prefix                | Key Endpoints                                                                           |
| ----------------- | --------------------- | --------------------------------------------------------------------------------------- |
| `health.py`       | `/api/v1/health`      | Health check                                                                            |
| `cards.py`        | `/api/v1/cards`       | GET /, GET /{id}, Search with embeddings                                                |
| `sets.py`         | `/api/v1/sets`        | GET /, GET /{id}                                                                        |
| `decks.py`        | `/api/v1/decks`       | CRUD operations, export/import                                                          |
| `meta.py`         | `/api/v1/meta`        | GET /current, /history, /archetypes, /compare, /forecast                                |
| `tournaments.py`  | `/api/v1/tournaments` | GET /, GET /{id}, Filter + paginate                                                     |
| `japan.py`        | `/api/v1/japan`       | JP-specific endpoints (innovation, archetypes, sets, predictions)                       |
| `lab_notes.py`    | `/api/v1/lab-notes`   | GET /, GET /{slug}                                                                      |
| `waitlist.py`     | `/api/v1/waitlist`    | POST /                                                                                  |
| `format.py`       | `/api/v1`             | GET /current, GET /rotations, GET /rotation-impact                                      |
| `users.py`        | `/api/v1/users`       | GET /me, PUT /me                                                                        |
| `pipeline.py`     | `/api/v1/pipeline`    | POST /discover-_, /process-tournament, /compute-_, /sync-_, /translate-_                |
| `admin.py`        | `/api/v1/admin`       | Placeholder card and archetype sprite CRUD                                              |
| `api_keys.py`     | `/api/v1/api-keys`    | POST /, GET /, GET /{id}, DELETE /{id}                                                  |
| `evolution.py`    | `/api/v1`             | GET /archetypes/{id}/evolution, /prediction, GET /evolution, /accuracy                  |
| `exports.py`      | `/api/v1/exports`     | POST /, GET /, GET /{id}, GET /{id}/download                                            |
| `public_api.py`   | `/api/v1/public`      | GET /teaser/home, /meta, /meta/history, /archetypes/{}, /tournaments, /japan/comparison |
| `translations.py` | `/api/v1`             | GET /japan/adoption-rates, /upcoming-cards, admin translation CRUD                      |
| `widgets.py`      | `/api/v1/widgets`     | POST /, GET /, GET /{id}, GET /{id}/data, PATCH /{id}, DELETE /{id}                     |

### Schemas (`schemas/`)

| Schema          | File                  | Purpose                                   |
| --------------- | --------------------- | ----------------------------------------- |
| Card            | `card.py`             | Card search, filter, detail responses     |
| Set             | `set.py`              | Set list and detail responses             |
| Deck            | `deck.py`             | Deck CRUD request/response                |
| Meta            | `meta.py`             | Meta snapshot and archetype share schemas |
| Tournament      | `tournament.py`       | Tournament list and detail schemas        |
| Japan           | `japan.py`            | JP innovation, archetype, set schemas     |
| LabNote         | `lab_note.py`         | Lab note request/response                 |
| Format          | `format.py`           | Format config and rotation schemas        |
| User            | `user.py`             | User profile schemas                      |
| Pagination      | `pagination.py`       | Generic paginated response wrapper        |
| Pipeline        | `pipeline.py`         | Pipeline trigger request/result schemas   |
| Usage           | `usage.py`            | Card usage statistics schemas             |
| ApiKey          | `api_key.py`          | API key create/list/response schemas      |
| ArchetypeSprite | `archetype_sprite.py` | Sprite mapping CRUD schemas               |
| Evolution       | `evolution.py`        | Evolution timeline and prediction schemas |
| Export          | `export.py`           | Data export request/download schemas      |
| Placeholder     | `placeholder.py`      | Placeholder card CRUD schemas             |
| Translation     | `translation.py`      | Translation request/response schemas      |
| Widget          | `widget.py`           | Widget create/update/data schemas         |
| Public          | `public/`             | Public API response schemas (subpackage)  |

### Services (`services/`)

| Service                          | Purpose                                                                            |
| -------------------------------- | ---------------------------------------------------------------------------------- |
| `card_service.py`                | Card search with vector embeddings                                                 |
| `card_sync.py`                   | Sync cards from TCGdex API                                                         |
| `set_service.py`                 | Set management                                                                     |
| `deck_service.py`                | Deck CRUD operations                                                               |
| `deck_import.py`                 | Import from PTCGO/Limitless/TCGONEgame formats                                     |
| `deck_export.py`                 | Export to PTCGO format                                                             |
| `meta_service.py`                | Meta snapshot queries                                                              |
| `tournament_scrape.py`           | Scrape Limitless tournament data                                                   |
| `archetype_detector.py`          | Detect deck archetype from signature cards (fallback)                              |
| `archetype_normalizer.py`        | Archetype normalization: sprite_lookup → auto_derive → signature_card → text_label |
| `lab_note_service.py`            | Lab notes CRUD                                                                     |
| `usage_service.py`               | Deck usage analytics                                                               |
| `user_service.py`                | User management                                                                    |
| `adaptation_classifier.py`       | AI-powered adaptation classification and meta context generation                   |
| `api_key_service.py`             | API key CRUD operations for creators                                               |
| `cloud_tasks.py`                 | Enqueue tournament processing via Cloud Tasks                                      |
| `data_export_service.py`         | Creator data exports (CSV/JSON/XLSX)                                               |
| `decklist_diff.py`               | Consensus decklist computation and diff engine                                     |
| `evolution_article_generator.py` | AI-generated archetype evolution narrative articles                                |
| `evolution_service.py`           | Archetype evolution snapshots and adaptation detection                             |
| `placeholder_service.py`         | Manage placeholder cards for unreleased JP cards                                   |
| `prediction_engine.py`           | AI-powered archetype performance forecasting                                       |
| `storage_service.py`             | Google Cloud Storage file operations                                               |
| `translation_service.py`         | 3-layer JP→EN translation (glossary → template → Claude)                           |
| `widget_service.py`              | Widget CRUD and data resolution for embeddable widgets                             |

### Pipelines (`pipelines/`)

| Pipeline                     | Trigger             | Purpose                                              |
| ---------------------------- | ------------------- | ---------------------------------------------------- |
| `scrape_limitless.py`        | Daily 6am/7am UTC   | Discover + process EN/JP tournaments from Limitless  |
| `compute_meta.py`            | Daily 8am UTC       | Compute meta snapshots, JP signals, tiers            |
| `compute_evolution.py`       | Daily 9am UTC       | AI-powered evolution analysis, predictions, articles |
| `compute_jp_intelligence.py` | On demand / chained | Derive JP innovations and new archetypes             |
| `sync_cards.py`              | Weekly Sunday       | Sync EN+JP card data from TCGdex                     |
| `sync_card_mappings.py`      | Weekly Sunday       | Sync JP↔EN card ID mappings                          |
| `sync_events.py`             | Weekly              | Sync upcoming events from RK9 + Pokemon Events       |
| `monitor_card_reveals.py`    | Every 6 hours       | Monitor Limitless for new JP card reveals            |
| `sync_jp_adoption_rates.py`  | Tue/Thu/Sat         | Sync JP card adoption rates from Pokecabook          |
| `translate_pokecabook.py`    | Mon/Wed/Fri         | Translate JP meta content from Pokecabook            |
| `translate_tier_lists.py`    | Weekly Sunday       | Translate tier lists from Pokecabook and Pokekameshi |
| `reprocess_archetypes.py`    | Monthly / manual    | Reprocess existing placement archetype labels        |
| `prune_tournaments.py`       | Manual              | Delete tournaments before a cutoff date              |
| `seed_data.py`               | Manual              | Seed format configs and archetype sprites            |
| `wipe_data.py`               | Manual              | Truncate non-user data tables for reset/testing      |

### External Clients (`clients/`)

- `tcgdex.py` - TCGdex API client (card data)
- `limitless.py` - Limitless API client (tournament data)
- `claude.py` - Anthropic Claude API client (AI features)
- `pokecabook.py` - Pokecabook scraper (JP meta data, tier lists, articles)
- `pokekameshi.py` - Pokekameshi scraper (JP tier data, meta percentages)

### Database Migrations

- **Location:** `alembic/versions/`
- **Count:** 23 migrations
- **Tool:** Alembic

---

## 2. Frontend (apps/web/)

**Tech Stack:** Next.js 14+ (App Router), React, TypeScript, Tailwind CSS, shadcn/ui

### Entry Point

- `src/app/layout.tsx` - Root layout, font setup, providers, navigation

### Core Structure

```
apps/web/src/
├── app/                      # Next.js App Router pages
│   ├── page.tsx             # Home page
│   ├── layout.tsx           # Root layout
│   ├── providers.tsx        # Context providers
│   ├── cards/               # Card search & detail
│   ├── decks/               # Deck builder & management
│   ├── meta/                # Meta dashboard
│   ├── tournaments/         # Tournament archive
│   ├── lab-notes/           # Content articles
│   ├── rotation/            # Format rotation page
│   ├── auth/                # Login (Google OAuth)
│   ├── api/                 # API routes (auth, waitlist)
│   └── feed.xml/            # RSS feed route
├── components/              # React components (organized by domain)
│   ├── admin/              # Admin guard and header
│   ├── cards/              # Card search, filters, grid (7 components)
│   ├── commerce/           # BuildDeckCTA (1 component)
│   ├── deck/               # Deck builder, list, stats (9 components)
│   ├── home/               # Home page sections (9 components)
│   ├── japan/              # JP-specific components (4 components)
│   ├── lab-notes/          # Lab notes components (2 components)
│   ├── layout/             # Navigation, footer (7 components)
│   ├── meta/               # Meta dashboard components (16 components)
│   ├── rotation/           # Rotation components (4 components)
│   ├── tournaments/        # Tournament components (2 components)
│   └── ui/                 # shadcn/ui + custom UI primitives (27 components)
├── lib/
│   └── auth.ts            # NextAuth.js configuration
├── hooks/                  # Custom React hooks (8 hooks)
├── lib/                    # Utilities
│   ├── api.ts             # API client wrapper
│   ├── auth.ts            # NextAuth.js config (Google OAuth, HS256 JWT)
│   ├── utils.ts           # cn() helper
│   ├── analytics.ts       # Analytics tracking
│   ├── affiliate.ts       # Commerce affiliate links
│   ├── chart-colors.ts    # Chart color utilities
│   ├── deckFormats.ts     # Deck format validation
│   └── meta-utils.ts      # Meta calculation utilities
├── stores/                # Zustand state management
│   └── deckStore.ts       # Deck builder state
├── types/                 # Local type definitions
└── test/
    └── setup.ts           # Vitest test setup
```

### App Router Pages (`app/`)

| Route               | File                        | Purpose                                        |
| ------------------- | --------------------------- | ---------------------------------------------- |
| `/`                 | `page.tsx`                  | Home page with hero, meta snapshot, JP preview |
| `/cards`            | `cards/page.tsx`            | Card search with filters                       |
| `/cards/[id]`       | `cards/[id]/page.tsx`       | Card detail view                               |
| `/decks`            | `decks/page.tsx`            | User's deck list                               |
| `/decks/new`        | `decks/new/page.tsx`        | Deck builder                                   |
| `/decks/[id]`       | `decks/[id]/page.tsx`       | Deck view/edit                                 |
| `/meta`             | `meta/page.tsx`             | Meta dashboard with tier list                  |
| `/meta/japan`       | `meta/japan/page.tsx`       | From Japan page with BO1 context               |
| `/tournaments`      | `tournaments/page.tsx`      | Tournament archive browser                     |
| `/tournaments/[id]` | `tournaments/[id]/page.tsx` | Tournament detail                              |
| `/lab-notes`        | `lab-notes/page.tsx`        | Lab notes list                                 |
| `/lab-notes/[slug]` | `lab-notes/[slug]/page.tsx` | Lab note article                               |
| `/rotation`         | `rotation/page.tsx`         | Format rotation & card survival                |
| `/auth/login`       | `auth/login/page.tsx`       | Login page (Google OAuth)                      |
| `/feed.xml`         | `feed.xml/route.ts`         | RSS feed generation                            |

### Component Organization

#### UI Primitives (`components/ui/`)

**shadcn/ui components (17):**

- button, input, card, badge, dialog, dropdown-menu, select, label, table, tabs, checkbox, textarea, progress, avatar, separator, sheet, sonner

**Custom TrainerLab components (11):**

- `pill-toggle.tsx` - Filter toggle group
- `section-label.tsx` - Mono label with icon + divider
- `tier-badge.tsx` - S/A/B/C/Rogue badges with colors
- `trend-arrow.tsx` - Up/down/stable indicators
- `jp-signal-badge.tsx` - JP divergence badge (red)
- `stat-block.tsx` - Large mono numbers with labels
- `panel-overlay.tsx` - Dark overlay for slide-outs
- `confidence-badge.tsx` - Data confidence indicator (high/medium/low)

#### Domain Components

**Cards (`components/cards/`):**

- CardSearchInput, CardFilters, MobileCardFilters, CardGrid, CardDetail, CardImage, CardFiltersSkeleton, CardGridSkeleton

**Deck Builder (`components/deck/`):**

- DeckBuilder, DeckList, DeckListItem, DeckCard, DeckStats, DeckValidation, DeckImportModal, DeckExportModal, DeckCardSkeleton

**Meta Dashboard (`components/meta/`):**

- FilterBar, HealthIndicators, TierList, ArchetypeCard, ArchetypePanel, MatchupSpread, BuildItBanner, RegionFilter, DateRangePicker, MetaBarChart, MetaPieChart, MetaTrendChart, ChartErrorBoundary, BO1ContextBanner, ChartSkeleton, ArchetypeCardSkeleton

**Home Page (`components/home/`):**

- Hero, JPAlertBanner, MetaSnapshot, EvolutionPreview, ContentGrid, FormatForecast, WhyTrainerLab, ResearchPassWaitlist, TrainersToolkit

**Japan (`components/japan/`):**

- PredictionAccuracyTracker, CardInnovationTracker, NewArchetypeWatch, SetImpactTimeline, MetaDivergenceComparison, CardCountEvolutionChart, CardCountEvolutionSection, CardAdoptionRates, UpcomingCards, CityLeagueResultsFeed, DecklistViewer

**Layout (`components/layout/`):**

- TopNav, MobileNav, Footer, Header, UserMenu, ScrollToTop

**Rotation (`components/rotation/`):**

- RotationCountdown, CardRotationList, ArchetypeSurvival, SurvivalBadge

**Tournaments (`components/tournaments/`):**

- TournamentCard, TournamentFilters

**Lab Notes (`components/lab-notes/`):**

- LabNoteCard, LabNoteTypeFilter

**Commerce (`components/commerce/`):**

- BuildDeckCTA

**Auth:**

- Login page uses `signIn("google")` from next-auth/react directly

### Custom Hooks (`hooks/`)

| Hook             | Purpose                                                      |
| ---------------- | ------------------------------------------------------------ |
| `useAuth`        | NextAuth.js session state                                    |
| `useCards`       | Card search queries                                          |
| `useSets`        | Card set queries                                             |
| `useDecks`       | Deck CRUD operations                                         |
| `useTournaments` | Tournament queries                                           |
| `useLabNotes`    | Lab notes queries                                            |
| `useJapan`       | Japan-specific queries                                       |
| `useFormat`      | Format rotation queries                                      |
| `useMeta`        | Meta queries: current, history, comparison, forecast, detail |

### State Management

- **Deck Builder:** Zustand store (`stores/deckStore.ts`)
- **Auth:** NextAuth.js SessionProvider + useSession
- **Server State:** React Query (via hooks)

### Design System

**Typography:**

- Display: Playfair Display (editorial)
- Body: DM Sans (hybrid)
- Mono: JetBrains Mono (terminal)

**Color Tokens:** (see `tailwind.config.ts`)

- Teal (primary), Amber (accent), Parchment (editorial)
- Terminal theme (dark backgrounds)
- Archetype colors (type-based)
- Tier colors (S/A/B/C/Rogue)
- Signal colors (up/down/stable/jp)

---

## 3. Shared Types (packages/shared-types/)

**Purpose:** TypeScript types shared between frontend and backend schemas

```
packages/shared-types/src/
├── index.ts           # Main export
├── card.ts            # Card, CardFilters, SearchParams
├── set.ts             # Set, SetFilters
├── meta.ts            # MetaSnapshot, ArchetypeShare, JPSignal
├── tournament.ts      # Tournament, TournamentPlacement
├── japan.ts           # JPCardInnovation, JPNewArchetype, JPSetImpact, Prediction
├── format.ts          # FormatConfig, RotationImpact
├── lab-note.ts        # LabNote, LabNoteType
└── pagination.ts      # PaginatedResponse
```

**Key Types:**

- `Card` - TCG card with embeddings
- `Deck` - User deck with card list
- `MetaSnapshot` - Aggregated meta data
- `ArchetypeShare` - Archetype meta share + tier
- `JPSignal` - Japan vs EN divergence indicator
- `Tournament` - Tournament metadata
- `TournamentPlacement` - Individual placement
- `LabNote` - Content article
- `FormatConfig` - Format rotation dates

---

## 4. Infrastructure (terraform/)

**Tech Stack:** Terraform, GCP (Cloud Run, Cloud SQL, Cloud Scheduler)

```
terraform/
├── main.tf            # Root module, provider config
├── variables.tf       # Input variables
├── outputs.tf         # Output values
├── github_oidc.tf     # GitHub Actions OIDC setup
├── modules/
│   ├── cloud_run/     # Cloud Run service module
│   ├── cloud_sql/     # PostgreSQL + pgvector module
│   └── scheduler/     # Cloud Scheduler jobs module
└── environments/
    └── prod.tfvars    # Production variables
```

**Resources:**

- Cloud Run: API service deployment
- Cloud SQL: PostgreSQL 15 with pgvector extension
- Cloud Scheduler: Data pipeline cron jobs
- Workload Identity: GitHub Actions deployment
- VPC Connector: Cloud Run → Cloud SQL connectivity

---

## 5. Key Workflows

### Data Flow

```
External Sources → Pipelines → Database → API → Frontend
     ↓                ↓           ↓        ↓       ↓
  TCGdex          sync_cards    Cards   GET     Card Search
  Limitless       discover-*/process-tournament      Tournaments  /tournaments  Browser
                  compute_meta  MetaSnapshots  /meta  Dashboard
```

### User Flows

1. **Card Search:** Frontend → API `/cards?q=...` → pgvector similarity search → Results
2. **Deck Building:** Frontend (Zustand) → API `/decks` → PostgreSQL → Saved
3. **Meta View:** Frontend → API `/meta/current?region=...` → Computed snapshot → Charts
4. **JP Comparison:** Frontend → API `/meta/compare?region_a=JP` → Server-side divergence analysis
5. **Format Forecast:** Frontend → API `/meta/forecast` → JP archetypes to watch for EN meta
6. **Tournament Browse:** Frontend → API `/tournaments?filter=...` → Paginated results

### Authentication Flow

```
User → Google OAuth (NextAuth.js) → HS256 JWT cookie → API (verify with NEXTAUTH_SECRET) → Protected endpoint
```

---

## 6. Testing

**Test Files:** ~56 test files

**Frontend (Vitest + React Testing Library):**

- Component tests: `__tests__/*.test.tsx`
- Hook tests: `__tests__/*.test.ts`
- Utility tests: `__tests__/*.test.ts`

**Backend (pytest):**

- Unit tests: `tests/unit/`
- Integration tests: `tests/integration/`

---

## 7. Key Algorithms

### JP Signal Calculation

```python
# src/services/meta_service.py
def calculate_jp_signal(jp_share: float, en_share: float, threshold: float = 0.05):
    diff = jp_share - en_share
    if abs(diff) < threshold:
        return {"has_signal": False}
    return {
        "has_signal": True,
        "direction": "rising" if diff > 0 else "falling",
        "difference": diff
    }
```

### Archetype Detection

```python
# Primary: src/services/archetype_normalizer.py
# Priority chain: sprite_lookup → auto_derive → signature_card → text_label
# SPRITE_ARCHETYPE_MAP maps known sprite-keys to canonical archetype names
# DB table: archetype_sprites (runtime override for curated mappings)
# Provenance: TournamentPlacement.archetype_detection_method

# Fallback: src/services/archetype_detector.py
# Maps signature cards (e.g., "sv4-125") → archetype name
# Used as Priority 3 within ArchetypeNormalizer
```

### Card Search with Embeddings

```python
# src/services/card_service.py
# 1. Generate embedding for search query (via external service)
# 2. pgvector similarity search: card_embedding <-> query_embedding
# 3. Apply filters (set, type, rarity)
# 4. Return ranked results
```

### Tier Assignment

```python
# Based on meta share %
S: > 15%, A: 8-15%, B: 3-8%, C: 1-3%, Rogue: < 1%
```

---

## 8. External Dependencies

### Backend

- **Web Framework:** FastAPI, Uvicorn
- **Database:** SQLAlchemy, Alembic, asyncpg, pgvector
- **Auth:** python-jose (HS256 JWT verification)
- **HTTP:** httpx
- **AI:** anthropic (Claude API)
- **Cloud:** google-cloud-tasks, google-cloud-storage
- **Scraping:** beautifulsoup4
- **Rate Limiting:** slowapi
- **Testing:** pytest, pytest-asyncio, pytest-cov

### Frontend

- **Framework:** Next.js 14+, React 18
- **Styling:** Tailwind CSS, class-variance-authority
- **UI Components:** Radix UI, Lucide icons
- **State:** Zustand, React Query
- **Auth:** NextAuth.js v5 (Auth.js), jose
- **Charts:** Recharts
- **Testing:** Vitest, React Testing Library
- **Forms:** React Hook Form, Zod

### Infrastructure

- **IaC:** Terraform
- **Cloud:** GCP (Cloud Run, Cloud SQL, Cloud Scheduler, Cloud Tasks, Cloud Storage)

---

## 9. Configuration Files

| File                          | Purpose                           |
| ----------------------------- | --------------------------------- |
| `package.json`                | Root workspace config (pnpm)      |
| `pnpm-workspace.yaml`         | Monorepo workspace definition     |
| `apps/web/next.config.mjs`    | Next.js configuration             |
| `apps/web/tailwind.config.ts` | Tailwind design tokens            |
| `apps/api/pyproject.toml`     | Python dependencies (uv)          |
| `apps/api/alembic.ini`        | Database migration config         |
| `.pre-commit-config.yaml`     | Pre-commit hooks (ruff, prettier) |
| `docker-compose.yml`          | Local development PostgreSQL      |
| `.github/workflows/`          | CI/CD pipelines                   |

---

## 10. Quick Reference

### Find By Concept

| What                     | Where                         |
| ------------------------ | ----------------------------- |
| API endpoint definitions | `apps/api/src/routers/`       |
| Database models          | `apps/api/src/models/`        |
| Business logic           | `apps/api/src/services/`      |
| Data pipelines           | `apps/api/src/pipelines/`     |
| Page routes              | `apps/web/src/app/*/page.tsx` |
| React components         | `apps/web/src/components/`    |
| Custom hooks             | `apps/web/src/hooks/`         |
| UI primitives            | `apps/web/src/components/ui/` |
| Shared types             | `packages/shared-types/src/`  |
| Infrastructure           | `terraform/`                  |
| Database migrations      | `apps/api/alembic/versions/`  |
| Tests (frontend)         | `apps/web/src/**/__tests__/`  |
| Tests (backend)          | `apps/api/tests/`             |

### Developer CLI

All developer scripts are accessible via `./tl`. Run `./tl --help` for the full command list.

```bash
./tl setup                 # First-time setup (deps, Docker, migrations, seed)
./tl dev                   # Start full local stack (Docker + API + web)
./tl check                 # Run all verification scripts
./tl test-all              # Run all test scripts
./tl verify local          # Verify local Docker environment
./tl sync cards --dry-run  # Sync cards from TCGdex
```

### Common Tasks

**Add new API endpoint:**

1. Create schema in `apps/api/src/schemas/`
2. Add service logic in `apps/api/src/services/`
3. Create router in `apps/api/src/routers/`
4. Register router in `apps/api/src/main.py`

**Add new page:**

1. Create `apps/web/src/app/[route]/page.tsx`
2. Add navigation link in `apps/web/src/components/layout/TopNav.tsx`
3. Add to mobile nav if needed

**Add new component:**

1. Create in appropriate domain folder under `apps/web/src/components/`
2. Export from `index.ts` in that folder
3. Add tests in `__tests__/` subfolder

**Add database model:**

1. Create model in `apps/api/src/models/`
2. Import in `apps/api/src/models/__init__.py`
3. Create migration: `cd apps/api && uv run alembic revision --autogenerate -m "description"`
4. Review and run: `uv run alembic upgrade head`

**Add shared type:**

1. Define in `packages/shared-types/src/`
2. Export from `packages/shared-types/src/index.ts`
3. Use in both frontend and backend schemas

---

## 11. Development Commands

### Frontend (apps/web)

```bash
pnpm dev              # Start dev server
pnpm build            # Production build
pnpm test             # Run tests
pnpm test:coverage    # Tests with coverage
pnpm lint             # Lint with eslint
pnpm format           # Format with prettier
```

### Backend (apps/api)

```bash
uv sync               # Install dependencies
uv run uvicorn src.main:app --reload  # Dev server
uv run pytest         # Run tests
uv run pytest --cov   # Tests with coverage
uv run ruff check     # Lint
uv run ruff format    # Format
uv run ty check src   # Type check
```

### Database (apps/api)

```bash
uv run alembic revision --autogenerate -m "msg"  # Create migration
uv run alembic upgrade head                       # Apply migrations
uv run alembic downgrade -1                       # Rollback one
```

### Infrastructure (terraform)

```bash
terraform init                              # Initialize
terraform plan -var-file=prod.tfvars        # Plan changes
terraform apply -var-file=prod.tfvars       # Apply changes
```

---

_Generated from codebase structure. Update when adding major new modules or restructuring._
