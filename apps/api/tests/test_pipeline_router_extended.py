"""Tests for remaining pipeline router endpoints (sync-card-mappings, compute-evolution,
translate-pokecabook, sync-jp-adoption, translate-tier-lists, monitor-card-reveals,
cleanup-exports)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.config import Settings
from src.pipelines.compute_evolution import (
    ComputeEvolutionResult as ComputeEvolutionResultInternal,
)
from src.pipelines.monitor_card_reveals import (
    MonitorCardRevealsResult as MonitorCardRevealsResultInternal,
)
from src.pipelines.sync_card_mappings import (
    SyncMappingsResult as SyncMappingsResultInternal,
)
from src.pipelines.sync_jp_adoption_rates import (
    SyncAdoptionRatesResult as SyncAdoptionRatesResultInternal,
)
from src.pipelines.translate_pokecabook import (
    TranslatePokecabookResult as TranslatePokecabookResultInternal,
)
from src.pipelines.translate_tier_lists import (
    TranslateTierListsResult as TranslateTierListsResultInternal,
)
from src.routers.pipeline import router


@pytest.fixture
def bypass_settings() -> Settings:
    """Settings with auth bypass for testing."""
    return Settings(scheduler_auth_bypass=True)


@pytest.fixture
def app(bypass_settings: Settings) -> FastAPI:
    """Create test app with pipeline router."""
    app = FastAPI()
    app.include_router(router)

    async def override_settings():
        return bypass_settings

    from src.config import get_settings

    app.dependency_overrides[get_settings] = override_settings
    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def error_client(app: FastAPI) -> TestClient:
    """Client that doesn't raise server exceptions."""
    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# /sync-card-mappings
# ---------------------------------------------------------------------------


class TestSyncCardMappingsEndpoint:
    """Tests for /sync-card-mappings endpoint."""

    def test_sync_card_mappings_recent_only(self, client: TestClient) -> None:
        """Should call sync_recent_jp_sets when recent_only=True."""
        mock_result = SyncMappingsResultInternal(
            sets_processed=5,
            mappings_found=200,
            mappings_inserted=50,
            mappings_updated=10,
            adoption_rows_backfilled=7,
            errors=[],
        )

        with patch(
            "src.routers.pipeline.sync_recent_jp_sets", new_callable=AsyncMock
        ) as mock_sync:
            mock_sync.return_value = mock_result

            response = client.post(
                "/api/v1/pipeline/sync-card-mappings",
                json={"recent_only": True, "lookback_sets": 3},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["sets_processed"] == 5
            assert data["mappings_found"] == 200
            assert data["mappings_inserted"] == 50
            assert data["mappings_updated"] == 10
            assert data["adoption_rows_backfilled"] == 7
            assert data["success"] is True
            mock_sync.assert_called_once_with(lookback_sets=3, dry_run=False)

    def test_sync_card_mappings_all(self, client: TestClient) -> None:
        """Should call sync_all_card_mappings when recent_only=False."""
        mock_result = SyncMappingsResultInternal(
            sets_processed=20,
            mappings_found=1000,
            mappings_inserted=100,
            mappings_updated=50,
            errors=[],
        )

        with patch(
            "src.routers.pipeline.sync_all_card_mappings", new_callable=AsyncMock
        ) as mock_sync:
            mock_sync.return_value = mock_result

            response = client.post(
                "/api/v1/pipeline/sync-card-mappings",
                json={"recent_only": False},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["sets_processed"] == 20
            assert data["success"] is True
            mock_sync.assert_called_once_with(dry_run=False)

    def test_sync_card_mappings_with_errors(self, client: TestClient) -> None:
        """Should include errors in response."""
        mock_result = SyncMappingsResultInternal(
            sets_processed=3,
            mappings_found=50,
            mappings_inserted=0,
            mappings_updated=0,
            errors=["Failed to fetch set SV7"],
        )

        with patch(
            "src.routers.pipeline.sync_recent_jp_sets", new_callable=AsyncMock
        ) as mock_sync:
            mock_sync.return_value = mock_result

            response = client.post(
                "/api/v1/pipeline/sync-card-mappings",
                json={},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert len(data["errors"]) == 1

    def test_sync_card_mappings_defaults(self, client: TestClient) -> None:
        """Should use default values when not provided."""
        mock_result = SyncMappingsResultInternal()

        with patch(
            "src.routers.pipeline.sync_recent_jp_sets", new_callable=AsyncMock
        ) as mock_sync:
            mock_sync.return_value = mock_result

            response = client.post(
                "/api/v1/pipeline/sync-card-mappings",
                json={},
            )

            assert response.status_code == 200
            # Default: recent_only=True, lookback_sets=5, dry_run=False
            mock_sync.assert_called_once_with(lookback_sets=5, dry_run=False)


# ---------------------------------------------------------------------------
# /compute-evolution
# ---------------------------------------------------------------------------


class TestComputeEvolutionEndpoint:
    """Tests for /compute-evolution endpoint."""

    def test_compute_evolution_success(self, client: TestClient) -> None:
        """Should return evolution result on success."""
        mock_result = ComputeEvolutionResultInternal(
            adaptations_classified=10,
            contexts_generated=5,
            predictions_generated=8,
            articles_generated=3,
            errors=[],
        )

        with patch(
            "src.routers.pipeline.compute_evolution_intelligence",
            new_callable=AsyncMock,
        ) as mock_compute:
            mock_compute.return_value = mock_result

            response = client.post(
                "/api/v1/pipeline/compute-evolution",
                json={"dry_run": False},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["adaptations_classified"] == 10
            assert data["contexts_generated"] == 5
            assert data["predictions_generated"] == 8
            assert data["articles_generated"] == 3
            assert data["success"] is True

    def test_compute_evolution_dry_run(self, client: TestClient) -> None:
        """Should pass dry_run flag to pipeline."""
        mock_result = ComputeEvolutionResultInternal()

        with patch(
            "src.routers.pipeline.compute_evolution_intelligence",
            new_callable=AsyncMock,
        ) as mock_compute:
            mock_compute.return_value = mock_result

            response = client.post(
                "/api/v1/pipeline/compute-evolution",
                json={"dry_run": True},
            )

            assert response.status_code == 200
            mock_compute.assert_called_once_with(dry_run=True)

    def test_compute_evolution_with_errors(self, client: TestClient) -> None:
        """Should include errors in response."""
        mock_result = ComputeEvolutionResultInternal(
            adaptations_classified=2,
            errors=["Claude API error: rate limited"],
        )

        with patch(
            "src.routers.pipeline.compute_evolution_intelligence",
            new_callable=AsyncMock,
        ) as mock_compute:
            mock_compute.return_value = mock_result

            response = client.post(
                "/api/v1/pipeline/compute-evolution",
                json={},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert len(data["errors"]) == 1

    def test_compute_evolution_handles_exception(
        self, error_client: TestClient
    ) -> None:
        """Should return 500 when pipeline raises unhandled exception."""
        with patch(
            "src.routers.pipeline.compute_evolution_intelligence",
            new_callable=AsyncMock,
        ) as mock_compute:
            mock_compute.side_effect = RuntimeError("Claude API down")

            response = error_client.post(
                "/api/v1/pipeline/compute-evolution",
                json={},
            )

            assert response.status_code == 500


# ---------------------------------------------------------------------------
# /translate-pokecabook
# ---------------------------------------------------------------------------


class TestTranslatePokecabookEndpoint:
    """Tests for /translate-pokecabook endpoint."""

    def test_translate_pokecabook_success(self, client: TestClient) -> None:
        """Should return translation result on success."""
        mock_result = TranslatePokecabookResultInternal(
            articles_fetched=10,
            articles_translated=8,
            articles_skipped=2,
            tier_lists_translated=3,
            errors=[],
        )

        with patch(
            "src.routers.pipeline.translate_pokecabook_content",
            new_callable=AsyncMock,
        ) as mock_translate:
            mock_translate.return_value = mock_result

            response = client.post(
                "/api/v1/pipeline/translate-pokecabook",
                json={"lookback_days": 14},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["articles_fetched"] == 10
            assert data["articles_translated"] == 8
            assert data["articles_skipped"] == 2
            assert data["tier_lists_translated"] == 3
            assert data["success"] is True

    def test_translate_pokecabook_dry_run(self, client: TestClient) -> None:
        """Should pass dry_run and lookback_days to pipeline."""
        mock_result = TranslatePokecabookResultInternal()

        with patch(
            "src.routers.pipeline.translate_pokecabook_content",
            new_callable=AsyncMock,
        ) as mock_translate:
            mock_translate.return_value = mock_result

            response = client.post(
                "/api/v1/pipeline/translate-pokecabook",
                json={"dry_run": True, "lookback_days": 3},
            )

            assert response.status_code == 200
            mock_translate.assert_called_once_with(lookback_days=3, dry_run=True)

    def test_translate_pokecabook_with_errors(self, client: TestClient) -> None:
        """Should include errors in response."""
        mock_result = TranslatePokecabookResultInternal(
            articles_fetched=5,
            errors=["Translation failed for article X"],
        )

        with patch(
            "src.routers.pipeline.translate_pokecabook_content",
            new_callable=AsyncMock,
        ) as mock_translate:
            mock_translate.return_value = mock_result

            response = client.post(
                "/api/v1/pipeline/translate-pokecabook",
                json={},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False

    def test_translate_pokecabook_validates_lookback(self, client: TestClient) -> None:
        """Should validate lookback_days range (1-90)."""
        response = client.post(
            "/api/v1/pipeline/translate-pokecabook",
            json={"lookback_days": 100},  # Max is 90
        )

        assert response.status_code == 422


# ---------------------------------------------------------------------------
# /sync-jp-adoption
# ---------------------------------------------------------------------------


class TestSyncJPAdoptionEndpoint:
    """Tests for /sync-jp-adoption endpoint."""

    def test_sync_jp_adoption_success(self, client: TestClient) -> None:
        """Should return sync result on success."""
        mock_result = SyncAdoptionRatesResultInternal(
            rates_fetched=100,
            rates_created=80,
            rates_updated=15,
            rates_skipped=5,
            rates_backfilled=12,
            mapping_resolved=90,
            mapping_unresolved=10,
            mapping_coverage=0.9,
            mapped_by_method={"card_name_en": 85, "generated_hash": 10},
            unmapped_by_source={"https://pokecabook.com/adoption/": 10},
            unmapped_by_set={"unknown": 10},
            unmapped_card_samples=["未知カード"],
            errors=[],
        )

        with patch(
            "src.routers.pipeline.sync_adoption_rates", new_callable=AsyncMock
        ) as mock_sync:
            mock_sync.return_value = mock_result

            response = client.post(
                "/api/v1/pipeline/sync-jp-adoption",
                json={"dry_run": False},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["rates_fetched"] == 100
            assert data["rates_created"] == 80
            assert data["rates_updated"] == 15
            assert data["rates_skipped"] == 5
            assert data["rates_backfilled"] == 12
            assert data["mapping_coverage"] == 0.9
            assert data["mapping_resolved"] == 90
            assert data["mapping_unresolved"] == 10
            assert data["mapped_by_method"]["card_name_en"] == 85
            assert data["success"] is True

    def test_sync_jp_adoption_dry_run(self, client: TestClient) -> None:
        """Should pass dry_run flag to pipeline."""
        mock_result = SyncAdoptionRatesResultInternal()

        with patch(
            "src.routers.pipeline.sync_adoption_rates", new_callable=AsyncMock
        ) as mock_sync:
            mock_sync.return_value = mock_result

            response = client.post(
                "/api/v1/pipeline/sync-jp-adoption",
                json={"dry_run": True},
            )

            assert response.status_code == 200
            mock_sync.assert_called_once_with(dry_run=True)

    def test_sync_jp_adoption_with_errors(self, client: TestClient) -> None:
        """Should include errors in response."""
        mock_result = SyncAdoptionRatesResultInternal(
            errors=["Pokecabook API unreachable"],
        )

        with patch(
            "src.routers.pipeline.sync_adoption_rates", new_callable=AsyncMock
        ) as mock_sync:
            mock_sync.return_value = mock_result

            response = client.post(
                "/api/v1/pipeline/sync-jp-adoption",
                json={},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert len(data["errors"]) == 1


# ---------------------------------------------------------------------------
# /translate-tier-lists
# ---------------------------------------------------------------------------


class TestTranslateTierListsEndpoint:
    """Tests for /translate-tier-lists endpoint."""

    def test_translate_tier_lists_success(self, client: TestClient) -> None:
        """Should return translation result on success."""
        mock_result = TranslateTierListsResultInternal(
            pokecabook_entries=10,
            pokekameshi_entries=8,
            translations_saved=18,
            errors=[],
        )

        with patch(
            "src.routers.pipeline.translate_tier_lists", new_callable=AsyncMock
        ) as mock_translate:
            mock_translate.return_value = mock_result

            response = client.post(
                "/api/v1/pipeline/translate-tier-lists",
                json={"dry_run": False},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["pokecabook_entries"] == 10
            assert data["pokekameshi_entries"] == 8
            assert data["translations_saved"] == 18
            assert data["success"] is True

    def test_translate_tier_lists_dry_run(self, client: TestClient) -> None:
        """Should pass dry_run flag to pipeline."""
        mock_result = TranslateTierListsResultInternal()

        with patch(
            "src.routers.pipeline.translate_tier_lists", new_callable=AsyncMock
        ) as mock_translate:
            mock_translate.return_value = mock_result

            response = client.post(
                "/api/v1/pipeline/translate-tier-lists",
                json={"dry_run": True},
            )

            assert response.status_code == 200
            mock_translate.assert_called_once_with(dry_run=True)

    def test_translate_tier_lists_with_errors(self, client: TestClient) -> None:
        """Should include errors in response."""
        mock_result = TranslateTierListsResultInternal(
            errors=["Pokekameshi scrape failed"],
        )

        with patch(
            "src.routers.pipeline.translate_tier_lists", new_callable=AsyncMock
        ) as mock_translate:
            mock_translate.return_value = mock_result

            response = client.post(
                "/api/v1/pipeline/translate-tier-lists",
                json={},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False


# ---------------------------------------------------------------------------
# /monitor-card-reveals
# ---------------------------------------------------------------------------


class TestMonitorCardRevealsEndpoint:
    """Tests for /monitor-card-reveals endpoint."""

    def test_monitor_card_reveals_success(self, client: TestClient) -> None:
        """Should return monitor result on success."""
        mock_result = MonitorCardRevealsResultInternal(
            cards_checked=50,
            new_cards_found=3,
            cards_updated=2,
            cards_marked_released=1,
            errors=[],
        )

        with patch(
            "src.routers.pipeline.check_card_reveals", new_callable=AsyncMock
        ) as mock_check:
            mock_check.return_value = mock_result

            response = client.post(
                "/api/v1/pipeline/monitor-card-reveals",
                json={"dry_run": False},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["cards_checked"] == 50
            assert data["new_cards_found"] == 3
            assert data["cards_updated"] == 2
            assert data["cards_marked_released"] == 1
            assert data["success"] is True

    def test_monitor_card_reveals_dry_run(self, client: TestClient) -> None:
        """Should pass dry_run flag to pipeline."""
        mock_result = MonitorCardRevealsResultInternal()

        with patch(
            "src.routers.pipeline.check_card_reveals", new_callable=AsyncMock
        ) as mock_check:
            mock_check.return_value = mock_result

            response = client.post(
                "/api/v1/pipeline/monitor-card-reveals",
                json={"dry_run": True},
            )

            assert response.status_code == 200
            mock_check.assert_called_once_with(dry_run=True)

    def test_monitor_card_reveals_with_errors(self, client: TestClient) -> None:
        """Should include errors in response."""
        mock_result = MonitorCardRevealsResultInternal(
            cards_checked=20,
            errors=["Limitless API unreachable"],
        )

        with patch(
            "src.routers.pipeline.check_card_reveals", new_callable=AsyncMock
        ) as mock_check:
            mock_check.return_value = mock_result

            response = client.post(
                "/api/v1/pipeline/monitor-card-reveals",
                json={},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert len(data["errors"]) == 1


# ---------------------------------------------------------------------------
# /cleanup-exports
# ---------------------------------------------------------------------------


class TestCleanupExportsEndpoint:
    """Tests for /cleanup-exports endpoint."""

    def test_cleanup_exports_success(self, client: TestClient) -> None:
        """Should return cleanup result on success."""
        with patch("src.routers.pipeline.StorageService") as mock_storage_cls:
            mock_storage = MagicMock()
            mock_storage.cleanup_expired_exports = AsyncMock(return_value=5)
            mock_storage_cls.return_value = mock_storage

            response = client.post(
                "/api/v1/pipeline/cleanup-exports",
                json={"max_age_hours": 48, "dry_run": False},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["files_deleted"] == 5
            assert data["success"] is True
            assert data["errors"] == []
            mock_storage.cleanup_expired_exports.assert_called_once_with(
                max_age_hours=48
            )

    def test_cleanup_exports_dry_run(self, client: TestClient) -> None:
        """Should skip cleanup on dry run."""
        with patch("src.routers.pipeline.StorageService") as mock_storage_cls:
            mock_storage = MagicMock()
            mock_storage_cls.return_value = mock_storage

            response = client.post(
                "/api/v1/pipeline/cleanup-exports",
                json={"dry_run": True},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["files_deleted"] == 0
            assert data["success"] is True
            # cleanup_expired_exports should NOT be called in dry_run
            mock_storage.cleanup_expired_exports.assert_not_called()

    def test_cleanup_exports_default_max_age(self, client: TestClient) -> None:
        """Should use default max_age_hours when not provided."""
        with patch("src.routers.pipeline.StorageService") as mock_storage_cls:
            mock_storage = MagicMock()
            mock_storage.cleanup_expired_exports = AsyncMock(return_value=0)
            mock_storage_cls.return_value = mock_storage

            response = client.post(
                "/api/v1/pipeline/cleanup-exports",
                json={},
            )

            assert response.status_code == 200
            mock_storage.cleanup_expired_exports.assert_called_once_with(
                max_age_hours=24  # default
            )

    def test_cleanup_exports_gcs_error(self, client: TestClient) -> None:
        """Should return structured error on GCS failure."""
        with patch("src.routers.pipeline.StorageService") as mock_storage_cls:
            mock_storage = MagicMock()
            mock_storage.cleanup_expired_exports = AsyncMock(
                side_effect=Exception("bucket not found")
            )
            mock_storage_cls.return_value = mock_storage

            response = client.post(
                "/api/v1/pipeline/cleanup-exports",
                json={"max_age_hours": 48, "dry_run": False},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert data["files_deleted"] == 0
            assert len(data["errors"]) == 1
            assert "failed" in data["errors"][0].lower()

    def test_cleanup_exports_validates_max_age(self, client: TestClient) -> None:
        """Should validate max_age_hours range (1-168)."""
        response = client.post(
            "/api/v1/pipeline/cleanup-exports",
            json={"max_age_hours": 200},  # Max is 168
        )

        assert response.status_code == 422
