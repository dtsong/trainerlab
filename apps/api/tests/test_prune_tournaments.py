"""Tests for the prune_tournaments pipeline."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.pipelines.prune_tournaments import (
    PruneTournamentsResult,
    prune_tournaments,
)


def _make_scalar_result(value: int) -> MagicMock:
    result = MagicMock()
    result.scalar.return_value = value
    return result


def _mock_session_factory(mock_session: AsyncMock) -> MagicMock:
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)
    return mock_ctx


class TestPruneTournamentsResult:
    def test_successful_result(self) -> None:
        r = PruneTournamentsResult(
            tournaments_deleted=5,
            placements_deleted=50,
            tournaments_remaining=100,
            errors=[],
            success=True,
        )
        assert r.success is True
        assert r.tournaments_deleted == 5

    def test_failed_result(self) -> None:
        r = PruneTournamentsResult(
            tournaments_deleted=0,
            placements_deleted=0,
            tournaments_remaining=0,
            errors=["Prune failed: connection lost"],
            success=False,
        )
        assert r.success is False


class TestPruneDryRun:
    """Dry run counts but never deletes."""

    @pytest.mark.asyncio
    async def test_dry_run_reports_counts(self) -> None:
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(
            side_effect=[
                _make_scalar_result(10),  # tournaments to delete
                _make_scalar_result(80),  # placements to delete
                _make_scalar_result(50),  # total tournaments
            ]
        )

        with patch(
            "src.pipelines.prune_tournaments.async_session_factory",
            return_value=_mock_session_factory(mock_session),
        ):
            result = await prune_tournaments(before_date=date(2024, 1, 1), dry_run=True)

        assert result.success is True
        assert result.tournaments_deleted == 0
        assert result.placements_deleted == 0
        assert result.tournaments_remaining == 40  # 50 - 10

    @pytest.mark.asyncio
    async def test_dry_run_never_commits(self) -> None:
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(
            side_effect=[
                _make_scalar_result(5),
                _make_scalar_result(25),
                _make_scalar_result(20),
            ]
        )

        with patch(
            "src.pipelines.prune_tournaments.async_session_factory",
            return_value=_mock_session_factory(mock_session),
        ):
            await prune_tournaments(before_date=date(2024, 1, 1), dry_run=True)

        mock_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_dry_run_with_region_filter(self) -> None:
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(
            side_effect=[
                _make_scalar_result(3),  # JP tournaments to delete
                _make_scalar_result(30),  # JP placements to delete
                _make_scalar_result(10),  # total JP tournaments
            ]
        )

        with patch(
            "src.pipelines.prune_tournaments.async_session_factory",
            return_value=_mock_session_factory(mock_session),
        ):
            result = await prune_tournaments(
                before_date=date(2024, 6, 1),
                region="JP",
                dry_run=True,
            )

        assert result.success is True
        assert result.tournaments_remaining == 7  # 10 - 3


class TestPruneExecution:
    """Normal execution deletes tournaments and placements."""

    @pytest.mark.asyncio
    async def test_deletes_tournaments_and_placements(self) -> None:
        mock_session = AsyncMock()

        call_count = 0

        async def execute_side_effect(stmt):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _make_scalar_result(5)  # tournaments count
            if call_count == 2:
                return _make_scalar_result(40)  # placements count
            if call_count == 3:
                return MagicMock()  # delete placements
            if call_count == 4:
                return MagicMock()  # delete tournaments
            return _make_scalar_result(20)  # remaining

        mock_session.execute = AsyncMock(side_effect=execute_side_effect)

        with patch(
            "src.pipelines.prune_tournaments.async_session_factory",
            return_value=_mock_session_factory(mock_session),
        ):
            result = await prune_tournaments(before_date=date(2024, 1, 1))

        assert result.success is True
        assert result.tournaments_deleted == 5
        assert result.placements_deleted == 40
        assert result.tournaments_remaining == 20
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_with_region_filter(self) -> None:
        mock_session = AsyncMock()

        call_count = 0

        async def execute_side_effect(stmt):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _make_scalar_result(2)  # JP tournaments
            if call_count == 2:
                return _make_scalar_result(16)  # JP placements
            if call_count == 3:
                return MagicMock()  # delete placements
            if call_count == 4:
                return MagicMock()  # delete tournaments
            return _make_scalar_result(8)  # remaining JP

        mock_session.execute = AsyncMock(side_effect=execute_side_effect)

        with patch(
            "src.pipelines.prune_tournaments.async_session_factory",
            return_value=_mock_session_factory(mock_session),
        ):
            result = await prune_tournaments(before_date=date(2024, 1, 1), region="JP")

        assert result.success is True
        assert result.tournaments_deleted == 2
        assert result.placements_deleted == 16

    @pytest.mark.asyncio
    async def test_nothing_to_prune(self) -> None:
        mock_session = AsyncMock()

        call_count = 0

        async def execute_side_effect(stmt):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _make_scalar_result(0)  # no tournaments
            if call_count == 2:
                return _make_scalar_result(0)  # no placements
            if call_count == 3:
                return MagicMock()  # delete placements (noop)
            if call_count == 4:
                return MagicMock()  # delete tournaments (noop)
            return _make_scalar_result(50)  # all remaining

        mock_session.execute = AsyncMock(side_effect=execute_side_effect)

        with patch(
            "src.pipelines.prune_tournaments.async_session_factory",
            return_value=_mock_session_factory(mock_session),
        ):
            result = await prune_tournaments(before_date=date(2020, 1, 1))

        assert result.success is True
        assert result.tournaments_deleted == 0
        assert result.placements_deleted == 0
        assert result.tournaments_remaining == 50


class TestPruneErrorHandling:
    """Error handling with rollback."""

    @pytest.mark.asyncio
    async def test_rollback_on_failure(self) -> None:
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(side_effect=RuntimeError("Connection lost"))

        with patch(
            "src.pipelines.prune_tournaments.async_session_factory",
            return_value=_mock_session_factory(mock_session),
        ):
            result = await prune_tournaments(before_date=date(2024, 1, 1))

        assert result.success is False
        assert result.tournaments_deleted == 0
        assert result.placements_deleted == 0
        assert len(result.errors) == 1
        assert "Prune failed" in result.errors[0]
        mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_rollback_on_commit_failure(self) -> None:
        mock_session = AsyncMock()

        call_count = 0

        async def execute_side_effect(stmt):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                return _make_scalar_result(3)  # counts
            return MagicMock()  # deletes

        mock_session.execute = AsyncMock(side_effect=execute_side_effect)
        mock_session.commit = AsyncMock(side_effect=RuntimeError("Commit failed"))

        with patch(
            "src.pipelines.prune_tournaments.async_session_factory",
            return_value=_mock_session_factory(mock_session),
        ):
            result = await prune_tournaments(before_date=date(2024, 1, 1))

        assert result.success is False
        mock_session.rollback.assert_called_once()
