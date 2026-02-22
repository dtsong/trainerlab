"""Tests for JP tournament article ingestion pipeline."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.clients.pokecabook import (
    PokecabookClient,
    PokecabookDeckEntry,
    PokecabookTournamentArticle,
)
from src.clients.pokekameshi import (
    PokekameshiClient,
    PokekameshiDeckEntry,
    PokekameshiTournamentArticle,
)
from src.pipelines.ingest_jp_tournament_articles import (
    IngestArticleResult,
    _merge_placements,
    ingest_jp_tournament_article,
)

# ─── HTML fixtures ───────────────────────────────────────


POKECABOOK_ARTICLE_HTML = """
<html><body>
<h1 class="entry-title">CL東京2026 結果</h1>
<time class="post-date" datetime="2026-01-15">
  2026年1月15日
</time>
<h2>優勝：ルギアVSTAR</h2>
<p>プレイヤー：田中太郎</p>
<p>
ルギアVSTAR ×4
アーケオス ×4
かがやくリザードン ×1
</p>
<h2>準優勝：パオジアンex</h2>
<p>
パオジアンex ×3
セグレイブ ×4
</p>
<h2>ベスト4：リザードンex</h2>
<p>
リザードンex ×3
ピジョットex ×2
</p>
</body></html>
"""

POKECABOOK_TABLE_HTML = """
<html><body>
<h1>シティリーグ結果</h1>
<table>
<tr><th>順位</th><th>デッキ</th><th>プレイヤー</th></tr>
<tr><td>1位</td><td>ルギアVSTAR</td><td>田中</td></tr>
<tr><td>2位</td><td>パオジアンex</td><td>鈴木</td></tr>
<tr><td>3</td><td>リザードンex</td><td>佐藤</td></tr>
</table>
</body></html>
"""

POKEKAMESHI_ARTICLE_HTML = """
<html><body>
<h1>CL東京2026 メタ分析</h1>
<time class="post-date" datetime="2026-01-15">
  2026年1月15日
</time>
<table>
<tr><th>順位</th><th>デッキ</th><th>シェア率</th></tr>
<tr><td>優勝</td><td>ルギアVSTAR</td><td>15.5%</td></tr>
<tr><td>準優勝</td><td>パオジアンex</td><td>12.3%</td></tr>
</table>
</body></html>
"""

POKEKAMESHI_HEADING_HTML = """
<html><body>
<h1>大会結果まとめ</h1>
<h2>優勝：ルギアVSTAR</h2>
<p>使用率 20.5%</p>
<h2>準優勝：パオジアンex</h2>
<p>使用率 15.0%</p>
</body></html>
"""

EMPTY_ARTICLE_HTML = """
<html><body>
<h1>ニュース記事</h1>
<p>今日の大会は中止になりました。</p>
</body></html>
"""


# ─── Pokecabook client tests ────────────────────────────


class TestPokecabookFetchTournamentArticle:
    """Tests for PokecabookClient.fetch_tournament_article."""

    @pytest.mark.asyncio
    async def test_parses_heading_based_entries(self):
        client = PokecabookClient()
        client._get = AsyncMock(return_value=POKECABOOK_ARTICLE_HTML)

        article = await client.fetch_tournament_article(
            "https://pokecabook.com/tournament/123"
        )

        assert article.title == "CL東京2026 結果"
        assert article.published_date == date(2026, 1, 15)
        assert len(article.deck_entries) == 3

        winner = article.deck_entries[0]
        assert winner.placement == 1
        assert winner.archetype_name == "ルギアVSTAR"
        assert winner.player_name == "田中太郎"
        assert winner.decklist is not None
        assert len(winner.decklist) == 3

        runner_up = article.deck_entries[1]
        assert runner_up.placement == 2
        assert runner_up.archetype_name == "パオジアンex"

        await client.close()

    @pytest.mark.asyncio
    async def test_parses_table_based_entries(self):
        client = PokecabookClient()
        client._get = AsyncMock(return_value=POKECABOOK_TABLE_HTML)

        article = await client.fetch_tournament_article(
            "https://pokecabook.com/tournament/456"
        )

        assert len(article.deck_entries) == 3
        assert article.deck_entries[0].placement == 1
        assert article.deck_entries[0].archetype_name == "ルギアVSTAR"
        assert article.deck_entries[0].player_name == "田中"
        assert article.deck_entries[2].placement == 3

        await client.close()

    @pytest.mark.asyncio
    async def test_empty_article_returns_no_entries(self):
        client = PokecabookClient()
        client._get = AsyncMock(return_value=EMPTY_ARTICLE_HTML)

        article = await client.fetch_tournament_article(
            "https://pokecabook.com/news/789"
        )

        assert article.title == "ニュース記事"
        assert article.deck_entries == []

        await client.close()

    @pytest.mark.asyncio
    async def test_card_list_parsing(self):
        client = PokecabookClient()
        cards = client._parse_card_lines(
            "ルギアVSTAR ×4\nアーケオス ×4\nかがやくリザードン ×1"
        )

        assert len(cards) == 3
        assert cards[0] == {
            "card_name": "ルギアVSTAR",
            "count": 4,
        }
        assert cards[2] == {
            "card_name": "かがやくリザードン",
            "count": 1,
        }

        await client.close()

    @pytest.mark.asyncio
    async def test_card_list_count_first_format(self):
        client = PokecabookClient()
        cards = client._parse_card_lines("4枚 ルギアVSTAR\n1 かがやくリザードン")

        assert len(cards) == 2
        assert cards[0] == {
            "card_name": "ルギアVSTAR",
            "count": 4,
        }

        await client.close()


# ─── Pokekameshi client tests ───────────────────────────


class TestPokekameshiFetchTournamentArticle:
    """Tests for PokekameshiClient.fetch_tournament_article."""

    @pytest.mark.asyncio
    async def test_parses_table_based_entries(self):
        client = PokekameshiClient()
        client._get = AsyncMock(return_value=POKEKAMESHI_ARTICLE_HTML)

        article = await client.fetch_tournament_article(
            "https://pokekameshi.com/tournament/123"
        )

        assert article.title == "CL東京2026 メタ分析"
        assert len(article.deck_entries) == 2

        winner = article.deck_entries[0]
        assert winner.placement == 1
        assert winner.archetype_name == "ルギアVSTAR"
        assert winner.meta_share == pytest.approx(0.155, abs=0.001)

        await client.close()

    @pytest.mark.asyncio
    async def test_parses_heading_based_entries(self):
        client = PokekameshiClient()
        client._get = AsyncMock(return_value=POKEKAMESHI_HEADING_HTML)

        article = await client.fetch_tournament_article(
            "https://pokekameshi.com/article/456"
        )

        assert len(article.deck_entries) == 2
        assert article.deck_entries[0].placement == 1
        assert article.deck_entries[0].archetype_name == "ルギアVSTAR"
        assert article.deck_entries[0].meta_share == (pytest.approx(0.205, abs=0.001))

        await client.close()

    @pytest.mark.asyncio
    async def test_empty_article_returns_no_entries(self):
        client = PokekameshiClient()
        client._get = AsyncMock(return_value=EMPTY_ARTICLE_HTML)

        article = await client.fetch_tournament_article(
            "https://pokekameshi.com/news/789"
        )

        assert article.deck_entries == []

        await client.close()


# ─── _merge_placements tests ────────────────────────────


class TestMergePlacements:
    """Tests for the _merge_placements helper."""

    def test_pokecabook_only(self):
        pokecabook = PokecabookTournamentArticle(
            title="Test",
            url="https://pokecabook.com/test",
            deck_entries=[
                PokecabookDeckEntry(
                    placement=1,
                    archetype_name="ルギアVSTAR",
                    player_name="田中",
                    decklist=[{"card_name": "ルギア", "count": 4}],
                ),
                PokecabookDeckEntry(
                    placement=2,
                    archetype_name="パオジアンex",
                ),
            ],
        )
        result = _merge_placements(pokecabook, None)

        assert len(result) == 2
        assert result[0]["placement"] == 1
        assert result[0]["archetype"] == "ルギアVSTAR"
        assert result[0]["player_name"] == "田中"
        assert result[0]["decklist"] is not None

    def test_pokekameshi_only(self):
        pokekameshi = PokekameshiTournamentArticle(
            title="Test",
            url="https://pokekameshi.com/test",
            deck_entries=[
                PokekameshiDeckEntry(
                    placement=1,
                    archetype_name="ルギアVSTAR",
                    player_name="田中",
                ),
            ],
        )
        result = _merge_placements(None, pokekameshi)

        assert len(result) == 1
        assert result[0]["archetype"] == "ルギアVSTAR"

    def test_pokecabook_overrides_pokekameshi(self):
        pokecabook = PokecabookTournamentArticle(
            title="Test",
            url="https://pokecabook.com/test",
            deck_entries=[
                PokecabookDeckEntry(
                    placement=1,
                    archetype_name="ルギアVSTAR",
                    decklist=[{"card_name": "ルギア", "count": 4}],
                ),
            ],
        )
        pokekameshi = PokekameshiTournamentArticle(
            title="Test",
            url="https://pokekameshi.com/test",
            deck_entries=[
                PokekameshiDeckEntry(
                    placement=1,
                    archetype_name="ルギア",
                    player_name="田中",
                ),
            ],
        )
        result = _merge_placements(pokecabook, pokekameshi)

        assert len(result) == 1
        # Pokecabook archetype wins
        assert result[0]["archetype"] == "ルギアVSTAR"
        # Player name preserved from pokekameshi
        assert result[0]["player_name"] == "田中"
        assert result[0]["decklist"] is not None

    def test_both_none_returns_empty(self):
        result = _merge_placements(None, None)
        assert result == []

    def test_sorted_by_placement(self):
        pokecabook = PokecabookTournamentArticle(
            title="Test",
            url="https://pokecabook.com/test",
            deck_entries=[
                PokecabookDeckEntry(
                    placement=3,
                    archetype_name="C",
                ),
                PokecabookDeckEntry(
                    placement=1,
                    archetype_name="A",
                ),
                PokecabookDeckEntry(
                    placement=2,
                    archetype_name="B",
                ),
            ],
        )
        result = _merge_placements(pokecabook, None)
        placements = [r["placement"] for r in result]
        assert placements == [1, 2, 3]


# ─── Pipeline integration tests ─────────────────────────


class TestIngestJPTournamentArticle:
    """Tests for the main pipeline function."""

    @pytest.mark.asyncio
    @patch("src.pipelines.ingest_jp_tournament_articles.PokecabookClient")
    async def test_dry_run_fetches_but_no_persist(self, mock_client_cls):
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.fetch_tournament_article = AsyncMock(
            return_value=PokecabookTournamentArticle(
                title="Test",
                url="https://pokecabook.com/test",
                deck_entries=[
                    PokecabookDeckEntry(
                        placement=1,
                        archetype_name="ルギア",
                    ),
                ],
            )
        )
        mock_client_cls.return_value = mock_client

        result = await ingest_jp_tournament_article(
            tournament_name="Test Tournament",
            tournament_date=date(2026, 1, 15),
            pokecabook_url="https://pokecabook.com/test",
            dry_run=True,
        )

        assert result.success is True
        assert result.pokecabook_entries == 1
        assert result.tournament_created is False
        assert result.placements_created == 0

    @pytest.mark.asyncio
    async def test_no_urls_returns_error(self):
        result = await ingest_jp_tournament_article(
            tournament_name="Test",
            tournament_date=date(2026, 1, 15),
        )

        assert result.success is False
        assert any("No data fetched" in e for e in result.errors)

    @pytest.mark.asyncio
    @patch("src.pipelines.ingest_jp_tournament_articles.PokecabookClient")
    async def test_fetch_error_recorded(self, mock_client_cls):
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.fetch_tournament_article = AsyncMock(
            side_effect=Exception("Connection timeout")
        )
        mock_client_cls.return_value = mock_client

        result = await ingest_jp_tournament_article(
            tournament_name="Test",
            tournament_date=date(2026, 1, 15),
            pokecabook_url="https://pokecabook.com/test",
        )

        assert result.success is False
        assert any("Pokecabook fetch failed" in e for e in result.errors)

    @pytest.mark.asyncio
    @patch("src.pipelines.ingest_jp_tournament_articles.async_session_factory")
    @patch("src.pipelines.ingest_jp_tournament_articles.ArchetypeNormalizer")
    @patch("src.pipelines.ingest_jp_tournament_articles.PokecabookClient")
    async def test_creates_tournament_and_placements(
        self,
        mock_client_cls,
        mock_normalizer_cls,
        mock_session_factory,
    ):
        # Set up client mock
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.fetch_tournament_article = AsyncMock(
            return_value=PokecabookTournamentArticle(
                title="CL東京",
                url="https://pokecabook.com/cl-tokyo",
                deck_entries=[
                    PokecabookDeckEntry(
                        placement=1,
                        archetype_name="ルギアVSTAR",
                        player_name="田中",
                    ),
                    PokecabookDeckEntry(
                        placement=2,
                        archetype_name="パオジアンex",
                    ),
                ],
            )
        )
        mock_client_cls.return_value = mock_client

        # Set up normalizer mock
        mock_normalizer = MagicMock()
        mock_normalizer.load_db_sprites = AsyncMock()
        mock_normalizer.resolve.return_value = (
            "Lugia VSTAR",
            "ルギアVSTAR",
            "text_label",
        )
        mock_normalizer_cls.return_value = mock_normalizer

        # Set up session mock
        mock_session = AsyncMock()
        mock_execute_result = MagicMock()
        mock_execute_result.first.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_execute_result)
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_session_factory.return_value = mock_ctx

        result = await ingest_jp_tournament_article(
            tournament_name="CL東京",
            tournament_date=date(2026, 1, 15),
            pokecabook_url=("https://pokecabook.com/cl-tokyo"),
        )

        assert result.success is True
        assert result.tournament_created is True
        assert result.placements_created == 2
        assert result.pokecabook_entries == 2
        assert result.tournament_id is not None
        mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("src.pipelines.ingest_jp_tournament_articles.async_session_factory")
    @patch("src.pipelines.ingest_jp_tournament_articles.ArchetypeNormalizer")
    @patch("src.pipelines.ingest_jp_tournament_articles.PokecabookClient")
    async def test_duplicate_tournament_returns_error(
        self,
        mock_client_cls,
        mock_normalizer_cls,
        mock_session_factory,
    ):
        # Set up client mock
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.fetch_tournament_article = AsyncMock(
            return_value=PokecabookTournamentArticle(
                title="CL東京",
                url="https://pokecabook.com/cl-tokyo",
                deck_entries=[
                    PokecabookDeckEntry(
                        placement=1,
                        archetype_name="ルギア",
                    ),
                ],
            )
        )
        mock_client_cls.return_value = mock_client

        # Session returns existing tournament
        mock_session = AsyncMock()
        mock_execute_result = MagicMock()
        mock_execute_result.first.return_value = ("existing-uuid",)
        mock_session.execute = AsyncMock(return_value=mock_execute_result)

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_session_factory.return_value = mock_ctx

        result = await ingest_jp_tournament_article(
            tournament_name="CL東京",
            tournament_date=date(2026, 1, 15),
            pokecabook_url=("https://pokecabook.com/cl-tokyo"),
        )

        assert result.success is False
        assert any("already exists" in e for e in result.errors)
        assert result.tournament_created is False

    @pytest.mark.asyncio
    @patch("src.pipelines.ingest_jp_tournament_articles.PokecabookClient")
    async def test_empty_entries_returns_error(self, mock_client_cls):
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.fetch_tournament_article = AsyncMock(
            return_value=PokecabookTournamentArticle(
                title="Empty",
                url="https://pokecabook.com/empty",
                deck_entries=[],
            )
        )
        mock_client_cls.return_value = mock_client

        result = await ingest_jp_tournament_article(
            tournament_name="Test",
            tournament_date=date(2026, 1, 15),
            pokecabook_url="https://pokecabook.com/empty",
        )

        assert result.success is False
        assert any("No placement data" in e for e in result.errors)


class TestIngestArticleResult:
    """Tests for IngestArticleResult dataclass."""

    def test_success_when_no_errors(self):
        result = IngestArticleResult()
        assert result.success is True

    def test_not_success_when_errors(self):
        result = IngestArticleResult(errors=["Something failed"])
        assert result.success is False
