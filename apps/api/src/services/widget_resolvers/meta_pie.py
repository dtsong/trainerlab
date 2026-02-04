"""Meta Pie Chart widget resolver."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.meta_snapshot import MetaSnapshot
from src.services.widget_resolvers import register_resolver


@register_resolver("meta_pie")
class MetaPieResolver:
    """Resolves meta data for pie chart visualization."""

    async def resolve(
        self, session: AsyncSession, config: dict[str, Any]
    ) -> dict[str, Any]:
        """Resolve meta pie chart data.

        Config options:
            region: Filter by region (null for global)
            format: "standard" or "expanded" (default: "standard")
            best_of: 1 or 3 (default: 3)
            top_n: Number of archetypes to show (default: 8)
            group_others: Whether to group remaining as "Others" (default: true)
        """
        region = config.get("region")
        format_type = config.get("format", "standard")
        best_of = config.get("best_of", 3)
        top_n = config.get("top_n", 8)
        group_others = config.get("group_others", True)

        query = (
            select(MetaSnapshot)
            .where(MetaSnapshot.format == format_type)
            .where(MetaSnapshot.best_of == best_of)
        )

        if region:
            query = query.where(MetaSnapshot.region == region)
        else:
            query = query.where(MetaSnapshot.region.is_(None))

        query = query.order_by(MetaSnapshot.snapshot_date.desc()).limit(1)

        result = await session.execute(query)
        snapshot = result.scalar_one_or_none()

        if not snapshot:
            return {
                "error": "No data available",
                "region": region,
                "format": format_type,
            }

        sorted_archetypes = sorted(
            snapshot.archetype_shares.items(), key=lambda x: x[1], reverse=True
        )

        slices = []
        others_share = 0.0

        for i, (name, share) in enumerate(sorted_archetypes):
            if i < top_n:
                tier = (
                    snapshot.tier_assignments.get(name)
                    if snapshot.tier_assignments
                    else None
                )
                slices.append(
                    {
                        "name": name,
                        "share": float(share),
                        "tier": tier,
                    }
                )
            elif group_others:
                others_share += float(share)

        if group_others and others_share > 0:
            slices.append(
                {
                    "name": "Others",
                    "share": others_share,
                    "tier": None,
                }
            )

        return {
            "snapshot_date": snapshot.snapshot_date.isoformat(),
            "region": region,
            "format": format_type,
            "slices": slices,
            "total_archetypes": len(snapshot.archetype_shares),
            "sample_size": snapshot.sample_size,
        }
