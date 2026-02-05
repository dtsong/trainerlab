# TrainerLab Codemap

> Last updated: 2026-02-02
> Purpose: Quick reference for code navigation and token-efficient context

---

## Repository Structure

```
trainerlab/
├── apps/
│   ├── api/          # FastAPI backend (Python)
│   └── web/          # Next.js frontend (TypeScript)
├── packages/
│   └── shared-types/ # Shared TypeScript types
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
│   └── scheduler_auth.py     # Cloud Scheduler auth dependency
├── models/                   # SQLAlchemy ORM models (14 files)
├── schemas/                  # Pydantic request/response schemas (12 files)
├── routers/                  # API endpoint definitions (12 files)
├── services/                 # Business logic (12 files)
├── pipelines/                # Data pipeline jobs (3 files)
├── clients/                  # External API clients (2 files)
├── data/                     # Static data (signature cards)
└── fixtures/                 # Test data
```

### Database Models (`models/`)

| Model               | File                      | Purpose                   |
| ------------------- | ------------------------- | ------------------------- |
| User                | `user.py`                 | User accounts             |
| Deck                | `deck.py`                 | User decks                |
| Card                | `card.py`                 | TCG card data             |
| Set                 | `set.py`                  | Card sets                 |
| Tournament          | `tournament.py`           | Tournament metadata       |
| TournamentPlacement | `tournament_placement.py` | Tournament results        |
| MetaSnapshot        | `meta_snapshot.py`        | Meta share aggregations   |
| LabNote             | `lab_note.py`             | Content articles          |
| Waitlist            | `waitlist.py`             | Email signups             |
| FormatConfig        | `format_config.py`        | Format rotation dates     |
| RotationImpact      | `rotation_impact.py`      | Card rotation analysis    |
| JPCardInnovation    | `jp_card_innovation.py`   | Japanese card tracking    |
| JPNewArchetype      | `jp_new_archetype.py`     | New JP archetypes         |
| JPSetImpact         | `jp_set_impact.py`        | JP set impact predictions |
| Prediction          | `prediction.py`           | Meta predictions          |

### API Routers (`routers/`)

| Router           | Prefix                | Key Endpoints                                                              |
| ---------------- | --------------------- | -------------------------------------------------------------------------- |
| `health.py`      | `/api/v1/health`      | Health check                                                               |
| `cards.py`       | `/api/v1/cards`       | GET /, GET /{id}, Search with embeddings                                   |
| `sets.py`        | `/api/v1/sets`        | GET /, GET /{id}                                                           |
| `decks.py`       | `/api/v1/decks`       | CRUD operations, export/import                                             |
| `meta.py`        | `/api/v1/meta`        | GET /current, GET /history, GET /archetypes                                |
| `tournaments.py` | `/api/v1/tournaments` | GET /, GET /{id}, Filter + paginate                                        |
| `japan.py`       | `/api/v1/japan`       | JP-specific endpoints (innovation, archetypes, sets, predictions)          |
| `lab_notes.py`   | `/api/v1/lab-notes`   | GET /, GET /{slug}                                                         |
| `waitlist.py`    | `/api/v1/waitlist`    | POST /                                                                     |
| `format.py`      | `/api/v1/format`      | GET /current, GET /rotations, GET /rotation-impact                         |
| `users.py`       | `/api/v1/users`       | GET /me, PUT /me                                                           |
| `pipeline.py`    | `/api/v1/pipeline`    | POST /discover-_, POST /process-tournament, POST /compute-_, POST /sync-\* |

### Services (`services/`)

| Service                 | Purpose                                        |
| ----------------------- | ---------------------------------------------- |
| `card_service.py`       | Card search with vector embeddings             |
| `card_sync.py`          | Sync cards from TCGdex API                     |
| `set_service.py`        | Set management                                 |
| `deck_service.py`       | Deck CRUD operations                           |
| `deck_import.py`        | Import from PTCGO/Limitless/TCGONEgame formats |
| `deck_export.py`        | Export to PTCGO format                         |
| `meta_service.py`       | Meta snapshot queries                          |
| `tournament_scrape.py`  | Scrape Limitless tournament data               |
| `archetype_detector.py` | Detect deck archetype from signature cards     |
| `lab_note_service.py`   | Lab notes CRUD                                 |
| `usage_service.py`      | Deck usage analytics                           |
| `user_service.py`       | User management                                |

### Pipelines (`pipelines/`)

| Pipeline                | Trigger               | Purpose                                             |
| ----------------------- | --------------------- | --------------------------------------------------- |
| `scrape_limitless.py`   | Daily 6am/7am UTC     | Discover + process EN/JP tournaments from Limitless |
| `compute_meta.py`       | Daily 8am UTC         | Compute meta snapshots, JP signals, tiers           |
| `sync_cards.py`         | Weekly Sunday 3am UTC | Sync cards from TCGdex                              |
| `sync_card_mappings.py` | Weekly Sunday 4am UTC | Sync JP↔EN card ID mappings                         |

### External Clients (`clients/`)

- `tcgdex.py` - TCGdex API client (card data)
- `limitless.py` - Limitless API client (tournament data)

### Database Migrations

- **Location:** `alembic/versions/`
- **Count:** ~14 migrations
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

**Custom TrainerLab components (10):**

- `pill-toggle.tsx` - Filter toggle group
- `section-label.tsx` - Mono label with icon + divider
- `tier-badge.tsx` - S/A/B/C/Rogue badges with colors
- `trend-arrow.tsx` - Up/down/stable indicators
- `jp-signal-badge.tsx` - JP divergence badge (red)
- `stat-block.tsx` - Large mono numbers with labels
- `panel-overlay.tsx` - Dark overlay for slide-outs

#### Domain Components

**Cards (`components/cards/`):**

- CardSearchInput, CardFilters, MobileCardFilters, CardGrid, CardDetail, CardImage, CardFiltersSkeleton, CardGridSkeleton

**Deck Builder (`components/deck/`):**

- DeckBuilder, DeckList, DeckListItem, DeckCard, DeckStats, DeckValidation, DeckImportModal, DeckExportModal, DeckCardSkeleton

**Meta Dashboard (`components/meta/`):**

- FilterBar, HealthIndicators, TierList, ArchetypeCard, ArchetypePanel, MatchupSpread, BuildItBanner, RegionFilter, DateRangePicker, MetaBarChart, MetaPieChart, MetaTrendChart, ChartErrorBoundary, BO1ContextBanner, ChartSkeleton, ArchetypeCardSkeleton

**Home Page (`components/home/`):**

- Hero, JPAlertBanner, MetaSnapshot, EvolutionPreview, ContentGrid, JPPreview, WhyTrainerLab, ResearchPassWaitlist, TrainersToolkit

**Japan (`components/japan/`):**

- PredictionAccuracyTracker, CardInnovationTracker, NewArchetypeWatch, SetImpactTimeline

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

| Hook             | Purpose                   |
| ---------------- | ------------------------- |
| `useAuth`        | NextAuth.js session state |
| `useCards`       | Card search queries       |
| `useSets`        | Card set queries          |
| `useDecks`       | Deck CRUD operations      |
| `useTournaments` | Tournament queries        |
| `useLabNotes`    | Lab notes queries         |
| `useJapan`       | Japan-specific queries    |
| `useFormat`      | Format rotation queries   |

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
4. **JP Comparison:** Frontend → API `/meta/current?region=JP` + `/meta/current?region=Global` → Side-by-side
5. **Tournament Browse:** Frontend → API `/tournaments?filter=...` → Paginated results

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
# src/services/archetype_detector.py
# Maps signature cards (e.g., "sv4-125") → archetype name
# Scans decklist for known signature cards
# Returns archetype name or "Rogue"
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
- **Cloud:** GCP (Cloud Run, Cloud SQL, Cloud Scheduler)

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
