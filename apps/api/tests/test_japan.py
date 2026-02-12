"""Tests for Japan intelligence endpoints."""

from datetime import UTC, date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from src.db.database import get_db
from src.main import app
from src.models import JPCardInnovation, JPNewArchetype, JPSetImpact, Prediction


class TestListCardInnovations:
    """Tests for GET /api/v1/japan/innovation."""

    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def client(self, mock_db: AsyncMock) -> TestClient:
        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        yield TestClient(app)
        app.dependency_overrides.clear()

    @pytest.fixture
    def mock_innovation(self) -> JPCardInnovation:
        """Create mock card innovation."""
        return JPCardInnovation(
            id=uuid4(),
            card_id="sv6-123",
            card_name="Test Card",
            card_name_jp="テストカード",
            set_code="sv6",
            set_release_jp=date(2024, 1, 15),
            set_release_en=date(2024, 4, 15),
            is_legal_en=False,
            adoption_rate=Decimal("0.25"),
            adoption_trend="rising",
            archetypes_using=["Charizard ex", "Lugia VSTAR"],
            competitive_impact_rating=4,
            sample_size=50,
        )

    def test_returns_innovations(
        self,
        client: TestClient,
        mock_db: AsyncMock,
        mock_innovation: JPCardInnovation,
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_innovation]

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_db.execute.side_effect = [mock_result, mock_count_result]

        response = client.get("/api/v1/japan/innovation")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["card_id"] == "sv6-123"

    def test_filters_by_set_code(self, client: TestClient, mock_db: AsyncMock) -> None:
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_db.execute.side_effect = [mock_result, mock_count_result]

        response = client.get(
            "/api/v1/japan/innovation",
            params={"set_code": "sv6"},
        )

        assert response.status_code == status.HTTP_200_OK

    def test_filters_by_en_legal(self, client: TestClient, mock_db: AsyncMock) -> None:
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_db.execute.side_effect = [mock_result, mock_count_result]

        response = client.get(
            "/api/v1/japan/innovation",
            params={"en_legal": "false"},
        )

        assert response.status_code == status.HTTP_200_OK

    def test_returns_503_on_database_error(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        mock_db.execute.side_effect = SQLAlchemyError("DB error")

        response = client.get("/api/v1/japan/innovation")

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE


class TestGetCardInnovationDetail:
    """Tests for GET /api/v1/japan/innovation/{card_id}."""

    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def client(self, mock_db: AsyncMock) -> TestClient:
        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        yield TestClient(app)
        app.dependency_overrides.clear()

    def test_returns_innovation_detail(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        innovation = JPCardInnovation(
            id=uuid4(),
            card_id="sv6-123",
            card_name="Test Card",
            card_name_jp="テストカード",
            set_code="sv6",
            set_release_jp=date(2024, 1, 15),
            set_release_en=date(2024, 4, 15),
            is_legal_en=False,
            adoption_rate=Decimal("0.25"),
            adoption_trend="rising",
            archetypes_using=["Charizard ex"],
            competitive_impact_rating=4,
            sample_size=50,
            impact_analysis="Detailed analysis here.",
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = innovation
        mock_db.execute.return_value = mock_result

        response = client.get("/api/v1/japan/innovation/sv6-123")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["card_id"] == "sv6-123"
        assert data["impact_analysis"] == "Detailed analysis here."

    def test_returns_404_when_not_found(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        response = client.get("/api/v1/japan/innovation/nonexistent")

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestListNewArchetypes:
    """Tests for GET /api/v1/japan/archetypes/new."""

    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def client(self, mock_db: AsyncMock) -> TestClient:
        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        yield TestClient(app)
        app.dependency_overrides.clear()

    def test_returns_new_archetypes(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        archetype = JPNewArchetype(
            id=uuid4(),
            archetype_id="test-archetype",
            name="Test Archetype",
            name_jp="テストアーキタイプ",
            key_cards=["card1", "card2"],
            enabled_by_set="sv6",
            jp_meta_share=Decimal("0.15"),
            jp_trend="stable",
            city_league_results=[],
            estimated_en_legal_date=date(2024, 6, 1),
            analysis="Analysis text",
        )

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [archetype]

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        # Card enrichment query (returns no matching cards)
        mock_card_enrich_result = MagicMock()
        mock_card_enrich_result.all.return_value = []

        mock_db.execute.side_effect = [
            mock_result,
            mock_count_result,
            mock_card_enrich_result,
        ]

        response = client.get("/api/v1/japan/archetypes/new")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["archetype_id"] == "test-archetype"


class TestListSetImpacts:
    """Tests for GET /api/v1/japan/set-impact."""

    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def client(self, mock_db: AsyncMock) -> TestClient:
        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        yield TestClient(app)
        app.dependency_overrides.clear()

    def test_returns_set_impacts(self, client: TestClient, mock_db: AsyncMock) -> None:
        impact = JPSetImpact(
            id=uuid4(),
            set_code="sv6",
            set_name="Twilight Masquerade",
            jp_release_date=date(2024, 1, 15),
            en_release_date=date(2024, 4, 15),
            jp_meta_before={"Charizard ex": 0.20},
            jp_meta_after={"Charizard ex": 0.15, "New Deck": 0.10},
            key_innovations=["card1", "card2"],
            new_archetypes=["New Deck"],
            analysis="Set impact analysis",
        )

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [impact]

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_db.execute.side_effect = [mock_result, mock_count_result]

        response = client.get("/api/v1/japan/set-impact")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["set_code"] == "sv6"


class TestListPredictions:
    """Tests for GET /api/v1/japan/predictions."""

    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def client(self, mock_db: AsyncMock) -> TestClient:
        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        yield TestClient(app)
        app.dependency_overrides.clear()

    def test_returns_predictions_with_stats(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        prediction = Prediction(
            id=uuid4(),
            prediction_text="Test prediction",
            target_event="NAIC 2024",
            target_date=date(2024, 6, 15),
            created_at=datetime.now(UTC),
            resolved_at=datetime.now(UTC),
            outcome="correct",
            confidence="high",
            category="meta",
            reasoning="Reasoning text",
            outcome_notes="Prediction was accurate",
        )

        mock_pred_result = MagicMock()
        mock_pred_result.scalars.return_value.all.return_value = [prediction]

        mock_count_results = [MagicMock() for _ in range(5)]
        mock_count_results[0].scalar.return_value = 10  # total
        mock_count_results[1].scalar.return_value = 8  # resolved
        mock_count_results[2].scalar.return_value = 6  # correct
        mock_count_results[3].scalar.return_value = 1  # partial
        mock_count_results[4].scalar.return_value = 1  # incorrect

        mock_db.execute.side_effect = [
            mock_pred_result,
            mock_count_results[0],
            mock_count_results[1],
            mock_count_results[2],
            mock_count_results[3],
            mock_count_results[4],
        ]

        response = client.get("/api/v1/japan/predictions")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 10
        assert data["resolved"] == 8
        assert data["correct"] == 6
        assert data["accuracy_rate"] == 0.75


class TestCardCountEvolution:
    """Tests for GET /api/v1/japan/card-count-evolution."""

    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        """Create mock database session."""
        return AsyncMock()

    @pytest.fixture
    def client(self, mock_db: AsyncMock) -> TestClient:
        """Create test client with mocked database."""

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
        """Create a mock row for aggregate query."""
        return (tournament_id or str(uuid4()), decklist, tournament_date)

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
