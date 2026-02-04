"""Add is_creator flag to users table.

Adds is_creator boolean column for content creator access control.

Revision ID: 019
Revises: 018
Create Date: 2026-02-04
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "019"
down_revision: str | None = "018"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add is_creator column to users table."""
    op.add_column(
        "users",
        sa.Column(
            "is_creator",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.create_index("ix_users_is_creator", "users", ["is_creator"])


def downgrade() -> None:
    """Remove is_creator column from users table."""
    op.drop_index("ix_users_is_creator", table_name="users")
    op.drop_column("users", "is_creator")
