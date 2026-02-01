"""Tests for authentication dependencies."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from src.dependencies.auth import get_current_user, get_current_user_optional
from src.models.user import User


class TestGetCurrentUser:
    """Tests for get_current_user dependency."""

    @pytest.mark.asyncio
    async def test_missing_auth_header(self) -> None:
        """Test that missing auth header raises 401."""
        mock_db = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_db, authorization=None)

        assert exc_info.value.status_code == 401
        assert "Authorization header required" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_invalid_auth_header_format(self) -> None:
        """Test that malformed auth header raises 401."""
        mock_db = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_db, authorization="InvalidFormat")

        assert exc_info.value.status_code == 401
        assert "Invalid authorization header format" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_invalid_auth_header_not_bearer(self) -> None:
        """Test that non-Bearer auth header raises 401."""
        mock_db = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_db, authorization="Basic abc123")

        assert exc_info.value.status_code == 401
        assert "Invalid authorization header format" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch("src.dependencies.auth.verify_token")
    async def test_invalid_token(self, mock_verify: MagicMock) -> None:
        """Test that invalid token raises 401."""
        mock_db = AsyncMock()
        mock_verify.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_db, authorization="Bearer invalid-token")

        assert exc_info.value.status_code == 401
        assert "Invalid or expired token" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch("src.dependencies.auth.verify_token")
    async def test_token_missing_uid(self, mock_verify: MagicMock) -> None:
        """Test that token without uid raises 401."""
        mock_db = AsyncMock()
        mock_verify.return_value = {"email": "test@example.com"}  # No uid

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_db, authorization="Bearer valid-token")

        assert exc_info.value.status_code == 401
        assert "Token missing user ID" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch("src.dependencies.auth.verify_token")
    async def test_existing_user_returned(self, mock_verify: MagicMock) -> None:
        """Test that existing user is returned from database."""
        mock_db = AsyncMock()
        mock_verify.return_value = {
            "uid": "firebase-uid-123",
            "email": "test@example.com",
        }

        # Mock existing user in database
        mock_user = MagicMock(spec=User)
        mock_user.id = uuid4()
        mock_user.firebase_uid = "firebase-uid-123"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        result = await get_current_user(mock_db, authorization="Bearer valid-token")

        assert result == mock_user
        mock_db.add.assert_not_called()  # User already exists

    @pytest.mark.asyncio
    @patch("src.dependencies.auth.verify_token")
    async def test_new_user_created(self, mock_verify: MagicMock) -> None:
        """Test that new user is created on first login."""
        mock_db = AsyncMock()
        mock_verify.return_value = {
            "uid": "firebase-uid-new",
            "email": "new@example.com",
            "name": "New User",
            "picture": "https://example.com/avatar.jpg",
        }

        # Mock no existing user
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        await get_current_user(mock_db, authorization="Bearer valid-token")

        # Verify user was created
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

        # Verify user attributes
        created_user = mock_db.add.call_args[0][0]
        assert created_user.firebase_uid == "firebase-uid-new"
        assert created_user.email == "new@example.com"
        assert created_user.display_name == "New User"
        assert created_user.avatar_url == "https://example.com/avatar.jpg"

    @pytest.mark.asyncio
    @patch("src.dependencies.auth.verify_token")
    async def test_new_user_missing_email_raises(self, mock_verify: MagicMock) -> None:
        """Test that new user creation requires email."""
        mock_db = AsyncMock()
        mock_verify.return_value = {
            "uid": "firebase-uid-new",
            # No email in token (e.g., phone auth)
            "name": "New User",
        }

        # Mock no existing user
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_db, authorization="Bearer valid-token")

        assert exc_info.value.status_code == 401
        assert "Email required for account creation" in exc_info.value.detail
        mock_db.add.assert_not_called()


class TestGetCurrentUserOptional:
    """Tests for get_current_user_optional dependency."""

    @pytest.mark.asyncio
    async def test_no_auth_returns_none(self) -> None:
        """Test that no auth header returns None."""
        mock_db = AsyncMock()

        result = await get_current_user_optional(mock_db, authorization=None)

        assert result is None

    @pytest.mark.asyncio
    @patch("src.dependencies.auth.verify_token")
    async def test_invalid_auth_raises(self, mock_verify: MagicMock) -> None:
        """Test that invalid auth header still raises 401."""
        mock_db = AsyncMock()
        mock_verify.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_optional(
                mock_db, authorization="Bearer invalid-token"
            )

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    @patch("src.dependencies.auth.verify_token")
    async def test_valid_auth_returns_user(self, mock_verify: MagicMock) -> None:
        """Test that valid auth returns user."""
        mock_db = AsyncMock()
        mock_verify.return_value = {
            "uid": "firebase-uid-123",
            "email": "test@example.com",
        }

        mock_user = MagicMock(spec=User)
        mock_user.firebase_uid = "firebase-uid-123"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        result = await get_current_user_optional(
            mock_db, authorization="Bearer valid-token"
        )

        assert result == mock_user
