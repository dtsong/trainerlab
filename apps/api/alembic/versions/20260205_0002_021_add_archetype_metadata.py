"""Add archetype metadata columns to tournament_placements

Revision ID: 021
Revises: 020
Create Date: 2026-02-05 14:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "021"
down_revision: str | None = "020"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add archetype provenance columns
    op.add_column(
        "tournament_placements",
        sa.Column("raw_archetype", sa.Text(), nullable=True),
    )
    op.add_column(
        "tournament_placements",
        sa.Column(
            "raw_archetype_sprites",
            postgresql.JSONB(),
            nullable=True,
        ),
    )
    op.add_column(
        "tournament_placements",
        sa.Column("archetype_detection_method", sa.Text(), nullable=True),
    )

    # Check constraint on detection method values
    op.create_check_constraint(
        "ck_placement_detection_method",
        "tournament_placements",
        sa.text(
            "archetype_detection_method IN "
            "('sprite_lookup', 'auto_derive', 'signature_card', 'text_label') "
            "OR archetype_detection_method IS NULL"
        ),
    )

    # Index for querying by raw_archetype
    op.create_index(
        "ix_tournament_placements_raw_archetype",
        "tournament_placements",
        ["raw_archetype"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_tournament_placements_raw_archetype",
        table_name="tournament_placements",
    )
    op.drop_constraint(
        "ck_placement_detection_method",
        "tournament_placements",
        type_="check",
    )
    op.drop_column("tournament_placements", "archetype_detection_method")
    op.drop_column("tournament_placements", "raw_archetype_sprites")
    op.drop_column("tournament_placements", "raw_archetype")
