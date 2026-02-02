"""Meta snapshot service for computing tournament meta analysis.

Aggregates tournament placements to compute archetype shares,
card inclusion rates, and other meta statistics.
"""

import logging
from collections import defaultdict
from collections.abc import Sequence
from datetime import date, timedelta
from decimal import Decimal
from typing import Literal
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import MetaSnapshot, Tournament, TournamentPlacement

logger = logging.getLogger(__name__)

# Tier thresholds based on meta share
TIER_S_THRESHOLD = 0.15  # >15%
TIER_A_THRESHOLD = 0.08  # 8-15%
TIER_B_THRESHOLD = 0.03  # 3-8%
TIER_C_THRESHOLD = 0.01  # 1-3%
# Below 1% = Rogue

# JP signal threshold
JP_SIGNAL_THRESHOLD = 0.05  # 5% divergence


class MetaService:
    """Service for computing and storing meta snapshots."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def compute_meta_snapshot(
        self,
        *,
        snapshot_date: date,
        region: str | None = None,
        game_format: Literal["standard", "expanded"] = "standard",
        best_of: Literal[1, 3] = 3,
        lookback_days: int = 90,
    ) -> MetaSnapshot:
        """Compute a meta snapshot from tournament placements.

        Aggregates placement data to calculate:
        - Archetype shares (percentage of top placements)
        - Card usage rates (how often each card appears in archetypes)
        - Sample size and tournaments included

        Args:
            snapshot_date: Reference date for the snapshot (lookback starts here).
            region: Region filter (NA, EU, JP, LATAM, OCE) or None for global.
            game_format: Game format (standard, expanded).
            best_of: Match format (1 for Japan BO1, 3 for international BO3).
            lookback_days: Number of days to look back for tournament data.

        Returns:
            MetaSnapshot with computed stats.

        Raises:
            SQLAlchemyError: If database query fails.
        """
        start_date = date.fromordinal(snapshot_date.toordinal() - lookback_days)

        try:
            tournament_query = select(Tournament).where(
                Tournament.date >= start_date,
                Tournament.date <= snapshot_date,
                Tournament.format == game_format,
                Tournament.best_of == best_of,
            )

            if region:
                tournament_query = tournament_query.where(Tournament.region == region)

            result = await self.session.execute(tournament_query)
            tournaments = result.scalars().all()
        except SQLAlchemyError:
            logger.error(
                "Failed to query tournaments: region=%s, format=%s, best_of=%s",
                region,
                game_format,
                best_of,
                exc_info=True,
            )
            raise

        if not tournaments:
            logger.warning(
                "No tournaments found for snapshot: region=%s, format=%s, best_of=%s",
                region,
                game_format,
                best_of,
            )
            return self._create_empty_snapshot(
                snapshot_date, region, game_format, best_of
            )

        tournament_ids = [t.id for t in tournaments]
        tournament_names = [str(t.id) for t in tournaments]

        try:
            placement_query = select(TournamentPlacement).where(
                TournamentPlacement.tournament_id.in_(tournament_ids)
            )
            placement_result = await self.session.execute(placement_query)
            placements = placement_result.scalars().all()
        except SQLAlchemyError:
            logger.error(
                "Failed to query placements for tournaments %s",
                tournament_ids,
                exc_info=True,
            )
            raise

        if not placements:
            logger.warning("No placements found for tournaments: %s", tournament_ids)
            return self._create_empty_snapshot(
                snapshot_date, region, game_format, best_of
            )

        archetype_shares = self._compute_archetype_shares(placements)
        card_usage = self._compute_card_usage(placements)

        snapshot = MetaSnapshot(
            id=uuid4(),
            snapshot_date=snapshot_date,
            region=region,
            format=game_format,
            best_of=best_of,
            archetype_shares=archetype_shares,
            card_usage=card_usage if card_usage else None,
            sample_size=len(placements),
            tournaments_included=tournament_names,
        )

        return snapshot

    async def save_snapshot(self, snapshot: MetaSnapshot) -> MetaSnapshot:
        """Save a meta snapshot to the database.

        If a snapshot with the same dimensions already exists, it will be updated.
        Dimensions are: snapshot_date, region, format, and best_of.

        Args:
            snapshot: The snapshot to save.

        Returns:
            The saved snapshot.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        try:
            existing_query = select(MetaSnapshot).where(
                MetaSnapshot.snapshot_date == snapshot.snapshot_date,
                MetaSnapshot.format == snapshot.format,
                MetaSnapshot.best_of == snapshot.best_of,
            )

            if snapshot.region is None:
                existing_query = existing_query.where(MetaSnapshot.region.is_(None))
            else:
                existing_query = existing_query.where(
                    MetaSnapshot.region == snapshot.region
                )

            result = await self.session.execute(existing_query)
            existing = result.scalar_one_or_none()

            if existing:
                existing.archetype_shares = snapshot.archetype_shares
                existing.card_usage = snapshot.card_usage
                existing.sample_size = snapshot.sample_size
                existing.tournaments_included = snapshot.tournaments_included
                await self.session.commit()
                await self.session.refresh(existing)
                return existing
            else:
                self.session.add(snapshot)
                await self.session.commit()
                await self.session.refresh(snapshot)
                return snapshot
        except SQLAlchemyError:
            logger.error(
                "Failed to save meta snapshot: date=%s, region=%s, format=%s",
                snapshot.snapshot_date,
                snapshot.region,
                snapshot.format,
                exc_info=True,
            )
            await self.session.rollback()
            raise

    async def get_snapshot(
        self,
        *,
        snapshot_date: date,
        region: str | None = None,
        game_format: Literal["standard", "expanded"] = "standard",
        best_of: Literal[1, 3] = 3,
    ) -> MetaSnapshot | None:
        """Get a meta snapshot by its dimensions.

        Args:
            snapshot_date: The snapshot date.
            region: Region filter or None for global.
            game_format: Game format.
            best_of: Match format.

        Returns:
            MetaSnapshot if found, None otherwise.

        Raises:
            SQLAlchemyError: If database query fails.
        """
        query = select(MetaSnapshot).where(
            MetaSnapshot.snapshot_date == snapshot_date,
            MetaSnapshot.format == game_format,
            MetaSnapshot.best_of == best_of,
        )

        if region is None:
            query = query.where(MetaSnapshot.region.is_(None))
        else:
            query = query.where(MetaSnapshot.region == region)

        try:
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
        except SQLAlchemyError:
            logger.error(
                "Failed to get snapshot: date=%s, region=%s, format=%s, best_of=%s",
                snapshot_date,
                region,
                game_format,
                best_of,
                exc_info=True,
            )
            raise

    def _compute_archetype_shares(
        self, placements: Sequence[TournamentPlacement]
    ) -> dict[str, float]:
        """Compute archetype share percentages from placements.

        Args:
            placements: Sequence of tournament placements.

        Returns:
            Dict mapping archetype name to share percentage (0.0-1.0).
        """
        if not placements:
            return {}

        archetype_counts: dict[str, int] = defaultdict(int)
        total = len(placements)

        for placement in placements:
            archetype_counts[placement.archetype] += 1

        shares = {
            archetype: count / total
            for archetype, count in sorted(
                archetype_counts.items(), key=lambda x: x[1], reverse=True
            )
        }

        return shares

    def _compute_card_usage(
        self, placements: Sequence[TournamentPlacement]
    ) -> dict[str, dict[str, float]]:
        """Compute card usage rates from placements with decklists.

        Args:
            placements: Sequence of tournament placements.

        Returns:
            Dict mapping card_id to usage stats (values are rounded):
            {"card_id": {"inclusion_rate": 0.85, "avg_count": 3.2}}
        """
        placements_with_lists = [p for p in placements if p.decklist]

        if not placements_with_lists:
            return {}

        total_lists = len(placements_with_lists)
        card_appearances: dict[str, int] = defaultdict(int)
        card_total_count: dict[str, int] = defaultdict(int)

        # Track data quality issues
        invalid_entry_count = 0
        invalid_quantity_count = 0
        empty_card_id_count = 0

        for placement in placements_with_lists:
            seen_cards: set[str] = set()
            for card_entry in placement.decklist or []:
                if not isinstance(card_entry, dict):
                    invalid_entry_count += 1
                    continue

                card_id = card_entry.get("card_id", "")
                if not card_id:
                    empty_card_id_count += 1
                    continue

                raw_quantity = card_entry.get("quantity", 1)

                try:
                    quantity = int(raw_quantity)
                    if quantity < 1:
                        invalid_quantity_count += 1
                        continue
                except (TypeError, ValueError):
                    invalid_quantity_count += 1
                    continue

                if card_id not in seen_cards:
                    card_appearances[card_id] += 1
                    seen_cards.add(card_id)

                card_total_count[card_id] += quantity

        # Log aggregate data quality issues
        has_issues = (
            invalid_entry_count > 0
            or invalid_quantity_count > 0
            or empty_card_id_count > 0
        )
        if has_issues:
            logger.warning(
                "Data quality issues in card_usage computation: "
                "invalid_entries=%d, invalid_quantities=%d, empty_card_ids=%d, "
                "total_placements=%d",
                invalid_entry_count,
                invalid_quantity_count,
                empty_card_id_count,
                len(placements_with_lists),
            )

        card_usage = {}
        for card_id in card_appearances:
            inclusion_rate = card_appearances[card_id] / total_lists
            avg_count = card_total_count[card_id] / card_appearances[card_id]
            card_usage[card_id] = {
                "inclusion_rate": round(inclusion_rate, 4),
                "avg_count": round(avg_count, 2),
            }

        return dict(
            sorted(
                card_usage.items(), key=lambda x: x[1]["inclusion_rate"], reverse=True
            )
        )

    def _create_empty_snapshot(
        self,
        snapshot_date: date,
        region: str | None,
        game_format: str,
        best_of: int,
    ) -> MetaSnapshot:
        """Create an empty snapshot when no data is available."""
        return MetaSnapshot(
            id=uuid4(),
            snapshot_date=snapshot_date,
            region=region,
            format=game_format,
            best_of=best_of,
            archetype_shares={},
            card_usage=None,
            sample_size=0,
            tournaments_included=[],
            diversity_index=None,
            tier_assignments=None,
            jp_signals=None,
            trends=None,
        )

    def compute_diversity_index(self, shares: dict[str, float]) -> Decimal | None:
        """Compute Simpson's diversity index from archetype shares.

        Simpson's diversity index: 1 - sum(share^2)
        Range 0-1, where higher values indicate more diverse meta.

        Args:
            shares: Dict mapping archetype names to their shares (0.0-1.0).

        Returns:
            Diversity index as Decimal, or None if no shares.
        """
        if not shares:
            return None

        sum_squared = sum(share**2 for share in shares.values())
        return Decimal(str(round(1 - sum_squared, 4)))

    def compute_tier_assignments(self, shares: dict[str, float]) -> dict[str, str]:
        """Assign tiers to archetypes based on meta share.

        Tier thresholds:
        - S: >15%
        - A: 8-15%
        - B: 3-8%
        - C: 1-3%
        - Rogue: <1%

        Args:
            shares: Dict mapping archetype names to their shares (0.0-1.0).

        Returns:
            Dict mapping archetype names to tier strings.
        """
        tiers: dict[str, str] = {}

        for archetype, share in shares.items():
            if share > TIER_S_THRESHOLD:
                tiers[archetype] = "S"
            elif share > TIER_A_THRESHOLD:
                tiers[archetype] = "A"
            elif share > TIER_B_THRESHOLD:
                tiers[archetype] = "B"
            elif share > TIER_C_THRESHOLD:
                tiers[archetype] = "C"
            else:
                tiers[archetype] = "Rogue"

        return tiers

    async def compute_jp_signals(
        self,
        snapshot_date: date,
        game_format: Literal["standard", "expanded"] = "standard",
        lookback_days: int = 90,
    ) -> dict | None:
        """Compute JP vs EN meta divergence signals.

        Compares JP (BO1) meta shares against EN (BO3) meta shares
        and identifies archetypes with significant divergence (>5%).

        Args:
            snapshot_date: Reference date for comparison.
            game_format: Game format to compare.
            lookback_days: Days to look back for data.

        Returns:
            Dict with rising/falling/divergent lists, or None if insufficient data.
        """
        # Get JP snapshot (BO1)
        jp_snapshot = await self.get_snapshot(
            snapshot_date=snapshot_date,
            region="JP",
            game_format=game_format,
            best_of=1,
        )

        # Get global/EN snapshot (BO3)
        en_snapshot = await self.get_snapshot(
            snapshot_date=snapshot_date,
            region=None,  # Global includes EN data
            game_format=game_format,
            best_of=3,
        )

        if not jp_snapshot or not en_snapshot:
            return None

        jp_shares = jp_snapshot.archetype_shares or {}
        en_shares = en_snapshot.archetype_shares or {}

        all_archetypes = set(jp_shares.keys()) | set(en_shares.keys())

        rising: list[str] = []  # Higher in JP
        falling: list[str] = []  # Lower in JP
        divergent: list[dict] = []

        for archetype in all_archetypes:
            jp_share = jp_shares.get(archetype, 0.0)
            en_share = en_shares.get(archetype, 0.0)
            diff = jp_share - en_share

            if abs(diff) > JP_SIGNAL_THRESHOLD:
                divergent.append(
                    {
                        "archetype": archetype,
                        "jp_share": round(jp_share, 4),
                        "en_share": round(en_share, 4),
                        "diff": round(diff, 4),
                    }
                )

                if diff > 0:
                    rising.append(archetype)
                else:
                    falling.append(archetype)

        if not divergent:
            return None

        return {
            "rising": rising,
            "falling": falling,
            "divergent": sorted(divergent, key=lambda x: abs(x["diff"]), reverse=True),
        }

    async def compute_trends(
        self,
        current_shares: dict[str, float],
        snapshot_date: date,
        region: str | None,
        game_format: Literal["standard", "expanded"],
        best_of: Literal[1, 3],
    ) -> dict | None:
        """Compute week-over-week trends for archetypes.

        Args:
            current_shares: Current archetype shares.
            snapshot_date: Current snapshot date.
            region: Region filter.
            game_format: Game format.
            best_of: Match format.

        Returns:
            Dict mapping archetypes to trend info, or None if no previous data.
        """
        previous_date = snapshot_date - timedelta(days=7)

        previous_snapshot = await self.get_snapshot(
            snapshot_date=previous_date,
            region=region,
            game_format=game_format,
            best_of=best_of,
        )

        if not previous_snapshot:
            return None

        previous_shares = previous_snapshot.archetype_shares or {}
        all_archetypes = set(current_shares.keys()) | set(previous_shares.keys())

        trends: dict[str, dict] = {}

        for archetype in all_archetypes:
            current = current_shares.get(archetype, 0.0)
            previous = previous_shares.get(archetype, 0.0)
            change = current - previous

            if abs(change) < 0.005:  # Less than 0.5% change
                direction = "stable"
            elif change > 0:
                direction = "up"
            else:
                direction = "down"

            trends[archetype] = {
                "change": round(change, 4),
                "direction": direction,
                "previous_share": round(previous, 4) if previous > 0 else None,
            }

        return trends

    async def compute_enhanced_meta_snapshot(
        self,
        *,
        snapshot_date: date,
        region: str | None = None,
        game_format: Literal["standard", "expanded"] = "standard",
        best_of: Literal[1, 3] = 3,
        lookback_days: int = 90,
    ) -> MetaSnapshot:
        """Compute an enhanced meta snapshot with diversity, tiers, and trends.

        This is an enhanced version of compute_meta_snapshot that also computes:
        - diversity_index: Simpson's diversity index
        - tier_assignments: S/A/B/C/Rogue tiers
        - jp_signals: JP vs EN divergence (for non-JP snapshots)
        - trends: Week-over-week changes

        Args:
            snapshot_date: Reference date for the snapshot.
            region: Region filter or None for global.
            game_format: Game format.
            best_of: Match format.
            lookback_days: Days to look back for tournament data.

        Returns:
            MetaSnapshot with all enhanced fields populated.
        """
        # First compute the base snapshot
        snapshot = await self.compute_meta_snapshot(
            snapshot_date=snapshot_date,
            region=region,
            game_format=game_format,
            best_of=best_of,
            lookback_days=lookback_days,
        )

        if snapshot.sample_size == 0:
            return snapshot

        shares = snapshot.archetype_shares

        # Compute enhanced fields
        snapshot.diversity_index = self.compute_diversity_index(shares)
        snapshot.tier_assignments = self.compute_tier_assignments(shares)

        # Compute JP signals (only for non-JP, BO3 snapshots)
        if region != "JP" and best_of == 3:
            snapshot.jp_signals = await self.compute_jp_signals(
                snapshot_date=snapshot_date,
                game_format=game_format,
                lookback_days=lookback_days,
            )

        # Compute trends
        snapshot.trends = await self.compute_trends(
            current_shares=shares,
            snapshot_date=snapshot_date,
            region=region,
            game_format=game_format,
            best_of=best_of,
        )

        return snapshot
