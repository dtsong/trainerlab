"""Create jp_external_meta_shares table.

Revision ID: 038
Revises: 037
Create Date: 2026-02-22
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "038"
down_revision: str | None = "037"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "jp_external_meta_shares",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("report_date", sa.Date(), nullable=False),
        sa.Column(
            "archetype_name_jp",
            sa.String(length=200),
            nullable=False,
        ),
        sa.Column(
            "archetype_name_en",
            sa.String(length=200),
            nullable=True,
        ),
        sa.Column("share_rate", sa.Float(), nullable=False),
        sa.Column("count", sa.Integer(), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source",
            "report_date",
            "archetype_name_jp",
            name="uq_jp_ext_meta_source_date_arch",
        ),
        sa.CheckConstraint(
            "share_rate >= 0.0 AND share_rate <= 1.0",
            name="ck_share_rate_range",
        ),
    )
    op.create_index(
        "ix_jp_ext_meta_source_date",
        "jp_external_meta_shares",
        ["source", "report_date"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_jp_ext_meta_source_date",
        table_name="jp_external_meta_shares",
    )
    op.drop_table("jp_external_meta_shares")
