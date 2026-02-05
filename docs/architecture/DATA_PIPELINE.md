# Data Pipeline

> Automated data ingestion and processing system that powers TrainerLab's competitive intelligence.

## Overview

TrainerLab uses a two-phase pipeline architecture. Cloud Scheduler triggers discovery jobs that identify new tournaments, then Cloud Tasks queues individual tournament processing at a controlled rate. Card sync and meta computation run on their own schedules.

## Diagram

```mermaid
flowchart TB
    subgraph Scheduler["Cloud Scheduler Jobs"]
        DiscoverEN["discover-en<br/>Daily 6 AM UTC"]
        DiscoverJP["discover-jp<br/>Daily 7 AM UTC"]
        ComputeMeta["compute-meta<br/>Daily 8 AM UTC"]
        SyncCards["sync-cards<br/>Sunday 3 AM UTC"]
        SyncMappings["sync-card-mappings<br/>Sunday 4 AM UTC"]
    end

    subgraph External["External Data Sources"]
        Limitless["Limitless TCG API"]
        TCGdex["TCGdex API"]
    end

    subgraph API["FastAPI Pipeline Endpoints"]
        PipelineEN["/api/v1/pipeline/discover-en"]
        PipelineJP["/api/v1/pipeline/discover-jp"]
        PipelineProcess["/api/v1/pipeline/process-tournament"]
        PipelineMeta["/api/v1/pipeline/compute-meta"]
        PipelineCards["/api/v1/pipeline/sync-cards"]
        PipelineMappings["/api/v1/pipeline/sync-card-mappings"]
    end

    subgraph Queue["Cloud Tasks"]
        TaskQueue["Tournament Queue<br/>0.5/sec, 2 concurrent"]
    end

    subgraph Services["Pipeline Services"]
        Scraper["tournament_scrape.py<br/>Scrape & parse tournaments"]
        CloudTasksSvc["cloud_tasks.py<br/>Enqueue tournament tasks"]
        Archetype["archetype_detector.py<br/>Classify deck archetypes"]
        MetaCalc["meta_service.py<br/>Compute snapshots & tiers"]
        CardSync["card_sync.py<br/>Sync card data"]
        CardMappings["sync_card_mappings.py<br/>JP↔EN card IDs"]
    end

    subgraph Database["PostgreSQL Database"]
        Tournaments[("Tournaments<br/>+ Placements")]
        MetaSnapshots[("Meta Snapshots<br/>EN + JP")]
        Cards[("Cards<br/>+ Embeddings")]
        CardIdMappings[("Card ID Mappings<br/>JP↔EN")]
    end

    subgraph Output["Computed Intelligence"]
        Tiers["Tier Rankings<br/>S/A/B/C/Rogue"]
        JPSignals["JP Signals<br/>Divergence Detection"]
        Trends["Meta Trends<br/>Historical Analysis"]
    end

    %% Scheduler to API (Phase 1: Discovery)
    DiscoverEN -->|"OIDC"| PipelineEN
    DiscoverJP -->|"OIDC"| PipelineJP
    ComputeMeta -->|"OIDC"| PipelineMeta
    SyncCards -->|"OIDC"| PipelineCards
    SyncMappings -->|"OIDC"| PipelineMappings

    %% Discovery enqueues to Cloud Tasks
    PipelineEN --> CloudTasksSvc
    PipelineJP --> CloudTasksSvc
    CloudTasksSvc -->|"Enqueue"| TaskQueue

    %% Cloud Tasks triggers processing (Phase 2: Processing)
    TaskQueue -->|"POST"| PipelineProcess
    PipelineProcess --> Scraper

    %% Other pipelines
    PipelineMeta --> MetaCalc
    PipelineCards --> CardSync
    PipelineMappings --> CardMappings

    %% External data
    Scraper -->|"Fetch"| Limitless
    CardMappings -->|"Fetch"| Limitless
    CardSync -->|"Fetch"| TCGdex

    %% Service processing
    Scraper --> Archetype
    Archetype --> Tournaments
    MetaCalc --> MetaSnapshots
    CardSync --> Cards
    CardMappings --> CardIdMappings

    %% Output generation
    MetaSnapshots --> Tiers
    MetaSnapshots --> JPSignals
    MetaSnapshots --> Trends

    %% Styling
    classDef scheduler fill:#4285f4,stroke:#1a73e8,color:#fff
    classDef external fill:#34a853,stroke:#1e8e3e,color:#fff
    classDef api fill:#ea4335,stroke:#c5221f,color:#fff
    classDef queue fill:#ff6d01,stroke:#e65100,color:#fff
    classDef service fill:#fbbc04,stroke:#f9ab00,color:#000
    classDef db fill:#9334e6,stroke:#7627bb,color:#fff
    classDef output fill:#00bcd4,stroke:#0097a7,color:#fff

    class DiscoverEN,DiscoverJP,ComputeMeta,SyncCards scheduler
    class Limitless,TCGdex external
    class PipelineEN,PipelineJP,PipelineProcess,PipelineMeta,PipelineCards api
    class TaskQueue queue
    class Scraper,CloudTasksSvc,Archetype,MetaCalc,CardSync service
    class Tournaments,MetaSnapshots,Cards db
    class Tiers,JPSignals,Trends output
```

## Key Components

| Component              | Description                                                                        |
| ---------------------- | ---------------------------------------------------------------------------------- |
| **discover-en**        | Discovers new English/international tournaments from Limitless (7-day lookback)    |
| **discover-jp**        | Discovers new Japanese tournaments with BO1 context (7-day lookback)               |
| **Cloud Tasks**        | Queues individual tournaments for processing (rate-limited 0.5/sec, 2 concurrent)  |
| **process-tournament** | Processes a single tournament: scrapes placements, detects archetypes, stores data |
| **compute-meta**       | Calculates meta shares, tier assignments, JP signals (90-day window)               |
| **sync-cards**         | Synchronizes card data and generates embeddings from TCGdex                        |
| **archetype_detector** | Identifies deck archetypes using signature card patterns                           |
| **Meta Snapshots**     | Daily aggregated meta share data, separated by region                              |

## Pipeline Schedule

| Job                | Schedule    | Timezone | Purpose                       |
| ------------------ | ----------- | -------- | ----------------------------- |
| discover-en        | `0 6 * * *` | UTC      | Discover new EN tournaments   |
| discover-jp        | `0 7 * * *` | UTC      | Discover new JP tournaments   |
| compute-meta       | `0 8 * * *` | UTC      | After all processing finishes |
| sync-cards         | `0 3 * * 0` | UTC      | Weekly during low traffic     |
| sync-card-mappings | `0 4 * * 0` | UTC      | JP↔EN card ID mapping sync    |

## Notes

- Two-phase architecture: discovery jobs find new tournaments, Cloud Tasks queues individual processing
- Cloud Tasks rate-limits processing at 0.5 requests/sec with 2 concurrent dispatches to avoid overwhelming Limitless
- Each job has retry logic: 3 attempts with exponential backoff (30s-300s)
- JP data processing accounts for BO1 format (ties count as double losses)
- Archetype detection uses a curated signature card mapping maintained in `data/`
- All pipeline endpoints require OIDC authentication from the scheduler service account or Cloud Tasks
