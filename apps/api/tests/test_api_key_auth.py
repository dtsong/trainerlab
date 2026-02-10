"""Tests for API key authentication dependency."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies.api_key_auth import get_api_key_user, record_api_request
from src.models.api_key import ApiKey


@pytest.fixture
def mock_request():
    """Create a mock request."""
    request = MagicMock()
    request.client.host = "127.0.0.1"
    request.headers.get.return_value = "test-user-agent"
    request.url.path = "/api/v1/public/meta"
    request.method = "GET"
    return request


@pytest.fixture
def mock_session() -> AsyncMock:
    """Create a mock database session."""
    session = AsyncMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def mock_api_key() -> ApiKey:
    """Create a mock API key."""
    api_key = MagicMock(spec=ApiKey)
    api_key.id = uuid4()
    api_key.user_id = uuid4()
    api_key.key_hash = "hashed_key"
    api_key.is_active = True
    api_key.monthly_limit = 1000
    api_key.requests_this_month = 100
    api_key.updated_at = datetime.now(UTC)
    return api_key


class TestGetApiKeyUser:
    """Tests for get_api_key_user dependency."""

    @pytest.mark.asyncio
    async def test_returns_api_key_on_valid_key(
        self, mock_request, mock_session: AsyncMock, mock_api_key: ApiKey
    ):
        """Test returning API key on valid authentication."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_api_key
        mock_session.execute.return_value = mock_result

        with patch("src.dependencies.api_key_auth.hash_api_key") as mock_hash:
            mock_hash.return_value = "hashed_key"
            result = await get_api_key_user(
                mock_request, mock_session, x_api_key="tl_test123"
            )

        assert result == mock_api_key
        assert mock_api_key.requests_this_month == 101
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_401_when_no_key_provided(
        self, mock_request, mock_session: AsyncMock
    ):
        """Test raising 401 when no API key header provided."""
        with pytest.raises(HTTPException) as exc_info:
            await get_api_key_user(mock_request, mock_session, x_api_key=None)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "X-API-Key header required"

    @pytest.mark.asyncio
    async def test_raises_401_when_key_invalid(
        self, mock_request, mock_session: AsyncMock
    ):
        """Test raising 401 when API key is invalid."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        with patch("src.dependencies.api_key_auth.hash_api_key") as mock_hash:
            mock_hash.return_value = "invalid_hash"
            with pytest.raises(HTTPException) as exc_info:
                await get_api_key_user(
                    mock_request, mock_session, x_api_key="tl_invalid"
                )

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid API key"

    @pytest.mark.asyncio
    async def test_raises_429_when_rate_limited(
        self, mock_request, mock_session: AsyncMock, mock_api_key: ApiKey
    ):
        """Test raising 429 when rate limit exceeded."""
        mock_api_key.monthly_limit = 100
        mock_api_key.requests_this_month = 100  # At limit

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_api_key
        mock_session.execute.return_value = mock_result

        with patch("src.dependencies.api_key_auth.hash_api_key") as mock_hash:
            mock_hash.return_value = "hashed_key"
            with pytest.raises(HTTPException) as exc_info:
                await get_api_key_user(
                    mock_request, mock_session, x_api_key="tl_test123"
                )

        assert exc_info.value.status_code == 429
        assert exc_info.value.detail == "Monthly rate limit exceeded"

    @pytest.mark.asyncio
    async def test_resets_monthly_counter_on_new_month(
        self, mock_request, mock_session: AsyncMock, mock_api_key: ApiKey
    ):
        """Test resetting monthly counter when month changes."""
        mock_api_key.updated_at = datetime.now(UTC) - timedelta(days=32)
        mock_api_key.requests_this_month = 500

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_api_key
        mock_session.execute.return_value = mock_result

        with patch("src.dependencies.api_key_auth.hash_api_key") as mock_hash:
            mock_hash.return_value = "hashed_key"
            await get_api_key_user(mock_request, mock_session, x_api_key="tl_test123")

        # Counter should be reset to 0, then incremented to 1
        assert mock_api_key.requests_this_month == 1

    @pytest.mark.asyncio
    async def test_resets_counter_on_year_change(
        self, mock_request, mock_session: AsyncMock, mock_api_key: ApiKey
    ):
        """Test resetting monthly counter when year changes."""
        last_year = datetime.now(UTC).replace(year=datetime.now(UTC).year - 1)
        mock_api_key.updated_at = last_year
        mock_api_key.requests_this_month = 500

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_api_key
        mock_session.execute.return_value = mock_result

        with patch("src.dependencies.api_key_auth.hash_api_key") as mock_hash:
            mock_hash.return_value = "hashed_key"
            await get_api_key_user(mock_request, mock_session, x_api_key="tl_test123")

        assert mock_api_key.requests_this_month == 1

    @pytest.mark.asyncio
    async def test_rate_limit_header_on_429(
        self, mock_request, mock_session: AsyncMock, mock_api_key: ApiKey
    ):
        """Test rate limit header is included in 429 response."""
        mock_api_key.monthly_limit = 1000
        mock_api_key.requests_this_month = 1000

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_api_key
        mock_session.execute.return_value = mock_result

        with patch("src.dependencies.api_key_auth.hash_api_key") as mock_hash:
            mock_hash.return_value = "hashed_key"
            with pytest.raises(HTTPException) as exc_info:
                await get_api_key_user(
                    mock_request, mock_session, x_api_key="tl_test123"
                )

        assert exc_info.value.headers["X-RateLimit-Limit"] == "1000"


class TestRecordApiRequest:
    """Tests for record_api_request function."""

    @pytest.mark.asyncio
    async def test_records_api_request(
        self, mock_request, mock_session: AsyncMock, mock_api_key: ApiKey
    ):
        """Test recording API request."""
        await record_api_request(
            mock_api_key,
            mock_request,
            mock_session,
            status_code=200,
            response_time_ms=50,
        )

        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

        added_request = mock_session.add.call_args[0][0]
        assert added_request.api_key_id == mock_api_key.id
        assert added_request.endpoint == "/api/v1/public/meta"
        assert added_request.method == "GET"
        assert added_request.status_code == 200
        assert added_request.response_time_ms == 50

    @pytest.mark.asyncio
    async def test_records_without_response_time(
        self, mock_request, mock_session: AsyncMock, mock_api_key: ApiKey
    ):
        """Test recording API request without response time."""
        await record_api_request(
            mock_api_key,
            mock_request,
            mock_session,
            status_code=200,
        )

        added_request = mock_session.add.call_args[0][0]
        assert added_request.response_time_ms is None

    @pytest.mark.asyncio
    async def test_records_error_status_codes(
        self, mock_request, mock_session: AsyncMock, mock_api_key: ApiKey
    ):
        """Test recording requests with error status codes."""
        await record_api_request(
            mock_api_key,
            mock_request,
            mock_session,
            status_code=500,
        )

        added_request = mock_session.add.call_args[0][0]
        assert added_request.status_code == 500
