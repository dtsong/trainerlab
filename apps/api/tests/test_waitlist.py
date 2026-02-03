"""Tests for waitlist endpoints."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.exc import IntegrityError

from src.models.waitlist import WaitlistEntry


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

    # Verify entry was added to session and committed
    mock_session.add.assert_called_once()
    added_entry = mock_session.add.call_args[0][0]
    assert isinstance(added_entry, WaitlistEntry)
    assert added_entry.email == "test@example.com"
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_join_waitlist_duplicate_email(client: AsyncClient):
    """Test that duplicate emails return success for privacy."""
    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session.commit.side_effect = IntegrityError(
        "duplicate key", params=None, orig=Exception()
    )

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
    mock_session.rollback.assert_called_once()


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

    # Verify email was normalized before saving
    added_entry = mock_session.add.call_args[0][0]
    assert added_entry.email == "test@example.com"


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
