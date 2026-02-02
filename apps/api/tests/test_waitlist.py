"""Tests for waitlist endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from src.models.waitlist import WaitlistEntry


@pytest.mark.asyncio
async def test_join_waitlist_success(client: AsyncClient, db_session):
    """Test successful waitlist signup."""
    response = await client.post(
        "/api/v1/waitlist",
        json={"email": "test@example.com"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert "on the list" in data["message"]

    # Verify email was saved
    result = await db_session.execute(
        select(WaitlistEntry).where(WaitlistEntry.email == "test@example.com")
    )
    entry = result.scalar_one_or_none()
    assert entry is not None


@pytest.mark.asyncio
async def test_join_waitlist_duplicate_email(client: AsyncClient, db_session):
    """Test that duplicate emails return success for privacy."""
    # First signup
    await client.post(
        "/api/v1/waitlist",
        json={"email": "dupe@example.com"},
    )

    # Second signup with same email
    response = await client.post(
        "/api/v1/waitlist",
        json={"email": "dupe@example.com"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True

    # Verify only one entry exists
    result = await db_session.execute(
        select(WaitlistEntry).where(WaitlistEntry.email == "dupe@example.com")
    )
    entries = result.scalars().all()
    assert len(entries) == 1


@pytest.mark.asyncio
async def test_join_waitlist_email_normalized(client: AsyncClient, db_session):
    """Test that email is normalized to lowercase."""
    response = await client.post(
        "/api/v1/waitlist",
        json={"email": "Test@Example.COM"},
    )

    assert response.status_code == 201

    # Verify email was saved lowercase
    result = await db_session.execute(
        select(WaitlistEntry).where(WaitlistEntry.email == "test@example.com")
    )
    entry = result.scalar_one_or_none()
    assert entry is not None


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
