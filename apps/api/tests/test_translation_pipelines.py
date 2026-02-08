"""Tests for translation pipeline modules."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.pipelines.monitor_card_reveals import (
    MonitorCardRevealsResult,
    _estimate_impact,
    _should_update,
    check_card_reveals,
)
from src.pipelines.sync_jp_adoption_rates import (
    SyncAdoptionRatesResult,
    _generate_card_id,
    sync_adoption_rates,
)
from src.pipelines.translate_pokecabook import (
    TranslatePokecabookResult,
    _extract_article_text,
    _format_tier_list_text,
    _url_to_source_id,
    translate_pokecabook_content,
)
from src.pipelines.translate_tier_lists import (
    TranslateTierListsResult,
    _format_combined_tier_lists,
    translate_tier_lists,
)


class TestTranslatePokecabookHelpers:
    """Tests for Pokecabook translation helpers."""

    def test_extract_article_text_from_article_tag(self) -> None:
        """Should extract text from article element."""
        html = """
        <html>
            <body>
                <nav>Navigation</nav>
                <article>
                    <h1>Title</h1>
                    <p>Article content here.</p>
                </article>
                <footer>Footer</footer>
            </body>
        </html>
        """
        result = _extract_article_text(html)
        assert "Article content here" in result
        assert "Navigation" not in result
        assert "Footer" not in result

    def test_extract_article_text_from_body(self) -> None:
        """Should fall back to body when no article tag."""
        html = """
        <html>
            <body>
                <p>Body content here.</p>
            </body>
        </html>
        """
        result = _extract_article_text(html)
        assert "Body content here" in result

    def test_url_to_source_id(self) -> None:
        """Should generate source ID from URL."""
        url = "https://pokecabook.com/article/2026/02/charizard-guide"
        result = _url_to_source_id(url)
        assert result.startswith("pokecabook-")
        assert "article" in result

    def test_format_tier_list_text(self) -> None:
        """Should format tier list as readable text."""
        tier_list = MagicMock()
        tier_list.date = date(2026, 2, 1)
        tier_list.entries = [
            MagicMock(
                archetype_name="リザードンex",
                tier="S",
                usage_rate=0.18,
                trend="rising",
            ),
            MagicMock(
                archetype_name="サーナイトex",
                tier="S",
                usage_rate=0.15,
                trend="stable",
            ),
            MagicMock(
                archetype_name="ドラパルトex",
                tier="A",
                usage_rate=0.10,
                trend=None,
            ),
        ]

        result = _format_tier_list_text(tier_list)

        assert "Pokecabook Tier List" in result
        assert "2026-02-01" in result
        assert "リザードンex" in result
        assert "18.0%" in result
        assert "【S】" in result
        assert "【A】" in result


class TestSyncAdoptionRatesHelpers:
    """Tests for adoption rate sync helpers."""

    def test_generate_card_id(self) -> None:
        """Should generate stable card IDs."""
        card_id_1 = _generate_card_id("ボスの指令")
        card_id_2 = _generate_card_id("ボスの指令")
        card_id_3 = _generate_card_id("ネストボール")

        assert card_id_1 == card_id_2
        assert card_id_1 != card_id_3
        assert card_id_1.startswith("jp-")


class TestMonitorCardRevealsHelpers:
    """Tests for card reveal monitoring helpers."""

    def test_should_update_new_en_name(self) -> None:
        """Should update when new EN name available."""
        existing = MagicMock()
        existing.name_en = None
        existing.card_type = "Pokemon"
        existing.jp_set_id = "SV10"

        card = MagicMock()
        card.name_en = "Charizard ex"
        card.card_type = "Pokemon"
        card.set_id = "SV10"

        assert _should_update(existing, card)

    def test_should_not_update_when_same(self) -> None:
        """Should not update when data is same."""
        existing = MagicMock()
        existing.name_en = "Charizard ex"
        existing.card_type = "Pokemon"
        existing.jp_set_id = "SV10"

        card = MagicMock()
        card.name_en = "Charizard ex"
        card.card_type = "Pokemon"
        card.set_id = "SV10"

        assert not _should_update(existing, card)

    def test_estimate_impact_ex(self) -> None:
        """Should rate ex Pokemon as high impact."""
        card = MagicMock()
        card.name_jp = "リザードンex"
        card.card_type = "Pokemon"

        assert _estimate_impact(card) == 4

    def test_estimate_impact_default(self) -> None:
        """Should default to medium impact."""
        card = MagicMock()
        card.name_jp = "ピカチュウ"
        card.card_type = "Pokemon"

        assert _estimate_impact(card) == 3


class TestTranslateTierListsHelpers:
    """Tests for tier list translation helpers."""

    def test_format_combined_tier_lists(self) -> None:
        """Should format combined tier list data."""
        pokecabook = MagicMock()
        pokecabook.entries = [
            MagicMock(archetype_name="リザードン", tier="S", usage_rate=0.18)
        ]

        pokekameshi = MagicMock()
        pokekameshi.environment_name = "SV10環境"
        pokekameshi.entries = [
            MagicMock(
                archetype_name="リザードン",
                tier="S",
                share_rate=0.18,
                csp_points=2500,
                deck_power=9.2,
            )
        ]

        result = _format_combined_tier_lists(pokecabook, pokekameshi)

        assert "Pokecabook" in result
        assert "Pokekameshi" in result
        assert "リザードン" in result
        assert "CSP:2500" in result


class TestTranslatePokecabookPipeline:
    """Tests for Pokecabook translation pipeline."""

    @pytest.mark.asyncio
    async def test_dry_run_returns_result(self) -> None:
        """Dry run should not persist but return result."""
        mock_article = MagicMock()
        mock_article.url = "https://pokecabook.com/test"
        mock_article.title = "Test Article"
        mock_article.raw_html = "<article>Test content here for translation.</article>"

        mock_tier_list = MagicMock()
        mock_tier_list.entries = []
        mock_tier_list.source_url = "https://pokecabook.com/tier/"

        with (
            patch("src.pipelines.translate_pokecabook.PokecabookClient") as mock_client,
            patch("src.pipelines.translate_pokecabook.ClaudeClient"),
            patch("src.pipelines.translate_pokecabook.async_session_factory"),
        ):
            mock_pokecabook = AsyncMock()
            mock_pokecabook.fetch_recent_articles = AsyncMock(return_value=[])
            mock_pokecabook.fetch_tier_list = AsyncMock(return_value=mock_tier_list)
            mock_client.return_value.__aenter__ = AsyncMock(
                return_value=mock_pokecabook
            )
            mock_client.return_value.__aexit__ = AsyncMock()

            result = await translate_pokecabook_content(lookback_days=0, dry_run=True)

            assert isinstance(result, TranslatePokecabookResult)
            assert result.success


class TestSyncAdoptionRatesPipeline:
    """Tests for adoption rate sync pipeline."""

    @pytest.mark.asyncio
    async def test_dry_run_returns_result(self) -> None:
        """Dry run should fetch but not persist."""
        mock_adoption = MagicMock()
        mock_adoption.entries = []

        with patch(
            "src.pipelines.sync_jp_adoption_rates.PokecabookClient"
        ) as mock_client:
            mock_pokecabook = AsyncMock()
            mock_pokecabook.fetch_adoption_rates = AsyncMock(return_value=mock_adoption)
            mock_client.return_value.__aenter__ = AsyncMock(
                return_value=mock_pokecabook
            )
            mock_client.return_value.__aexit__ = AsyncMock()

            result = await sync_adoption_rates(dry_run=True)

            assert isinstance(result, SyncAdoptionRatesResult)
            assert result.success


class TestTranslateTierListsPipeline:
    """Tests for tier list translation pipeline."""

    @pytest.mark.asyncio
    async def test_handles_partial_failure(self) -> None:
        """Should continue if one source fails."""
        from contextlib import asynccontextmanager

        from src.clients.pokekameshi import PokekameshiError

        mock_pokecabook_tier = MagicMock()
        mock_pokecabook_tier.entries = [
            MagicMock(archetype_name="リザードン", tier="S", usage_rate=0.18)
        ]

        mock_db_result = MagicMock()
        mock_db_result.scalars.return_value.all.return_value = []
        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_db_result

        @asynccontextmanager
        async def mock_session_cm():
            yield mock_session

        @asynccontextmanager
        async def mock_pokecabook_cm():
            mock_client = AsyncMock()
            mock_client.fetch_tier_list = AsyncMock(return_value=mock_pokecabook_tier)
            yield mock_client

        @asynccontextmanager
        async def mock_pokekameshi_cm():
            mock_client = AsyncMock()
            mock_client.fetch_tier_tables = AsyncMock(
                side_effect=PokekameshiError("Test error")
            )
            yield mock_client

        with (
            patch(
                "src.pipelines.translate_tier_lists.PokecabookClient",
                return_value=mock_pokecabook_cm(),
            ),
            patch(
                "src.pipelines.translate_tier_lists.PokekameshiClient",
                return_value=mock_pokekameshi_cm(),
            ),
            patch("src.pipelines.translate_tier_lists.ClaudeClient"),
            patch(
                "src.pipelines.translate_tier_lists.async_session_factory",
                return_value=mock_session_cm(),
            ),
        ):
            result = await translate_tier_lists(dry_run=True)

            assert isinstance(result, TranslateTierListsResult)
            assert result.pokecabook_entries == 1
            assert len(result.errors) > 0


class TestMonitorCardRevealsPipeline:
    """Tests for card reveal monitoring pipeline."""

    @pytest.mark.asyncio
    async def test_dry_run_returns_result(self) -> None:
        """Dry run should fetch but not persist."""
        from src.clients.limitless import LimitlessJPCard

        mock_cards = [
            LimitlessJPCard(
                card_id="SV10-001",
                name_jp="テストカード",
                name_en="Test Card",
                set_id="SV10",
                card_type="Pokemon",
                is_unreleased=True,
            )
        ]

        with patch("src.pipelines.monitor_card_reveals.LimitlessClient") as mock_client:
            mock_limitless = AsyncMock()
            mock_limitless.fetch_unreleased_cards = AsyncMock(return_value=mock_cards)
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_limitless)
            mock_client.return_value.__aexit__ = AsyncMock()

            result = await check_card_reveals(dry_run=True)

            assert isinstance(result, MonitorCardRevealsResult)
            assert result.cards_checked == 1
            assert result.success
