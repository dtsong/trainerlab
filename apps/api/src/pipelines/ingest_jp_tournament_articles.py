"""Pipeline to ingest JP tournament data from content site articles."""

import logging
from dataclasses import dataclass, field
from datetime import date
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.clients.pokecabook import (
    PokecabookClient,
    PokecabookTournamentArticle,
)
from src.clients.pokekameshi import (
    PokekameshiClient,
    PokekameshiTournamentArticle,
)
from src.db.database import async_session_factory
from src.models import Tournament, TournamentPlacement
from src.services.archetype_normalizer import ArchetypeNormalizer

logger = logging.getLogger(__name__)


@dataclass
class IngestArticleResult:
    """Result of JP article ingestion."""

    tournament_created: bool = False
    tournament_id: str | None = None
    placements_created: int = 0
    archetypes_detected: int = 0
    pokecabook_entries: int = 0
    pokekameshi_entries: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return len(self.errors) == 0


async def ingest_jp_tournament_article(
    tournament_name: str,
    tournament_date: date,
    pokecabook_url: str | None = None,
    pokekameshi_url: str | None = None,
    dry_run: bool = False,
) -> IngestArticleResult:
    """Ingest tournament data from JP content site articles.

    Fetches tournament results from Pokecabook and/or Pokekameshi,
    merges placement data (preferring Pokecabook for detail),
    and creates a tournament with placements in the database.

    Args:
        tournament_name: Name for the tournament record.
        tournament_date: Date of the tournament.
        pokecabook_url: Optional Pokecabook article URL.
        pokekameshi_url: Optional Pokekameshi article URL.
        dry_run: If true, fetch but don't persist.

    Returns:
        Result with counts and any errors.
    """
    result = IngestArticleResult()

    # Fetch from sources
    pokecabook_article = None
    pokekameshi_article = None

    if pokecabook_url:
        try:
            async with PokecabookClient() as client:
                pokecabook_article = await client.fetch_tournament_article(
                    pokecabook_url
                )
                result.pokecabook_entries = len(pokecabook_article.deck_entries)
        except Exception as e:
            result.errors.append(f"Pokecabook fetch failed: {e}")

    if pokekameshi_url:
        try:
            async with PokekameshiClient() as client:
                pokekameshi_article = await client.fetch_tournament_article(
                    pokekameshi_url
                )
                result.pokekameshi_entries = len(pokekameshi_article.deck_entries)
        except Exception as e:
            result.errors.append(f"Pokekameshi fetch failed: {e}")

    if not pokecabook_article and not pokekameshi_article:
        result.errors.append("No data fetched from any source")
        return result

    if dry_run:
        result.tournament_created = False
        return result

    # Merge placement data - prefer pokecabook (more detailed)
    placements_data = _merge_placements(pokecabook_article, pokekameshi_article)

    if not placements_data:
        result.errors.append("No placement data extracted from articles")
        return result

    # Create tournament + placements
    async with async_session_factory() as session:
        tournament_id = await _persist_tournament(
            session=session,
            tournament_name=tournament_name,
            tournament_date=tournament_date,
            placements_data=placements_data,
            source_url=pokecabook_url or pokekameshi_url,
            result=result,
        )
        if tournament_id:
            result.tournament_id = str(tournament_id)
            result.tournament_created = True

    return result


async def _persist_tournament(
    session: AsyncSession,
    tournament_name: str,
    tournament_date: date,
    placements_data: list[dict],
    source_url: str | None,
    result: IngestArticleResult,
) -> str | None:
    """Create tournament and placements in DB.

    Returns tournament_id on success, None on failure.
    """
    # Check duplicate
    existing = await session.execute(
        select(Tournament.id).where(
            Tournament.name == tournament_name,
            Tournament.date == tournament_date,
        )
    )
    if existing.first():
        result.errors.append(
            f"Tournament already exists: {tournament_name} on {tournament_date}"
        )
        return None

    tournament_id = uuid4()

    tournament = Tournament(
        id=tournament_id,
        name=tournament_name,
        date=tournament_date,
        region="JP",
        format="standard",
        best_of=1,
        participant_count=len(placements_data),
        tier="major",
        source="jp_article",
        source_url=source_url,
    )
    session.add(tournament)

    # Create placements with archetype normalizer
    normalizer = ArchetypeNormalizer()
    await normalizer.load_db_sprites(session)

    for p_data in placements_data:
        archetype = p_data.get("archetype", "Unknown")

        if archetype and archetype != "Unknown":
            try:
                resolved, _, method = normalizer.resolve(
                    sprite_urls=[],
                    html_archetype=archetype,
                    decklist=p_data.get("decklist"),
                )
                if resolved:
                    archetype = resolved
                    result.archetypes_detected += 1
            except Exception:
                logger.debug(
                    "Archetype resolve failed for: %s",
                    archetype,
                    exc_info=True,
                )

        placement = TournamentPlacement(
            id=uuid4(),
            tournament_id=tournament_id,
            placement=p_data["placement"],
            player_name=p_data.get("player_name"),
            archetype=archetype,
            decklist=p_data.get("decklist"),
            archetype_detection_method="text_label",
        )
        session.add(placement)
        result.placements_created += 1

    await session.commit()
    return str(tournament_id)


def _merge_placements(
    pokecabook: PokecabookTournamentArticle | None,
    pokekameshi: PokekameshiTournamentArticle | None,
) -> list[dict]:
    """Merge placement data, preferring pokecabook detail."""
    placements: dict[int, dict] = {}

    # Start with pokekameshi (less detailed)
    if pokekameshi and pokekameshi.deck_entries:
        for entry in pokekameshi.deck_entries:
            placements[entry.placement] = {
                "placement": entry.placement,
                "archetype": entry.archetype_name,
                "player_name": entry.player_name,
            }

    # Override with pokecabook (more detailed, has decklists)
    if pokecabook and pokecabook.deck_entries:
        for entry in pokecabook.deck_entries:
            existing = placements.get(entry.placement, {})
            placements[entry.placement] = {
                "placement": entry.placement,
                "archetype": entry.archetype_name,
                "player_name": (entry.player_name or existing.get("player_name")),
                "decklist": entry.decklist,
            }

    return sorted(placements.values(), key=lambda p: p["placement"])
