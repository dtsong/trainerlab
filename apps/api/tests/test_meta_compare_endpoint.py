"""Tests for meta comparison and forecast endpoints."""

from datetime import date
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.dependencies.beta import require_beta
from src.main import app
from src.schemas.meta import (
    ArchetypeComparison,
    ConfidenceIndicator,
    FormatForecastEntry,
    FormatForecastResponse,
    MetaComparisonResponse,
)


class TestCompareEndpoint:
    """Tests for GET /api/v1/meta/compare."""

    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def client(self, mock_db: AsyncMock) -> TestClient:
        from src.db.database import get_db

        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[require_beta] = lambda: None
        yield TestClient(app)
        app.dependency_overrides.clear()

    def _make_comparison_response(self) -> MetaComparisonResponse:
        return MetaComparisonResponse(
            region_a="JP",
            region_b="Global",
            region_a_snapshot_date=date(2026, 2, 5),
            region_b_snapshot_date=date(2026, 2, 5),
            comparisons=[
                ArchetypeComparison(
                    archetype="Charizard ex",
                    region_a_share=0.20,
                    region_b_share=0.15,
                    divergence=0.05,
                    region_a_tier="S",
                    region_b_tier="A",
                    sprite_urls=[],
                ),
            ],
            region_a_confidence=ConfidenceIndicator(
                sample_size=200,
                data_freshness_days=1,
                confidence="high",
            ),
            region_b_confidence=ConfidenceIndicator(
                sample_size=500,
                data_freshness_days=1,
                confidence="high",
            ),
            lag_analysis=None,
        )

    @patch("src.routers.meta.MetaService")
    def test_compare_success(self, mock_svc_cls, client):
        mock_svc = AsyncMock()
        mock_svc.compute_meta_comparison.return_value = self._make_comparison_response()
        mock_svc_cls.return_value = mock_svc

        response = client.get("/api/v1/meta/compare?region_a=JP")

        assert response.status_code == 200
        data = response.json()
        assert data["region_a"] == "JP"
        assert data["region_b"] == "Global"
        assert len(data["comparisons"]) == 1
        assert data["comparisons"][0]["archetype"] == "Charizard ex"
        assert data["region_a_confidence"]["confidence"] == "high"

    @patch("src.routers.meta.MetaService")
    def test_compare_with_lag_days(self, mock_svc_cls, client):
        mock_svc = AsyncMock()
        mock_svc.compute_meta_comparison.return_value = self._make_comparison_response()
        mock_svc_cls.return_value = mock_svc

        response = client.get("/api/v1/meta/compare?region_a=JP&lag_days=14")

        assert response.status_code == 200
        mock_svc.compute_meta_comparison.assert_called_once_with(
            region_a="JP",
            region_b=None,
            game_format="standard",
            lag_days=14,
            top_n=15,
        )

    @patch("src.routers.meta.MetaService")
    def test_compare_missing_data_404(self, mock_svc_cls, client):
        mock_svc = AsyncMock()
        mock_svc.compute_meta_comparison.side_effect = ValueError(
            "No snapshot data for: JP"
        )
        mock_svc_cls.return_value = mock_svc

        response = client.get("/api/v1/meta/compare?region_a=JP")

        assert response.status_code == 404

    def test_compare_invalid_lag_days(self, client):
        response = client.get("/api/v1/meta/compare?lag_days=100")
        assert response.status_code == 422

    def test_compare_invalid_top_n(self, client):
        response = client.get("/api/v1/meta/compare?top_n=0")
        assert response.status_code == 422

    def test_compare_negative_lag_days(self, client):
        response = client.get("/api/v1/meta/compare?lag_days=-1")
        assert response.status_code == 422

    @patch("src.routers.meta.MetaService")
    def test_compare_format_forwarded(self, mock_svc_cls, client):
        mock_svc = AsyncMock()
        mock_svc.compute_meta_comparison.return_value = self._make_comparison_response()
        mock_svc_cls.return_value = mock_svc

        response = client.get("/api/v1/meta/compare?format=expanded&top_n=5")

        assert response.status_code == 200
        mock_svc.compute_meta_comparison.assert_called_once_with(
            region_a="JP",
            region_b=None,
            game_format="expanded",
            lag_days=0,
            top_n=5,
        )

    @patch("src.routers.meta.MetaService")
    def test_compare_dates_are_iso8601(self, mock_svc_cls, client):
        mock_svc = AsyncMock()
        mock_svc.compute_meta_comparison.return_value = self._make_comparison_response()
        mock_svc_cls.return_value = mock_svc

        response = client.get("/api/v1/meta/compare?region_a=JP")

        assert response.status_code == 200
        data = response.json()
        # ISO 8601 date format YYYY-MM-DD
        assert len(data["region_a_snapshot_date"]) == 10
        assert data["region_a_snapshot_date"][4] == "-"
        assert data["region_b_snapshot_date"][4] == "-"


class TestForecastEndpoint:
    """Tests for GET /api/v1/meta/forecast."""

    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def client(self, mock_db: AsyncMock) -> TestClient:
        from src.db.database import get_db

        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[require_beta] = lambda: None
        yield TestClient(app)
        app.dependency_overrides.clear()

    def _make_forecast_response(self) -> FormatForecastResponse:
        return FormatForecastResponse(
            forecast_archetypes=[
                FormatForecastEntry(
                    archetype="Raging Bolt ex",
                    jp_share=0.15,
                    en_share=0.08,
                    divergence=0.07,
                    tier="A",
                    trend_direction="up",
                    sprite_urls=[],
                    confidence="high",
                ),
            ],
            jp_snapshot_date=date(2026, 2, 5),
            en_snapshot_date=date(2026, 2, 5),
            jp_sample_size=200,
            en_sample_size=500,
        )

    @patch("src.routers.meta.MetaService")
    def test_forecast_success(self, mock_svc_cls, client):
        mock_svc = AsyncMock()
        mock_svc.compute_format_forecast.return_value = self._make_forecast_response()
        mock_svc_cls.return_value = mock_svc

        response = client.get("/api/v1/meta/forecast")

        assert response.status_code == 200
        data = response.json()
        assert len(data["forecast_archetypes"]) == 1
        assert data["forecast_archetypes"][0]["archetype"] == "Raging Bolt ex"
        assert data["jp_sample_size"] == 200

    @patch("src.routers.meta.MetaService")
    def test_forecast_custom_params(self, mock_svc_cls, client):
        mock_svc = AsyncMock()
        mock_svc.compute_format_forecast.return_value = self._make_forecast_response()
        mock_svc_cls.return_value = mock_svc

        response = client.get("/api/v1/meta/forecast?format=expanded&top_n=3")

        assert response.status_code == 200
        mock_svc.compute_format_forecast.assert_called_once_with(
            game_format="expanded",
            top_n=3,
        )

    @patch("src.routers.meta.MetaService")
    def test_forecast_missing_data_404(self, mock_svc_cls, client):
        mock_svc = AsyncMock()
        mock_svc.compute_format_forecast.side_effect = ValueError(
            "No snapshot data for: JP"
        )
        mock_svc_cls.return_value = mock_svc

        response = client.get("/api/v1/meta/forecast")

        assert response.status_code == 404

    def test_forecast_invalid_top_n(self, client):
        response = client.get("/api/v1/meta/forecast?top_n=20")
        assert response.status_code == 422

    def test_forecast_top_n_zero_invalid(self, client):
        response = client.get("/api/v1/meta/forecast?top_n=0")
        assert response.status_code == 422

    @patch("src.routers.meta.MetaService")
    def test_forecast_dates_are_iso8601(self, mock_svc_cls, client):
        mock_svc = AsyncMock()
        mock_svc.compute_format_forecast.return_value = self._make_forecast_response()
        mock_svc_cls.return_value = mock_svc

        response = client.get("/api/v1/meta/forecast")

        assert response.status_code == 200
        data = response.json()
        assert len(data["jp_snapshot_date"]) == 10
        assert data["jp_snapshot_date"][4] == "-"
        assert data["en_snapshot_date"][4] == "-"
