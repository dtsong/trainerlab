"""Add archetype_confidence column to tournament_placements

Revision ID: 024
Revises: 023
Create Date: 2026-02-07 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "024"
down_revision: str | None = "023"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "tournament_placements",
        sa.Column("archetype_confidence", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("tournament_placements", "archetype_confidence")
