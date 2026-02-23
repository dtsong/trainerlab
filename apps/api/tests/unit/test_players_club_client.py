"""Unit tests for PlayersClubClient."""

from datetime import date
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from src.clients.players_club import (
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


class TestFetchRecentTournaments:
    @pytest.mark.asyncio
    async def test_fetch_recent_tournaments(self, client):
        mock_response = httpx.Response(
            200,
            json=[
                {
                    "id": "t1",
                    "name": "Tokyo City League",
                    "date": date.today().isoformat(),
                    "prefecture": "Tokyo",
                    "participant_count": 64,
                },
                {
                    "id": "t2",
                    "name": "Osaka City League",
                    "date": date.today().isoformat(),
                    "participant_count": 32,
                },
            ],
            request=httpx.Request("GET", "http://test"),
        )

        with patch.object(
            client._client,
            "get",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            tournaments = await client.fetch_recent_tournaments(
                days=30,
            )

        assert len(tournaments) == 2
        assert tournaments[0].tournament_id == "t1"
        assert tournaments[0].name == "Tokyo City League"
        assert tournaments[0].prefecture == "Tokyo"
        assert tournaments[0].participant_count == 64
        assert tournaments[0].source_url == (
            "https://players.pokemon-card.com/event/t1"
        )

    @pytest.mark.asyncio
    async def test_fetch_tournaments_returns_empty_on_404(self, client):
        mock_response = httpx.Response(
            404,
            request=httpx.Request("GET", "http://test"),
        )

        with patch.object(
            client._client,
            "get",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            tournaments = await client.fetch_recent_tournaments()

        assert tournaments == []

    @pytest.mark.asyncio
    async def test_fetch_tournaments_raises_on_non_404_error(self, client):
        error_response = httpx.Response(
            503,
            request=httpx.Request("GET", "http://test"),
        )

        with (
            patch.object(
                client._client,
                "get",
                new_callable=AsyncMock,
                return_value=error_response,
            ),
            pytest.raises(PlayersClubError),
        ):
            await client.fetch_recent_tournaments()


class TestFetchTournamentDetail:
    @pytest.mark.asyncio
    async def test_fetch_tournament_detail(self, client):
        mock_response = httpx.Response(
            200,
            json={
                "tournament": {
                    "id": "t1",
                    "name": "Tokyo City League",
                    "date": "2026-02-01",
                },
                "results": [
                    {
                        "rank": 1,
                        "player_name": "Taro",
                        "deck_name": "Charizard ex",
                    },
                    {
                        "rank": 2,
                        "player_name": "Jiro",
                        "deck_name": "Lugia VSTAR",
                    },
                ],
            },
            request=httpx.Request("GET", "http://test"),
        )

        with patch.object(
            client._client,
            "get",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            detail = await client.fetch_tournament_detail(
                "t1",
            )

        assert detail.tournament.tournament_id == "t1"
        assert len(detail.placements) == 2
        assert detail.placements[0].placement == 1
        assert detail.placements[0].player_name == "Taro"
        assert detail.placements[0].archetype_name == "Charizard ex"
        assert detail.placements[1].placement == 2

    @pytest.mark.asyncio
    async def test_fetch_detail_raises_on_unparseable(self, client):
        mock_response = httpx.Response(
            200,
            json={"unexpected": "format"},
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
                match="Could not parse tournament metadata",
            ),
        ):
            await client.fetch_tournament_detail("t1")


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
            # First two should be immediate
            await rate_limited_client._get("/test1")
            await rate_limited_client._get("/test2")

        assert call_count == 2
        await rate_limited_client.close()


class TestParsing:
    def test_parse_tournament_missing_fields(self, client):
        result = client._parse_tournament({})
        assert result is None

    def test_parse_tournament_missing_date(self, client):
        result = client._parse_tournament({"id": "t1", "name": "Test"})
        assert result is None

    def test_parse_date_formats(self, client):
        assert client._parse_date("2026-02-01") == date(2026, 2, 1)
        assert client._parse_date("2026/02/01") == date(2026, 2, 1)
        assert client._parse_date("2026年02月01日") == date(2026, 2, 1)
        assert client._parse_date("invalid") is None

    def test_parse_placement_missing_rank(self, client):
        result = client._parse_placement({"player_name": "Test"})
        assert result is None

    def test_parse_placement_valid(self, client):
        result = client._parse_placement(
            {
                "rank": 1,
                "player_name": "Taro",
                "deck_name": "Pikachu",
            }
        )
        assert result is not None
        assert result.placement == 1
        assert result.player_name == "Taro"
        assert result.archetype_name == "Pikachu"


class TestContextManager:
    @pytest.mark.asyncio
    async def test_context_manager(self):
        async with PlayersClubClient() as client:
            assert client is not None
            assert isinstance(client._client, httpx.AsyncClient)
