"""Backfill tournament tier values for existing rows.

Populates NULL tier values using the same classification logic as
TournamentScrapeService.classify_tier(): name-based patterns first,
then participant count thresholds.

Revision ID: 012
Revises: 011
Create Date: 2026-02-03
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers
revision: str = "012"
down_revision: str | None = "011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Backfill tier for tournaments where tier IS NULL."""
    # 1. Name-based: major
    op.execute("""
        UPDATE tournaments SET tier = 'major'
        WHERE tier IS NULL
          AND (lower(name) LIKE '%regional%'
            OR lower(name) LIKE '%international%'
            OR lower(name) LIKE '%worlds%'
            OR lower(name) LIKE '%world championship%')
    """)

    # 2. Name-based: premier
    op.execute("""
        UPDATE tournaments SET tier = 'premier'
        WHERE tier IS NULL
          AND (lower(name) LIKE '%league challenge%'
            OR lower(name) LIKE '%league cup%'
            OR lower(name) LIKE '%special event%')
    """)

    # 3. Name-based: league
    op.execute("""
        UPDATE tournaments SET tier = 'league'
        WHERE tier IS NULL
          AND (lower(name) LIKE '%city league%'
            OR lower(name) LIKE '%league battle%')
    """)

    # 4. Participant count fallback: major >= 256
    op.execute("""
        UPDATE tournaments SET tier = 'major'
        WHERE tier IS NULL
          AND participant_count >= 256
    """)

    # 5. Participant count fallback: premier >= 64
    op.execute("""
        UPDATE tournaments SET tier = 'premier'
        WHERE tier IS NULL
          AND participant_count >= 64
    """)

    # 6. Participant count fallback: league > 0
    op.execute("""
        UPDATE tournaments SET tier = 'league'
        WHERE tier IS NULL
          AND participant_count > 0
    """)


def downgrade() -> None:
    """Reset all tier values to NULL."""
    op.execute("UPDATE tournaments SET tier = NULL")
