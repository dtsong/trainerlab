"""Add major format windows table.

Revision ID: 036
Revises: 035
Create Date: 2026-02-12
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "036"
down_revision: str | None = "035"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "major_format_windows",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("key", sa.String(length=50), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("set_range_label", sa.String(length=120), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_major_format_windows_end_date",
        "major_format_windows",
        ["end_date"],
        unique=False,
    )
    op.create_index(
        "ix_major_format_windows_is_active",
        "major_format_windows",
        ["is_active"],
        unique=False,
    )
    op.create_index(
        "ix_major_format_windows_key",
        "major_format_windows",
        ["key"],
        unique=True,
    )
    op.create_index(
        "ix_major_format_windows_start_date",
        "major_format_windows",
        ["start_date"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_major_format_windows_start_date", table_name="major_format_windows"
    )
    op.drop_index("ix_major_format_windows_key", table_name="major_format_windows")
    op.drop_index(
        "ix_major_format_windows_is_active", table_name="major_format_windows"
    )
    op.drop_index("ix_major_format_windows_end_date", table_name="major_format_windows")
    op.drop_table("major_format_windows")
