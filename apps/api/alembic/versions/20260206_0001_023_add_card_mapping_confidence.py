"""Add confidence column to card_id_mappings

Revision ID: 023
Revises: 022
Create Date: 2026-02-06 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "023"
down_revision: str | None = "022"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "card_id_mappings",
        sa.Column(
            "confidence",
            sa.Float(),
            nullable=False,
            server_default="1.0",
        ),
    )


def downgrade() -> None:
    op.drop_column("card_id_mappings", "confidence")
