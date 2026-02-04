"""Add card_id_mappings table for JP-to-EN card ID translation.

Creates the card_id_mappings table to store mappings between Japanese
card IDs and their English equivalents. This enables proper archetype
detection for JP tournament decklists.

Revision ID: 017
Revises: 016
Create Date: 2026-02-04
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "017"
down_revision: str | None = "016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create card_id_mappings table."""
    op.create_table(
        "card_id_mappings",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("jp_card_id", sa.String(50), nullable=False, unique=True, index=True),
        sa.Column("en_card_id", sa.String(50), nullable=False),
        sa.Column("card_name_en", sa.String(255), nullable=True),
        sa.Column("jp_set_id", sa.String(20), nullable=True),
        sa.Column("en_set_id", sa.String(20), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_index(
        "ix_card_id_mappings_en_card_id",
        "card_id_mappings",
        ["en_card_id"],
    )


def downgrade() -> None:
    """Drop card_id_mappings table."""
    op.drop_index("ix_card_id_mappings_en_card_id", table_name="card_id_mappings")
    op.drop_table("card_id_mappings")
