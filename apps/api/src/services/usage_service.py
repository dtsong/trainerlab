"""Card usage statistics service."""

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.meta_snapshot import MetaSnapshot
from src.schemas.usage import CardUsageResponse, UsageTrendPoint


class UsageService:
    """Service for querying card usage statistics from meta snapshots."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_card_usage(
        self,
        card_id: str,
        format: str = "standard",
        days: int = 30,
    ) -> CardUsageResponse | None:
        """Get usage statistics for a card.

        Args:
            card_id: The card ID (e.g., "sv4-6")
            format: The format (standard/expanded)
            days: Number of days of trend data to include

        Returns:
            CardUsageResponse if data exists, None otherwise
        """
        # Calculate date range
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        # Query snapshots for the format within date range
        query = (
            select(MetaSnapshot)
            .where(MetaSnapshot.format == format)
            .where(MetaSnapshot.snapshot_date >= start_date)
            .where(MetaSnapshot.snapshot_date <= end_date)
            .order_by(MetaSnapshot.snapshot_date.desc())
        )
        result = await self.session.execute(query)
        snapshots = result.scalars().all()

        if not snapshots:
            return None

        # Get latest snapshot for current stats
        latest = snapshots[0]
        card_usage = latest.card_usage or {}
        card_data = card_usage.get(card_id)

        if card_data is None:
            # Card not found in usage data - return empty stats
            return CardUsageResponse(
                card_id=card_id,
                format=format,
                inclusion_rate=0.0,
                avg_copies=None,
                trend=[],
                sample_size=latest.sample_size,
            )

        # Build trend data from all snapshots
        trend: list[UsageTrendPoint] = []
        for snapshot in reversed(snapshots):  # oldest to newest
            snapshot_card_usage = snapshot.card_usage or {}
            snapshot_card_data = snapshot_card_usage.get(card_id)
            if snapshot_card_data:
                trend.append(
                    UsageTrendPoint(
                        date=snapshot.snapshot_date,
                        inclusion_rate=snapshot_card_data.get("inclusion_rate", 0.0),
                        avg_copies=snapshot_card_data.get("avg_copies"),
                    )
                )

        return CardUsageResponse(
            card_id=card_id,
            format=format,
            inclusion_rate=card_data.get("inclusion_rate", 0.0),
            avg_copies=card_data.get("avg_copies"),
            trend=trend,
            sample_size=latest.sample_size,
        )
