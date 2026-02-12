"""Add indexes for JSONB decklist aggregate workloads.

Revision ID: 031
Revises: 030
Create Date: 2026-02-12
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers
revision: str = "031"
down_revision: str | None = "030"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create indexes used by JP aggregate decklist endpoints."""
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_tournaments_region_bestof_date "
        "ON tournaments (region, best_of, date DESC)"
    )

    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_tp_archetype_tournament_with_decklist "
        "ON tournament_placements (archetype, tournament_id) "
        "WHERE decklist IS NOT NULL"
    )

    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_tp_decklist_gin "
        "ON tournament_placements USING gin (decklist jsonb_path_ops) "
        "WHERE decklist IS NOT NULL"
    )


def downgrade() -> None:
    """Drop indexes added for decklist aggregate workloads."""
    op.execute("DROP INDEX IF EXISTS ix_tp_decklist_gin")
    op.execute("DROP INDEX IF EXISTS ix_tp_archetype_tournament_with_decklist")
    op.execute("DROP INDEX IF EXISTS ix_tournaments_region_bestof_date")
