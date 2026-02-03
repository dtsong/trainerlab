"""Tests for Cloud Scheduler authentication dependency."""

from unittest.mock import patch

import pytest
from fastapi import HTTPException

from src.config import Settings
from src.dependencies.scheduler_auth import (
    SchedulerAuthError,
    _verify_oidc_token,
    verify_scheduler_auth,
)


class TestVerifyOidcToken:
    """Tests for _verify_oidc_token function."""

    def test_verifies_valid_token(self) -> None:
        """Should return claims for valid token."""
        expected_claims = {
            "email": "scheduler@project.iam.gserviceaccount.com",
            "aud": "https://api.example.com",
        }

        with patch(
            "src.dependencies.scheduler_auth.id_token.verify_oauth2_token"
        ) as mock_verify:
            mock_verify.return_value = expected_claims

            claims = _verify_oidc_token(
                token="valid-token",
                expected_audience="https://api.example.com",
            )

            assert claims == expected_claims
            mock_verify.assert_called_once()

    def test_raises_on_invalid_token(self) -> None:
        """Should raise SchedulerAuthError for invalid token."""
        with patch(
            "src.dependencies.scheduler_auth.id_token.verify_oauth2_token"
        ) as mock_verify:
            mock_verify.side_effect = ValueError("Token expired")

            with pytest.raises(SchedulerAuthError, match="Token verification failed"):
                _verify_oidc_token(
                    token="invalid-token",
                    expected_audience="https://api.example.com",
                )

    def test_verifies_email_when_provided(self) -> None:
        """Should verify email claim matches one of allowed emails."""
        claims = {
            "email": "scheduler@project.iam.gserviceaccount.com",
            "aud": "https://api.example.com",
        }

        with patch(
            "src.dependencies.scheduler_auth.id_token.verify_oauth2_token"
        ) as mock_verify:
            mock_verify.return_value = claims

            result = _verify_oidc_token(
                token="valid-token",
                expected_audience="https://api.example.com",
                allowed_emails=["scheduler@project.iam.gserviceaccount.com"],
            )

            assert result == claims

    def test_raises_on_email_mismatch(self) -> None:
        """Should raise SchedulerAuthError when email not in allowed list."""
        claims = {
            "email": "wrong@project.iam.gserviceaccount.com",
            "aud": "https://api.example.com",
        }

        with patch(
            "src.dependencies.scheduler_auth.id_token.verify_oauth2_token"
        ) as mock_verify:
            mock_verify.return_value = claims

            with pytest.raises(SchedulerAuthError, match="Token email not allowed"):
                _verify_oidc_token(
                    token="valid-token",
                    expected_audience="https://api.example.com",
                    allowed_emails=["scheduler@project.iam.gserviceaccount.com"],
                )

    def test_raises_on_missing_email(self) -> None:
        """Should raise when allowed_emails specified but token has no email."""
        claims = {"aud": "https://api.example.com"}  # No email

        with patch(
            "src.dependencies.scheduler_auth.id_token.verify_oauth2_token"
        ) as mock_verify:
            mock_verify.return_value = claims

            with pytest.raises(SchedulerAuthError, match="Token email not allowed"):
                _verify_oidc_token(
                    token="valid-token",
                    expected_audience="https://api.example.com",
                    allowed_emails=["scheduler@project.iam.gserviceaccount.com"],
                )


class TestVerifySchedulerAuth:
    """Tests for verify_scheduler_auth dependency."""

    @pytest.fixture
    def bypass_settings(self) -> Settings:
        """Settings with auth bypass enabled."""
        return Settings(
            scheduler_auth_bypass=True,
            cloud_run_url="https://api.example.com",
        )

    @pytest.fixture
    def production_settings(self) -> Settings:
        """Settings for production (no bypass)."""
        return Settings(
            scheduler_auth_bypass=False,
            cloud_run_url="https://api.example.com",
            scheduler_service_account="scheduler@project.iam.gserviceaccount.com",
        )

    @pytest.fixture
    def unconfigured_settings(self) -> Settings:
        """Settings without cloud_run_url configured."""
        return Settings(
            scheduler_auth_bypass=False,
            cloud_run_url=None,
        )

    @pytest.mark.asyncio
    async def test_bypasses_auth_in_development(
        self, bypass_settings: Settings
    ) -> None:
        """Should return None when bypass is enabled."""
        result = await verify_scheduler_auth(
            authorization="Bearer some-token",
            settings=bypass_settings,
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_bypasses_without_authorization_header(
        self, bypass_settings: Settings
    ) -> None:
        """Should bypass even without auth header in dev mode."""
        result = await verify_scheduler_auth(
            authorization=None,
            settings=bypass_settings,
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_raises_on_missing_auth_header(
        self, production_settings: Settings
    ) -> None:
        """Should raise 401 when Authorization header missing."""
        with pytest.raises(HTTPException) as exc_info:
            await verify_scheduler_auth(
                authorization=None,
                settings=production_settings,
            )

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Authorization header required"

    @pytest.mark.asyncio
    async def test_raises_on_invalid_auth_format(
        self, production_settings: Settings
    ) -> None:
        """Should raise 401 for non-Bearer auth format."""
        with pytest.raises(HTTPException) as exc_info:
            await verify_scheduler_auth(
                authorization="Basic dXNlcjpwYXNz",
                settings=production_settings,
            )

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid authorization header format"

    @pytest.mark.asyncio
    async def test_raises_on_malformed_bearer(
        self, production_settings: Settings
    ) -> None:
        """Should raise 401 for malformed Bearer token."""
        with pytest.raises(HTTPException) as exc_info:
            await verify_scheduler_auth(
                authorization="Bearer",  # Missing token
                settings=production_settings,
            )

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid authorization header format"

    @pytest.mark.asyncio
    async def test_raises_on_missing_cloud_run_url(
        self, unconfigured_settings: Settings
    ) -> None:
        """Should raise 500 when cloud_run_url not configured."""
        with pytest.raises(HTTPException) as exc_info:
            await verify_scheduler_auth(
                authorization="Bearer valid-token",
                settings=unconfigured_settings,
            )

        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "Scheduler authentication not configured"

    @pytest.mark.asyncio
    async def test_returns_claims_on_valid_token(
        self, production_settings: Settings
    ) -> None:
        """Should return claims for valid token."""
        expected_claims = {
            "email": "scheduler@project.iam.gserviceaccount.com",
            "aud": "https://api.example.com",
        }

        with patch("src.dependencies.scheduler_auth._verify_oidc_token") as mock_verify:
            mock_verify.return_value = expected_claims

            result = await verify_scheduler_auth(
                authorization="Bearer valid-token",
                settings=production_settings,
            )

            assert result == expected_claims
            mock_verify.assert_called_once_with(
                token="valid-token",
                expected_audience="https://api.example.com",
                allowed_emails=["scheduler@project.iam.gserviceaccount.com"],
            )

    @pytest.mark.asyncio
    async def test_raises_on_verification_failure(
        self, production_settings: Settings
    ) -> None:
        """Should raise 401 when token verification fails."""
        with patch("src.dependencies.scheduler_auth._verify_oidc_token") as mock_verify:
            mock_verify.side_effect = SchedulerAuthError("Token expired")

            with pytest.raises(HTTPException) as exc_info:
                await verify_scheduler_auth(
                    authorization="Bearer expired-token",
                    settings=production_settings,
                )

            assert exc_info.value.status_code == 401
            assert exc_info.value.detail == "Invalid or expired token"

    @pytest.mark.asyncio
    async def test_bearer_case_insensitive(self, production_settings: Settings) -> None:
        """Should accept Bearer in any case."""
        expected_claims = {"email": "scheduler@project.iam.gserviceaccount.com"}

        with patch("src.dependencies.scheduler_auth._verify_oidc_token") as mock_verify:
            mock_verify.return_value = expected_claims

            # Lowercase "bearer"
            result = await verify_scheduler_auth(
                authorization="bearer valid-token",
                settings=production_settings,
            )

            assert result == expected_claims

    @pytest.mark.asyncio
    async def test_bypasses_without_calling_verify(
        self, bypass_settings: Settings
    ) -> None:
        """Should skip token verification entirely in bypass mode."""
        with patch("src.dependencies.scheduler_auth._verify_oidc_token") as mock_verify:
            result = await verify_scheduler_auth(
                authorization="Bearer some-token",
                settings=bypass_settings,
            )

            assert result is None
            mock_verify.assert_not_called()

    @pytest.mark.asyncio
    async def test_handles_unexpected_verification_error(
        self, production_settings: Settings
    ) -> None:
        """Should propagate unexpected exceptions from verification.

        Note: The implementation only catches SchedulerAuthError. Other
        exceptions (e.g., network errors from Google auth library) will
        propagate as 500 errors. This test documents that behavior.
        """
        with patch("src.dependencies.scheduler_auth._verify_oidc_token") as mock_verify:
            # Simulate an unexpected error (not SchedulerAuthError)
            mock_verify.side_effect = ConnectionError("Network unreachable")

            # Exception propagates - FastAPI will convert to 500
            with pytest.raises(ConnectionError, match="Network unreachable"):
                await verify_scheduler_auth(
                    authorization="Bearer some-token",
                    settings=production_settings,
                )
