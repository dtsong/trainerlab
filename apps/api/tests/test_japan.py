"""Tests for Japan intelligence endpoints."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.models.tournament_placement import TournamentPlacement


class TestCardCountEvolution:
    """Tests for GET /api/v1/japan/card-count-evolution."""

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

    def _make_placement_row(
        self,
        tournament_date: date,
        decklist: list[dict],
        tournament_id: str | None = None,
    ) -> tuple:
        """Create a mock (TournamentPlacement, date) row."""
        placement = MagicMock(spec=TournamentPlacement)
        placement.tournament_id = tournament_id or str(uuid4())
        placement.decklist = decklist
        return (placement, tournament_date)

    def test_card_count_evolution_success(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test successful card count evolution response."""
        tid = str(uuid4())
        rows = [
            self._make_placement_row(
                date(2024, 1, 8),
                [
                    {"card_id": "sv4-6", "quantity": 3},
                    {"card_id": "sv3-12", "quantity": 4},
                ],
                tid,
            ),
            self._make_placement_row(
                date(2024, 1, 15),
                [
                    {"card_id": "sv4-6", "quantity": 4},
                    {"card_id": "sv3-12", "quantity": 3},
                ],
                tid,
            ),
        ]

        # Mock placement query
        mock_placement_result = MagicMock()
        mock_placement_result.all.return_value = rows

        # Mock card name resolution
        card_row1 = MagicMock()
        card_row1.id = "sv4-6"
        card_row1.name = "Charizard ex"
        card_row2 = MagicMock()
        card_row2.id = "sv3-12"
        card_row2.name = "Rare Candy"
        mock_card_result = MagicMock()
        mock_card_result.__iter__ = MagicMock(return_value=iter([card_row1, card_row2]))

        mock_db.execute.side_effect = [mock_placement_result, mock_card_result]

        response = client.get(
            "/api/v1/japan/card-count-evolution?archetype=Charizard%20ex"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["archetype"] == "Charizard ex"
        assert data["tournaments_analyzed"] == 1
        assert len(data["cards"]) == 2

    def test_card_count_evolution_empty(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test empty response when no placements found."""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_db.execute.return_value = mock_result

        response = client.get(
            "/api/v1/japan/card-count-evolution?archetype=NonExistent"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["archetype"] == "NonExistent"
        assert data["cards"] == []
        assert data["tournaments_analyzed"] == 0

    def test_card_count_evolution_requires_archetype(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test that archetype parameter is required."""
        response = client.get("/api/v1/japan/card-count-evolution")

        assert response.status_code == 422

    def test_card_count_evolution_days_validation(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test days parameter validation."""
        response = client.get(
            "/api/v1/japan/card-count-evolution?archetype=Test&days=1"
        )
        assert response.status_code == 422

        response = client.get(
            "/api/v1/japan/card-count-evolution?archetype=Test&days=500"
        )
        assert response.status_code == 422

    def test_card_count_evolution_multiple_weeks(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test that data points are grouped by week."""
        tid1 = str(uuid4())
        tid2 = str(uuid4())
        rows = [
            # Week 1 (Mon Jan 8)
            self._make_placement_row(
                date(2024, 1, 8),
                [{"card_id": "sv4-6", "quantity": 2}],
                tid1,
            ),
            self._make_placement_row(
                date(2024, 1, 10),
                [{"card_id": "sv4-6", "quantity": 4}],
                tid1,
            ),
            # Week 2 (Mon Jan 15)
            self._make_placement_row(
                date(2024, 1, 15),
                [{"card_id": "sv4-6", "quantity": 3}],
                tid2,
            ),
        ]

        mock_placement_result = MagicMock()
        mock_placement_result.all.return_value = rows

        card_row = MagicMock()
        card_row.id = "sv4-6"
        card_row.name = "Charizard ex"
        mock_card_result = MagicMock()
        mock_card_result.__iter__ = MagicMock(return_value=iter([card_row]))

        mock_db.execute.side_effect = [mock_placement_result, mock_card_result]

        response = client.get(
            "/api/v1/japan/card-count-evolution?archetype=Charizard%20ex"
        )

        assert response.status_code == 200
        data = response.json()
        # Should have 2 data points (2 weeks) for the card
        card = data["cards"][0]
        assert len(card["data_points"]) == 2
        assert card["card_name"] == "Charizard ex"


class TestCardCountEvolutionSchemas:
    """Tests for card count evolution Pydantic schemas."""

    def test_card_count_data_point(self) -> None:
        """Test CardCountDataPoint schema."""
        from src.schemas.japan import CardCountDataPoint

        point = CardCountDataPoint(
            snapshot_date=date(2024, 1, 8),
            avg_copies=3.5,
            inclusion_rate=0.85,
            sample_size=20,
        )
        assert point.avg_copies == 3.5
        assert point.inclusion_rate == 0.85
        assert point.sample_size == 20

    def test_card_count_evolution(self) -> None:
        """Test CardCountEvolution schema."""
        from src.schemas.japan import CardCountDataPoint, CardCountEvolution

        evolution = CardCountEvolution(
            card_id="sv4-6",
            card_name="Charizard ex",
            data_points=[
                CardCountDataPoint(
                    snapshot_date=date(2024, 1, 8),
                    avg_copies=2.0,
                    inclusion_rate=0.75,
                    sample_size=12,
                ),
            ],
            total_change=1.5,
            current_avg=3.5,
        )
        assert evolution.card_name == "Charizard ex"
        assert evolution.total_change == 1.5
        assert len(evolution.data_points) == 1

    def test_card_count_evolution_response(self) -> None:
        """Test CardCountEvolutionResponse schema."""
        from src.schemas.japan import CardCountEvolutionResponse

        response = CardCountEvolutionResponse(
            archetype="Charizard ex",
            cards=[],
            tournaments_analyzed=5,
        )
        assert response.archetype == "Charizard ex"
        assert response.tournaments_analyzed == 5
        assert response.cards == []
