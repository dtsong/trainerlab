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
from src.services.archetype_detector import ArchetypeDetector
from src.services.archetype_normalizer import ArchetypeNormalizer
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

    def test_normalizer_with_unknown_sprites(
        self,
        service: TournamentScrapeService,
        normalizer: ArchetypeNormalizer,
    ) -> None:
        """Should auto-derive archetype for unknown sprite combos."""
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

        assert result.archetype == "Grimmsnarl Froslass"
        assert result.archetype_detection_method == "auto_derive"
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
