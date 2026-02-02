# Data Pipeline

> Automated data ingestion and processing system that powers TrainerLab's competitive intelligence.

## Overview

TrainerLab uses Cloud Scheduler to orchestrate four automated pipelines that continuously gather tournament data, synchronize card information, and compute meta snapshots. The pipelines run sequentially each day, with card sync occurring weekly during low-traffic hours.

## Diagram

```mermaid
flowchart TB
    subgraph Scheduler["Cloud Scheduler Jobs"]
        ScrapeEN["scrape-en<br/>Daily 6 AM UTC"]
        ScrapeJP["scrape-jp<br/>Daily 7 AM UTC"]
        ComputeMeta["compute-meta<br/>Daily 8 AM UTC"]
        SyncCards["sync-cards<br/>Sunday 3 AM UTC"]
    end

    subgraph External["External Data Sources"]
        Limitless["Limitless TCG API"]
        TCGdex["TCGdex API"]
    end

    subgraph API["FastAPI Pipeline Endpoints"]
        PipelineEN["/api/v1/pipeline/scrape-en"]
        PipelineJP["/api/v1/pipeline/scrape-jp"]
        PipelineMeta["/api/v1/pipeline/compute-meta"]
        PipelineCards["/api/v1/pipeline/sync-cards"]
    end

    subgraph Services["Pipeline Services"]
        Scraper["tournament_scrape.py<br/>Scrape & parse tournaments"]
        Archetype["archetype_detector.py<br/>Classify deck archetypes"]
        MetaCalc["meta_service.py<br/>Compute snapshots & tiers"]
        CardSync["card_sync.py<br/>Sync card data"]
    end

    subgraph Database["PostgreSQL Database"]
        Tournaments[("Tournaments<br/>+ Placements")]
        MetaSnapshots[("Meta Snapshots<br/>EN + JP")]
        Cards[("Cards<br/>+ Embeddings")]
    end

    subgraph Output["Computed Intelligence"]
        Tiers["Tier Rankings<br/>S/A/B/C/Rogue"]
        JPSignals["JP Signals<br/>Divergence Detection"]
        Trends["Meta Trends<br/>Historical Analysis"]
    end

    %% Scheduler to API
    ScrapeEN -->|"OIDC"| PipelineEN
    ScrapeJP -->|"OIDC"| PipelineJP
    ComputeMeta -->|"OIDC"| PipelineMeta
    SyncCards -->|"OIDC"| PipelineCards

    %% API to Services
    PipelineEN --> Scraper
    PipelineJP --> Scraper
    PipelineMeta --> MetaCalc
    PipelineCards --> CardSync

    %% External data
    Scraper -->|"Fetch"| Limitless
    CardSync -->|"Fetch"| TCGdex

    %% Service processing
    Scraper --> Archetype
    Archetype --> Tournaments
    MetaCalc --> MetaSnapshots
    CardSync --> Cards

    %% Output generation
    MetaSnapshots --> Tiers
    MetaSnapshots --> JPSignals
    MetaSnapshots --> Trends

    %% Styling
    classDef scheduler fill:#4285f4,stroke:#1a73e8,color:#fff
    classDef external fill:#34a853,stroke:#1e8e3e,color:#fff
    classDef api fill:#ea4335,stroke:#c5221f,color:#fff
    classDef service fill:#fbbc04,stroke:#f9ab00,color:#000
    classDef db fill:#9334e6,stroke:#7627bb,color:#fff
    classDef output fill:#00bcd4,stroke:#0097a7,color:#fff

    class ScrapeEN,ScrapeJP,ComputeMeta,SyncCards scheduler
    class Limitless,TCGdex external
    class PipelineEN,PipelineJP,PipelineMeta,PipelineCards api
    class Scraper,Archetype,MetaCalc,CardSync service
    class Tournaments,MetaSnapshots,Cards db
    class Tiers,JPSignals,Trends output
```

## Key Components

| Component              | Description                                                               |
| ---------------------- | ------------------------------------------------------------------------- |
| **scrape-en**          | Scrapes English/international tournaments from Limitless (7-day lookback) |
| **scrape-jp**          | Scrapes Japanese tournaments with BO1 context (7-day lookback)            |
| **compute-meta**       | Calculates meta shares, tier assignments, JP signals (90-day window)      |
| **sync-cards**         | Synchronizes card data and generates embeddings from TCGdex               |
| **archetype_detector** | Identifies deck archetypes using signature card patterns                  |
| **Meta Snapshots**     | Daily aggregated meta share data, separated by region                     |

## Pipeline Schedule

| Job          | Schedule    | Timezone | Purpose                       |
| ------------ | ----------- | -------- | ----------------------------- |
| scrape-en    | `0 6 * * *` | UTC      | After EN tournaments complete |
| scrape-jp    | `0 7 * * *` | UTC      | After JP tournaments complete |
| compute-meta | `0 8 * * *` | UTC      | After all scraping finishes   |
| sync-cards   | `0 3 * * 0` | UTC      | Weekly during low traffic     |

## Notes

- Jobs execute sequentially to ensure data dependencies are met
- Each job has retry logic: 3 attempts with exponential backoff (30s-300s)
- JP data processing accounts for BO1 format (ties count as double losses)
- Archetype detection uses a curated signature card mapping maintained in `data/`
- All pipeline endpoints require OIDC authentication from the scheduler service account
