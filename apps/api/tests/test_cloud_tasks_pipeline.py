"""Tests for the Cloud Tasks tournament scrape pipeline.

Tests the two-phase pipeline: discover → enqueue → process.
"""

from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.clients.limitless import (
    LimitlessClient,
    LimitlessTournament,
)
from src.pipelines.scrape_limitless import (
    DiscoverResult,
    _tournament_to_task_payload,
    discover_en_tournaments,
    discover_jp_tournaments,
    process_single_tournament,
)
from src.services.cloud_tasks import CloudTasksService
from src.services.tournament_scrape import TournamentScrapeService


@pytest.fixture
def sample_tournament() -> LimitlessTournament:
    """Create a sample tournament."""
    return LimitlessTournament(
        name="Regional Championship",
        tournament_date=date.today() - timedelta(days=2),
        region="NA",
        game_format="standard",
        best_of=3,
        participant_count=256,
        source_url="https://play.limitlesstcg.com/tournament/12345",
        placements=[],
    )


class TestTournamentToTaskPayload:
    """Tests for _tournament_to_task_payload helper."""

    def test_converts_tournament_to_dict(
        self, sample_tournament: LimitlessTournament
    ) -> None:
        """Should convert LimitlessTournament to a dict payload."""
        payload = _tournament_to_task_payload(sample_tournament)

        assert payload["source_url"] == sample_tournament.source_url
        assert payload["name"] == sample_tournament.name
        assert (
            payload["tournament_date"] == sample_tournament.tournament_date.isoformat()
        )
        assert payload["region"] == sample_tournament.region
        assert payload["game_format"] == sample_tournament.game_format
        assert payload["best_of"] == sample_tournament.best_of
        assert payload["participant_count"] == sample_tournament.participant_count


class TestCloudTasksService:
    """Tests for CloudTasksService."""

    def test_is_configured_false_without_settings(self) -> None:
        """Should report not configured when settings are missing."""
        with patch("src.services.cloud_tasks.get_settings") as mock_settings:
            settings = MagicMock()
            settings.cloud_tasks_queue_path = None
            settings.cloud_run_url = None
            settings.api_service_account = None
            mock_settings.return_value = settings

            service = CloudTasksService()
            assert service.is_configured is False

    def test_is_configured_true_with_settings(self) -> None:
        """Should report configured when settings are present."""
        with patch("src.services.cloud_tasks.get_settings") as mock_settings:
            settings = MagicMock()
            settings.cloud_tasks_queue_path = "projects/p/locations/l/queues/q"
            settings.cloud_run_url = "https://api.example.com"
            settings.api_service_account = "sa@example.iam.gserviceaccount.com"
            mock_settings.return_value = settings

            service = CloudTasksService()
            assert service.is_configured is True

    @pytest.mark.asyncio
    async def test_enqueue_returns_none_when_not_configured(self) -> None:
        """Should return None when Cloud Tasks is not configured."""
        with patch("src.services.cloud_tasks.get_settings") as mock_settings:
            settings = MagicMock()
            settings.cloud_tasks_queue_path = None
            settings.cloud_run_url = None
            settings.api_service_account = None
            mock_settings.return_value = settings

            service = CloudTasksService()
            result = await service.enqueue_tournament(
                {"source_url": "https://example.com/t/1"}
            )
            assert result is None

    def test_task_id_from_url_deterministic(self) -> None:
        """Should generate same task ID for same URL."""
        url = "https://play.limitlesstcg.com/tournament/12345"
        id1 = CloudTasksService._task_id_from_url(url)
        id2 = CloudTasksService._task_id_from_url(url)
        assert id1 == id2
        assert id1.startswith("tournament-")

    def test_task_id_different_for_different_urls(self) -> None:
        """Should generate different task IDs for different URLs."""
        id1 = CloudTasksService._task_id_from_url("https://example.com/t/1")
        id2 = CloudTasksService._task_id_from_url("https://example.com/t/2")
        assert id1 != id2


class TestDiscoverEnTournaments:
    """Tests for discover_en_tournaments pipeline function."""

    @pytest.mark.asyncio
    async def test_discovers_and_enqueues_new_tournaments(
        self, sample_tournament: LimitlessTournament
    ) -> None:
        """Should discover new tournaments and enqueue them."""
        with (
            patch("src.pipelines.scrape_limitless.LimitlessClient") as mock_client_cls,
            patch(
                "src.pipelines.scrape_limitless.async_session_factory"
            ) as mock_session_factory,
            patch("src.pipelines.scrape_limitless.CloudTasksService") as mock_tasks_cls,
            patch.object(
                TournamentScrapeService,
                "discover_new_tournaments",
                new_callable=AsyncMock,
            ) as mock_discover,
            patch.object(
                TournamentScrapeService,
                "discover_official_tournaments",
                new_callable=AsyncMock,
            ) as mock_discover_official,
        ):
            # Setup mocks
            mock_client = AsyncMock(spec=LimitlessClient)
            mock_client_cls.return_value.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=None)

            mock_session = AsyncMock(spec=AsyncSession)
            mock_session_factory.return_value.__aenter__ = AsyncMock(
                return_value=mock_session
            )
            mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

            mock_discover.return_value = [sample_tournament]
            mock_discover_official.return_value = []

            mock_tasks = MagicMock(spec=CloudTasksService)
            mock_tasks.enqueue_tournament = AsyncMock(return_value="task-name")
            mock_tasks_cls.return_value = mock_tasks

            result = await discover_en_tournaments(lookback_days=90)

            assert result.tournaments_discovered == 1
            assert result.tasks_enqueued == 1
            assert result.success is True
            mock_tasks.enqueue_tournament.assert_called_once()

    @pytest.mark.asyncio
    async def test_handles_enqueue_failure(
        self, sample_tournament: LimitlessTournament
    ) -> None:
        """Should record error when enqueue fails."""
        with (
            patch("src.pipelines.scrape_limitless.LimitlessClient") as mock_client_cls,
            patch(
                "src.pipelines.scrape_limitless.async_session_factory"
            ) as mock_session_factory,
            patch("src.pipelines.scrape_limitless.CloudTasksService") as mock_tasks_cls,
            patch.object(
                TournamentScrapeService,
                "discover_new_tournaments",
                new_callable=AsyncMock,
            ) as mock_discover,
            patch.object(
                TournamentScrapeService,
                "discover_official_tournaments",
                new_callable=AsyncMock,
            ) as mock_discover_official,
        ):
            mock_client = AsyncMock(spec=LimitlessClient)
            mock_client_cls.return_value.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=None)

            mock_session = AsyncMock(spec=AsyncSession)
            mock_session_factory.return_value.__aenter__ = AsyncMock(
                return_value=mock_session
            )
            mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

            mock_discover.return_value = [sample_tournament]
            mock_discover_official.return_value = []

            mock_tasks = MagicMock(spec=CloudTasksService)
            mock_tasks.enqueue_tournament = AsyncMock(
                side_effect=RuntimeError("Queue error")
            )
            mock_tasks_cls.return_value = mock_tasks

            result = await discover_en_tournaments()

            assert result.tournaments_discovered == 1
            assert result.tasks_enqueued == 0
            assert len(result.errors) == 1
            assert result.success is False


class TestDiscoverJpTournaments:
    """Tests for discover_jp_tournaments pipeline function."""

    @pytest.mark.asyncio
    async def test_discovers_jp_tournaments(
        self,
    ) -> None:
        """Should discover JP tournaments and enqueue them."""
        jp_tournament = LimitlessTournament(
            name="City League Tokyo",
            tournament_date=date.today() - timedelta(days=1),
            region="JP",
            game_format="standard",
            best_of=1,
            participant_count=64,
            source_url="https://limitlesstcg.com/tournaments/jp/123",
            placements=[],
        )

        with (
            patch("src.pipelines.scrape_limitless.LimitlessClient") as mock_client_cls,
            patch(
                "src.pipelines.scrape_limitless.async_session_factory"
            ) as mock_session_factory,
            patch("src.pipelines.scrape_limitless.CloudTasksService") as mock_tasks_cls,
            patch.object(
                TournamentScrapeService,
                "discover_jp_city_leagues",
                new_callable=AsyncMock,
            ) as mock_discover,
        ):
            mock_client = AsyncMock(spec=LimitlessClient)
            mock_client_cls.return_value.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=None)

            mock_session = AsyncMock(spec=AsyncSession)
            mock_session_factory.return_value.__aenter__ = AsyncMock(
                return_value=mock_session
            )
            mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

            mock_discover.return_value = [jp_tournament]

            mock_tasks = MagicMock(spec=CloudTasksService)
            mock_tasks.enqueue_tournament = AsyncMock(return_value="task-name")
            mock_tasks_cls.return_value = mock_tasks

            result = await discover_jp_tournaments(lookback_days=30)

            assert result.tournaments_discovered == 1
            assert result.tasks_enqueued == 1
            # Verify JP-specific flag is set in payload
            call_args = mock_tasks.enqueue_tournament.call_args[0][0]
            assert call_args["is_jp_city_league"] is True


class TestProcessSingleTournament:
    """Tests for process_single_tournament pipeline function."""

    @pytest.mark.asyncio
    async def test_processes_tournament_from_payload(self) -> None:
        """Should process a single tournament from a task payload."""
        payload = {
            "source_url": "https://play.limitlesstcg.com/tournament/12345",
            "name": "Regional Championship",
            "tournament_date": (date.today() - timedelta(days=2)).isoformat(),
            "region": "NA",
            "game_format": "standard",
            "best_of": 3,
            "participant_count": 256,
            "is_official": False,
            "is_jp_city_league": False,
        }

        with (
            patch("src.pipelines.scrape_limitless.LimitlessClient") as mock_client_cls,
            patch(
                "src.pipelines.scrape_limitless.async_session_factory"
            ) as mock_session_factory,
            patch.object(
                TournamentScrapeService,
                "process_tournament_by_url",
                new_callable=AsyncMock,
            ) as mock_process,
        ):
            from src.services.tournament_scrape import ScrapeResult

            mock_client = AsyncMock(spec=LimitlessClient)
            mock_client_cls.return_value.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=None)

            mock_session = AsyncMock(spec=AsyncSession)
            mock_session_factory.return_value.__aenter__ = AsyncMock(
                return_value=mock_session
            )
            mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

            mock_process.return_value = ScrapeResult(
                tournaments_scraped=1,
                tournaments_saved=1,
                placements_saved=32,
            )

            result = await process_single_tournament(payload)

            assert result.tournaments_saved == 1
            assert result.placements_saved == 32
            mock_process.assert_called_once()

    @pytest.mark.asyncio
    async def test_skips_already_existing_tournament(self) -> None:
        """Should skip if tournament already exists (defense in depth)."""
        payload = {
            "source_url": "https://play.limitlesstcg.com/tournament/12345",
            "name": "Regional Championship",
            "tournament_date": date.today().isoformat(),
            "region": "NA",
            "game_format": "standard",
            "best_of": 3,
            "participant_count": 256,
        }

        with (
            patch("src.pipelines.scrape_limitless.LimitlessClient") as mock_client_cls,
            patch(
                "src.pipelines.scrape_limitless.async_session_factory"
            ) as mock_session_factory,
            patch.object(
                TournamentScrapeService,
                "process_tournament_by_url",
                new_callable=AsyncMock,
            ) as mock_process,
        ):
            from src.services.tournament_scrape import ScrapeResult

            mock_client = AsyncMock(spec=LimitlessClient)
            mock_client_cls.return_value.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=None)

            mock_session = AsyncMock(spec=AsyncSession)
            mock_session_factory.return_value.__aenter__ = AsyncMock(
                return_value=mock_session
            )
            mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

            # process_tournament_by_url returns skipped
            mock_process.return_value = ScrapeResult(
                tournaments_scraped=1,
                tournaments_skipped=1,
            )

            result = await process_single_tournament(payload)

            assert result.tournaments_skipped == 1
            assert result.tournaments_saved == 0


class TestDiscoverResult:
    """Tests for DiscoverResult dataclass."""

    def test_success_true_when_no_errors(self) -> None:
        """Should report success when no errors."""
        result = DiscoverResult(
            tournaments_discovered=5,
            tasks_enqueued=3,
        )
        assert result.success is True

    def test_success_false_when_errors(self) -> None:
        """Should report failure when errors exist."""
        result = DiscoverResult(
            tournaments_discovered=5,
            tasks_enqueued=0,
            errors=["Queue error"],
        )
        assert result.success is False
