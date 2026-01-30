"""Tests for health check endpoint."""

from httpx import AsyncClient


async def test_health_check(client: AsyncClient) -> None:
    """Test basic health check endpoint."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
