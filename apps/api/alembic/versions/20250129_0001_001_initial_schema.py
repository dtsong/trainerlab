"""Initial schema with all tables and pgvector extension.

Revision ID: 001
Revises:
Create Date: 2025-01-29

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Create sets table
    op.create_table(
        "sets",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("series", sa.String(255), nullable=False),
        sa.Column("release_date", sa.Date, nullable=True),
        sa.Column("release_date_jp", sa.Date, nullable=True),
        sa.Column("card_count", sa.Integer, nullable=True),
        sa.Column("logo_url", sa.Text, nullable=True),
        sa.Column("symbol_url", sa.Text, nullable=True),
        sa.Column("legalities", postgresql.JSONB, nullable=True),
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
    )

    # Create cards table
    op.create_table(
        "cards",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("local_id", sa.String(20), nullable=False),
        sa.Column("name", sa.String(255), nullable=False, index=True),
        sa.Column("japanese_name", sa.String(255), nullable=True),
        sa.Column("supertype", sa.String(50), nullable=False, index=True),
        sa.Column("subtypes", postgresql.ARRAY(sa.String(50)), nullable=True),
        sa.Column("types", postgresql.ARRAY(sa.String(50)), nullable=True),
        sa.Column("hp", sa.Integer, nullable=True),
        sa.Column("stage", sa.String(50), nullable=True),
        sa.Column("evolves_from", sa.String(255), nullable=True),
        sa.Column("evolves_to", postgresql.ARRAY(sa.String(255)), nullable=True),
        sa.Column("attacks", postgresql.JSONB, nullable=True),
        sa.Column("abilities", postgresql.JSONB, nullable=True),
        sa.Column("weaknesses", postgresql.JSONB, nullable=True),
        sa.Column("resistances", postgresql.JSONB, nullable=True),
        sa.Column("retreat_cost", sa.Integer, nullable=True),
        sa.Column("rules", postgresql.ARRAY(sa.Text), nullable=True),
        sa.Column("set_id", sa.String(50), sa.ForeignKey("sets.id"), nullable=False),
        sa.Column("rarity", sa.String(100), nullable=True),
        sa.Column("number", sa.String(20), nullable=True),
        sa.Column("image_small", sa.Text, nullable=True),
        sa.Column("image_large", sa.Text, nullable=True),
        sa.Column("regulation_mark", sa.String(10), nullable=True),
        sa.Column("legalities", postgresql.JSONB, nullable=True),
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
    )
    op.create_index("ix_cards_set_id", "cards", ["set_id"])

    # Create users table
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID, primary_key=True),
        sa.Column(
            "firebase_uid", sa.String(128), unique=True, nullable=False, index=True
        ),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("display_name", sa.String(255), nullable=True),
        sa.Column("avatar_url", sa.Text, nullable=True),
        sa.Column("preferences", postgresql.JSONB, nullable=True, default={}),
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
    )

    # Create decks table
    op.create_table(
        "decks",
        sa.Column("id", postgresql.UUID, primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("cards", postgresql.JSONB, nullable=False, default=[]),
        sa.Column("format", sa.String(50), nullable=False, default="standard"),
        sa.Column("archetype", sa.String(255), nullable=True),
        sa.Column("is_public", sa.Boolean, nullable=False, default=False),
        sa.Column("share_code", sa.String(20), unique=True, nullable=True),
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
    )
    op.create_index("ix_decks_user_id", "decks", ["user_id"])
    op.create_index("ix_decks_archetype", "decks", ["archetype"])

    # Create tournaments table
    op.create_table(
        "tournaments",
        sa.Column("id", postgresql.UUID, primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("region", sa.String(20), nullable=False),
        sa.Column("country", sa.String(100), nullable=True),
        sa.Column("format", sa.String(50), nullable=False),
        sa.Column("best_of", sa.Integer, nullable=False, default=3),
        sa.Column("participant_count", sa.Integer, nullable=True),
        sa.Column("source", sa.String(100), nullable=True),
        sa.Column("source_url", sa.Text, nullable=True),
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
    )
    op.create_index("ix_tournaments_date", "tournaments", ["date"])
    op.create_index("ix_tournaments_region", "tournaments", ["region"])
    op.create_index("ix_tournaments_format", "tournaments", ["format"])

    # Create tournament_placements table
    op.create_table(
        "tournament_placements",
        sa.Column("id", postgresql.UUID, primary_key=True),
        sa.Column(
            "tournament_id",
            postgresql.UUID,
            sa.ForeignKey("tournaments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "deck_id",
            postgresql.UUID,
            sa.ForeignKey("decks.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("placement", sa.Integer, nullable=False),
        sa.Column("player_name", sa.String(255), nullable=True),
        sa.Column("archetype", sa.String(255), nullable=False),
        sa.Column("decklist", postgresql.JSONB, nullable=True),
        sa.Column("decklist_source", sa.Text, nullable=True),
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
    )
    op.create_index(
        "ix_tournament_placements_tournament_id",
        "tournament_placements",
        ["tournament_id"],
    )
    op.create_index(
        "ix_tournament_placements_placement", "tournament_placements", ["placement"]
    )
    op.create_index(
        "ix_tournament_placements_archetype", "tournament_placements", ["archetype"]
    )

    # Create meta_snapshots table
    op.create_table(
        "meta_snapshots",
        sa.Column("id", postgresql.UUID, primary_key=True),
        sa.Column("snapshot_date", sa.Date, nullable=False),
        sa.Column("region", sa.String(20), nullable=True),
        sa.Column("format", sa.String(50), nullable=False),
        sa.Column("best_of", sa.Integer, nullable=False, default=3),
        sa.Column("archetype_shares", postgresql.JSONB, nullable=False),
        sa.Column("card_usage", postgresql.JSONB, nullable=True),
        sa.Column("sample_size", sa.Integer, nullable=False),
        sa.Column(
            "tournaments_included", postgresql.ARRAY(sa.String(50)), nullable=True
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
    )
    op.create_index(
        "ix_meta_snapshots_snapshot_date", "meta_snapshots", ["snapshot_date"]
    )
    op.create_index("ix_meta_snapshots_region", "meta_snapshots", ["region"])
    op.create_index("ix_meta_snapshots_format", "meta_snapshots", ["format"])
    op.create_unique_constraint(
        "uq_meta_snapshot",
        "meta_snapshots",
        ["snapshot_date", "region", "format", "best_of"],
    )


def downgrade() -> None:
    op.drop_table("meta_snapshots")
    op.drop_table("tournament_placements")
    op.drop_table("tournaments")
    op.drop_table("decks")
    op.drop_table("users")
    op.drop_table("cards")
    op.drop_table("sets")
    op.execute("DROP EXTENSION IF EXISTS vector")
