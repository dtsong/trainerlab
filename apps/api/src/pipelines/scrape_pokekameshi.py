"""Pipeline to fetch and store meta percentage data from Pokekameshi."""

import logging
from dataclasses import dataclass, field
from datetime import date
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.clients.pokekameshi import (
    PokekameshiClient,
    PokekameshiError,
)
from src.db.database import async_session_factory
from src.models.jp_external_meta_share import JPExternalMetaShare

logger = logging.getLogger(__name__)


@dataclass
class ScrapePokekameshiResult:
    reports_fetched: int = 0
    shares_recorded: int = 0
    shares_skipped: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return len(self.errors) == 0


async def scrape_pokekameshi_meta(
    dry_run: bool = False,
) -> ScrapePokekameshiResult:
    """Fetch meta percentages from Pokekameshi and store.

    Fetches the current meta report, checks for existing records,
    and inserts new JPExternalMetaShare rows (skipping existing).
    """
    result = ScrapePokekameshiResult()

    # Step 1: Fetch meta report
    try:
        async with PokekameshiClient() as client:
            report = await client.fetch_meta_percentages()
    except PokekameshiError as e:
        result.errors.append(f"Failed to fetch meta report: {e}")
        return result

    result.reports_fetched = 1

    if not report.shares:
        logger.info("No meta shares in report")
        return result

    if dry_run:
        logger.info(
            "Dry run: would record %d shares from %s",
            len(report.shares),
            report.date,
        )
        return result

    # Step 2: Persist shares
    async with async_session_factory() as session:
        for share in report.shares:
            try:
                await _insert_or_skip_share(
                    session=session,
                    source="pokekameshi",
                    report_date=report.date,
                    archetype_name_jp=share.archetype_name,
                    archetype_name_en=share.archetype_name_en,
                    share_rate=share.share_rate,
                    count=share.count,
                    source_url=report.source_url,
                    result=result,
                )
            except Exception as e:
                error_msg = f"Error recording share for {share.archetype_name}: {e}"
                logger.error(error_msg)
                result.errors.append(error_msg)

        try:
            await session.commit()
        except Exception as e:
            error_msg = f"Failed to commit meta shares: {e}"
            logger.error(error_msg, exc_info=True)
            result.errors.append(error_msg)
            result.shares_recorded = 0

    return result


async def _insert_or_skip_share(
    session: AsyncSession,
    source: str,
    report_date: date,
    archetype_name_jp: str,
    archetype_name_en: str | None,
    share_rate: float,
    count: int | None,
    source_url: str | None,
    result: ScrapePokekameshiResult,
) -> None:
    """Insert or skip a meta share record."""
    existing = await session.execute(
        select(JPExternalMetaShare.id).where(
            JPExternalMetaShare.source == source,
            JPExternalMetaShare.report_date == report_date,
            JPExternalMetaShare.archetype_name_jp == archetype_name_jp,
        )
    )
    if existing.first():
        result.shares_skipped += 1
        return

    record = JPExternalMetaShare(
        id=uuid4(),
        source=source,
        report_date=report_date,
        archetype_name_jp=archetype_name_jp,
        archetype_name_en=archetype_name_en,
        share_rate=share_rate,
        count=count,
        source_url=source_url,
    )
    session.add(record)
    result.shares_recorded += 1
