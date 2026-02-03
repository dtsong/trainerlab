"""Service for computing archetype evolution snapshots and adaptations.

Orchestrates snapshot computation from tournament data and diff-based
adaptation detection between consecutive snapshots.
"""

import logging
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.adaptation import Adaptation
from src.models.archetype_evolution_snapshot import ArchetypeEvolutionSnapshot
from src.models.tournament import Tournament
from src.models.tournament_placement import TournamentPlacement
from src.services.decklist_diff import DecklistDiffEngine

logger = logging.getLogger(__name__)


class EvolutionError(Exception):
    """Base exception for evolution service errors."""


class EvolutionSnapshotNotFoundError(EvolutionError):
    """Raised when a requested snapshot does not exist."""


class EvolutionService:
    """Service for computing and managing archetype evolution data."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.diff_engine = DecklistDiffEngine()

    async def compute_tournament_snapshot(
        self,
        archetype: str,
        tournament_id: UUID,
    ) -> ArchetypeEvolutionSnapshot:
        """Compute an evolution snapshot for an archetype at a tournament.

        Queries all placements for the archetype in the given tournament,
        computes performance metrics, and builds a consensus decklist.

        Args:
            archetype: Normalized archetype name.
            tournament_id: Tournament to compute snapshot for.

        Returns:
            ArchetypeEvolutionSnapshot (not yet persisted).

        Raises:
            EvolutionError: If tournament not found or no placements.
        """
        # Get the tournament
        tournament_result = await self.session.execute(
            select(Tournament).where(Tournament.id == tournament_id)
        )
        tournament = tournament_result.scalar_one_or_none()
        if not tournament:
            raise EvolutionError(f"Tournament {tournament_id} not found")

        # Get placements for this archetype
        placements_result = await self.session.execute(
            select(TournamentPlacement).where(
                TournamentPlacement.tournament_id == tournament_id,
                TournamentPlacement.archetype == archetype,
            )
        )
        placements = list(placements_result.scalars().all())

        if not placements:
            msg = f"No placements for '{archetype}' in tournament {tournament_id}"
            raise EvolutionError(msg)

        # Compute total placements in tournament for meta share
        total_result = await self.session.execute(
            select(TournamentPlacement).where(
                TournamentPlacement.tournament_id == tournament_id,
            )
        )
        total_placements = list(total_result.scalars().all())
        total_count = len(total_placements)

        # Performance metrics
        deck_count = len(placements)
        meta_share = deck_count / total_count if total_count > 0 else 0.0
        best_placement = min(p.placement for p in placements)

        # Top cut conversion (top 8 out of this archetype's entries)
        top_cut = sum(1 for p in placements if p.placement <= 8)
        top_cut_conversion = top_cut / deck_count if deck_count > 0 else 0.0

        # Build consensus decklist from available decklists
        decklists = [p.decklist for p in placements if p.decklist]
        consensus_list = (
            self.diff_engine.compute_consensus_list(decklists) if decklists else None
        )

        # Card usage stats
        card_usage = self._compute_card_usage(decklists) if decklists else None

        return ArchetypeEvolutionSnapshot(
            id=uuid4(),
            archetype=archetype,
            tournament_id=tournament_id,
            meta_share=round(meta_share, 4),
            top_cut_conversion=round(top_cut_conversion, 4),
            best_placement=best_placement,
            deck_count=deck_count,
            consensus_list=consensus_list,
            card_usage=card_usage,
        )

    def _compute_card_usage(self, decklists: list[list[dict]]) -> dict:
        """Compute per-card usage statistics across decklists.

        Args:
            decklists: List of decklists.

        Returns:
            Dict mapping card_name to usage stats.
        """
        if not decklists:
            return {}

        total = len(decklists)
        card_data: dict[str, list[int]] = {}

        for decklist in decklists:
            aggregated = self.diff_engine._aggregate_decklist(decklist)
            for card_name, quantity in aggregated.items():
                if card_name not in card_data:
                    card_data[card_name] = []
                card_data[card_name].append(quantity)

        usage: dict[str, dict] = {}
        for card_name, counts in card_data.items():
            avg_count = sum(counts) / len(counts)
            inclusion_rate = len(counts) / total
            usage[card_name] = {
                "name": card_name,
                "avg_count": round(avg_count, 2),
                "inclusion_rate": round(inclusion_rate, 3),
            }

        return usage

    async def compute_adaptations(
        self,
        from_snapshot_id: UUID,
        to_snapshot_id: UUID,
    ) -> list[Adaptation]:
        """Compute adaptations between two consecutive snapshots.

        Runs the diff engine on consensus lists and creates unclassified
        Adaptation records for each change detected.

        Args:
            from_snapshot_id: Earlier snapshot ID.
            to_snapshot_id: Later snapshot ID.

        Returns:
            List of Adaptation records (not yet persisted).

        Raises:
            EvolutionSnapshotNotFoundError: If either snapshot not found.
        """
        from_snapshot = await self._get_snapshot(from_snapshot_id)
        to_snapshot = await self._get_snapshot(to_snapshot_id)

        old_consensus = from_snapshot.consensus_list or []
        new_consensus = to_snapshot.consensus_list or []

        diff_result = self.diff_engine.diff(old_consensus, new_consensus)

        adaptations: list[Adaptation] = []

        for card_change in diff_result.added:
            name = card_change.card_name
            qty = card_change.new_quantity
            adaptations.append(
                Adaptation(
                    id=uuid4(),
                    snapshot_id=to_snapshot_id,
                    type="tech",
                    description=f"Added {name} (x{qty})",
                    cards_added=[{"name": name, "quantity": qty}],
                    source="diff",
                )
            )

        for card_change in diff_result.removed:
            name = card_change.card_name
            qty = card_change.old_quantity
            adaptations.append(
                Adaptation(
                    id=uuid4(),
                    snapshot_id=to_snapshot_id,
                    type="removal",
                    description=f"Removed {name} (was x{qty})",
                    cards_removed=[{"name": name, "quantity": qty}],
                    source="diff",
                )
            )

        for card_change in diff_result.changed:
            name = card_change.card_name
            old_qty = card_change.old_quantity
            new_qty = card_change.new_quantity
            direction = "increased" if card_change.change > 0 else "decreased"
            adaptations.append(
                Adaptation(
                    id=uuid4(),
                    snapshot_id=to_snapshot_id,
                    type="consistency",
                    description=(f"{name} {direction} from x{old_qty} to x{new_qty}"),
                    cards_added=(
                        [{"name": name, "quantity": new_qty}]
                        if card_change.change > 0
                        else None
                    ),
                    cards_removed=(
                        [{"name": name, "quantity": old_qty}]
                        if card_change.change < 0
                        else None
                    ),
                    source="diff",
                )
            )

        return adaptations

    async def get_evolution_timeline(
        self,
        archetype: str,
        limit: int = 10,
    ) -> list[ArchetypeEvolutionSnapshot]:
        """Get the evolution timeline for an archetype.

        Args:
            archetype: Normalized archetype name.
            limit: Maximum number of snapshots to return.

        Returns:
            List of snapshots ordered by tournament date (most recent first).
        """
        query = (
            select(ArchetypeEvolutionSnapshot)
            .join(Tournament, ArchetypeEvolutionSnapshot.tournament_id == Tournament.id)
            .where(ArchetypeEvolutionSnapshot.archetype == archetype)
            .order_by(Tournament.date.desc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_previous_snapshot(
        self,
        archetype: str,
        tournament_id: UUID,
    ) -> ArchetypeEvolutionSnapshot | None:
        """Get the snapshot immediately before the given tournament.

        Args:
            archetype: Normalized archetype name.
            tournament_id: Current tournament ID (to find the one before it).

        Returns:
            Previous snapshot or None if this is the first.
        """
        # Get the current tournament's date
        tournament_result = await self.session.execute(
            select(Tournament.date).where(Tournament.id == tournament_id)
        )
        row = tournament_result.one_or_none()
        if not row:
            return None
        current_date = row[0]

        # Find the most recent snapshot before this tournament
        query = (
            select(ArchetypeEvolutionSnapshot)
            .join(Tournament, ArchetypeEvolutionSnapshot.tournament_id == Tournament.id)
            .where(
                ArchetypeEvolutionSnapshot.archetype == archetype,
                Tournament.date < current_date,
            )
            .order_by(Tournament.date.desc())
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def save_snapshot(self, snapshot: ArchetypeEvolutionSnapshot) -> None:
        """Save a snapshot, handling upsert on unique constraint.

        Args:
            snapshot: The snapshot to save.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        try:
            # Check for existing snapshot
            existing_result = await self.session.execute(
                select(ArchetypeEvolutionSnapshot).where(
                    ArchetypeEvolutionSnapshot.archetype == snapshot.archetype,
                    ArchetypeEvolutionSnapshot.tournament_id == snapshot.tournament_id,
                )
            )
            existing = existing_result.scalar_one_or_none()

            if existing:
                # Update existing snapshot
                existing.meta_share = snapshot.meta_share
                existing.top_cut_conversion = snapshot.top_cut_conversion
                existing.best_placement = snapshot.best_placement
                existing.deck_count = snapshot.deck_count
                existing.consensus_list = snapshot.consensus_list
                existing.card_usage = snapshot.card_usage
                existing.meta_context = snapshot.meta_context
                await self.session.commit()
            else:
                self.session.add(snapshot)
                await self.session.commit()

        except IntegrityError:
            await self.session.rollback()
            logger.warning(
                "Integrity error saving snapshot: archetype=%s, tournament=%s",
                snapshot.archetype,
                snapshot.tournament_id,
            )
            raise

        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def _get_snapshot(self, snapshot_id: UUID) -> ArchetypeEvolutionSnapshot:
        """Get a snapshot by ID or raise EvolutionSnapshotNotFoundError."""
        result = await self.session.execute(
            select(ArchetypeEvolutionSnapshot).where(
                ArchetypeEvolutionSnapshot.id == snapshot_id
            )
        )
        snapshot = result.scalar_one_or_none()
        if not snapshot:
            raise EvolutionSnapshotNotFoundError(f"Snapshot {snapshot_id} not found")
        return snapshot
