"""Tests for Firebase Admin SDK initialization."""

from unittest.mock import MagicMock, patch

import pytest

from src.core.firebase import init_firebase, verify_token


class TestFirebaseInit:
    """Tests for Firebase initialization."""

    def setup_method(self) -> None:
        """Reset Firebase state before each test."""
        import src.core.firebase as firebase_module

        firebase_module._app = None

    @patch("src.core.firebase.get_settings")
    def test_init_firebase_no_project_id(self, mock_get_settings: MagicMock) -> None:
        """Test that init returns None when project ID not configured."""
        mock_settings = MagicMock()
        mock_settings.firebase_project_id = None
        mock_get_settings.return_value = mock_settings

        result = init_firebase()

        assert result is None

    @patch("src.core.firebase.firebase_admin")
    @patch("src.core.firebase.credentials")
    @patch("src.core.firebase.get_settings")
    def test_init_firebase_success(
        self,
        mock_get_settings: MagicMock,
        mock_credentials: MagicMock,
        mock_firebase_admin: MagicMock,
    ) -> None:
        """Test successful Firebase initialization."""
        mock_settings = MagicMock()
        mock_settings.firebase_project_id = "test-project"
        mock_get_settings.return_value = mock_settings

        mock_cred = MagicMock()
        mock_credentials.ApplicationDefault.return_value = mock_cred

        mock_app = MagicMock()
        mock_firebase_admin.initialize_app.return_value = mock_app

        result = init_firebase()

        assert result == mock_app
        mock_firebase_admin.initialize_app.assert_called_once_with(
            mock_cred,
            options={"projectId": "test-project"},
        )

    @patch("src.core.firebase.firebase_admin")
    @patch("src.core.firebase.credentials")
    @patch("src.core.firebase.get_settings")
    def test_init_firebase_returns_cached_app(
        self,
        mock_get_settings: MagicMock,
        mock_credentials: MagicMock,
        mock_firebase_admin: MagicMock,
    ) -> None:
        """Test that second call returns cached app."""
        mock_settings = MagicMock()
        mock_settings.firebase_project_id = "test-project"
        mock_get_settings.return_value = mock_settings

        mock_app = MagicMock()
        mock_firebase_admin.initialize_app.return_value = mock_app

        # First call
        result1 = init_firebase()
        # Second call
        result2 = init_firebase()

        assert result1 == result2
        # Should only be called once
        assert mock_firebase_admin.initialize_app.call_count == 1


class TestVerifyToken:
    """Tests for token verification."""

    def setup_method(self) -> None:
        """Reset Firebase state before each test."""
        import src.core.firebase as firebase_module

        firebase_module._app = None

    @pytest.mark.asyncio
    async def test_verify_token_firebase_not_initialized(self) -> None:
        """Test that verify_token returns None when Firebase not initialized."""
        result = await verify_token("some-token")

        assert result is None

    @pytest.mark.asyncio
    @patch("src.core.firebase.auth.verify_id_token")
    async def test_verify_token_success(self, mock_verify: MagicMock) -> None:
        """Test successful token verification."""
        import src.core.firebase as firebase_module

        firebase_module._app = MagicMock()

        mock_decoded = {
            "uid": "test-uid",
            "email": "test@example.com",
        }
        mock_verify.return_value = mock_decoded

        result = await verify_token("valid-token")

        assert result == mock_decoded
        mock_verify.assert_called_once_with("valid-token")

    @pytest.mark.asyncio
    @patch("src.core.firebase.auth.verify_id_token")
    async def test_verify_token_invalid(self, mock_verify: MagicMock) -> None:
        """Test that invalid token returns None."""
        from firebase_admin import auth as real_auth

        import src.core.firebase as firebase_module

        firebase_module._app = MagicMock()
        mock_verify.side_effect = real_auth.InvalidIdTokenError("Invalid")

        result = await verify_token("invalid-token")

        assert result is None

    @pytest.mark.asyncio
    @patch("src.core.firebase.auth.verify_id_token")
    async def test_verify_token_expired(self, mock_verify: MagicMock) -> None:
        """Test that expired token returns None."""
        from firebase_admin import auth as real_auth

        import src.core.firebase as firebase_module

        firebase_module._app = MagicMock()
        mock_verify.side_effect = real_auth.ExpiredIdTokenError("Expired", None)

        result = await verify_token("expired-token")

        assert result is None

    @pytest.mark.asyncio
    @patch("src.core.firebase.auth.verify_id_token")
    async def test_verify_token_revoked(self, mock_verify: MagicMock) -> None:
        """Test that revoked token returns None."""
        from firebase_admin import auth as real_auth

        import src.core.firebase as firebase_module

        firebase_module._app = MagicMock()
        mock_verify.side_effect = real_auth.RevokedIdTokenError("Revoked")

        result = await verify_token("revoked-token")

        assert result is None
