"""Tests for JP official tournament discovery (Track 1).

Validates that discover-jp auto-discovers official JP tournaments
(Champions League, etc.) alongside city leagues.
"""

from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.clients.limitless import (
    LimitlessClient,
    LimitlessTournament,
)
from src.services.tournament_scrape import TournamentScrapeService


@pytest.fixture
def mock_session() -> AsyncMock:
    """Create a mock async session."""
    session = AsyncMock(spec=AsyncSession)
    session.add = MagicMock()
    default_result = MagicMock()
    default_result.scalars.return_value.all.return_value = []
    session.execute = AsyncMock(return_value=default_result)
    return session


@pytest.fixture
def mock_client() -> AsyncMock:
    """Create a mock Limitless client."""
    return AsyncMock(spec=LimitlessClient)


@pytest.fixture
def service(
    mock_session: AsyncMock,
    mock_client: AsyncMock,
) -> TournamentScrapeService:
    """Create service with mocked dependencies."""
    return TournamentScrapeService(
        session=mock_session,
        client=mock_client,
    )


def _make_tournament(
    name: str,
    region: str,
    days_ago: int = 5,
    participant_count: int = 128,
) -> LimitlessTournament:
    """Helper to build a LimitlessTournament."""
    slug = name.replace(" ", "-").lower()
    return LimitlessTournament(
        name=name,
        tournament_date=date.today() - timedelta(days=days_ago),
        region=region,
        game_format="standard",
        best_of=1 if region == "JP" else 3,
        participant_count=participant_count,
        source_url=f"https://limitlesstcg.com/tournaments/{slug}",
        placements=[],
    )


# ── discover_official_tournaments region filter ──────────


class TestDiscoverOfficialRegionFilter:
    """discover_official_tournaments(region=...) filters correctly."""

    @pytest.mark.asyncio
    async def test_region_jp_filters_to_jp_only(
        self, service: TournamentScrapeService, mock_client: AsyncMock
    ):
        """region='JP' returns only JP tournaments."""
        jp_tourney = _make_tournament("Champions League Fukuoka", "JP")
        na_tourney = _make_tournament("Charlotte Regional", "NA")
        mock_client.fetch_official_tournament_listings.return_value = [
            jp_tourney,
            na_tourney,
        ]
        service.tournament_exists = AsyncMock(return_value=False)

        result = await service.discover_official_tournaments(
            region="JP", lookback_days=90
        )

        assert len(result) == 1
        assert result[0].name == "Champions League Fukuoka"

    @pytest.mark.asyncio
    async def test_region_none_returns_all(
        self, service: TournamentScrapeService, mock_client: AsyncMock
    ):
        """region=None returns all tournaments (backwards compat)."""
        jp_tourney = _make_tournament("Champions League Fukuoka", "JP")
        na_tourney = _make_tournament("Charlotte Regional", "NA")
        mock_client.fetch_official_tournament_listings.return_value = [
            jp_tourney,
            na_tourney,
        ]
        service.tournament_exists = AsyncMock(return_value=False)

        result = await service.discover_official_tournaments(
            region=None, lookback_days=90
        )

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_region_filter_case_insensitive(
        self, service: TournamentScrapeService, mock_client: AsyncMock
    ):
        """Region filter is case-insensitive."""
        jp_tourney = _make_tournament("Champions League Tokyo", "JP")
        mock_client.fetch_official_tournament_listings.return_value = [
            jp_tourney,
        ]
        service.tournament_exists = AsyncMock(return_value=False)

        result = await service.discover_official_tournaments(
            region="jp", lookback_days=90
        )

        assert len(result) == 1


# ── scrape_official_tournaments region filter ────────────


class TestScrapeOfficialRegionFilter:
    """scrape_official_tournaments(region=...) filters correctly."""

    @pytest.mark.asyncio
    async def test_region_jp_filters_scrape(
        self, service: TournamentScrapeService, mock_client: AsyncMock
    ):
        """region='JP' only scrapes JP official tournaments."""
        jp_tourney = _make_tournament("Champions League Fukuoka", "JP")
        na_tourney = _make_tournament("Charlotte Regional", "NA")
        mock_client.fetch_official_tournament_listings.return_value = [
            jp_tourney,
            na_tourney,
        ]
        service.tournament_exists = AsyncMock(return_value=False)
        mock_client.fetch_official_tournament_placements.return_value = []

        result = await service.scrape_official_tournaments(
            region="JP", lookback_days=90
        )

        # Only the JP tournament should be processed
        assert result.tournaments_scraped == 1


# ── discover_jp_tournaments combines city + official ─────


class TestDiscoverJpCombined:
    """discover_jp_tournaments discovers both city leagues and official."""

    @pytest.mark.asyncio
    async def test_discovers_both_city_and_official(self):
        """Pipeline discovers city leagues AND official JP tournaments."""
        city_league = _make_tournament("City League Osaka", "JP", participant_count=64)
        champions = _make_tournament(
            "Champions League Fukuoka",
            "JP",
            participant_count=512,
        )

        with (
            patch("src.pipelines.scrape_limitless.LimitlessClient") as mock_client_cls,
            patch("src.pipelines.scrape_limitless.async_session_factory") as mock_sf,
            patch("src.pipelines.scrape_limitless.CloudTasksService") as mock_tasks_cls,
            patch(
                "src.pipelines.scrape_limitless.TournamentScrapeService"
            ) as mock_svc_cls,
        ):
            # Configure async context managers
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_session = AsyncMock()
            mock_sf.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_sf.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_service = MagicMock()
            mock_svc_cls.return_value = mock_service

            mock_service.discover_jp_city_leagues = AsyncMock(
                return_value=[city_league]
            )
            mock_service.discover_official_tournaments = AsyncMock(
                return_value=[champions]
            )

            # Cloud Tasks not configured, no auto_process
            mock_tasks = MagicMock()
            mock_tasks.is_configured = True
            mock_tasks.enqueue_tournament = AsyncMock(return_value="task-1")
            mock_tasks_cls.return_value = mock_tasks

            from src.pipelines.scrape_limitless import (
                discover_jp_tournaments,
            )

            result = await discover_jp_tournaments(lookback_days=90)

            assert result.tournaments_discovered == 2
            mock_service.discover_official_tournaments.assert_awaited_once_with(
                region="JP",
                lookback_days=90,
            )

    @pytest.mark.asyncio
    async def test_official_gets_is_official_flag(self):
        """Official JP tournaments get is_official=True in payload."""
        city_league = _make_tournament("City League Osaka", "JP", participant_count=64)
        champions = _make_tournament(
            "Champions League Fukuoka",
            "JP",
            participant_count=512,
        )

        with (
            patch("src.pipelines.scrape_limitless.LimitlessClient") as mock_client_cls,
            patch("src.pipelines.scrape_limitless.async_session_factory") as mock_sf,
            patch("src.pipelines.scrape_limitless.CloudTasksService") as mock_tasks_cls,
            patch(
                "src.pipelines.scrape_limitless.TournamentScrapeService"
            ) as mock_svc_cls,
        ):
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_session = AsyncMock()
            mock_sf.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_sf.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_service = MagicMock()
            mock_svc_cls.return_value = mock_service
            mock_service.discover_jp_city_leagues = AsyncMock(
                return_value=[city_league]
            )
            mock_service.discover_official_tournaments = AsyncMock(
                return_value=[champions]
            )

            mock_tasks = MagicMock()
            mock_tasks.is_configured = True
            mock_tasks.enqueue_tournament = AsyncMock(return_value="task-1")
            mock_tasks_cls.return_value = mock_tasks

            from src.pipelines.scrape_limitless import (
                discover_jp_tournaments,
            )

            await discover_jp_tournaments(lookback_days=90)

            # Check payloads sent to enqueue
            calls = mock_tasks.enqueue_tournament.call_args_list
            assert len(calls) == 2

            # First call: city league
            city_payload = calls[0][0][0]
            assert city_payload.get("is_jp_city_league") is True
            assert "is_official" not in city_payload

            # Second call: official
            official_payload = calls[1][0][0]
            assert official_payload.get("is_official") is True
            assert "is_jp_city_league" not in official_payload


# ── Champions League classified as major ─────────────────


class TestChampionsLeagueTier:
    """Champions League events are classified as tier 'major'."""

    def test_champions_league_is_major(self):
        """'Champions League Fukuoka' classified as major."""
        tier = TournamentScrapeService.classify_tier(
            participant_count=512,
            name="Champions League Fukuoka",
        )
        assert tier == "major"

    def test_champions_league_case_insensitive(self):
        """Pattern matching is case-insensitive."""
        tier = TournamentScrapeService.classify_tier(
            participant_count=0,
            name="CHAMPIONS LEAGUE TOKYO",
        )
        assert tier == "major"
