"""Limitless TCG scraping pipelines.

Orchestrates scraping tournament data from Limitless for both
English (international) and Japanese tournaments.

Supports two modes:
- Legacy: monolithic scrape (discovery + processing in one request)
- Pipeline: two-phase (discover → Cloud Tasks → process per tournament)
"""

import logging
from dataclasses import dataclass, field
from datetime import date
from uuid import UUID, uuid4

import httpx

from src.clients.limitless import LimitlessClient, LimitlessError, LimitlessTournament
from src.db.database import async_session_factory
from src.services.cloud_tasks import CloudTasksService
from src.services.tournament_scrape import ScrapeResult, TournamentScrapeService

logger = logging.getLogger(__name__)


@dataclass
class DiscoverResult:
    """Result of a tournament discovery operation."""

    tournaments_discovered: int = 0
    tasks_enqueued: int = 0
    tournaments_skipped: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return len(self.errors) == 0


def _tournament_to_task_payload(t: LimitlessTournament) -> dict:
    """Convert a LimitlessTournament to a Cloud Tasks payload dict."""
    return {
        "source_url": t.source_url,
        "name": t.name,
        "tournament_date": t.tournament_date.isoformat(),
        "region": t.region,
        "game_format": t.game_format,
        "best_of": t.best_of,
        "participant_count": t.participant_count,
    }


async def discover_en_tournaments(
    lookback_days: int = 90,
    game_format: str = "standard",
    auto_process: bool = False,
    max_auto_process: int = 50,
) -> DiscoverResult:
    """Discover new EN tournaments and enqueue them for processing.

    Phase 1 of the two-phase pipeline. Completes in <30s.

    Args:
        lookback_days: Number of days to look back.
        game_format: Game format to scrape.
        auto_process: Process synchronously if Cloud Tasks
            not configured.
        max_auto_process: Maximum tournaments to process synchronously.

    Returns:
        DiscoverResult with discovery statistics.
    """
    result = DiscoverResult()
    tasks_service = CloudTasksService()
    run_id = str(uuid4())
    _extra = {"pipeline": "discover-en", "run_id": run_id}

    async with LimitlessClient() as client, async_session_factory() as session:
        service = TournamentScrapeService(session, client)

        # Discover grassroots tournaments
        grassroots = await service.discover_new_tournaments(
            region="en",
            game_format=game_format,
            lookback_days=lookback_days,
        )

        # Discover official tournaments
        official = await service.discover_official_tournaments(
            game_format=game_format,
            lookback_days=lookback_days,
        )

    all_new = grassroots + official
    result.tournaments_discovered = len(all_new)

    # Check if we're in local dev mode (Cloud Tasks not configured)
    if not tasks_service.is_configured and auto_process:
        logger.info(
            "Cloud Tasks not configured, processing %d tournaments synchronously",
            min(len(all_new), max_auto_process),
            extra=_extra,
        )

        for tournament in all_new[:max_auto_process]:
            payload = _tournament_to_task_payload(tournament)
            payload["is_official"] = tournament in official
            try:
                scrape_result = await process_single_tournament(payload)
                if scrape_result.success and scrape_result.tournaments_saved > 0:
                    result.tasks_enqueued += 1  # Count as "processed"
                else:
                    result.tournaments_skipped += 1
                    if scrape_result.errors:
                        result.errors.extend(scrape_result.errors)
            except Exception as e:
                error_msg = f"Failed to process {tournament.name}: {e}"
                logger.error(error_msg)
                result.errors.append(error_msg)
    else:
        # Use Cloud Tasks (production mode)
        for tournament in all_new:
            payload = _tournament_to_task_payload(tournament)
            payload["is_official"] = tournament in official
            try:
                task_name = await tasks_service.enqueue_tournament(payload)
                if task_name:
                    result.tasks_enqueued += 1
                else:
                    # Cloud Tasks not configured (local dev) — skip
                    result.tournaments_skipped += 1
            except Exception as e:
                error_msg = f"Failed to enqueue {tournament.name}: {e}"
                logger.error(error_msg)
                result.errors.append(error_msg)

    logger.info(
        "EN discovery complete: discovered=%d, "
        "enqueued/processed=%d, skipped=%d, errors=%d",
        result.tournaments_discovered,
        result.tasks_enqueued,
        result.tournaments_skipped,
        len(result.errors),
        extra=_extra,
    )
    return result


async def discover_jp_tournaments(
    lookback_days: int = 90,
    auto_process: bool = False,
    max_auto_process: int = 50,
    min_date: date | None = None,
) -> DiscoverResult:
    """Discover new JP tournaments and enqueue them for processing.

    Phase 1 of the two-phase pipeline. Completes in <30s.

    Args:
        lookback_days: Number of days to look back.
        auto_process: Process synchronously if Cloud Tasks
            not configured.
        max_auto_process: Maximum tournaments to process synchronously.
        min_date: Only discover tournaments on or after this date.

    Returns:
        DiscoverResult with discovery statistics.
    """
    result = DiscoverResult()
    tasks_service = CloudTasksService()
    run_id = str(uuid4())
    _extra = {"pipeline": "discover-jp", "run_id": run_id}

    async with LimitlessClient() as client, async_session_factory() as session:
        service = TournamentScrapeService(session, client)

        jp_tournaments = await service.discover_jp_city_leagues(
            lookback_days=lookback_days,
            min_date=min_date,
        )

        # Also discover official JP tournaments (Champions League, etc.)
        jp_official = await service.discover_official_tournaments(
            region="JP",
            lookback_days=lookback_days,
        )

    all_jp = jp_tournaments + jp_official
    result.tournaments_discovered = len(all_jp)

    # Check if we're in local dev mode (Cloud Tasks not configured)
    if not tasks_service.is_configured and auto_process:
        logger.info(
            "Cloud Tasks not configured, processing %d JP tournaments synchronously",
            min(len(all_jp), max_auto_process),
            extra=_extra,
        )

        for tournament in all_jp[:max_auto_process]:
            payload = _tournament_to_task_payload(tournament)
            if tournament in jp_official:
                payload["is_official"] = True
            else:
                payload["is_jp_city_league"] = True
            try:
                scrape_result = await process_single_tournament(payload)
                if scrape_result.success and scrape_result.tournaments_saved > 0:
                    result.tasks_enqueued += 1  # Count as "processed"
                else:
                    result.tournaments_skipped += 1
                    if scrape_result.errors:
                        result.errors.extend(scrape_result.errors)
            except Exception as e:
                error_msg = f"Failed to process {tournament.name}: {e}"
                logger.error(error_msg)
                result.errors.append(error_msg)
    else:
        # Use Cloud Tasks (production mode)
        for tournament in all_jp:
            payload = _tournament_to_task_payload(tournament)
            if tournament in jp_official:
                payload["is_official"] = True
            else:
                payload["is_jp_city_league"] = True
            try:
                task_name = await tasks_service.enqueue_tournament(payload)
                if task_name:
                    result.tasks_enqueued += 1
                else:
                    result.tournaments_skipped += 1
            except Exception as e:
                error_msg = f"Failed to enqueue {tournament.name}: {e}"
                logger.error(error_msg)
                result.errors.append(error_msg)

    logger.info(
        "JP discovery complete: discovered=%d, "
        "enqueued/processed=%d, skipped=%d, errors=%d",
        result.tournaments_discovered,
        result.tasks_enqueued,
        result.tournaments_skipped,
        len(result.errors),
        extra=_extra,
    )
    return result


async def process_single_tournament(payload: dict) -> ScrapeResult:
    """Process a single tournament from a Cloud Tasks payload.

    Phase 2 of the two-phase pipeline. Called by the process-tournament endpoint.

    Args:
        payload: Tournament metadata dict from Cloud Tasks.

    Returns:
        ScrapeResult with processing statistics.
    """
    source_url = payload["source_url"]
    tournament_date = date.fromisoformat(payload["tournament_date"])
    run_id = str(uuid4())
    _extra = {"pipeline": "process-tournament", "run_id": run_id}

    logger.info(
        "Processing tournament: %s (%s)",
        payload["name"],
        source_url,
        extra=_extra,
    )

    async with LimitlessClient() as client, async_session_factory() as session:
        service = TournamentScrapeService(session, client)
        result = await service.process_tournament_by_url(
            source_url=source_url,
            name=payload["name"],
            tournament_date=tournament_date,
            region=payload["region"],
            game_format=payload.get("game_format", "standard"),
            best_of=payload.get("best_of", 3),
            participant_count=payload.get("participant_count", 0),
            is_official=payload.get("is_official", False),
            is_jp_city_league=payload.get("is_jp_city_league", False),
        )

    logger.info(
        "Processing complete for %s: saved=%d, skipped=%d, errors=%d",
        payload["name"],
        result.tournaments_saved,
        result.tournaments_skipped,
        len(result.errors),
        extra=_extra,
    )

    # Trigger evolution snapshot computation for qualifying tournaments
    if result.tournaments_saved > 0:
        tier = payload.get("tier")
        participant_count = payload.get("participant_count", 0)
        if tier in ("major", "premier") or participant_count >= 64:
            try:
                await compute_evolution_for_tournament(
                    tournament_id=None,
                    source_url=source_url,
                )
            except Exception:
                logger.error(
                    "Evolution snapshot computation failed for %s",
                    payload["name"],
                    exc_info=True,
                )

    return result


async def scrape_en_tournaments(
    dry_run: bool = False,
    lookback_days: int = 7,
    game_format: str = "standard",
    max_placements: int = 32,
    fetch_decklists: bool = True,
) -> ScrapeResult:
    """Scrape English (international) tournaments from Limitless.

    Scrapes tournaments from both:
    - play.limitlesstcg.com (grassroots tournaments)
    - limitlesstcg.com (official major events)

    Args:
        dry_run: If True, fetch data but don't save to database.
        lookback_days: Number of days to look back.
        game_format: Game format to scrape ("standard" or "expanded").
        max_placements: Maximum placements per tournament.
        fetch_decklists: Whether to fetch decklists.

    Returns:
        ScrapeResult with combined statistics.
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

    combined_result = ScrapeResult()

    async with LimitlessClient() as client, async_session_factory() as session:
        service = TournamentScrapeService(session, client)

        # Scrape grassroots tournaments from play.limitlesstcg.com
        logger.info("Scraping grassroots tournaments...")
        grassroots_result = await service.scrape_new_tournaments(
            region="en",
            game_format=game_format,
            lookback_days=lookback_days,
            max_placements=max_placements,
            fetch_decklists=fetch_decklists,
        )

        # Scrape official tournaments from limitlesstcg.com
        logger.info("Scraping official tournaments...")
        official_result = await service.scrape_official_tournaments(
            game_format=game_format,
            lookback_days=lookback_days,
            max_placements=64,  # Official events often have more placements
            fetch_decklists=fetch_decklists,
        )

    # Combine results
    combined_result.tournaments_scraped = (
        grassroots_result.tournaments_scraped + official_result.tournaments_scraped
    )
    combined_result.tournaments_saved = (
        grassroots_result.tournaments_saved + official_result.tournaments_saved
    )
    combined_result.tournaments_skipped = (
        grassroots_result.tournaments_skipped + official_result.tournaments_skipped
    )
    combined_result.placements_saved = (
        grassroots_result.placements_saved + official_result.placements_saved
    )
    combined_result.decklists_saved = (
        grassroots_result.decklists_saved + official_result.decklists_saved
    )
    combined_result.errors = grassroots_result.errors + official_result.errors

    logger.info(
        "EN scrape complete: saved=%d (grassroots=%d, official=%d), "
        "skipped=%d, errors=%d",
        combined_result.tournaments_saved,
        grassroots_result.tournaments_saved,
        official_result.tournaments_saved,
        combined_result.tournaments_skipped,
        len(combined_result.errors),
    )

    return combined_result


async def scrape_jp_tournaments(
    dry_run: bool = False,
    lookback_days: int = 90,
    game_format: str = "standard",
    max_placements: int = 32,
    fetch_decklists: bool = True,
) -> ScrapeResult:
    """Scrape Japanese tournaments from Limitless.

    Japanese tournaments use BO1 (best of 1) format, which affects
    meta analysis differently than BO3.

    Scrapes from:
    - play.limitlesstcg.com (JP grassroots)
    - limitlesstcg.com (Champions League and other official JP events)

    Args:
        dry_run: If True, fetch data but don't save to database.
        lookback_days: Number of days to look back.
        game_format: Game format to scrape ("standard" or "expanded").
        max_placements: Maximum placements per tournament.
        fetch_decklists: Whether to fetch decklists.

    Returns:
        ScrapeResult with combined statistics.
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

    combined_result = ScrapeResult()

    async with LimitlessClient() as client, async_session_factory() as session:
        service = TournamentScrapeService(session, client)

        # Scrape JP City League tournaments from limitlesstcg.com/tournaments/jp
        logger.info("Scraping JP City League tournaments...")
        city_league_result = await service.scrape_jp_city_leagues(
            lookback_days=lookback_days,
            max_placements=max_placements,
            fetch_decklists=fetch_decklists,
        )

        # Scrape official JP tournaments (Champions League, etc.)
        logger.info("Scraping official JP tournaments...")
        official_result = await service.scrape_official_tournaments(
            region="JP",
            lookback_days=lookback_days,
            max_placements=64,
            fetch_decklists=fetch_decklists,
        )

    # Combine results
    combined_result.tournaments_scraped = (
        city_league_result.tournaments_scraped + official_result.tournaments_scraped
    )
    combined_result.tournaments_saved = (
        city_league_result.tournaments_saved + official_result.tournaments_saved
    )
    combined_result.tournaments_skipped = (
        city_league_result.tournaments_skipped + official_result.tournaments_skipped
    )
    combined_result.placements_saved = (
        city_league_result.placements_saved + official_result.placements_saved
    )
    combined_result.decklists_saved = (
        city_league_result.decklists_saved + official_result.decklists_saved
    )
    combined_result.errors = city_league_result.errors + official_result.errors

    logger.info(
        "JP scrape complete: saved=%d (city_league=%d, official=%d), "
        "skipped=%d, errors=%d",
        combined_result.tournaments_saved,
        city_league_result.tournaments_saved,
        official_result.tournaments_saved,
        combined_result.tournaments_skipped,
        len(combined_result.errors),
    )

    return combined_result


@dataclass
class RescrapeResult:
    """Result of a rescrape operation."""

    tournaments_found: int = 0
    tournaments_rescraped: int = 0
    tournaments_skipped: int = 0
    placements_refreshed: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return len(self.errors) == 0


async def rescrape_jp_tournaments(
    dry_run: bool = False,
    lookback_days: int = 90,
) -> RescrapeResult:
    """Re-scrape JP tournaments that have empty archetype data.

    Finds tournaments where >50% of placements have empty archetypes
    (from scrapes that ran during pipeline development), deletes their
    placements, and re-fetches from Limitless with the current
    archetype detection pipeline.

    Args:
        dry_run: If True, report what would be rescraped without
            modifying the database.
        lookback_days: Number of days to look back.

    Returns:
        RescrapeResult with statistics.
    """
    result = RescrapeResult()

    logger.info(
        "Starting JP rescrape: dry_run=%s, lookback=%d",
        dry_run,
        lookback_days,
    )

    async with LimitlessClient() as client, async_session_factory() as session:
        service = TournamentScrapeService(session, client)

        tournaments = await service.find_tournaments_needing_rescrape(
            region="JP",
            lookback_days=lookback_days,
        )

        result.tournaments_found = len(tournaments)
        logger.info("Found %d JP tournaments needing rescrape", len(tournaments))

        if dry_run:
            for t in tournaments:
                logger.info(
                    "Would rescrape: %s (%s) — %s",
                    t.name,
                    t.date,
                    t.source_url,
                )
            return result

        for tournament in tournaments:
            try:
                count = await service.rescrape_tournament(tournament)
                result.tournaments_rescraped += 1
                result.placements_refreshed += count
            except (LimitlessError, httpx.RequestError) as e:
                msg = f"Error rescraping {tournament.name}: {e}"
                logger.error(msg, exc_info=True)
                result.errors.append(msg)

    logger.info(
        "JP rescrape complete: found=%d, rescraped=%d, placements=%d, errors=%d",
        result.tournaments_found,
        result.tournaments_rescraped,
        result.placements_refreshed,
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
        for page in range(1, 11):  # Max 10 pages
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

            except (LimitlessError, httpx.RequestError, httpx.HTTPStatusError) as e:
                result.errors.append(f"Error on page {page}: {e}")
                break

    logger.info("DRY RUN complete: found %d tournaments", result.tournaments_scraped)
    return result


async def compute_evolution_for_tournament(
    tournament_id: UUID | None = None,
    source_url: str | None = None,
) -> int:
    """Compute evolution snapshots for all archetypes in a tournament.

    For each archetype with >= 3 decklists, computes a snapshot and
    adaptations (diff only, no Claude API calls).

    Args:
        tournament_id: Tournament UUID (if known).
        source_url: Tournament source URL (used to look up ID if not provided).

    Returns:
        Number of snapshots created.
    """
    from sqlalchemy import func, select

    from src.models.tournament import Tournament
    from src.models.tournament_placement import TournamentPlacement
    from src.services.evolution_service import EvolutionService

    snapshots_created = 0

    async with async_session_factory() as session:
        # Resolve tournament_id from source_url if needed
        if tournament_id is None and source_url:
            result = await session.execute(
                select(Tournament.id).where(Tournament.source_url == source_url)
            )
            row = result.one_or_none()
            if not row:
                logger.warning(
                    "Cannot compute evolution: tournament not found for URL %s",
                    source_url,
                )
                return 0
            tournament_id = row[0]

        if tournament_id is None:
            logger.warning("Cannot compute evolution: no tournament_id or source_url")
            return 0

        # Get archetypes with their decklist counts for this tournament
        archetype_query = (
            select(
                TournamentPlacement.archetype,
                func.count(TournamentPlacement.id).label("total"),
                func.count(TournamentPlacement.decklist).label("with_decklist"),
            )
            .where(TournamentPlacement.tournament_id == tournament_id)
            .group_by(TournamentPlacement.archetype)
        )

        result = await session.execute(archetype_query)
        archetype_rows = result.all()

        service = EvolutionService(session)

        for archetype_name, _total_count, decklist_count in archetype_rows:
            if decklist_count < 3:
                logger.debug(
                    "Skipping %s: only %d decklists (need 3+)",
                    archetype_name,
                    decklist_count,
                )
                continue

            try:
                # Compute snapshot
                snapshot = await service.compute_tournament_snapshot(
                    archetype_name, tournament_id
                )
                await service.save_snapshot(snapshot)
                snapshots_created += 1

                # Find previous snapshot and compute adaptations
                previous = await service.get_previous_snapshot(
                    archetype_name, tournament_id
                )
                if previous and previous.consensus_list:
                    adaptations = await service.compute_adaptations(
                        previous.id, snapshot.id
                    )
                    for adaptation in adaptations:
                        session.add(adaptation)
                    await session.commit()

                logger.info(
                    "Evolution snapshot created: %s (tournament %s, %d decklists)",
                    archetype_name,
                    tournament_id,
                    decklist_count,
                )

            except Exception:
                logger.error(
                    "Failed to compute evolution for %s in tournament %s",
                    archetype_name,
                    tournament_id,
                    exc_info=True,
                )

    logger.info(
        "Evolution computation complete: %d snapshots created for tournament %s",
        snapshots_created,
        tournament_id,
    )
    return snapshots_created
