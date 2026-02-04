"""Tests for Pokecabook scraper client."""

from datetime import date
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from src.clients.pokecabook import (
    PokecabookAdoptionRates,
    PokecabookArticle,
    PokecabookClient,
    PokecabookError,
    PokecabookTierList,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> str:
    """Load an HTML fixture file."""
    return (FIXTURES_DIR / name).read_text()


class TestPokecabookTierList:
    """Tests for tier list parsing."""

    @pytest.mark.asyncio
    async def test_parses_tier_table(self) -> None:
        """Should parse tier table from HTML."""
        html = load_fixture("pokecabook_tier_list.html")

        client = PokecabookClient()
        with patch.object(client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = html
            result = await client.fetch_tier_list()
            await client.close()

        assert isinstance(result, PokecabookTierList)
        assert len(result.entries) >= 3

        charizard = next(
            (e for e in result.entries if "リザードン" in e.archetype_name), None
        )
        assert charizard is not None
        assert charizard.tier == "S"
        assert charizard.usage_rate == pytest.approx(0.185, rel=0.01)

        gardevoir = next(
            (e for e in result.entries if "サーナイト" in e.archetype_name), None
        )
        assert gardevoir is not None
        assert gardevoir.tier == "S"

        dragapult = next(
            (e for e in result.entries if "ドラパルト" in e.archetype_name), None
        )
        assert dragapult is not None
        assert dragapult.tier == "A"

    @pytest.mark.asyncio
    async def test_includes_source_url(self) -> None:
        """Should include source URL in result."""
        html = load_fixture("pokecabook_tier_list.html")

        client = PokecabookClient()
        with patch.object(client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = html
            result = await client.fetch_tier_list()
            await client.close()

        assert result.source_url is not None
        assert "pokecabook.com" in result.source_url

    @pytest.mark.asyncio
    async def test_stores_raw_html(self) -> None:
        """Should store raw HTML for re-parsing."""
        html = load_fixture("pokecabook_tier_list.html")

        client = PokecabookClient()
        with patch.object(client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = html
            result = await client.fetch_tier_list()
            await client.close()

        assert result.raw_html is not None
        assert "リザードン" in result.raw_html


class TestPokecabookArticles:
    """Tests for article fetching."""

    @pytest.mark.asyncio
    async def test_parses_article_list(self) -> None:
        """Should parse article list from HTML."""
        html = load_fixture("pokecabook_article_list.html")

        client = PokecabookClient()
        with patch.object(client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = html
            result = await client.fetch_recent_articles(days=365)
            await client.close()

        assert len(result) >= 2

        charizard_guide = next(
            (a for a in result if "リザードン" in a.title), None
        )
        assert charizard_guide is not None
        assert charizard_guide.published_date == date(2026, 2, 1)
        assert charizard_guide.category == "デッキ解説"

    @pytest.mark.asyncio
    async def test_filters_by_date(self) -> None:
        """Should filter articles by date."""
        html = load_fixture("pokecabook_article_list.html")

        client = PokecabookClient()
        with patch.object(client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = html
            result = await client.fetch_recent_articles(days=3)
            await client.close()

        for article in result:
            if article.published_date:
                delta = date.today() - article.published_date
                assert delta.days <= 3 or delta.days < 0

    @pytest.mark.asyncio
    async def test_article_has_url(self) -> None:
        """Should include URL for each article."""
        html = load_fixture("pokecabook_article_list.html")

        client = PokecabookClient()
        with patch.object(client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = html
            result = await client.fetch_recent_articles(days=365)
            await client.close()

        for article in result:
            assert article.url is not None
            assert article.url.startswith("http")


class TestPokecabookAdoptionRates:
    """Tests for card adoption rate parsing."""

    @pytest.mark.asyncio
    async def test_parses_adoption_table(self) -> None:
        """Should parse adoption rate table from HTML."""
        html = load_fixture("pokecabook_adoption_rates.html")

        client = PokecabookClient()
        with patch.object(client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = html
            result = await client.fetch_adoption_rates()
            await client.close()

        assert isinstance(result, PokecabookAdoptionRates)
        assert len(result.entries) >= 3

        boss_orders = next(
            (e for e in result.entries if "ボスの指令" in e.card_name_jp), None
        )
        assert boss_orders is not None
        assert boss_orders.inclusion_rate == pytest.approx(0.925, rel=0.01)
        assert boss_orders.avg_copies == pytest.approx(2.1, rel=0.1)

        nest_ball = next(
            (e for e in result.entries if "ネストボール" in e.card_name_jp), None
        )
        assert nest_ball is not None
        assert nest_ball.inclusion_rate == pytest.approx(0.88, rel=0.01)
        assert nest_ball.avg_copies == pytest.approx(3.8, rel=0.1)


class TestPokecabookClientRateLimiting:
    """Tests for rate limiting behavior."""

    def test_default_rate_limit(self) -> None:
        """Should have conservative rate limit."""
        client = PokecabookClient()
        assert client._requests_per_minute == 10

    def test_custom_rate_limit(self) -> None:
        """Should allow custom rate limit."""
        client = PokecabookClient(requests_per_minute=5)
        assert client._requests_per_minute == 5


class TestPokecabookClientErrors:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_raises_error_on_404(self) -> None:
        """Should raise PokecabookError on 404."""
        client = PokecabookClient()

        async def mock_get_404(*args, **kwargs):
            import httpx

            response = httpx.Response(404, request=httpx.Request("GET", "/test"))
            raise httpx.HTTPStatusError("Not Found", request=response.request, response=response)

        with patch.object(client._client, "get", side_effect=mock_get_404):
            with pytest.raises(PokecabookError, match="Not found"):
                await client._get("/nonexistent")

        await client.close()
