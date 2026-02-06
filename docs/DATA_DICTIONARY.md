# Data Dictionary

> Reference for all JSONB field schemas, confidence indicators, and tier thresholds used in TrainerLab.

---

## MetaSnapshot JSONB Fields

### `archetype_shares`

```json
{
  "Charizard ex": 0.2,
  "Raging Bolt ex": 0.15,
  "Dragapult ex": 0.1
}
```

Map of archetype name to meta share (0.0 - 1.0). Excludes "Other" and "Unknown" during computation.

### `card_usage`

```json
[
  { "card_id": "sv4-125", "inclusion_rate": 0.85, "avg_copies": 3.2 },
  { "card_id": "sv1-191", "inclusion_rate": 0.72, "avg_copies": 4.0 }
]
```

Top cards by inclusion rate across all placements in the snapshot period.

### `jp_signals`

```json
{
  "Charizard ex": {
    "has_signal": true,
    "direction": "rising",
    "difference": 0.07
  },
  "Pidgeot ex": { "has_signal": false }
}
```

Per-archetype JP vs EN divergence. Signal threshold: 5% difference.

### `tier_assignments`

```json
{
  "Charizard ex": "S",
  "Raging Bolt ex": "A",
  "Dragapult ex": "B"
}
```

Tier assigned based on meta share percentage.

### `trends`

```json
{
  "Charizard ex": "up",
  "Raging Bolt ex": "stable",
  "Pidgeot ex": "down"
}
```

Trend direction based on share change over recent snapshots.

---

## Tier Thresholds

| Tier  | Share Range |
| ----- | ----------- |
| S     | > 15%       |
| A     | 8% - 15%    |
| B     | 3% - 8%     |
| C     | 1% - 3%     |
| Rogue | < 1%        |

---

## Confidence Indicators

Confidence levels for data quality assessment:

| Level  | Sample Size | Data Freshness |
| ------ | ----------- | -------------- |
| High   | >= 200      | <= 3 days      |
| Medium | >= 50       | <= 7 days      |
| Low    | < 50        | > 7 days       |

Both conditions must be met for the higher tier. If either condition fails, the lower tier applies.

---

## JP-Specific Context

### Best-of Format

| Region     | Best-of | Impact                         |
| ---------- | ------- | ------------------------------ |
| JP         | BO1     | Tie = double loss; faster meta |
| All others | BO3     | Standard competitive format    |

The `REGION_BEST_OF` mapping in `MetaService` determines which best-of value to use per region:

- `JP` -> 1 (Best-of-1)
- All other regions -> 3 (Best-of-3)

### JP Signal Threshold

A JP signal is generated when the absolute difference between JP share and EN share exceeds **5%** (`0.05`). Direction is "rising" when JP > EN, "falling" when JP < EN.

### Excluded Archetypes

The following labels are excluded from meta computations:

- `"Other"`
- `"Unknown"`

---

## Comparison & Forecast Types

### MetaComparisonResponse

Server-side comparison between two regions (default: JP vs Global):

- `comparisons`: list of per-archetype divergence entries
- `lag_analysis`: optional lagged comparison (JP snapshot from N days ago vs current EN)
- Confidence indicators per region

### FormatForecastResponse

JP archetypes sorted by share descending, with divergence from global:

- Only includes archetypes with > 1% JP share
- Each entry includes sprites, tier, trend direction, confidence level

---

## ArchetypeSprite Table

Stores the mapping from sprite-based archetype identifiers to canonical names and sprite images:

| Column         | Type      | Purpose                                        |
| -------------- | --------- | ---------------------------------------------- |
| sprite_key     | TEXT (PK) | Unique sprite identifier from Limitless        |
| canonical_name | TEXT      | Normalized archetype name                      |
| sprite_order   | JSONB     | Ordered list of sprite names for image display |

Sprite URLs are constructed as:

```
https://limitlesstcg.nyc3.digitaloceanspaces.com/pokemon/gen9/{name}.png
```
