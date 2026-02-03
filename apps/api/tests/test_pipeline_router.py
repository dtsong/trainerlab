"""Tests for pipeline router endpoints."""

from datetime import date
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.config import Settings
from src.pipelines.compute_meta import ComputeMetaResult as ComputeMetaResultInternal
from src.pipelines.sync_cards import SyncResult
from src.routers.pipeline import router
from src.services.tournament_scrape import ScrapeResult as ScrapeResultInternal


@pytest.fixture
def bypass_settings() -> Settings:
    """Settings with auth bypass for testing."""
    return Settings(scheduler_auth_bypass=True)


@pytest.fixture
def app(bypass_settings: Settings) -> FastAPI:
    """Create test app with pipeline router."""
    app = FastAPI()
    app.include_router(router)

    # Override settings to bypass auth
    async def override_settings():
        return bypass_settings

    from src.config import get_settings

    app.dependency_overrides[get_settings] = override_settings

    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Create test client."""
    return TestClient(app)


class TestScrapeEnEndpoint:
    """Tests for /scrape-en endpoint."""

    def test_scrape_en_success(self, client: TestClient) -> None:
        """Should return scrape result on success."""
        mock_result = ScrapeResultInternal(
            tournaments_scraped=10,
            tournaments_saved=8,
            tournaments_skipped=2,
            placements_saved=256,
            decklists_saved=200,
            errors=[],
        )

        with patch(
            "src.routers.pipeline.scrape_en_tournaments", new_callable=AsyncMock
        ) as mock_scrape:
            mock_scrape.return_value = mock_result

            response = client.post(
                "/api/v1/pipeline/scrape-en",
                json={"dry_run": False, "lookback_days": 7},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["tournaments_scraped"] == 10
            assert data["tournaments_saved"] == 8
            assert data["tournaments_skipped"] == 2
            assert data["placements_saved"] == 256
            assert data["decklists_saved"] == 200
            assert data["success"] is True

    def test_scrape_en_with_errors(self, client: TestClient) -> None:
        """Should include errors in response."""
        mock_result = ScrapeResultInternal(
            tournaments_scraped=5,
            tournaments_saved=3,
            tournaments_skipped=0,
            placements_saved=96,
            decklists_saved=50,
            errors=["Error fetching tournament X", "Error parsing decklist Y"],
        )

        with patch(
            "src.routers.pipeline.scrape_en_tournaments", new_callable=AsyncMock
        ) as mock_scrape:
            mock_scrape.return_value = mock_result

            response = client.post(
                "/api/v1/pipeline/scrape-en",
                json={"dry_run": True},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert len(data["errors"]) == 2

    def test_scrape_en_validates_lookback_days(self, client: TestClient) -> None:
        """Should validate lookback_days range."""
        response = client.post(
            "/api/v1/pipeline/scrape-en",
            json={"lookback_days": 500},  # Max is 365
        )

        assert response.status_code == 422  # Validation error

    def test_scrape_en_validates_game_format(self, client: TestClient) -> None:
        """Should validate game_format pattern."""
        response = client.post(
            "/api/v1/pipeline/scrape-en",
            json={"game_format": "invalid"},
        )

        assert response.status_code == 422

    def test_scrape_en_uses_defaults(self, client: TestClient) -> None:
        """Should use default values when not provided."""
        mock_result = ScrapeResultInternal()

        with patch(
            "src.routers.pipeline.scrape_en_tournaments", new_callable=AsyncMock
        ) as mock_scrape:
            mock_scrape.return_value = mock_result

            response = client.post(
                "/api/v1/pipeline/scrape-en",
                json={},
            )

            assert response.status_code == 200
            mock_scrape.assert_called_once_with(
                dry_run=False,
                lookback_days=7,
                game_format="standard",
                max_placements=32,
                fetch_decklists=True,
            )


class TestScrapeJpEndpoint:
    """Tests for /scrape-jp endpoint."""

    def test_scrape_jp_success(self, client: TestClient) -> None:
        """Should return scrape result on success."""
        mock_result = ScrapeResultInternal(
            tournaments_scraped=5,
            tournaments_saved=4,
            tournaments_skipped=1,
            placements_saved=128,
            decklists_saved=100,
            errors=[],
        )

        with patch(
            "src.routers.pipeline.scrape_jp_tournaments", new_callable=AsyncMock
        ) as mock_scrape:
            mock_scrape.return_value = mock_result

            response = client.post(
                "/api/v1/pipeline/scrape-jp",
                json={"dry_run": False, "lookback_days": 14},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["tournaments_scraped"] == 5
            assert data["success"] is True

    def test_scrape_jp_expanded_format(self, client: TestClient) -> None:
        """Should accept expanded format."""
        mock_result = ScrapeResultInternal()

        with patch(
            "src.routers.pipeline.scrape_jp_tournaments", new_callable=AsyncMock
        ) as mock_scrape:
            mock_scrape.return_value = mock_result

            response = client.post(
                "/api/v1/pipeline/scrape-jp",
                json={"game_format": "expanded"},
            )

            assert response.status_code == 200
            mock_scrape.assert_called_once()
            call_kwargs = mock_scrape.call_args.kwargs
            assert call_kwargs["game_format"] == "expanded"


class TestComputeMetaEndpoint:
    """Tests for /compute-meta endpoint."""

    def test_compute_meta_success(self, client: TestClient) -> None:
        """Should return compute result on success."""
        mock_result = ComputeMetaResultInternal(
            snapshots_computed=12,
            snapshots_saved=10,
            snapshots_skipped=2,
            errors=[],
        )

        with patch(
            "src.routers.pipeline.compute_daily_snapshots", new_callable=AsyncMock
        ) as mock_compute:
            mock_compute.return_value = mock_result

            response = client.post(
                "/api/v1/pipeline/compute-meta",
                json={"dry_run": False},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["snapshots_computed"] == 12
            assert data["snapshots_saved"] == 10
            assert data["snapshots_skipped"] == 2
            assert data["success"] is True

    def test_compute_meta_with_date(self, client: TestClient) -> None:
        """Should pass snapshot_date to pipeline."""
        mock_result = ComputeMetaResultInternal()

        with patch(
            "src.routers.pipeline.compute_daily_snapshots", new_callable=AsyncMock
        ) as mock_compute:
            mock_compute.return_value = mock_result

            response = client.post(
                "/api/v1/pipeline/compute-meta",
                json={"snapshot_date": "2024-01-15"},
            )

            assert response.status_code == 200
            mock_compute.assert_called_once()
            call_kwargs = mock_compute.call_args.kwargs
            assert call_kwargs["snapshot_date"] == date(2024, 1, 15)

    def test_compute_meta_dry_run(self, client: TestClient) -> None:
        """Should pass dry_run flag to pipeline."""
        mock_result = ComputeMetaResultInternal(
            snapshots_computed=12,
            snapshots_saved=0,
            snapshots_skipped=12,
        )

        with patch(
            "src.routers.pipeline.compute_daily_snapshots", new_callable=AsyncMock
        ) as mock_compute:
            mock_compute.return_value = mock_result

            response = client.post(
                "/api/v1/pipeline/compute-meta",
                json={"dry_run": True},
            )

            assert response.status_code == 200
            mock_compute.assert_called_once_with(
                snapshot_date=None,
                dry_run=True,
                lookback_days=90,
            )

    def test_compute_meta_validates_lookback(self, client: TestClient) -> None:
        """Should validate lookback_days range (7-365)."""
        response = client.post(
            "/api/v1/pipeline/compute-meta",
            json={"lookback_days": 5},  # Min is 7
        )

        assert response.status_code == 422


class TestSyncCardsEndpoint:
    """Tests for /sync-cards endpoint."""

    def test_sync_cards_success(self, client: TestClient) -> None:
        """Should return sync result on success."""
        mock_result = SyncResult(
            sets_processed=15,
            cards_processed=2500,
            cards_updated=100,
            errors=[],
        )

        with patch(
            "src.routers.pipeline.sync_english_cards", new_callable=AsyncMock
        ) as mock_sync:
            mock_sync.return_value = mock_result

            response = client.post(
                "/api/v1/pipeline/sync-cards",
                json={"dry_run": False},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["sets_synced"] == 15
            assert data["cards_synced"] == 2500
            assert data["cards_updated"] == 100
            assert data["success"] is True

    def test_sync_cards_with_errors(self, client: TestClient) -> None:
        """Should include errors in response."""
        mock_result = SyncResult(
            sets_processed=10,
            cards_processed=1000,
            cards_updated=0,
            errors=["Failed to fetch set XY"],
        )

        with patch(
            "src.routers.pipeline.sync_english_cards", new_callable=AsyncMock
        ) as mock_sync:
            mock_sync.return_value = mock_result

            response = client.post(
                "/api/v1/pipeline/sync-cards",
                json={},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert len(data["errors"]) == 1

    def test_sync_cards_dry_run(self, client: TestClient) -> None:
        """Should pass dry_run flag to pipeline."""
        mock_result = SyncResult()

        with patch(
            "src.routers.pipeline.sync_english_cards", new_callable=AsyncMock
        ) as mock_sync:
            mock_sync.return_value = mock_result

            response = client.post(
                "/api/v1/pipeline/sync-cards",
                json={"dry_run": True},
            )

            assert response.status_code == 200
            mock_sync.assert_called_once_with(dry_run=True)


class TestExceptionHandling:
    """Tests for exception handling in pipeline endpoints."""

    @pytest.fixture
    def error_client(self, app: FastAPI) -> TestClient:
        """Client that doesn't raise server exceptions."""
        return TestClient(app, raise_server_exceptions=False)

    def test_scrape_en_handles_pipeline_exception(
        self, error_client: TestClient
    ) -> None:
        """Should return 500 when pipeline raises unhandled exception."""
        with patch(
            "src.routers.pipeline.scrape_en_tournaments", new_callable=AsyncMock
        ) as mock_scrape:
            mock_scrape.side_effect = RuntimeError("Database connection lost")

            response = error_client.post(
                "/api/v1/pipeline/scrape-en",
                json={},
            )

            assert response.status_code == 500

    def test_scrape_jp_handles_pipeline_exception(
        self, error_client: TestClient
    ) -> None:
        """Should return 500 when JP pipeline raises unhandled exception."""
        with patch(
            "src.routers.pipeline.scrape_jp_tournaments", new_callable=AsyncMock
        ) as mock_scrape:
            mock_scrape.side_effect = RuntimeError("Network timeout")

            response = error_client.post(
                "/api/v1/pipeline/scrape-jp",
                json={},
            )

            assert response.status_code == 500

    def test_compute_meta_handles_pipeline_exception(
        self, error_client: TestClient
    ) -> None:
        """Should return 500 when compute meta raises unhandled exception."""
        with patch(
            "src.routers.pipeline.compute_daily_snapshots", new_callable=AsyncMock
        ) as mock_compute:
            mock_compute.side_effect = RuntimeError("Computation failed")

            response = error_client.post(
                "/api/v1/pipeline/compute-meta",
                json={},
            )

            assert response.status_code == 500

    def test_sync_cards_handles_pipeline_exception(
        self, error_client: TestClient
    ) -> None:
        """Should return 500 when sync cards raises unhandled exception."""
        with patch(
            "src.routers.pipeline.sync_english_cards", new_callable=AsyncMock
        ) as mock_sync:
            mock_sync.side_effect = RuntimeError("API unavailable")

            response = error_client.post(
                "/api/v1/pipeline/sync-cards",
                json={},
            )

            assert response.status_code == 500


class TestAuthenticationIntegration:
    """Tests for authentication on pipeline endpoints."""

    @pytest.fixture
    def production_app(self) -> FastAPI:
        """Create app without auth bypass."""
        app = FastAPI()
        app.include_router(router)

        # Use production settings (no bypass)
        prod_settings = Settings(
            scheduler_auth_bypass=False,
            cloud_run_url="https://api.example.com",
        )

        async def override_settings():
            return prod_settings

        from src.config import get_settings

        app.dependency_overrides[get_settings] = override_settings

        return app

    @pytest.fixture
    def production_client(self, production_app: FastAPI) -> TestClient:
        """Client for production app."""
        return TestClient(production_app)

    def test_requires_auth_in_production(self, production_client: TestClient) -> None:
        """Should require auth header in production mode."""
        response = production_client.post(
            "/api/v1/pipeline/scrape-en",
            json={},
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Authorization header required"

    def test_rejects_invalid_token_format(self, production_client: TestClient) -> None:
        """Should reject non-Bearer auth."""
        response = production_client.post(
            "/api/v1/pipeline/scrape-en",
            json={},
            headers={"Authorization": "Basic dXNlcjpwYXNz"},
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid authorization header format"
