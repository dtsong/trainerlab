"""Tests for tournament scraping service."""

from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.clients.limitless import (
    LimitlessClient,
    LimitlessDecklist,
    LimitlessError,
    LimitlessPlacement,
    LimitlessTournament,
)
from src.models import Tournament
from src.models.major_format_window import MajorFormatWindow
from src.services.archetype_detector import ArchetypeDetector
from src.services.archetype_normalizer import ArchetypeNormalizer
from src.services.tournament_scrape import ScrapeResult, TournamentScrapeService


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


class TestClassifyTier:
    """Tests for tier classification logic."""

    def test_classifies_major_by_name_regional(self) -> None:
        """Should classify as major based on 'regional' in name."""
        tier = TournamentScrapeService.classify_tier(
            50, "Portland Regional Championship"
        )
        assert tier == "major"

    def test_classifies_major_by_name_international(self) -> None:
        """Should classify as major based on 'international' in name."""
        tier = TournamentScrapeService.classify_tier(100, "Latin America International")
        assert tier == "major"

    def test_classifies_major_by_name_worlds(self) -> None:
        """Should classify as major based on 'worlds' in name."""
        tier = TournamentScrapeService.classify_tier(200, "Pokemon Worlds 2024")
        assert tier == "major"

    def test_classifies_premier_by_name_league_cup(self) -> None:
        """Should classify as premier based on 'league cup' in name."""
        tier = TournamentScrapeService.classify_tier(20, "January League Cup")
        assert tier == "premier"

    def test_classifies_premier_by_name_league_challenge(self) -> None:
        """Should classify as premier based on 'league challenge' in name."""
        tier = TournamentScrapeService.classify_tier(15, "February League Challenge")
        assert tier == "premier"

    def test_classifies_league_by_name_city_league(self) -> None:
        """Should classify as league based on 'city league' in name."""
        tier = TournamentScrapeService.classify_tier(0, "Tokyo City League")
        assert tier == "league"

    def test_classifies_major_by_participant_count(self) -> None:
        """Should classify as major when 256+ participants and no name match."""
        tier = TournamentScrapeService.classify_tier(300, "Big Event")
        assert tier == "major"

    def test_classifies_premier_by_participant_count(self) -> None:
        """Should classify as premier when 64-255 participants."""
        tier = TournamentScrapeService.classify_tier(100, "Medium Event")
        assert tier == "premier"

    def test_classifies_league_by_participant_count(self) -> None:
        """Should classify as league when under 64 participants."""
        tier = TournamentScrapeService.classify_tier(30, "Small Event")
        assert tier == "league"

    def test_returns_none_for_zero_participants_and_unknown_name(self) -> None:
        """Should return None when 0 participants and name doesn't match patterns."""
        tier = TournamentScrapeService.classify_tier(0, "Unknown Event")
        assert tier is None

    def test_name_takes_priority_over_participant_count(self) -> None:
        """Name-based classification should override participant count."""
        tier = TournamentScrapeService.classify_tier(10, "Regional Championship")
        assert tier == "major"


class TestTournamentExists:
    """Tests for tournament_exists method."""

    @pytest.mark.asyncio
    async def test_returns_true_when_exists(
        self, service: TournamentScrapeService, mock_session: AsyncMock
    ) -> None:
        """Should return True when tournament exists in database."""
        # Mock query result
        mock_result = MagicMock()
        mock_result.first.return_value = Tournament(
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
        mock_result.first.return_value = None
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
        mock_result.first.return_value = None
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
        mock_result.first.return_value = Tournament(
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
        mock_result.first.return_value = None
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
        mock_client.fetch_decklist.side_effect = LimitlessError("Network error")

        mock_result = MagicMock()
        mock_result.first.return_value = None
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
        mock_result.first.return_value = None
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
        mock_client.fetch_tournament_listings.side_effect = LimitlessError(
            "Network error"
        )

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
        mock_client.fetch_tournament_placements.side_effect = LimitlessError(
            "Parse error"
        )

        mock_result = MagicMock()
        mock_result.first.return_value = None
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
        assert result is not None
        assert result.name == sample_tournament.name

    @pytest.mark.asyncio
    async def test_tags_official_tournament_with_major_format_window(
        self,
        service: TournamentScrapeService,
        mock_session: AsyncMock,
        sample_tournament: LimitlessTournament,
    ) -> None:
        """Should apply major format metadata for official-major tournaments."""
        window = MajorFormatWindow(
            id=uuid4(),
            key="svi-asc",
            display_name="SVI-ASC",
            set_range_label="Scarlet & Violet to Ascended Heroes",
            start_date=date(2026, 2, 1),
            end_date=date(2026, 3, 31),
            is_active=True,
        )
        window_result = MagicMock()
        window_result.scalars.return_value.all.return_value = [window]
        mock_session.execute = AsyncMock(return_value=window_result)

        result = await service.save_tournament(sample_tournament)

        assert result is not None
        assert result.major_format_key == "svi-asc"
        assert result.major_format_label == "SVI-ASC"

    @pytest.mark.asyncio
    async def test_does_not_tag_non_official_tournament(
        self,
        service: TournamentScrapeService,
        sample_tournament: LimitlessTournament,
    ) -> None:
        """Should leave major format metadata unset for non-official tiers."""
        sample_tournament.name = "Local League Cup"
        sample_tournament.participant_count = 32

        result = await service.save_tournament(sample_tournament)

        assert result is not None
        assert result.tier == "premier"
        assert result.major_format_key is None
        assert result.major_format_label is None

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

    @pytest.mark.asyncio
    async def test_returns_none_on_duplicate_source_url(
        self,
        service: TournamentScrapeService,
        mock_session: AsyncMock,
        sample_tournament: LimitlessTournament,
    ) -> None:
        """Should return None and rollback on IntegrityError (duplicate source_url)."""
        mock_session.commit.side_effect = IntegrityError(
            "duplicate key", params=None, orig=Exception("unique violation")
        )

        result = await service.save_tournament(sample_tournament)

        assert result is None
        mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_scrape_counts_duplicate_as_skipped(
        self,
        service: TournamentScrapeService,
        mock_session: AsyncMock,
        mock_client: AsyncMock,
        sample_tournament: LimitlessTournament,
        sample_placement: LimitlessPlacement,
    ) -> None:
        """Should count IntegrityError duplicates as skipped in scrape results."""
        mock_client.fetch_tournament_listings.return_value = [sample_tournament]
        mock_client.fetch_tournament_placements.return_value = [sample_placement]

        # tournament_exists returns False (race condition: another process inserted it)
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.execute.return_value = mock_result

        # But commit fails with IntegrityError (duplicate)
        mock_session.commit.side_effect = IntegrityError(
            "duplicate key", params=None, orig=Exception("unique violation")
        )

        result = await service.scrape_new_tournaments(
            max_pages=1, fetch_decklists=False
        )

        assert result.tournaments_saved == 0
        assert result.tournaments_skipped == 1


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


class TestDiscoverNewTournaments:
    """Tests for discover_new_tournaments method."""

    @pytest.mark.asyncio
    async def test_discovers_new_tournaments(
        self,
        service: TournamentScrapeService,
        mock_session: AsyncMock,
        mock_client: AsyncMock,
        sample_tournament: LimitlessTournament,
    ) -> None:
        """Should return tournaments not in database."""
        mock_client.fetch_tournament_listings.return_value = [sample_tournament]

        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.execute.return_value = mock_result

        result = await service.discover_new_tournaments(max_pages=1)

        assert len(result) == 1
        assert result[0].name == sample_tournament.name

    @pytest.mark.asyncio
    async def test_filters_existing_tournaments(
        self,
        service: TournamentScrapeService,
        mock_session: AsyncMock,
        mock_client: AsyncMock,
        sample_tournament: LimitlessTournament,
    ) -> None:
        """Should exclude tournaments already in database."""
        mock_client.fetch_tournament_listings.return_value = [sample_tournament]

        mock_result = MagicMock()
        mock_result.first.return_value = Tournament(
            id=uuid4(),
            name="Existing",
            date=date.today(),
            region="NA",
            format="standard",
            best_of=3,
            source_url=sample_tournament.source_url,
        )
        mock_session.execute.return_value = mock_result

        result = await service.discover_new_tournaments(max_pages=1)

        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_stops_pagination_on_empty_page(
        self,
        service: TournamentScrapeService,
        mock_client: AsyncMock,
    ) -> None:
        """Should stop pagination when page returns empty."""
        mock_client.fetch_tournament_listings.side_effect = [
            [
                LimitlessTournament(
                    name="T1",
                    tournament_date=date.today(),
                    region="NA",
                    game_format="standard",
                    best_of=3,
                    participant_count=100,
                    source_url="url1",
                    placements=[],
                )
            ],
            [],
        ]

        await service.discover_new_tournaments(max_pages=5)

        assert mock_client.fetch_tournament_listings.call_count == 2

    @pytest.mark.asyncio
    async def test_handles_fetch_error(
        self,
        service: TournamentScrapeService,
        mock_client: AsyncMock,
    ) -> None:
        """Should handle fetch error and return empty list."""
        mock_client.fetch_tournament_listings.side_effect = LimitlessError("Error")

        result = await service.discover_new_tournaments(max_pages=1)

        assert len(result) == 0


class TestDiscoverOfficialTournaments:
    """Tests for discover_official_tournaments method."""

    @pytest.mark.asyncio
    async def test_discovers_official_tournaments(
        self,
        service: TournamentScrapeService,
        mock_session: AsyncMock,
        mock_client: AsyncMock,
    ) -> None:
        """Should return official tournaments not in database."""
        tournament = LimitlessTournament(
            name="Official Event",
            tournament_date=date.today() - timedelta(days=5),
            region="NA",
            game_format="standard",
            best_of=3,
            participant_count=500,
            source_url="https://limitlesstcg.com/tournaments/official/1",
            placements=[],
        )
        mock_client.fetch_official_tournament_listings.return_value = [tournament]

        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.execute.return_value = mock_result

        result = await service.discover_official_tournaments(lookback_days=30)

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_filters_old_tournaments(
        self,
        service: TournamentScrapeService,
        mock_session: AsyncMock,
        mock_client: AsyncMock,
    ) -> None:
        """Should filter tournaments outside lookback period."""
        old_tournament = LimitlessTournament(
            name="Old Event",
            tournament_date=date.today() - timedelta(days=100),
            region="NA",
            game_format="standard",
            best_of=3,
            participant_count=500,
            source_url="https://limitlesstcg.com/tournaments/official/old",
            placements=[],
        )
        mock_client.fetch_official_tournament_listings.return_value = [old_tournament]

        result = await service.discover_official_tournaments(lookback_days=30)

        assert len(result) == 0


class TestDiscoverJPCityLeagues:
    """Tests for discover_jp_city_leagues method."""

    @pytest.mark.asyncio
    async def test_discovers_jp_city_leagues(
        self,
        service: TournamentScrapeService,
        mock_session: AsyncMock,
        mock_client: AsyncMock,
    ) -> None:
        """Should return JP City League tournaments not in database."""
        tournament = LimitlessTournament(
            name="Tokyo City League",
            tournament_date=date.today() - timedelta(days=5),
            region="JP",
            game_format="standard",
            best_of=1,
            participant_count=64,
            source_url="https://limitlesstcg.com/tournaments/jp/1",
            placements=[],
        )
        mock_client.fetch_jp_city_league_listings.return_value = [tournament]

        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.execute.return_value = mock_result

        result = await service.discover_jp_city_leagues(lookback_days=30)

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_handles_fetch_error(
        self,
        service: TournamentScrapeService,
        mock_client: AsyncMock,
    ) -> None:
        """Should return empty list on fetch error."""
        mock_client.fetch_jp_city_league_listings.side_effect = LimitlessError("Error")

        result = await service.discover_jp_city_leagues()

        assert len(result) == 0


class TestProcessTournamentByUrl:
    """Tests for process_tournament_by_url method."""

    @pytest.mark.asyncio
    async def test_processes_standard_tournament(
        self,
        service: TournamentScrapeService,
        mock_session: AsyncMock,
        mock_client: AsyncMock,
        sample_placement: LimitlessPlacement,
    ) -> None:
        """Should process and save standard tournament."""
        mock_client.fetch_tournament_placements.return_value = [sample_placement]

        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.execute.return_value = mock_result

        result = await service.process_tournament_by_url(
            source_url="https://example.com/tournament",
            name="Test Tournament",
            tournament_date=date.today(),
            region="NA",
            fetch_decklists=False,
        )

        assert result.tournaments_saved == 1
        assert result.placements_saved == 1

    @pytest.mark.asyncio
    async def test_skips_existing_tournament(
        self,
        service: TournamentScrapeService,
        mock_session: AsyncMock,
    ) -> None:
        """Should skip if tournament already exists."""
        mock_result = MagicMock()
        mock_result.first.return_value = Tournament(
            id=uuid4(),
            name="Existing",
            date=date.today(),
            region="NA",
            format="standard",
            best_of=3,
            source_url="https://example.com/tournament",
        )
        mock_session.execute.return_value = mock_result

        result = await service.process_tournament_by_url(
            source_url="https://example.com/tournament",
            name="Test Tournament",
            tournament_date=date.today(),
            region="NA",
        )

        assert result.tournaments_skipped == 1
        assert result.tournaments_saved == 0

    @pytest.mark.asyncio
    async def test_processes_official_tournament(
        self,
        service: TournamentScrapeService,
        mock_session: AsyncMock,
        mock_client: AsyncMock,
        sample_placement: LimitlessPlacement,
    ) -> None:
        """Should use official placements fetcher when is_official=True."""
        mock_client.fetch_official_tournament_placements.return_value = [
            sample_placement
        ]

        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.execute.return_value = mock_result

        await service.process_tournament_by_url(
            source_url="https://example.com/official",
            name="Official Tournament",
            tournament_date=date.today(),
            region="NA",
            is_official=True,
            fetch_decklists=False,
        )

        mock_client.fetch_official_tournament_placements.assert_called_once()
        mock_client.fetch_tournament_placements.assert_not_called()

    @pytest.mark.asyncio
    async def test_processes_jp_city_league(
        self,
        service: TournamentScrapeService,
        mock_session: AsyncMock,
        mock_client: AsyncMock,
        sample_placement: LimitlessPlacement,
    ) -> None:
        """Should use JP placements fetcher when is_jp_city_league=True."""
        mock_client.fetch_jp_city_league_placements.return_value = [sample_placement]

        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.execute.return_value = mock_result

        await service.process_tournament_by_url(
            source_url="https://example.com/jp",
            name="JP City League",
            tournament_date=date.today(),
            region="JP",
            is_jp_city_league=True,
            fetch_decklists=False,
        )

        mock_client.fetch_jp_city_league_placements.assert_called_once()


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


class TestCreatePlacementWithNormalizer:
    """Tests for _create_placement with ArchetypeNormalizer."""

    @pytest.fixture
    def normalizer(self) -> ArchetypeNormalizer:
        detector = MagicMock(spec=ArchetypeDetector)
        detector.detect.return_value = "Rogue"
        return ArchetypeNormalizer(detector=detector)

    def test_normalizer_with_known_sprites(
        self,
        service: TournamentScrapeService,
        normalizer: ArchetypeNormalizer,
    ) -> None:
        """Should resolve archetype via sprite_lookup with normalizer."""
        placement = LimitlessPlacement(
            placement=1,
            player_name="Player",
            country="JP",
            archetype="Unknown",
            sprite_urls=["https://r2.limitlesstcg.net/pokemon/gen9/charizard.png"],
        )
        tournament_id = uuid4()

        result = service._create_placement(
            placement,
            tournament_id,
            normalizer=normalizer,
        )

        assert result.archetype == "Charizard ex"
        assert result.raw_archetype == "Unknown"
        assert result.archetype_detection_method == "sprite_lookup"
        assert result.raw_archetype_sprites == [
            "https://r2.limitlesstcg.net/pokemon/gen9/charizard.png"
        ]

    def test_normalizer_with_known_sprite_combo(
        self,
        service: TournamentScrapeService,
        normalizer: ArchetypeNormalizer,
    ) -> None:
        """Should resolve archetype via sprite_lookup for known combos."""
        placement = LimitlessPlacement(
            placement=2,
            player_name="Player",
            country="JP",
            archetype="Unknown",
            sprite_urls=[
                "https://example.com/grimmsnarl.png",
                "https://example.com/froslass.png",
            ],
        )
        tournament_id = uuid4()

        result = service._create_placement(
            placement,
            tournament_id,
            normalizer=normalizer,
        )

        assert result.archetype == "Froslass Grimmsnarl"
        assert result.archetype_detection_method == "sprite_lookup"
        assert result.raw_archetype_sprites is not None
        assert len(result.raw_archetype_sprites) == 2

    def test_legacy_path_without_normalizer(
        self,
        service: TournamentScrapeService,
        mock_detector: MagicMock,
    ) -> None:
        """Legacy path should leave new columns as None."""
        placement = LimitlessPlacement(
            placement=1,
            player_name="EN Player",
            country="US",
            archetype="Charizard ex",
            decklist=LimitlessDecklist(cards=[{"card_id": "sv3-125", "quantity": 2}]),
        )
        tournament_id = uuid4()

        result = service._create_placement(
            placement,
            tournament_id,
            normalizer=None,
        )

        assert result.archetype == "Charizard ex"
        assert result.raw_archetype is None
        assert result.raw_archetype_sprites is None
        assert result.archetype_detection_method is None

    def test_normalizer_text_label_fallback(
        self,
        service: TournamentScrapeService,
        normalizer: ArchetypeNormalizer,
    ) -> None:
        """Should fall back to text_label when no sprites or decklist."""
        placement = LimitlessPlacement(
            placement=4,
            player_name="Player",
            country="JP",
            archetype="Charizard",
            sprite_urls=[],
        )
        tournament_id = uuid4()

        result = service._create_placement(
            placement,
            tournament_id,
            normalizer=normalizer,
        )

        assert result.archetype == "Charizard ex"
        assert result.archetype_detection_method == "text_label"
        assert result.raw_archetype == "Charizard"
        assert result.raw_archetype_sprites is None


class TestSaveTournamentNormalizerAutoCreate:
    """Tests for save_tournament auto-creating normalizer for JP."""

    @pytest.fixture
    def jp_tournament(self) -> LimitlessTournament:
        return LimitlessTournament(
            name="City League Tokyo",
            tournament_date=date.today(),
            region="JP",
            game_format="standard",
            best_of=1,
            participant_count=32,
            source_url="https://play.limitlesstcg.com/tournament/jp001",
            placements=[
                LimitlessPlacement(
                    placement=1,
                    player_name="Player",
                    country="JP",
                    archetype="Unknown",
                    sprite_urls=[
                        "https://r2.limitlesstcg.net/pokemon/gen9/charizard.png",
                    ],
                ),
            ],
        )

    @pytest.mark.asyncio
    async def test_jp_tournament_auto_creates_normalizer(
        self,
        mock_session: AsyncMock,
        mock_client: AsyncMock,
        mock_detector: MagicMock,
        jp_tournament: LimitlessTournament,
    ) -> None:
        """save_tournament should auto-create normalizer for JP."""
        service = TournamentScrapeService(
            session=mock_session,
            client=mock_client,
            archetype_detector=mock_detector,
        )
        assert service.normalizer is None

        # Mock DB responses: JP mapping query, then load_db_sprites query
        mock_empty = MagicMock()
        mock_empty.all.return_value = []
        mock_empty.first.return_value = None
        mock_session.execute.return_value = mock_empty

        result = await service.save_tournament(jp_tournament)

        assert result is not None
        # The placement should have normalizer-resolved archetype
        added_calls = mock_session.add.call_args_list
        placement_obj = added_calls[1][0][0]  # 2nd add = placement
        assert placement_obj.archetype == "Charizard ex"
        assert placement_obj.archetype_detection_method == "sprite_lookup"
        assert placement_obj.raw_archetype_sprites is not None

    @pytest.mark.asyncio
    async def test_en_tournament_does_not_create_normalizer(
        self,
        mock_session: AsyncMock,
        mock_client: AsyncMock,
        mock_detector: MagicMock,
    ) -> None:
        """save_tournament should NOT create normalizer for EN."""
        service = TournamentScrapeService(
            session=mock_session,
            client=mock_client,
            archetype_detector=mock_detector,
        )
        en_tournament = LimitlessTournament(
            name="Regional Championship",
            tournament_date=date.today(),
            region="NA",
            game_format="standard",
            best_of=3,
            participant_count=256,
            source_url="https://play.limitlesstcg.com/tournament/en001",
            placements=[
                LimitlessPlacement(
                    placement=1,
                    player_name="Player",
                    country="US",
                    archetype="Charizard ex",
                ),
            ],
        )

        mock_empty = MagicMock()
        mock_empty.all.return_value = []
        mock_empty.first.return_value = None
        mock_session.execute.return_value = mock_empty

        result = await service.save_tournament(en_tournament)

        assert result is not None
        added_calls = mock_session.add.call_args_list
        placement_obj = added_calls[1][0][0]
        assert placement_obj.archetype_detection_method is None
        assert placement_obj.raw_archetype is None


class TestCreatePlacementJpMapping:
    """Tests for _create_placement JP card ID mapping."""

    def test_mapped_card_ids_pass_through(
        self,
        service: TournamentScrapeService,
    ) -> None:
        """Mapped JP card IDs should be translated to EN."""
        placement = LimitlessPlacement(
            placement=1,
            player_name="Player",
            country="JP",
            archetype="Charizard ex",
            decklist=LimitlessDecklist(
                cards=[
                    {"card_id": "SV7-018", "quantity": 2},
                    {"card_id": "SV7-055", "quantity": 3},
                ],
                source_url="https://example.com/deck",
            ),
        )
        jp_to_en = {
            "SV7-018": "sv7-28",
            "SV7-055": "sv7-65",
        }

        result = service._create_placement(
            placement,
            uuid4(),
            jp_to_en_mapping=jp_to_en,
        )

        assert result.decklist is not None
        assert len(result.decklist) == 2
        assert result.decklist[0]["card_id"] == "sv7-28"
        assert result.decklist[0]["jp_card_id"] == "SV7-018"
        assert result.decklist[1]["card_id"] == "sv7-65"
        assert result.decklist[1]["jp_card_id"] == "SV7-055"

    def test_unmapped_jp_ids_log_warning(
        self,
        service: TournamentScrapeService,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Unmapped JP card IDs should produce a warning."""
        placement = LimitlessPlacement(
            placement=3,
            player_name="Player",
            country="JP",
            archetype="Unknown",
            decklist=LimitlessDecklist(
                cards=[
                    {"card_id": "SV7-018", "quantity": 2},
                    {"card_id": "JP-ONLY-001", "quantity": 1},
                    {"card_id": "JP-ONLY-002", "quantity": 4},
                ],
                source_url="https://example.com/deck",
            ),
        )
        jp_to_en = {"SV7-018": "sv7-28"}

        import logging

        with caplog.at_level(logging.WARNING):
            result = service._create_placement(
                placement,
                uuid4(),
                jp_to_en_mapping=jp_to_en,
            )

        assert result.decklist is not None
        assert len(result.decklist) == 3
        # Unmapped cards keep their JP ID
        assert result.decklist[1]["card_id"] == "JP-ONLY-001"
        assert result.decklist[2]["card_id"] == "JP-ONLY-002"

        assert any("Unmapped JP card IDs" in r.message for r in caplog.records)
        warning_record = next(
            r for r in caplog.records if "Unmapped JP card IDs" in r.message
        )
        assert "2 of 3" in warning_record.message

    def test_no_warning_when_all_mapped(
        self,
        service: TournamentScrapeService,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """No warning when all JP cards have EN mappings."""
        placement = LimitlessPlacement(
            placement=1,
            player_name="Player",
            country="JP",
            archetype="Charizard ex",
            decklist=LimitlessDecklist(
                cards=[
                    {"card_id": "SV7-018", "quantity": 2},
                ],
                source_url="https://example.com/deck",
            ),
        )
        jp_to_en = {"SV7-018": "sv7-28"}

        import logging

        with caplog.at_level(logging.WARNING):
            service._create_placement(
                placement,
                uuid4(),
                jp_to_en_mapping=jp_to_en,
            )

        assert not any("Unmapped JP card IDs" in r.message for r in caplog.records)


class TestCardIdVariants:
    """Tests for _card_id_variants static method."""

    def test_empty_string(self) -> None:
        result = TournamentScrapeService._card_id_variants("")
        assert result == set()

    def test_whitespace_only(self) -> None:
        result = TournamentScrapeService._card_id_variants("  ")
        assert result == set()

    def test_no_hyphen(self) -> None:
        result = TournamentScrapeService._card_id_variants("SV7")
        assert "SV7" in result
        assert "sv7" in result
        assert "SV7" in result

    def test_standard_card_id(self) -> None:
        result = TournamentScrapeService._card_id_variants("SV7-018")
        assert "sv7-18" in result
        assert "SV7-018" in result
        assert "sv7-018" in result
        assert "SV7-18" in result

    def test_zero_padding_variants(self) -> None:
        result = TournamentScrapeService._card_id_variants("SV9-5")
        assert "sv9-5" in result
        assert "sv9-05" in result
        assert "sv9-005" in result
        assert "SV9-5" in result

    def test_case_variants(self) -> None:
        result = TournamentScrapeService._card_id_variants("SV8a-001")
        # Set part case variants
        assert any("sv8a-" in v for v in result)
        assert any("SV8A-" in v for v in result)
        assert any("SV8a-" in v for v in result)

    def test_letter_prefix_in_num_part(self) -> None:
        """Card IDs like 'SV2D-TG01' with letter prefix."""
        result = TournamentScrapeService._card_id_variants("SV2-TG01")
        assert "SV2-TG01" in result
        assert "sv2-tg1" in result
        assert "sv2-TG1" in result


class TestGetJpToEnMapping:
    """Tests for _get_jp_to_en_mapping caching and expansion."""

    @pytest.mark.asyncio
    async def test_loads_and_caches_mapping(
        self, service: TournamentScrapeService, mock_session: AsyncMock
    ) -> None:
        """First call queries DB, second returns cached."""
        mock_result = MagicMock()
        mock_result.__iter__ = MagicMock(
            return_value=iter(
                [
                    MagicMock(jp_card_id="SV9-001", en_card_id="sv09-1"),
                ]
            )
        )
        mock_session.execute.return_value = mock_result

        mapping1 = await service._get_jp_to_en_mapping()
        mapping2 = await service._get_jp_to_en_mapping()

        # Only one DB query (cached on second call)
        assert mock_session.execute.call_count == 1
        assert mapping1 is mapping2
        # Variants should be expanded
        assert "sv9-1" in mapping1 or "sv9-001" in mapping1

    @pytest.mark.asyncio
    async def test_empty_mapping(
        self, service: TournamentScrapeService, mock_session: AsyncMock
    ) -> None:
        """Empty DB returns empty mapping."""
        mock_result = MagicMock()
        mock_result.__iter__ = MagicMock(return_value=iter([]))
        mock_session.execute.return_value = mock_result

        mapping = await service._get_jp_to_en_mapping()
        assert mapping == {}


class TestGetDetectorForRegion:
    """Tests for _get_detector_for_region."""

    def test_returns_default_for_non_jp(
        self, service: TournamentScrapeService, mock_detector: MagicMock
    ) -> None:
        result = service._get_detector_for_region("NA")
        assert result is mock_detector

    def test_returns_default_when_no_jp_mapping(
        self, service: TournamentScrapeService, mock_detector: MagicMock
    ) -> None:
        """JP region without loaded mapping returns default detector."""
        service._jp_to_en_mapping = None
        result = service._get_detector_for_region("JP")
        assert result is mock_detector

    def test_returns_jp_detector_with_mapping(
        self, service: TournamentScrapeService
    ) -> None:
        """JP region with mapping returns new detector."""
        service._jp_to_en_mapping = {"sv9-1": "sv09-1"}
        result = service._get_detector_for_region("JP")
        assert isinstance(result, ArchetypeDetector)


class TestScrapeOfficialTournaments:
    """Tests for scrape_official_tournaments."""

    @pytest.mark.asyncio
    async def test_happy_path(
        self,
        service: TournamentScrapeService,
        mock_session: AsyncMock,
        mock_client: AsyncMock,
        sample_placement: LimitlessPlacement,
    ) -> None:
        """Scrapes and saves official tournaments."""
        tournament = LimitlessTournament(
            name="Portland Regional",
            tournament_date=date.today() - timedelta(days=5),
            region="NA",
            game_format="standard",
            best_of=3,
            participant_count=500,
            source_url="https://limitlesstcg.com/tournament/1",
            placements=[],
        )
        mock_client.fetch_official_tournament_listings.return_value = [tournament]
        mock_client.fetch_official_tournament_placements.return_value = [
            sample_placement
        ]

        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.execute.return_value = mock_result

        result = await service.scrape_official_tournaments(
            lookback_days=30, fetch_decklists=False
        )

        assert result.tournaments_scraped == 1
        assert result.tournaments_saved == 1
        assert result.placements_saved == 1

    @pytest.mark.asyncio
    async def test_listing_fetch_error(
        self,
        service: TournamentScrapeService,
        mock_client: AsyncMock,
    ) -> None:
        """Returns early with error on listing fetch failure."""
        mock_client.fetch_official_tournament_listings.side_effect = LimitlessError(
            "Network error"
        )

        result = await service.scrape_official_tournaments()

        assert result.tournaments_scraped == 0
        assert len(result.errors) == 1
        assert "Error fetching official" in result.errors[0]

    @pytest.mark.asyncio
    async def test_skips_existing(
        self,
        service: TournamentScrapeService,
        mock_session: AsyncMock,
        mock_client: AsyncMock,
    ) -> None:
        """Skips tournaments that already exist."""
        tournament = LimitlessTournament(
            name="Existing Regional",
            tournament_date=date.today() - timedelta(days=5),
            region="NA",
            game_format="standard",
            best_of=3,
            participant_count=300,
            source_url="https://limitlesstcg.com/tournament/existing",
            placements=[],
        )
        mock_client.fetch_official_tournament_listings.return_value = [tournament]

        mock_result = MagicMock()
        mock_result.first.return_value = MagicMock()  # exists
        mock_session.execute.return_value = mock_result

        result = await service.scrape_official_tournaments(lookback_days=30)

        assert result.tournaments_skipped == 1
        assert result.tournaments_saved == 0

    @pytest.mark.asyncio
    async def test_processing_error_continues(
        self,
        service: TournamentScrapeService,
        mock_session: AsyncMock,
        mock_client: AsyncMock,
    ) -> None:
        """Processing error is recorded but scrape continues."""
        tournament = LimitlessTournament(
            name="Bad Regional",
            tournament_date=date.today() - timedelta(days=5),
            region="NA",
            game_format="standard",
            best_of=3,
            participant_count=300,
            source_url="https://limitlesstcg.com/tournament/bad",
            placements=[],
        )
        mock_client.fetch_official_tournament_listings.return_value = [tournament]
        mock_client.fetch_official_tournament_placements.side_effect = LimitlessError(
            "Parse error"
        )

        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.execute.return_value = mock_result

        result = await service.scrape_official_tournaments(lookback_days=30)

        assert len(result.errors) == 1
        assert "Error processing official" in result.errors[0]


class TestScrapeJPCityLeagues:
    """Tests for scrape_jp_city_leagues."""

    @pytest.mark.asyncio
    async def test_happy_path(
        self,
        service: TournamentScrapeService,
        mock_session: AsyncMock,
        mock_client: AsyncMock,
        sample_placement: LimitlessPlacement,
    ) -> None:
        """Scrapes and saves JP City Leagues."""
        tournament = LimitlessTournament(
            name="Tokyo City League",
            tournament_date=date.today() - timedelta(days=3),
            region="JP",
            game_format="standard",
            best_of=1,
            participant_count=64,
            source_url="https://limitlesstcg.com/tournaments/jp/1",
            placements=[],
        )
        mock_client.fetch_jp_city_league_listings.return_value = [tournament]
        mock_client.fetch_jp_city_league_placements.return_value = [sample_placement]

        # Mock: no existing, empty mapping, empty sprites DB
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_result.__iter__ = MagicMock(return_value=iter([]))
        mock_result.all = MagicMock(return_value=[])
        mock_session.execute.return_value = mock_result

        result = await service.scrape_jp_city_leagues(
            lookback_days=30, fetch_decklists=False
        )

        assert result.tournaments_scraped == 1
        assert result.tournaments_saved == 1

    @pytest.mark.asyncio
    async def test_listing_fetch_error(
        self,
        service: TournamentScrapeService,
        mock_session: AsyncMock,
        mock_client: AsyncMock,
    ) -> None:
        """Returns early with error on listing failure."""
        # Need mock for _get_jp_to_en_mapping DB call
        mock_result = MagicMock()
        mock_result.__iter__ = MagicMock(return_value=iter([]))
        mock_session.execute.return_value = mock_result

        mock_client.fetch_jp_city_league_listings.side_effect = LimitlessError(
            "Network error"
        )

        result = await service.scrape_jp_city_leagues()

        assert len(result.errors) == 1
        assert "Error fetching JP City League" in result.errors[0]

    @pytest.mark.asyncio
    async def test_skips_existing(
        self,
        service: TournamentScrapeService,
        mock_session: AsyncMock,
        mock_client: AsyncMock,
    ) -> None:
        """Skips existing JP tournaments."""
        tournament = LimitlessTournament(
            name="Existing CL",
            tournament_date=date.today() - timedelta(days=3),
            region="JP",
            game_format="standard",
            best_of=1,
            participant_count=64,
            source_url="https://limitlesstcg.com/tournaments/jp/x",
            placements=[],
        )
        mock_client.fetch_jp_city_league_listings.return_value = [tournament]

        # First call: mapping query (returns iter), second: exists check
        call_count = 0

        def execute_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            mock = MagicMock()
            if call_count == 1:
                # JP mapping query
                mock.__iter__ = MagicMock(return_value=iter([]))
                return mock
            # Exists check — tournament found
            mock.first.return_value = MagicMock()
            return mock

        mock_session.execute = AsyncMock(side_effect=execute_side_effect)

        result = await service.scrape_jp_city_leagues(lookback_days=30)

        assert result.tournaments_skipped == 1
        assert result.tournaments_saved == 0


class TestRescrapeTournament:
    """Tests for rescrape_tournament."""

    @pytest.mark.asyncio
    async def test_rescrape_jp_city_league(
        self,
        service: TournamentScrapeService,
        mock_session: AsyncMock,
        mock_client: AsyncMock,
        sample_placement: LimitlessPlacement,
    ) -> None:
        """Rescrapes JP city league by URL pattern."""
        tournament = MagicMock(spec=Tournament)
        tournament.id = uuid4()
        tournament.name = "Tokyo CL"
        tournament.region = "JP"
        tournament.source_url = "https://play.limitlesstcg.com/tournaments/jp/123"

        mock_client.fetch_jp_city_league_placements.return_value = [sample_placement]

        # Mock mapping + sprites DB queries
        mock_result = MagicMock()
        mock_result.__iter__ = MagicMock(return_value=iter([]))
        mock_result.all = MagicMock(return_value=[])
        mock_session.execute.return_value = mock_result

        count = await service.rescrape_tournament(tournament, fetch_decklists=False)

        assert count == 1
        mock_client.fetch_jp_city_league_placements.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_rescrape_official_tournament(
        self,
        service: TournamentScrapeService,
        mock_session: AsyncMock,
        mock_client: AsyncMock,
        sample_placement: LimitlessPlacement,
    ) -> None:
        """Rescrapes official tournament by URL pattern."""
        tournament = MagicMock(spec=Tournament)
        tournament.id = uuid4()
        tournament.name = "Portland Regional"
        tournament.region = "NA"
        tournament.source_url = "https://limitlesstcg.com/tournament/12345"

        mock_client.fetch_official_tournament_placements.return_value = [
            sample_placement
        ]

        count = await service.rescrape_tournament(tournament, fetch_decklists=False)

        assert count == 1
        mock_client.fetch_official_tournament_placements.assert_called_once()

    @pytest.mark.asyncio
    async def test_rescrape_standard_tournament(
        self,
        service: TournamentScrapeService,
        mock_session: AsyncMock,
        mock_client: AsyncMock,
        sample_placement: LimitlessPlacement,
    ) -> None:
        """Rescrapes standard tournament (fallback URL)."""
        tournament = MagicMock(spec=Tournament)
        tournament.id = uuid4()
        tournament.name = "Local Event"
        tournament.region = "NA"
        tournament.source_url = "https://play.limitlesstcg.com/other/99999"

        mock_client.fetch_tournament_placements.return_value = [sample_placement]

        count = await service.rescrape_tournament(tournament, fetch_decklists=False)

        assert count == 1
        mock_client.fetch_tournament_placements.assert_called_once()

    @pytest.mark.asyncio
    async def test_rescrape_no_source_url(
        self,
        service: TournamentScrapeService,
    ) -> None:
        """Returns 0 when tournament has no source_url."""
        tournament = MagicMock(spec=Tournament)
        tournament.name = "No URL"
        tournament.source_url = None

        count = await service.rescrape_tournament(tournament)
        assert count == 0

    @pytest.mark.asyncio
    async def test_rescrape_empty_source_url(
        self,
        service: TournamentScrapeService,
    ) -> None:
        """Returns 0 when tournament has empty source_url."""
        tournament = MagicMock(spec=Tournament)
        tournament.name = "Empty URL"
        tournament.source_url = ""

        count = await service.rescrape_tournament(tournament)
        assert count == 0

    @pytest.mark.asyncio
    async def test_rescrape_deletes_old_placements(
        self,
        service: TournamentScrapeService,
        mock_session: AsyncMock,
        mock_client: AsyncMock,
    ) -> None:
        """Old placements are deleted before re-fetch."""
        tournament = MagicMock(spec=Tournament)
        tournament.id = uuid4()
        tournament.name = "Tournament"
        tournament.region = "NA"
        tournament.source_url = "https://play.limitlesstcg.com/tournament/123"

        mock_client.fetch_tournament_placements.return_value = []

        await service.rescrape_tournament(tournament, fetch_decklists=False)

        # First execute call should be the delete
        assert mock_session.execute.call_count >= 1


class TestFindTournamentsNeedingRescrape:
    """Tests for find_tournaments_needing_rescrape."""

    @pytest.mark.asyncio
    async def test_finds_tournaments_over_50pct_empty(
        self,
        service: TournamentScrapeService,
        mock_session: AsyncMock,
    ) -> None:
        """Returns tournaments with >50% empty archetypes."""
        tournament = MagicMock(spec=Tournament)
        tournament.id = uuid4()

        # First query: get all tournaments
        tournaments_result = MagicMock()
        tournaments_result.scalars.return_value.all.return_value = [tournament]

        # Second query: placement counts (60% empty)
        counts_result = MagicMock()
        count_row = MagicMock()
        count_row.total = 10
        count_row.non_empty = 4  # 60% empty
        counts_result.one.return_value = count_row

        mock_session.execute = AsyncMock(
            side_effect=[tournaments_result, counts_result]
        )

        result = await service.find_tournaments_needing_rescrape()

        assert len(result) == 1
        assert result[0] is tournament

    @pytest.mark.asyncio
    async def test_excludes_tournaments_under_50pct_empty(
        self,
        service: TournamentScrapeService,
        mock_session: AsyncMock,
    ) -> None:
        """Excludes tournaments with <=50% empty archetypes."""
        tournament = MagicMock(spec=Tournament)
        tournament.id = uuid4()

        tournaments_result = MagicMock()
        tournaments_result.scalars.return_value.all.return_value = [tournament]

        counts_result = MagicMock()
        count_row = MagicMock()
        count_row.total = 10
        count_row.non_empty = 8  # 20% empty
        counts_result.one.return_value = count_row

        mock_session.execute = AsyncMock(
            side_effect=[tournaments_result, counts_result]
        )

        result = await service.find_tournaments_needing_rescrape()

        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_skips_tournaments_with_no_placements(
        self,
        service: TournamentScrapeService,
        mock_session: AsyncMock,
    ) -> None:
        """Skips tournaments with 0 placements."""
        tournament = MagicMock(spec=Tournament)
        tournament.id = uuid4()

        tournaments_result = MagicMock()
        tournaments_result.scalars.return_value.all.return_value = [tournament]

        counts_result = MagicMock()
        count_row = MagicMock()
        count_row.total = 0
        count_row.non_empty = 0
        counts_result.one.return_value = count_row

        mock_session.execute = AsyncMock(
            side_effect=[tournaments_result, counts_result]
        )

        result = await service.find_tournaments_needing_rescrape()

        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_empty_result(
        self,
        service: TournamentScrapeService,
        mock_session: AsyncMock,
    ) -> None:
        """Returns empty list when no tournaments found."""
        tournaments_result = MagicMock()
        tournaments_result.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=tournaments_result)

        result = await service.find_tournaments_needing_rescrape()

        assert result == []


class TestCreatePlacementEdgeCases:
    """Edge case tests for _create_placement."""

    def test_skips_cards_without_card_id(
        self,
        service: TournamentScrapeService,
    ) -> None:
        """Cards without card_id should be skipped in decklist."""
        placement = LimitlessPlacement(
            placement=1,
            player_name="Player",
            country="US",
            archetype="Charizard ex",
            decklist=LimitlessDecklist(
                cards=[
                    {"card_id": "sv3-125", "quantity": 2},
                    {"card_id": "", "quantity": 1},  # empty
                    {"card_id": None, "quantity": 1},  # None
                    {"quantity": 1},  # missing
                ],
                source_url="https://example.com/deck",
            ),
        )

        result = service._create_placement(placement, uuid4())

        # Only the valid card should be included
        assert result.decklist is not None
        assert len(result.decklist) == 1
        assert result.decklist[0]["card_id"] == "sv3-125"

    def test_decklist_with_no_valid_cards(
        self,
        service: TournamentScrapeService,
    ) -> None:
        """Decklist with all invalid cards still creates placement."""
        placement = LimitlessPlacement(
            placement=1,
            player_name="Player",
            country="US",
            archetype="Unknown",
            decklist=LimitlessDecklist(
                cards=[{"quantity": 1}],
                source_url="https://example.com/deck",
            ),
        )

        result = service._create_placement(placement, uuid4())

        assert result.decklist is not None
        assert len(result.decklist) == 0

    def test_invalid_decklist_treated_as_none(
        self,
        service: TournamentScrapeService,
    ) -> None:
        """Invalid decklist (is_valid=False) treated as no decklist."""
        decklist = MagicMock()
        decklist.is_valid = False
        placement = LimitlessPlacement(
            placement=1,
            player_name="Player",
            country="US",
            archetype="Unknown",
            decklist=decklist,
        )

        result = service._create_placement(placement, uuid4())

        assert result.decklist is None


class TestCardIdMappingConfidence:
    """Tests for confidence column on CardIdMapping model."""

    def test_confidence_column_exists(self) -> None:
        """CardIdMapping should have a confidence attribute."""
        from src.models.card_id_mapping import CardIdMapping

        assert hasattr(CardIdMapping, "confidence")
