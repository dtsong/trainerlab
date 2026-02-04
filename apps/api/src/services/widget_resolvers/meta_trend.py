"""Meta Trend widget resolver."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.meta_snapshot import MetaSnapshot
from src.services.widget_resolvers import register_resolver


@register_resolver("meta_trend")
class MetaTrendResolver:
    """Resolves meta trend data for line chart visualization."""

    async def resolve(
        self, session: AsyncSession, config: dict[str, Any]
    ) -> dict[str, Any]:
        """Resolve meta trend data over time.

        Config options:
            archetypes: List of archetype names to track (required, max 5)
            region: Filter by region (null for global)
            format: "standard" or "expanded" (default: "standard")
            best_of: 1 or 3 (default: 3)
            days: Number of days of history (default: 30, max 90)
        """
        archetypes = config.get("archetypes", [])
        if not archetypes:
            return {"error": "At least one archetype is required"}

        archetypes = archetypes[:5]  # Limit to 5 archetypes

        region = config.get("region")
        format_type = config.get("format", "standard")
        best_of = config.get("best_of", 3)
        days = min(config.get("days", 30), 90)

        query = (
            select(MetaSnapshot)
            .where(MetaSnapshot.format == format_type)
            .where(MetaSnapshot.best_of == best_of)
        )

        if region:
            query = query.where(MetaSnapshot.region == region)
        else:
            query = query.where(MetaSnapshot.region.is_(None))

        query = query.order_by(MetaSnapshot.snapshot_date.desc()).limit(days)

        result = await session.execute(query)
        snapshots = list(result.scalars().all())

        if not snapshots:
            return {
                "error": "No data available",
                "region": region,
                "format": format_type,
            }

        # Build time series for each archetype
        series = {archetype: [] for archetype in archetypes}

        # Reverse to chronological order
        for snapshot in reversed(snapshots):
            date_str = snapshot.snapshot_date.isoformat()
            for archetype in archetypes:
                share = snapshot.archetype_shares.get(archetype, 0)
                series[archetype].append(
                    {
                        "date": date_str,
                        "share": float(share),
                    }
                )

        # Format response
        trend_lines = []
        for archetype in archetypes:
            data_points = series[archetype]
            if data_points:
                first_share = data_points[0]["share"]
                last_share = data_points[-1]["share"]
                change = last_share - first_share
                trend_lines.append(
                    {
                        "archetype": archetype,
                        "data": data_points,
                        "current_share": last_share,
                        "change": change,
                    }
                )

        return {
            "region": region,
            "format": format_type,
            "days": days,
            "start_date": snapshots[-1].snapshot_date.isoformat()
            if snapshots
            else None,
            "end_date": snapshots[0].snapshot_date.isoformat() if snapshots else None,
            "trends": trend_lines,
        }
