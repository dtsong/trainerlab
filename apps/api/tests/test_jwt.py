"""Tests for JWT verification (NextAuth.js HS256 tokens)."""

import time
from unittest.mock import MagicMock, patch

import pytest
from jose import jwt

from src.core.jwt import DecodedToken, TokenVerificationError, verify_token

TEST_SECRET = "test-secret-for-jwt-verification"


def _make_token(
    sub: str = "google-uid-123",
    email: str | None = "test@example.com",
    name: str | None = "Test User",
    picture: str | None = "https://example.com/photo.jpg",
    exp_offset: int = 3600,
    secret: str = TEST_SECRET,
) -> str:
    """Create a test HS256 JWT."""
    payload: dict = {"sub": sub, "iat": int(time.time())}
    if email is not None:
        payload["email"] = email
    if name is not None:
        payload["name"] = name
    if picture is not None:
        payload["picture"] = picture
    payload["exp"] = int(time.time()) + exp_offset
    return jwt.encode(payload, secret, algorithm="HS256")


class TestVerifyToken:
    """Tests for verify_token."""

    @patch("src.core.jwt.get_settings")
    def test_missing_secret_raises(self, mock_get_settings: MagicMock) -> None:
        """Test that missing NEXTAUTH_SECRET raises TokenVerificationError."""
        mock_settings = MagicMock()
        mock_settings.nextauth_secret = None
        mock_get_settings.return_value = mock_settings

        with pytest.raises(TokenVerificationError, match="not configured"):
            verify_token("some-token")

    @patch("src.core.jwt.get_settings")
    def test_valid_token(self, mock_get_settings: MagicMock) -> None:
        """Test successful token verification."""
        mock_settings = MagicMock()
        mock_settings.nextauth_secret = TEST_SECRET
        mock_get_settings.return_value = mock_settings

        token = _make_token()
        result = verify_token(token)

        assert result == DecodedToken(
            sub="google-uid-123",
            email="test@example.com",
            name="Test User",
            picture="https://example.com/photo.jpg",
        )

    @patch("src.core.jwt.get_settings")
    def test_valid_token_minimal_claims(self, mock_get_settings: MagicMock) -> None:
        """Test token with only sub claim."""
        mock_settings = MagicMock()
        mock_settings.nextauth_secret = TEST_SECRET
        mock_get_settings.return_value = mock_settings

        token = _make_token(email=None, name=None, picture=None)
        result = verify_token(token)

        assert result is not None
        assert result.sub == "google-uid-123"
        assert result.email is None
        assert result.name is None
        assert result.picture is None

    @patch("src.core.jwt.get_settings")
    def test_expired_token_returns_none(self, mock_get_settings: MagicMock) -> None:
        """Test that expired token returns None."""
        mock_settings = MagicMock()
        mock_settings.nextauth_secret = TEST_SECRET
        mock_get_settings.return_value = mock_settings

        token = _make_token(exp_offset=-3600)  # Expired 1 hour ago
        result = verify_token(token)

        assert result is None

    @patch("src.core.jwt.get_settings")
    def test_wrong_secret_returns_none(self, mock_get_settings: MagicMock) -> None:
        """Test that token signed with wrong secret returns None."""
        mock_settings = MagicMock()
        mock_settings.nextauth_secret = TEST_SECRET
        mock_get_settings.return_value = mock_settings

        token = _make_token(secret="wrong-secret")
        result = verify_token(token)

        assert result is None

    @patch("src.core.jwt.get_settings")
    def test_malformed_token_returns_none(self, mock_get_settings: MagicMock) -> None:
        """Test that malformed token returns None."""
        mock_settings = MagicMock()
        mock_settings.nextauth_secret = TEST_SECRET
        mock_get_settings.return_value = mock_settings

        result = verify_token("not.a.valid.jwt")

        assert result is None

    @patch("src.core.jwt.get_settings")
    def test_missing_sub_returns_none(self, mock_get_settings: MagicMock) -> None:
        """Test that token without sub claim returns None."""
        mock_settings = MagicMock()
        mock_settings.nextauth_secret = TEST_SECRET
        mock_get_settings.return_value = mock_settings

        # Create token without sub
        payload = {
            "email": "test@example.com",
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
        }
        token = jwt.encode(payload, TEST_SECRET, algorithm="HS256")
        result = verify_token(token)

        assert result is None
