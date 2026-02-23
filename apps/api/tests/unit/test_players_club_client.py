"""Unit tests for PlayersClubClient."""

from datetime import date
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from src.clients.players_club import (
    _DECK_CODE_RE,
    _PLAYER_ID_RE,
    PlayersClubClient,
    PlayersClubError,
)


@pytest.fixture
def client():
    return PlayersClubClient(
        timeout=5.0,
        max_retries=2,
        retry_delay=0.01,
        requests_per_minute=100,
    )


# --- Sample HTML fixtures ---

EVENT_LIST_HTML = """
<html><body>
<div class="event-list-item">
  <a href="/event/detail/12345/result">
    <h3 class="event-list-item__name">Tokyo City League</h3>
  </a>
  <span class="event-list-item__date">2026/02/15</span>
  <span class="event-list-item__type">シティリーグ</span>
  <span class="event-list-item__prefecture">東京都</span>
</div>
<div class="event-list-item">
  <a href="/event/detail/12346/result">
    <h3 class="event-list-item__name">Osaka Gym Battle</h3>
  </a>
  <span class="event-list-item__date">2026/02/14</span>
  <span class="event-list-item__type">ジムバトル</span>
  <span class="event-list-item__prefecture">大阪府</span>
</div>
</body></html>
"""

EVENT_LIST_PAGE2_HTML = """
<html><body>
<div class="event-list-item">
  <a href="/event/detail/12347/result">
    <h3 class="event-list-item__name">Nagoya City League</h3>
  </a>
  <span class="event-list-item__date">2026/02/13</span>
  <span class="event-list-item__type">シティリーグ</span>
</div>
</body></html>
"""

EMPTY_EVENT_LIST_HTML = """
<html><body>
<div class="event-result-list">
  <p>結果はありません</p>
</div>
</body></html>
"""

EVENT_DETAIL_HTML = """
<html><body>
<h1 class="event-detail__name">Tokyo City League</h1>
<span class="event-detail__date">2026/02/15</span>
<table class="c-rankTable">
  <tr>
    <th>順位</th><th>ユーザー名</th><th>エリア</th><th>デッキ</th>
  </tr>
  <tr>
    <td>1</td>
    <td>
      <span class="player-name">Taro</span>
      プレイヤーID：1234567890
    </td>
    <td>東京都</td>
    <td><a href="https://pokemon-card.com/deck/confirm.html/deckID/abc-123">デッキ</a></td>
  </tr>
  <tr>
    <td>2</td>
    <td>
      <span class="player-name">Jiro</span>
      プレイヤーID：0987654321
    </td>
    <td>神奈川県</td>
    <td><a href="https://pokemon-card.com/deck/confirm.html/deckID/def-456">デッキ</a></td>
  </tr>
  <tr>
    <td>3</td>
    <td>
      <span class="player-name">Saburo</span>
    </td>
    <td>千葉県</td>
    <td></td>
  </tr>
</table>
</body></html>
"""


class TestFetchEventList:
    @pytest.mark.asyncio
    async def test_parse_event_list_html(self, client):
        with patch.object(
            client,
            "_get_rendered",
            new_callable=AsyncMock,
            side_effect=[EVENT_LIST_HTML, EMPTY_EVENT_LIST_HTML],
        ):
            tournaments = await client.fetch_event_list(days=30)

        assert len(tournaments) == 2
        assert tournaments[0].tournament_id == "12345"
        assert tournaments[0].name == "Tokyo City League"
        assert tournaments[0].date == date(2026, 2, 15)
        assert tournaments[0].event_type == "シティリーグ"
        assert tournaments[0].prefecture == "東京都"
        assert tournaments[0].source_url == (
            "https://players.pokemon-card.com/event/detail/12345/result"
        )

        assert tournaments[1].tournament_id == "12346"
        assert tournaments[1].name == "Osaka Gym Battle"
        assert tournaments[1].event_type == "ジムバトル"

    @pytest.mark.asyncio
    async def test_empty_event_list(self, client):
        with patch.object(
            client,
            "_get_rendered",
            new_callable=AsyncMock,
            return_value=EMPTY_EVENT_LIST_HTML,
        ):
            tournaments = await client.fetch_event_list(days=30)

        assert tournaments == []

    @pytest.mark.asyncio
    async def test_pagination(self, client):
        with patch.object(
            client,
            "_get_rendered",
            new_callable=AsyncMock,
            side_effect=[
                EVENT_LIST_HTML,
                EVENT_LIST_PAGE2_HTML,
                EMPTY_EVENT_LIST_HTML,
            ],
        ):
            tournaments = await client.fetch_event_list(days=30, max_pages=3)

        assert len(tournaments) == 3
        assert tournaments[2].tournament_id == "12347"
        assert tournaments[2].name == "Nagoya City League"

    @pytest.mark.asyncio
    async def test_event_type_filtering(self, client):
        with patch.object(
            client,
            "_get_rendered",
            new_callable=AsyncMock,
            side_effect=[EVENT_LIST_HTML, EMPTY_EVENT_LIST_HTML],
        ):
            tournaments = await client.fetch_event_list(
                days=30,
                event_types=["シティリーグ"],
            )

        assert len(tournaments) == 1
        assert tournaments[0].name == "Tokyo City League"

    @pytest.mark.asyncio
    async def test_render_error_on_first_page_raises(self, client):
        with (
            patch.object(
                client,
                "_get_rendered",
                new_callable=AsyncMock,
                side_effect=PlayersClubError("Render failed"),
            ),
            pytest.raises(PlayersClubError),
        ):
            await client.fetch_event_list(days=30)

    @pytest.mark.asyncio
    async def test_render_error_on_later_page_stops(self, client):
        with patch.object(
            client,
            "_get_rendered",
            new_callable=AsyncMock,
            side_effect=[
                EVENT_LIST_HTML,
                PlayersClubError("No more pages"),
            ],
        ):
            tournaments = await client.fetch_event_list(days=30, max_pages=3)

        assert len(tournaments) == 2

    @pytest.mark.asyncio
    async def test_date_cutoff(self, client):
        old_html = """
        <html><body>
        <div class="event-list-item">
          <a href="/event/detail/99999/result">
            <h3 class="event-list-item__name">Old Event</h3>
          </a>
          <span class="event-list-item__date">2020/01/01</span>
        </div>
        </body></html>
        """
        with patch.object(
            client,
            "_get_rendered",
            new_callable=AsyncMock,
            return_value=old_html,
        ):
            tournaments = await client.fetch_event_list(days=30)

        assert tournaments == []


class TestFetchEventDetail:
    @pytest.mark.asyncio
    async def test_parse_event_detail_html(self, client):
        with patch.object(
            client,
            "_get_rendered",
            new_callable=AsyncMock,
            return_value=EVENT_DETAIL_HTML,
        ):
            detail = await client.fetch_event_detail("12345")

        assert detail.tournament.tournament_id == "12345"
        assert detail.tournament.name == "Tokyo City League"
        assert detail.tournament.date == date(2026, 2, 15)
        assert len(detail.placements) == 3

        p1 = detail.placements[0]
        assert p1.placement == 1
        assert p1.player_name == "Taro"
        assert p1.player_id == "1234567890"
        assert p1.prefecture == "東京都"
        assert p1.deck_code == "abc-123"

        p2 = detail.placements[1]
        assert p2.placement == 2
        assert p2.player_name == "Jiro"
        assert p2.player_id == "0987654321"
        assert p2.deck_code == "def-456"

        p3 = detail.placements[2]
        assert p3.placement == 3
        assert p3.player_name == "Saburo"
        assert p3.deck_code is None

    @pytest.mark.asyncio
    async def test_empty_rank_table(self, client):
        html = """
        <html><body>
        <h1 class="event-detail__name">Empty Event</h1>
        <span class="event-detail__date">2026/02/15</span>
        <table class="c-rankTable">
          <tr><th>順位</th><th>ユーザー名</th></tr>
        </table>
        </body></html>
        """
        with patch.object(
            client,
            "_get_rendered",
            new_callable=AsyncMock,
            return_value=html,
        ):
            detail = await client.fetch_event_detail("12345")

        assert detail.placements == []

    @pytest.mark.asyncio
    async def test_no_rank_table(self, client):
        html = """
        <html><body>
        <h1>Event Without Results</h1>
        <span class="event-detail__date">2026/02/15</span>
        </body></html>
        """
        with patch.object(
            client,
            "_get_rendered",
            new_callable=AsyncMock,
            return_value=html,
        ):
            detail = await client.fetch_event_detail("12345")

        assert detail.placements == []


class TestPlayerIdExtraction:
    def test_standard_format(self):
        match = _PLAYER_ID_RE.search("プレイヤーID：1234567890")
        assert match is not None
        assert match.group(1) == "1234567890"

    def test_colon_format(self):
        match = _PLAYER_ID_RE.search("プレイヤーID:9876543210")
        assert match is not None
        assert match.group(1) == "9876543210"

    def test_with_space(self):
        match = _PLAYER_ID_RE.search("プレイヤーID 1234567890")
        assert match is not None
        assert match.group(1) == "1234567890"

    def test_no_match(self):
        match = _PLAYER_ID_RE.search("No player ID here")
        assert match is None


class TestDeckCodeExtraction:
    def test_deck_url(self):
        match = _DECK_CODE_RE.search(
            "https://pokemon-card.com/deck/confirm.html/deckID/abc-123"
        )
        assert match is not None
        assert match.group(1) == "abc-123"

    def test_no_match(self):
        match = _DECK_CODE_RE.search("https://example.com")
        assert match is None


class TestRetryBehavior:
    @pytest.mark.asyncio
    async def test_retry_on_transient_error(self, client):
        error_response = httpx.Response(
            503,
            request=httpx.Request("GET", "http://test"),
        )
        ok_response = httpx.Response(
            200,
            json={"results": []},
            request=httpx.Request("GET", "http://test"),
        )

        mock_get = AsyncMock(
            side_effect=[error_response, ok_response],
        )

        with patch.object(client._client, "get", mock_get):
            response = await client._get("/test")

        assert response.status_code == 200
        assert mock_get.call_count == 2

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, client):
        error_response = httpx.Response(
            503,
            request=httpx.Request("GET", "http://test"),
        )

        mock_get = AsyncMock(
            return_value=error_response,
        )

        with (
            patch.object(client._client, "get", mock_get),
            pytest.raises(
                PlayersClubError,
                match="Max retries exceeded",
            ),
        ):
            await client._get("/test")

    @pytest.mark.asyncio
    async def test_404_raises_error(self, client):
        mock_response = httpx.Response(
            404,
            request=httpx.Request("GET", "http://test"),
        )

        with (
            patch.object(
                client._client,
                "get",
                new_callable=AsyncMock,
                return_value=mock_response,
            ),
            pytest.raises(
                PlayersClubError,
                match="Not found",
            ),
        ):
            await client._get("/missing")


class TestRateLimiting:
    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        rate_limited_client = PlayersClubClient(
            requests_per_minute=2,
            retry_delay=0.01,
        )

        mock_response = httpx.Response(
            200,
            json={},
            request=httpx.Request("GET", "http://test"),
        )

        call_count = 0

        async def mock_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return mock_response

        with patch.object(
            rate_limited_client._client,
            "get",
            side_effect=mock_get,
        ):
            await rate_limited_client._get("/test1")
            await rate_limited_client._get("/test2")

        assert call_count == 2
        await rate_limited_client.close()


class TestParsing:
    def test_parse_date_formats(self, client):
        assert client._parse_date("2026-02-01") == date(2026, 2, 1)
        assert client._parse_date("2026/02/01") == date(2026, 2, 1)
        assert client._parse_date("2026年02月01日") == date(2026, 2, 1)
        assert client._parse_date("invalid") is None

    def test_parse_event_list_item_no_link(self, client):
        from bs4 import BeautifulSoup

        html = '<div class="event-list-item"><span>No link</span></div>'
        soup = BeautifulSoup(html, "html.parser")
        item = soup.select_one(".event-list-item")
        result = client._parse_event_list_item(item)
        assert result is None

    def test_parse_event_list_item_no_date(self, client):
        from bs4 import BeautifulSoup

        html = """
        <div class="event-list-item">
          <a href="/event/detail/123/result">Test</a>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        item = soup.select_one(".event-list-item")
        result = client._parse_event_list_item(item)
        assert result is None

    def test_extract_league_master(self, client):
        from bs4 import BeautifulSoup

        html = "<div>マスターリーグ</div>"
        soup = BeautifulSoup(html, "html.parser")
        assert client._extract_league(soup.div) == "Master"

    def test_extract_league_none(self, client):
        from bs4 import BeautifulSoup

        html = "<div>Some event</div>"
        soup = BeautifulSoup(html, "html.parser")
        assert client._extract_league(soup.div) is None


class TestContextManager:
    @pytest.mark.asyncio
    async def test_context_manager(self):
        async with PlayersClubClient() as client:
            assert client is not None
            assert isinstance(client._client, httpx.AsyncClient)
