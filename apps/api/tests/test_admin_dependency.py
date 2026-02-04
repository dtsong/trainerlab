"""Tests for admin authorization dependency."""

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from src.dependencies.admin import _log_admin_security_event, require_admin
from src.models.user import User


def make_mock_request() -> MagicMock:
    """Create a mock FastAPI Request object."""
    request = MagicMock()
    request.client.host = "127.0.0.1"
    request.headers.get.return_value = "test-user-agent"
    request.url.path = "/admin/test"
    return request


def make_mock_user(email: str = "admin@trainerlab.gg") -> MagicMock:
    """Create a mock User with the given email."""
    user = MagicMock(spec=User)
    user.email = email
    return user


class TestRequireAdmin:
    """Tests for require_admin dependency."""

    @pytest.mark.asyncio
    @patch("src.dependencies.admin.get_settings")
    async def test_admin_email_allowed(self, mock_settings: MagicMock) -> None:
        """Test that a user with an admin email passes the check."""
        mock_settings.return_value.admin_emails = "admin@trainerlab.gg"
        mock_request = make_mock_request()
        mock_user = make_mock_user("admin@trainerlab.gg")

        result = await require_admin(mock_request, mock_user)

        assert result == mock_user

    @pytest.mark.asyncio
    @patch("src.dependencies.admin.get_settings")
    async def test_non_admin_email_rejected(self, mock_settings: MagicMock) -> None:
        """Test that a non-admin email raises 403."""
        mock_settings.return_value.admin_emails = "admin@trainerlab.gg"
        mock_request = make_mock_request()
        mock_user = make_mock_user("regular@example.com")

        with pytest.raises(HTTPException) as exc_info:
            await require_admin(mock_request, mock_user)

        assert exc_info.value.status_code == 403
        assert "Admin access required" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch("src.dependencies.admin.get_settings")
    async def test_case_insensitive_email_matching(
        self, mock_settings: MagicMock
    ) -> None:
        """Test that email comparison is case-insensitive."""
        mock_settings.return_value.admin_emails = "Admin@TrainerLab.GG"
        mock_request = make_mock_request()
        mock_user = make_mock_user("admin@trainerlab.gg")

        result = await require_admin(mock_request, mock_user)

        assert result == mock_user

    @pytest.mark.asyncio
    @patch("src.dependencies.admin.get_settings")
    async def test_case_insensitive_user_email(self, mock_settings: MagicMock) -> None:
        """Test that user email with mixed case matches lowercase admin list."""
        mock_settings.return_value.admin_emails = "admin@trainerlab.gg"
        mock_request = make_mock_request()
        mock_user = make_mock_user("ADMIN@TRAINERLAB.GG")

        result = await require_admin(mock_request, mock_user)

        assert result == mock_user

    @pytest.mark.asyncio
    @patch("src.dependencies.admin.get_settings")
    async def test_multiple_admin_emails(self, mock_settings: MagicMock) -> None:
        """Test that multiple comma-separated admin emails work."""
        mock_settings.return_value.admin_emails = (
            "admin1@trainerlab.gg, admin2@trainerlab.gg, admin3@trainerlab.gg"
        )
        mock_request = make_mock_request()
        mock_user = make_mock_user("admin2@trainerlab.gg")

        result = await require_admin(mock_request, mock_user)

        assert result == mock_user

    @pytest.mark.asyncio
    @patch("src.dependencies.admin.get_settings")
    async def test_empty_admin_emails_rejects_all(
        self, mock_settings: MagicMock
    ) -> None:
        """Test that empty admin_emails setting rejects everyone."""
        mock_settings.return_value.admin_emails = ""
        mock_request = make_mock_request()
        mock_user = make_mock_user("anyone@example.com")

        with pytest.raises(HTTPException) as exc_info:
            await require_admin(mock_request, mock_user)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    @patch("src.dependencies.admin.get_settings")
    async def test_whitespace_only_admin_emails_rejects_all(
        self, mock_settings: MagicMock
    ) -> None:
        """Test that whitespace-only admin_emails rejects everyone."""
        mock_settings.return_value.admin_emails = "  ,  , "
        mock_request = make_mock_request()
        mock_user = make_mock_user("anyone@example.com")

        with pytest.raises(HTTPException) as exc_info:
            await require_admin(mock_request, mock_user)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    @patch("src.dependencies.admin.security_logger")
    @patch("src.dependencies.admin.logger")
    @patch("src.dependencies.admin.get_settings")
    async def test_non_admin_logs_warning(
        self,
        mock_settings: MagicMock,
        mock_logger: MagicMock,
        mock_security_logger: MagicMock,
    ) -> None:
        """Test that non-admin access attempt is logged."""
        mock_settings.return_value.admin_emails = "admin@trainerlab.gg"
        mock_request = make_mock_request()
        mock_user = make_mock_user("intruder@example.com")

        with pytest.raises(HTTPException):
            await require_admin(mock_request, mock_user)

        mock_logger.warning.assert_called_once()
        assert "intruder@example.com" in mock_logger.warning.call_args[0][1]

    @pytest.mark.asyncio
    @patch("src.dependencies.admin.security_logger")
    @patch("src.dependencies.admin.logger")
    @patch("src.dependencies.admin.get_settings")
    async def test_non_admin_logs_security_event(
        self,
        mock_settings: MagicMock,
        mock_logger: MagicMock,
        mock_security_logger: MagicMock,
    ) -> None:
        """Test that a structured security event is logged on denied access."""
        mock_settings.return_value.admin_emails = "admin@trainerlab.gg"
        mock_request = make_mock_request()
        mock_user = make_mock_user("intruder@example.com")

        with pytest.raises(HTTPException):
            await require_admin(mock_request, mock_user)

        mock_security_logger.warning.assert_called_once()
        logged_event = json.loads(mock_security_logger.warning.call_args[0][0])
        assert logged_event["event_type"] == "admin_access_denied"
        assert logged_event["user_email"] == "intruder@example.com"
        assert logged_event["ip_address"] == "127.0.0.1"
        assert logged_event["path"] == "/admin/test"


class TestLogAdminSecurityEvent:
    """Tests for _log_admin_security_event helper."""

    @patch("src.dependencies.admin.security_logger")
    def test_logs_with_request_context(self, mock_security_logger: MagicMock) -> None:
        """Test that security event includes request context."""
        mock_request = make_mock_request()

        _log_admin_security_event(
            "test_event",
            request=mock_request,
            user_email="test@example.com",
            details={"key": "value"},
        )

        mock_security_logger.warning.assert_called_once()
        logged_event = json.loads(mock_security_logger.warning.call_args[0][0])
        assert logged_event["event_type"] == "test_event"
        assert logged_event["user_email"] == "test@example.com"
        assert logged_event["ip_address"] == "127.0.0.1"
        assert logged_event["details"] == {"key": "value"}
        assert "timestamp" in logged_event

    @patch("src.dependencies.admin.security_logger")
    def test_logs_without_request(self, mock_security_logger: MagicMock) -> None:
        """Test that security event handles None request gracefully."""
        _log_admin_security_event(
            "test_event",
            request=None,
            user_email="test@example.com",
        )

        mock_security_logger.warning.assert_called_once()
        logged_event = json.loads(mock_security_logger.warning.call_args[0][0])
        assert logged_event["ip_address"] is None
        assert logged_event["user_agent"] is None
        assert logged_event["path"] is None
        assert logged_event["details"] == {}
