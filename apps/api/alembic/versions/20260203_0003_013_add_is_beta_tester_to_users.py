"""Add is_beta_tester column to users table.

All existing users are backfilled as beta testers via server_default.

Revision ID: 013
Revises: 012
Create Date: 2026-02-03
"""

from collections.abc import Sequence

from sqlalchemy import Boolean, Column, text

from alembic import op

# revision identifiers
revision: str = "013"
down_revision: str | None = "012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add is_beta_tester boolean column with server default true."""
    op.add_column(
        "users",
        Column(
            "is_beta_tester", Boolean(), nullable=False, server_default=text("true")
        ),
    )


def downgrade() -> None:
    """Remove is_beta_tester column."""
    op.drop_column("users", "is_beta_tester")
