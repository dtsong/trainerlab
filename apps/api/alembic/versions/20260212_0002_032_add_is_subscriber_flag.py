"""Add is_subscriber flag to users.

Revision ID: 032
Revises: 031
Create Date: 2026-02-12
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "032"
down_revision: str | None = "031"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "is_subscriber",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.create_index(
        "ix_users_is_subscriber",
        "users",
        ["is_subscriber"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_users_is_subscriber", table_name="users")
    op.drop_column("users", "is_subscriber")
