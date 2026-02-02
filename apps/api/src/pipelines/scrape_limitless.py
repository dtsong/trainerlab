"""Limitless TCG scraping pipelines.

Orchestrates scraping tournament data from Limitless for both
English (international) and Japanese tournaments.
"""

import logging

from src.clients.limitless import LimitlessClient
from src.db.database import async_session_factory
from src.services.tournament_scrape import ScrapeResult, TournamentScrapeService

logger = logging.getLogger(__name__)


async def scrape_en_tournaments(
    dry_run: bool = False,
    lookback_days: int = 7,
    game_format: str = "standard",
    max_placements: int = 32,
    fetch_decklists: bool = True,
) -> ScrapeResult:
    """Scrape English (international) tournaments from Limitless.

    Scrapes tournaments from the main Limitless TCG page, which includes
    NA, EU, LATAM, and OCE events.

    Args:
        dry_run: If True, fetch data but don't save to database.
        lookback_days: Number of days to look back.
        game_format: Game format to scrape ("standard" or "expanded").
        max_placements: Maximum placements per tournament.
        fetch_decklists: Whether to fetch decklists.

    Returns:
        ScrapeResult with statistics.
    """
    logger.info(
        "Starting EN tournament scrape: dry_run=%s, lookback=%d, format=%s",
        dry_run,
        lookback_days,
        game_format,
    )

    if dry_run:
        logger.info("DRY RUN - will fetch data but not save")
        return await _scrape_dry_run(
            region="en",
            game_format=game_format,
            lookback_days=lookback_days,
        )

    async with LimitlessClient() as client, async_session_factory() as session:
        service = TournamentScrapeService(session, client)
        result = await service.scrape_new_tournaments(
            region="en",
            game_format=game_format,
            lookback_days=lookback_days,
            max_placements=max_placements,
            fetch_decklists=fetch_decklists,
        )

    logger.info(
        "EN scrape complete: saved=%d, skipped=%d, errors=%d",
        result.tournaments_saved,
        result.tournaments_skipped,
        len(result.errors),
    )

    return result


async def scrape_jp_tournaments(
    dry_run: bool = False,
    lookback_days: int = 7,
    game_format: str = "standard",
    max_placements: int = 32,
    fetch_decklists: bool = True,
) -> ScrapeResult:
    """Scrape Japanese tournaments from Limitless.

    Japanese tournaments use BO1 (best of 1) format, which affects
    meta analysis differently than BO3.

    Args:
        dry_run: If True, fetch data but don't save to database.
        lookback_days: Number of days to look back.
        game_format: Game format to scrape ("standard" or "expanded").
        max_placements: Maximum placements per tournament.
        fetch_decklists: Whether to fetch decklists.

    Returns:
        ScrapeResult with statistics.
    """
    logger.info(
        "Starting JP tournament scrape: dry_run=%s, lookback=%d, format=%s",
        dry_run,
        lookback_days,
        game_format,
    )

    if dry_run:
        logger.info("DRY RUN - will fetch data but not save")
        return await _scrape_dry_run(
            region="jp",
            game_format=game_format,
            lookback_days=lookback_days,
        )

    async with LimitlessClient() as client, async_session_factory() as session:
        service = TournamentScrapeService(session, client)
        result = await service.scrape_new_tournaments(
            region="jp",
            game_format=game_format,
            lookback_days=lookback_days,
            max_placements=max_placements,
            fetch_decklists=fetch_decklists,
        )

    logger.info(
        "JP scrape complete: saved=%d, skipped=%d, errors=%d",
        result.tournaments_saved,
        result.tournaments_skipped,
        len(result.errors),
    )

    return result


async def scrape_all_tournaments(
    dry_run: bool = False,
    lookback_days: int = 7,
    game_format: str = "standard",
    max_placements: int = 32,
    fetch_decklists: bool = True,
) -> tuple[ScrapeResult, ScrapeResult]:
    """Scrape both EN and JP tournaments.

    Args:
        dry_run: If True, fetch data but don't save.
        lookback_days: Days to look back.
        game_format: Game format.
        max_placements: Max placements per tournament.
        fetch_decklists: Whether to fetch decklists.

    Returns:
        Tuple of (EN result, JP result).
    """
    en_result = await scrape_en_tournaments(
        dry_run=dry_run,
        lookback_days=lookback_days,
        game_format=game_format,
        max_placements=max_placements,
        fetch_decklists=fetch_decklists,
    )

    jp_result = await scrape_jp_tournaments(
        dry_run=dry_run,
        lookback_days=lookback_days,
        game_format=game_format,
        max_placements=max_placements,
        fetch_decklists=fetch_decklists,
    )

    return en_result, jp_result


async def _scrape_dry_run(
    region: str,
    game_format: str,
    lookback_days: int,
) -> ScrapeResult:
    """Perform a dry run scrape (fetch but don't save).

    Args:
        region: Region to scrape.
        game_format: Game format.
        lookback_days: Days to look back.

    Returns:
        ScrapeResult showing what would be scraped.
    """
    result = ScrapeResult()

    async with LimitlessClient() as client:
        # Just fetch listings without saving
        for page in range(1, 4):  # Max 3 pages
            try:
                tournaments = await client.fetch_tournament_listings(
                    region=region,
                    game_format=game_format,
                    page=page,
                )

                if not tournaments:
                    break

                result.tournaments_scraped += len(tournaments)

                for t in tournaments:
                    logger.info(
                        "DRY RUN: Would scrape %s (%s, %d players)",
                        t.name,
                        t.tournament_date,
                        t.participant_count,
                    )

            except Exception as e:
                result.errors.append(f"Error on page {page}: {e}")
                break

    logger.info("DRY RUN complete: found %d tournaments", result.tournaments_scraped)
    return result
