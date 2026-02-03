# Application Layers

> Internal architecture showing clean separation of concerns across frontend and backend.

## Overview

TrainerLab follows a layered architecture pattern with clear boundaries between presentation, business logic, and data access. The frontend uses React with modern state management, while the backend follows a service-oriented architecture with dedicated layers for routing, business logic, and data persistence.

## Diagram

```mermaid
flowchart TB
    subgraph Frontend["Frontend (apps/web)"]
        subgraph AppRouter["App Router"]
            Pages["Pages<br/>15 routes"]
        end

        subgraph Components["Components (81 total)"]
            UI["UI Primitives<br/>27 components"]
            Domain["Domain Components<br/>54 components"]
        end

        subgraph Hooks["Custom Hooks (8)"]
            DataHooks["useCards, useDecks<br/>useMeta, useTournaments<br/>useJapan, useFormat<br/>useLabNotes, useSets"]
        end

        subgraph State["State Management"]
            ReactQuery["React Query<br/>Server State"]
            Zustand["Zustand<br/>Deck Builder"]
            Context["Auth Context<br/>NextAuth.js"]
        end
    end

    subgraph SharedTypes["Shared Types (packages/shared-types)"]
        Types["Card, Deck, Meta<br/>Tournament, Japan<br/>Format, LabNote"]
    end

    subgraph Backend["Backend (apps/api)"]
        subgraph Routers["Routers (12)"]
            APIRoutes["health, cards, sets<br/>decks, meta, tournaments<br/>japan, lab-notes, waitlist<br/>format, users, pipeline"]
        end

        subgraph Services["Services (12)"]
            BusinessLogic["card_service, deck_service<br/>meta_service, user_service<br/>tournament_scrape, archetype_detector<br/>card_sync, lab_note_service<br/>deck_import, deck_export<br/>set_service, usage_service"]
        end

        subgraph Models["Models (14)"]
            ORM["User, Deck, Card, Set<br/>Tournament, TournamentPlacement<br/>MetaSnapshot, LabNote<br/>Waitlist, FormatConfig<br/>RotationImpact, JPCardInnovation<br/>JPNewArchetype, JPSetImpact<br/>Prediction"]
        end

        subgraph Clients["External Clients"]
            LimitlessClient["limitless.py"]
            TCGdexClient["tcgdex.py"]
        end
    end

    subgraph Database["Database Layer"]
        SQLAlchemy["SQLAlchemy ORM"]
        PostgreSQL[("PostgreSQL 16<br/>+ pgvector")]
    end

    subgraph External["External APIs"]
        Limitless["Limitless TCG"]
        TCGdex["TCGdex"]
    end

    %% Frontend flow
    Pages --> Components
    Components --> Hooks
    Hooks --> State
    State -->|"API Calls"| Routers

    %% Shared types
    State -.->|"Types"| SharedTypes
    Routers -.->|"Types"| SharedTypes

    %% Backend flow
    Routers --> Services
    Services --> Models
    Services --> Clients
    Models --> SQLAlchemy
    SQLAlchemy --> PostgreSQL

    %% External
    Clients --> Limitless
    Clients --> TCGdex

    %% Styling
    classDef frontend fill:#ea4335,stroke:#c5221f,color:#fff
    classDef backend fill:#4285f4,stroke:#1a73e8,color:#fff
    classDef shared fill:#fbbc04,stroke:#f9ab00,color:#000
    classDef db fill:#9334e6,stroke:#7627bb,color:#fff
    classDef external fill:#34a853,stroke:#1e8e3e,color:#fff

    class Pages,Components,UI,Domain,Hooks,DataHooks,State,ReactQuery,Zustand,Context frontend
    class Routers,APIRoutes,Services,BusinessLogic,Models,ORM,Clients,LimitlessClient,TCGdexClient backend
    class Types,SharedTypes shared
    class SQLAlchemy,PostgreSQL db
    class Limitless,TCGdex external
```

## Key Components

| Layer          | Count | Description                          |
| -------------- | ----- | ------------------------------------ |
| **Pages**      | 15    | Next.js App Router page components   |
| **Components** | 81    | React components (27 UI + 54 domain) |
| **Hooks**      | 8     | Custom React hooks for data fetching |
| **Routers**    | 12    | FastAPI endpoint groups              |
| **Services**   | 12    | Business logic implementations       |
| **Models**     | 14    | SQLAlchemy ORM models                |
| **Clients**    | 2     | External API integrations            |

## Frontend Component Breakdown

| Domain      | Components | Purpose                       |
| ----------- | ---------- | ----------------------------- |
| ui          | 27         | shadcn/ui + custom primitives |
| meta        | 16         | Meta dashboard visualizations |
| deck        | 9          | Deck builder interface        |
| home        | 9          | Landing page sections         |
| cards       | 7          | Card search and display       |
| layout      | 7          | Navigation and structure      |
| japan       | 4          | JP-specific intelligence      |
| rotation    | 4          | Format rotation tracking      |
| auth        | 2          | Login/register forms          |
| tournaments | 2          | Tournament browsing           |
| lab-notes   | 2          | Content articles              |
| commerce    | 1          | Affiliate CTAs                |

## Notes

- Frontend uses React Query for server state caching and Zustand for local UI state
- Backend follows dependency injection pattern via FastAPI's `Depends()`
- Shared types package ensures type consistency between frontend and backend
- All database access goes through SQLAlchemy ORM with async support
- External clients are isolated to allow easy mocking in tests
