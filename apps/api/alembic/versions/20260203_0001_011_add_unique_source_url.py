"""Add unique constraint on tournaments.source_url.

Deduplicates existing rows (keeping newest by created_at) then adds
a UNIQUE constraint to prevent future duplicates.

Revision ID: 011
Revises: 010
Create Date: 2026-02-03
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers
revision: str = "011"
down_revision: str | None = "010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Deduplicate tournaments and add UNIQUE constraint on source_url."""
    # Delete duplicate rows, keeping the newest (by created_at) for each source_url
    op.execute("""
        DELETE FROM tournaments
        WHERE id IN (
            SELECT id FROM (
                SELECT id,
                       ROW_NUMBER() OVER (
                           PARTITION BY source_url
                           ORDER BY created_at DESC
                       ) AS rn
                FROM tournaments
                WHERE source_url IS NOT NULL
            ) ranked
            WHERE rn > 1
        )
    """)

    # Add unique constraint
    op.create_unique_constraint(
        "uq_tournaments_source_url", "tournaments", ["source_url"]
    )


def downgrade() -> None:
    """Remove unique constraint on source_url."""
    op.drop_constraint("uq_tournaments_source_url", "tournaments", type_="unique")
