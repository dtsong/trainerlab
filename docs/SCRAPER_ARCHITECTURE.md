# Scraper Architecture

How tournament data flows from Limitless into TrainerLab.

## Data Sources

There are **two separate Limitless websites** with different data:

| Source          | URL                                                     | What it has                          | Used by       |
| --------------- | ------------------------------------------------------- | ------------------------------------ | ------------- |
| **Official DB** | `limitlesstcg.com/tournaments`                          | Regionals, ICs, Worlds (all regions) | `discover-en` |
| **Official JP** | `limitlesstcg.com/tournaments/jp`                       | Japanese City Leagues (BO1)          | `discover-jp` |
| **Grassroots**  | `play.limitlesstcg.com/tournaments/completed?game=PTCG` | Community-run online events          | `discover-en` |

> **Weighting note:** Official tournament data should carry heavier weight for
> evaluating the competitive format. Grassroots data is useful for tracking how
> community meta trends influence major tournament metagame share.

## Pipeline Overview

```mermaid
flowchart TD
    subgraph triggers["Cloud Scheduler (daily/weekly)"]
        T1[trainerlab-sync-cards]
        T2[trainerlab-sync-card-mappings]
        T3[trainerlab-discover-en]
        T4[trainerlab-discover-jp]
        T5[trainerlab-compute-meta]
    end

    subgraph api["Cloud Run — FastAPI"]
        P1[POST /pipeline/sync-cards]
        P2[POST /pipeline/sync-card-mappings]
        P3[POST /pipeline/discover-en]
        P4[POST /pipeline/discover-jp]
        P5[POST /pipeline/process-tournament]
        P6[POST /pipeline/compute-meta]
    end

    subgraph tasks["Cloud Tasks"]
        Q1[Tournament queue]
    end

    T1 -->|OIDC token| P1
    T2 -->|OIDC token| P2
    T3 -->|OIDC token| P3
    T4 -->|OIDC token| P4
    T5 -->|OIDC token| P6

    P1 --> sync[sync_english_cards]
    P2 --> mappings[sync_card_mappings]
    P3 --> enqueue1[enqueue tournament tasks]
    P4 --> enqueue2[enqueue tournament tasks]
    enqueue1 --> Q1
    enqueue2 --> Q1
    Q1 -->|OIDC token| P5
    P5 --> scrape[process_tournament_by_url]
    P6 --> meta[compute_daily_snapshots]

    sync -->|TCGdex API| DB[(PostgreSQL)]
    mappings --> DB
    scrape --> DB
    meta -->|reads tournaments| DB
    meta -->|writes snapshots| DB
```

## Discovery + Processing Detail

```mermaid
flowchart LR
    subgraph discover_en["discover-en pipeline"]
        direction TB
        EN_G[Grassroots scraper]
        EN_O[Official scraper]
        EN_G -->|play.limitlesstcg.com| listings1[Tournament listings]
        EN_O -->|limitlesstcg.com/tournaments| listings2[Tournament listings]
        listings1 --> dedup1{Already in DB?}
        listings2 --> dedup2{Already in DB?}
        dedup1 -->|No| enqueue1[Enqueue task]
        dedup2 -->|No| enqueue2[Enqueue task]
    end

    subgraph discover_jp["discover-jp pipeline"]
        direction TB
        JP_CL[City League scraper]
        JP_CL -->|limitlesstcg.com/tournaments/jp| listings3[Tournament listings]
        listings3 --> dedup3{Already in DB?}
        dedup3 -->|No| enqueue3[Enqueue task]
    end

    subgraph process["process-tournament pipeline"]
        direction TB
        task[Cloud Task payload]
        task --> placements[Fetch placements]
        placements --> decks[Fetch decklists]
        decks --> save[Save to DB]
    end

    enqueue1 --> task
    enqueue2 --> task
    enqueue3 --> task
```

## Key Files

```
apps/api/src/
  routers/pipeline.py              # POST endpoints (entry points)
  pipelines/
    scrape_limitless.py            # Discovery + processing orchestration (EN + JP)
    compute_meta.py                # Meta snapshot computation
    sync_cards.py                  # TCGdex card sync
    sync_card_mappings.py          # JP↔EN card ID mapping sync
  services/
    cloud_tasks.py                 # Cloud Tasks enqueue logic
    tournament_scrape.py           # Scrape + save logic (TournamentScrapeService)
  clients/
    limitless.py                   # HTTP client for both Limitless sites
  models/
    tournament.py                  # Tournament + TournamentPlacement models
    card_id_mapping.py             # JP↔EN card ID mapping table
```

## Call Chain

### discover-en

```
POST /pipeline/discover-en
  -> discover_en_tournaments()                         # scrape_limitless.py
    -> TournamentScrapeService.discover_new_tournaments(region="en")
      -> LimitlessClient.fetch_tournament_listings()    # play.limitlesstcg.com
    -> TournamentScrapeService.discover_official_tournaments()
      -> LimitlessClient.fetch_official_tournament_listings() # limitlesstcg.com
    -> CloudTasksService.enqueue_tournament()
```

### discover-jp

```
POST /pipeline/discover-jp
  -> discover_jp_tournaments()                         # scrape_limitless.py
    -> TournamentScrapeService.discover_jp_city_leagues()
      -> LimitlessClient.fetch_jp_city_league_listings()      # limitlesstcg.com/tournaments/jp
    -> CloudTasksService.enqueue_tournament()
```

### process-tournament (Cloud Tasks)

```
POST /pipeline/process-tournament
  -> process_single_tournament()                        # scrape_limitless.py
    -> TournamentScrapeService.process_tournament_by_url()
      -> LimitlessClient.fetch_*_placements()
      -> LimitlessClient.fetch_decklist()
      -> save_tournament()
```

## Data Model

```mermaid
erDiagram
    Tournament {
        uuid id PK
        string name
        date date
        string region "NA, EU, JP, LATAM, OCE, APAC"
        string format "standard, expanded"
        int best_of "3 for intl, 1 for JP"
        int participant_count
        string source_url
    }
    TournamentPlacement {
        uuid id PK
        uuid tournament_id FK
        int placement
        string player_name
        string archetype
        json decklist
        string decklist_source
    }
    MetaSnapshot {
        uuid id PK
        date snapshot_date
        string region
        string format
        int best_of
        json archetypes
    }

    Tournament ||--o{ TournamentPlacement : "has"
    Tournament }o--|| MetaSnapshot : "feeds into"
```

## Region Handling

| Region             | Source                      | best_of | Page                                     |
| ------------------ | --------------------------- | ------- | ---------------------------------------- |
| NA, EU, LATAM, OCE | Official + Grassroots       | 3       | `/tournaments` + `play.limitlesstcg.com` |
| JP                 | City Leagues                | 1       | `/tournaments/jp`                        |
| APAC               | Official (KR, TW, SG, etc.) | 3       | `/tournaments`                           |

The EN pipeline's official scraper maps country codes to regions via `_country_to_region()`.
JP tournaments are always BO1 (ties = double loss).

## Tool Radar

Tools evaluated for potential adoption. Not currently in use.

| Tool                               | What It Does                                                                                                                                                                                            | When to Revisit                                                                         | Evaluated  |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- | ---------- |
| [Kernel.sh](https://www.kernel.sh) | Browsers-as-a-Service (cloud headless browsers via CDP). Headless at $0.06/hr, free tier includes $5/mo credits and 5 concurrent sessions. Supports Playwright/Puppeteer, residential proxies included. | If target sites add JS rendering, Cloudflare/bot protection, or we need to scrape SPAs. | 2026-02-22 |
