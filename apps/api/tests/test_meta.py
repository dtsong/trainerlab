"""Tests for meta snapshot endpoints."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.models.meta_snapshot import MetaSnapshot


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

        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
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
