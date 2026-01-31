"""Tests for meta snapshot service."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.exc import SQLAlchemyError

from src.models import MetaSnapshot, Tournament, TournamentPlacement
from src.services.meta_service import MetaService


class TestComputeArchetypeShares:
    """Tests for archetype share computation."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> MetaService:
        return MetaService(mock_session)

    def test_computes_shares_correctly(self, service: MetaService) -> None:
        """Should compute correct archetype percentages."""
        placements = []
        archetypes = ["Charizard ex", "Charizard ex", "Lugia VSTAR", "Gardevoir ex"]

        for archetype in archetypes:
            placement = MagicMock(spec=TournamentPlacement)
            placement.archetype = archetype
            placements.append(placement)

        shares = service._compute_archetype_shares(placements)

        assert shares["Charizard ex"] == 0.5  # 2/4
        assert shares["Lugia VSTAR"] == 0.25  # 1/4
        assert shares["Gardevoir ex"] == 0.25  # 1/4

    def test_sorts_by_share_descending(self, service: MetaService) -> None:
        """Should sort archetypes by share, highest first."""
        placements = []
        archetypes = ["A", "B", "B", "C", "C", "C"]

        for archetype in archetypes:
            placement = MagicMock(spec=TournamentPlacement)
            placement.archetype = archetype
            placements.append(placement)

        shares = service._compute_archetype_shares(placements)
        keys = list(shares.keys())

        assert keys[0] == "C"  # Most common
        assert keys[1] == "B"
        assert keys[2] == "A"  # Least common

    def test_handles_empty_list(self, service: MetaService) -> None:
        """Should handle empty placement list."""
        shares = service._compute_archetype_shares([])
        assert shares == {}


class TestComputeCardUsage:
    """Tests for card usage computation."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> MetaService:
        return MetaService(mock_session)

    def test_computes_inclusion_rate(self, service: MetaService) -> None:
        """Should compute correct card inclusion rates."""
        placements = []

        # Placement 1: has card A and B
        p1 = MagicMock(spec=TournamentPlacement)
        p1.decklist = [
            {"card_id": "card-a", "quantity": 4},
            {"card_id": "card-b", "quantity": 2},
        ]
        placements.append(p1)

        # Placement 2: has card A only
        p2 = MagicMock(spec=TournamentPlacement)
        p2.decklist = [
            {"card_id": "card-a", "quantity": 3},
        ]
        placements.append(p2)

        usage = service._compute_card_usage(placements)

        assert usage["card-a"]["inclusion_rate"] == 1.0  # In 2/2 lists
        assert usage["card-b"]["inclusion_rate"] == 0.5  # In 1/2 lists

    def test_computes_average_count(self, service: MetaService) -> None:
        """Should compute correct average card counts."""
        placements = []

        # Placement 1: 4 copies of card A
        p1 = MagicMock(spec=TournamentPlacement)
        p1.decklist = [{"card_id": "card-a", "quantity": 4}]
        placements.append(p1)

        # Placement 2: 2 copies of card A
        p2 = MagicMock(spec=TournamentPlacement)
        p2.decklist = [{"card_id": "card-a", "quantity": 2}]
        placements.append(p2)

        usage = service._compute_card_usage(placements)

        assert usage["card-a"]["avg_count"] == 3.0  # (4+2)/2

    def test_handles_no_decklists(self, service: MetaService) -> None:
        """Should return empty dict when no placements have decklists."""
        placements = []

        p1 = MagicMock(spec=TournamentPlacement)
        p1.decklist = None
        placements.append(p1)

        p2 = MagicMock(spec=TournamentPlacement)
        p2.decklist = None
        placements.append(p2)

        usage = service._compute_card_usage(placements)
        assert usage == {}

    def test_handles_mixed_decklists(self, service: MetaService) -> None:
        """Should only count placements with decklists."""
        placements = []

        # Placement with decklist
        p1 = MagicMock(spec=TournamentPlacement)
        p1.decklist = [{"card_id": "card-a", "quantity": 4}]
        placements.append(p1)

        # Placement without decklist
        p2 = MagicMock(spec=TournamentPlacement)
        p2.decklist = None
        placements.append(p2)

        usage = service._compute_card_usage(placements)

        # Inclusion rate should be 1.0 (1 out of 1 lists with decklists)
        assert usage["card-a"]["inclusion_rate"] == 1.0

    def test_sorts_by_inclusion_rate(self, service: MetaService) -> None:
        """Should sort cards by inclusion rate descending."""
        placements = []

        # 3 placements: card-a in all, card-b in 2, card-c in 1
        for i in range(3):
            p = MagicMock(spec=TournamentPlacement)
            cards = [{"card_id": "card-a", "quantity": 1}]
            if i < 2:
                cards.append({"card_id": "card-b", "quantity": 1})
            if i < 1:
                cards.append({"card_id": "card-c", "quantity": 1})
            p.decklist = cards
            placements.append(p)

        usage = service._compute_card_usage(placements)
        keys = list(usage.keys())

        assert keys[0] == "card-a"  # 100%
        assert keys[1] == "card-b"  # 66%
        assert keys[2] == "card-c"  # 33%

    def test_handles_non_dict_card_entries(self, service: MetaService) -> None:
        """Should skip non-dict entries in decklist."""
        p = MagicMock(spec=TournamentPlacement)
        p.decklist = ["invalid_string", {"card_id": "valid-card", "quantity": 2}]

        usage = service._compute_card_usage([p])

        assert "valid-card" in usage
        assert len(usage) == 1

    def test_handles_empty_card_id(self, service: MetaService) -> None:
        """Should skip entries with empty card_id."""
        p = MagicMock(spec=TournamentPlacement)
        p.decklist = [
            {"card_id": "", "quantity": 4},
            {"card_id": "valid-card", "quantity": 2},
        ]

        usage = service._compute_card_usage([p])

        assert "valid-card" in usage
        assert "" not in usage
        assert len(usage) == 1

    def test_handles_invalid_quantity_string(self, service: MetaService) -> None:
        """Should skip entries with non-numeric quantity."""
        p = MagicMock(spec=TournamentPlacement)
        p.decklist = [
            {"card_id": "bad-qty", "quantity": "not-a-number"},
            {"card_id": "good-card", "quantity": 3},
        ]

        usage = service._compute_card_usage([p])

        assert "good-card" in usage
        assert "bad-qty" not in usage
        assert len(usage) == 1

    def test_handles_invalid_quantity_zero(self, service: MetaService) -> None:
        """Should skip entries with zero or negative quantity."""
        p = MagicMock(spec=TournamentPlacement)
        p.decklist = [
            {"card_id": "zero-qty", "quantity": 0},
            {"card_id": "negative-qty", "quantity": -1},
            {"card_id": "good-card", "quantity": 1},
        ]

        usage = service._compute_card_usage([p])

        assert "good-card" in usage
        assert "zero-qty" not in usage
        assert "negative-qty" not in usage
        assert len(usage) == 1

    def test_handles_missing_card_id_key(self, service: MetaService) -> None:
        """Should skip entries missing card_id key."""
        p = MagicMock(spec=TournamentPlacement)
        p.decklist = [
            {"quantity": 4},  # Missing card_id
            {"card_id": "valid-card", "quantity": 2},
        ]

        usage = service._compute_card_usage([p])

        assert "valid-card" in usage
        assert len(usage) == 1


class TestCreateEmptySnapshot:
    """Tests for empty snapshot creation."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> MetaService:
        return MetaService(mock_session)

    def test_creates_empty_snapshot(self, service: MetaService) -> None:
        """Should create a valid empty snapshot."""
        snapshot = service._create_empty_snapshot(
            snapshot_date=date(2024, 6, 15),
            region="NA",
            game_format="standard",
            best_of=3,
        )

        assert snapshot.snapshot_date == date(2024, 6, 15)
        assert snapshot.region == "NA"
        assert snapshot.format == "standard"
        assert snapshot.best_of == 3
        assert snapshot.archetype_shares == {}
        assert snapshot.card_usage is None
        assert snapshot.sample_size == 0
        assert snapshot.tournaments_included == []

    def test_creates_global_snapshot(self, service: MetaService) -> None:
        """Should create a global snapshot with region=None."""
        snapshot = service._create_empty_snapshot(
            snapshot_date=date(2024, 6, 15),
            region=None,
            game_format="standard",
            best_of=3,
        )

        assert snapshot.region is None

    def test_creates_bo1_snapshot(self, service: MetaService) -> None:
        """Should create a BO1 snapshot for Japan."""
        snapshot = service._create_empty_snapshot(
            snapshot_date=date(2024, 6, 15),
            region="JP",
            game_format="standard",
            best_of=1,
        )

        assert snapshot.region == "JP"
        assert snapshot.best_of == 1


class TestComputeMetaSnapshotAsync:
    """Async tests for compute_meta_snapshot method."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> MetaService:
        return MetaService(mock_session)

    @pytest.mark.asyncio
    async def test_returns_empty_snapshot_when_no_tournaments(
        self, service: MetaService, mock_session: AsyncMock
    ) -> None:
        """Should return empty snapshot when no tournaments found."""
        # Mock empty tournament result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        snapshot = await service.compute_meta_snapshot(
            snapshot_date=date(2024, 6, 15),
            region="NA",
            game_format="standard",
            best_of=3,
        )

        assert snapshot.sample_size == 0
        assert snapshot.archetype_shares == {}
        assert snapshot.card_usage is None
        assert snapshot.tournaments_included == []

    @pytest.mark.asyncio
    async def test_computes_snapshot_from_tournaments(
        self, service: MetaService, mock_session: AsyncMock
    ) -> None:
        """Should compute snapshot with archetype shares from placements."""
        # Create mock tournament
        mock_tournament = MagicMock(spec=Tournament)
        mock_tournament.id = uuid4()

        # Create mock placements
        mock_placements = []
        for archetype in ["Charizard ex", "Charizard ex", "Lugia VSTAR"]:
            p = MagicMock(spec=TournamentPlacement)
            p.archetype = archetype
            p.decklist = None
            mock_placements.append(p)

        # Setup execute to return tournaments then placements
        tournament_result = MagicMock()
        tournament_result.scalars.return_value.all.return_value = [mock_tournament]

        placement_result = MagicMock()
        placement_result.scalars.return_value.all.return_value = mock_placements

        mock_session.execute.side_effect = [tournament_result, placement_result]

        snapshot = await service.compute_meta_snapshot(
            snapshot_date=date(2024, 6, 15),
            region="NA",
            game_format="standard",
            best_of=3,
        )

        assert snapshot.sample_size == 3
        assert "Charizard ex" in snapshot.archetype_shares
        assert snapshot.archetype_shares["Charizard ex"] == pytest.approx(2 / 3)
        assert snapshot.archetype_shares["Lugia VSTAR"] == pytest.approx(1 / 3)

    @pytest.mark.asyncio
    async def test_returns_empty_snapshot_when_no_placements(
        self, service: MetaService, mock_session: AsyncMock
    ) -> None:
        """Should return empty snapshot when no placements found."""
        mock_tournament = MagicMock(spec=Tournament)
        mock_tournament.id = uuid4()

        tournament_result = MagicMock()
        tournament_result.scalars.return_value.all.return_value = [mock_tournament]

        placement_result = MagicMock()
        placement_result.scalars.return_value.all.return_value = []

        mock_session.execute.side_effect = [tournament_result, placement_result]

        snapshot = await service.compute_meta_snapshot(
            snapshot_date=date(2024, 6, 15),
            region="NA",
            game_format="standard",
            best_of=3,
        )

        assert snapshot.sample_size == 0
        assert snapshot.archetype_shares == {}

    @pytest.mark.asyncio
    async def test_raises_on_tournament_query_error(
        self, service: MetaService, mock_session: AsyncMock
    ) -> None:
        """Should raise SQLAlchemyError when tournament query fails."""
        mock_session.execute.side_effect = SQLAlchemyError("Connection failed")

        with pytest.raises(SQLAlchemyError):
            await service.compute_meta_snapshot(
                snapshot_date=date(2024, 6, 15),
                region="NA",
                game_format="standard",
                best_of=3,
            )

    @pytest.mark.asyncio
    async def test_raises_on_placement_query_error(
        self, service: MetaService, mock_session: AsyncMock
    ) -> None:
        """Should raise SQLAlchemyError when placement query fails."""
        mock_tournament = MagicMock(spec=Tournament)
        mock_tournament.id = uuid4()

        tournament_result = MagicMock()
        tournament_result.scalars.return_value.all.return_value = [mock_tournament]

        mock_session.execute.side_effect = [
            tournament_result,
            SQLAlchemyError("Query failed"),
        ]

        with pytest.raises(SQLAlchemyError):
            await service.compute_meta_snapshot(
                snapshot_date=date(2024, 6, 15),
                region="NA",
                game_format="standard",
                best_of=3,
            )

    @pytest.mark.asyncio
    async def test_computes_card_usage_from_decklists(
        self, service: MetaService, mock_session: AsyncMock
    ) -> None:
        """Should compute card usage when placements have decklists."""
        mock_tournament = MagicMock(spec=Tournament)
        mock_tournament.id = uuid4()

        # Create placements with decklists
        p1 = MagicMock(spec=TournamentPlacement)
        p1.archetype = "Charizard ex"
        p1.decklist = [
            {"card_id": "card-a", "quantity": 4},
            {"card_id": "card-b", "quantity": 2},
        ]

        p2 = MagicMock(spec=TournamentPlacement)
        p2.archetype = "Charizard ex"
        p2.decklist = [{"card_id": "card-a", "quantity": 3}]

        tournament_result = MagicMock()
        tournament_result.scalars.return_value.all.return_value = [mock_tournament]

        placement_result = MagicMock()
        placement_result.scalars.return_value.all.return_value = [p1, p2]

        mock_session.execute.side_effect = [tournament_result, placement_result]

        snapshot = await service.compute_meta_snapshot(
            snapshot_date=date(2024, 6, 15),
            region="NA",
            game_format="standard",
            best_of=3,
        )

        assert snapshot.card_usage is not None
        assert "card-a" in snapshot.card_usage
        assert snapshot.card_usage["card-a"]["inclusion_rate"] == 1.0

    @pytest.mark.asyncio
    async def test_populates_tournaments_included(
        self, service: MetaService, mock_session: AsyncMock
    ) -> None:
        """Should populate tournaments_included with tournament IDs."""
        t1 = MagicMock(spec=Tournament)
        t1.id = uuid4()
        t2 = MagicMock(spec=Tournament)
        t2.id = uuid4()

        p1 = MagicMock(spec=TournamentPlacement)
        p1.archetype = "Charizard ex"
        p1.decklist = None

        tournament_result = MagicMock()
        tournament_result.scalars.return_value.all.return_value = [t1, t2]

        placement_result = MagicMock()
        placement_result.scalars.return_value.all.return_value = [p1]

        mock_session.execute.side_effect = [tournament_result, placement_result]

        snapshot = await service.compute_meta_snapshot(
            snapshot_date=date(2024, 6, 15),
            region="NA",
            game_format="standard",
            best_of=3,
        )

        assert len(snapshot.tournaments_included) == 2
        assert str(t1.id) in snapshot.tournaments_included
        assert str(t2.id) in snapshot.tournaments_included

    @pytest.mark.asyncio
    async def test_computes_global_snapshot_without_region(
        self, service: MetaService, mock_session: AsyncMock
    ) -> None:
        """Should compute snapshot for global (region=None)."""
        mock_tournament = MagicMock(spec=Tournament)
        mock_tournament.id = uuid4()

        p1 = MagicMock(spec=TournamentPlacement)
        p1.archetype = "Charizard ex"
        p1.decklist = None

        tournament_result = MagicMock()
        tournament_result.scalars.return_value.all.return_value = [mock_tournament]

        placement_result = MagicMock()
        placement_result.scalars.return_value.all.return_value = [p1]

        mock_session.execute.side_effect = [tournament_result, placement_result]

        snapshot = await service.compute_meta_snapshot(
            snapshot_date=date(2024, 6, 15),
            region=None,  # Global
            game_format="standard",
            best_of=3,
        )

        assert snapshot.region is None
        assert snapshot.sample_size == 1


class TestSaveSnapshotAsync:
    """Async tests for save_snapshot method."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        session = AsyncMock()
        session.add = MagicMock()
        return session

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> MetaService:
        return MetaService(mock_session)

    @pytest.fixture
    def sample_snapshot(self) -> MetaSnapshot:
        """Create a sample snapshot for testing."""
        return MetaSnapshot(
            id=uuid4(),
            snapshot_date=date(2024, 6, 15),
            region="NA",
            format="standard",
            best_of=3,
            archetype_shares={"Charizard ex": 0.5},
            card_usage=None,
            sample_size=10,
            tournaments_included=["t1", "t2"],
        )

    @pytest.mark.asyncio
    async def test_inserts_new_snapshot(
        self,
        service: MetaService,
        mock_session: AsyncMock,
        sample_snapshot: MetaSnapshot,
    ) -> None:
        """Should insert new snapshot when none exists."""
        # Mock no existing snapshot
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        await service.save_snapshot(sample_snapshot)

        mock_session.add.assert_called_once_with(sample_snapshot)
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_snapshot_and_calls_refresh(
        self,
        service: MetaService,
        mock_session: AsyncMock,
        sample_snapshot: MetaSnapshot,
    ) -> None:
        """Should return the saved snapshot after commit and refresh."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await service.save_snapshot(sample_snapshot)

        assert result is sample_snapshot
        mock_session.refresh.assert_called_once_with(sample_snapshot)

    @pytest.mark.asyncio
    async def test_returns_updated_existing_snapshot(
        self,
        service: MetaService,
        mock_session: AsyncMock,
        sample_snapshot: MetaSnapshot,
    ) -> None:
        """Should return the existing snapshot after update and refresh."""
        existing = MagicMock(spec=MetaSnapshot)
        existing.archetype_shares = {}
        existing.card_usage = None
        existing.sample_size = 5
        existing.tournaments_included = []

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing
        mock_session.execute.return_value = mock_result

        result = await service.save_snapshot(sample_snapshot)

        # Should return existing (not the input snapshot)
        assert result is existing
        mock_session.refresh.assert_called_once_with(existing)

    @pytest.mark.asyncio
    async def test_updates_existing_snapshot(
        self,
        service: MetaService,
        mock_session: AsyncMock,
        sample_snapshot: MetaSnapshot,
    ) -> None:
        """Should update existing snapshot with same dimensions."""
        existing = MagicMock(spec=MetaSnapshot)
        existing.archetype_shares = {}
        existing.card_usage = None
        existing.sample_size = 5
        existing.tournaments_included = []

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing
        mock_session.execute.return_value = mock_result

        await service.save_snapshot(sample_snapshot)

        # Should update existing, not add new
        mock_session.add.assert_not_called()
        assert existing.archetype_shares == sample_snapshot.archetype_shares
        assert existing.sample_size == sample_snapshot.sample_size
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_and_rollsback_on_error(
        self,
        service: MetaService,
        mock_session: AsyncMock,
        sample_snapshot: MetaSnapshot,
    ) -> None:
        """Should rollback and raise on database error."""
        mock_session.execute.side_effect = SQLAlchemyError("Insert failed")

        with pytest.raises(SQLAlchemyError):
            await service.save_snapshot(sample_snapshot)

        mock_session.rollback.assert_called_once()


class TestGetSnapshotAsync:
    """Async tests for get_snapshot method."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> MetaService:
        return MetaService(mock_session)

    @pytest.mark.asyncio
    async def test_returns_snapshot_when_found(
        self, service: MetaService, mock_session: AsyncMock
    ) -> None:
        """Should return snapshot when found."""
        expected = MagicMock(spec=MetaSnapshot)
        expected.snapshot_date = date(2024, 6, 15)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = expected
        mock_session.execute.return_value = mock_result

        result = await service.get_snapshot(
            snapshot_date=date(2024, 6, 15),
            region="NA",
            game_format="standard",
            best_of=3,
        )

        assert result == expected

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(
        self, service: MetaService, mock_session: AsyncMock
    ) -> None:
        """Should return None when no snapshot found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await service.get_snapshot(
            snapshot_date=date(2024, 6, 15),
            region="NA",
            game_format="standard",
            best_of=3,
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_handles_global_region(
        self, service: MetaService, mock_session: AsyncMock
    ) -> None:
        """Should query with NULL region for global snapshots."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        await service.get_snapshot(
            snapshot_date=date(2024, 6, 15),
            region=None,
            game_format="standard",
            best_of=3,
        )

        # Verify execute was called (query construction verified implicitly)
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_on_database_error(
        self, service: MetaService, mock_session: AsyncMock
    ) -> None:
        """Should raise SQLAlchemyError on database failure."""
        mock_session.execute.side_effect = SQLAlchemyError("Query failed")

        with pytest.raises(SQLAlchemyError):
            await service.get_snapshot(
                snapshot_date=date(2024, 6, 15),
                region="NA",
                game_format="standard",
                best_of=3,
            )
