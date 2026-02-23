"""Pipeline to discover and ingest tournaments from Official Players Club."""

import logging
from dataclasses import dataclass, field
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.clients.players_club import (
    PlayersClubClient,
    PlayersClubError,
    PlayersClubTournament,
)
from src.db.database import async_session_factory
from src.models import Tournament, TournamentPlacement
from src.services.archetype_normalizer import (
    ArchetypeNormalizer,
)

logger = logging.getLogger(__name__)


@dataclass
class ScrapePlayersClubResult:
    tournaments_discovered: int = 0
    tournaments_created: int = 0
    tournaments_skipped: int = 0
    placements_created: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return len(self.errors) == 0


async def scrape_players_club(
    lookback_days: int = 30,
    dry_run: bool = False,
    max_pages: int = 5,
    event_types: list[str] | None = None,
) -> ScrapePlayersClubResult:
    """Discover and ingest tournaments from Players Club.

    Fetches recent events via rendered HTML, checks for existing
    records, and creates Tournament + TournamentPlacement records.
    """
    result = ScrapePlayersClubResult()

    async with PlayersClubClient() as client:
        try:
            tournaments = await client.fetch_event_list(
                days=lookback_days,
                max_pages=max_pages,
                event_types=event_types,
            )
        except PlayersClubError as e:
            result.errors.append(f"Failed to fetch tournaments: {e}")
            return result

        result.tournaments_discovered = len(tournaments)

        if not tournaments:
            logger.info("No tournaments found from Players Club")
            return result

        if dry_run:
            logger.info(
                "Dry run: would process %d tournaments",
                len(tournaments),
            )
            return result

        async with async_session_factory() as session:
            normalizer = ArchetypeNormalizer()
            await normalizer.load_db_sprites(session)

            for tournament in tournaments:
                try:
                    await _process_tournament(
                        session=session,
                        client=client,
                        normalizer=normalizer,
                        tournament=tournament,
                        result=result,
                    )
                except Exception as e:
                    error_msg = f"Error processing tournament {tournament.name}: {e}"
                    logger.error(error_msg)
                    result.errors.append(error_msg)

            try:
                await session.commit()
            except Exception as e:
                error_msg = f"Failed to commit tournament data: {e}"
                logger.error(error_msg, exc_info=True)
                result.errors.append(error_msg)
                result.tournaments_created = 0
                result.placements_created = 0

    return result


async def _process_tournament(
    session: AsyncSession,
    client: PlayersClubClient,
    normalizer: ArchetypeNormalizer,
    tournament: PlayersClubTournament,
    result: ScrapePlayersClubResult,
) -> None:
    """Process a single tournament."""
    # Check for existing
    existing = await session.execute(
        select(Tournament.id).where(
            Tournament.source_url == tournament.source_url,
        )
    )
    if existing.first():
        result.tournaments_skipped += 1
        return

    # Fetch details
    detail = await client.fetch_event_detail(
        tournament.tournament_id,
    )

    if not detail.placements:
        logger.info(
            "No placements for tournament: %s",
            tournament.name,
        )
        result.tournaments_skipped += 1
        return

    # Create tournament record
    tournament_id = uuid4()
    db_tournament = Tournament(
        id=tournament_id,
        name=tournament.name,
        date=tournament.date,
        region="JP",
        format="standard",
        best_of=1,
        participant_count=(tournament.participant_count or len(detail.placements)),
        source="players_club",
        source_url=tournament.source_url,
    )
    session.add(db_tournament)

    # Create placements
    for p in detail.placements:
        archetype = p.archetype_name or "Unknown"
        detection_method = "text_label"

        if archetype and archetype != "Unknown":
            try:
                resolved, _, method = normalizer.resolve(
                    sprite_urls=[],
                    html_archetype=archetype,
                    decklist=None,
                )
                if resolved:
                    archetype = resolved
                    detection_method = method
            except Exception:
                logger.warning(
                    "Archetype resolve failed for: %s",
                    archetype,
                    exc_info=True,
                )

        placement = TournamentPlacement(
            id=uuid4(),
            tournament_id=tournament_id,
            placement=p.placement,
            player_name=p.player_name,
            archetype=archetype,
            archetype_detection_method=detection_method,
            decklist_source=p.deck_code,
        )
        session.add(placement)
        result.placements_created += 1

    result.tournaments_created += 1
