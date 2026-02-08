"""Pipeline to seed format configs and archetype sprites."""

import json
import logging
from datetime import date
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel
from sqlalchemy import select

from src.db.database import async_session_factory
from src.models.format_config import FormatConfig
from src.services.archetype_normalizer import ArchetypeNormalizer

logger = logging.getLogger(__name__)

FIXTURES_PATH = Path(__file__).parent.parent.parent / "fixtures" / "formats.json"


class SeedDataResult(BaseModel):
    formats_seeded: int
    sprites_seeded: int
    errors: list[str]
    success: bool


def _load_fixtures() -> dict:
    """Load format fixtures from JSON (sync, tiny file)."""
    with open(FIXTURES_PATH) as f:
        return json.load(f)


async def seed_reference_data(*, dry_run: bool = False) -> SeedDataResult:
    """Seed format configs from fixtures and archetype sprites from code."""
    errors: list[str] = []
    formats_seeded = 0
    sprites_seeded = 0

    data = _load_fixtures()

    async with async_session_factory() as session:
        # 1. Seed format configs
        try:
            for item in data.get("formats", []):
                existing = await session.execute(
                    select(FormatConfig).where(FormatConfig.name == item["name"])
                )
                if existing.scalar_one_or_none():
                    logger.info("Format already exists: %s", item["name"])
                    continue

                if not dry_run:
                    start = item.get("start_date")
                    end = item.get("end_date")
                    fmt = FormatConfig(
                        id=uuid4(),
                        name=item["name"],
                        display_name=item["display_name"],
                        legal_sets=item["legal_sets"],
                        start_date=date.fromisoformat(start) if start else None,
                        end_date=date.fromisoformat(end) if end else None,
                        is_current=item.get("is_current", False),
                        is_upcoming=item.get("is_upcoming", False),
                        rotation_details=item.get("rotation_details"),
                    )
                    session.add(fmt)

                formats_seeded += 1
                logger.info("Seeded format: %s", item["name"])

            if not dry_run:
                await session.commit()

        except Exception as e:
            await session.rollback()
            msg = f"Failed to seed formats: {e}"
            logger.exception(msg)
            errors.append(msg)

        # 2. Seed archetype sprites
        try:
            if dry_run:
                from src.services.archetype_normalizer import (
                    SPRITE_ARCHETYPE_MAP,
                )

                sprites_seeded = len(SPRITE_ARCHETYPE_MAP)
                logger.info("[DRY RUN] Would seed %d sprites", sprites_seeded)
            else:
                sprites_seeded = await ArchetypeNormalizer.seed_db_sprites(session)
                await session.commit()
                logger.info("Seeded %d archetype sprites", sprites_seeded)
        except Exception as e:
            await session.rollback()
            msg = f"Failed to seed sprites: {e}"
            logger.exception(msg)
            errors.append(msg)

    return SeedDataResult(
        formats_seeded=formats_seeded,
        sprites_seeded=sprites_seeded,
        errors=errors,
        success=len(errors) == 0,
    )
