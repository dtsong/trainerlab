"""Tests for tournament scraping service."""

from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.clients.limitless import (
    LimitlessClient,
    LimitlessDecklist,
    LimitlessPlacement,
    LimitlessTournament,
)
from src.models import Tournament
from src.services.archetype_detector import ArchetypeDetector
from src.services.tournament_scrape import ScrapeResult, TournamentScrapeService


@pytest.fixture
def mock_session() -> AsyncMock:
    """Create a mock async session."""
    session = AsyncMock(spec=AsyncSession)
    session.add = MagicMock()
    return session


@pytest.fixture
def mock_client() -> AsyncMock:
    """Create a mock Limitless client."""
    return AsyncMock(spec=LimitlessClient)


@pytest.fixture
def mock_detector() -> MagicMock:
    """Create a mock archetype detector."""
    detector = MagicMock(spec=ArchetypeDetector)
    detector.detect_from_existing_archetype.return_value = "Charizard ex"
    return detector


@pytest.fixture
def service(
    mock_session: AsyncMock,
    mock_client: AsyncMock,
    mock_detector: MagicMock,
) -> TournamentScrapeService:
    """Create service with mocked dependencies."""
    return TournamentScrapeService(
        session=mock_session,
        client=mock_client,
        archetype_detector=mock_detector,
    )


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


@pytest.fixture
def sample_placement() -> LimitlessPlacement:
    """Create a sample placement."""
    return LimitlessPlacement(
        placement=1,
        player_name="Champion Player",
        country="US",
        archetype="Charizard ex",
        decklist_url="https://play.limitlesstcg.com/deck/abc123",
        decklist=None,
    )


@pytest.fixture
def sample_decklist() -> LimitlessDecklist:
    """Create a sample decklist."""
    return LimitlessDecklist(
        cards=[
            {"card_id": "sv3-125", "name": "Charizard ex", "quantity": 2},
            {"card_id": "sv3-46", "name": "Charmander", "quantity": 4},
        ],
        source_url="https://play.limitlesstcg.com/deck/abc123",
    )


class TestTournamentExists:
    """Tests for tournament_exists method."""

    @pytest.mark.asyncio
    async def test_returns_true_when_exists(
        self, service: TournamentScrapeService, mock_session: AsyncMock
    ) -> None:
        """Should return True when tournament exists in database."""
        # Mock query result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = Tournament(
            id=uuid4(),
            name="Existing Tournament",
            date=date.today(),
            region="NA",
            format="standard",
            best_of=3,
            source_url="https://example.com/tournament/1",
        )
        mock_session.execute.return_value = mock_result

        exists = await service.tournament_exists("https://example.com/tournament/1")

        assert exists is True
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_false_when_not_exists(
        self, service: TournamentScrapeService, mock_session: AsyncMock
    ) -> None:
        """Should return False when tournament not in database."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        exists = await service.tournament_exists("https://example.com/tournament/new")

        assert exists is False


class TestScrapeNewTournaments:
    """Tests for scrape_new_tournaments method."""

    @pytest.mark.asyncio
    async def test_scrapes_and_saves_new_tournaments(
        self,
        service: TournamentScrapeService,
        mock_session: AsyncMock,
        mock_client: AsyncMock,
        sample_tournament: LimitlessTournament,
        sample_placement: LimitlessPlacement,
    ) -> None:
        """Should scrape and save new tournaments."""
        # Setup: tournament listing returns one tournament
        mock_client.fetch_tournament_listings.return_value = [sample_tournament]
        mock_client.fetch_tournament_placements.return_value = [sample_placement]

        # Tournament doesn't exist yet
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await service.scrape_new_tournaments(
            region="en",
            game_format="standard",
            lookback_days=7,
            max_pages=1,
            fetch_decklists=False,
        )

        assert result.tournaments_scraped == 1
        assert result.tournaments_saved == 1
        assert result.tournaments_skipped == 0
        assert result.placements_saved == 1
        assert result.success is True

    @pytest.mark.asyncio
    async def test_skips_existing_tournaments(
        self,
        service: TournamentScrapeService,
        mock_session: AsyncMock,
        mock_client: AsyncMock,
        sample_tournament: LimitlessTournament,
    ) -> None:
        """Should skip tournaments that already exist."""
        mock_client.fetch_tournament_listings.return_value = [sample_tournament]

        # Tournament already exists
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = Tournament(
            id=uuid4(),
            name="Existing",
            date=date.today(),
            region="NA",
            format="standard",
            best_of=3,
            source_url=sample_tournament.source_url,
        )
        mock_session.execute.return_value = mock_result

        result = await service.scrape_new_tournaments(max_pages=1)

        assert result.tournaments_scraped == 1
        assert result.tournaments_saved == 0
        assert result.tournaments_skipped == 1

    @pytest.mark.asyncio
    async def test_fetches_decklists_when_enabled(
        self,
        service: TournamentScrapeService,
        mock_session: AsyncMock,
        mock_client: AsyncMock,
        sample_tournament: LimitlessTournament,
        sample_placement: LimitlessPlacement,
        sample_decklist: LimitlessDecklist,
    ) -> None:
        """Should fetch decklists when fetch_decklists=True."""
        mock_client.fetch_tournament_listings.return_value = [sample_tournament]
        mock_client.fetch_tournament_placements.return_value = [sample_placement]
        mock_client.fetch_decklist.return_value = sample_decklist

        # Tournament doesn't exist
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await service.scrape_new_tournaments(max_pages=1, fetch_decklists=True)

        assert result.decklists_saved == 1
        mock_client.fetch_decklist.assert_called_once_with(
            sample_placement.decklist_url
        )

    @pytest.mark.asyncio
    async def test_handles_decklist_fetch_error(
        self,
        service: TournamentScrapeService,
        mock_session: AsyncMock,
        mock_client: AsyncMock,
        sample_tournament: LimitlessTournament,
        sample_placement: LimitlessPlacement,
    ) -> None:
        """Should log warning and continue on decklist fetch error.

        Note: Decklist fetch errors are intentionally "soft failures" - they
        are logged but not added to result.errors. This allows the scrape to
        report success even if some decklists couldn't be fetched, since
        tournament data is still valuable without decklists.
        """
        mock_client.fetch_tournament_listings.return_value = [sample_tournament]
        mock_client.fetch_tournament_placements.return_value = [sample_placement]
        mock_client.fetch_decklist.side_effect = Exception("Network error")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        with patch("src.services.tournament_scrape.logger") as mock_logger:
            result = await service.scrape_new_tournaments(
                max_pages=1, fetch_decklists=True
            )

            # Should still save tournament without decklist
            assert result.tournaments_saved == 1
            assert result.decklists_saved == 0

            # Verify warning was logged (soft failure behavior)
            mock_logger.warning.assert_called()
            warning_call = str(mock_logger.warning.call_args)
            assert "Network error" in warning_call

            # Intentional: decklist errors don't fail the scrape
            assert result.success is True
            assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_filters_by_lookback_date(
        self,
        service: TournamentScrapeService,
        mock_session: AsyncMock,
        mock_client: AsyncMock,
    ) -> None:
        """Should only include tournaments within lookback period."""
        recent = LimitlessTournament(
            name="Recent",
            tournament_date=date.today() - timedelta(days=3),
            region="NA",
            game_format="standard",
            best_of=3,
            participant_count=100,
            source_url="https://example.com/recent",
            placements=[],
        )
        old = LimitlessTournament(
            name="Old",
            tournament_date=date.today() - timedelta(days=30),
            region="NA",
            game_format="standard",
            best_of=3,
            participant_count=100,
            source_url="https://example.com/old",
            placements=[],
        )

        mock_client.fetch_tournament_listings.return_value = [recent, old]
        mock_client.fetch_tournament_placements.return_value = []

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await service.scrape_new_tournaments(
            lookback_days=7, max_pages=1, fetch_decklists=False
        )

        # Only recent tournament should be included
        assert result.tournaments_scraped == 1

    @pytest.mark.asyncio
    async def test_handles_page_fetch_error(
        self,
        service: TournamentScrapeService,
        mock_client: AsyncMock,
    ) -> None:
        """Should record error and stop on page fetch failure."""
        mock_client.fetch_tournament_listings.side_effect = Exception("Network error")

        result = await service.scrape_new_tournaments(max_pages=3)

        assert result.tournaments_scraped == 0
        assert len(result.errors) == 1
        assert "Error fetching page 1" in result.errors[0]

    @pytest.mark.asyncio
    async def test_stops_on_empty_page(
        self,
        service: TournamentScrapeService,
        mock_client: AsyncMock,
    ) -> None:
        """Should stop fetching when page returns no tournaments."""
        mock_client.fetch_tournament_listings.return_value = []

        result = await service.scrape_new_tournaments(max_pages=5)

        assert result.tournaments_scraped == 0
        # Should only fetch one page
        mock_client.fetch_tournament_listings.assert_called_once()

    @pytest.mark.asyncio
    async def test_handles_tournament_processing_error(
        self,
        service: TournamentScrapeService,
        mock_session: AsyncMock,
        mock_client: AsyncMock,
        sample_tournament: LimitlessTournament,
    ) -> None:
        """Should continue on tournament processing error."""
        mock_client.fetch_tournament_listings.return_value = [sample_tournament]
        mock_client.fetch_tournament_placements.side_effect = Exception("Parse error")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await service.scrape_new_tournaments(
            max_pages=1, fetch_decklists=False
        )

        assert result.tournaments_saved == 0
        assert len(result.errors) == 1
        assert "Error processing tournament" in result.errors[0]


class TestSaveTournament:
    """Tests for save_tournament method."""

    @pytest.mark.asyncio
    async def test_saves_tournament_and_placements(
        self,
        service: TournamentScrapeService,
        mock_session: AsyncMock,
        sample_tournament: LimitlessTournament,
        sample_placement: LimitlessPlacement,
    ) -> None:
        """Should save tournament and its placements."""
        sample_tournament.placements = [sample_placement]

        result = await service.save_tournament(sample_tournament)

        # Should add tournament and placement
        assert mock_session.add.call_count == 2
        mock_session.commit.assert_called_once()
        assert result.name == sample_tournament.name

    @pytest.mark.asyncio
    async def test_rollback_on_database_error(
        self,
        service: TournamentScrapeService,
        mock_session: AsyncMock,
        sample_tournament: LimitlessTournament,
    ) -> None:
        """Should rollback on database error."""
        mock_session.commit.side_effect = SQLAlchemyError("Constraint violation")

        with pytest.raises(SQLAlchemyError):
            await service.save_tournament(sample_tournament)

        mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_saves_tournament_without_placements(
        self,
        service: TournamentScrapeService,
        mock_session: AsyncMock,
        sample_tournament: LimitlessTournament,
    ) -> None:
        """Should handle tournament with no placements."""
        sample_tournament.placements = []

        await service.save_tournament(sample_tournament)

        assert mock_session.add.call_count == 1  # Only tournament
        mock_session.commit.assert_called_once()


class TestCreatePlacement:
    """Tests for _create_placement method."""

    def test_creates_placement_with_decklist(
        self,
        service: TournamentScrapeService,
        sample_placement: LimitlessPlacement,
        sample_decklist: LimitlessDecklist,
        mock_detector: MagicMock,
    ) -> None:
        """Should create placement with decklist data."""
        sample_placement.decklist = sample_decklist
        tournament_id = uuid4()

        result = service._create_placement(sample_placement, tournament_id)

        assert result.tournament_id == tournament_id
        assert result.placement == 1
        assert result.player_name == "Champion Player"
        assert result.decklist is not None
        assert len(result.decklist) == 2

        # Should detect archetype from decklist
        mock_detector.detect_from_existing_archetype.assert_called_once()

    def test_creates_placement_without_decklist(
        self,
        service: TournamentScrapeService,
        sample_placement: LimitlessPlacement,
    ) -> None:
        """Should create placement without decklist data."""
        sample_placement.decklist = None
        tournament_id = uuid4()

        result = service._create_placement(sample_placement, tournament_id)

        assert result.decklist is None
        assert result.decklist_source is None
        assert result.archetype == sample_placement.archetype

    def test_preserves_archetype_from_placement(
        self,
        service: TournamentScrapeService,
        sample_placement: LimitlessPlacement,
        mock_detector: MagicMock,
    ) -> None:
        """Should use existing archetype when no decklist."""
        sample_placement.decklist = None
        sample_placement.archetype = "Custom Archetype"
        tournament_id = uuid4()

        result = service._create_placement(sample_placement, tournament_id)

        assert result.archetype == "Custom Archetype"
        mock_detector.detect_from_existing_archetype.assert_not_called()


class TestGetRecentTournaments:
    """Tests for get_recent_tournaments method."""

    @pytest.mark.asyncio
    async def test_returns_recent_tournaments(
        self,
        service: TournamentScrapeService,
        mock_session: AsyncMock,
    ) -> None:
        """Should return tournaments from database."""
        tournaments = [
            Tournament(
                id=uuid4(),
                name="Tournament 1",
                date=date.today() - timedelta(days=5),
                region="NA",
                format="standard",
                best_of=3,
                source_url="https://example.com/1",
            ),
            Tournament(
                id=uuid4(),
                name="Tournament 2",
                date=date.today() - timedelta(days=10),
                region="NA",
                format="standard",
                best_of=3,
                source_url="https://example.com/2",
            ),
        ]

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = tournaments
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await service.get_recent_tournaments(days=30)

        assert len(result) == 2
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_filters_by_region(
        self,
        service: TournamentScrapeService,
        mock_session: AsyncMock,
    ) -> None:
        """Should filter by region when provided."""
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        await service.get_recent_tournaments(region="JP")

        # Verify the query was executed
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_filters_by_format(
        self,
        service: TournamentScrapeService,
        mock_session: AsyncMock,
    ) -> None:
        """Should filter by game format when provided."""
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        await service.get_recent_tournaments(game_format="expanded")

        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_filters_by_best_of(
        self,
        service: TournamentScrapeService,
        mock_session: AsyncMock,
    ) -> None:
        """Should filter by best_of when provided."""
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        await service.get_recent_tournaments(best_of=1)

        mock_session.execute.assert_called_once()


class TestScrapeResult:
    """Tests for ScrapeResult dataclass."""

    def test_success_true_when_no_errors(self) -> None:
        """Should report success when no errors."""
        result = ScrapeResult(
            tournaments_scraped=5,
            tournaments_saved=3,
            errors=[],
        )
        assert result.success is True

    def test_success_false_when_errors(self) -> None:
        """Should report failure when errors exist."""
        result = ScrapeResult(
            tournaments_scraped=5,
            tournaments_saved=0,
            errors=["Error 1", "Error 2"],
        )
        assert result.success is False

    def test_default_values(self) -> None:
        """Should have sensible defaults."""
        result = ScrapeResult()
        assert result.tournaments_scraped == 0
        assert result.tournaments_saved == 0
        assert result.tournaments_skipped == 0
        assert result.placements_saved == 0
        assert result.decklists_saved == 0
        assert result.errors == []
        assert result.success is True
