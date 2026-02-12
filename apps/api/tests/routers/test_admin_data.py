"""Tests for admin data dashboard endpoints."""

from datetime import UTC, date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.db.database import get_db
from src.dependencies.admin import require_admin
from src.main import app
from src.models.user import User


@pytest.fixture
def mock_db() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_admin() -> MagicMock:
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.email = "admin@trainerlab.gg"
    return user


@pytest.fixture
def client(mock_db: AsyncMock, mock_admin: MagicMock) -> TestClient:
    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[require_admin] = lambda: mock_admin
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def unauthed_client(mock_db: AsyncMock) -> TestClient:
    """Client without admin override."""

    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


class TestGetDataOverview:
    """Tests for GET /api/v1/admin/data/overview."""

    def test_returns_table_counts(self, client: TestClient, mock_db: AsyncMock) -> None:
        """Verify overview returns all table info."""
        # Mock db.scalar calls (one per table count + extras)
        mock_db.scalar = AsyncMock(
            side_effect=[
                42,  # tournaments count
                date(2026, 2, 1),  # tournaments max date
                100,  # tournament_placements count
                10,  # meta_snapshots count
                date(2026, 1, 30),  # meta max date
                5,  # cards count
                2,  # sets count
                3,  # users count
                8,  # archetype_sprites count
                6,  # sprites with urls
                20,  # jp adoption rates count
                date(2026, 1, 15),  # jp adoption max
                4,  # jp new archetypes count
            ]
        )

        # Mock db.execute for distinct regions
        mock_regions_result = MagicMock()
        mock_regions_result.all.return_value = [
            ("NA",),
            ("JP",),
            (None,),
        ]
        mock_db.execute = AsyncMock(return_value=mock_regions_result)

        response = client.get("/api/v1/admin/data/overview")
        assert response.status_code == 200

        data = response.json()
        assert "tables" in data
        assert "generated_at" in data
        assert len(data["tables"]) == 9

        names = [t["name"] for t in data["tables"]]
        assert "tournaments" in names
        assert "meta_snapshots" in names
        assert "cards" in names
        assert "archetype_sprites" in names

    def test_requires_admin(self, unauthed_client: TestClient) -> None:
        """Non-admin gets 401/403."""
        response = unauthed_client.get("/api/v1/admin/data/overview")
        assert response.status_code in (401, 403)


class TestListMetaSnapshots:
    """Tests for GET /api/v1/admin/data/meta-snapshots."""

    def _make_snapshot(
        self,
        region: str | None = "NA",
        fmt: str = "standard",
    ) -> MagicMock:
        snap = MagicMock()
        snap.id = uuid4()
        snap.snapshot_date = date(2026, 2, 1)
        snap.region = region
        snap.format = fmt
        snap.best_of = 3
        snap.sample_size = 500
        snap.archetype_shares = {
            "Charizard ex": 0.15,
            "Lugia VSTAR": 0.12,
        }
        snap.diversity_index = Decimal("0.8500")
        return snap

    def test_returns_paginated_list(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Verify paginated snapshot list."""
        snap = self._make_snapshot()

        # scalar for count
        mock_db.scalar = AsyncMock(return_value=1)

        # execute for query results
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [snap]
        mock_db.execute = AsyncMock(return_value=mock_result)

        response = client.get("/api/v1/admin/data/meta-snapshots")
        assert response.status_code == 200

        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        item = data["items"][0]
        assert item["archetype_count"] == 2
        assert item["diversity_index"] == 0.85

    def test_with_region_filter(self, client: TestClient, mock_db: AsyncMock) -> None:
        """Verify region filter is applied."""
        mock_db.scalar = AsyncMock(return_value=0)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        response = client.get(
            "/api/v1/admin/data/meta-snapshots?region=JP&format=standard"
        )
        assert response.status_code == 200
        assert response.json()["total"] == 0

    def test_requires_admin(self, unauthed_client: TestClient) -> None:
        response = unauthed_client.get("/api/v1/admin/data/meta-snapshots")
        assert response.status_code in (401, 403)


class TestGetMetaSnapshotDetail:
    """Tests for GET /api/v1/admin/data/meta-snapshots/{id}."""

    def test_returns_full_detail(self, client: TestClient, mock_db: AsyncMock) -> None:
        """Verify detail includes all JSON fields."""
        snap = MagicMock()
        snap.id = uuid4()
        snap.snapshot_date = date(2026, 2, 1)
        snap.region = "NA"
        snap.format = "standard"
        snap.best_of = 3
        snap.sample_size = 500
        snap.archetype_shares = {"Charizard ex": 0.15}
        snap.diversity_index = Decimal("0.9000")
        snap.tier_assignments = {"Charizard ex": "S"}
        snap.card_usage = {"sv4-6": {"rate": 0.85}}
        snap.jp_signals = {"rising": ["NewDeck"]}
        snap.trends = {"Charizard ex": {"change": 0.02}}
        snap.tournaments_included = ["tourney-1"]

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = snap
        mock_db.execute = AsyncMock(return_value=mock_result)

        response = client.get(f"/api/v1/admin/data/meta-snapshots/{snap.id}")
        assert response.status_code == 200

        data = response.json()
        assert data["archetype_shares"] == {"Charizard ex": 0.15}
        assert data["tier_assignments"] == {"Charizard ex": "S"}
        assert data["card_usage"] == {"sv4-6": {"rate": 0.85}}
        assert data["jp_signals"] == {"rising": ["NewDeck"]}
        assert data["trends"] == {"Charizard ex": {"change": 0.02}}
        assert data["tournaments_included"] == ["tourney-1"]

    def test_not_found(self, client: TestClient, mock_db: AsyncMock) -> None:
        """404 for missing snapshot."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        fake_id = uuid4()
        response = client.get(f"/api/v1/admin/data/meta-snapshots/{fake_id}")
        assert response.status_code == 404

    def test_requires_admin(self, unauthed_client: TestClient) -> None:
        fake_id = uuid4()
        response = unauthed_client.get(f"/api/v1/admin/data/meta-snapshots/{fake_id}")
        assert response.status_code in (401, 403)


class TestGetPipelineHealth:
    """Tests for GET /api/v1/admin/data/pipeline-health."""

    def test_returns_all_pipelines(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Verify pipeline and source health items are reported."""
        today = datetime.now(UTC).date()
        now_dt = datetime.now(UTC)
        mock_db.scalar = AsyncMock(
            side_effect=[
                today,  # meta snapshot_date (healthy)
                today,  # jp tournament date (healthy)
                now_dt,  # jp intel
                now_dt,  # card sync
                today,  # jp adoption period_end
                today,  # limitless date
                now_dt,  # rk9 updated_at
                now_dt,  # pokemon.com updated_at
                now_dt,  # pokecabook updated_at
                now_dt,  # pokekameshi updated_at
            ]
        )

        response = client.get("/api/v1/admin/data/pipeline-health")
        assert response.status_code == 200

        data = response.json()
        assert "pipelines" in data
        assert "checked_at" in data
        assert len(data["pipelines"]) == 10

        names = [p["name"] for p in data["pipelines"]]
        assert "Meta Compute" in names
        assert "JP Scrape" in names
        assert "JP Intelligence" in names
        assert "Card Sync" in names
        assert "JP Adoption Rate" in names
        assert "Limitless Source" in names
        assert "RK9 Source" in names
        assert "Pokemon Events Source" in names
        assert "Pokecabook Source" in names
        assert "Pokekameshi Source" in names

        # All should be healthy (today's dates)
        for pipeline in data["pipelines"]:
            assert pipeline["status"] == "healthy"
            assert pipeline["days_since_run"] == 0

    def test_stale_detection(self, client: TestClient, mock_db: AsyncMock) -> None:
        """Old dates produce stale/critical statuses."""
        today = datetime.now(UTC).date()
        from datetime import timedelta

        stale_date = today - timedelta(days=5)
        critical_date = today - timedelta(days=20)
        stale_dt = datetime(
            stale_date.year,
            stale_date.month,
            stale_date.day,
            tzinfo=UTC,
        )

        mock_db.scalar = AsyncMock(
            side_effect=[
                stale_date,  # meta: 5d > 2d threshold
                stale_date,  # jp scrape: 5d <= 7d
                stale_dt,  # jp intel: 5d <= 7d
                stale_dt,  # card sync: 5d <= 7d
                critical_date,  # adoption: 20d <= 30d
                stale_date,  # limitless source
                stale_dt,  # rk9 source
                stale_dt,  # pokemon events source
                stale_dt,  # pokecabook source
                stale_dt,  # pokekameshi source
            ]
        )

        response = client.get("/api/v1/admin/data/pipeline-health")
        assert response.status_code == 200

        data = response.json()
        pipelines_map = {p["name"]: p for p in data["pipelines"]}

        # Meta Compute: 5 days > 2 (healthy) → stale
        assert pipelines_map["Meta Compute"]["status"] == "stale"
        assert pipelines_map["Meta Compute"]["days_since_run"] == 5

        # JP Scrape: 5 days <= 7 (healthy threshold)
        assert pipelines_map["JP Scrape"]["status"] == "healthy"

        # JP Adoption Rate: 20 days <= 30 (stale)
        assert pipelines_map["JP Adoption Rate"]["status"] == "stale"

        # Source-level checks are also surfaced
        assert pipelines_map["Limitless Source"]["status"] == "stale"
        assert pipelines_map["RK9 Source"]["status"] == "healthy"
        assert pipelines_map["Pokemon Events Source"]["status"] == "healthy"

    def test_null_dates_critical(self, client: TestClient, mock_db: AsyncMock) -> None:
        """All null dates should produce critical status."""
        mock_db.scalar = AsyncMock(
            side_effect=[
                None,  # meta
                None,  # jp scrape
                None,  # jp intel
                None,  # card sync
                None,  # jp adoption
                None,  # limitless source
                None,  # rk9 source
                None,  # pokemon events source
                None,  # pokecabook source
                None,  # pokekameshi source
            ]
        )

        response = client.get("/api/v1/admin/data/pipeline-health")
        assert response.status_code == 200

        data = response.json()
        for pipeline in data["pipelines"]:
            assert pipeline["status"] == "critical"
            assert pipeline["last_run"] is None
            assert pipeline["days_since_run"] is None

    def test_requires_admin(self, unauthed_client: TestClient) -> None:
        response = unauthed_client.get("/api/v1/admin/data/pipeline-health")
        assert response.status_code in (401, 403)
