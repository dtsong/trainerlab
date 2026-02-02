"""Add JP innovation and prediction tables.

Revision ID: 008
Revises: 007
Create Date: 2026-02-01

Creates tables for Japan meta intelligence:
- jp_card_innovations: Track new card adoption in JP
- jp_new_archetypes: Track JP-only archetypes
- jp_set_impacts: Track set release impacts
- predictions: Track prediction accuracy
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "008"
down_revision: str | None = "007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create jp_card_innovations table
    op.create_table(
        "jp_card_innovations",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("card_id", sa.String(50), nullable=False, unique=True),
        sa.Column("card_name", sa.String(255), nullable=False),
        sa.Column("card_name_jp", sa.String(255), nullable=True),
        sa.Column("set_code", sa.String(20), nullable=False),
        sa.Column("set_release_jp", sa.Date(), nullable=True),
        sa.Column("set_release_en", sa.Date(), nullable=True),
        sa.Column("is_legal_en", sa.Boolean(), nullable=False, default=False),
        sa.Column("adoption_rate", sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column("adoption_trend", sa.String(20), nullable=True),
        sa.Column(
            "archetypes_using",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("competitive_impact_rating", sa.Integer(), nullable=False, default=3),
        sa.Column("impact_analysis", sa.String(5000), nullable=True),
        sa.Column("sample_size", sa.Integer(), nullable=False, default=0),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "adoption_rate >= 0 AND adoption_rate <= 1",
            name="ck_jp_card_adoption_rate_range",
        ),
        sa.CheckConstraint(
            "competitive_impact_rating >= 1 AND competitive_impact_rating <= 5",
            name="ck_jp_card_impact_rating_range",
        ),
    )
    op.create_index(
        "ix_jp_card_innovations_card_id", "jp_card_innovations", ["card_id"]
    )
    op.create_index(
        "ix_jp_card_innovations_set_code", "jp_card_innovations", ["set_code"]
    )
    op.create_index(
        "ix_jp_card_innovations_is_legal_en", "jp_card_innovations", ["is_legal_en"]
    )

    # Create jp_new_archetypes table
    op.create_table(
        "jp_new_archetypes",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("archetype_id", sa.String(100), nullable=False, unique=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("name_jp", sa.String(100), nullable=True),
        sa.Column(
            "key_cards",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("enabled_by_set", sa.String(20), nullable=True),
        sa.Column("jp_meta_share", sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column("jp_trend", sa.String(20), nullable=True),
        sa.Column(
            "city_league_results",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("estimated_en_legal_date", sa.Date(), nullable=True),
        sa.Column("analysis", sa.String(5000), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "jp_meta_share >= 0 AND jp_meta_share <= 1",
            name="ck_jp_archetype_meta_share_range",
        ),
    )
    op.create_index(
        "ix_jp_new_archetypes_archetype_id", "jp_new_archetypes", ["archetype_id"]
    )
    op.create_index(
        "ix_jp_new_archetypes_enabled_by_set", "jp_new_archetypes", ["enabled_by_set"]
    )

    # Create jp_set_impacts table
    op.create_table(
        "jp_set_impacts",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("set_code", sa.String(20), nullable=False, unique=True),
        sa.Column("set_name", sa.String(100), nullable=False),
        sa.Column("jp_release_date", sa.Date(), nullable=False),
        sa.Column("en_release_date", sa.Date(), nullable=True),
        sa.Column(
            "jp_meta_before",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "jp_meta_after",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "key_innovations",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "new_archetypes",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("analysis", sa.String(5000), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_jp_set_impacts_set_code", "jp_set_impacts", ["set_code"])
    op.create_index(
        "ix_jp_set_impacts_jp_release_date", "jp_set_impacts", ["jp_release_date"]
    )

    # Create predictions table
    op.create_table(
        "predictions",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("prediction_text", sa.String(2000), nullable=False),
        sa.Column("target_event", sa.String(255), nullable=False),
        sa.Column("target_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("outcome", sa.String(20), nullable=True),
        sa.Column("confidence", sa.String(20), nullable=True),
        sa.Column("category", sa.String(50), nullable=True),
        sa.Column("reasoning", sa.String(2000), nullable=True),
        sa.Column("outcome_notes", sa.String(2000), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_predictions_target_event", "predictions", ["target_event"])
    op.create_index("ix_predictions_target_date", "predictions", ["target_date"])
    op.create_index("ix_predictions_category", "predictions", ["category"])


def downgrade() -> None:
    op.drop_index("ix_predictions_category", table_name="predictions")
    op.drop_index("ix_predictions_target_date", table_name="predictions")
    op.drop_index("ix_predictions_target_event", table_name="predictions")
    op.drop_table("predictions")

    op.drop_index("ix_jp_set_impacts_jp_release_date", table_name="jp_set_impacts")
    op.drop_index("ix_jp_set_impacts_set_code", table_name="jp_set_impacts")
    op.drop_table("jp_set_impacts")

    op.drop_index("ix_jp_new_archetypes_enabled_by_set", table_name="jp_new_archetypes")
    op.drop_index("ix_jp_new_archetypes_archetype_id", table_name="jp_new_archetypes")
    op.drop_table("jp_new_archetypes")

    op.drop_index(
        "ix_jp_card_innovations_is_legal_en", table_name="jp_card_innovations"
    )
    op.drop_index("ix_jp_card_innovations_set_code", table_name="jp_card_innovations")
    op.drop_index("ix_jp_card_innovations_card_id", table_name="jp_card_innovations")
    op.drop_table("jp_card_innovations")
