"""Create card inclusion rates SQL view.

Revision ID: 003
Revises: 002
Create Date: 2026-01-30

This migration creates a materialized view for computing card inclusion rates
from tournament placements. The view calculates:
- Cards appearing in tournament decks with available decklists
- Percentage of decks including each card (inclusion_rate)
- Average copies when the card is included (avg_copies)
- Grouped by format, region, and best_of (match format)

Includes first_seen and last_seen dates for trend analysis.
The view uses tournament placements that have non-empty decklists.
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: str | None = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create the card usage stats materialized view
    # This aggregates card inclusion rates from tournament placements
    op.execute("""
        CREATE MATERIALIZED VIEW card_usage_stats AS
        WITH decklist_cards AS (
            -- Extract individual card entries from JSON decklists
            -- Filters out entries with missing card_id or quantity to prevent
            -- silent data loss and cast failures
            SELECT
                tp.id AS placement_id,
                tp.tournament_id,
                t.format,
                t.date AS tournament_date,
                t.region,
                t.best_of,
                tp.archetype,
                (card_entry->>'card_id')::text AS card_id,
                (card_entry->>'quantity')::integer AS quantity
            FROM tournament_placements tp
            JOIN tournaments t ON t.id = tp.tournament_id
            CROSS JOIN LATERAL jsonb_array_elements(tp.decklist) AS card_entry
            WHERE tp.decklist IS NOT NULL
              AND jsonb_typeof(tp.decklist) = 'array'
              AND jsonb_array_length(tp.decklist) > 0
              AND card_entry->>'card_id' IS NOT NULL
              AND card_entry->>'quantity' IS NOT NULL
        ),
        card_aggregates AS (
            -- Calculate inclusion rate and average copies per card
            SELECT
                card_id,
                format,
                region,
                best_of,
                COUNT(DISTINCT placement_id) AS decks_including,
                -- Count total decks with valid decklists for same format/region/best_of
                (SELECT COUNT(DISTINCT tp2.id)
                 FROM tournament_placements tp2
                 JOIN tournaments t2 ON t2.id = tp2.tournament_id
                 WHERE tp2.decklist IS NOT NULL
                   AND jsonb_typeof(tp2.decklist) = 'array'
                   AND jsonb_array_length(tp2.decklist) > 0
                   AND t2.format = dc.format
                   AND (t2.region = dc.region
                        OR (t2.region IS NULL AND dc.region IS NULL))
                   AND t2.best_of = dc.best_of
                ) AS total_decks_with_lists,
                SUM(quantity) AS total_copies,
                MIN(tournament_date) AS first_seen,
                MAX(tournament_date) AS last_seen
            FROM decklist_cards dc
            GROUP BY card_id, format, region, best_of
        )
        SELECT
            card_id,
            format,
            region,
            best_of,
            decks_including,
            total_decks_with_lists,
            CASE
                WHEN total_decks_with_lists > 0
                THEN ROUND(decks_including::numeric / total_decks_with_lists, 4)
                ELSE 0
            END AS inclusion_rate,
            CASE
                WHEN decks_including > 0
                THEN ROUND(total_copies::numeric / decks_including, 2)
                ELSE 0
            END AS avg_copies,
            first_seen,
            last_seen,
            NOW() AS computed_at
        FROM card_aggregates
        WHERE decks_including > 0
    """)

    # Create indexes on the materialized view for common query patterns
    op.execute("""
        CREATE INDEX ix_card_usage_stats_card_id
        ON card_usage_stats (card_id)
    """)

    op.execute("""
        CREATE INDEX ix_card_usage_stats_format_region
        ON card_usage_stats (format, region, best_of)
    """)

    op.execute("""
        CREATE INDEX ix_card_usage_stats_inclusion_rate
        ON card_usage_stats (inclusion_rate DESC)
    """)

    op.execute("""
        CREATE UNIQUE INDEX ix_card_usage_stats_unique
        ON card_usage_stats (card_id, format, COALESCE(region, ''), best_of)
    """)


def downgrade() -> None:
    op.execute("DROP MATERIALIZED VIEW IF EXISTS card_usage_stats CASCADE")
