"""JP vs EN Comparison widget resolver."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.meta_snapshot import MetaSnapshot
from src.services.widget_resolvers import register_resolver


@register_resolver("jp_comparison")
class JPComparisonResolver:
    """Resolves JP vs EN meta comparison data."""

    async def resolve(
        self, session: AsyncSession, config: dict[str, Any]
    ) -> dict[str, Any]:
        """Resolve JP vs EN comparison data.

        Config options:
            format: "standard" or "expanded" (default: "standard")
            top_n: Number of archetypes to compare (default: 10)
            min_divergence: Minimum share difference to highlight (default: 0.03)
        """
        format_type = config.get("format", "standard")
        top_n = config.get("top_n", 10)
        min_divergence = config.get("min_divergence", 0.03)

        # Get JP snapshot (BO1)
        jp_query = (
            select(MetaSnapshot)
            .where(MetaSnapshot.format == format_type)
            .where(MetaSnapshot.best_of == 1)
            .where(MetaSnapshot.region == "JP")
            .order_by(MetaSnapshot.snapshot_date.desc())
            .limit(1)
        )

        jp_result = await session.execute(jp_query)
        jp_snapshot = jp_result.scalar_one_or_none()

        # Get global snapshot (BO3)
        en_query = (
            select(MetaSnapshot)
            .where(MetaSnapshot.format == format_type)
            .where(MetaSnapshot.best_of == 3)
            .where(MetaSnapshot.region.is_(None))
            .order_by(MetaSnapshot.snapshot_date.desc())
            .limit(1)
        )

        en_result = await session.execute(en_query)
        en_snapshot = en_result.scalar_one_or_none()

        if not jp_snapshot and not en_snapshot:
            return {"error": "No data available"}

        # Get all unique archetypes
        all_archetypes = set()
        if jp_snapshot:
            all_archetypes.update(jp_snapshot.archetype_shares.keys())
        if en_snapshot:
            all_archetypes.update(en_snapshot.archetype_shares.keys())

        # Build comparison data
        comparisons = []
        for archetype in all_archetypes:
            jp_share = (
                float(jp_snapshot.archetype_shares.get(archetype, 0))
                if jp_snapshot
                else 0
            )
            en_share = (
                float(en_snapshot.archetype_shares.get(archetype, 0))
                if en_snapshot
                else 0
            )
            divergence = jp_share - en_share

            jp_tier = None
            en_tier = None
            if jp_snapshot and jp_snapshot.tier_assignments:
                jp_tier = jp_snapshot.tier_assignments.get(archetype)
            if en_snapshot and en_snapshot.tier_assignments:
                en_tier = en_snapshot.tier_assignments.get(archetype)

            comparisons.append(
                {
                    "archetype": archetype,
                    "jp_share": jp_share,
                    "en_share": en_share,
                    "divergence": divergence,
                    "jp_tier": jp_tier,
                    "en_tier": en_tier,
                    "is_divergent": abs(divergence) >= min_divergence,
                }
            )

        # Sort by max share and take top N
        comparisons.sort(key=lambda x: max(x["jp_share"], x["en_share"]), reverse=True)
        comparisons = comparisons[:top_n]

        # Identify rising/falling in JP
        rising = [c for c in comparisons if c["divergence"] >= min_divergence]
        falling = [c for c in comparisons if c["divergence"] <= -min_divergence]

        return {
            "format": format_type,
            "jp_date": jp_snapshot.snapshot_date.isoformat() if jp_snapshot else None,
            "en_date": en_snapshot.snapshot_date.isoformat() if en_snapshot else None,
            "jp_sample_size": jp_snapshot.sample_size if jp_snapshot else 0,
            "en_sample_size": en_snapshot.sample_size if en_snapshot else 0,
            "comparisons": comparisons,
            "rising_in_jp": [c["archetype"] for c in rising],
            "falling_in_jp": [c["archetype"] for c in falling],
        }
