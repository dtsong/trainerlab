# Scraper Architecture

How tournament data flows from Limitless into TrainerLab.

## Data Sources

There are **two separate Limitless websites** with different data:

| Source          | URL                                                     | What it has                          | Used by     |
| --------------- | ------------------------------------------------------- | ------------------------------------ | ----------- |
| **Official DB** | `limitlesstcg.com/tournaments`                          | Regionals, ICs, Worlds (all regions) | `scrape-en` |
| **Official JP** | `limitlesstcg.com/tournaments/jp`                       | Japanese City Leagues (BO1)          | `scrape-jp` |
| **Grassroots**  | `play.limitlesstcg.com/tournaments/completed?game=PTCG` | Community-run online events          | `scrape-en` |

> **Weighting note:** Official tournament data should carry heavier weight for
> evaluating the competitive format. Grassroots data is useful for tracking how
> community meta trends influence major tournament metagame share.

## Pipeline Overview

```mermaid
flowchart TD
    subgraph triggers["Cloud Scheduler (daily)"]
        T1[trainerlab-sync-cards]
        T2[trainerlab-scrape-en]
        T3[trainerlab-scrape-jp]
        T4[trainerlab-compute-meta]
    end

    subgraph api["Cloud Run — FastAPI"]
        P1[POST /pipeline/sync-cards]
        P2[POST /pipeline/scrape-en]
        P3[POST /pipeline/scrape-jp]
        P4[POST /pipeline/compute-meta]
    end

    T1 -->|OIDC token| P1
    T2 -->|OIDC token| P2
    T3 -->|OIDC token| P3
    T4 -->|OIDC token| P4

    P1 --> sync[sync_english_cards]
    P2 --> en[scrape_en_tournaments]
    P3 --> jp[scrape_jp_tournaments]
    P4 --> meta[compute_daily_snapshots]

    sync -->|TCGdex API| DB[(PostgreSQL)]
    en --> DB
    jp --> DB
    meta -->|reads tournaments| DB
    meta -->|writes snapshots| DB
```

## Scrape Pipeline Detail

```mermaid
flowchart LR
    subgraph en["scrape-en pipeline"]
        direction TB
        EN_G[Grassroots scraper]
        EN_O[Official scraper]
        EN_G -->|play.limitlesstcg.com| listings1[Tournament listings]
        EN_O -->|limitlesstcg.com/tournaments| listings2[Tournament listings]
        listings1 --> dedup1{Already in DB?}
        listings2 --> dedup2{Already in DB?}
        dedup1 -->|No| placements1[Fetch placements]
        dedup2 -->|No| placements2[Fetch placements]
        placements1 --> decks1[Fetch decklists]
        placements2 --> decks2[Fetch decklists]
        decks1 --> save1[Save to DB]
        decks2 --> save2[Save to DB]
    end

    subgraph jp["scrape-jp pipeline"]
        direction TB
        JP_CL[City League scraper]
        JP_CL -->|limitlesstcg.com/tournaments/jp| listings3[Tournament listings]
        listings3 --> dedup3{Already in DB?}
        dedup3 -->|No| placements3[Fetch placements]
        placements3 --> decks3[Fetch decklists]
        decks3 --> save3[Save to DB]
    end
```

## Key Files

```
apps/api/src/
  routers/pipeline.py              # POST endpoints (entry points)
  pipelines/
    scrape_limitless.py            # Pipeline orchestration (EN + JP)
    compute_meta.py                # Meta snapshot computation
    sync_cards.py                  # TCGdex card sync
  services/
    tournament_scrape.py           # Scrape + save logic (TournamentScrapeService)
  clients/
    limitless.py                   # HTTP client for both Limitless sites
  models/
    tournament.py                  # Tournament + TournamentPlacement models
```

## Call Chain

### scrape-en

```
POST /pipeline/scrape-en
  -> scrape_en_tournaments()                         # scrape_limitless.py
    -> TournamentScrapeService.scrape_new_tournaments(region="en")
      -> LimitlessClient.fetch_tournament_listings() # play.limitlesstcg.com
      -> LimitlessClient.fetch_tournament_placements()
      -> LimitlessClient.fetch_decklist()
      -> save_tournament()
    -> TournamentScrapeService.scrape_official_tournaments()
      -> LimitlessClient.fetch_official_tournament_listings()  # limitlesstcg.com
      -> LimitlessClient.fetch_official_tournament_placements()
      -> LimitlessClient.fetch_decklist()
      -> save_tournament()
```

### scrape-jp

```
POST /pipeline/scrape-jp
  -> scrape_jp_tournaments()                         # scrape_limitless.py
    -> TournamentScrapeService.scrape_jp_city_leagues()
      -> LimitlessClient.fetch_jp_city_league_listings()     # limitlesstcg.com/tournaments/jp
      -> LimitlessClient.fetch_jp_city_league_placements()   # reuses official placement parser
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
