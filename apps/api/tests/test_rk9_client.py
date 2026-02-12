"""Tests for RK9 client."""

from datetime import date
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from src.clients.rk9 import (
    RegistrationStatus,
    RK9Client,
    RK9Error,
    RK9Event,
)


@pytest.fixture
def rk9_client():
    return RK9Client(timeout=5.0, max_retries=1, retry_delay=0.01)


class TestRK9EventDataclass:
    """Tests for RK9Event dataclass."""

    def test_creates_event_with_defaults(self):
        event = RK9Event(
            name="Orlando Regional",
            date=date(2026, 3, 15),
        )
        assert event.name == "Orlando Regional"
        assert event.date == date(2026, 3, 15)
        assert event.city is None
        assert event.status == "upcoming"
        assert event.source_url == ""

    def test_creates_event_with_all_fields(self):
        event = RK9Event(
            name="NAIC",
            date=date(2026, 6, 20),
            end_date=date(2026, 6, 22),
            city="Columbus",
            venue="Convention Center",
            country="US",
            registration_url="https://rk9.gg/event/naic",
            status="registration_open",
            source_url="https://rk9.gg/event/naic",
        )
        assert event.end_date == date(2026, 6, 22)
        assert event.city == "Columbus"
        assert event.country == "US"


class TestRegistrationStatus:
    """Tests for RegistrationStatus dataclass."""

    def test_open_registration(self):
        status = RegistrationStatus(
            is_open=True,
            capacity=256,
            registered_count=150,
        )
        assert status.is_open is True
        assert status.capacity == 256
        assert status.registered_count == 150

    def test_closed_registration(self):
        status = RegistrationStatus(is_open=False)
        assert status.is_open is False
        assert status.opens_at is None


class TestRK9ClientInit:
    """Tests for RK9Client initialization."""

    def test_creates_client(self, rk9_client):
        assert rk9_client is not None

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        async with RK9Client(timeout=5.0, max_retries=1) as client:
            assert client is not None


class TestRK9ClientParsing:
    """Tests for HTML parsing methods."""

    @pytest.mark.asyncio
    async def test_fetch_upcoming_events_parses_html(self, rk9_client):
        """Test that fetch_upcoming_events handles empty HTML."""
        html = "<html><body><div>No events</div></body></html>"

        with patch.object(rk9_client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = html
            events = await rk9_client.fetch_upcoming_events()

        assert isinstance(events, list)
        # Empty HTML should return empty list
        assert len(events) == 0

    @pytest.mark.asyncio
    async def test_handles_rate_limit_error(self, rk9_client):
        """Test that RK9 errors propagate correctly."""
        with (
            patch.object(
                rk9_client,
                "_get",
                new_callable=AsyncMock,
                side_effect=RK9Error("Rate limit exceeded"),
            ),
            pytest.raises(RK9Error),
        ):
            await rk9_client.fetch_upcoming_events()


class TestRK9ClientRetryBehavior:
    """Transient and hard failure behaviors for _get."""

    @pytest.mark.asyncio
    async def test_retries_transient_502_then_succeeds(self) -> None:
        client = RK9Client(timeout=5.0, max_retries=2, retry_delay=0.01)
        call_count = 0

        async def mock_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            request = httpx.Request("GET", "https://rk9.gg/test")
            if call_count == 1:
                return httpx.Response(502, request=request)
            return httpx.Response(200, text="ok", request=request)

        with patch.object(client._client, "get", side_effect=mock_get):
            result = await client._get("/test")

        assert result == "ok"
        assert call_count == 2
        await client.close()

    @pytest.mark.asyncio
    async def test_non_retryable_401_fails_fast(self) -> None:
        client = RK9Client(timeout=5.0, max_retries=3, retry_delay=0.01)
        call_count = 0

        async def mock_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            request = httpx.Request("GET", "https://rk9.gg/test")
            return httpx.Response(401, request=request)

        with (
            patch.object(client._client, "get", side_effect=mock_get),
            pytest.raises(RK9Error, match="HTTP error 401"),
        ):
            await client._get("/test")

        assert call_count == 1
        await client.close()
