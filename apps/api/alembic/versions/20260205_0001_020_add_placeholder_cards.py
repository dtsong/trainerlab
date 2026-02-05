"""Add placeholder cards table and enhance card_id_mappings

Revision ID: 20260205_0001_020_add_placeholder_cards
Revises: 20260204_0004_019_add_is_creator_flag
Create Date: 2026-02-05 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "020"
down_revision: str | None = "019"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create placeholder_cards table
    op.create_table(
        "placeholder_cards",
        sa.Column("id", postgresql.UUID(), nullable=False),
        sa.Column("jp_card_id", sa.String(50), nullable=False),
        sa.Column("en_card_id", sa.String(50), nullable=False),
        sa.Column("name_jp", sa.String(255), nullable=False),
        sa.Column("name_en", sa.String(255), nullable=False),
        sa.Column("supertype", sa.String(50), nullable=False),
        sa.Column("subtypes", postgresql.JSONB(), nullable=True),
        sa.Column("hp", sa.Integer(), nullable=True),
        sa.Column("types", postgresql.JSONB(), nullable=True),
        sa.Column("attacks", postgresql.JSONB(), nullable=True),
        sa.Column("set_code", sa.String(50), nullable=False, server_default="POR"),
        sa.Column("official_set_code", sa.String(50), nullable=True),
        sa.Column("is_unreleased", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_released", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("released_at", sa.DateTime(), nullable=True),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("source_account", sa.String(255), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("jp_card_id"),
        sa.UniqueConstraint("en_card_id"),
    )

    # Create indexes for placeholder_cards
    op.create_index(
        "ix_placeholder_cards_jp_card_id", "placeholder_cards", ["jp_card_id"]
    )
    op.create_index(
        "ix_placeholder_cards_en_card_id", "placeholder_cards", ["en_card_id"]
    )
    op.create_index(
        "ix_placeholder_cards_is_unreleased", "placeholder_cards", ["is_unreleased"]
    )
    op.create_index(
        "ix_placeholder_cards_is_released", "placeholder_cards", ["is_released"]
    )

    # Add columns to card_id_mappings
    op.add_column(
        "card_id_mappings",
        sa.Column("is_synthetic", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "card_id_mappings",
        sa.Column("placeholder_card_id", postgresql.UUID(), nullable=True),
    )

    # Create foreign key and index for card_id_mappings
    op.create_foreign_key(
        "fk_card_id_mappings_placeholder_card",
        "card_id_mappings",
        "placeholder_cards",
        ["placeholder_card_id"],
        ["id"],
    )
    op.create_index(
        "ix_card_id_mappings_placeholder_card_id",
        "card_id_mappings",
        ["placeholder_card_id"],
    )


def downgrade() -> None:
    # Drop foreign key and index from card_id_mappings
    op.drop_index(
        "ix_card_id_mappings_placeholder_card_id", table_name="card_id_mappings"
    )
    op.drop_constraint(
        "fk_card_id_mappings_placeholder_card", "card_id_mappings", type_="foreignkey"
    )
    op.drop_column("card_id_mappings", "placeholder_card_id")
    op.drop_column("card_id_mappings", "is_synthetic")

    # Drop indexes from placeholder_cards
    op.drop_index("ix_placeholder_cards_is_released", table_name="placeholder_cards")
    op.drop_index("ix_placeholder_cards_is_unreleased", table_name="placeholder_cards")
    op.drop_index("ix_placeholder_cards_en_card_id", table_name="placeholder_cards")
    op.drop_index("ix_placeholder_cards_jp_card_id", table_name="placeholder_cards")

    # Drop placeholder_cards table
    op.drop_table("placeholder_cards")
