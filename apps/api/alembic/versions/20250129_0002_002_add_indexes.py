"""Add performance indexes and embedding column.

Revision ID: 002
Revises: 001
Create Date: 2025-01-29

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Enable pg_trgm extension for trigram indexes
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # Add embedding column for semantic search (1536 dimensions for OpenAI ada-002)
    op.execute("ALTER TABLE cards ADD COLUMN embedding vector(1536)")

    # GIN trigram index for card name fuzzy search
    op.execute("CREATE INDEX ix_cards_name_trgm ON cards USING gin (name gin_trgm_ops)")

    # GIN trigram index for card japanese_name fuzzy search
    op.execute(
        "CREATE INDEX ix_cards_japanese_name_trgm ON cards "
        "USING gin (japanese_name gin_trgm_ops) WHERE japanese_name IS NOT NULL"
    )

    # HNSW index for vector similarity search (faster than ivfflat)
    op.execute(
        "CREATE INDEX ix_cards_embedding ON cards "
        "USING hnsw (embedding vector_cosine_ops)"
    )

    # Additional composite indexes for common queries
    op.execute("CREATE INDEX ix_cards_supertype_set_id ON cards (supertype, set_id)")

    # Decks: index for public deck browsing
    op.execute(
        "CREATE INDEX ix_decks_is_public ON decks (is_public) WHERE is_public = true"
    )

    # Meta snapshots: composite index for common lookups
    op.execute(
        "CREATE INDEX ix_meta_snapshots_lookup ON meta_snapshots "
        "(format, region, snapshot_date DESC)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_meta_snapshots_lookup")
    op.execute("DROP INDEX IF EXISTS ix_decks_is_public")
    op.execute("DROP INDEX IF EXISTS ix_cards_supertype_set_id")
    op.execute("DROP INDEX IF EXISTS ix_cards_embedding")
    op.execute("DROP INDEX IF EXISTS ix_cards_japanese_name_trgm")
    op.execute("DROP INDEX IF EXISTS ix_cards_name_trgm")
    op.execute("ALTER TABLE cards DROP COLUMN IF EXISTS embedding")
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
