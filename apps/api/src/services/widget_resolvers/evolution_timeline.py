"""Evolution Timeline widget resolver."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.archetype_evolution_snapshot import ArchetypeEvolutionSnapshot
from src.services.widget_resolvers import register_resolver


@register_resolver("evolution_timeline")
class EvolutionTimelineResolver:
    """Resolves archetype evolution timeline data."""

    async def resolve(
        self, session: AsyncSession, config: dict[str, Any]
    ) -> dict[str, Any]:
        """Resolve evolution timeline data.

        Config options:
            archetype: Archetype name (required)
            limit: Number of snapshots to show (default: 10)
        """
        archetype = config.get("archetype")
        if not archetype:
            return {"error": "Archetype name is required"}

        limit = config.get("limit", 10)

        query = (
            select(ArchetypeEvolutionSnapshot)
            .options(selectinload(ArchetypeEvolutionSnapshot.tournament))
            .where(ArchetypeEvolutionSnapshot.archetype == archetype)
            .order_by(ArchetypeEvolutionSnapshot.created_at.desc())
            .limit(limit)
        )

        result = await session.execute(query)
        snapshots = list(result.scalars().all())

        if not snapshots:
            return {
                "archetype": archetype,
                "timeline": [],
                "message": "No evolution data available",
            }

        timeline = []
        for snapshot in reversed(snapshots):  # Chronological order
            tournament_date = None
            tournament_name = None
            if snapshot.tournament:
                tournament_date = snapshot.tournament.date.isoformat()
                tournament_name = snapshot.tournament.name
            timeline.append(
                {
                    "date": tournament_date,
                    "tournament": tournament_name,
                    "meta_share": float(snapshot.meta_share)
                    if snapshot.meta_share
                    else None,
                    "top_cut_conversion": float(snapshot.top_cut_conversion)
                    if snapshot.top_cut_conversion
                    else None,
                    "deck_count": snapshot.deck_count,
                    "best_placement": snapshot.best_placement,
                    "consensus_list": snapshot.consensus_list,
                    "card_usage": snapshot.card_usage,
                }
            )

        # Calculate trend summary
        if len(timeline) >= 2:
            first_share = timeline[0].get("meta_share") or 0
            last_share = timeline[-1].get("meta_share") or 0
            overall_change = last_share - first_share
        else:
            overall_change = 0

        return {
            "archetype": archetype,
            "timeline": timeline,
            "total_snapshots": len(timeline),
            "overall_change": overall_change,
            "start_date": timeline[0]["date"] if timeline else None,
            "end_date": timeline[-1]["date"] if timeline else None,
        }
