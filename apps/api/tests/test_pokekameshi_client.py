"""Tests for Pokekameshi scraper client."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from src.clients.pokekameshi import (
    PokekameshiClient,
    PokekameshiError,
    PokekameshiMetaReport,
    PokekameshiTierTable,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> str:
    """Load an HTML fixture file."""
    return (FIXTURES_DIR / name).read_text()


class TestPokekameshiTierTable:
    """Tests for tier table parsing."""

    @pytest.mark.asyncio
    async def test_parses_tier_table(self) -> None:
        """Should parse tier table from HTML."""
        html = load_fixture("pokekameshi_tier_table.html")

        client = PokekameshiClient()
        with patch.object(client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = html
            result = await client.fetch_tier_tables()
            await client.close()

        assert isinstance(result, PokekameshiTierTable)
        assert len(result.entries) >= 3

        charizard = next(
            (e for e in result.entries if "リザードン" in e.archetype_name), None
        )
        assert charizard is not None
        assert charizard.tier == "S"
        assert charizard.share_rate == pytest.approx(0.185, rel=0.01)
        assert charizard.csp_points == 2450
        assert charizard.deck_power == pytest.approx(9.2, rel=0.1)
        gardevoir = next(
            (e for e in result.entries if "サーナイト" in e.archetype_name), None
        )
        assert gardevoir is not None
        assert gardevoir.tier == "S"
        assert gardevoir.csp_points == 2100

        dragapult = next(
            (e for e in result.entries if "ドラパルト" in e.archetype_name), None
        )
        assert dragapult is not None
        assert dragapult.tier == "A"

    @pytest.mark.asyncio
    async def test_includes_source_url(self) -> None:
        """Should include source URL in result."""
        html = load_fixture("pokekameshi_tier_table.html")

        client = PokekameshiClient()
        with patch.object(client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = html
            result = await client.fetch_tier_tables()
            await client.close()

        assert result.source_url is not None
        assert "pokekameshi.com" in result.source_url

    @pytest.mark.asyncio
    async def test_stores_raw_html(self) -> None:
        """Should store raw HTML for re-parsing."""
        html = load_fixture("pokekameshi_tier_table.html")

        client = PokekameshiClient()
        with patch.object(client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = html
            result = await client.fetch_tier_tables()
            await client.close()

        assert result.raw_html is not None
        assert "リザードン" in result.raw_html


class TestPokekameshiMetaReport:
    """Tests for meta share report parsing."""

    @pytest.mark.asyncio
    async def test_parses_meta_table(self) -> None:
        """Should parse meta share table from HTML."""
        html = load_fixture("pokekameshi_meta_report.html")

        client = PokekameshiClient()
        with patch.object(client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = html
            result = await client.fetch_meta_percentages()
            await client.close()

        assert isinstance(result, PokekameshiMetaReport)
        assert result.total_entries == 256
        assert len(result.shares) >= 3

        charizard = next(
            (s for s in result.shares if "リザードン" in s.archetype_name), None
        )
        assert charizard is not None
        assert charizard.share_rate == pytest.approx(0.203, rel=0.01)
        assert charizard.count == 52

        gardevoir = next(
            (s for s in result.shares if "サーナイト" in s.archetype_name), None
        )
        assert gardevoir is not None
        assert gardevoir.share_rate == pytest.approx(0.16, rel=0.01)
        assert gardevoir.count == 41

    @pytest.mark.asyncio
    async def test_extracts_event_name(self) -> None:
        """Should extract event name from page."""
        html = load_fixture("pokekameshi_meta_report.html")

        client = PokekameshiClient()
        with patch.object(client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = html
            result = await client.fetch_meta_percentages()
            await client.close()

        assert result.event_name is not None
        assert "シティリーグ" in result.event_name

    @pytest.mark.asyncio
    async def test_extracts_participant_count(self) -> None:
        """Should extract total participant count."""
        html = load_fixture("pokekameshi_meta_report.html")

        client = PokekameshiClient()
        with patch.object(client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = html
            result = await client.fetch_meta_percentages()
            await client.close()

        assert result.total_entries == 256


class TestPokekameshiClientRateLimiting:
    """Tests for rate limiting behavior."""

    def test_default_rate_limit(self) -> None:
        """Should have conservative rate limit."""
        client = PokekameshiClient()
        assert client._requests_per_minute == 10

    def test_custom_rate_limit(self) -> None:
        """Should allow custom rate limit."""
        client = PokekameshiClient(requests_per_minute=5)
        assert client._requests_per_minute == 5


class TestPokekameshiClientErrors:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_raises_error_on_404(self) -> None:
        """Should raise PokekameshiError on 404."""
        client = PokekameshiClient()

        async def mock_get_404(*args, **kwargs):
            import httpx

            response = httpx.Response(404, request=httpx.Request("GET", "/test"))
            raise httpx.HTTPStatusError(
                "Not Found", request=response.request, response=response
            )

        with (
            patch.object(client._client, "get", side_effect=mock_get_404),
            pytest.raises(PokekameshiError, match="Not found"),
        ):
            await client._get("/nonexistent")

        await client.close()


class TestPokekameshiClientContextManager:
    """Tests for async context manager."""

    @pytest.mark.asyncio
    async def test_context_manager(self) -> None:
        """Should work as async context manager."""
        async with PokekameshiClient() as client:
            assert client is not None
            assert client._client is not None
