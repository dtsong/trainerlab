"""Tests for creator authorization dependency."""

from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from src.dependencies.creator import require_creator
from src.models.user import User


@pytest.fixture
def mock_request():
    """Create a mock request."""
    request = MagicMock()
    request.client.host = "127.0.0.1"
    request.headers.get.return_value = "test-user-agent"
    request.url.path = "/api/v1/widgets"
    return request


@pytest.fixture
def creator_user() -> User:
    """Create a mock creator user."""
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.email = "creator@example.com"
    user.is_creator = True
    return user


@pytest.fixture
def regular_user() -> User:
    """Create a mock regular user."""
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.email = "regular@example.com"
    user.is_creator = False
    return user


class TestRequireCreator:
    """Tests for require_creator dependency."""

    @pytest.mark.asyncio
    async def test_allows_creator_user(self, mock_request, creator_user: User):
        """Test allowing creator user access."""
        result = await require_creator(mock_request, creator_user)
        assert result == creator_user

    @pytest.mark.asyncio
    async def test_denies_non_creator_user(self, mock_request, regular_user: User):
        """Test denying non-creator user access."""
        with pytest.raises(HTTPException) as exc_info:
            await require_creator(mock_request, regular_user)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "Creator access required"

    @pytest.mark.asyncio
    async def test_logs_denied_access(self, mock_request, regular_user: User, caplog):
        """Test logging denied access attempts."""
        with pytest.raises(HTTPException):
            await require_creator(mock_request, regular_user)

        assert "Non-creator access attempt" in caplog.text

    @pytest.mark.asyncio
    async def test_returns_same_user_object(self, mock_request, creator_user: User):
        """Test returning the same user object."""
        result = await require_creator(mock_request, creator_user)
        assert result is creator_user
        assert result.id == creator_user.id

    @pytest.mark.asyncio
    async def test_handles_missing_client(self, creator_user: User):
        """Test handling request with no client info."""
        request = MagicMock()
        request.client = None
        request.headers.get.return_value = None
        request.url.path = "/test"

        result = await require_creator(request, creator_user)
        assert result == creator_user

    @pytest.mark.asyncio
    async def test_handles_user_with_none_is_creator(self, mock_request):
        """Test handling user with None is_creator (should deny)."""
        user = MagicMock(spec=User)
        user.id = uuid4()
        user.email = "test@example.com"
        user.is_creator = None

        with pytest.raises(HTTPException) as exc_info:
            await require_creator(mock_request, user)

        assert exc_info.value.status_code == 403
