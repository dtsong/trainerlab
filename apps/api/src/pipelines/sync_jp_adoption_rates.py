"""JP card adoption rate sync pipeline.

Fetches card adoption rate data from Pokecabook and syncs to database.
"""

import logging
from dataclasses import dataclass, field
from datetime import date, timedelta
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from src.clients.pokecabook import PokecabookClient, PokecabookError
from src.db.database import async_session_factory
from src.models.jp_card_adoption_rate import JPCardAdoptionRate
from src.services.pipeline_resilience import retry_commit, with_timeout

FETCH_TIMEOUT = 30  # seconds for external HTTP call

logger = logging.getLogger(__name__)


@dataclass
class SyncAdoptionRatesResult:
    """Result of adoption rate sync pipeline."""

    rates_fetched: int = 0
    rates_created: int = 0
    rates_updated: int = 0
    rates_skipped: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return len(self.errors) == 0


async def sync_adoption_rates(
    dry_run: bool = False,
) -> SyncAdoptionRatesResult:
    """Sync card adoption rates from Pokecabook.

    Fetches current adoption rate data and stores in the database,
    tracking historical rates over time.

    Args:
        dry_run: If True, fetch data but don't persist.

    Returns:
        SyncAdoptionRatesResult with statistics.
    """
    result = SyncAdoptionRatesResult()

    logger.info("Starting adoption rate sync: dry_run=%s", dry_run)

    try:
        async with PokecabookClient() as pokecabook:
            adoption_data = await with_timeout(
                pokecabook.fetch_adoption_rates(),
                FETCH_TIMEOUT,
                pipeline="sync-jp-adoption-rates",
                step="fetch-adoption-rates",
            )

            result.rates_fetched = len(adoption_data.entries)
            logger.info("Fetched %d adoption rate entries", len(adoption_data.entries))

            if dry_run:
                logger.info(
                    "DRY RUN: Would sync %d adoption rate entries",
                    len(adoption_data.entries),
                )
                return result

            async with async_session_factory() as session:
                today = date.today()
                period_start = today - timedelta(days=7)
                period_end = today

                for entry in adoption_data.entries:
                    try:
                        if not entry.card_name_jp or entry.inclusion_rate <= 0:
                            result.rates_skipped += 1
                            continue

                        card_id = _generate_card_id(entry.card_name_jp)

                        existing_query = select(JPCardAdoptionRate).where(
                            JPCardAdoptionRate.card_id == card_id,
                            JPCardAdoptionRate.period_start == period_start,
                            JPCardAdoptionRate.period_end == period_end,
                        )
                        existing_result = await session.execute(existing_query)
                        existing = existing_result.scalar_one_or_none()

                        if existing:
                            existing.inclusion_rate = entry.inclusion_rate
                            existing.avg_copies = entry.avg_copies
                            existing.archetype_context = entry.archetype
                            existing.source_url = adoption_data.source_url
                            result.rates_updated += 1
                        else:
                            new_rate = JPCardAdoptionRate(
                                id=uuid4(),
                                card_id=card_id,
                                card_name_jp=entry.card_name_jp,
                                card_name_en=entry.card_name_en,
                                inclusion_rate=entry.inclusion_rate,
                                avg_copies=entry.avg_copies,
                                archetype_context=entry.archetype,
                                period_start=period_start,
                                period_end=period_end,
                                source="pokecabook",
                                source_url=adoption_data.source_url,
                            )
                            session.add(new_rate)
                            result.rates_created += 1

                    except SQLAlchemyError as e:
                        error_msg = f"Error saving rate for {entry.card_name_jp}: {e}"
                        logger.warning(error_msg)
                        result.errors.append(error_msg)

                await retry_commit(session, context="sync-adoption-rates")

    except PokecabookError as e:
        error_msg = f"Error fetching adoption rates: {e}"
        logger.error(error_msg)
        result.errors.append(error_msg)
    except Exception as e:
        error_msg = f"Pipeline error: {e}"
        logger.error(error_msg, exc_info=True)
        result.errors.append(error_msg)

    logger.info(
        "Adoption rate sync complete: fetched=%d, created=%d, updated=%d, errors=%d",
        result.rates_fetched,
        result.rates_created,
        result.rates_updated,
        len(result.errors),
    )

    return result


def _generate_card_id(card_name_jp: str) -> str:
    """Generate a stable card ID from Japanese card name.

    Uses a hash-based approach since we don't have set/number info
    from adoption rate data.
    """
    import hashlib

    name_hash = hashlib.sha256(card_name_jp.encode()).hexdigest()[:8]
    return f"jp-{name_hash}"
