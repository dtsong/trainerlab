"""Tests for the EvolutionService."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.models.archetype_evolution_snapshot import ArchetypeEvolutionSnapshot
from src.models.tournament import Tournament
from src.models.tournament_placement import TournamentPlacement
from src.services.evolution_service import (
    EvolutionError,
    EvolutionService,
    EvolutionSnapshotNotFoundError,
)

_UNSET = object()


def _make_execute_result(
    *, scalar_one_or_none=_UNSET, scalars_all=_UNSET, one_or_none=_UNSET
):
    """Create a mock result from session.execute().

    AsyncMock.execute returns a coroutine wrapping this MagicMock,
    so chained calls like result.scalar_one_or_none() are sync.
    """
    mock_result = MagicMock()
    if scalar_one_or_none is not _UNSET:
        mock_result.scalar_one_or_none.return_value = scalar_one_or_none
    if scalars_all is not _UNSET:
        mock_result.scalars.return_value.all.return_value = scalars_all
    if one_or_none is not _UNSET:
        mock_result.one_or_none.return_value = one_or_none
    return mock_result


def _make_placement(
    archetype: str = "Charizard ex",
    placement: int = 1,
    decklist: list[dict] | None = None,
    tournament_id=None,
) -> MagicMock:
    """Helper to create a mock TournamentPlacement."""
    mock = MagicMock(spec=TournamentPlacement)
    mock.archetype = archetype
    mock.placement = placement
    mock.decklist = decklist
    mock.tournament_id = tournament_id or uuid4()
    return mock


def _make_tournament(
    tournament_id=None,
    tier="major",
    participant_count=256,
    tournament_date=None,
) -> MagicMock:
    """Helper to create a mock Tournament."""
    mock = MagicMock(spec=Tournament)
    mock.id = tournament_id or uuid4()
    mock.tier = tier
    mock.participant_count = participant_count
    mock.date = tournament_date or date(2026, 1, 15)
    return mock


class TestComputeTournamentSnapshot:
    """Tests for snapshot computation from tournament data."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> EvolutionService:
        return EvolutionService(mock_session)

    @pytest.mark.asyncio
    async def test_raises_when_tournament_not_found(
        self, service: EvolutionService, mock_session: AsyncMock
    ) -> None:
        """Should raise EvolutionError when tournament doesn't exist."""
        mock_session.execute.return_value = _make_execute_result(
            scalar_one_or_none=None
        )

        with pytest.raises(EvolutionError, match="not found"):
            await service.compute_tournament_snapshot("Charizard ex", uuid4())

    @pytest.mark.asyncio
    async def test_raises_when_no_placements(
        self, service: EvolutionService, mock_session: AsyncMock
    ) -> None:
        """Should raise EvolutionError when archetype has no placements."""
        tournament = _make_tournament()

        mock_session.execute.side_effect = [
            _make_execute_result(scalar_one_or_none=tournament),
            _make_execute_result(scalars_all=[]),
        ]

        with pytest.raises(EvolutionError, match="No placements"):
            await service.compute_tournament_snapshot("Charizard ex", tournament.id)

    @pytest.mark.asyncio
    async def test_computes_correct_metrics(
        self, service: EvolutionService, mock_session: AsyncMock
    ) -> None:
        """Should compute meta_share, top_cut_conversion, best_placement."""
        tournament = _make_tournament()
        tid = tournament.id

        charizard_placements = [
            _make_placement("Charizard ex", 1, tournament_id=tid),
            _make_placement("Charizard ex", 5, tournament_id=tid),
            _make_placement("Charizard ex", 12, tournament_id=tid),
            _make_placement("Charizard ex", 20, tournament_id=tid),
        ]

        all_placements = charizard_placements + [
            _make_placement("Dragapult ex", 2, tournament_id=tid),
            _make_placement("Dragapult ex", 3, tournament_id=tid),
            _make_placement("Lugia VSTAR", 4, tournament_id=tid),
            _make_placement("Gardevoir ex", 6, tournament_id=tid),
            _make_placement("Gardevoir ex", 7, tournament_id=tid),
            _make_placement("Raging Bolt ex", 8, tournament_id=tid),
        ]

        mock_session.execute.side_effect = [
            _make_execute_result(scalar_one_or_none=tournament),
            _make_execute_result(scalars_all=charizard_placements),
            _make_execute_result(scalars_all=all_placements),
        ]

        snapshot = await service.compute_tournament_snapshot("Charizard ex", tid)

        assert snapshot.archetype == "Charizard ex"
        assert snapshot.tournament_id == tid
        assert snapshot.deck_count == 4
        assert snapshot.meta_share == round(4 / 10, 4)
        assert snapshot.best_placement == 1
        # 2 of 4 in top 8 (placements 1 and 5)
        assert snapshot.top_cut_conversion == round(2 / 4, 4)

    @pytest.mark.asyncio
    async def test_builds_consensus_from_decklists(
        self, service: EvolutionService, mock_session: AsyncMock
    ) -> None:
        """Should compute consensus list from available decklists."""
        tournament = _make_tournament()
        tid = tournament.id

        decklist_a = [
            {"card_id": "a", "name": "CardA", "quantity": 4},
            {"card_id": "b", "name": "CardB", "quantity": 3},
        ]
        decklist_b = [
            {"card_id": "a", "name": "CardA", "quantity": 4},
            {"card_id": "b", "name": "CardB", "quantity": 2},
            {"card_id": "c", "name": "CardC", "quantity": 1},
        ]

        placements = [
            _make_placement("Test", 1, decklist=decklist_a, tournament_id=tid),
            _make_placement("Test", 2, decklist=decklist_b, tournament_id=tid),
            _make_placement("Test", 3, decklist=None, tournament_id=tid),
        ]

        mock_session.execute.side_effect = [
            _make_execute_result(scalar_one_or_none=tournament),
            _make_execute_result(scalars_all=placements),
            _make_execute_result(scalars_all=placements),
        ]

        snapshot = await service.compute_tournament_snapshot("Test", tid)

        assert snapshot.consensus_list is not None
        names = [c["name"] for c in snapshot.consensus_list]
        assert "CardA" in names
        assert "CardB" in names
        # CardC only in 1 of 2 decklists = 50%, meets threshold
        assert "CardC" in names

    @pytest.mark.asyncio
    async def test_no_consensus_without_decklists(
        self, service: EvolutionService, mock_session: AsyncMock
    ) -> None:
        """Should produce None consensus when no decklists available."""
        tournament = _make_tournament()
        tid = tournament.id

        placements = [
            _make_placement("Test", 1, decklist=None, tournament_id=tid),
            _make_placement("Test", 5, decklist=None, tournament_id=tid),
        ]

        mock_session.execute.side_effect = [
            _make_execute_result(scalar_one_or_none=tournament),
            _make_execute_result(scalars_all=placements),
            _make_execute_result(scalars_all=placements),
        ]

        snapshot = await service.compute_tournament_snapshot("Test", tid)
        assert snapshot.consensus_list is None
        assert snapshot.card_usage is None


class TestComputeAdaptations:
    """Tests for adaptation computation between snapshots."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> EvolutionService:
        return EvolutionService(mock_session)

    @pytest.mark.asyncio
    async def test_raises_when_snapshot_not_found(
        self, service: EvolutionService, mock_session: AsyncMock
    ) -> None:
        """Should raise EvolutionSnapshotNotFoundError."""
        mock_session.execute.return_value = _make_execute_result(
            scalar_one_or_none=None
        )

        with pytest.raises(EvolutionSnapshotNotFoundError):
            await service.compute_adaptations(uuid4(), uuid4())

    @pytest.mark.asyncio
    async def test_detects_card_additions(
        self, service: EvolutionService, mock_session: AsyncMock
    ) -> None:
        """Should create adaptation records for added cards."""
        old_snapshot = MagicMock(spec=ArchetypeEvolutionSnapshot)
        old_snapshot.consensus_list = [
            {"name": "CardA", "quantity": 4, "inclusion_rate": 1.0},
        ]

        new_snapshot = MagicMock(spec=ArchetypeEvolutionSnapshot)
        new_snapshot.consensus_list = [
            {"name": "CardA", "quantity": 4, "inclusion_rate": 1.0},
            {"name": "CardB", "quantity": 2, "inclusion_rate": 0.7},
        ]

        mock_session.execute.side_effect = [
            _make_execute_result(scalar_one_or_none=old_snapshot),
            _make_execute_result(scalar_one_or_none=new_snapshot),
        ]

        adaptations = await service.compute_adaptations(uuid4(), uuid4())

        assert len(adaptations) == 1
        assert adaptations[0].type == "tech"
        assert "CardB" in adaptations[0].description

    @pytest.mark.asyncio
    async def test_detects_card_removals(
        self, service: EvolutionService, mock_session: AsyncMock
    ) -> None:
        """Should create adaptation records for removed cards."""
        old_snapshot = MagicMock(spec=ArchetypeEvolutionSnapshot)
        old_snapshot.consensus_list = [
            {"name": "CardA", "quantity": 4, "inclusion_rate": 1.0},
            {"name": "CardB", "quantity": 2, "inclusion_rate": 0.8},
        ]

        new_snapshot = MagicMock(spec=ArchetypeEvolutionSnapshot)
        new_snapshot.consensus_list = [
            {"name": "CardA", "quantity": 4, "inclusion_rate": 1.0},
        ]

        mock_session.execute.side_effect = [
            _make_execute_result(scalar_one_or_none=old_snapshot),
            _make_execute_result(scalar_one_or_none=new_snapshot),
        ]

        adaptations = await service.compute_adaptations(uuid4(), uuid4())

        assert len(adaptations) == 1
        assert adaptations[0].type == "removal"
        assert "CardB" in adaptations[0].description

    @pytest.mark.asyncio
    async def test_no_adaptations_for_identical_snapshots(
        self, service: EvolutionService, mock_session: AsyncMock
    ) -> None:
        """Should return empty list when consensus lists are identical."""
        consensus = [{"name": "CardA", "quantity": 4, "inclusion_rate": 1.0}]

        snapshot = MagicMock(spec=ArchetypeEvolutionSnapshot)
        snapshot.consensus_list = consensus

        mock_session.execute.return_value = _make_execute_result(
            scalar_one_or_none=snapshot
        )

        adaptations = await service.compute_adaptations(uuid4(), uuid4())
        assert adaptations == []

    @pytest.mark.asyncio
    async def test_handles_null_consensus_lists(
        self, service: EvolutionService, mock_session: AsyncMock
    ) -> None:
        """Should handle snapshots with None consensus lists."""
        old_snapshot = MagicMock(spec=ArchetypeEvolutionSnapshot)
        old_snapshot.consensus_list = None

        new_snapshot = MagicMock(spec=ArchetypeEvolutionSnapshot)
        new_snapshot.consensus_list = [
            {"name": "CardA", "quantity": 4, "inclusion_rate": 1.0},
        ]

        mock_session.execute.side_effect = [
            _make_execute_result(scalar_one_or_none=old_snapshot),
            _make_execute_result(scalar_one_or_none=new_snapshot),
        ]

        adaptations = await service.compute_adaptations(uuid4(), uuid4())
        assert len(adaptations) == 1
        assert adaptations[0].type == "tech"


class TestSaveSnapshot:
    """Tests for snapshot persistence."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> EvolutionService:
        return EvolutionService(mock_session)

    @pytest.mark.asyncio
    async def test_creates_new_snapshot(
        self, service: EvolutionService, mock_session: AsyncMock
    ) -> None:
        """Should add new snapshot when none exists."""
        mock_session.execute.return_value = _make_execute_result(
            scalar_one_or_none=None
        )

        snapshot = ArchetypeEvolutionSnapshot(
            id=uuid4(),
            archetype="Charizard ex",
            tournament_id=uuid4(),
            deck_count=5,
        )

        await service.save_snapshot(snapshot)
        mock_session.add.assert_called_once_with(snapshot)
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_updates_existing_snapshot(
        self, service: EvolutionService, mock_session: AsyncMock
    ) -> None:
        """Should update fields when snapshot already exists."""
        existing = MagicMock(spec=ArchetypeEvolutionSnapshot)
        mock_session.execute.return_value = _make_execute_result(
            scalar_one_or_none=existing
        )

        snapshot = ArchetypeEvolutionSnapshot(
            id=uuid4(),
            archetype="Charizard ex",
            tournament_id=uuid4(),
            meta_share=0.15,
            deck_count=8,
            best_placement=2,
        )

        await service.save_snapshot(snapshot)
        assert existing.meta_share == 0.15
        assert existing.deck_count == 8
        mock_session.commit.assert_called_once()


class TestGetEvolutionTimeline:
    """Tests for timeline queries."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> EvolutionService:
        return EvolutionService(mock_session)

    @pytest.mark.asyncio
    async def test_returns_snapshots_ordered_by_date(
        self, service: EvolutionService, mock_session: AsyncMock
    ) -> None:
        """Should return snapshots in reverse chronological order."""
        snapshots = [MagicMock(spec=ArchetypeEvolutionSnapshot) for _ in range(3)]

        mock_session.execute.return_value = _make_execute_result(scalars_all=snapshots)

        result = await service.get_evolution_timeline("Charizard ex", limit=10)
        assert len(result) == 3
        mock_session.execute.assert_called_once()


class TestGetPreviousSnapshot:
    """Tests for finding previous snapshots."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> EvolutionService:
        return EvolutionService(mock_session)

    @pytest.mark.asyncio
    async def test_returns_none_when_no_previous(
        self, service: EvolutionService, mock_session: AsyncMock
    ) -> None:
        """Should return None when tournament not found."""
        mock_session.execute.return_value = _make_execute_result(one_or_none=None)

        result = await service.get_previous_snapshot("Charizard ex", uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_previous_snapshot(
        self, service: EvolutionService, mock_session: AsyncMock
    ) -> None:
        """Should return the most recent snapshot before the tournament."""
        previous = MagicMock(spec=ArchetypeEvolutionSnapshot)

        mock_session.execute.side_effect = [
            _make_execute_result(one_or_none=(date(2026, 1, 15),)),
            _make_execute_result(scalar_one_or_none=previous),
        ]

        result = await service.get_previous_snapshot("Charizard ex", uuid4())
        assert result is previous
