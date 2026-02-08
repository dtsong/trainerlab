"""Add era_label to meta_snapshots and enhanced fields to translated_content

Revision ID: 025
Revises: 024
Create Date: 2026-02-07 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "025"
down_revision: str | None = "024"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # meta_snapshots: add era_label
    op.add_column(
        "meta_snapshots",
        sa.Column("era_label", sa.String(50), nullable=True),
    )
    op.create_index(
        "ix_meta_snapshots_era_label",
        "meta_snapshots",
        ["era_label"],
    )

    # translated_content: add enhanced fields
    op.add_column(
        "translated_content",
        sa.Column("title_jp", sa.String(500), nullable=True),
    )
    op.add_column(
        "translated_content",
        sa.Column("title_en", sa.String(500), nullable=True),
    )
    op.add_column(
        "translated_content",
        sa.Column("published_date", sa.Date(), nullable=True),
    )
    op.create_index(
        "ix_translated_content_published_date",
        "translated_content",
        ["published_date"],
    )
    op.add_column(
        "translated_content",
        sa.Column("source_name", sa.String(100), nullable=True),
    )
    op.add_column(
        "translated_content",
        sa.Column(
            "tags",
            sa.dialects.postgresql.ARRAY(sa.String(50)),
            nullable=True,
        ),
    )
    op.add_column(
        "translated_content",
        sa.Column(
            "archetype_refs",
            sa.dialects.postgresql.ARRAY(sa.String(100)),
            nullable=True,
        ),
    )
    op.add_column(
        "translated_content",
        sa.Column("era_label", sa.String(50), nullable=True),
    )
    op.create_index(
        "ix_translated_content_era_label",
        "translated_content",
        ["era_label"],
    )
    op.add_column(
        "translated_content",
        sa.Column(
            "review_status",
            sa.String(20),
            server_default="auto_approved",
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("translated_content", "review_status")
    op.drop_index(
        "ix_translated_content_era_label",
        table_name="translated_content",
    )
    op.drop_column("translated_content", "era_label")
    op.drop_column("translated_content", "archetype_refs")
    op.drop_column("translated_content", "tags")
    op.drop_column("translated_content", "source_name")
    op.drop_index(
        "ix_translated_content_published_date",
        table_name="translated_content",
    )
    op.drop_column("translated_content", "published_date")
    op.drop_column("translated_content", "title_en")
    op.drop_column("translated_content", "title_jp")
    op.drop_index(
        "ix_meta_snapshots_era_label",
        table_name="meta_snapshots",
    )
    op.drop_column("meta_snapshots", "era_label")
