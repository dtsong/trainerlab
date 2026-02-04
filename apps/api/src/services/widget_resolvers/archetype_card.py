"""Archetype Card widget resolver."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.meta_snapshot import MetaSnapshot
from src.services.widget_resolvers import register_resolver


@register_resolver("archetype_card")
class ArchetypeCardResolver:
    """Resolves single archetype data for card-style widget display."""

    async def resolve(
        self, session: AsyncSession, config: dict[str, Any]
    ) -> dict[str, Any]:
        """Resolve archetype card data.

        Config options:
            archetype: Archetype name (required)
            region: Filter by region (null for global)
            format: "standard" or "expanded" (default: "standard")
            best_of: 1 or 3 (default: 3)
        """
        archetype = config.get("archetype")
        if not archetype:
            return {"error": "Archetype name is required"}

        region = config.get("region")
        format_type = config.get("format", "standard")
        best_of = config.get("best_of", 3)

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
                "archetype": archetype,
            }

        share = snapshot.archetype_shares.get(archetype)
        if share is None:
            return {
                "error": f"Archetype '{archetype}' not found in current meta",
                "archetype": archetype,
            }

        tier = (
            snapshot.tier_assignments.get(archetype)
            if snapshot.tier_assignments
            else None
        )
        trend = snapshot.trends.get(archetype, {}) if snapshot.trends else {}

        # Calculate rank
        sorted_archetypes = sorted(
            snapshot.archetype_shares.items(), key=lambda x: x[1], reverse=True
        )
        rank = next(
            (
                i + 1
                for i, (name, _) in enumerate(sorted_archetypes)
                if name == archetype
            ),
            None,
        )

        return {
            "archetype": archetype,
            "share": float(share),
            "tier": tier,
            "rank": rank,
            "trend": trend.get("direction"),
            "trend_change": trend.get("change"),
            "snapshot_date": snapshot.snapshot_date.isoformat(),
            "region": region,
            "format": format_type,
            "sample_size": snapshot.sample_size,
        }
