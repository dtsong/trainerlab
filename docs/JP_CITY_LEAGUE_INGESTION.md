# Japanese City League Deep Ingestion System

## Overview

This document specifies the implementation of a comprehensive data ingestion system for Japanese Pokemon TCG City League tournaments, enabling deep analysis of the post-rotation meta before it reaches international tournaments.

### Key Dates

- **November 28, 2025**: MEGA Dream EX release (ingestion start date)
- **January 23, 2026**: Nihil Zero release (major format shift)
- **March 2026**: SVI-ASC international legality
- **April 10, 2026**: Rotation to Temporal Forces - Perfect Order

### Data Sources

1. **LimitlessTCG JP** (`limitlesstcg.com/tournaments/jp`)
   - City League tournament listings
   - Tournament results and placements
   - Decklists (top 8-32)
   - Card equivalents (JP to EN mappings)

2. **Social Media Translation Accounts** (X/BlueSky)
   - Card translations from Japanese to English
   - LLM-powered parsing of translation threads
   - User-specified account monitoring

3. **TCGdex API** (self-hosted)
   - Released card data
   - Set information
   - Card images and attributes

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    Docker Compose Environment                    │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Database   │  │     API      │  │   Frontend   │          │
│  │  (PostgreSQL)│  │   (FastAPI)  │  │  (Next.js)   │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                  │                  │                 │
│  ┌──────▼──────────────────▼──────────────────▼───────┐         │
│  │              Ingestion Pipeline                     │         │
│  │  ┌─────────────────────────────────────────────┐   │         │
│  │  │ 1. Discover JP City Leagues                 │   │         │
│  │  │ 2. Fetch decklists (top 8-32)              │   │         │
│  │  │ 3. Map JP cards to EN equivalents          │   │         │
│  │  │ 4. Generate placeholders for unreleased    │   │         │
│  │  │ 5. Store enriched decklist data            │   │         │
│  │  └─────────────────────────────────────────────┘   │         │
│  └────────────────────────────────────────────────────┘         │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │           LLM Translation Fetcher                        │    │
│  │  ┌─────────────────────────────────────────────────┐    │    │
│  │  │ • Monitor X/BlueSky accounts                     │    │    │
│  │  │ • Parse translation threads                      │    │    │
│  │  │ • Extract card data (name, type, attacks)       │    │    │
│  │  │ • Store in PlaceholderCard table                │    │    │
│  │  └─────────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## Data Models

### PlaceholderCard

Stores unreleased JP cards with translated English data for archetype detection.

```python
class PlaceholderCard(Base):
    """Unreleased JP cards with English translations."""

    __tablename__ = "placeholder_cards"

    # Primary key
    id: Mapped[UUID] = mapped_column(primary_key=True)

    # Card identification
    jp_card_id: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    # Format: POR-XXX (Perfect Order + random 3-digit)
    en_card_id: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)

    # Names
    name_jp: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[str] = mapped_column(String(255), nullable=False)

    # Card attributes
    supertype: Mapped[str] = mapped_column(String(50), nullable=False)  # Pokemon, Trainer, Energy
    subtypes: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)  # Basic, Stage 1, V, etc.
    hp: Mapped[int | None] = mapped_column(Integer, nullable=True)
    types: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)  # Fire, Water, etc.

    # Attacks (for Pokemon cards)
    attacks: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)
    # Format: [{"name": "Photon Blaster", "cost": ["Lightning", "Colorless"], "damage": "120", "text": "..."}]

    # Set information
    set_code: Mapped[str] = mapped_column(String(50), nullable=False, default="POR")
    official_set_code: Mapped[str | None] = mapped_column(String(50), nullable=True)  # ME03

    # Status
    is_unreleased: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_released: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    released_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Source tracking
    source: Mapped[str] = mapped_column(String(50), nullable=False)  # "limitless", "llm_x", "llm_bluesky", "manual"
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)  # Link to original post
    source_account: Mapped[str | None] = mapped_column(String(255), nullable=True)  # @username

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
```

### Enhanced TournamentPlacement

Stores decklists with both JP and EN card IDs.

```python
class TournamentPlacement(Base):
    """Extended to include enriched decklist data."""

    # ... existing fields ...

    # Original decklist from Limitless
    decklist: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)
    # Format: [{"jp_card_id": "SV10-15", "card_id": "POR-042", "quantity": 3}]

    # Enriched decklist with full card details
    decklist_enriched: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)
    # Format: [{
    #   "card_id": "POR-042",
    #   "name": "Miraidon ex",
    #   "supertype": "Pokemon",
    #   "is_placeholder": true,
    #   "quantity": 3,
    #   "set_code": "POR"
    # }]

    decklist_source: Mapped[str | None] = mapped_column(Text, nullable=True)
```

### CardIdMapping (Enhanced)

Links JP card IDs to EN equivalents, including placeholders.

```python
class CardIdMapping(Base):
    """Extended to track synthetic mappings."""

    # ... existing fields ...

    is_synthetic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # True for auto-generated POR-XXX placeholders

    placeholder_card_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("placeholder_cards.id"), nullable=True
    )
    # Links to placeholder card details
```

## API Endpoints

### Admin Endpoints (Authentication Required)

#### `POST /api/v1/admin/placeholder-cards`

Manually add a placeholder card translation.

**Request Body:**

```json
{
  "jp_card_id": "SV10-15",
  "name_en": "Miraidon ex",
  "supertype": "Pokemon",
  "subtypes": ["Basic", "ex"],
  "hp": 220,
  "types": ["Lightning"],
  "attacks": [
    {
      "name": "Photon Blaster",
      "cost": ["Lightning", "Lightning", "Colorless"],
      "damage": "230",
      "text": "This Pokemon also does 30 damage to itself."
    }
  ],
  "source": "manual",
  "source_url": "https://x.com/trainer/status/1234567890"
}
```

**Response:**

```json
{
  "id": "uuid",
  "jp_card_id": "SV10-15",
  "en_card_id": "POR-042",
  "name_en": "Miraidon ex",
  "created_at": "2026-02-05T10:00:00Z"
}
```

#### `POST /api/v1/admin/placeholder-cards/batch`

Bulk import placeholder cards from JSON file.

**Request:**

- Content-Type: `multipart/form-data`
- File: `translations.json`

**File Format:**

```json
{
  "cards": [
    {
      "jp_card_id": "SV10-15",
      "name_en": "Miraidon ex",
      ...
    },
    {
      "jp_card_id": "SV10-16",
      "name_en": "Another Card",
      ...
    }
  ]
}
```

#### `GET /api/v1/admin/placeholder-cards`

List all placeholder cards with filtering.

**Query Parameters:**

- `is_unreleased` (bool): Filter by release status
- `set_code` (str): Filter by set (POR)
- `source` (str): Filter by source (limitless, llm_x, llm_bluesky, manual)
- `limit` (int): Pagination limit
- `offset` (int): Pagination offset

#### `POST /api/v1/admin/translations/fetch`

Trigger LLM fetch from X/BlueSky accounts.

**Request Body:**

```json
{
  "accounts": ["@cardtranslator", "@jptcgen"],
  "since_date": "2026-01-23",
  "dry_run": false
}
```

### Export Endpoints

#### `GET /api/v1/exports/decklists`

Export decklists as JSON or CSV.

**Query Parameters:**

- `start_date` (date): Filter from date (YYYY-MM-DD)
- `end_date` (date): Filter to date (YYYY-MM-DD)
- `region` (str): Tournament region (default: JP)
- `archetype` (str): Filter by archetype name
- `format` (str): Export format (json, csv)
- `include_placeholders` (bool): Include placeholder cards (default: true)

**Response (JSON):**

```json
{
  "total": 150,
  "decklists": [
    {
      "tournament_name": "Tokyo City League",
      "tournament_date": "2026-01-25",
      "placement": 1,
      "player_name": "Player Name",
      "archetype": "Miraidon Box",
      "cards": [
        {
          "card_id": "POR-042",
          "name": "Miraidon ex",
          "quantity": 3,
          "is_placeholder": true
        },
        {
          "card_id": "SVI-18",
          "name": "Some Card",
          "quantity": 4,
          "is_placeholder": false
        }
      ]
    }
  ]
}
```

#### `GET /api/v1/exports/card-usage`

Export aggregated card usage statistics.

**Query Parameters:**

- `start_date` (date): Required
- `end_date` (date): Required
- `group_by` (str): Aggregation level (day, week, archetype)
- `format` (str): json, csv

**Response (JSON):**

```json
{
  "aggregation": "day",
  "data": [
    {
      "date": "2026-01-23",
      "card_id": "POR-042",
      "card_name": "Miraidon ex",
      "is_placeholder": true,
      "total_decks": 45,
      "inclusion_rate": 0.85,
      "avg_copies": 3.2
    }
  ]
}
```

### Enhanced Pipeline Endpoints

#### `POST /api/v1/pipeline/discover-jp` (Enhanced)

Discover and optionally auto-process JP City Leagues.

**Enhanced Request Body:**

```json
{
  "lookback_days": 70,
  "auto_process": true,
  "max_auto_process": 200,
  "fetch_decklists": true,
  "min_placements": 8,
  "max_placements": 32,
  "generate_placeholders": true
}
```

**Response:**

```json
{
  "tournaments_discovered": 150,
  "tournaments_processed": 150,
  "decklists_saved": 2800,
  "placeholders_generated": 127,
  "errors": []
}
```

## Implementation Scripts

### Main Ingestion Script

**File:** `scripts/ingest-jp-deep.sh`

```bash
#!/bin/bash
set -e

# Configuration
START_DATE="${START_DATE:-2025-11-28}"
END_DATE="${END_DATE:-$(date +%Y-%m-%d)}"
API_URL="${API_URL:-http://localhost:8080}"

# Calculate days between dates
days_between() {
    local start=$1
    local end=$2
    echo $(( ($(date -d "$end" +%s) - $(date -d "$start" +%s)) / 86400 ))
}

LOOKBACK_DAYS=$(days_between "$START_DATE" "$END_DATE")

echo "🎯 Deep JP City League Ingestion"
echo "   Period: $START_DATE to $END_DATE ($LOOKBACK_DAYS days)"
echo "   API: $API_URL"
echo ""

# Step 1: Sync card mappings
echo "1️⃣ Syncing card mappings..."
curl -s -X POST "$API_URL/api/v1/pipeline/sync-card-mappings" \
  -H "Content-Type: application/json" \
  -d '{"recent_only": false}' | jq .

# Step 2: Monitor card reveals
echo "2️⃣ Fetching unreleased cards from Limitless..."
curl -s -X POST "$API_URL/api/v1/pipeline/monitor-card-reveals" \
  -H "Content-Type: application/json" \
  -d '{"dry_run": false}' | jq .

# Step 3: Generate placeholders
echo "3️⃣ Generating placeholder mappings..."
python scripts/generate-placeholders.py \
  --set-code="POR" \
  --official-code="ME03" \
  --start-date="$START_DATE"

# Step 4: Fetch LLM translations from X/BlueSky
echo "4️⃣ Fetching translations from social media..."
curl -s -X POST "$API_URL/api/v1/admin/translations/fetch" \
  -H "Content-Type: application/json" \
  -d '{
    "accounts": ["@account1", "@account2"],
    "since_date": "'$START_DATE'",
    "dry_run": false
  }' | jq .

# Step 5: Discover and process tournaments
echo "5️⃣ Discovering and processing JP City Leagues..."
curl -s -X POST "$API_URL/api/v1/pipeline/discover-jp" \
  -H "Content-Type: application/json" \
  -d '{
    "lookback_days": '$LOOKBACK_DAYS',
    "auto_process": true,
    "max_auto_process": 200,
    "fetch_decklists": true,
    "min_placements": 8,
    "max_placements": 32,
    "generate_placeholders": true
  }' | jq .

# Step 6: Compute meta snapshots
echo "6️⃣ Computing daily meta snapshots..."
curl -s -X POST "$API_URL/api/v1/pipeline/compute-meta" \
  -H "Content-Type: application/json" \
  -d '{
    "regions": ["JP"],
    "formats": ["standard"],
    "best_of": [1],
    "lookback_days": 90
  }' | jq .

# Step 7: Verify completeness
echo "7️⃣ Verifying data completeness..."
./scripts/verify-jp-ingestion.sh --start-date="$START_DATE"

echo ""
echo "✅ Ingestion complete!"
echo "   Explore data: ./scripts/db-local.sh"
echo "   Export data: ./scripts/export-data.sh"
```

## Database Views

### View: `v_nihil_zero_impact`

Track card adoption before and after Nihil Zero release.

```sql
CREATE OR REPLACE VIEW v_nihil_zero_impact AS
WITH daily_stats AS (
  SELECT
    date_trunc('day', t.date) as day,
    card_entry->>'card_id' as card_id,
    c.name as card_name,
    pc.is_placeholder,
    COUNT(DISTINCT p.id) as deck_count,
    AVG((card_entry->>'quantity')::int) as avg_copies,
    COUNT(DISTINCT p.id)::float / NULLIF(
      (SELECT COUNT(DISTINCT p2.id)
       FROM tournament_placements p2
       JOIN tournaments t2 ON p2.tournament_id = t2.id
       WHERE date_trunc('day', t2.date) = date_trunc('day', t.date)),
      0
    ) as inclusion_rate
  FROM tournament_placements p
  JOIN tournaments t ON p.tournament_id = t.id
  LEFT JOIN LATERAL jsonb_array_elements(p.decklist) as card_entry ON true
  LEFT JOIN cards c ON card_entry->>'card_id' = c.id
  LEFT JOIN placeholder_cards pc ON card_entry->>'card_id' = pc.en_card_id
  WHERE t.region = 'JP'
    AND t.date >= '2025-11-28'
  GROUP BY 1, 2, 3, 4
)
SELECT
  day,
  card_id,
  card_name,
  is_placeholder,
  deck_count,
  avg_copies,
  inclusion_rate,
  CASE
    WHEN day < '2026-01-23'::date THEN 'pre_nihil_zero'
    ELSE 'post_nihil_zero'
  END as era
FROM daily_stats
ORDER BY day, deck_count DESC;
```

### View: `v_placeholder_usage`

Track usage of placeholder (unreleased) cards in JP meta.

```sql
CREATE OR REPLACE VIEW v_placeholder_usage AS
SELECT
  pc.en_card_id,
  pc.name_en,
  pc.name_jp,
  pc.jp_card_id,
  pc.set_code,
  COUNT(DISTINCT t.id) as tournament_count,
  COUNT(DISTINCT p.id) as deck_count,
  AVG(p.placement) as avg_placement,
  COUNT(DISTINCT p.archetype) as archetype_count,
  ARRAY_AGG(DISTINCT p.archetype) as archetypes,
  MIN(t.date) as first_seen,
  MAX(t.date) as last_seen
FROM placeholder_cards pc
LEFT JOIN LATERAL (
  SELECT * FROM tournament_placements
  WHERE decklist @> '[{"card_id": "' || pc.en_card_id || '"}]'
) p ON true
LEFT JOIN tournaments t ON p.tournament_id = t.id
WHERE pc.is_unreleased = true
GROUP BY pc.en_card_id, pc.name_en, pc.name_jp, pc.jp_card_id, pc.set_code
ORDER BY deck_count DESC;
```

## Usage Workflow

### One-Time Setup

```bash
# 1. Create environment file
cp .env.example .env
# Edit .env and add:
# ANTHROPIC_API_KEY=sk-ant-api03-...
# NEXTAUTH_SECRET=$(openssl rand -base64 32)

# 2. Start all services
docker-compose up -d

# 3. Wait for services to be healthy
docker-compose ps

# 4. Verify API is running
curl http://localhost:8080/api/v1/health
```

### Initial Data Ingestion

```bash
# Run complete ingestion (Nov 28, 2025 - present)
./scripts/ingest-jp-deep.sh

# Or with custom date range
START_DATE=2026-01-23 ./scripts/ingest-jp-deep.sh
```

### Daily Updates

```bash
# On-demand ingestion of latest tournaments
./scripts/ingest-jp-deep.sh

# Or trigger via API for specific date range
curl -X POST http://localhost:8080/api/v1/pipeline/discover-jp \
  -d '{
    "lookback_days": 7,
    "auto_process": true,
    "fetch_decklists": true
  }'
```

### Add Translations

```bash
# Option A: API submission
curl -X POST http://localhost:8080/api/v1/admin/placeholder-cards \
  -H "Content-Type: application/json" \
  -d @translation.json

# Option B: Batch file upload
curl -X POST http://localhost:8080/api/v1/admin/placeholder-cards/batch \
  -F "file=@translations_batch.json"

# Option C: Trigger LLM fetch from social media
curl -X POST http://localhost:8080/api/v1/admin/translations/fetch \
  -d '{
    "accounts": ["@cardtranslator", "@jptcgnews"],
    "since_date": "2026-01-23"
  }'
```

### Data Analysis

```bash
# Access database
./scripts/db-local.sh

# Run analysis queries
./scripts/db-local.sh -c "SELECT * FROM v_nihil_zero_impact LIMIT 10;"

# Or use Jupyter notebooks
open http://localhost:8888

# Export data for external analysis
./scripts/export-data.sh 2026-01-23 2026-02-05 json ./exports
```

---

_Last updated: February 5, 2026_
_Document version: 1.0_
