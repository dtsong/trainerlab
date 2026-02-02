"""Tests for Limitless scraping pipeline functions."""

from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.clients.limitless import (
    LimitlessClient,
    LimitlessError,
    LimitlessTournament,
)
from src.pipelines.scrape_limitless import (
    _scrape_dry_run,
    scrape_all_tournaments,
    scrape_en_tournaments,
    scrape_jp_tournaments,
)
from src.services.tournament_scrape import ScrapeResult


@pytest.fixture
def sample_tournaments() -> list[LimitlessTournament]:
    """Create sample tournaments for testing."""
    return [
        LimitlessTournament(
            name="Regional Championship",
            tournament_date=date.today() - timedelta(days=1),
            region="NA",
            game_format="standard",
            best_of=3,
            participant_count=256,
            source_url="https://play.limitlesstcg.com/tournament/123",
            placements=[],
        ),
        LimitlessTournament(
            name="League Cup",
            tournament_date=date.today() - timedelta(days=2),
            region="NA",
            game_format="standard",
            best_of=3,
            participant_count=32,
            source_url="https://play.limitlesstcg.com/tournament/456",
            placements=[],
        ),
    ]


class TestScrapeEnTournaments:
    """Tests for scrape_en_tournaments function."""

    @pytest.mark.asyncio
    async def test_dry_run_does_not_save(self, sample_tournaments):
        """Verify dry run mode fetches but doesn't save data."""
        mock_client = AsyncMock(spec=LimitlessClient)
        # Return tournaments on first page, empty on subsequent pages
        mock_client.fetch_tournament_listings.side_effect = [sample_tournaments, [], []]
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "src.pipelines.scrape_limitless.LimitlessClient",
            return_value=mock_client,
        ):
            result = await scrape_en_tournaments(dry_run=True)

        assert result.tournaments_scraped == len(sample_tournaments)
        assert result.tournaments_saved == 0
        assert result.success

    @pytest.mark.asyncio
    async def test_creates_client_and_session(self, sample_tournaments):
        """Verify EN scrape creates proper client and session."""
        mock_client = AsyncMock(spec=LimitlessClient)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_service = AsyncMock()
        mock_service.scrape_new_tournaments.return_value = ScrapeResult(
            tournaments_scraped=2,
            tournaments_saved=2,
        )

        with (
            patch(
                "src.pipelines.scrape_limitless.LimitlessClient",
                return_value=mock_client,
            ),
            patch(
                "src.pipelines.scrape_limitless.async_session_factory",
                return_value=mock_session,
            ),
            patch(
                "src.pipelines.scrape_limitless.TournamentScrapeService",
                return_value=mock_service,
            ),
        ):
            result = await scrape_en_tournaments(dry_run=False)

        assert result.tournaments_saved == 2
        mock_service.scrape_new_tournaments.assert_called_once_with(
            region="en",
            game_format="standard",
            lookback_days=7,
            max_placements=32,
            fetch_decklists=True,
        )

    @pytest.mark.asyncio
    async def test_passes_custom_parameters(self):
        """Verify custom parameters are passed through."""
        mock_client = AsyncMock(spec=LimitlessClient)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_service = AsyncMock()
        mock_service.scrape_new_tournaments.return_value = ScrapeResult()

        with (
            patch(
                "src.pipelines.scrape_limitless.LimitlessClient",
                return_value=mock_client,
            ),
            patch(
                "src.pipelines.scrape_limitless.async_session_factory",
                return_value=mock_session,
            ),
            patch(
                "src.pipelines.scrape_limitless.TournamentScrapeService",
                return_value=mock_service,
            ),
        ):
            await scrape_en_tournaments(
                dry_run=False,
                lookback_days=14,
                game_format="expanded",
                max_placements=64,
                fetch_decklists=False,
            )

        mock_service.scrape_new_tournaments.assert_called_once_with(
            region="en",
            game_format="expanded",
            lookback_days=14,
            max_placements=64,
            fetch_decklists=False,
        )


class TestScrapeJpTournaments:
    """Tests for scrape_jp_tournaments function."""

    @pytest.mark.asyncio
    async def test_uses_jp_region(self):
        """Verify JP scrape uses jp region parameter."""
        mock_client = AsyncMock(spec=LimitlessClient)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_service = AsyncMock()
        mock_service.scrape_new_tournaments.return_value = ScrapeResult()

        with (
            patch(
                "src.pipelines.scrape_limitless.LimitlessClient",
                return_value=mock_client,
            ),
            patch(
                "src.pipelines.scrape_limitless.async_session_factory",
                return_value=mock_session,
            ),
            patch(
                "src.pipelines.scrape_limitless.TournamentScrapeService",
                return_value=mock_service,
            ),
        ):
            await scrape_jp_tournaments(dry_run=False)

        mock_service.scrape_new_tournaments.assert_called_once()
        call_kwargs = mock_service.scrape_new_tournaments.call_args.kwargs
        assert call_kwargs["region"] == "jp"

    @pytest.mark.asyncio
    async def test_dry_run_mode(self, sample_tournaments):
        """Verify JP dry run mode works correctly."""
        mock_client = AsyncMock(spec=LimitlessClient)
        # Return tournaments on first page, empty on subsequent pages
        mock_client.fetch_tournament_listings.side_effect = [sample_tournaments, [], []]
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "src.pipelines.scrape_limitless.LimitlessClient",
            return_value=mock_client,
        ):
            result = await scrape_jp_tournaments(dry_run=True)

        assert result.tournaments_scraped == len(sample_tournaments)
        assert result.tournaments_saved == 0


class TestScrapeAllTournaments:
    """Tests for scrape_all_tournaments function."""

    @pytest.mark.asyncio
    async def test_runs_both_regions(self):
        """Verify scrape_all runs both EN and JP scrapes."""
        en_result = ScrapeResult(tournaments_saved=5)
        jp_result = ScrapeResult(tournaments_saved=3)

        with (
            patch(
                "src.pipelines.scrape_limitless.scrape_en_tournaments",
                new_callable=AsyncMock,
                return_value=en_result,
            ) as mock_en,
            patch(
                "src.pipelines.scrape_limitless.scrape_jp_tournaments",
                new_callable=AsyncMock,
                return_value=jp_result,
            ) as mock_jp,
        ):
            result_en, result_jp = await scrape_all_tournaments(
                dry_run=True,
                lookback_days=14,
            )

        assert result_en.tournaments_saved == 5
        assert result_jp.tournaments_saved == 3
        mock_en.assert_called_once()
        mock_jp.assert_called_once()

    @pytest.mark.asyncio
    async def test_passes_parameters_to_both(self):
        """Verify parameters are passed to both scrape functions."""
        with (
            patch(
                "src.pipelines.scrape_limitless.scrape_en_tournaments",
                new_callable=AsyncMock,
                return_value=ScrapeResult(),
            ) as mock_en,
            patch(
                "src.pipelines.scrape_limitless.scrape_jp_tournaments",
                new_callable=AsyncMock,
                return_value=ScrapeResult(),
            ) as mock_jp,
        ):
            await scrape_all_tournaments(
                dry_run=True,
                lookback_days=30,
                game_format="expanded",
                max_placements=16,
                fetch_decklists=False,
            )

        expected_kwargs = {
            "dry_run": True,
            "lookback_days": 30,
            "game_format": "expanded",
            "max_placements": 16,
            "fetch_decklists": False,
        }
        mock_en.assert_called_once_with(**expected_kwargs)
        mock_jp.assert_called_once_with(**expected_kwargs)


class TestScrapeDryRun:
    """Tests for _scrape_dry_run function."""

    @pytest.mark.asyncio
    async def test_fetches_without_saving(self, sample_tournaments):
        """Verify dry run fetches data but doesn't save."""
        mock_client = AsyncMock(spec=LimitlessClient)
        # Return tournaments on first page, empty on subsequent pages
        mock_client.fetch_tournament_listings.side_effect = [sample_tournaments, [], []]
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "src.pipelines.scrape_limitless.LimitlessClient",
            return_value=mock_client,
        ):
            result = await _scrape_dry_run(
                region="en",
                game_format="standard",
                lookback_days=7,
            )

        assert result.tournaments_scraped == len(sample_tournaments)
        assert result.tournaments_saved == 0
        assert result.success
        mock_client.fetch_tournament_listings.assert_called()

    @pytest.mark.asyncio
    async def test_iterates_pages_until_empty(self):
        """Verify dry run stops when page returns empty."""
        mock_client = AsyncMock(spec=LimitlessClient)
        # First two pages return data, third is empty
        mock_client.fetch_tournament_listings.side_effect = [
            [MagicMock(name="T1", tournament_date=date.today(), participant_count=10)],
            [MagicMock(name="T2", tournament_date=date.today(), participant_count=10)],
            [],  # Empty page stops iteration
        ]
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "src.pipelines.scrape_limitless.LimitlessClient",
            return_value=mock_client,
        ):
            result = await _scrape_dry_run(
                region="en",
                game_format="standard",
                lookback_days=7,
            )

        assert result.tournaments_scraped == 2
        assert mock_client.fetch_tournament_listings.call_count == 3

    @pytest.mark.asyncio
    async def test_handles_limitless_error(self):
        """Verify dry run handles LimitlessError gracefully."""
        mock_client = AsyncMock(spec=LimitlessClient)
        mock_client.fetch_tournament_listings.side_effect = LimitlessError("API error")
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "src.pipelines.scrape_limitless.LimitlessClient",
            return_value=mock_client,
        ):
            result = await _scrape_dry_run(
                region="en",
                game_format="standard",
                lookback_days=7,
            )

        assert not result.success
        assert len(result.errors) == 1
        assert "Error on page 1" in result.errors[0]

    @pytest.mark.asyncio
    async def test_handles_httpx_request_error(self):
        """Verify dry run handles httpx.RequestError gracefully."""
        mock_client = AsyncMock(spec=LimitlessClient)
        mock_client.fetch_tournament_listings.side_effect = httpx.RequestError(
            "Connection failed"
        )
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "src.pipelines.scrape_limitless.LimitlessClient",
            return_value=mock_client,
        ):
            result = await _scrape_dry_run(
                region="en",
                game_format="standard",
                lookback_days=7,
            )

        assert not result.success
        assert len(result.errors) == 1

    @pytest.mark.asyncio
    async def test_stops_on_error(self, sample_tournaments):
        """Verify dry run stops iteration on first error."""
        mock_client = AsyncMock(spec=LimitlessClient)
        mock_client.fetch_tournament_listings.side_effect = [
            sample_tournaments,
            LimitlessError("Page 2 error"),
        ]
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "src.pipelines.scrape_limitless.LimitlessClient",
            return_value=mock_client,
        ):
            result = await _scrape_dry_run(
                region="en",
                game_format="standard",
                lookback_days=7,
            )

        assert result.tournaments_scraped == len(sample_tournaments)
        assert len(result.errors) == 1
        assert "page 2" in result.errors[0].lower()
