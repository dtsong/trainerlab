"""Add major format fields to tournaments.

Revision ID: 037
Revises: 036
Create Date: 2026-02-12
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "037"
down_revision: str | None = "036"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "tournaments",
        sa.Column("major_format_key", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "tournaments",
        sa.Column("major_format_label", sa.String(length=120), nullable=True),
    )
    op.create_index(
        "ix_tournaments_major_format_key",
        "tournaments",
        ["major_format_key"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_tournaments_major_format_key", table_name="tournaments")
    op.drop_column("tournaments", "major_format_label")
    op.drop_column("tournaments", "major_format_key")
