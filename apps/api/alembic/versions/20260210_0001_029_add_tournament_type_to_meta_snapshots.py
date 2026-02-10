"""Add tournament_type to meta_snapshots

Revision ID: 029
Revises: 028
Create Date: 2026-02-10 00:01:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "029"
down_revision: str | None = "028"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add tournament_type column with server default
    op.add_column(
        "meta_snapshots",
        sa.Column(
            "tournament_type",
            sa.String(20),
            nullable=False,
            server_default="all",
        ),
    )

    # Add index for tournament_type
    op.create_index(
        "ix_meta_snapshots_tournament_type",
        "meta_snapshots",
        ["tournament_type"],
    )

    # Drop the old unique constraint
    op.drop_constraint("uq_meta_snapshot", "meta_snapshots", type_="unique")

    # Create new unique constraint including tournament_type
    op.create_unique_constraint(
        "uq_meta_snapshot",
        "meta_snapshots",
        ["snapshot_date", "region", "format", "best_of", "tournament_type"],
    )

    # Add check constraint for valid values
    op.create_check_constraint(
        "ck_tournament_type_valid",
        "meta_snapshots",
        "tournament_type IN ('all', 'official', 'grassroots')",
    )


def downgrade() -> None:
    # Drop check constraint
    op.drop_constraint("ck_tournament_type_valid", "meta_snapshots", type_="check")

    # Drop new unique constraint
    op.drop_constraint("uq_meta_snapshot", "meta_snapshots", type_="unique")

    # Recreate old unique constraint
    op.create_unique_constraint(
        "uq_meta_snapshot",
        "meta_snapshots",
        ["snapshot_date", "region", "format", "best_of"],
    )

    # Drop index
    op.drop_index("ix_meta_snapshots_tournament_type", table_name="meta_snapshots")

    # Drop column
    op.drop_column("meta_snapshots", "tournament_type")
