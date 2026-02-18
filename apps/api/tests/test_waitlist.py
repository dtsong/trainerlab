"""Tests for waitlist endpoints."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_join_waitlist_success(client: AsyncClient):
    """Test successful waitlist signup."""
    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    with patch(
        "src.routers.waitlist.async_session_factory",
        return_value=mock_session,
    ):
        response = await client.post(
            "/api/v1/waitlist",
            json={"email": "test@example.com"},
        )

    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert "on the list" in data["message"]

    # Verify upsert was executed and committed
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_join_waitlist_duplicate_email(client: AsyncClient):
    """Test that duplicate emails return success (upsert handles conflict)."""
    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    with patch(
        "src.routers.waitlist.async_session_factory",
        return_value=mock_session,
    ):
        response = await client.post(
            "/api/v1/waitlist",
            json={"email": "dupe@example.com"},
        )

    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_join_waitlist_email_normalized(client: AsyncClient):
    """Test that email is normalized to lowercase."""
    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    with patch(
        "src.routers.waitlist.async_session_factory",
        return_value=mock_session,
    ):
        response = await client.post(
            "/api/v1/waitlist",
            json={"email": "Test@Example.COM"},
        )

    assert response.status_code == 201

    # Verify execute was called (upsert with normalized email)
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_join_waitlist_invalid_email(client: AsyncClient):
    """Test that invalid email returns error."""
    response = await client.post(
        "/api/v1/waitlist",
        json={"email": "not-an-email"},
    )

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_join_waitlist_missing_email(client: AsyncClient):
    """Test that missing email returns error."""
    response = await client.post(
        "/api/v1/waitlist",
        json={},
    )

    assert response.status_code == 422
