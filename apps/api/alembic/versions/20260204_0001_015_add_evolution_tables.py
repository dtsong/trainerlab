"""Add evolution tracking tables.

Creates archetype_evolution_snapshots, adaptations, archetype_predictions,
evolution_articles, and evolution_article_snapshots tables for Phase 3A.

Revision ID: 015
Revises: 014
Create Date: 2026-02-04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers
revision: str = "015"
down_revision: str | None = "014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create evolution tracking tables."""
    # Archetype evolution snapshots
    op.create_table(
        "archetype_evolution_snapshots",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("archetype", sa.String(255), nullable=False, index=True),
        sa.Column(
            "tournament_id",
            sa.Uuid(),
            sa.ForeignKey("tournaments.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("meta_share", sa.Float(), nullable=True),
        sa.Column("top_cut_conversion", sa.Float(), nullable=True),
        sa.Column("best_placement", sa.Integer(), nullable=True),
        sa.Column(
            "deck_count", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column("consensus_list", postgresql.JSONB(), nullable=True),
        sa.Column("card_usage", postgresql.JSONB(), nullable=True),
        sa.Column("meta_context", sa.Text(), nullable=True),
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
        sa.UniqueConstraint(
            "archetype", "tournament_id", name="uq_snapshot_archetype_tournament"
        ),
    )

    # Adaptations
    op.create_table(
        "adaptations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "snapshot_id",
            sa.Uuid(),
            sa.ForeignKey("archetype_evolution_snapshots.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("cards_added", postgresql.JSONB(), nullable=True),
        sa.Column("cards_removed", postgresql.JSONB(), nullable=True),
        sa.Column("target_archetype", sa.String(255), nullable=True),
        sa.Column("prevalence", sa.Float(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("source", sa.String(50), nullable=True),
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

    # Archetype predictions
    op.create_table(
        "archetype_predictions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("archetype_id", sa.String(255), nullable=False, index=True),
        sa.Column(
            "target_tournament_id",
            sa.Uuid(),
            sa.ForeignKey("tournaments.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("predicted_meta_share", postgresql.JSONB(), nullable=True),
        sa.Column("predicted_day2_rate", postgresql.JSONB(), nullable=True),
        sa.Column("predicted_tier", sa.String(10), nullable=True),
        sa.Column("likely_adaptations", postgresql.JSONB(), nullable=True),
        sa.Column("jp_signals", postgresql.JSONB(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("methodology", sa.Text(), nullable=True),
        sa.Column("actual_meta_share", sa.Float(), nullable=True),
        sa.Column("accuracy_score", sa.Float(), nullable=True),
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
        sa.UniqueConstraint(
            "archetype_id",
            "target_tournament_id",
            name="uq_prediction_archetype_tournament",
        ),
    )

    # Evolution articles
    op.create_table(
        "evolution_articles",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("archetype_id", sa.String(255), nullable=False, index=True),
        sa.Column("slug", sa.String(255), nullable=False, unique=True, index=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("excerpt", sa.String(1000), nullable=True),
        sa.Column("introduction", sa.Text(), nullable=True),
        sa.Column("conclusion", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'draft'"),
            index=True,
        ),
        sa.Column(
            "is_premium",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
            index=True,
        ),
        sa.Column(
            "published_at", sa.DateTime(timezone=True), nullable=True, index=True
        ),
        sa.Column(
            "lab_note_id",
            sa.Uuid(),
            sa.ForeignKey("lab_notes.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("commerce_links", postgresql.JSONB(), nullable=True),
        sa.Column(
            "view_count", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column(
            "share_count", sa.Integer(), nullable=False, server_default=sa.text("0")
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

    # Evolution article snapshots (join table)
    op.create_table(
        "evolution_article_snapshots",
        sa.Column(
            "article_id",
            sa.Uuid(),
            sa.ForeignKey("evolution_articles.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "snapshot_id",
            sa.Uuid(),
            sa.ForeignKey("archetype_evolution_snapshots.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "position", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
    )


def downgrade() -> None:
    """Drop evolution tracking tables."""
    op.drop_table("evolution_article_snapshots")
    op.drop_table("evolution_articles")
    op.drop_table("archetype_predictions")
    op.drop_table("adaptations")
    op.drop_table("archetype_evolution_snapshots")
