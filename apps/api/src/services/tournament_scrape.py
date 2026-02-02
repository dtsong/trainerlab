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
from sqlalchemy.exc import SQLAlchemyError
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
        query = select(Tournament).where(Tournament.source_url == source_url)
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None

    async def scrape_new_tournaments(
        self,
        region: str = "en",
        game_format: str = "standard",
        lookback_days: int = 7,
        max_pages: int = 3,
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
                            except Exception as e:
                                url = placement.decklist_url
                                logger.warning(f"Error fetching decklist {url}: {e}")

                tournament.placements = placements

                # Save to database
                await self.save_tournament(tournament)
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

    async def save_tournament(
        self,
        tournament: LimitlessTournament,
    ) -> Tournament:
        """Save a tournament and its placements to the database.

        Args:
            tournament: Tournament data from Limitless.

        Returns:
            The saved Tournament model.

        Raises:
            SQLAlchemyError: If database operation fails.
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
