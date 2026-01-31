"""Tests for meta snapshot service."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.models import Tournament, TournamentPlacement
from src.services.meta_service import MetaService


class TestMetaService:
    """Tests for MetaService."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> MetaService:
        return MetaService(mock_session)

    @pytest.fixture
    def sample_tournament(self) -> Tournament:
        """Create a sample tournament for testing."""
        tournament = MagicMock(spec=Tournament)
        tournament.id = uuid4()
        tournament.name = "Test Regional"
        tournament.date = date(2024, 6, 1)
        tournament.region = "NA"
        tournament.format = "standard"
        tournament.best_of = 3
        return tournament

    @pytest.fixture
    def sample_placements(
        self, sample_tournament: Tournament
    ) -> list[TournamentPlacement]:
        """Create sample placements for testing."""
        placements = []
        archetypes = [
            "Charizard ex",
            "Charizard ex",
            "Lugia VSTAR",
            "Gardevoir ex",
            "Charizard ex",
            "Roaring Moon ex",
            "Lugia VSTAR",
            "Raging Bolt ex",
        ]

        for i, archetype in enumerate(archetypes, 1):
            placement = MagicMock(spec=TournamentPlacement)
            placement.id = uuid4()
            placement.tournament_id = sample_tournament.id
            placement.placement = i
            placement.archetype = archetype
            placement.decklist = None
            placements.append(placement)

        return placements


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
