"""Tests for tournament endpoints."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.models.tournament import Tournament
from src.models.tournament_placement import TournamentPlacement


class TestListTournaments:
    """Tests for GET /api/v1/meta/tournaments."""

    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        """Create mock database session."""
        return AsyncMock()

    @pytest.fixture
    def client(self, mock_db: AsyncMock) -> TestClient:
        """Create test client with mocked database."""
        from src.db.database import get_db

        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        yield TestClient(app)
        app.dependency_overrides.clear()

    @pytest.fixture
    def sample_tournament(self) -> MagicMock:
        """Create a sample tournament mock."""
        tournament = MagicMock(spec=Tournament)
        tournament.id = uuid4()
        tournament.name = "Test Regional"
        tournament.date = date(2024, 1, 15)
        tournament.region = "NA"
        tournament.country = "USA"
        tournament.format = "standard"
        tournament.best_of = 3
        tournament.participant_count = 256

        # Mock placements
        placement1 = MagicMock(spec=TournamentPlacement)
        placement1.placement = 1
        placement1.player_name = "Player One"
        placement1.archetype = "Charizard ex"

        placement2 = MagicMock(spec=TournamentPlacement)
        placement2.placement = 2
        placement2.player_name = "Player Two"
        placement2.archetype = "Lugia VSTAR"

        tournament.placements = [placement1, placement2]

        return tournament

    def test_list_tournaments_success(
        self, client: TestClient, mock_db: AsyncMock, sample_tournament: MagicMock
    ) -> None:
        """Test listing tournaments successfully."""
        # Mock count query
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        # Mock tournament query
        mock_result = MagicMock()
        mock_result.scalars.return_value.unique.return_value.all.return_value = [
            sample_tournament
        ]

        mock_db.execute.side_effect = [mock_count_result, mock_result]

        response = client.get("/api/v1/meta/tournaments")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["page"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "Test Regional"
        assert data["items"][0]["region"] == "NA"
        assert len(data["items"][0]["top_placements"]) == 2

    def test_list_tournaments_empty(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test listing tournaments when none exist."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_result = MagicMock()
        mock_result.scalars.return_value.unique.return_value.all.return_value = []

        mock_db.execute.side_effect = [mock_count_result, mock_result]

        response = client.get("/api/v1/meta/tournaments")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_list_tournaments_with_region_filter(
        self, client: TestClient, mock_db: AsyncMock, sample_tournament: MagicMock
    ) -> None:
        """Test filtering tournaments by region."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_result = MagicMock()
        mock_result.scalars.return_value.unique.return_value.all.return_value = [
            sample_tournament
        ]

        mock_db.execute.side_effect = [mock_count_result, mock_result]

        response = client.get("/api/v1/meta/tournaments?region=NA")

        assert response.status_code == 200
        data = response.json()
        assert data["items"][0]["region"] == "NA"

    def test_list_tournaments_with_format_filter(
        self, client: TestClient, mock_db: AsyncMock, sample_tournament: MagicMock
    ) -> None:
        """Test filtering tournaments by format."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_result = MagicMock()
        mock_result.scalars.return_value.unique.return_value.all.return_value = [
            sample_tournament
        ]

        mock_db.execute.side_effect = [mock_count_result, mock_result]

        response = client.get("/api/v1/meta/tournaments?format=standard")

        assert response.status_code == 200
        data = response.json()
        assert data["items"][0]["format"] == "standard"

    def test_list_tournaments_with_date_range(
        self, client: TestClient, mock_db: AsyncMock, sample_tournament: MagicMock
    ) -> None:
        """Test filtering tournaments by date range."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_result = MagicMock()
        mock_result.scalars.return_value.unique.return_value.all.return_value = [
            sample_tournament
        ]

        mock_db.execute.side_effect = [mock_count_result, mock_result]

        response = client.get(
            "/api/v1/meta/tournaments?start_date=2024-01-01&end_date=2024-01-31"
        )

        assert response.status_code == 200

    def test_list_tournaments_with_best_of_filter(
        self, client: TestClient, mock_db: AsyncMock, sample_tournament: MagicMock
    ) -> None:
        """Test filtering tournaments by best_of."""
        sample_tournament.best_of = 1
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_result = MagicMock()
        mock_result.scalars.return_value.unique.return_value.all.return_value = [
            sample_tournament
        ]

        mock_db.execute.side_effect = [mock_count_result, mock_result]

        response = client.get("/api/v1/meta/tournaments?best_of=1")

        assert response.status_code == 200
        data = response.json()
        assert data["items"][0]["best_of"] == 1

    def test_list_tournaments_pagination(
        self, client: TestClient, mock_db: AsyncMock, sample_tournament: MagicMock
    ) -> None:
        """Test tournament pagination."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 50

        mock_result = MagicMock()
        mock_result.scalars.return_value.unique.return_value.all.return_value = [
            sample_tournament
        ]

        mock_db.execute.side_effect = [mock_count_result, mock_result]

        response = client.get("/api/v1/meta/tournaments?page=2&limit=10")

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["limit"] == 10
        assert data["has_prev"] is True
        assert data["has_next"] is True
        assert data["total_pages"] == 5

    def test_list_tournaments_top_placements_sorted(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test top placements are sorted by placement."""
        tournament = MagicMock(spec=Tournament)
        tournament.id = uuid4()
        tournament.name = "Test Regional"
        tournament.date = date(2024, 1, 15)
        tournament.region = "NA"
        tournament.country = "USA"
        tournament.format = "standard"
        tournament.best_of = 3
        tournament.participant_count = 256

        # Create placements out of order
        placements = []
        for i in [3, 1, 4, 2]:
            p = MagicMock(spec=TournamentPlacement)
            p.placement = i
            p.player_name = f"Player {i}"
            p.archetype = "Archetype"
            placements.append(p)

        tournament.placements = placements

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_result = MagicMock()
        mock_result.scalars.return_value.unique.return_value.all.return_value = [
            tournament
        ]

        mock_db.execute.side_effect = [mock_count_result, mock_result]

        response = client.get("/api/v1/meta/tournaments")

        assert response.status_code == 200
        data = response.json()
        placements_data = data["items"][0]["top_placements"]
        assert placements_data[0]["placement"] == 1
        assert placements_data[1]["placement"] == 2
        assert placements_data[2]["placement"] == 3
        assert placements_data[3]["placement"] == 4


class TestTournamentSchemas:
    """Tests for tournament Pydantic schemas."""

    def test_top_placement_validation(self) -> None:
        """Test TopPlacement schema validation."""
        from src.schemas.tournament import TopPlacement

        placement = TopPlacement(
            placement=1,
            player_name="Test Player",
            archetype="Charizard ex",
        )
        assert placement.placement == 1
        assert placement.player_name == "Test Player"
        assert placement.archetype == "Charizard ex"

    def test_tournament_summary_validation(self) -> None:
        """Test TournamentSummary schema validation."""
        from src.schemas.tournament import TopPlacement, TournamentSummary

        tournament = TournamentSummary(
            id="test-id",
            name="Test Regional",
            date=date(2024, 1, 15),
            region="NA",
            country="USA",
            format="standard",
            best_of=3,
            participant_count=256,
            top_placements=[
                TopPlacement(placement=1, archetype="Charizard ex"),
            ],
        )
        assert tournament.name == "Test Regional"
        assert tournament.region == "NA"
        assert len(tournament.top_placements) == 1
