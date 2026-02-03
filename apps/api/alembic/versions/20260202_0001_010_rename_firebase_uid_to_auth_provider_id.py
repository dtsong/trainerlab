"""Rename firebase_uid to auth_provider_id.

Revision ID: 010
Revises: 009
Create Date: 2026-02-02
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers
revision: str = "010"
down_revision: str | None = "009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Rename firebase_uid column and index to auth_provider_id."""
    op.alter_column("users", "firebase_uid", new_column_name="auth_provider_id")
    op.drop_index("ix_users_firebase_uid", table_name="users")
    op.create_index(
        "ix_users_auth_provider_id", "users", ["auth_provider_id"], unique=True
    )


def downgrade() -> None:
    """Revert auth_provider_id back to firebase_uid."""
    op.drop_index("ix_users_auth_provider_id", table_name="users")
    op.alter_column("users", "auth_provider_id", new_column_name="firebase_uid")
    op.create_index("ix_users_firebase_uid", "users", ["firebase_uid"], unique=True)
