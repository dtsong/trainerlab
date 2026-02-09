"""Tests for the wipe_data pipeline."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.pipelines.wipe_data import (
    PRESERVED_TABLES,
    TABLES_TO_TRUNCATE,
    WipeDataResult,
    wipe_data,
)


class TestWipeDataConstants:
    """Verify table lists are correct and non-overlapping."""

    def test_no_overlap_between_truncate_and_preserved(self) -> None:
        overlap = set(TABLES_TO_TRUNCATE) & PRESERVED_TABLES
        assert overlap == set(), f"Tables in both lists: {overlap}"

    def test_truncate_list_not_empty(self) -> None:
        assert len(TABLES_TO_TRUNCATE) > 0

    def test_preserved_set_not_empty(self) -> None:
        assert len(PRESERVED_TABLES) > 0

    def test_no_duplicate_tables_in_truncate_list(self) -> None:
        assert len(TABLES_TO_TRUNCATE) == len(set(TABLES_TO_TRUNCATE))

    def test_alembic_version_is_preserved(self) -> None:
        assert "alembic_version" in PRESERVED_TABLES

    def test_users_table_is_preserved(self) -> None:
        assert "users" in PRESERVED_TABLES

    def test_tournament_placements_before_tournaments(self) -> None:
        tp_idx = TABLES_TO_TRUNCATE.index("tournament_placements")
        t_idx = TABLES_TO_TRUNCATE.index("tournaments")
        assert tp_idx < t_idx, "Children must come before parents in truncation order"

    def test_cards_before_sets_not_required_but_present(self) -> None:
        """Cards references sets via FK; CASCADE handles it."""
        assert "cards" in TABLES_TO_TRUNCATE
        assert "sets" in TABLES_TO_TRUNCATE


class TestWipeDataResult:
    """WipeDataResult model tests."""

    def test_successful_result(self) -> None:
        r = WipeDataResult(
            tables_truncated=21,
            tables_verified_empty=21,
            preserved_tables_checked=11,
            errors=[],
            success=True,
        )
        assert r.success is True
        assert r.tables_truncated == 21

    def test_failed_result(self) -> None:
        r = WipeDataResult(
            tables_truncated=0,
            tables_verified_empty=0,
            preserved_tables_checked=0,
            errors=["Truncation transaction failed, rolled back"],
            success=False,
        )
        assert r.success is False
        assert len(r.errors) == 1


def _make_scalar_result(value: int) -> MagicMock:
    """Create a mock result whose .scalar() returns value."""
    result = MagicMock()
    result.scalar.return_value = value
    return result


class TestWipeDataDryRun:
    """Dry run should query row counts but never truncate."""

    @pytest.mark.asyncio
    async def test_dry_run_returns_zero_truncated(self) -> None:
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=_make_scalar_result(100))

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "src.pipelines.wipe_data.async_session_factory",
            return_value=mock_ctx,
        ):
            result = await wipe_data(dry_run=True)

        assert result.success is True
        assert result.tables_truncated == 0
        assert result.tables_verified_empty == 0
        assert result.preserved_tables_checked == 0

    @pytest.mark.asyncio
    async def test_dry_run_queries_all_tables(self) -> None:
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=_make_scalar_result(50))

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "src.pipelines.wipe_data.async_session_factory",
            return_value=mock_ctx,
        ):
            await wipe_data(dry_run=True)

        assert mock_session.execute.call_count == len(TABLES_TO_TRUNCATE)

    @pytest.mark.asyncio
    async def test_dry_run_never_calls_commit(self) -> None:
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=_make_scalar_result(10))

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "src.pipelines.wipe_data.async_session_factory",
            return_value=mock_ctx,
        ):
            await wipe_data(dry_run=True)

        mock_session.commit.assert_not_called()


class TestWipeDataExecution:
    """Normal execution should truncate, verify, and check preserved."""

    @pytest.mark.asyncio
    async def test_truncates_all_tables(self) -> None:
        mock_session = AsyncMock()
        # execute returns 0 rows for verification queries
        mock_session.execute = AsyncMock(return_value=_make_scalar_result(0))

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "src.pipelines.wipe_data.async_session_factory",
            return_value=mock_ctx,
        ):
            result = await wipe_data(dry_run=False)

        assert result.success is True
        assert result.tables_truncated == len(TABLES_TO_TRUNCATE)
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_uses_cascade(self) -> None:
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=_make_scalar_result(0))

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "src.pipelines.wipe_data.async_session_factory",
            return_value=mock_ctx,
        ):
            await wipe_data(dry_run=False)

        # Check that TRUNCATE calls used CASCADE
        truncate_calls = [
            c
            for c in mock_session.execute.call_args_list
            if hasattr(c.args[0], "text") and "TRUNCATE" in c.args[0].text
        ]
        assert len(truncate_calls) == len(TABLES_TO_TRUNCATE)
        for c in truncate_calls:
            assert "CASCADE" in c.args[0].text

    @pytest.mark.asyncio
    async def test_reports_nonempty_table_after_truncation(self) -> None:
        mock_session = AsyncMock()

        call_count = 0
        total_truncate = len(TABLES_TO_TRUNCATE)

        async def side_effect(stmt):
            nonlocal call_count
            call_count += 1
            # First N calls = TRUNCATE (return doesn't matter)
            if call_count <= total_truncate:
                return _make_scalar_result(0)
            # Verification: first table still has rows
            if call_count == total_truncate + 1:
                return _make_scalar_result(5)
            # All other verifications return 0
            return _make_scalar_result(0)

        mock_session.execute = AsyncMock(side_effect=side_effect)

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "src.pipelines.wipe_data.async_session_factory",
            return_value=mock_ctx,
        ):
            result = await wipe_data(dry_run=False)

        assert result.success is False
        assert len(result.errors) == 1
        assert "still has 5 rows" in result.errors[0]

    @pytest.mark.asyncio
    async def test_verifies_all_truncated_tables(self) -> None:
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=_make_scalar_result(0))

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "src.pipelines.wipe_data.async_session_factory",
            return_value=mock_ctx,
        ):
            result = await wipe_data(dry_run=False)

        assert result.tables_verified_empty == len(TABLES_TO_TRUNCATE)

    @pytest.mark.asyncio
    async def test_checks_preserved_tables(self) -> None:
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=_make_scalar_result(0))

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "src.pipelines.wipe_data.async_session_factory",
            return_value=mock_ctx,
        ):
            result = await wipe_data(dry_run=False)

        assert result.preserved_tables_checked == len(PRESERVED_TABLES)


class TestWipeDataErrorHandling:
    """Error handling: rollback on failure, preserved table errors."""

    @pytest.mark.asyncio
    async def test_rollback_on_truncation_failure(self) -> None:
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(side_effect=RuntimeError("DB connection lost"))

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "src.pipelines.wipe_data.async_session_factory",
            return_value=mock_ctx,
        ):
            result = await wipe_data(dry_run=False)

        assert result.success is False
        assert result.tables_truncated == 0
        assert "rolled back" in result.errors[0].lower()
        mock_session.rollback.assert_called_once()
        mock_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_preserved_table_check_error_handled(self) -> None:
        mock_session = AsyncMock()

        call_count = 0
        total_truncate = len(TABLES_TO_TRUNCATE)
        total_verify = len(TABLES_TO_TRUNCATE)

        async def side_effect(stmt):
            nonlocal call_count
            call_count += 1
            # Truncation phase
            if call_count <= total_truncate:
                return _make_scalar_result(0)
            # Verification phase
            if call_count <= total_truncate + total_verify:
                return _make_scalar_result(0)
            # Preserved table check — fail on first
            if call_count == total_truncate + total_verify + 1:
                raise RuntimeError("Table does not exist")
            return _make_scalar_result(10)

        mock_session.execute = AsyncMock(side_effect=side_effect)

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "src.pipelines.wipe_data.async_session_factory",
            return_value=mock_ctx,
        ):
            result = await wipe_data(dry_run=False)

        # Should still succeed — preserved table check errors
        # are logged but don't fail the operation
        assert result.success is True
        # One preserved table errored, rest checked ok
        assert result.preserved_tables_checked == (len(PRESERVED_TABLES) - 1)
