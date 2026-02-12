"""Set users.is_beta_tester default to false.

Revision ID: 030
Revises: 029
Create Date: 2026-02-11
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers
revision: str = "030"
down_revision: str | None = "029"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Set beta tester default to false."""
    op.alter_column(
        "users",
        "is_beta_tester",
        existing_type=sa.Boolean(),
        existing_nullable=False,
        server_default=sa.text("false"),
    )


def downgrade() -> None:
    """Restore beta tester default to true."""
    op.alter_column(
        "users",
        "is_beta_tester",
        existing_type=sa.Boolean(),
        existing_nullable=False,
        server_default=sa.text("true"),
    )
