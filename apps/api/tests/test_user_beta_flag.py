"""Tests for beta tester flag on auto-created users."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.jwt import DecodedToken
from src.dependencies.auth import get_current_user


def make_mock_request() -> MagicMock:
    """Create a mock FastAPI Request object."""
    request = MagicMock()
    request.client.host = "127.0.0.1"
    request.headers.get.return_value = "test-user-agent"
    request.url.path = "/test"
    return request


class TestBetaTesterFlag:
    """Verify auto-created users receive is_beta_tester=True."""

    @pytest.mark.asyncio
    @patch("src.dependencies.auth.verify_token")
    async def test_new_user_has_beta_tester_flag(self, mock_verify: MagicMock) -> None:
        """Auto-created users should have is_beta_tester=True."""
        mock_request = make_mock_request()
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_verify.return_value = DecodedToken(
            sub="google-uid-beta",
            email="beta@example.com",
            name="Beta Tester",
        )

        # No existing user
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        await get_current_user(mock_request, mock_db, authorization="Bearer valid-token")

        created_user = mock_db.add.call_args[0][0]
        assert created_user.is_beta_tester is True
