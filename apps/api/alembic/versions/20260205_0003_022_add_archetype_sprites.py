"""Add archetype_sprites lookup table

Revision ID: 022
Revises: 021
Create Date: 2026-02-05 14:01:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "022"
down_revision: str | None = "021"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "archetype_sprites",
        sa.Column("id", postgresql.UUID(), nullable=False),
        sa.Column("sprite_key", sa.String(255), nullable=False),
        sa.Column("archetype_name", sa.String(255), nullable=False),
        sa.Column(
            "sprite_urls",
            postgresql.JSONB(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "pokemon_names",
            postgresql.JSONB(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sprite_key"),
    )

    op.create_index(
        "ix_archetype_sprites_sprite_key",
        "archetype_sprites",
        ["sprite_key"],
    )
    op.create_index(
        "ix_archetype_sprites_archetype_name",
        "archetype_sprites",
        ["archetype_name"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_archetype_sprites_archetype_name",
        table_name="archetype_sprites",
    )
    op.drop_index(
        "ix_archetype_sprites_sprite_key",
        table_name="archetype_sprites",
    )
    op.drop_table("archetype_sprites")
