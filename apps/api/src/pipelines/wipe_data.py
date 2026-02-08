"""Pipeline to wipe tournament, meta, card, and reference data.

Preserves user data (users, decks, waitlist, api_keys, api_requests,
lab_notes, lab_note_revisions, widgets, widget_views, data_exports).
"""

import logging

from pydantic import BaseModel
from sqlalchemy import text

from src.db.database import async_session_factory

logger = logging.getLogger(__name__)

# Tables to truncate, ordered with children before parents
# to respect FK constraints (CASCADE handles this, but
# explicit ordering documents the dependency graph).
TABLES_TO_TRUNCATE = [
    # Tournament & placement data
    "tournament_placements",
    "tournaments",
    # Meta & analysis data
    "meta_snapshots",
    "archetype_evolution_snapshots",
    "adaptations",
    "evolution_article_snapshots",
    "evolution_articles",
    "predictions",
    "archetype_predictions",
    # JP intelligence data
    "jp_card_innovations",
    "jp_new_archetypes",
    "jp_set_impacts",
    "jp_card_adoption_rates",
    "jp_unreleased_cards",
    # Card & set data
    "cards",
    "sets",
    "card_id_mappings",
    "placeholder_cards",
    # Archetype detection data (will be re-seeded)
    "archetype_sprites",
    # Format configs (will be re-seeded)
    "format_configs",
    # Translation data
    "translated_content",
    "translation_term_overrides",
    # Rotation analysis
    "rotation_impacts",
]

# Tables that must NOT be truncated
PRESERVED_TABLES = {
    "users",
    "decks",
    "waitlist",
    "api_keys",
    "api_requests",
    "lab_notes",
    "lab_note_revisions",
    "widgets",
    "widget_views",
    "data_exports",
    "alembic_version",
}


class WipeDataResult(BaseModel):
    tables_truncated: int
    tables_verified_empty: int
    preserved_tables_checked: int
    errors: list[str]
    success: bool


async def wipe_data(*, dry_run: bool = False) -> WipeDataResult:
    """Truncate all data tables, preserving user tables."""
    errors: list[str] = []
    tables_truncated = 0
    tables_verified = 0
    preserved_checked = 0

    async with async_session_factory() as session:
        if dry_run:
            for table in TABLES_TO_TRUNCATE:
                result = await session.execute(
                    text(f"SELECT count(*) FROM {table}")  # noqa: S608
                )
                count = result.scalar()
                logger.info(
                    "[DRY RUN] Would truncate %s (%d rows)",
                    table,
                    count,
                )
                tables_truncated += 1

            return WipeDataResult(
                tables_truncated=0,
                tables_verified_empty=0,
                preserved_tables_checked=0,
                errors=[],
                success=True,
            )

        # Execute truncation in a single transaction
        try:
            for table in TABLES_TO_TRUNCATE:
                logger.info("Truncating %s...", table)
                await session.execute(
                    text(f"TRUNCATE TABLE {table} CASCADE")  # noqa: S608
                )
                tables_truncated += 1

            await session.commit()
            logger.info("Truncation complete: %d tables", tables_truncated)
        except Exception:
            await session.rollback()
            logger.exception("Truncation failed, rolled back")
            return WipeDataResult(
                tables_truncated=0,
                tables_verified_empty=0,
                preserved_tables_checked=0,
                errors=["Truncation transaction failed, rolled back"],
                success=False,
            )

        # Verify truncated tables are empty
        for table in TABLES_TO_TRUNCATE:
            result = await session.execute(
                text(f"SELECT count(*) FROM {table}")  # noqa: S608
            )
            count = result.scalar()
            if count == 0:
                tables_verified += 1
            else:
                msg = f"{table} still has {count} rows after truncation"
                logger.error(msg)
                errors.append(msg)

        # Verify preserved tables still have data
        for table in PRESERVED_TABLES:
            try:
                result = await session.execute(
                    text(f"SELECT count(*) FROM {table}")  # noqa: S608
                )
                count = result.scalar()
                logger.info("Preserved table %s: %d rows", table, count)
                preserved_checked += 1
            except Exception:
                logger.warning("Could not check preserved table %s", table)

    return WipeDataResult(
        tables_truncated=tables_truncated,
        tables_verified_empty=tables_verified,
        preserved_tables_checked=preserved_checked,
        errors=errors,
        success=len(errors) == 0,
    )
