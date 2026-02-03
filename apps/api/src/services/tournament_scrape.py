"""Service for scraping and storing tournament data.

Handles the orchestration of scraping from Limitless and storing
tournament data in the database.
"""

import logging
from dataclasses import dataclass, field
from datetime import date, timedelta
from uuid import uuid4

import httpx
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.clients.limitless import (
    LimitlessClient,
    LimitlessError,
    LimitlessPlacement,
    LimitlessTournament,
)
from src.models import Tournament, TournamentPlacement
from src.services.archetype_detector import ArchetypeDetector

logger = logging.getLogger(__name__)


@dataclass
class ScrapeResult:
    """Result of a tournament scrape operation."""

    tournaments_scraped: int = 0
    tournaments_saved: int = 0
    tournaments_skipped: int = 0  # Already exist
    placements_saved: int = 0
    decklists_saved: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return len(self.errors) == 0


class TournamentScrapeService:
    """Service for scraping and storing tournament data."""

    def __init__(
        self,
        session: AsyncSession,
        client: LimitlessClient,
        archetype_detector: ArchetypeDetector | None = None,
    ):
        """Initialize the service.

        Args:
            session: Database session.
            client: Limitless HTTP client.
            archetype_detector: Optional archetype detector for re-detecting.
        """
        self.session = session
        self.client = client
        self.detector = archetype_detector or ArchetypeDetector()

    async def tournament_exists(self, source_url: str) -> bool:
        """Check if a tournament already exists in the database.

        Args:
            source_url: The source URL of the tournament.

        Returns:
            True if tournament exists, False otherwise.
        """
        query = (
            select(Tournament.id).where(Tournament.source_url == source_url).limit(1)
        )
        result = await self.session.execute(query)
        return result.first() is not None

    async def scrape_new_tournaments(
        self,
        region: str = "en",
        game_format: str = "standard",
        lookback_days: int = 7,
        max_pages: int = 10,
        max_placements: int = 32,
        fetch_decklists: bool = True,
    ) -> ScrapeResult:
        """Scrape new tournaments that don't exist in the database.

        Args:
            region: Region to scrape ("en", "jp", etc.).
            game_format: Game format ("standard", "expanded").
            lookback_days: Only scrape tournaments from last N days.
            max_pages: Maximum listing pages to fetch.
            max_placements: Maximum placements per tournament.
            fetch_decklists: Whether to fetch decklists.

        Returns:
            ScrapeResult with statistics.
        """
        result = ScrapeResult()
        cutoff_date = date.today() - timedelta(days=lookback_days)

        logger.info(
            "Starting tournament scrape: region=%s, format=%s, lookback=%d days",
            region,
            game_format,
            lookback_days,
        )

        # Fetch tournament listings
        all_tournaments: list[LimitlessTournament] = []

        for page in range(1, max_pages + 1):
            try:
                tournaments = await self.client.fetch_tournament_listings(
                    region=region,
                    game_format=game_format,
                    page=page,
                )

                if not tournaments:
                    break

                # Filter by date
                for t in tournaments:
                    if t.tournament_date >= cutoff_date:
                        all_tournaments.append(t)

                logger.info(f"Fetched page {page}: {len(tournaments)} tournaments")

            except (LimitlessError, httpx.RequestError) as e:
                error_msg = f"Error fetching page {page}: {e}"
                logger.error(error_msg, exc_info=True)
                result.errors.append(error_msg)
                break

        result.tournaments_scraped = len(all_tournaments)
        logger.info(f"Found {len(all_tournaments)} tournaments in lookback period")

        # Process each tournament
        for tournament in all_tournaments:
            try:
                # Check if already exists
                if await self.tournament_exists(tournament.source_url):
                    logger.debug(f"Skipping existing tournament: {tournament.name}")
                    result.tournaments_skipped += 1
                    continue

                # Fetch placements
                placements = await self.client.fetch_tournament_placements(
                    tournament.source_url,
                    max_placements=max_placements,
                )

                # Optionally fetch decklists
                if fetch_decklists:
                    for placement in placements:
                        if placement.decklist_url:
                            try:
                                placement.decklist = await self.client.fetch_decklist(
                                    placement.decklist_url
                                )
                                if placement.decklist and placement.decklist.is_valid:
                                    result.decklists_saved += 1
                            except (
                                LimitlessError,
                                httpx.RequestError,
                                httpx.HTTPStatusError,
                            ) as e:
                                url = placement.decklist_url
                                logger.warning(f"Error fetching decklist {url}: {e}")

                tournament.placements = placements

                # Save to database
                saved = await self.save_tournament(tournament)
                if saved is None:
                    result.tournaments_skipped += 1
                else:
                    result.tournaments_saved += 1
                    result.placements_saved += len(placements)

                    logger.info(
                        f"Saved tournament: {tournament.name} "
                        f"({len(placements)} placements)"
                    )

            except (LimitlessError, SQLAlchemyError, httpx.RequestError) as e:
                error_msg = f"Error processing tournament {tournament.name}: {e}"
                logger.error(error_msg, exc_info=True)
                result.errors.append(error_msg)

        logger.info(
            "Scrape complete: scraped=%d, saved=%d, skipped=%d, errors=%d",
            result.tournaments_scraped,
            result.tournaments_saved,
            result.tournaments_skipped,
            len(result.errors),
        )

        return result

    async def scrape_official_tournaments(
        self,
        game_format: str = "standard",
        lookback_days: int = 90,
        max_placements: int = 64,
        fetch_decklists: bool = True,
    ) -> ScrapeResult:
        """Scrape official tournaments from limitlesstcg.com database.

        This fetches major competitive events (Regionals, ICs, Champions League)
        from the main Limitless database.

        Args:
            game_format: Game format ("standard", "expanded").
            lookback_days: Only scrape tournaments from last N days.
            max_placements: Maximum placements per tournament.
            fetch_decklists: Whether to fetch decklists.

        Returns:
            ScrapeResult with statistics.
        """
        result = ScrapeResult()
        cutoff_date = date.today() - timedelta(days=lookback_days)

        logger.info(
            "Starting official tournament scrape: format=%s, lookback=%d days",
            game_format,
            lookback_days,
        )

        try:
            # Fetch all official tournaments
            all_tournaments = await self.client.fetch_official_tournament_listings(
                game_format=game_format,
            )
        except (LimitlessError, httpx.RequestError) as e:
            error_msg = f"Error fetching official tournament listings: {e}"
            logger.error(error_msg, exc_info=True)
            result.errors.append(error_msg)
            return result

        # Filter by date
        tournaments_in_range = [
            t for t in all_tournaments if t.tournament_date >= cutoff_date
        ]

        result.tournaments_scraped = len(tournaments_in_range)
        logger.info(
            f"Found {len(tournaments_in_range)} official tournaments in lookback period"
        )

        # Process each tournament
        for tournament in tournaments_in_range:
            try:
                # Check if already exists
                if await self.tournament_exists(tournament.source_url):
                    logger.debug(f"Skipping existing tournament: {tournament.name}")
                    result.tournaments_skipped += 1
                    continue

                # Fetch placements from official tournament page
                placements = await self.client.fetch_official_tournament_placements(
                    tournament.source_url,
                    max_placements=max_placements,
                )

                # Optionally fetch decklists
                if fetch_decklists:
                    for placement in placements:
                        if placement.decklist_url:
                            try:
                                placement.decklist = await self.client.fetch_decklist(
                                    placement.decklist_url
                                )
                                if placement.decklist and placement.decklist.is_valid:
                                    result.decklists_saved += 1
                            except (
                                LimitlessError,
                                httpx.RequestError,
                                httpx.HTTPStatusError,
                            ) as e:
                                url = placement.decklist_url
                                logger.warning(f"Error fetching decklist {url}: {e}")

                tournament.placements = placements

                # Save to database
                saved = await self.save_tournament(tournament)
                if saved is None:
                    result.tournaments_skipped += 1
                else:
                    result.tournaments_saved += 1
                    result.placements_saved += len(placements)

                    logger.info(
                        f"Saved official tournament: {tournament.name} "
                        f"({len(placements)} placements)"
                    )

            except (LimitlessError, SQLAlchemyError, httpx.RequestError) as e:
                error_msg = f"Error processing official tournament {tournament.name}"
                logger.error(f"{error_msg}: {e}", exc_info=True)
                result.errors.append(f"{error_msg}: {e}")

        logger.info(
            "Official scrape complete: scraped=%d, saved=%d, skipped=%d, errors=%d",
            result.tournaments_scraped,
            result.tournaments_saved,
            result.tournaments_skipped,
            len(result.errors),
        )

        return result

    async def scrape_jp_city_leagues(
        self,
        lookback_days: int = 30,
        max_placements: int = 32,
        fetch_decklists: bool = True,
    ) -> ScrapeResult:
        """Scrape JP City League tournaments from limitlesstcg.com/tournaments/jp.

        Args:
            lookback_days: Only scrape tournaments from last N days.
            max_placements: Maximum placements per tournament.
            fetch_decklists: Whether to fetch decklists.

        Returns:
            ScrapeResult with statistics.
        """
        result = ScrapeResult()

        logger.info(
            "Starting JP City League scrape: lookback=%d days",
            lookback_days,
        )

        try:
            all_tournaments = await self.client.fetch_jp_city_league_listings(
                lookback_days=lookback_days,
            )
        except (LimitlessError, httpx.RequestError) as e:
            error_msg = f"Error fetching JP City League listings: {e}"
            logger.error(error_msg, exc_info=True)
            result.errors.append(error_msg)
            return result

        result.tournaments_scraped = len(all_tournaments)
        logger.info(f"Found {len(all_tournaments)} JP City League tournaments")

        for tournament in all_tournaments:
            try:
                if await self.tournament_exists(tournament.source_url):
                    logger.info(
                        "Skipping existing JP tournament: %s (%s)",
                        tournament.name,
                        tournament.source_url,
                    )
                    result.tournaments_skipped += 1
                    continue

                # Fetch placements from the tournament detail page
                placements = await self.client.fetch_jp_city_league_placements(
                    tournament.source_url,
                    max_placements=max_placements,
                )

                # Count decklist availability for logging
                placements_with_url = sum(1 for p in placements if p.decklist_url)
                logger.info(
                    "JP tournament %s: %d placements, %d with decklist URLs",
                    tournament.name,
                    len(placements),
                    placements_with_url,
                )

                # Optionally fetch decklists
                if fetch_decklists:
                    for placement in placements:
                        if placement.decklist_url:
                            try:
                                placement.decklist = await self.client.fetch_decklist(
                                    placement.decklist_url
                                )
                                if placement.decklist and placement.decklist.is_valid:
                                    result.decklists_saved += 1
                                else:
                                    logger.info(
                                        "Decklist empty/invalid for %s place %d: %s",
                                        tournament.name,
                                        placement.placement,
                                        placement.decklist_url,
                                    )
                            except (
                                LimitlessError,
                                httpx.RequestError,
                                httpx.HTTPStatusError,
                            ) as e:
                                url = placement.decklist_url
                                logger.warning(f"Error fetching decklist {url}: {e}")

                tournament.placements = placements

                saved = await self.save_tournament(tournament)
                if saved is None:
                    result.tournaments_skipped += 1
                else:
                    result.tournaments_saved += 1
                    result.placements_saved += len(placements)

                    logger.info(
                        "Saved JP City League: %s (%d placements, %d decklists)",
                        tournament.name,
                        len(placements),
                        sum(
                            1 for p in placements if p.decklist and p.decklist.is_valid
                        ),
                    )

            except (LimitlessError, SQLAlchemyError, httpx.RequestError) as e:
                error_msg = f"Error processing JP tournament {tournament.name}: {e}"
                logger.error(error_msg, exc_info=True)
                result.errors.append(error_msg)

        logger.info(
            "JP City League scrape: scraped=%d, saved=%d, skipped=%d, errors=%d",
            result.tournaments_scraped,
            result.tournaments_saved,
            result.tournaments_skipped,
            len(result.errors),
        )

        return result

    async def save_tournament(
        self,
        tournament: LimitlessTournament,
    ) -> Tournament | None:
        """Save a tournament and its placements to the database.

        Args:
            tournament: Tournament data from Limitless.

        Returns:
            The saved Tournament model, or None if duplicate (source_url conflict).

        Raises:
            SQLAlchemyError: If database operation fails (other than duplicate).
        """
        try:
            # Create tournament record
            db_tournament = Tournament(
                id=uuid4(),
                name=tournament.name,
                date=tournament.tournament_date,
                region=tournament.region,
                format=tournament.game_format,
                best_of=tournament.best_of,
                participant_count=tournament.participant_count,
                source_url=tournament.source_url,
            )

            self.session.add(db_tournament)

            # Create placement records
            for placement in tournament.placements:
                db_placement = self._create_placement(placement, db_tournament.id)
                self.session.add(db_placement)

            await self.session.commit()
            return db_tournament

        except IntegrityError:
            await self.session.rollback()
            logger.info(
                "Skipping duplicate tournament (source_url conflict): %s (%s)",
                tournament.name,
                tournament.source_url,
            )
            return None

        except SQLAlchemyError:
            await self.session.rollback()
            raise

    def _create_placement(
        self,
        placement: LimitlessPlacement,
        tournament_id,
    ) -> TournamentPlacement:
        """Create a TournamentPlacement model from Limitless data.

        Args:
            placement: Placement data from Limitless.
            tournament_id: ID of the parent tournament.

        Returns:
            TournamentPlacement model.
        """
        # Convert decklist to our format
        decklist_data = None
        decklist_source = None

        if placement.decklist and placement.decklist.is_valid:
            decklist_data = [
                {
                    "card_id": card.get("card_id"),
                    "quantity": card.get("quantity"),
                }
                for card in placement.decklist.cards
                if card.get("card_id")
            ]
            decklist_source = placement.decklist.source_url

        # Detect archetype from decklist if available
        archetype = placement.archetype
        if decklist_data:
            detected = self.detector.detect_from_existing_archetype(
                decklist_data, placement.archetype
            )
            archetype = detected

        return TournamentPlacement(
            id=uuid4(),
            tournament_id=tournament_id,
            placement=placement.placement,
            player_name=placement.player_name,
            archetype=archetype,
            decklist=decklist_data,
            decklist_source=decklist_source,
        )

    async def discover_new_tournaments(
        self,
        region: str = "en",
        game_format: str = "standard",
        lookback_days: int = 7,
        max_pages: int = 10,
    ) -> list[LimitlessTournament]:
        """Discover new tournaments without processing them.

        Returns metadata for tournaments not yet in the database.
        Used by the two-phase pipeline (discover → enqueue → process).

        Args:
            region: Region to scrape ("en", "jp", etc.).
            game_format: Game format ("standard", "expanded").
            lookback_days: Only include tournaments from last N days.
            max_pages: Maximum listing pages to fetch.

        Returns:
            List of new LimitlessTournament metadata (no placements fetched).
        """
        cutoff_date = date.today() - timedelta(days=lookback_days)
        all_tournaments: list[LimitlessTournament] = []

        for page in range(1, max_pages + 1):
            try:
                tournaments = await self.client.fetch_tournament_listings(
                    region=region,
                    game_format=game_format,
                    page=page,
                )
                if not tournaments:
                    break
                for t in tournaments:
                    if t.tournament_date >= cutoff_date:
                        all_tournaments.append(t)
            except (LimitlessError, httpx.RequestError) as e:
                logger.error("Error fetching page %d: %s", page, e)
                break

        # Filter out tournaments that already exist
        new_tournaments = []
        for t in all_tournaments:
            if not await self.tournament_exists(t.source_url):
                new_tournaments.append(t)

        logger.info(
            "Discovery complete: found=%d, new=%d, region=%s",
            len(all_tournaments),
            len(new_tournaments),
            region,
        )
        return new_tournaments

    async def discover_official_tournaments(
        self,
        game_format: str = "standard",
        lookback_days: int = 90,
    ) -> list[LimitlessTournament]:
        """Discover new official tournaments without processing them.

        Args:
            game_format: Game format ("standard", "expanded").
            lookback_days: Only include tournaments from last N days.

        Returns:
            List of new LimitlessTournament metadata.
        """
        cutoff_date = date.today() - timedelta(days=lookback_days)

        try:
            all_tournaments = await self.client.fetch_official_tournament_listings(
                game_format=game_format,
            )
        except (LimitlessError, httpx.RequestError) as e:
            logger.error("Error fetching official tournament listings: %s", e)
            return []

        tournaments_in_range = [
            t for t in all_tournaments if t.tournament_date >= cutoff_date
        ]

        new_tournaments = []
        for t in tournaments_in_range:
            if not await self.tournament_exists(t.source_url):
                new_tournaments.append(t)

        logger.info(
            "Official discovery complete: found=%d, new=%d",
            len(tournaments_in_range),
            len(new_tournaments),
        )
        return new_tournaments

    async def discover_jp_city_leagues(
        self,
        lookback_days: int = 30,
    ) -> list[LimitlessTournament]:
        """Discover new JP City League tournaments without processing them.

        Args:
            lookback_days: Only include tournaments from last N days.

        Returns:
            List of new LimitlessTournament metadata.
        """
        try:
            all_tournaments = await self.client.fetch_jp_city_league_listings(
                lookback_days=lookback_days,
            )
        except (LimitlessError, httpx.RequestError) as e:
            logger.error("Error fetching JP City League listings: %s", e)
            return []

        new_tournaments = []
        for t in all_tournaments:
            if not await self.tournament_exists(t.source_url):
                new_tournaments.append(t)

        logger.info(
            "JP discovery complete: found=%d, new=%d",
            len(all_tournaments),
            len(new_tournaments),
        )
        return new_tournaments

    async def process_tournament_by_url(
        self,
        source_url: str,
        name: str,
        tournament_date: date,
        region: str,
        game_format: str = "standard",
        best_of: int = 3,
        participant_count: int = 0,
        max_placements: int = 32,
        fetch_decklists: bool = True,
        is_official: bool = False,
        is_jp_city_league: bool = False,
    ) -> ScrapeResult:
        """Process a single tournament by its source URL.

        Used by the Cloud Tasks worker endpoint. Fetches placements,
        decklists, and saves to database.

        Args:
            source_url: Tournament source URL.
            name: Tournament name.
            tournament_date: Tournament date.
            region: Tournament region.
            game_format: Game format.
            best_of: Best-of format.
            participant_count: Number of participants.
            max_placements: Max placements to fetch.
            fetch_decklists: Whether to fetch decklists.
            is_official: Whether this is an official Limitless tournament.
            is_jp_city_league: Whether this is a JP City League tournament.

        Returns:
            ScrapeResult with statistics.
        """
        result = ScrapeResult()
        result.tournaments_scraped = 1

        # Defense in depth: check if already processed
        if await self.tournament_exists(source_url):
            logger.info("Tournament already exists, skipping: %s", source_url)
            result.tournaments_skipped = 1
            return result

        try:
            # Fetch placements based on tournament type
            if is_jp_city_league:
                placements = await self.client.fetch_jp_city_league_placements(
                    source_url, max_placements=max_placements
                )
            elif is_official:
                placements = await self.client.fetch_official_tournament_placements(
                    source_url, max_placements=max_placements
                )
            else:
                placements = await self.client.fetch_tournament_placements(
                    source_url, max_placements=max_placements
                )

            # Fetch decklists
            if fetch_decklists:
                for placement in placements:
                    if placement.decklist_url:
                        try:
                            placement.decklist = await self.client.fetch_decklist(
                                placement.decklist_url
                            )
                            if placement.decklist and placement.decklist.is_valid:
                                result.decklists_saved += 1
                        except (
                            LimitlessError,
                            httpx.RequestError,
                            httpx.HTTPStatusError,
                        ) as e:
                            logger.warning(
                                "Error fetching decklist %s: %s",
                                placement.decklist_url,
                                e,
                            )

            # Build tournament object and save
            tournament = LimitlessTournament(
                name=name,
                tournament_date=tournament_date,
                region=region,
                game_format=game_format,
                best_of=best_of,
                participant_count=participant_count,
                source_url=source_url,
                placements=placements,
            )

            saved = await self.save_tournament(tournament)
            if saved is None:
                result.tournaments_skipped = 1
            else:
                result.tournaments_saved = 1
                result.placements_saved = len(placements)

        except (LimitlessError, SQLAlchemyError, httpx.RequestError) as e:
            error_msg = f"Error processing tournament {name}: {e}"
            logger.error(error_msg, exc_info=True)
            result.errors.append(error_msg)

        return result

    async def get_recent_tournaments(
        self,
        region: str | None = None,
        game_format: str | None = None,
        best_of: int | None = None,
        days: int = 30,
    ) -> list[Tournament]:
        """Get recent tournaments from the database.

        Args:
            region: Optional region filter.
            game_format: Optional format filter.
            best_of: Optional best_of filter.
            days: Number of days to look back.

        Returns:
            List of tournaments.
        """
        cutoff = date.today() - timedelta(days=days)

        query = select(Tournament).where(Tournament.date >= cutoff)

        if region:
            query = query.where(Tournament.region == region)
        if game_format:
            query = query.where(Tournament.format == game_format)
        if best_of:
            query = query.where(Tournament.best_of == best_of)

        query = query.order_by(Tournament.date.desc())

        result = await self.session.execute(query)
        return list(result.scalars().all())
