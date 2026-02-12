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
    """Tests for GET /api/v1/tournaments."""

    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        """Create mock database session."""
        return AsyncMock()

    @pytest.fixture
    def client(self, mock_db: AsyncMock) -> TestClient:
        """Create test client with mocked database."""
        from src.db.database import get_db
        from src.dependencies.beta import require_beta

        async def override_get_db():
            yield mock_db

        async def override_require_beta():
            return None

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[require_beta] = override_require_beta
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
        tournament.tier = "major"
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

    @staticmethod
    def _freshness_result(latest_date: date | None) -> MagicMock:
        """Create mock result for max tournament date freshness query."""
        result = MagicMock()
        result.scalar_one_or_none.return_value = latest_date
        return result

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

        mock_db.execute.side_effect = [
            mock_count_result,
            self._freshness_result(sample_tournament.date),
            mock_result,
        ]

        response = client.get("/api/v1/tournaments")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["page"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "Test Regional"
        assert data["items"][0]["region"] == "NA"
        assert len(data["items"][0]["top_placements"]) == 2
        assert data["freshness"]["cadence_profile"] == "default_cadence"
        assert data["freshness"]["snapshot_date"] == "2024-01-15"

    def test_list_tournaments_empty(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test listing tournaments when none exist."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_result = MagicMock()
        mock_result.scalars.return_value.unique.return_value.all.return_value = []

        mock_db.execute.side_effect = [
            mock_count_result,
            self._freshness_result(None),
            mock_result,
        ]

        response = client.get("/api/v1/tournaments")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []
        assert data["freshness"]["status"] == "no_data"

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

        mock_db.execute.side_effect = [
            mock_count_result,
            self._freshness_result(sample_tournament.date),
            mock_result,
        ]

        response = client.get("/api/v1/tournaments?region=NA")

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

        mock_db.execute.side_effect = [
            mock_count_result,
            self._freshness_result(sample_tournament.date),
            mock_result,
        ]

        response = client.get("/api/v1/tournaments?format=standard")

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

        mock_db.execute.side_effect = [
            mock_count_result,
            self._freshness_result(sample_tournament.date),
            mock_result,
        ]

        response = client.get(
            "/api/v1/tournaments?start_date=2024-01-01&end_date=2024-01-31"
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

        mock_db.execute.side_effect = [
            mock_count_result,
            self._freshness_result(sample_tournament.date),
            mock_result,
        ]

        response = client.get("/api/v1/tournaments?best_of=1")

        assert response.status_code == 200
        data = response.json()
        assert data["items"][0]["best_of"] == 1

    def test_list_tournaments_major_tier_uses_tpci_cadence(
        self, client: TestClient, mock_db: AsyncMock, sample_tournament: MagicMock
    ) -> None:
        """Major-tier filter should evaluate freshness with TPCI cadence."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_result = MagicMock()
        mock_result.scalars.return_value.unique.return_value.all.return_value = [
            sample_tournament
        ]

        mock_db.execute.side_effect = [
            mock_count_result,
            self._freshness_result(sample_tournament.date),
            mock_result,
        ]

        response = client.get("/api/v1/tournaments?tier=major")

        assert response.status_code == 200
        data = response.json()
        assert data["freshness"]["cadence_profile"] == "tpci_event_cadence"

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

        mock_db.execute.side_effect = [
            mock_count_result,
            self._freshness_result(sample_tournament.date),
            mock_result,
        ]

        response = client.get("/api/v1/tournaments?page=2&limit=10")

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
        tournament.tier = "major"
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

        mock_db.execute.side_effect = [
            mock_count_result,
            self._freshness_result(tournament.date),
            mock_result,
        ]

        response = client.get("/api/v1/tournaments")

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


class TestGetPlacementDecklist:
    """Tests for GET /api/v1/tournaments/{id}/placements/{id}/decklist."""

    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        """Create mock database session."""
        return AsyncMock()

    @pytest.fixture
    def client(self, mock_db: AsyncMock) -> TestClient:
        """Create test client with mocked database."""
        from src.db.database import get_db
        from src.dependencies.beta import require_beta

        async def override_get_db():
            yield mock_db

        async def override_require_beta():
            return None

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[require_beta] = override_require_beta
        yield TestClient(app)
        app.dependency_overrides.clear()

    @pytest.fixture
    def sample_placement(self) -> MagicMock:
        """Create a sample placement with decklist."""
        tournament = MagicMock(spec=Tournament)
        tournament.name = "City League Tokyo"
        tournament.date = date(2024, 3, 10)

        placement = MagicMock(spec=TournamentPlacement)
        placement.id = uuid4()
        placement.tournament_id = uuid4()
        placement.player_name = "Taro"
        placement.archetype = "Charizard ex"
        placement.decklist = [
            {"card_id": "sv4-6", "quantity": 3},
            {"card_id": "sv3-12", "quantity": 4},
            {"card_id": "sv1-198", "quantity": 2},
        ]
        placement.decklist_source = "https://limitlesstcg.com/decks/abc"
        placement.tournament = tournament

        return placement

    def test_decklist_success(
        self, client: TestClient, mock_db: AsyncMock, sample_placement: MagicMock
    ) -> None:
        """Test fetching a decklist successfully."""
        # Mock placement query
        mock_placement_result = MagicMock()
        mock_placement_result.scalar_one_or_none.return_value = sample_placement

        # Mock card name resolution
        mock_card_row1 = MagicMock()
        mock_card_row1.id = "sv4-6"
        mock_card_row1.name = "Charizard ex"
        mock_card_row1.supertype = "Pokemon"

        mock_card_row2 = MagicMock()
        mock_card_row2.id = "sv3-12"
        mock_card_row2.name = "Rare Candy"
        mock_card_row2.supertype = "Trainer"

        mock_card_row3 = MagicMock()
        mock_card_row3.id = "sv1-198"
        mock_card_row3.name = "Fire Energy"
        mock_card_row3.supertype = "Energy"

        mock_card_result = MagicMock()
        mock_card_result.__iter__ = MagicMock(
            return_value=iter([mock_card_row1, mock_card_row2, mock_card_row3])
        )

        mock_db.execute.side_effect = [mock_placement_result, mock_card_result]

        tournament_id = sample_placement.tournament_id
        placement_id = sample_placement.id
        response = client.get(
            f"/api/v1/tournaments/{tournament_id}/placements/{placement_id}/decklist"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["archetype"] == "Charizard ex"
        assert data["player_name"] == "Taro"
        assert data["tournament_name"] == "City League Tokyo"
        assert data["source_url"] == "https://limitlesstcg.com/decks/abc"
        assert data["total_cards"] == 9  # 3 + 4 + 2
        assert len(data["cards"]) == 3
        assert data["cards"][0]["card_name"] == "Charizard ex"
        assert data["cards"][0]["supertype"] == "Pokemon"

    def test_decklist_placement_not_found(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test 404 when placement doesn't exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        tid = uuid4()
        pid = uuid4()
        response = client.get(f"/api/v1/tournaments/{tid}/placements/{pid}/decklist")

        assert response.status_code == 404

    def test_decklist_not_available(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test 404 when placement has no decklist."""
        placement = MagicMock(spec=TournamentPlacement)
        placement.id = uuid4()
        placement.decklist = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = placement
        mock_db.execute.return_value = mock_result

        tid = uuid4()
        response = client.get(
            f"/api/v1/tournaments/{tid}/placements/{placement.id}/decklist"
        )

        assert response.status_code == 404

    def test_decklist_empty_list(self, client: TestClient, mock_db: AsyncMock) -> None:
        """Test 404 when placement has empty decklist."""
        placement = MagicMock(spec=TournamentPlacement)
        placement.id = uuid4()
        placement.decklist = []

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = placement
        mock_db.execute.return_value = mock_result

        tid = uuid4()
        response = client.get(
            f"/api/v1/tournaments/{tid}/placements/{placement.id}/decklist"
        )

        assert response.status_code == 404

    def test_decklist_card_name_fallback(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test that card IDs are used as fallback names when resolution fails."""
        tournament = MagicMock(spec=Tournament)
        tournament.name = "City League"
        tournament.date = date(2024, 3, 10)

        placement = MagicMock(spec=TournamentPlacement)
        placement.id = uuid4()
        placement.tournament_id = uuid4()
        placement.player_name = None
        placement.archetype = "Unknown"
        placement.decklist = [{"card_id": "unknown-1", "quantity": 4}]
        placement.decklist_source = None
        placement.tournament = tournament

        mock_placement_result = MagicMock()
        mock_placement_result.scalar_one_or_none.return_value = placement

        # Card resolution returns empty (card not found)
        mock_card_result = MagicMock()
        mock_card_result.__iter__ = MagicMock(return_value=iter([]))

        mock_db.execute.side_effect = [mock_placement_result, mock_card_result]

        response = client.get(
            f"/api/v1/tournaments/{placement.tournament_id}/placements/{placement.id}/decklist"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["cards"][0]["card_name"] == "unknown-1"  # Fallback to card_id
        assert data["cards"][0]["supertype"] is None


class TestDecklistSchemas:
    """Tests for decklist Pydantic schemas."""

    def test_decklist_card_response(self) -> None:
        """Test DecklistCardResponse schema."""
        from src.schemas.tournament import DecklistCardResponse

        card = DecklistCardResponse(
            card_id="sv4-6",
            card_name="Charizard ex",
            quantity=3,
            supertype="Pokemon",
        )
        assert card.card_id == "sv4-6"
        assert card.card_name == "Charizard ex"
        assert card.quantity == 3
        assert card.supertype == "Pokemon"

    def test_decklist_response(self) -> None:
        """Test DecklistResponse schema."""
        from src.schemas.tournament import DecklistCardResponse, DecklistResponse

        decklist = DecklistResponse(
            placement_id="test-id",
            player_name="Test Player",
            archetype="Charizard ex",
            tournament_name="City League",
            tournament_date=date(2024, 3, 10),
            source_url="https://limitlesstcg.com/decks/abc",
            cards=[
                DecklistCardResponse(
                    card_id="sv4-6",
                    card_name="Charizard ex",
                    quantity=3,
                    supertype="Pokemon",
                )
            ],
            total_cards=3,
        )
        assert decklist.archetype == "Charizard ex"
        assert decklist.total_cards == 3
        assert len(decklist.cards) == 1


class TestGetTournament:
    """Tests for GET /api/v1/tournaments/{tournament_id}."""

    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        """Create mock database session."""
        return AsyncMock()

    @pytest.fixture
    def client(self, mock_db: AsyncMock) -> TestClient:
        """Create test client with mocked database."""
        from src.db.database import get_db
        from src.dependencies.beta import require_beta

        async def override_get_db():
            yield mock_db

        async def override_require_beta():
            return None

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[require_beta] = override_require_beta
        yield TestClient(app)
        app.dependency_overrides.clear()

    @pytest.fixture
    def sample_tournament_with_placements(self) -> MagicMock:
        """Create a sample tournament with placements for detail view."""
        tournament = MagicMock(spec=Tournament)
        tournament.id = uuid4()
        tournament.name = "Charlotte Regional"
        tournament.date = date(2024, 3, 15)
        tournament.region = "NA"
        tournament.country = "USA"
        tournament.format = "standard"
        tournament.best_of = 3
        tournament.tier = "major"
        tournament.participant_count = 512
        tournament.source = "limitless"
        tournament.source_url = "https://limitlesstcg.com/tournaments/en/1234"

        p1 = MagicMock(spec=TournamentPlacement)
        p1.id = uuid4()
        p1.placement = 1
        p1.player_name = "Alice"
        p1.archetype = "Charizard ex"
        p1.decklist = [{"card_id": "sv3-125", "quantity": 3}]

        p2 = MagicMock(spec=TournamentPlacement)
        p2.id = uuid4()
        p2.placement = 2
        p2.player_name = "Bob"
        p2.archetype = "Lugia VSTAR"
        p2.decklist = None

        p3 = MagicMock(spec=TournamentPlacement)
        p3.id = uuid4()
        p3.placement = 3
        p3.player_name = "Charlie"
        p3.archetype = "Charizard ex"
        p3.decklist = [{"card_id": "sv3-125", "quantity": 2}]

        tournament.placements = [p2, p3, p1]  # Intentionally unordered

        return tournament

    def test_get_tournament_success(
        self,
        client: TestClient,
        mock_db: AsyncMock,
        sample_tournament_with_placements: MagicMock,
    ) -> None:
        """Test getting tournament detail successfully."""
        tournament = sample_tournament_with_placements
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = tournament
        mock_db.execute.return_value = mock_result

        response = client.get(f"/api/v1/tournaments/{tournament.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Charlotte Regional"
        assert data["region"] == "NA"
        assert data["format"] == "standard"
        assert data["best_of"] == 3
        assert data["tier"] == "major"
        assert data["participant_count"] == 512
        assert data["source"] == "limitless"
        assert data["source_url"] == "https://limitlesstcg.com/tournaments/en/1234"

        # Placements should be sorted by placement number
        assert len(data["placements"]) == 3
        assert data["placements"][0]["placement"] == 1
        assert data["placements"][0]["player_name"] == "Alice"
        assert data["placements"][0]["has_decklist"] is True
        assert data["placements"][1]["placement"] == 2
        assert data["placements"][1]["has_decklist"] is False
        assert data["placements"][2]["placement"] == 3

    def test_get_tournament_not_found(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test 404 when tournament does not exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        tid = uuid4()
        response = client.get(f"/api/v1/tournaments/{tid}")

        assert response.status_code == 404
        assert "Tournament not found" in response.json()["detail"]

    def test_get_tournament_db_error_returns_503(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test database error returns 503."""
        from sqlalchemy.exc import SQLAlchemyError

        mock_db.execute.side_effect = SQLAlchemyError("Connection failed")

        tid = uuid4()
        response = client.get(f"/api/v1/tournaments/{tid}")

        assert response.status_code == 503
        assert "try again later" in response.json()["detail"]

    def test_get_tournament_meta_breakdown(
        self,
        client: TestClient,
        mock_db: AsyncMock,
        sample_tournament_with_placements: MagicMock,
    ) -> None:
        """Test meta breakdown is computed correctly from placements."""
        tournament = sample_tournament_with_placements
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = tournament
        mock_db.execute.return_value = mock_result

        response = client.get(f"/api/v1/tournaments/{tournament.id}")

        assert response.status_code == 200
        data = response.json()

        # 2 Charizard ex, 1 Lugia VSTAR
        meta = {m["archetype"]: m for m in data["meta_breakdown"]}
        assert "Charizard ex" in meta
        assert meta["Charizard ex"]["count"] == 2
        assert meta["Charizard ex"]["share"] == round(2 / 3, 4)

        assert "Lugia VSTAR" in meta
        assert meta["Lugia VSTAR"]["count"] == 1
        assert meta["Lugia VSTAR"]["share"] == round(1 / 3, 4)
