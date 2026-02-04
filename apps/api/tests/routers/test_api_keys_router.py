"""Tests for API keys router."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.models.api_key import ApiKey
from src.models.user import User
from src.routers.api_keys import create_api_key, get_api_key, list_api_keys, revoke_api_key
from src.schemas.api_key import ApiKeyCreate


@pytest.fixture
def mock_session() -> AsyncMock:
    """Create a mock database session."""
    return AsyncMock()


@pytest.fixture
def mock_creator_user():
    """Create a mock creator user."""
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.email = "creator@example.com"
    user.is_creator = True
    return user


@pytest.fixture
def mock_api_key(mock_creator_user):
    """Create a mock API key."""
    api_key = MagicMock(spec=ApiKey)
    api_key.id = uuid4()
    api_key.user_id = mock_creator_user.id
    api_key.key_prefix = "tl_test12"
    api_key.name = "Test Key"
    api_key.monthly_limit = 1000
    api_key.requests_this_month = 50
    api_key.is_active = True
    api_key.created_at = datetime.now(UTC)
    api_key.updated_at = datetime.now(UTC)
    return api_key


class TestCreateApiKey:
    """Tests for POST /api/v1/api-keys."""

    @pytest.mark.asyncio
    async def test_creates_api_key_successfully(
        self, mock_session, mock_creator_user, mock_api_key
    ):
        """Test creating API key successfully."""
        key_data = ApiKeyCreate(name="Test Key", monthly_limit=1000)

        with patch("src.routers.api_keys.ApiKeyService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.create_api_key = AsyncMock(
                return_value=(mock_api_key, "tl_test123456789abcdef")
            )
            mock_service_class.return_value = mock_service

            response = await create_api_key(mock_session, mock_creator_user, key_data)

        assert response.full_key == "tl_test123456789abcdef"
        mock_service.create_api_key.assert_called_once()


class TestListApiKeys:
    """Tests for GET /api/v1/api-keys."""

    @pytest.mark.asyncio
    async def test_lists_api_keys(self, mock_session, mock_creator_user, mock_api_key):
        """Test listing API keys."""
        with patch("src.routers.api_keys.ApiKeyService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.list_user_api_keys = AsyncMock(return_value=[mock_api_key])
            mock_service_class.return_value = mock_service

            response = await list_api_keys(mock_session, mock_creator_user)

        assert response.total == 1
        assert len(response.items) == 1


class TestGetApiKey:
    """Tests for GET /api/v1/api-keys/{key_id}."""

    @pytest.mark.asyncio
    async def test_gets_api_key(self, mock_session, mock_creator_user, mock_api_key):
        """Test getting a specific API key."""
        with patch("src.routers.api_keys.ApiKeyService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_api_key = AsyncMock(return_value=mock_api_key)
            mock_service_class.return_value = mock_service

            response = await get_api_key(mock_session, mock_creator_user, mock_api_key.id)

        assert response.id == mock_api_key.id

    @pytest.mark.asyncio
    async def test_returns_404_when_not_found(self, mock_session, mock_creator_user):
        """Test returning 404 when API key not found."""
        from fastapi import HTTPException

        with patch("src.routers.api_keys.ApiKeyService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_api_key = AsyncMock(return_value=None)
            mock_service_class.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                await get_api_key(mock_session, mock_creator_user, uuid4())

        assert exc_info.value.status_code == 404


class TestRevokeApiKey:
    """Tests for DELETE /api/v1/api-keys/{key_id}."""

    @pytest.mark.asyncio
    async def test_revokes_api_key(self, mock_session, mock_creator_user, mock_api_key):
        """Test revoking an API key."""
        with patch("src.routers.api_keys.ApiKeyService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.revoke_api_key = AsyncMock(return_value=True)
            mock_service_class.return_value = mock_service

            # Should not raise
            await revoke_api_key(mock_session, mock_creator_user, mock_api_key.id)

    @pytest.mark.asyncio
    async def test_returns_404_when_not_found(self, mock_session, mock_creator_user):
        """Test returning 404 when API key not found."""
        from fastapi import HTTPException

        with patch("src.routers.api_keys.ApiKeyService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.revoke_api_key = AsyncMock(return_value=False)
            mock_service_class.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                await revoke_api_key(mock_session, mock_creator_user, uuid4())

        assert exc_info.value.status_code == 404
