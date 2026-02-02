"""Add tier field to tournaments table.

Revision ID: 007
Revises: 006
Create Date: 2026-02-01

Adds tier field to tournaments for filtering:
- major: Worlds, Internationals, Regionals
- premier: Cups, Challenges
- league: City Leagues, local events
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "007"
down_revision: str | None = "006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "tournaments",
        sa.Column("tier", sa.String(20), nullable=True),
    )
    op.create_index("ix_tournaments_tier", "tournaments", ["tier"])


def downgrade() -> None:
    op.drop_index("ix_tournaments_tier", table_name="tournaments")
    op.drop_column("tournaments", "tier")
