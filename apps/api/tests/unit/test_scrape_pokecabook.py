"""Tests for Pokecabook discovery pipeline."""

from datetime import date
from unittest.mock import AsyncMock, patch

import pytest

from src.clients.pokecabook import (
    PokecabookArticle,
    PokecabookClient,
    PokecabookError,
)
from src.pipelines.ingest_jp_tournament_articles import (
    IngestArticleResult,
)
from src.pipelines.scrape_pokecabook import (
    _is_tournament_article,
    discover_pokecabook_tournaments,
)


def _make_article(
    title: str,
    url: str = "https://pokecabook.com/test",
    published_date: date | None = None,
) -> PokecabookArticle:
    return PokecabookArticle(
        url=url,
        title=title,
        published_date=published_date or date(2026, 2, 15),
    )


class TestIsTournamentArticle:
    def test_matches_tournament_keywords(self):
        assert _is_tournament_article("シティリーグ 結果")
        assert _is_tournament_article("CL 東京 優勝デッキ")
        assert _is_tournament_article("ジムバトル 入賞デッキ")
        assert _is_tournament_article("チャンピオンズリーグ結果")
        assert _is_tournament_article("トレーナーズリーグ結果")

    def test_rejects_non_tournament(self):
        assert not _is_tournament_article("新カード紹介")
        assert not _is_tournament_article("デッキ構築ガイド")
        assert not _is_tournament_article("ポケモン最新ニュース")


class TestDiscoverPokecabookTournaments:
    @pytest.mark.asyncio
    async def test_discover_happy_path(self):
        articles = [
            _make_article("シティリーグ 結果まとめ"),
            _make_article("新カード紹介"),
            _make_article("CL 東京 優勝デッキ"),
        ]

        ingest_result = IngestArticleResult(
            tournament_created=True,
            placements_created=8,
        )

        with (
            patch(
                "src.pipelines.scrape_pokecabook.PokecabookClient"
            ) as mock_client_cls,
            patch(
                "src.pipelines.scrape_pokecabook.ingest_jp_tournament_article",
                new_callable=AsyncMock,
                return_value=ingest_result,
            ) as mock_ingest,
        ):
            mock_client = AsyncMock()
            mock_client.fetch_recent_articles = AsyncMock(
                return_value=articles,
            )
            mock_client_cls.return_value.__aenter__ = AsyncMock(
                return_value=mock_client,
            )
            mock_client_cls.return_value.__aexit__ = AsyncMock(
                return_value=False,
            )

            result = await discover_pokecabook_tournaments(
                lookback_days=14,
            )

        assert result.articles_discovered == 3
        assert result.articles_filtered == 2
        assert result.tournaments_created == 2
        assert result.placements_created == 16
        assert result.success is True
        assert mock_ingest.call_count == 2

    @pytest.mark.asyncio
    async def test_filter_non_tournament_articles(self):
        articles = [
            _make_article("新カード紹介"),
            _make_article("デッキ構築ガイド"),
        ]

        with patch(
            "src.pipelines.scrape_pokecabook.PokecabookClient"
        ) as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.fetch_recent_articles = AsyncMock(
                return_value=articles,
            )
            mock_client_cls.return_value.__aenter__ = AsyncMock(
                return_value=mock_client,
            )
            mock_client_cls.return_value.__aexit__ = AsyncMock(
                return_value=False,
            )

            result = await discover_pokecabook_tournaments()

        assert result.articles_discovered == 2
        assert result.articles_filtered == 0
        assert result.tournaments_created == 0
        assert result.success is True

    @pytest.mark.asyncio
    async def test_dedup_skips_existing(self):
        articles = [
            _make_article("シティリーグ 結果まとめ"),
        ]

        ingest_result = IngestArticleResult(
            tournament_created=False,
            errors=["Tournament already exists: test"],
        )

        with (
            patch(
                "src.pipelines.scrape_pokecabook.PokecabookClient"
            ) as mock_client_cls,
            patch(
                "src.pipelines.scrape_pokecabook.ingest_jp_tournament_article",
                new_callable=AsyncMock,
                return_value=ingest_result,
            ),
        ):
            mock_client = AsyncMock()
            mock_client.fetch_recent_articles = AsyncMock(
                return_value=articles,
            )
            mock_client_cls.return_value.__aenter__ = AsyncMock(
                return_value=mock_client,
            )
            mock_client_cls.return_value.__aexit__ = AsyncMock(
                return_value=False,
            )

            result = await discover_pokecabook_tournaments()

        assert result.tournaments_skipped == 1
        assert result.tournaments_created == 0
        # "already exists" errors are debug-logged, not added
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_dry_run_skips_ingestion(self):
        articles = [
            _make_article("シティリーグ 結果まとめ"),
        ]

        with (
            patch(
                "src.pipelines.scrape_pokecabook.PokecabookClient"
            ) as mock_client_cls,
            patch(
                "src.pipelines.scrape_pokecabook.ingest_jp_tournament_article",
                new_callable=AsyncMock,
            ) as mock_ingest,
        ):
            mock_client = AsyncMock()
            mock_client.fetch_recent_articles = AsyncMock(
                return_value=articles,
            )
            mock_client_cls.return_value.__aenter__ = AsyncMock(
                return_value=mock_client,
            )
            mock_client_cls.return_value.__aexit__ = AsyncMock(
                return_value=False,
            )

            result = await discover_pokecabook_tournaments(
                dry_run=True,
            )

        assert result.articles_discovered == 1
        assert result.articles_filtered == 1
        assert result.tournaments_created == 0
        mock_ingest.assert_not_called()

    @pytest.mark.asyncio
    async def test_fetch_error_returns_error(self):
        with patch(
            "src.pipelines.scrape_pokecabook.PokecabookClient"
        ) as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.fetch_recent_articles = AsyncMock(
                side_effect=PokecabookError("Connection failed"),
            )
            mock_client_cls.return_value.__aenter__ = AsyncMock(
                return_value=mock_client,
            )
            mock_client_cls.return_value.__aexit__ = AsyncMock(
                return_value=False,
            )

            result = await discover_pokecabook_tournaments()

        assert result.success is False
        assert len(result.errors) == 1
        assert "Failed to fetch articles" in result.errors[0]

    @pytest.mark.asyncio
    async def test_empty_results(self):
        with patch(
            "src.pipelines.scrape_pokecabook.PokecabookClient"
        ) as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.fetch_recent_articles = AsyncMock(
                return_value=[],
            )
            mock_client_cls.return_value.__aenter__ = AsyncMock(
                return_value=mock_client,
            )
            mock_client_cls.return_value.__aexit__ = AsyncMock(
                return_value=False,
            )

            result = await discover_pokecabook_tournaments()

        assert result.articles_discovered == 0
        assert result.articles_filtered == 0
        assert result.tournaments_created == 0
        assert result.success is True

    @pytest.mark.asyncio
    async def test_article_without_date_skipped(self):
        articles = [
            _make_article(
                "シティリーグ 結果",
                published_date=None,
            ),
        ]
        # Override to have None date
        articles[0].published_date = None

        with (
            patch(
                "src.pipelines.scrape_pokecabook.PokecabookClient"
            ) as mock_client_cls,
            patch(
                "src.pipelines.scrape_pokecabook.ingest_jp_tournament_article",
                new_callable=AsyncMock,
            ) as mock_ingest,
        ):
            mock_client = AsyncMock()
            mock_client.fetch_recent_articles = AsyncMock(
                return_value=articles,
            )
            mock_client_cls.return_value.__aenter__ = AsyncMock(
                return_value=mock_client,
            )
            mock_client_cls.return_value.__aexit__ = AsyncMock(
                return_value=False,
            )

            result = await discover_pokecabook_tournaments()

        assert result.tournaments_skipped == 1
        assert result.tournaments_created == 0
        mock_ingest.assert_not_called()


class TestPokecabookRenderedFetch:
    @pytest.mark.asyncio
    async def test_get_rendered_calls_kernel_browser(self):
        """_get_rendered delegates to KernelBrowser.fetch_rendered."""
        with patch("src.clients.pokecabook.KernelBrowser") as mock_kb_cls:
            mock_kb = AsyncMock()
            mock_kb.fetch_rendered = AsyncMock(return_value="<html>Rendered</html>")
            mock_kb_cls.return_value.__aenter__ = AsyncMock(return_value=mock_kb)
            mock_kb_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            client = PokecabookClient()
            # Bypass rate limiting for test
            client._wait_for_rate_limit = AsyncMock()

            html = await client._get_rendered("/test/")

        assert html == "<html>Rendered</html>"
        mock_kb.fetch_rendered.assert_awaited_once_with(
            "https://pokecabook.com/test/",
            wait_selector=None,
        )

    @pytest.mark.asyncio
    async def test_get_rendered_with_selector(self):
        with patch("src.clients.pokecabook.KernelBrowser") as mock_kb_cls:
            mock_kb = AsyncMock()
            mock_kb.fetch_rendered = AsyncMock(return_value="<html>OK</html>")
            mock_kb_cls.return_value.__aenter__ = AsyncMock(return_value=mock_kb)
            mock_kb_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            client = PokecabookClient()
            client._wait_for_rate_limit = AsyncMock()

            await client._get_rendered("/tier/", wait_selector=".tier-section")

        mock_kb.fetch_rendered.assert_awaited_once_with(
            "https://pokecabook.com/tier/",
            wait_selector=".tier-section",
        )

    @pytest.mark.asyncio
    async def test_get_rendered_wraps_kernel_error(self):
        from src.clients.kernel_browser import KernelBrowserError

        with patch("src.clients.pokecabook.KernelBrowser") as mock_kb_cls:
            mock_kb = AsyncMock()
            mock_kb.fetch_rendered = AsyncMock(
                side_effect=KernelBrowserError("Browser failed")
            )
            mock_kb_cls.return_value.__aenter__ = AsyncMock(return_value=mock_kb)
            mock_kb_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            client = PokecabookClient()
            client._wait_for_rate_limit = AsyncMock()

            with pytest.raises(PokecabookError, match="Rendered fetch failed"):
                await client._get_rendered("/test/")

    @pytest.mark.asyncio
    async def test_fetch_article_detail_rendered(self):
        """fetch_article_detail(rendered=True) uses _get_rendered."""
        with patch("src.clients.pokecabook.KernelBrowser") as mock_kb_cls:
            mock_kb = AsyncMock()
            mock_kb.fetch_rendered = AsyncMock(
                return_value=(
                    "<html><head><title>Test</title></head>"
                    "<body><h1>Article Title</h1></body></html>"
                )
            )
            mock_kb_cls.return_value.__aenter__ = AsyncMock(return_value=mock_kb)
            mock_kb_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            client = PokecabookClient()
            client._wait_for_rate_limit = AsyncMock()

            article = await client.fetch_article_detail(
                "https://pokecabook.com/article/123",
                rendered=True,
            )

        assert article.title == "Article Title"
        assert article.raw_html is not None
        mock_kb.fetch_rendered.assert_awaited_once()
