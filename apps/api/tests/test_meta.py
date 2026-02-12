"""Tests for meta snapshot endpoints."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.models.meta_snapshot import MetaSnapshot
from src.models.tournament import Tournament
from src.models.tournament_placement import TournamentPlacement


class TestMetaEndpoints:
    """Tests for meta API endpoints."""

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
    def sample_snapshot(self) -> MagicMock:
        """Create a sample meta snapshot mock."""
        snapshot = MagicMock(spec=MetaSnapshot)
        snapshot.snapshot_date = date(2024, 1, 15)
        snapshot.region = None
        snapshot.format = "standard"
        snapshot.best_of = 3
        snapshot.archetype_shares = {
            "Charizard ex": 0.15,
            "Lugia VSTAR": 0.12,
            "Giratina VSTAR": 0.10,
        }
        snapshot.card_usage = {
            "sv4-6": {"inclusion_rate": 0.85, "avg_count": 3.5},
            "sv3-1": {"inclusion_rate": 0.60, "avg_count": 2.0},
        }
        snapshot.sample_size = 100
        snapshot.tournaments_included = ["tournament-1", "tournament-2"]
        snapshot.diversity_index = None
        snapshot.tier_assignments = None
        snapshot.jp_signals = None
        snapshot.trends = None
        snapshot.era_label = None
        snapshot.tournament_type = "all"
        return snapshot


class TestGetCurrentMeta(TestMetaEndpoints):
    """Tests for GET /api/v1/meta/current."""

    def test_get_current_meta_success(
        self, client: TestClient, mock_db: AsyncMock, sample_snapshot: MagicMock
    ) -> None:
        """Test getting current meta snapshot successfully."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_snapshot
        mock_db.execute.return_value = mock_result

        response = client.get("/api/v1/meta/current")

        assert response.status_code == 200
        data = response.json()
        assert data["snapshot_date"] == "2024-01-15"
        assert data["region"] is None
        assert data["format"] == "standard"
        assert data["best_of"] == 3
        assert data["sample_size"] == 100
        assert len(data["archetype_breakdown"]) == 3
        assert len(data["card_usage"]) == 2
        assert data["freshness"]["cadence_profile"] == "default_cadence"
        assert "status" in data["freshness"]

    def test_get_current_meta_not_found(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test getting current meta when no snapshot exists."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        response = client.get("/api/v1/meta/current")

        assert response.status_code == 404
        data = response.json()
        assert "No meta snapshot found" in data["detail"]

    def test_get_current_meta_with_region_filter(
        self, client: TestClient, mock_db: AsyncMock, sample_snapshot: MagicMock
    ) -> None:
        """Test filtering current meta by region."""
        sample_snapshot.region = "NA"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_snapshot
        mock_db.execute.return_value = mock_result

        response = client.get("/api/v1/meta/current?region=NA")

        assert response.status_code == 200
        data = response.json()
        assert data["region"] == "NA"

    def test_get_current_meta_with_format_filter(
        self, client: TestClient, mock_db: AsyncMock, sample_snapshot: MagicMock
    ) -> None:
        """Test filtering current meta by format."""
        sample_snapshot.format = "expanded"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_snapshot
        mock_db.execute.return_value = mock_result

        response = client.get("/api/v1/meta/current?format=expanded")

        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "expanded"

    def test_get_current_meta_with_best_of_filter(
        self, client: TestClient, mock_db: AsyncMock, sample_snapshot: MagicMock
    ) -> None:
        """Test filtering current meta by best_of."""
        sample_snapshot.best_of = 1
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_snapshot
        mock_db.execute.return_value = mock_result

        response = client.get("/api/v1/meta/current?best_of=1")

        assert response.status_code == 200
        data = response.json()
        assert data["best_of"] == 1

    def test_get_current_meta_invalid_format(self, client: TestClient) -> None:
        """Test invalid format parameter returns 422."""
        response = client.get("/api/v1/meta/current?format=invalid")
        assert response.status_code == 422

    def test_get_current_meta_invalid_best_of(self, client: TestClient) -> None:
        """Test invalid best_of parameter returns 422."""
        response = client.get("/api/v1/meta/current?best_of=2")
        assert response.status_code == 422


class TestGetMetaHistory(TestMetaEndpoints):
    """Tests for GET /api/v1/meta/history."""

    def test_get_meta_history_success(
        self, client: TestClient, mock_db: AsyncMock, sample_snapshot: MagicMock
    ) -> None:
        """Test getting meta history successfully."""
        snapshot2 = MagicMock(spec=MetaSnapshot)
        snapshot2.snapshot_date = date(2024, 1, 8)
        snapshot2.region = None
        snapshot2.format = "standard"
        snapshot2.best_of = 3
        snapshot2.archetype_shares = {"Charizard ex": 0.14}
        snapshot2.card_usage = {}
        snapshot2.sample_size = 80
        snapshot2.tournaments_included = ["tournament-3"]
        snapshot2.diversity_index = None
        snapshot2.tier_assignments = None
        snapshot2.jp_signals = None
        snapshot2.trends = None
        snapshot2.era_label = None
        snapshot2.tournament_type = "all"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            sample_snapshot,
            snapshot2,
        ]
        mock_db.execute.return_value = mock_result

        response = client.get("/api/v1/meta/history")

        assert response.status_code == 200
        data = response.json()
        assert "snapshots" in data
        assert len(data["snapshots"]) == 2
        assert data["snapshots"][0]["snapshot_date"] == "2024-01-15"
        assert data["snapshots"][1]["snapshot_date"] == "2024-01-08"
        assert data["snapshots"][0]["freshness"]["cadence_profile"] == "default_cadence"

    def test_get_meta_history_empty(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test getting meta history when no snapshots exist."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        response = client.get("/api/v1/meta/history")

        assert response.status_code == 200
        data = response.json()
        assert data["snapshots"] == []

    def test_get_meta_history_with_days_filter(
        self, client: TestClient, mock_db: AsyncMock, sample_snapshot: MagicMock
    ) -> None:
        """Test filtering meta history by days."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_snapshot]
        mock_db.execute.return_value = mock_result

        response = client.get("/api/v1/meta/history?days=30")

        assert response.status_code == 200
        data = response.json()
        assert len(data["snapshots"]) == 1

    def test_get_meta_history_with_region_filter(
        self, client: TestClient, mock_db: AsyncMock, sample_snapshot: MagicMock
    ) -> None:
        """Test filtering meta history by region."""
        sample_snapshot.region = "EU"
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_snapshot]
        mock_db.execute.return_value = mock_result

        response = client.get("/api/v1/meta/history?region=EU")

        assert response.status_code == 200
        data = response.json()
        assert data["snapshots"][0]["region"] == "EU"

    def test_get_meta_history_invalid_days(self, client: TestClient) -> None:
        """Test invalid days parameter returns 422."""
        response = client.get("/api/v1/meta/history?days=0")
        assert response.status_code == 422

        response = client.get("/api/v1/meta/history?days=400")
        assert response.status_code == 422


class TestListArchetypes(TestMetaEndpoints):
    """Tests for GET /api/v1/meta/archetypes."""

    def test_list_archetypes_success(
        self, client: TestClient, mock_db: AsyncMock, sample_snapshot: MagicMock
    ) -> None:
        """Test listing archetypes successfully."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_snapshot
        mock_db.execute.return_value = mock_result

        response = client.get("/api/v1/meta/archetypes")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3
        # Should be sorted by share descending
        assert data[0]["name"] == "Charizard ex"
        assert data[0]["share"] == 0.15
        assert data[1]["name"] == "Lugia VSTAR"
        assert data[2]["name"] == "Giratina VSTAR"

    def test_list_archetypes_not_found(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test listing archetypes when no snapshot exists returns 404."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        response = client.get("/api/v1/meta/archetypes")

        assert response.status_code == 404
        data = response.json()
        assert "No meta snapshot found" in data["detail"]

    def test_list_archetypes_empty_snapshot(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test listing archetypes when snapshot has no archetypes."""
        snapshot = MagicMock(spec=MetaSnapshot)
        snapshot.snapshot_date = date(2024, 1, 15)
        snapshot.archetype_shares = {}

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = snapshot
        mock_db.execute.return_value = mock_result

        response = client.get("/api/v1/meta/archetypes")

        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_list_archetypes_with_region_filter(
        self, client: TestClient, mock_db: AsyncMock, sample_snapshot: MagicMock
    ) -> None:
        """Test filtering archetypes by region."""
        sample_snapshot.region = "JP"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_snapshot
        mock_db.execute.return_value = mock_result

        response = client.get("/api/v1/meta/archetypes?region=JP")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_list_archetypes_with_format_filter(
        self, client: TestClient, mock_db: AsyncMock, sample_snapshot: MagicMock
    ) -> None:
        """Test filtering archetypes by format."""
        sample_snapshot.format = "expanded"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_snapshot
        mock_db.execute.return_value = mock_result

        response = client.get("/api/v1/meta/archetypes?format=expanded")

        assert response.status_code == 200

    def test_list_archetypes_with_best_of_filter(
        self, client: TestClient, mock_db: AsyncMock, sample_snapshot: MagicMock
    ) -> None:
        """Test filtering archetypes by best_of."""
        sample_snapshot.best_of = 1
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_snapshot
        mock_db.execute.return_value = mock_result

        response = client.get("/api/v1/meta/archetypes?best_of=1")

        assert response.status_code == 200


class TestMetaSchemas:
    """Tests for meta Pydantic schemas."""

    def test_archetype_response_validation(self) -> None:
        """Test ArchetypeResponse schema validation."""
        from src.schemas.meta import ArchetypeResponse

        archetype = ArchetypeResponse(name="Charizard ex", share=0.15)
        assert archetype.name == "Charizard ex"
        assert archetype.share == 0.15
        assert archetype.sample_decks is None
        assert archetype.key_cards is None

    def test_archetype_response_with_optional_fields(self) -> None:
        """Test ArchetypeResponse with optional fields."""
        from src.schemas.meta import ArchetypeResponse

        archetype = ArchetypeResponse(
            name="Charizard ex",
            share=0.15,
            sample_decks=["deck-1", "deck-2"],
            key_cards=["card-1", "card-2"],
        )
        assert archetype.sample_decks == ["deck-1", "deck-2"]
        assert archetype.key_cards == ["card-1", "card-2"]

    def test_archetype_response_share_bounds(self) -> None:
        """Test ArchetypeResponse share bounds validation."""
        from pydantic import ValidationError

        from src.schemas.meta import ArchetypeResponse

        with pytest.raises(ValidationError):
            ArchetypeResponse(name="Test", share=-0.1)

        with pytest.raises(ValidationError):
            ArchetypeResponse(name="Test", share=1.5)

    def test_card_usage_summary_validation(self) -> None:
        """Test CardUsageSummary schema validation."""
        from src.schemas.meta import CardUsageSummary

        usage = CardUsageSummary(card_id="sv4-6", inclusion_rate=0.85, avg_copies=3.5)
        assert usage.card_id == "sv4-6"
        assert usage.inclusion_rate == 0.85
        assert usage.avg_copies == 3.5

    def test_meta_snapshot_response_validation(self) -> None:
        """Test MetaSnapshotResponse schema validation."""
        from src.schemas.meta import (
            ArchetypeResponse,
            CardUsageSummary,
            MetaSnapshotResponse,
        )

        snapshot = MetaSnapshotResponse(
            snapshot_date=date(2024, 1, 15),
            region=None,
            format="standard",
            best_of=3,
            archetype_breakdown=[
                ArchetypeResponse(name="Charizard ex", share=0.15),
            ],
            card_usage=[
                CardUsageSummary(card_id="sv4-6", inclusion_rate=0.85, avg_copies=3.5),
            ],
            sample_size=100,
            tournaments_included=["tournament-1"],
        )

        assert snapshot.snapshot_date == date(2024, 1, 15)
        assert snapshot.region is None
        assert snapshot.format == "standard"
        assert len(snapshot.archetype_breakdown) == 1
        assert len(snapshot.card_usage) == 1

    def test_meta_history_response_validation(self) -> None:
        """Test MetaHistoryResponse schema validation."""
        from src.schemas.meta import MetaHistoryResponse, MetaSnapshotResponse

        history = MetaHistoryResponse(
            snapshots=[
                MetaSnapshotResponse(
                    snapshot_date=date(2024, 1, 15),
                    format="standard",
                    best_of=3,
                    archetype_breakdown=[],
                    sample_size=100,
                ),
            ]
        )

        assert len(history.snapshots) == 1


class TestJapanBO1Meta(TestMetaEndpoints):
    """Tests for Japan BO1 meta handling."""

    def test_bo1_meta_includes_format_notes(
        self, client: TestClient, mock_db: AsyncMock, sample_snapshot: MagicMock
    ) -> None:
        """Test that BO1 meta snapshots include Japan format notes."""
        sample_snapshot.best_of = 1
        sample_snapshot.region = "JP"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_snapshot
        mock_db.execute.return_value = mock_result

        response = client.get("/api/v1/meta/current?best_of=1&region=JP")

        assert response.status_code == 200
        data = response.json()
        assert data["best_of"] == 1
        assert data["format_notes"] is not None
        assert "double loss" in data["format_notes"]["tie_rules"]
        assert "JP" in data["format_notes"]["typical_regions"]

    def test_bo3_meta_no_format_notes(
        self, client: TestClient, mock_db: AsyncMock, sample_snapshot: MagicMock
    ) -> None:
        """Test that BO3 meta snapshots do not include BO1 format notes."""
        sample_snapshot.best_of = 3
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_snapshot
        mock_db.execute.return_value = mock_result

        response = client.get("/api/v1/meta/current?best_of=3")

        assert response.status_code == 200
        data = response.json()
        assert data["best_of"] == 3
        assert data["format_notes"] is None

    def test_bo1_history_includes_format_notes(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test that BO1 meta history includes format notes."""
        snapshot = MagicMock(spec=MetaSnapshot)
        snapshot.snapshot_date = date(2024, 1, 15)
        snapshot.region = "JP"
        snapshot.format = "standard"
        snapshot.best_of = 1
        snapshot.archetype_shares = {"Charizard ex": 0.15}
        snapshot.card_usage = {}
        snapshot.sample_size = 100
        snapshot.tournaments_included = []
        snapshot.diversity_index = None
        snapshot.tier_assignments = None
        snapshot.jp_signals = None
        snapshot.trends = None
        snapshot.era_label = None
        snapshot.tournament_type = "all"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [snapshot]
        mock_db.execute.return_value = mock_result

        response = client.get("/api/v1/meta/history?best_of=1&region=JP")

        assert response.status_code == 200
        data = response.json()
        assert len(data["snapshots"]) == 1
        assert data["snapshots"][0]["format_notes"] is not None
        assert "double loss" in data["snapshots"][0]["format_notes"]["tie_rules"]

    def test_bo1_non_jp_region_no_format_notes(
        self, client: TestClient, mock_db: AsyncMock, sample_snapshot: MagicMock
    ) -> None:
        """Test that BO1 with non-JP region does not include format notes.

        International major events are all BO3, so only Japan BO1
        tournaments need the special tie rule documentation.
        """
        sample_snapshot.best_of = 1
        sample_snapshot.region = "NA"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_snapshot
        mock_db.execute.return_value = mock_result

        response = client.get("/api/v1/meta/current?best_of=1&region=NA")

        assert response.status_code == 200
        data = response.json()
        assert data["best_of"] == 1
        assert data["region"] == "NA"
        assert data["format_notes"] is None


class TestGetArchetypeDetail(TestMetaEndpoints):
    """Tests for GET /api/v1/meta/archetypes/{name}."""

    def test_get_archetype_detail_success(
        self, client: TestClient, mock_db: AsyncMock, sample_snapshot: MagicMock
    ) -> None:
        """Test getting archetype detail successfully."""
        # Mock snapshot query
        mock_snapshot_result = MagicMock()
        mock_snapshot_result.scalars.return_value.all.return_value = [sample_snapshot]

        # Mock placement query (empty placements)
        mock_placement_result = MagicMock()
        mock_placement_result.scalars.return_value.all.return_value = []

        mock_db.execute.side_effect = [mock_snapshot_result, mock_placement_result]

        response = client.get("/api/v1/meta/archetypes/Charizard%20ex")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Charizard ex"
        assert data["current_share"] == 0.15
        assert len(data["history"]) == 1
        assert data["history"][0]["share"] == 0.15

    def test_get_archetype_detail_not_found(
        self, client: TestClient, mock_db: AsyncMock, sample_snapshot: MagicMock
    ) -> None:
        """Test getting archetype that doesn't exist returns 404."""
        mock_snapshot_result = MagicMock()
        mock_snapshot_result.scalars.return_value.all.return_value = [sample_snapshot]
        mock_db.execute.return_value = mock_snapshot_result

        response = client.get("/api/v1/meta/archetypes/NonexistentArchetype")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_get_archetype_detail_with_placements(
        self, client: TestClient, mock_db: AsyncMock, sample_snapshot: MagicMock
    ) -> None:
        """Test archetype detail includes key cards from placements."""
        from uuid import uuid4

        # Mock placement with decklist
        placement = MagicMock(spec=TournamentPlacement)
        placement.id = uuid4()
        placement.tournament_id = uuid4()
        placement.archetype = "Charizard ex"
        placement.placement = 1
        placement.player_name = "Test Player"
        placement.decklist = [
            {"card_id": "sv4-6", "quantity": 4},
            {"card_id": "sv3-1", "quantity": 3},
        ]

        tournament = MagicMock(spec=Tournament)
        tournament.id = placement.tournament_id
        tournament.name = "Test Tournament"

        # Mock snapshot query
        mock_snapshot_result = MagicMock()
        mock_snapshot_result.scalars.return_value.all.return_value = [sample_snapshot]

        # Mock placement query
        mock_placement_result = MagicMock()
        mock_placement_result.scalars.return_value.all.return_value = [placement]

        # Mock tournament query
        mock_tournament_result = MagicMock()
        mock_tournament_result.scalars.return_value.all.return_value = [tournament]

        # Card enrichment query (returns no matching cards)
        mock_card_enrich_result = MagicMock()
        mock_card_enrich_result.all.return_value = []

        # Card ID mapping fallback (no mappings found)
        mock_mapping_result = MagicMock()
        mock_mapping_result.all.return_value = []

        mock_db.execute.side_effect = [
            mock_snapshot_result,
            mock_placement_result,
            mock_card_enrich_result,
            mock_mapping_result,
            mock_tournament_result,
        ]

        response = client.get("/api/v1/meta/archetypes/Charizard%20ex")

        assert response.status_code == 200
        data = response.json()
        assert len(data["key_cards"]) == 2
        assert data["key_cards"][0]["card_id"] in ["sv4-6", "sv3-1"]
        assert len(data["sample_decks"]) == 1
        assert data["sample_decks"][0]["tournament_name"] == "Test Tournament"

    def test_get_archetype_detail_with_region_filter(
        self, client: TestClient, mock_db: AsyncMock, sample_snapshot: MagicMock
    ) -> None:
        """Test filtering archetype detail by region."""
        sample_snapshot.region = "NA"
        mock_snapshot_result = MagicMock()
        mock_snapshot_result.scalars.return_value.all.return_value = [sample_snapshot]

        mock_placement_result = MagicMock()
        mock_placement_result.scalars.return_value.all.return_value = []

        mock_db.execute.side_effect = [mock_snapshot_result, mock_placement_result]

        response = client.get("/api/v1/meta/archetypes/Charizard%20ex?region=NA")

        assert response.status_code == 200

    def test_get_archetype_detail_history_over_time(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test archetype history shows share changes over time."""
        snapshot1 = MagicMock(spec=MetaSnapshot)
        snapshot1.snapshot_date = date(2024, 1, 15)
        snapshot1.archetype_shares = {"Charizard ex": 0.15}
        snapshot1.sample_size = 100

        snapshot2 = MagicMock(spec=MetaSnapshot)
        snapshot2.snapshot_date = date(2024, 1, 8)
        snapshot2.archetype_shares = {"Charizard ex": 0.12}
        snapshot2.sample_size = 80

        mock_snapshot_result = MagicMock()
        mock_snapshot_result.scalars.return_value.all.return_value = [
            snapshot1,
            snapshot2,
        ]

        mock_placement_result = MagicMock()
        mock_placement_result.scalars.return_value.all.return_value = []

        mock_db.execute.side_effect = [mock_snapshot_result, mock_placement_result]

        response = client.get("/api/v1/meta/archetypes/Charizard%20ex")

        assert response.status_code == 200
        data = response.json()
        assert len(data["history"]) == 2
        assert data["history"][0]["share"] == 0.15
        assert data["history"][1]["share"] == 0.12

    def test_get_archetype_detail_snapshot_db_error_returns_503(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test database error during snapshot query returns 503."""
        from sqlalchemy.exc import SQLAlchemyError

        mock_db.execute.side_effect = SQLAlchemyError("Connection failed")

        response = client.get("/api/v1/meta/archetypes/Charizard%20ex")

        assert response.status_code == 503
        assert "try again later" in response.json()["detail"]

    def test_get_archetype_detail_placement_db_error_returns_503(
        self, client: TestClient, mock_db: AsyncMock, sample_snapshot: MagicMock
    ) -> None:
        """Test database error during placement query returns 503."""
        from sqlalchemy.exc import SQLAlchemyError

        mock_snapshot_result = MagicMock()
        mock_snapshot_result.scalars.return_value.all.return_value = [sample_snapshot]

        mock_db.execute.side_effect = [
            mock_snapshot_result,
            SQLAlchemyError("Placement query failed"),
        ]

        response = client.get("/api/v1/meta/archetypes/Charizard%20ex")

        assert response.status_code == 503
        assert "try again later" in response.json()["detail"]

    def test_get_archetype_detail_tournament_db_error_returns_503(
        self, client: TestClient, mock_db: AsyncMock, sample_snapshot: MagicMock
    ) -> None:
        """Test database error during tournament lookup returns 503."""
        from uuid import uuid4

        from sqlalchemy.exc import SQLAlchemyError

        placement = MagicMock(spec=TournamentPlacement)
        placement.id = uuid4()
        placement.tournament_id = uuid4()
        placement.decklist = [{"card_id": "sv4-6", "quantity": 4}]

        mock_snapshot_result = MagicMock()
        mock_snapshot_result.scalars.return_value.all.return_value = [sample_snapshot]

        mock_placement_result = MagicMock()
        mock_placement_result.scalars.return_value.all.return_value = [placement]

        # Card enrichment query (returns no matching cards)
        mock_card_enrich_result = MagicMock()
        mock_card_enrich_result.all.return_value = []

        # Card ID mapping fallback (no mappings found)
        mock_mapping_result = MagicMock()
        mock_mapping_result.all.return_value = []

        mock_db.execute.side_effect = [
            mock_snapshot_result,
            mock_placement_result,
            mock_card_enrich_result,
            mock_mapping_result,
            SQLAlchemyError("Tournament query failed"),
        ]

        response = client.get("/api/v1/meta/archetypes/Charizard%20ex")

        assert response.status_code == 503
        assert "try again later" in response.json()["detail"]

    def test_get_archetype_detail_no_snapshots_returns_404(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test 404 when no meta snapshots exist."""
        mock_snapshot_result = MagicMock()
        mock_snapshot_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_snapshot_result

        response = client.get("/api/v1/meta/archetypes/Charizard%20ex")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_get_archetype_detail_invalid_format(self, client: TestClient) -> None:
        """Test invalid format parameter returns 422."""
        response = client.get("/api/v1/meta/archetypes/Charizard%20ex?format=invalid")
        assert response.status_code == 422

    def test_get_archetype_detail_invalid_best_of(self, client: TestClient) -> None:
        """Test invalid best_of parameter returns 422."""
        response = client.get("/api/v1/meta/archetypes/Charizard%20ex?best_of=2")
        assert response.status_code == 422

    def test_get_archetype_detail_invalid_days(self, client: TestClient) -> None:
        """Test invalid days parameter returns 422."""
        response = client.get("/api/v1/meta/archetypes/Charizard%20ex?days=0")
        assert response.status_code == 422

        response = client.get("/api/v1/meta/archetypes/Charizard%20ex?days=400")
        assert response.status_code == 422

    def test_get_archetype_detail_with_format_filter(
        self, client: TestClient, mock_db: AsyncMock, sample_snapshot: MagicMock
    ) -> None:
        """Test filtering archetype detail by format."""
        sample_snapshot.format = "expanded"
        mock_snapshot_result = MagicMock()
        mock_snapshot_result.scalars.return_value.all.return_value = [sample_snapshot]

        mock_placement_result = MagicMock()
        mock_placement_result.scalars.return_value.all.return_value = []

        mock_db.execute.side_effect = [mock_snapshot_result, mock_placement_result]

        response = client.get("/api/v1/meta/archetypes/Charizard%20ex?format=expanded")

        assert response.status_code == 200

    def test_get_archetype_detail_with_best_of_filter(
        self, client: TestClient, mock_db: AsyncMock, sample_snapshot: MagicMock
    ) -> None:
        """Test filtering archetype detail by best_of (BO1 for Japan)."""
        sample_snapshot.best_of = 1
        mock_snapshot_result = MagicMock()
        mock_snapshot_result.scalars.return_value.all.return_value = [sample_snapshot]

        mock_placement_result = MagicMock()
        mock_placement_result.scalars.return_value.all.return_value = []

        mock_db.execute.side_effect = [mock_snapshot_result, mock_placement_result]

        response = client.get("/api/v1/meta/archetypes/Charizard%20ex?best_of=1")

        assert response.status_code == 200

    def test_get_archetype_detail_zero_share_handled_correctly(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test current_share=0.0 is returned correctly (not skipped)."""
        snapshot = MagicMock(spec=MetaSnapshot)
        snapshot.snapshot_date = date(2024, 1, 15)
        snapshot.archetype_shares = {"Charizard ex": 0.0}  # Archetype dropped to 0%
        snapshot.sample_size = 100

        mock_snapshot_result = MagicMock()
        mock_snapshot_result.scalars.return_value.all.return_value = [snapshot]

        mock_placement_result = MagicMock()
        mock_placement_result.scalars.return_value.all.return_value = []

        mock_db.execute.side_effect = [mock_snapshot_result, mock_placement_result]

        response = client.get("/api/v1/meta/archetypes/Charizard%20ex")

        assert response.status_code == 200
        data = response.json()
        assert data["current_share"] == 0.0  # Should be 0.0, not skipped
        assert len(data["history"]) == 1
        assert data["history"][0]["share"] == 0.0

    def test_get_archetype_detail_handles_malformed_decklist(
        self, client: TestClient, mock_db: AsyncMock, sample_snapshot: MagicMock
    ) -> None:
        """Test key cards computation handles malformed decklist data gracefully."""
        from uuid import uuid4

        placement = MagicMock(spec=TournamentPlacement)
        placement.id = uuid4()
        placement.tournament_id = uuid4()
        placement.placement = 1
        placement.player_name = "Test Player"
        placement.decklist = [
            {"card_id": "sv4-6", "quantity": 4},  # Valid
            "not_a_dict",  # Non-dict entry (should be skipped)
            {"quantity": 2},  # Missing card_id (should be skipped)
            {"card_id": "", "quantity": 2},  # Empty card_id (should be skipped)
            {"card_id": "sv3-1", "quantity": "invalid"},  # Non-numeric (skip)
            {"card_id": "sv3-2", "quantity": 0},  # Zero quantity (skip)
            {"card_id": "sv3-3", "quantity": -1},  # Negative quantity (skip)
        ]

        tournament = MagicMock(spec=Tournament)
        tournament.id = placement.tournament_id
        tournament.name = "Test Tournament"

        mock_snapshot_result = MagicMock()
        mock_snapshot_result.scalars.return_value.all.return_value = [sample_snapshot]

        mock_placement_result = MagicMock()
        mock_placement_result.scalars.return_value.all.return_value = [placement]

        mock_tournament_result = MagicMock()
        mock_tournament_result.scalars.return_value.all.return_value = [tournament]

        # Card enrichment query (returns no matching cards)
        mock_card_enrich_result = MagicMock()
        mock_card_enrich_result.all.return_value = []

        # Card ID mapping fallback (no mappings found)
        mock_mapping_result = MagicMock()
        mock_mapping_result.all.return_value = []

        mock_db.execute.side_effect = [
            mock_snapshot_result,
            mock_placement_result,
            mock_card_enrich_result,
            mock_mapping_result,
            mock_tournament_result,
        ]

        response = client.get("/api/v1/meta/archetypes/Charizard%20ex")

        assert response.status_code == 200
        data = response.json()
        # Only sv4-6 should appear in key_cards (only valid entry)
        assert len(data["key_cards"]) == 1
        assert data["key_cards"][0]["card_id"] == "sv4-6"
        assert data["key_cards"][0]["inclusion_rate"] == 1.0
        assert data["key_cards"][0]["avg_copies"] == 4.0

    def test_get_archetype_detail_key_card_calculations(
        self, client: TestClient, mock_db: AsyncMock, sample_snapshot: MagicMock
    ) -> None:
        """Test key card inclusion_rate and avg_copies are calculated correctly."""
        from uuid import uuid4

        # Two placements with different card counts
        placement1 = MagicMock(spec=TournamentPlacement)
        placement1.id = uuid4()
        placement1.tournament_id = uuid4()
        placement1.placement = 1
        placement1.player_name = "Player 1"
        placement1.decklist = [
            {"card_id": "sv4-6", "quantity": 4},  # In both
            {"card_id": "sv3-1", "quantity": 2},  # Only in placement1
        ]

        placement2 = MagicMock(spec=TournamentPlacement)
        placement2.id = uuid4()
        placement2.tournament_id = placement1.tournament_id
        placement2.placement = 2
        placement2.player_name = "Player 2"
        placement2.decklist = [
            {"card_id": "sv4-6", "quantity": 3},  # In both (different count)
        ]

        tournament = MagicMock(spec=Tournament)
        tournament.id = placement1.tournament_id
        tournament.name = "Test Tournament"

        mock_snapshot_result = MagicMock()
        mock_snapshot_result.scalars.return_value.all.return_value = [sample_snapshot]

        mock_placement_result = MagicMock()
        mock_placement_result.scalars.return_value.all.return_value = [
            placement1,
            placement2,
        ]

        mock_tournament_result = MagicMock()
        mock_tournament_result.scalars.return_value.all.return_value = [tournament]

        # Card enrichment query (returns no matching cards)
        mock_card_enrich_result = MagicMock()
        mock_card_enrich_result.all.return_value = []

        # Card ID mapping fallback (no mappings found)
        mock_mapping_result = MagicMock()
        mock_mapping_result.all.return_value = []

        mock_db.execute.side_effect = [
            mock_snapshot_result,
            mock_placement_result,
            mock_card_enrich_result,
            mock_mapping_result,
            mock_tournament_result,
        ]

        response = client.get("/api/v1/meta/archetypes/Charizard%20ex")

        assert response.status_code == 200
        data = response.json()

        # sv4-6: in both placements (2/2 = 100%), avg (4+3)/2 = 3.5
        # sv3-1: in 1 placement (1/2 = 50%), avg = 2.0
        key_cards = {kc["card_id"]: kc for kc in data["key_cards"]}

        assert key_cards["sv4-6"]["inclusion_rate"] == 1.0
        assert key_cards["sv4-6"]["avg_copies"] == 3.5

        assert key_cards["sv3-1"]["inclusion_rate"] == 0.5
        assert key_cards["sv3-1"]["avg_copies"] == 2.0


class TestComputeMatchupsFromPlacements:
    """Tests for _compute_matchups_from_placements helper function."""

    def test_returns_empty_when_no_placements(self) -> None:
        """Test empty placements return empty matchups."""
        from src.routers.meta import _compute_matchups_from_placements

        matchups, overall_win_rate, total_games = _compute_matchups_from_placements(
            [], "Charizard ex"
        )

        assert matchups == []
        assert overall_win_rate is None
        assert total_games == 0

    def test_returns_empty_when_archetype_not_present(self) -> None:
        """Test returns empty when target archetype is not in placements."""
        from src.routers.meta import _compute_matchups_from_placements

        p1 = MagicMock(spec=TournamentPlacement)
        p1.tournament_id = "t1"
        p1.archetype = "Lugia VSTAR"
        p1.placement = 1

        matchups, overall_win_rate, total_games = _compute_matchups_from_placements(
            [p1], "Charizard ex"
        )

        assert matchups == []
        assert overall_win_rate is None
        assert total_games == 0

    def test_win_when_archetype_places_higher(self) -> None:
        """Test archetype placing higher counts as a win."""
        from src.routers.meta import _compute_matchups_from_placements

        t_id = "tournament-1"

        p1 = MagicMock(spec=TournamentPlacement)
        p1.tournament_id = t_id
        p1.archetype = "Charizard ex"
        p1.placement = 1

        p2 = MagicMock(spec=TournamentPlacement)
        p2.tournament_id = t_id
        p2.archetype = "Lugia VSTAR"
        p2.placement = 2

        matchups, overall_win_rate, total_games = _compute_matchups_from_placements(
            [p1, p2], "Charizard ex"
        )

        assert len(matchups) == 1
        assert matchups[0].opponent == "Lugia VSTAR"
        assert matchups[0].win_rate == 1.0
        assert matchups[0].sample_size == 1
        assert total_games == 1
        assert overall_win_rate == 1.0

    def test_loss_when_archetype_places_lower(self) -> None:
        """Test archetype placing lower counts as a loss."""
        from src.routers.meta import _compute_matchups_from_placements

        t_id = "tournament-1"

        p1 = MagicMock(spec=TournamentPlacement)
        p1.tournament_id = t_id
        p1.archetype = "Charizard ex"
        p1.placement = 5

        p2 = MagicMock(spec=TournamentPlacement)
        p2.tournament_id = t_id
        p2.archetype = "Lugia VSTAR"
        p2.placement = 1

        matchups, overall_win_rate, total_games = _compute_matchups_from_placements(
            [p1, p2], "Charizard ex"
        )

        assert len(matchups) == 1
        assert matchups[0].opponent == "Lugia VSTAR"
        assert matchups[0].win_rate == 0.0
        assert total_games == 1
        assert overall_win_rate == 0.0

    def test_tie_counts_as_half_win(self) -> None:
        """Test equal placement counts as 0.5 win (tie)."""
        from src.routers.meta import _compute_matchups_from_placements

        t_id = "tournament-1"

        p1 = MagicMock(spec=TournamentPlacement)
        p1.tournament_id = t_id
        p1.archetype = "Charizard ex"
        p1.placement = 3

        p2 = MagicMock(spec=TournamentPlacement)
        p2.tournament_id = t_id
        p2.archetype = "Lugia VSTAR"
        p2.placement = 3

        matchups, overall_win_rate, total_games = _compute_matchups_from_placements(
            [p1, p2], "Charizard ex"
        )

        assert len(matchups) == 1
        assert matchups[0].win_rate == 0.5
        assert total_games == 1
        assert overall_win_rate == 0.5

    def test_multiple_tournaments_aggregated(self) -> None:
        """Test matchups aggregate across multiple tournaments."""
        from src.routers.meta import _compute_matchups_from_placements

        # Tournament 1: Charizard wins
        p1 = MagicMock(spec=TournamentPlacement)
        p1.tournament_id = "t1"
        p1.archetype = "Charizard ex"
        p1.placement = 1

        p2 = MagicMock(spec=TournamentPlacement)
        p2.tournament_id = "t1"
        p2.archetype = "Lugia VSTAR"
        p2.placement = 2

        # Tournament 2: Lugia wins
        p3 = MagicMock(spec=TournamentPlacement)
        p3.tournament_id = "t2"
        p3.archetype = "Charizard ex"
        p3.placement = 4

        p4 = MagicMock(spec=TournamentPlacement)
        p4.tournament_id = "t2"
        p4.archetype = "Lugia VSTAR"
        p4.placement = 1

        matchups, overall_win_rate, total_games = _compute_matchups_from_placements(
            [p1, p2, p3, p4], "Charizard ex"
        )

        assert len(matchups) == 1
        assert matchups[0].opponent == "Lugia VSTAR"
        assert matchups[0].win_rate == 0.5  # 1 win, 1 loss = 50%
        assert matchups[0].sample_size == 2
        assert total_games == 2
        assert overall_win_rate == 0.5

    def test_confidence_levels(self) -> None:
        """Test confidence levels based on sample size."""
        from src.routers.meta import _compute_matchup_confidence

        assert _compute_matchup_confidence(50) == "high"
        assert _compute_matchup_confidence(100) == "high"
        assert _compute_matchup_confidence(20) == "medium"
        assert _compute_matchup_confidence(49) == "medium"
        assert _compute_matchup_confidence(19) == "low"
        assert _compute_matchup_confidence(1) == "low"
        assert _compute_matchup_confidence(0) == "low"

    def test_uses_best_placement_per_tournament(self) -> None:
        """Test that the best placement for the archetype is used per tournament."""
        from src.routers.meta import _compute_matchups_from_placements

        t_id = "tournament-1"

        # Two Charizard placements: 2nd and 5th
        p1 = MagicMock(spec=TournamentPlacement)
        p1.tournament_id = t_id
        p1.archetype = "Charizard ex"
        p1.placement = 5

        p2 = MagicMock(spec=TournamentPlacement)
        p2.tournament_id = t_id
        p2.archetype = "Charizard ex"
        p2.placement = 2

        # Opponent at 3rd place
        p3 = MagicMock(spec=TournamentPlacement)
        p3.tournament_id = t_id
        p3.archetype = "Lugia VSTAR"
        p3.placement = 3

        matchups, overall_win_rate, total_games = _compute_matchups_from_placements(
            [p1, p2, p3], "Charizard ex"
        )

        assert len(matchups) == 1
        # Best Charizard placement is 2, opponent is 3 -> win
        assert matchups[0].win_rate == 1.0


class TestGetArchetypeMatchups(TestMetaEndpoints):
    """Tests for GET /api/v1/meta/archetypes/{name}/matchups."""

    def test_get_matchups_success(self, client: TestClient, mock_db: AsyncMock) -> None:
        """Test getting matchup spread successfully."""
        t_id = "tournament-1"

        p1 = MagicMock(spec=TournamentPlacement)
        p1.tournament_id = t_id
        p1.archetype = "Charizard ex"
        p1.placement = 1

        p2 = MagicMock(spec=TournamentPlacement)
        p2.tournament_id = t_id
        p2.archetype = "Lugia VSTAR"
        p2.placement = 2

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [p1, p2]
        mock_db.execute.return_value = mock_result

        response = client.get("/api/v1/meta/archetypes/Charizard%20ex/matchups")

        assert response.status_code == 200
        data = response.json()
        assert data["archetype"] == "Charizard ex"
        assert len(data["matchups"]) == 1
        assert data["matchups"][0]["opponent"] == "Lugia VSTAR"
        assert data["matchups"][0]["win_rate"] == 1.0
        assert data["total_games"] == 1

    def test_get_matchups_archetype_not_found(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test 404 when archetype not found in tournament data."""
        p1 = MagicMock(spec=TournamentPlacement)
        p1.tournament_id = "t1"
        p1.archetype = "Lugia VSTAR"
        p1.placement = 1

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [p1]
        mock_db.execute.return_value = mock_result

        response = client.get("/api/v1/meta/archetypes/NonexistentDeck/matchups")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_get_matchups_db_error_returns_503(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test database error returns 503."""
        from sqlalchemy.exc import SQLAlchemyError

        mock_db.execute.side_effect = SQLAlchemyError("Connection failed")

        response = client.get("/api/v1/meta/archetypes/Charizard%20ex/matchups")

        assert response.status_code == 503
        assert "try again later" in response.json()["detail"]

    def test_get_matchups_limits_to_top_10(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test that matchup results are limited to top 10."""
        placements = []
        t_id = "tournament-1"

        # Create a Charizard placement
        p = MagicMock(spec=TournamentPlacement)
        p.tournament_id = t_id
        p.archetype = "Charizard ex"
        p.placement = 1
        placements.append(p)

        # Create 15 different opponent archetypes
        for i in range(15):
            opp = MagicMock(spec=TournamentPlacement)
            opp.tournament_id = t_id
            opp.archetype = f"Archetype {i}"
            opp.placement = i + 2
            placements.append(opp)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = placements
        mock_db.execute.return_value = mock_result

        response = client.get("/api/v1/meta/archetypes/Charizard%20ex/matchups")

        assert response.status_code == 200
        data = response.json()
        assert len(data["matchups"]) == 10  # Limited to top 10
