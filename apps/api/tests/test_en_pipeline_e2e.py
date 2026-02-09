"""E2E tests for EN tournament pipeline and failure scenarios.

Tests the full flow: scrape → archetype detect → save → verify,
plus failure recovery and no-op scenarios.
"""

from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from src.clients.limitless import (
    LimitlessDecklist,
    LimitlessError,
    LimitlessPlacement,
    LimitlessTournament,
)
from src.services.archetype_detector import ArchetypeDetector
from src.services.tournament_scrape import TournamentScrapeService


def _make_tournament(name: str, source_url: str, **kwargs) -> LimitlessTournament:
    """Helper to create a tournament with defaults."""
    defaults = {
        "tournament_date": date.today() - timedelta(days=3),
        "region": "NA",
        "game_format": "standard",
        "best_of": 3,
        "participant_count": 256,
        "placements": [],
    }
    defaults.update(kwargs)
    return LimitlessTournament(name=name, source_url=source_url, **defaults)


def _make_placement(
    rank: int,
    player: str,
    archetype: str,
    decklist: LimitlessDecklist | None = None,
) -> LimitlessPlacement:
    return LimitlessPlacement(
        placement=rank,
        player_name=player,
        country="US",
        archetype=archetype,
        decklist=decklist,
    )


def _not_found_result() -> MagicMock:
    """Mock session.execute result where tournament doesn't exist."""
    mock = MagicMock()
    mock.first.return_value = None
    return mock


class TestENTournamentPipeline:
    """EN scrape → archetype detect → save → verify placements."""

    @pytest.mark.asyncio
    async def test_full_en_scrape_pipeline(self) -> None:
        """Scrape EN tournament, detect archetypes, save, verify."""
        session = AsyncMock()
        session.add = MagicMock()
        client = AsyncMock()

        detector = ArchetypeDetector()

        tournament = _make_tournament(
            "Portland Regional",
            "https://play.limitlesstcg.com/tournament/12345",
            participant_count=500,
        )

        decklist = LimitlessDecklist(
            cards=[
                {"card_id": "sv3-125", "name": "Charizard ex", "quantity": 2},
                {"card_id": "sv3-46", "name": "Charmander", "quantity": 4},
            ],
            source_url="https://example.com/deck/1",
        )

        placements = [
            _make_placement(1, "Alice", "Charizard ex", decklist),
            _make_placement(2, "Bob", "Lugia VSTAR"),
            _make_placement(3, "Charlie", "Gardevoir ex"),
        ]

        client.fetch_tournament_listings.return_value = [tournament]
        client.fetch_tournament_placements.return_value = placements
        client.fetch_decklist.return_value = decklist
        session.execute.return_value = _not_found_result()

        service = TournamentScrapeService(
            session=session,
            client=client,
            archetype_detector=detector,
        )

        result = await service.scrape_new_tournaments(
            region="en",
            game_format="standard",
            lookback_days=7,
            max_pages=1,
            fetch_decklists=True,
        )

        assert result.tournaments_saved == 1
        assert result.placements_saved == 3
        assert result.success is True

        # Verify all 4 objects added (1 tournament + 3 placements)
        assert session.add.call_count == 4
        session.commit.assert_called_once()

        # Check placement archetypes were preserved/detected
        added = [c[0][0] for c in session.add.call_args_list]
        placement_objs = added[1:]  # skip tournament
        archetypes = [p.archetype for p in placement_objs]
        assert "Charizard ex" in archetypes

    @pytest.mark.asyncio
    async def test_en_official_scrape_pipeline(self) -> None:
        """Scrape official EN tournament end-to-end."""
        session = AsyncMock()
        session.add = MagicMock()
        client = AsyncMock()
        detector = ArchetypeDetector()

        tournament = _make_tournament(
            "LAIC 2025",
            "https://limitlesstcg.com/tournament/laic",
            participant_count=1000,
        )

        placements = [
            _make_placement(1, "Winner", "Charizard ex"),
            _make_placement(2, "Runner", "Lugia VSTAR"),
        ]

        client.fetch_official_tournament_listings.return_value = [tournament]
        client.fetch_official_tournament_placements.return_value = placements
        session.execute.return_value = _not_found_result()

        service = TournamentScrapeService(
            session=session,
            client=client,
            archetype_detector=detector,
        )

        result = await service.scrape_official_tournaments(
            lookback_days=30, fetch_decklists=False
        )

        assert result.tournaments_saved == 1
        assert result.placements_saved == 2
        assert result.success is True


class TestPartialScrapeFailureRecovery:
    """Scrape fails mid-tournament, remaining still process."""

    @pytest.mark.asyncio
    async def test_second_tournament_fails_others_saved(self) -> None:
        """3 tournaments: 1st saves, 2nd fails, 3rd saves."""
        session = AsyncMock()
        session.add = MagicMock()
        client = AsyncMock()
        detector = ArchetypeDetector()

        t1 = _make_tournament("Good 1", "https://example.com/t1")
        t2 = _make_tournament("Bad One", "https://example.com/t2")
        t3 = _make_tournament("Good 3", "https://example.com/t3")

        placement = _make_placement(1, "Player", "Charizard ex")

        client.fetch_tournament_listings.return_value = [t1, t2, t3]

        # t2 fails when fetching placements
        call_count = 0

        async def placements_side_effect(url, **kwargs):
            nonlocal call_count
            call_count += 1
            if "t2" in url:
                raise LimitlessError("Server error on t2")
            return [placement]

        client.fetch_tournament_placements = AsyncMock(
            side_effect=placements_side_effect
        )
        session.execute.return_value = _not_found_result()

        service = TournamentScrapeService(
            session=session,
            client=client,
            archetype_detector=detector,
        )

        result = await service.scrape_new_tournaments(
            max_pages=1, fetch_decklists=False
        )

        # t1 and t3 saved, t2 had error
        assert result.tournaments_saved == 2
        assert len(result.errors) == 1
        assert "Bad One" in result.errors[0]

    @pytest.mark.asyncio
    async def test_decklist_failure_does_not_block_save(self) -> None:
        """Decklist fetch fails but tournament still saves."""
        session = AsyncMock()
        session.add = MagicMock()
        client = AsyncMock()
        detector = ArchetypeDetector()

        tournament = _make_tournament("Tourney", "https://example.com/t1")
        placement = LimitlessPlacement(
            placement=1,
            player_name="Player",
            country="US",
            archetype="Charizard ex",
            decklist_url="https://example.com/deck/1",
        )

        client.fetch_tournament_listings.return_value = [tournament]
        client.fetch_tournament_placements.return_value = [placement]
        client.fetch_decklist.side_effect = LimitlessError("Timeout")
        session.execute.return_value = _not_found_result()

        service = TournamentScrapeService(
            session=session,
            client=client,
            archetype_detector=detector,
        )

        result = await service.scrape_new_tournaments(max_pages=1, fetch_decklists=True)

        assert result.tournaments_saved == 1
        assert result.decklists_saved == 0
        assert result.success is True  # decklist errors are soft


class TestDBWriteFailureRecovery:
    """DB write fails → error recorded, pipeline continues."""

    @pytest.mark.asyncio
    async def test_db_commit_fails_error_recorded(self) -> None:
        """DB error during save_tournament is recorded, scrape continues."""
        session = AsyncMock()
        session.add = MagicMock()
        client = AsyncMock()
        detector = ArchetypeDetector()

        t1 = _make_tournament("Good", "https://example.com/t1")
        t2 = _make_tournament("DB Fail", "https://example.com/t2")

        placement = _make_placement(1, "Player", "Charizard ex")

        client.fetch_tournament_listings.return_value = [t1, t2]
        client.fetch_tournament_placements.return_value = [placement]
        session.execute.return_value = _not_found_result()

        # First commit succeeds, second fails
        session.commit = AsyncMock(
            side_effect=[None, SQLAlchemyError("Connection lost"), None]
        )
        session.rollback = AsyncMock()

        service = TournamentScrapeService(
            session=session,
            client=client,
            archetype_detector=detector,
        )

        result = await service.scrape_new_tournaments(
            max_pages=1, fetch_decklists=False
        )

        assert result.tournaments_saved == 1
        assert len(result.errors) == 1
        assert "DB Fail" in result.errors[0]

    @pytest.mark.asyncio
    async def test_official_db_error_recorded(self) -> None:
        """Official pipeline records DB errors and continues."""
        session = AsyncMock()
        session.add = MagicMock()
        client = AsyncMock()

        tournament = _make_tournament(
            "DB Fail Regional",
            "https://limitlesstcg.com/tournament/fail",
        )
        placement = _make_placement(1, "Player", "Charizard ex")

        client.fetch_official_tournament_listings.return_value = [tournament]
        client.fetch_official_tournament_placements.return_value = [placement]
        session.execute.return_value = _not_found_result()
        session.commit = AsyncMock(side_effect=SQLAlchemyError("Timeout"))
        session.rollback = AsyncMock()

        service = TournamentScrapeService(
            session=session,
            client=client,
        )

        result = await service.scrape_official_tournaments(
            lookback_days=30, fetch_decklists=False
        )

        assert result.tournaments_saved == 0
        assert len(result.errors) == 1


class TestNoNewTournamentsNoOp:
    """Pipeline runs with no new tournaments → clean no-op."""

    @pytest.mark.asyncio
    async def test_scrape_no_new_is_clean_noop(self) -> None:
        """All tournaments already exist → no saves, no errors."""
        session = AsyncMock()
        client = AsyncMock()

        tournament = _make_tournament("Existing", "https://example.com/existing")

        client.fetch_tournament_listings.return_value = [tournament]

        # Tournament exists
        mock_result = MagicMock()
        mock_result.first.return_value = MagicMock()  # found
        session.execute.return_value = mock_result

        service = TournamentScrapeService(session=session, client=client)

        result = await service.scrape_new_tournaments(
            max_pages=1, fetch_decklists=False
        )

        assert result.tournaments_scraped == 1
        assert result.tournaments_saved == 0
        assert result.tournaments_skipped == 1
        assert result.placements_saved == 0
        assert result.success is True

    @pytest.mark.asyncio
    async def test_scrape_empty_listing_is_clean_noop(self) -> None:
        """No tournaments in listing → clean no-op."""
        session = AsyncMock()
        client = AsyncMock()
        client.fetch_tournament_listings.return_value = []

        service = TournamentScrapeService(session=session, client=client)

        result = await service.scrape_new_tournaments(max_pages=1)

        assert result.tournaments_scraped == 0
        assert result.tournaments_saved == 0
        assert result.success is True
        session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_official_no_new_is_clean_noop(self) -> None:
        """All official tournaments exist → clean no-op."""
        session = AsyncMock()
        client = AsyncMock()

        tournament = _make_tournament(
            "Existing Regional",
            "https://limitlesstcg.com/tournament/exists",
        )
        client.fetch_official_tournament_listings.return_value = [tournament]

        mock_result = MagicMock()
        mock_result.first.return_value = MagicMock()
        session.execute.return_value = mock_result

        service = TournamentScrapeService(session=session, client=client)

        result = await service.scrape_official_tournaments(lookback_days=30)

        assert result.tournaments_skipped == 1
        assert result.tournaments_saved == 0
        assert result.success is True

    @pytest.mark.asyncio
    async def test_jp_no_new_is_clean_noop(self) -> None:
        """All JP tournaments exist → clean no-op."""
        session = AsyncMock()
        client = AsyncMock()

        tournament = _make_tournament(
            "Existing CL",
            "https://limitlesstcg.com/tournaments/jp/exists",
            region="JP",
            best_of=1,
        )
        client.fetch_jp_city_league_listings.return_value = [tournament]

        call_count = 0

        def execute_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            mock = MagicMock()
            if call_count == 1:
                # JP mapping query
                mock.__iter__ = MagicMock(return_value=iter([]))
                return mock
            # Exists check — found
            mock.first.return_value = MagicMock()
            return mock

        session.execute = AsyncMock(side_effect=execute_side_effect)

        service = TournamentScrapeService(session=session, client=client)

        result = await service.scrape_jp_city_leagues(lookback_days=30)

        assert result.tournaments_skipped == 1
        assert result.tournaments_saved == 0
        assert result.success is True
