"""Tests for health check router endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.routers.health import router


@pytest.fixture
def app() -> FastAPI:
    """Create test app with health router."""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Create test client."""
    return TestClient(app)


class TestBasicHealthCheck:
    """Tests for GET /api/v1/health."""

    def test_health_check_returns_ok(self, client: TestClient) -> None:
        """Should return status ok and version."""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "0.0.1"


class TestDbHealthCheck:
    """Tests for GET /api/v1/health/db."""

    def test_all_healthy(self, client: TestClient) -> None:
        """Should return ok when both database and redis are healthy."""
        with (
            patch(
                "src.routers.health.check_database_health",
                new_callable=AsyncMock,
            ) as mock_db,
            patch(
                "src.routers.health.check_redis_health",
                new_callable=AsyncMock,
            ) as mock_redis,
        ):
            mock_db.return_value = {"status": "ok", "latency_ms": 1.5}
            mock_redis.return_value = {"status": "ok", "latency_ms": 0.8}

            response = client.get("/api/v1/health/db")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert data["database"]["status"] == "ok"
            assert data["redis"]["status"] == "ok"

    def test_database_unhealthy(self, client: TestClient) -> None:
        """Should return 503 and degraded when database is down."""
        with (
            patch(
                "src.routers.health.check_database_health",
                new_callable=AsyncMock,
            ) as mock_db,
            patch(
                "src.routers.health.check_redis_health",
                new_callable=AsyncMock,
            ) as mock_redis,
        ):
            mock_db.return_value = {"status": "error", "error": "Connection refused"}
            mock_redis.return_value = {"status": "ok", "latency_ms": 0.8}

            response = client.get("/api/v1/health/db")

            assert response.status_code == 503
            data = response.json()
            assert data["status"] == "degraded"
            assert data["database"]["status"] == "error"
            assert data["redis"]["status"] == "ok"

    def test_redis_unhealthy(self, client: TestClient) -> None:
        """Should return 503 and degraded when redis is down."""
        with (
            patch(
                "src.routers.health.check_database_health",
                new_callable=AsyncMock,
            ) as mock_db,
            patch(
                "src.routers.health.check_redis_health",
                new_callable=AsyncMock,
            ) as mock_redis,
        ):
            mock_db.return_value = {"status": "ok", "latency_ms": 1.5}
            mock_redis.return_value = {"status": "error", "error": "Connection refused"}

            response = client.get("/api/v1/health/db")

            assert response.status_code == 503
            data = response.json()
            assert data["status"] == "degraded"
            assert data["database"]["status"] == "ok"
            assert data["redis"]["status"] == "error"

    def test_both_unhealthy(self, client: TestClient) -> None:
        """Should return 503 and degraded when both are down."""
        with (
            patch(
                "src.routers.health.check_database_health",
                new_callable=AsyncMock,
            ) as mock_db,
            patch(
                "src.routers.health.check_redis_health",
                new_callable=AsyncMock,
            ) as mock_redis,
        ):
            mock_db.return_value = {"status": "error", "error": "Timeout"}
            mock_redis.return_value = {"status": "error", "error": "Timeout"}

            response = client.get("/api/v1/health/db")

            assert response.status_code == 503
            data = response.json()
            assert data["status"] == "degraded"


class TestCheckDatabaseHealth:
    """Tests for check_database_health helper."""

    @pytest.mark.asyncio
    async def test_database_healthy(self) -> None:
        """Should return ok with latency when database responds."""
        mock_session = AsyncMock()

        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_session)
        mock_context.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "src.routers.health.async_session_factory",
            return_value=mock_context,
        ):
            from src.routers.health import check_database_health

            result = await check_database_health()

        assert result["status"] == "ok"
        assert "latency_ms" in result

    @pytest.mark.asyncio
    async def test_database_connection_error(self) -> None:
        """Should return error when database connection fails."""
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(
            side_effect=ConnectionError("Connection refused")
        )
        mock_context.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "src.routers.health.async_session_factory",
            return_value=mock_context,
        ):
            from src.routers.health import check_database_health

            result = await check_database_health()

        assert result["status"] == "error"
        assert "error" in result

    @pytest.mark.asyncio
    async def test_database_timeout(self) -> None:
        """Should return error on timeout."""
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(side_effect=TimeoutError())
        mock_context.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "src.routers.health.async_session_factory",
            return_value=mock_context,
        ):
            from src.routers.health import check_database_health

            result = await check_database_health()

        assert result["status"] == "error"
        assert result["error"] == "Connection timeout"


class TestCheckRedisHealth:
    """Tests for check_redis_health helper."""

    @pytest.mark.asyncio
    async def test_redis_healthy(self) -> None:
        """Should return ok with latency when redis responds."""
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(return_value=True)
        mock_client.aclose = AsyncMock()

        mock_redis_mod = MagicMock()
        mock_redis_mod.from_url.return_value = mock_client

        with patch("redis.asyncio", mock_redis_mod):
            from src.routers.health import check_redis_health

            result = await check_redis_health()

        assert result["status"] == "ok"
        assert "latency_ms" in result

    @pytest.mark.asyncio
    async def test_redis_connection_error(self) -> None:
        """Should return error when redis connection fails."""
        mock_redis_mod = MagicMock()
        mock_redis_mod.from_url.side_effect = ConnectionError("Connection refused")

        with patch("redis.asyncio", mock_redis_mod):
            from src.routers.health import check_redis_health

            result = await check_redis_health()

        assert result["status"] == "error"
        assert "error" in result

    @pytest.mark.asyncio
    async def test_redis_timeout(self) -> None:
        """Should return error on timeout."""
        mock_redis_mod = MagicMock()
        mock_redis_mod.from_url.side_effect = TimeoutError()

        with patch("redis.asyncio", mock_redis_mod):
            from src.routers.health import check_redis_health

            result = await check_redis_health()

        assert result["status"] == "error"
        assert result["error"] == "Connection timeout"
