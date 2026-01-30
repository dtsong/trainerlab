"""Tests for health check endpoints."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


async def test_health_check(client: AsyncClient) -> None:
    """Test basic health check endpoint."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


async def test_health_check_version_format(client: AsyncClient) -> None:
    """Test health check version is valid semver-like format."""
    response = await client.get("/api/v1/health")
    data = response.json()
    version = data["version"]
    # Basic semver format check (x.y.z)
    parts = version.split(".")
    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)


class TestDatabaseHealthCheck:
    """Tests for database health check endpoint."""

    @pytest.mark.asyncio
    async def test_db_health_check_success(self, client: AsyncClient) -> None:
        """Test DB health check when database is available."""
        # Mock successful database connection
        with (
            patch(
                "src.routers.health.check_database_health",
                new_callable=AsyncMock,
                return_value={"status": "ok", "latency_ms": 5.0},
            ),
            patch(
                "src.routers.health.check_redis_health",
                new_callable=AsyncMock,
                return_value={"status": "ok", "latency_ms": 2.0},
            ),
        ):
            response = await client.get("/api/v1/health/db")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "database" in data
        assert "redis" in data
        assert data["database"]["status"] == "ok"
        assert data["redis"]["status"] == "ok"

    @pytest.mark.asyncio
    async def test_db_health_check_database_failure(self, client: AsyncClient) -> None:
        """Test DB health check when database is unavailable."""
        with (
            patch(
                "src.routers.health.check_database_health",
                new_callable=AsyncMock,
                return_value={"status": "error", "error": "Connection refused"},
            ),
            patch(
                "src.routers.health.check_redis_health",
                new_callable=AsyncMock,
                return_value={"status": "ok", "latency_ms": 2.0},
            ),
        ):
            response = await client.get("/api/v1/health/db")

        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "degraded"
        assert data["database"]["status"] == "error"

    @pytest.mark.asyncio
    async def test_db_health_check_redis_failure(self, client: AsyncClient) -> None:
        """Test DB health check when Redis is unavailable."""
        with (
            patch(
                "src.routers.health.check_database_health",
                new_callable=AsyncMock,
                return_value={"status": "ok", "latency_ms": 5.0},
            ),
            patch(
                "src.routers.health.check_redis_health",
                new_callable=AsyncMock,
                return_value={"status": "error", "error": "Connection refused"},
            ),
        ):
            response = await client.get("/api/v1/health/db")

        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "degraded"
        assert data["redis"]["status"] == "error"

    @pytest.mark.asyncio
    async def test_db_health_check_all_failed(self, client: AsyncClient) -> None:
        """Test DB health check when all services are unavailable."""
        with (
            patch(
                "src.routers.health.check_database_health",
                new_callable=AsyncMock,
                return_value={"status": "error", "error": "DB down"},
            ),
            patch(
                "src.routers.health.check_redis_health",
                new_callable=AsyncMock,
                return_value={"status": "error", "error": "Redis down"},
            ),
        ):
            response = await client.get("/api/v1/health/db")

        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "degraded"
