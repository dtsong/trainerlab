"""Enhance meta snapshots with diversity, tiers, JP signals, and trends.

Revision ID: 004
Revises: 003
Create Date: 2026-02-01

Adds new columns to meta_snapshots for richer meta analysis:
- diversity_index: Simpson's diversity index (1 - sum of shares squared)
- tier_assignments: JSONB mapping archetypes to tiers (S/A/B/C/Rogue)
- jp_signals: JSONB with JP vs EN divergence signals
- trends: JSONB with week-over-week changes
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: str | None = "003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add diversity_index column
    op.add_column(
        "meta_snapshots",
        sa.Column(
            "diversity_index",
            sa.Numeric(precision=5, scale=4),
            nullable=True,
            comment="Simpson's diversity index: 1 - sum(share^2)",
        ),
    )

    # Add tier_assignments JSONB column
    op.add_column(
        "meta_snapshots",
        sa.Column(
            "tier_assignments",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="Archetype tier mapping: {archetype: tier}",
        ),
    )

    # Add jp_signals JSONB column
    op.add_column(
        "meta_snapshots",
        sa.Column(
            "jp_signals",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="JP vs EN divergence signals",
        ),
    )

    # Add trends JSONB column
    op.add_column(
        "meta_snapshots",
        sa.Column(
            "trends",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="Week-over-week trend data",
        ),
    )


def downgrade() -> None:
    op.drop_column("meta_snapshots", "trends")
    op.drop_column("meta_snapshots", "jp_signals")
    op.drop_column("meta_snapshots", "tier_assignments")
    op.drop_column("meta_snapshots", "diversity_index")
