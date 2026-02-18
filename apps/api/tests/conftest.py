"""Pytest fixtures for API tests."""

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies.beta import require_beta
from src.main import app


async def _override_require_beta():
    return None


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create async test client."""
    app.dependency_overrides[require_beta] = _override_require_beta
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
    app.dependency_overrides.pop(require_beta, None)


@pytest.fixture
def db_session() -> AsyncMock:
    """Create a mock async database session for unit/integration tests."""
    return AsyncMock(spec=AsyncSession)
