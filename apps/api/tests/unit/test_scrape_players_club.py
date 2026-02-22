"""Unit tests for scrape_players_club pipeline."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.clients.players_club import (
    PlayersClubClient,
    PlayersClubError,
    PlayersClubPlacement,
    PlayersClubTournament,
    PlayersClubTournamentDetail,
)
from src.pipelines.scrape_players_club import (
    ScrapePlayersClubResult,
    _process_tournament,
    scrape_players_club,
)


def _make_tournament(
    tid: str = "t1",
    name: str = "Tokyo City League",
) -> PlayersClubTournament:
    return PlayersClubTournament(
        tournament_id=tid,
        name=name,
        date=date(2026, 2, 1),
        participant_count=32,
        source_url=(f"https://players.pokemon-card.com/event/{tid}"),
    )


def _make_detail(
    tournament: PlayersClubTournament | None = None,
) -> PlayersClubTournamentDetail:
    t = tournament or _make_tournament()
    return PlayersClubTournamentDetail(
        tournament=t,
        placements=[
            PlayersClubPlacement(
                placement=1,
                player_name="Taro",
                archetype_name="Charizard ex",
            ),
            PlayersClubPlacement(
                placement=2,
                player_name="Jiro",
                archetype_name="Lugia VSTAR",
            ),
        ],
    )


class TestScrapePlayersClub:
    @pytest.mark.asyncio
    async def test_scrape_happy_path(self):
        tournaments = [_make_tournament()]
        detail = _make_detail(tournaments[0])

        mock_client = AsyncMock(spec=PlayersClubClient)
        mock_client.fetch_recent_tournaments = AsyncMock(return_value=tournaments)
        mock_client.fetch_tournament_detail = AsyncMock(
            return_value=detail,
        )
        mock_client.__aenter__ = AsyncMock(
            return_value=mock_client,
        )
        mock_client.__aexit__ = AsyncMock(
            return_value=None,
        )

        mock_session = AsyncMock()
        # No existing tournament
        mock_exec = MagicMock()
        mock_exec.first.return_value = None
        mock_session.execute = AsyncMock(
            return_value=mock_exec,
        )

        mock_normalizer = MagicMock()
        mock_normalizer.load_db_sprites = AsyncMock()
        mock_normalizer.resolve.return_value = (
            "Charizard ex",
            [],
            "text_label",
        )

        with (
            patch(
                "src.pipelines.scrape_players_club.PlayersClubClient",
                return_value=mock_client,
            ),
            patch(
                "src.pipelines.scrape_players_club.async_session_factory",
            ) as mock_sf,
            patch(
                "src.pipelines.scrape_players_club.ArchetypeNormalizer",
                return_value=mock_normalizer,
            ),
        ):
            mock_sf.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_sf.return_value.__aexit__ = AsyncMock(
                return_value=None,
            )

            result = await scrape_players_club(
                lookback_days=30,
            )

        assert result.tournaments_discovered == 1
        assert result.tournaments_created == 1
        assert result.placements_created == 2
        assert result.success is True

    @pytest.mark.asyncio
    async def test_dry_run_skips_processing(self):
        tournaments = [_make_tournament()]

        mock_client = AsyncMock(spec=PlayersClubClient)
        mock_client.fetch_recent_tournaments = AsyncMock(return_value=tournaments)
        mock_client.__aenter__ = AsyncMock(
            return_value=mock_client,
        )
        mock_client.__aexit__ = AsyncMock(
            return_value=None,
        )

        with patch(
            "src.pipelines.scrape_players_club.PlayersClubClient",
            return_value=mock_client,
        ):
            result = await scrape_players_club(
                dry_run=True,
            )

        assert result.tournaments_discovered == 1
        assert result.tournaments_created == 0
        assert result.placements_created == 0

    @pytest.mark.asyncio
    async def test_fetch_error_returns_error(self):
        mock_client = AsyncMock(spec=PlayersClubClient)
        mock_client.fetch_recent_tournaments = AsyncMock(
            side_effect=PlayersClubError("Boom"),
        )
        mock_client.__aenter__ = AsyncMock(
            return_value=mock_client,
        )
        mock_client.__aexit__ = AsyncMock(
            return_value=None,
        )

        with patch(
            "src.pipelines.scrape_players_club.PlayersClubClient",
            return_value=mock_client,
        ):
            result = await scrape_players_club()

        assert result.success is False
        assert len(result.errors) == 1
        assert "Failed to fetch" in result.errors[0]

    @pytest.mark.asyncio
    async def test_empty_tournaments(self):
        mock_client = AsyncMock(spec=PlayersClubClient)
        mock_client.fetch_recent_tournaments = AsyncMock(return_value=[])
        mock_client.__aenter__ = AsyncMock(
            return_value=mock_client,
        )
        mock_client.__aexit__ = AsyncMock(
            return_value=None,
        )

        with patch(
            "src.pipelines.scrape_players_club.PlayersClubClient",
            return_value=mock_client,
        ):
            result = await scrape_players_club()

        assert result.tournaments_discovered == 0
        assert result.success is True


class TestProcessTournament:
    @pytest.mark.asyncio
    async def test_dedup_skips_existing(self):
        mock_session = AsyncMock()
        mock_exec = MagicMock()
        mock_exec.first.return_value = (uuid4(),)
        mock_session.execute = AsyncMock(
            return_value=mock_exec,
        )

        mock_client = AsyncMock(spec=PlayersClubClient)
        mock_normalizer = MagicMock()
        tournament = _make_tournament()
        result = ScrapePlayersClubResult()

        await _process_tournament(
            session=mock_session,
            client=mock_client,
            normalizer=mock_normalizer,
            tournament=tournament,
            result=result,
        )

        assert result.tournaments_skipped == 1
        assert result.tournaments_created == 0
        mock_client.fetch_tournament_detail.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_placements_skipped(self):
        mock_session = AsyncMock()
        mock_exec = MagicMock()
        mock_exec.first.return_value = None
        mock_session.execute = AsyncMock(
            return_value=mock_exec,
        )

        empty_detail = PlayersClubTournamentDetail(
            tournament=_make_tournament(),
            placements=[],
        )
        mock_client = AsyncMock(spec=PlayersClubClient)
        mock_client.fetch_tournament_detail = AsyncMock(
            return_value=empty_detail,
        )

        mock_normalizer = MagicMock()
        tournament = _make_tournament()
        result = ScrapePlayersClubResult()

        await _process_tournament(
            session=mock_session,
            client=mock_client,
            normalizer=mock_normalizer,
            tournament=tournament,
            result=result,
        )

        assert result.tournaments_skipped == 1
        assert result.tournaments_created == 0

    @pytest.mark.asyncio
    async def test_archetype_normalization(self):
        mock_session = AsyncMock()
        mock_exec = MagicMock()
        mock_exec.first.return_value = None
        mock_session.execute = AsyncMock(
            return_value=mock_exec,
        )

        detail = _make_detail()
        mock_client = AsyncMock(spec=PlayersClubClient)
        mock_client.fetch_tournament_detail = AsyncMock(
            return_value=detail,
        )

        mock_normalizer = MagicMock()
        mock_normalizer.resolve.return_value = (
            "Charizard ex",
            [],
            "sprite_lookup",
        )

        tournament = _make_tournament()
        result = ScrapePlayersClubResult()

        await _process_tournament(
            session=mock_session,
            client=mock_client,
            normalizer=mock_normalizer,
            tournament=tournament,
            result=result,
        )

        assert result.tournaments_created == 1
        assert result.placements_created == 2
        assert mock_normalizer.resolve.call_count == 2

    @pytest.mark.asyncio
    async def test_archetype_normalization_failure_fallback(self):
        """When normalizer.resolve raises, placement uses raw archetype."""
        mock_session = AsyncMock()
        mock_exec = MagicMock()
        mock_exec.first.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_exec)

        detail = _make_detail()
        mock_client = AsyncMock(spec=PlayersClubClient)
        mock_client.fetch_tournament_detail = AsyncMock(
            return_value=detail,
        )

        mock_normalizer = MagicMock()
        mock_normalizer.resolve.side_effect = RuntimeError("boom")

        tournament = _make_tournament()
        result = ScrapePlayersClubResult()

        await _process_tournament(
            session=mock_session,
            client=mock_client,
            normalizer=mock_normalizer,
            tournament=tournament,
            result=result,
        )

        assert result.tournaments_created == 1
        assert result.placements_created == 2
        # Placements still created with raw archetype text
        added = [c.args[0] for c in mock_session.add.call_args_list]
        placements = [a for a in added if hasattr(a, "archetype")]
        assert placements[0].archetype == "Charizard ex"
        assert placements[0].archetype_detection_method == "text_label"


class TestCommitFailure:
    @pytest.mark.asyncio
    async def test_commit_failure_zeros_counts(self):
        """When session.commit fails, created counts are zeroed."""
        tournaments = [_make_tournament()]
        detail = _make_detail(tournaments[0])

        mock_client = AsyncMock(spec=PlayersClubClient)
        mock_client.fetch_recent_tournaments = AsyncMock(
            return_value=tournaments,
        )
        mock_client.fetch_tournament_detail = AsyncMock(
            return_value=detail,
        )
        mock_client.__aenter__ = AsyncMock(
            return_value=mock_client,
        )
        mock_client.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_exec = MagicMock()
        mock_exec.first.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_exec)
        mock_session.commit = AsyncMock(
            side_effect=RuntimeError("DB error"),
        )

        mock_normalizer = MagicMock()
        mock_normalizer.load_db_sprites = AsyncMock()
        mock_normalizer.resolve.return_value = (
            "Charizard ex",
            [],
            "text_label",
        )

        with (
            patch(
                "src.pipelines.scrape_players_club.PlayersClubClient",
                return_value=mock_client,
            ),
            patch(
                "src.pipelines.scrape_players_club.async_session_factory",
            ) as mock_sf,
            patch(
                "src.pipelines.scrape_players_club.ArchetypeNormalizer",
                return_value=mock_normalizer,
            ),
        ):
            mock_sf.return_value.__aenter__ = AsyncMock(
                return_value=mock_session,
            )
            mock_sf.return_value.__aexit__ = AsyncMock(
                return_value=None,
            )

            result = await scrape_players_club(lookback_days=30)

        assert result.success is False
        assert result.tournaments_created == 0
        assert result.placements_created == 0
        assert any("Failed to commit" in e for e in result.errors)
