"""Tests for meta snapshot service."""

from datetime import date
from decimal import Decimal
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
        t1, t2, t3 = uuid4(), uuid4(), uuid4()
        placements = []
        # Each archetype must appear in 3+ tournaments
        arch_tournaments = {
            "Charizard ex": [t1, t2, t3, t1, t2, t3],  # 6 placements
            "Lugia VSTAR": [t1, t2, t3],  # 3 placements
            "Gardevoir ex": [t1, t2, t3],  # 3 placements
        }
        for archetype, tids in arch_tournaments.items():
            for tid in tids:
                p = MagicMock(spec=TournamentPlacement)
                p.archetype = archetype
                p.tournament_id = tid
                placements.append(p)

        shares = service._compute_archetype_shares(placements)

        assert shares["Charizard ex"] == 0.5  # 6/12
        assert shares["Lugia VSTAR"] == 0.25  # 3/12
        assert shares["Gardevoir ex"] == 0.25  # 3/12

    def test_sorts_by_share_descending(self, service: MetaService) -> None:
        """Should sort archetypes by share, highest first."""
        t1, t2, t3 = uuid4(), uuid4(), uuid4()
        placements = []
        # Each archetype spread across 3 tournaments
        arch_tournaments = {
            "A": [t1, t2, t3],  # 3 placements
            "B": [t1, t1, t2, t2, t3, t3],  # 6 placements
            "C": [t1, t1, t1, t2, t2, t2, t3, t3, t3],  # 9 placements
        }
        for archetype, tids in arch_tournaments.items():
            for tid in tids:
                p = MagicMock(spec=TournamentPlacement)
                p.archetype = archetype
                p.tournament_id = tid
                placements.append(p)

        shares = service._compute_archetype_shares(placements)
        keys = list(shares.keys())

        assert keys[0] == "C"  # Most common
        assert keys[1] == "B"
        assert keys[2] == "A"  # Least common

    def test_handles_empty_list(self, service: MetaService) -> None:
        """Should handle empty placement list."""
        shares = service._compute_archetype_shares([])
        assert shares == {}

    def test_excludes_unknown_archetype(self, service: MetaService) -> None:
        """Should exclude 'Unknown' from shares output."""
        t1, t2, t3 = uuid4(), uuid4(), uuid4()
        placements = []
        for archetype, tid in [
            ("Charizard ex", t1),
            ("Charizard ex", t2),
            ("Charizard ex", t3),
            ("Unknown", t1),
            ("Unknown", t2),
            ("Unknown", t3),
        ]:
            p = MagicMock(spec=TournamentPlacement)
            p.archetype = archetype
            p.tournament_id = tid
            placements.append(p)

        shares = service._compute_archetype_shares(placements)

        assert "Unknown" not in shares
        # Charizard share computed against total (including Unknown counts)
        assert shares["Charizard ex"] == 0.5  # 3/6

    def test_excludes_empty_string_archetype_as_unknown(
        self, service: MetaService
    ) -> None:
        """Should map empty/blank archetype names to 'Unknown' and exclude them."""
        t1, t2, t3 = uuid4(), uuid4(), uuid4()
        placements = []
        # Charizard in 3 tournaments so it passes the filter
        for tid in [t1, t2, t3]:
            p = MagicMock(spec=TournamentPlacement)
            p.archetype = "Charizard ex"
            p.tournament_id = tid
            placements.append(p)
        for archetype in ["", "  ", None]:
            p = MagicMock(spec=TournamentPlacement)
            p.archetype = archetype
            p.tournament_id = t1
            placements.append(p)

        shares = service._compute_archetype_shares(placements)

        assert "Unknown" not in shares
        assert "" not in shares

    def test_excludes_low_share_archetypes(self, service: MetaService) -> None:
        """Should exclude archetypes below MIN_ARCHETYPE_SHARE (0.5%)."""
        t1, t2, t3 = uuid4(), uuid4(), uuid4()
        tids = [t1, t2, t3]
        placements = []
        # 200 Charizard across 3 tournaments
        for i in range(200):
            p = MagicMock(spec=TournamentPlacement)
            p.archetype = "Charizard ex"
            p.tournament_id = tids[i % 3]
            placements.append(p)
        # 1 Rogue in 1 tournament (fails both share and tournament filter)
        p = MagicMock(spec=TournamentPlacement)
        p.archetype = "Rogue Deck"
        p.tournament_id = t1
        placements.append(p)

        shares = service._compute_archetype_shares(placements)

        # 1/201 ≈ 0.00497 < 0.005, so excluded
        assert "Rogue Deck" not in shares
        assert "Charizard ex" in shares

    def test_keeps_archetypes_above_min_share(self, service: MetaService) -> None:
        """Should keep archetypes at or above the minimum share threshold."""
        t1, t2, t3 = uuid4(), uuid4(), uuid4()
        tids = [t1, t2, t3]
        placements = []
        # 99 Charizard across 3 tournaments
        for i in range(99):
            p = MagicMock(spec=TournamentPlacement)
            p.archetype = "Charizard ex"
            p.tournament_id = tids[i % 3]
            placements.append(p)
        # 3 Lugia across 3 tournaments (passes tournament filter)
        for tid in tids:
            p = MagicMock(spec=TournamentPlacement)
            p.archetype = "Lugia VSTAR"
            p.tournament_id = tid
            placements.append(p)

        shares = service._compute_archetype_shares(placements)

        assert "Lugia VSTAR" in shares
        # 3/102 ≈ 0.0294 > 0.005
        assert shares["Lugia VSTAR"] == pytest.approx(3 / 102)

    def test_excludes_archetypes_below_min_tournaments(
        self, service: MetaService
    ) -> None:
        """Should exclude archetypes appearing in fewer than 3 tournaments."""
        t1, t2, t3 = uuid4(), uuid4(), uuid4()
        placements = []
        # "Rare Deck" appears in only 2 tournaments
        for tid in [t1, t2]:
            p = MagicMock(spec=TournamentPlacement)
            p.archetype = "Rare Deck"
            p.tournament_id = tid
            placements.append(p)
        # "Common Deck" appears in 3 tournaments
        for tid in [t1, t2, t3]:
            p = MagicMock(spec=TournamentPlacement)
            p.archetype = "Common Deck"
            p.tournament_id = tid
            placements.append(p)

        shares = service._compute_archetype_shares(placements)
        assert "Rare Deck" not in shares
        assert "Common Deck" in shares

    def test_keeps_archetypes_at_min_tournaments(self, service: MetaService) -> None:
        """Should keep archetypes appearing in exactly 3 tournaments."""
        t1, t2, t3 = uuid4(), uuid4(), uuid4()
        placements = []
        for tid in [t1, t2, t3]:
            p = MagicMock(spec=TournamentPlacement)
            p.archetype = "Viable Deck"
            p.tournament_id = tid
            placements.append(p)

        shares = service._compute_archetype_shares(placements)
        assert "Viable Deck" in shares


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
        # Create 3 mock tournaments so archetypes pass the min filter
        t1, t2, t3 = uuid4(), uuid4(), uuid4()
        mock_tournaments = []
        for tid in [t1, t2, t3]:
            t = MagicMock(spec=Tournament)
            t.id = tid
            mock_tournaments.append(t)

        # Create mock placements spread across 3 tournaments
        mock_placements = []
        for archetype, tid in [
            ("Charizard ex", t1),
            ("Charizard ex", t2),
            ("Charizard ex", t3),
            ("Charizard ex", t1),
            ("Charizard ex", t2),
            ("Charizard ex", t3),
            ("Lugia VSTAR", t1),
            ("Lugia VSTAR", t2),
            ("Lugia VSTAR", t3),
        ]:
            p = MagicMock(spec=TournamentPlacement)
            p.archetype = archetype
            p.tournament_id = tid
            p.decklist = None
            mock_placements.append(p)

        # Setup execute to return tournaments then placements
        tournament_result = MagicMock()
        tournament_result.scalars.return_value.all.return_value = mock_tournaments

        placement_result = MagicMock()
        placement_result.scalars.return_value.all.return_value = mock_placements

        mock_session.execute.side_effect = [tournament_result, placement_result]

        snapshot = await service.compute_meta_snapshot(
            snapshot_date=date(2024, 6, 15),
            region="NA",
            game_format="standard",
            best_of=3,
        )

        assert snapshot.sample_size == 9
        assert "Charizard ex" in snapshot.archetype_shares
        assert snapshot.archetype_shares["Charizard ex"] == pytest.approx(6 / 9)
        assert snapshot.archetype_shares["Lugia VSTAR"] == pytest.approx(3 / 9)

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
            diversity_index=Decimal("0.75"),
            tier_assignments={"Charizard ex": "S"},
            jp_signals={"rising": ["Charizard ex"]},
            trends={"Charizard ex": {"direction": "up"}},
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
        existing.diversity_index = None
        existing.tier_assignments = None
        existing.jp_signals = None
        existing.trends = None

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
        """Should update all fields on existing snapshot."""
        existing = MagicMock(spec=MetaSnapshot)
        existing.archetype_shares = {}
        existing.card_usage = None
        existing.sample_size = 5
        existing.tournaments_included = []
        existing.diversity_index = None
        existing.tier_assignments = None
        existing.jp_signals = None
        existing.trends = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing
        mock_session.execute.return_value = mock_result

        await service.save_snapshot(sample_snapshot)

        # Should update existing, not add new
        mock_session.add.assert_not_called()
        assert existing.archetype_shares == sample_snapshot.archetype_shares
        assert existing.sample_size == sample_snapshot.sample_size
        assert existing.diversity_index == sample_snapshot.diversity_index
        assert existing.tier_assignments == sample_snapshot.tier_assignments
        assert existing.jp_signals == sample_snapshot.jp_signals
        assert existing.trends == sample_snapshot.trends
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


class TestComputeDiversityIndex:
    """Tests for diversity index computation."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> MetaService:
        return MetaService(mock_session)

    def test_computes_diversity_for_even_shares(self, service: MetaService) -> None:
        """Should compute high diversity for evenly distributed shares."""
        shares = {"A": 0.25, "B": 0.25, "C": 0.25, "D": 0.25}
        diversity = service.compute_diversity_index(shares)

        # 1 - (0.25^2 * 4) = 1 - 0.25 = 0.75
        assert diversity == Decimal("0.75")

    def test_computes_low_diversity_for_dominant_share(
        self, service: MetaService
    ) -> None:
        """Should compute low diversity when one archetype dominates."""
        shares = {"A": 0.9, "B": 0.05, "C": 0.05}
        diversity = service.compute_diversity_index(shares)

        # 1 - (0.9^2 + 0.05^2 + 0.05^2) = 1 - 0.815 = 0.185
        assert diversity == Decimal("0.185")

    def test_computes_zero_diversity_for_single_archetype(
        self, service: MetaService
    ) -> None:
        """Should compute zero diversity when only one archetype."""
        shares = {"A": 1.0}
        diversity = service.compute_diversity_index(shares)

        # 1 - 1^2 = 0
        assert diversity == Decimal("0.0")

    def test_returns_none_for_empty_shares(self, service: MetaService) -> None:
        """Should return None for empty shares."""
        assert service.compute_diversity_index({}) is None


class TestComputeTierAssignments:
    """Tests for tier assignment computation."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> MetaService:
        return MetaService(mock_session)

    def test_assigns_s_tier_above_15_percent(self, service: MetaService) -> None:
        """Should assign S tier for shares >15%."""
        shares = {"A": 0.20}
        tiers = service.compute_tier_assignments(shares)
        assert tiers["A"] == "S"

    def test_assigns_a_tier_between_8_and_15_percent(
        self, service: MetaService
    ) -> None:
        """Should assign A tier for shares 8-15%."""
        shares = {"A": 0.12}
        tiers = service.compute_tier_assignments(shares)
        assert tiers["A"] == "A"

    def test_assigns_b_tier_between_3_and_8_percent(self, service: MetaService) -> None:
        """Should assign B tier for shares 3-8%."""
        shares = {"A": 0.05}
        tiers = service.compute_tier_assignments(shares)
        assert tiers["A"] == "B"

    def test_assigns_c_tier_between_1_and_3_percent(self, service: MetaService) -> None:
        """Should assign C tier for shares 1-3%."""
        shares = {"A": 0.02}
        tiers = service.compute_tier_assignments(shares)
        assert tiers["A"] == "C"

    def test_assigns_rogue_below_1_percent(self, service: MetaService) -> None:
        """Should assign Rogue tier for shares <1%."""
        shares = {"A": 0.005}
        tiers = service.compute_tier_assignments(shares)
        assert tiers["A"] == "Rogue"

    def test_assigns_all_tiers_correctly(self, service: MetaService) -> None:
        """Should assign correct tiers for full meta."""
        shares = {
            "S-tier": 0.20,
            "A-tier": 0.10,
            "B-tier": 0.05,
            "C-tier": 0.015,
            "Rogue-tier": 0.005,
        }
        tiers = service.compute_tier_assignments(shares)

        assert tiers["S-tier"] == "S"
        assert tiers["A-tier"] == "A"
        assert tiers["B-tier"] == "B"
        assert tiers["C-tier"] == "C"
        assert tiers["Rogue-tier"] == "Rogue"

    def test_handles_boundary_values(self, service: MetaService) -> None:
        """Should handle boundary values correctly (exclusive thresholds)."""
        shares = {
            "exactly_15": 0.15,  # Not > 0.15, so A tier
            "exactly_8": 0.08,  # Not > 0.08, so B tier
            "exactly_3": 0.03,  # Not > 0.03, so C tier
            "exactly_1": 0.01,  # Not > 0.01, so Rogue tier
        }
        tiers = service.compute_tier_assignments(shares)

        assert tiers["exactly_15"] == "A"
        assert tiers["exactly_8"] == "B"
        assert tiers["exactly_3"] == "C"
        assert tiers["exactly_1"] == "Rogue"

    def test_excludes_unknown_from_tiers(self, service: MetaService) -> None:
        """Should not assign tiers to 'Unknown' archetype."""
        shares = {"Charizard ex": 0.20, "Unknown": 0.10}
        tiers = service.compute_tier_assignments(shares)

        assert "Unknown" not in tiers
        assert tiers["Charizard ex"] == "S"


class TestComputeJPSignals:
    """Tests for JP signal computation."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> MetaService:
        return MetaService(mock_session)

    @pytest.mark.asyncio
    async def test_returns_none_when_no_jp_snapshot(
        self, service: MetaService, mock_session: AsyncMock
    ) -> None:
        """Should return None when JP snapshot not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        signals = await service.compute_jp_signals(
            snapshot_date=date(2024, 6, 15),
            game_format="standard",
        )

        assert signals is None

    @pytest.mark.asyncio
    async def test_returns_none_when_no_en_snapshot(
        self, service: MetaService, mock_session: AsyncMock
    ) -> None:
        """Should return None when EN snapshot not found."""
        jp_snapshot = MagicMock(spec=MetaSnapshot)
        jp_snapshot.archetype_shares = {"A": 0.20}

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.side_effect = [jp_snapshot, None]
        mock_session.execute.return_value = mock_result

        signals = await service.compute_jp_signals(
            snapshot_date=date(2024, 6, 15),
            game_format="standard",
        )

        assert signals is None

    @pytest.mark.asyncio
    async def test_detects_rising_archetype(
        self, service: MetaService, mock_session: AsyncMock
    ) -> None:
        """Should detect archetype rising in JP vs EN."""
        jp_snapshot = MagicMock(spec=MetaSnapshot)
        jp_snapshot.archetype_shares = {"Rising": 0.20, "Normal": 0.10}

        en_snapshot = MagicMock(spec=MetaSnapshot)
        en_snapshot.archetype_shares = {"Rising": 0.10, "Normal": 0.10}

        # Mock execute to return different snapshots
        jp_result = MagicMock()
        jp_result.scalar_one_or_none.return_value = jp_snapshot

        en_result = MagicMock()
        en_result.scalar_one_or_none.return_value = en_snapshot

        mock_session.execute.side_effect = [jp_result, en_result]

        signals = await service.compute_jp_signals(
            snapshot_date=date(2024, 6, 15),
            game_format="standard",
        )

        assert signals is not None
        assert "Rising" in signals["rising"]
        assert "Rising" not in signals["falling"]

    @pytest.mark.asyncio
    async def test_detects_falling_archetype(
        self, service: MetaService, mock_session: AsyncMock
    ) -> None:
        """Should detect archetype falling in JP vs EN."""
        jp_snapshot = MagicMock(spec=MetaSnapshot)
        jp_snapshot.archetype_shares = {"Falling": 0.05, "Normal": 0.10}

        en_snapshot = MagicMock(spec=MetaSnapshot)
        en_snapshot.archetype_shares = {"Falling": 0.15, "Normal": 0.10}

        jp_result = MagicMock()
        jp_result.scalar_one_or_none.return_value = jp_snapshot

        en_result = MagicMock()
        en_result.scalar_one_or_none.return_value = en_snapshot

        mock_session.execute.side_effect = [jp_result, en_result]

        signals = await service.compute_jp_signals(
            snapshot_date=date(2024, 6, 15),
            game_format="standard",
        )

        assert signals is not None
        assert "Falling" in signals["falling"]
        assert "Falling" not in signals["rising"]

    @pytest.mark.asyncio
    async def test_returns_none_when_no_significant_divergence(
        self, service: MetaService, mock_session: AsyncMock
    ) -> None:
        """Should return None when no significant divergence."""
        jp_snapshot = MagicMock(spec=MetaSnapshot)
        jp_snapshot.archetype_shares = {"A": 0.12, "B": 0.10}

        en_snapshot = MagicMock(spec=MetaSnapshot)
        en_snapshot.archetype_shares = {"A": 0.11, "B": 0.09}  # <5% diff

        jp_result = MagicMock()
        jp_result.scalar_one_or_none.return_value = jp_snapshot

        en_result = MagicMock()
        en_result.scalar_one_or_none.return_value = en_snapshot

        mock_session.execute.side_effect = [jp_result, en_result]

        signals = await service.compute_jp_signals(
            snapshot_date=date(2024, 6, 15),
            game_format="standard",
        )

        assert signals is None

    @pytest.mark.asyncio
    async def test_excludes_unknown_from_divergence(
        self, service: MetaService, mock_session: AsyncMock
    ) -> None:
        """Should exclude 'Unknown' from JP signal divergence computation."""
        jp_snapshot = MagicMock(spec=MetaSnapshot)
        jp_snapshot.archetype_shares = {"Unknown": 0.30, "Charizard ex": 0.10}

        en_snapshot = MagicMock(spec=MetaSnapshot)
        en_snapshot.archetype_shares = {"Charizard ex": 0.10}

        jp_result = MagicMock()
        jp_result.scalar_one_or_none.return_value = jp_snapshot

        en_result = MagicMock()
        en_result.scalar_one_or_none.return_value = en_snapshot

        mock_session.execute.side_effect = [jp_result, en_result]

        signals = await service.compute_jp_signals(
            snapshot_date=date(2024, 6, 15),
            game_format="standard",
        )

        # Unknown has 30% divergence but should be excluded
        assert signals is None


class TestComputeTrends:
    """Tests for trend computation."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> MetaService:
        return MetaService(mock_session)

    @pytest.mark.asyncio
    async def test_returns_none_when_no_previous_snapshot(
        self, service: MetaService, mock_session: AsyncMock
    ) -> None:
        """Should return None when no previous snapshot."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        trends = await service.compute_trends(
            current_shares={"A": 0.20},
            snapshot_date=date(2024, 6, 15),
            region=None,
            game_format="standard",
            best_of=3,
        )

        assert trends is None

    @pytest.mark.asyncio
    async def test_computes_upward_trend(
        self, service: MetaService, mock_session: AsyncMock
    ) -> None:
        """Should compute upward trend when share increased."""
        previous = MagicMock(spec=MetaSnapshot)
        previous.archetype_shares = {"A": 0.10}

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = previous
        mock_session.execute.return_value = mock_result

        trends = await service.compute_trends(
            current_shares={"A": 0.15},
            snapshot_date=date(2024, 6, 15),
            region=None,
            game_format="standard",
            best_of=3,
        )

        assert trends is not None
        assert trends["A"]["direction"] == "up"
        assert trends["A"]["change"] == 0.05

    @pytest.mark.asyncio
    async def test_computes_downward_trend(
        self, service: MetaService, mock_session: AsyncMock
    ) -> None:
        """Should compute downward trend when share decreased."""
        previous = MagicMock(spec=MetaSnapshot)
        previous.archetype_shares = {"A": 0.20}

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = previous
        mock_session.execute.return_value = mock_result

        trends = await service.compute_trends(
            current_shares={"A": 0.10},
            snapshot_date=date(2024, 6, 15),
            region=None,
            game_format="standard",
            best_of=3,
        )

        assert trends is not None
        assert trends["A"]["direction"] == "down"
        assert trends["A"]["change"] == -0.10

    @pytest.mark.asyncio
    async def test_computes_stable_trend(
        self, service: MetaService, mock_session: AsyncMock
    ) -> None:
        """Should compute stable trend when change <0.5%."""
        previous = MagicMock(spec=MetaSnapshot)
        previous.archetype_shares = {"A": 0.10}

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = previous
        mock_session.execute.return_value = mock_result

        trends = await service.compute_trends(
            current_shares={"A": 0.103},  # 0.3% change
            snapshot_date=date(2024, 6, 15),
            region=None,
            game_format="standard",
            best_of=3,
        )

        assert trends is not None
        assert trends["A"]["direction"] == "stable"

    @pytest.mark.asyncio
    async def test_handles_new_archetype(
        self, service: MetaService, mock_session: AsyncMock
    ) -> None:
        """Should handle archetype that didn't exist before."""
        previous = MagicMock(spec=MetaSnapshot)
        previous.archetype_shares = {"A": 0.20}

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = previous
        mock_session.execute.return_value = mock_result

        trends = await service.compute_trends(
            current_shares={"A": 0.20, "B": 0.10},  # B is new
            snapshot_date=date(2024, 6, 15),
            region=None,
            game_format="standard",
            best_of=3,
        )

        assert trends is not None
        assert trends["B"]["direction"] == "up"
        assert trends["B"]["previous_share"] is None

    @pytest.mark.asyncio
    async def test_handles_disappeared_archetype(
        self, service: MetaService, mock_session: AsyncMock
    ) -> None:
        """Should handle archetype that disappeared from current."""
        previous = MagicMock(spec=MetaSnapshot)
        previous.archetype_shares = {"A": 0.20, "B": 0.10}

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = previous
        mock_session.execute.return_value = mock_result

        trends = await service.compute_trends(
            current_shares={"A": 0.20},  # B disappeared
            snapshot_date=date(2024, 6, 15),
            region=None,
            game_format="standard",
            best_of=3,
        )

        assert trends is not None
        assert trends["B"]["direction"] == "down"
        assert trends["B"]["change"] == -0.10
