# Scripts Reference

Quick reference for all operational scripts in the TrainerLab project.

## Shell Scripts (`scripts/`)

### verify-pipelines.sh

Triggers Cloud Scheduler pipelines and verifies data existence via API.

```bash
./scripts/cloud/verify-pipelines.sh [OPTIONS]
```

| Option          | Description                    |
| --------------- | ------------------------------ |
| `--step=N`      | Run specific step (1-13)       |
| `--verify-only` | Skip triggers, just check data |
| `-h, --help`    | Show help                      |

**Steps:**

| Step | Pipeline             | Verifies                                  |
| ---- | -------------------- | ----------------------------------------- |
| 1    | sync-cards           | Card count > 0                            |
| 2    | sync-jp-cards        | Card API remains healthy after JP sync    |
| 3    | sync-card-mappings   | Mapping sync job completed                |
| 4    | sync-events          | Scheduler trigger + completion            |
| 5    | discover-en          | Tournament count > 0                      |
| 6    | discover-jp          | JP tournament count > 0                   |
| 7    | compute-meta         | Meta archetypes present                   |
| 8    | compute-evolution    | Evolution pipeline completes              |
| 9    | translate-pokecabook | Translation pipeline completes            |
| 10   | sync-jp-adoption     | JP innovation/adoption API data available |
| 11   | translate-tier-lists | Tier list translation pipeline completes  |
| 12   | monitor-card-reveals | Card reveal monitor pipeline completes    |
| 13   | cleanup-exports      | Export cleanup pipeline completes         |

**Prerequisites:** gcloud CLI, jq, authenticated GCP session

### test-production-scrapers.sh

Manually triggers production pipelines via Cloud Scheduler. Writes to the production database.

```bash
./scripts/cloud/test-production-scrapers.sh [OPTIONS]
```

| Option            | Description                                                                                                                                                       |
| ----------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--pipeline=NAME` | Run specific pipeline from scheduler jobs (e.g. `discover-en`, `discover-jp`, `compute-meta`, `sync-cards`, `sync-jp-cards`, `sync-card-mappings`, `sync-events`) |
| `--all`           | Run all pipelines (triggered in parallel)                                                                                                                         |
| `--confirm`       | **Required** — acknowledge production DB writes                                                                                                                   |
| `--verify`        | Verify results after execution                                                                                                                                    |
| `--check-logs`    | Check Cloud Logs for recent errors (no execution)                                                                                                                 |
| `-h, --help`      | Show help                                                                                                                                                         |

**Safety:** Requires `--confirm` flag because it writes to the production database.

**Prerequisites:** gcloud CLI, jq, authenticated GCP session

### verify-data.sh

Deep data quality verification across all API endpoints. Validates response shapes, field presence, data ranges, and cross-entity consistency.

```bash
./scripts/verify-data.sh [OPTIONS]
```

| Option          | Description                                                                               |
| --------------- | ----------------------------------------------------------------------------------------- |
| `--group=NAME`  | Run specific group: `cards`, `sets`, `tournaments`, `meta`, `japan`, `format`, `frontend` |
| `--api-url=URL` | Override API URL (default: auto-detect from Cloud Run)                                    |
| `--local`       | Use `localhost:8000` (no auth)                                                            |
| `-h, --help`    | Show help                                                                                 |

**Verification groups:**

| Group       | What it checks                                                  |
| ----------- | --------------------------------------------------------------- |
| cards       | Pagination shape, required fields, fuzzy search                 |
| sets        | Non-empty list, required fields per set                         |
| tournaments | Pagination, JP filter, freshness (last 14 days)                 |
| meta        | Archetype shares sum to ~1.0, diversity index, tier assignments |
| japan       | JP meta snapshot, innovation adoption rates, new archetypes     |
| format      | Current format config, rotation impact data                     |
| frontend    | Exact fields that frontend hooks destructure                    |

**Prerequisites:** gcloud CLI (or `--local` for dev), jq

## Python Scripts (`apps/api/scripts/`)

### seed-tournaments.py

Seeds tournament data from JSON fixtures into the database.

```bash
cd apps/api && uv run scripts/seed-tournaments.py [OPTIONS]
```

| Option      | Description                        |
| ----------- | ---------------------------------- |
| `--dry-run` | Preview changes without writing    |
| `--clear`   | Clear existing data before seeding |
| `--verbose` | Enable verbose logging             |

**Fixtures:** `apps/api/fixtures/tournaments.json`

### seed-formats.py

Seeds format configuration data from JSON fixtures into the database.

```bash
cd apps/api && uv run scripts/seed-formats.py [OPTIONS]
```

| Option      | Description                        |
| ----------- | ---------------------------------- |
| `--dry-run` | Preview changes without writing    |
| `--clear`   | Clear existing data before seeding |
| `--verbose` | Enable verbose logging             |

**Fixtures:** `apps/api/fixtures/formats.json`

### sync-cards.py

Syncs card data from TCGdex into the database.

```bash
cd apps/api && uv run scripts/sync-cards.py [OPTIONS]
```

| Option            | Description                     |
| ----------------- | ------------------------------- |
| `--english-only`  | Sync English cards only         |
| `--japanese-only` | Sync Japanese names only        |
| `--dry-run`       | Preview changes without writing |
| `--verbose`       | Enable verbose logging          |

**Modes:** all (default), english, japanese
