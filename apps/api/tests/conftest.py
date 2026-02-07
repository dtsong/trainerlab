"""Pytest fixtures for API tests."""

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.main import app


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create async test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest.fixture
def db_session() -> AsyncMock:
    """Create a mock async database session for unit/integration tests."""
    return AsyncMock(spec=AsyncSession)
