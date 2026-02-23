"""Add limitless_id column to cards table.

Revision ID: 039
Revises: 038
Create Date: 2026-02-23
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "039"
down_revision: str | None = "038"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "cards",
        sa.Column("limitless_id", sa.String(length=50), nullable=True),
    )
    op.create_index(
        "ix_cards_limitless_id",
        "cards",
        ["limitless_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_cards_limitless_id", table_name="cards")
    op.drop_column("cards", "limitless_id")
