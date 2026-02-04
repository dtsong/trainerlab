"""Meta Snapshot widget resolver."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.meta_snapshot import MetaSnapshot
from src.services.widget_resolvers import register_resolver


@register_resolver("meta_snapshot")
class MetaSnapshotResolver:
    """Resolves current meta snapshot data for widget display."""

    async def resolve(
        self, session: AsyncSession, config: dict[str, Any]
    ) -> dict[str, Any]:
        """Resolve meta snapshot data.

        Config options:
            region: Filter by region (null for global)
            format: "standard" or "expanded" (default: "standard")
            best_of: 1 or 3 (default: 3)
            top_n: Number of archetypes to include (default: 10)
        """
        region = config.get("region")
        format_type = config.get("format", "standard")
        best_of = config.get("best_of", 3)
        top_n = config.get("top_n", 10)

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

        # Sort archetypes by share and take top N
        sorted_archetypes = sorted(
            snapshot.archetype_shares.items(), key=lambda x: x[1], reverse=True
        )[:top_n]

        archetypes = []
        for name, share in sorted_archetypes:
            tier = (
                snapshot.tier_assignments.get(name)
                if snapshot.tier_assignments
                else None
            )
            trend = snapshot.trends.get(name, {}) if snapshot.trends else {}
            archetypes.append(
                {
                    "name": name,
                    "share": float(share),
                    "tier": tier,
                    "trend": trend.get("direction"),
                    "trend_change": trend.get("change"),
                }
            )

        return {
            "snapshot_date": snapshot.snapshot_date.isoformat(),
            "region": region,
            "format": format_type,
            "best_of": best_of,
            "archetypes": archetypes,
            "diversity_index": float(snapshot.diversity_index)
            if snapshot.diversity_index
            else None,
            "sample_size": snapshot.sample_size,
        }
