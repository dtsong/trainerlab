"""Tournament Result widget resolver."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.tournament import Tournament
from src.services.widget_resolvers import register_resolver


@register_resolver("tournament_result")
class TournamentResultResolver:
    """Resolves tournament result data for display."""

    async def resolve(
        self, session: AsyncSession, config: dict[str, Any]
    ) -> dict[str, Any]:
        """Resolve tournament result data.

        Config options:
            tournament_id: Tournament ID (required)
            top_n: Number of placements to show (default: 8)
            include_decklist: Whether to include deck details (default: false)
        """
        tournament_id = config.get("tournament_id")
        if not tournament_id:
            return {"error": "Tournament ID is required"}

        top_n = config.get("top_n", 8)
        include_decklist = config.get("include_decklist", False)

        # Get tournament with placements
        query = (
            select(Tournament)
            .where(Tournament.id == tournament_id)
            .options(selectinload(Tournament.placements))
        )
        result = await session.execute(query)
        tournament = result.scalar_one_or_none()

        if not tournament:
            return {"error": "Tournament not found"}

        # Sort placements by placement number
        placements = sorted(tournament.placements, key=lambda p: p.placement)[:top_n]

        results = []
        for placement in placements:
            result_data = {
                "standing": placement.placement,
                "player_name": placement.player_name,
                "archetype": placement.archetype,
            }
            if include_decklist and placement.decklist:
                result_data["decklist_preview"] = placement.decklist[
                    :10
                ]  # First 10 cards
            results.append(result_data)

        # Calculate archetype distribution
        archetype_counts: dict[str, int] = {}
        for p in tournament.placements:
            if p.archetype:
                archetype_counts[p.archetype] = archetype_counts.get(p.archetype, 0) + 1

        top_archetypes = sorted(
            archetype_counts.items(), key=lambda x: x[1], reverse=True
        )[:5]

        return {
            "tournament_id": tournament_id,
            "name": tournament.name,
            "date": tournament.date.isoformat() if tournament.date else None,
            "region": tournament.region,
            "format": tournament.format,
            "tier": tournament.tier,
            "participant_count": tournament.participant_count,
            "results": results,
            "top_archetypes": [
                {"archetype": name, "count": count} for name, count in top_archetypes
            ],
        }
