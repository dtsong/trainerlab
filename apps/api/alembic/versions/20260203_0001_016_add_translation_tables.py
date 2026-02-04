"""Add translation pipeline tables.

Creates translated_content, jp_card_adoption_rates, jp_unreleased_cards,
and translation_term_overrides tables for Phase 3B translation pipeline.

Revision ID: 016
Revises: 015
Create Date: 2026-02-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "016"
down_revision: str | None = "015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create translation pipeline tables."""
    # Translated content from Japanese sources
    op.create_table(
        "translated_content",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("source_id", sa.String(255), nullable=False, index=True),
        sa.Column("source_url", sa.Text(), nullable=False, index=True),
        sa.Column("content_type", sa.String(50), nullable=False, index=True),
        sa.Column("original_text", sa.Text(), nullable=False),
        sa.Column("translated_text", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'pending'"),
            index=True,
        ),
        sa.Column("uncertainties", postgresql.JSONB(), nullable=True),
        sa.Column("translated_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.UniqueConstraint("source_id", "source_url", name="uq_translated_source"),
    )

    # Japanese card adoption rates
    op.create_table(
        "jp_card_adoption_rates",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("card_id", sa.String(255), nullable=False, index=True),
        sa.Column("card_name_jp", sa.String(255), nullable=True),
        sa.Column("card_name_en", sa.String(255), nullable=True),
        sa.Column("inclusion_rate", sa.Float(), nullable=False),
        sa.Column("avg_copies", sa.Float(), nullable=True),
        sa.Column("archetype_context", sa.String(255), nullable=True),
        sa.Column("sample_size", sa.Integer(), nullable=True),
        sa.Column("period_start", sa.Date(), nullable=False, index=True),
        sa.Column("period_end", sa.Date(), nullable=False, index=True),
        sa.Column("source", sa.String(100), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("raw_data", postgresql.JSONB(), nullable=True),
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
        sa.CheckConstraint(
            "inclusion_rate >= 0 AND inclusion_rate <= 1",
            name="ck_inclusion_rate_range",
        ),
        sa.CheckConstraint(
            "avg_copies >= 0 AND avg_copies <= 4", name="ck_avg_copies_range"
        ),
    )

    # Japanese unreleased cards
    op.create_table(
        "jp_unreleased_cards",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("jp_card_id", sa.String(255), nullable=False, unique=True),
        sa.Column("jp_set_id", sa.String(100), nullable=True),
        sa.Column("name_jp", sa.String(255), nullable=False),
        sa.Column("name_en", sa.String(255), nullable=True),
        sa.Column("card_type", sa.String(50), nullable=True),
        sa.Column(
            "competitive_impact",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("3"),
        ),
        sa.Column("affected_archetypes", postgresql.JSONB(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("expected_release_set", sa.String(100), nullable=True),
        sa.Column(
            "is_released",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
            index=True,
        ),
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
        sa.CheckConstraint(
            "competitive_impact >= 1 AND competitive_impact <= 5",
            name="ck_competitive_impact_range",
        ),
    )

    # Translation term overrides
    op.create_table(
        "translation_term_overrides",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("term_jp", sa.String(255), nullable=False, unique=True),
        sa.Column("term_en", sa.String(255), nullable=False),
        sa.Column("context", sa.Text(), nullable=True),
        sa.Column("source", sa.String(100), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
            index=True,
        ),
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


def downgrade() -> None:
    """Drop translation pipeline tables."""
    op.drop_table("translation_term_overrides")
    op.drop_table("jp_unreleased_cards")
    op.drop_table("jp_card_adoption_rates")
    op.drop_table("translated_content")
