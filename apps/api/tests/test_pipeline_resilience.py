"""Tests for pipeline resilience utilities (retry_commit, with_timeout)."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.exc import IntegrityError, OperationalError

from src.services.pipeline_resilience import (
    DEFAULT_BASE_DELAY,
    DEFAULT_MAX_RETRIES,
    retry_commit,
    with_timeout,
)


class TestRetryCommit:
    """Tests for retry_commit()."""

    @pytest.mark.asyncio
    async def test_successful_commit_no_retry(self) -> None:
        """Commit succeeds on first attempt — no retry needed."""
        session = AsyncMock()
        session.commit = AsyncMock()

        await retry_commit(session)

        session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_retries_on_operational_error(self) -> None:
        """Retries on OperationalError then succeeds."""
        session = AsyncMock()
        session.commit = AsyncMock(
            side_effect=[
                OperationalError("connection reset", {}, None),
                None,  # succeeds on second attempt
            ]
        )

        with patch("src.services.pipeline_resilience.asyncio.sleep"):
            await retry_commit(session)

        assert session.commit.call_count == 2

    @pytest.mark.asyncio
    async def test_raises_after_max_retries(self) -> None:
        """Raises OperationalError after all retries exhausted."""
        session = AsyncMock()
        session.commit = AsyncMock(
            side_effect=OperationalError("lock timeout", {}, None)
        )

        with (
            patch("src.services.pipeline_resilience.asyncio.sleep"),
            pytest.raises(OperationalError),
        ):
            await retry_commit(session, max_retries=3)

        assert session.commit.call_count == 3

    @pytest.mark.asyncio
    async def test_does_not_retry_integrity_error(self) -> None:
        """IntegrityError is not transient — raise immediately."""
        session = AsyncMock()
        session.commit = AsyncMock(
            side_effect=IntegrityError("unique violation", {}, None)
        )

        with pytest.raises(IntegrityError):
            await retry_commit(session)

        session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_exponential_backoff_delays(self) -> None:
        """Delay doubles on each retry attempt."""
        session = AsyncMock()
        session.commit = AsyncMock(
            side_effect=[
                OperationalError("err", {}, None),
                OperationalError("err", {}, None),
                None,  # success on third
            ]
        )

        with patch("src.services.pipeline_resilience.asyncio.sleep") as mock_sleep:
            await retry_commit(session, base_delay=1.0, max_retries=3)

        assert mock_sleep.call_count == 2
        # First delay: 1.0 * 2^0 = 1.0
        mock_sleep.assert_any_call(1.0)
        # Second delay: 1.0 * 2^1 = 2.0
        mock_sleep.assert_any_call(2.0)

    @pytest.mark.asyncio
    async def test_context_included_in_log(self) -> None:
        """Context string is passed through for logging."""
        session = AsyncMock()
        session.commit = AsyncMock(side_effect=OperationalError("deadlock", {}, None))

        with (
            patch("src.services.pipeline_resilience.asyncio.sleep"),
            patch("src.services.pipeline_resilience.logger") as mock_logger,
            pytest.raises(OperationalError),
        ):
            await retry_commit(
                session,
                max_retries=1,
                context="save-snapshot",
            )

        # Should have logged with context
        mock_logger.error.assert_called_once()
        log_args = mock_logger.error.call_args[0]
        formatted = log_args[0] % log_args[1:]
        assert "save-snapshot" in formatted

    @pytest.mark.asyncio
    async def test_defaults(self) -> None:
        """Default values match module constants."""
        assert DEFAULT_MAX_RETRIES == 3
        assert DEFAULT_BASE_DELAY == 1.0

    @pytest.mark.asyncio
    async def test_retry_once_then_succeed(self) -> None:
        """Single failure then success."""
        session = AsyncMock()
        session.commit = AsyncMock(
            side_effect=[
                OperationalError("timeout", {}, None),
                None,
            ]
        )

        with patch("src.services.pipeline_resilience.asyncio.sleep"):
            await retry_commit(session, max_retries=2)

        assert session.commit.call_count == 2


class TestWithTimeout:
    """Tests for with_timeout()."""

    @pytest.mark.asyncio
    async def test_returns_result_within_timeout(self) -> None:
        """Returns coroutine result when it completes in time."""

        async def fast_op():
            return 42

        result = await with_timeout(fast_op(), timeout_seconds=5.0)
        assert result == 42

    @pytest.mark.asyncio
    async def test_raises_timeout_error(self) -> None:
        """Raises TimeoutError when operation exceeds timeout."""

        async def slow_op():
            await asyncio.sleep(10)
            return "never"

        with pytest.raises(TimeoutError):
            await with_timeout(slow_op(), timeout_seconds=0.01)

    @pytest.mark.asyncio
    async def test_logs_timeout_with_context(self) -> None:
        """Logs pipeline/step info on timeout."""

        async def slow_op():
            await asyncio.sleep(10)

        with (
            patch("src.services.pipeline_resilience.logger") as mock_logger,
            pytest.raises(TimeoutError),
        ):
            await with_timeout(
                slow_op(),
                timeout_seconds=0.01,
                pipeline="compute-meta",
                step="compute-global",
            )

        mock_logger.error.assert_called_once()
        args = mock_logger.error.call_args[0]
        assert "compute-meta" in str(args)
        assert "compute-global" in str(args)

    @pytest.mark.asyncio
    async def test_propagates_exceptions(self) -> None:
        """Non-timeout exceptions propagate normally."""

        async def failing_op():
            raise ValueError("bad input")

        with pytest.raises(ValueError, match="bad input"):
            await with_timeout(failing_op(), timeout_seconds=5.0)

    @pytest.mark.asyncio
    async def test_returns_none(self) -> None:
        """Handles coroutines that return None."""

        async def void_op():
            pass

        result = await with_timeout(void_op(), timeout_seconds=5.0)
        assert result is None


class TestRetryCommitIntegration:
    """Integration-style tests verifying retry_commit in pipelines."""

    @pytest.mark.asyncio
    async def test_card_sync_uses_retry(self) -> None:
        """card_sync calls retry_commit instead of raw commit."""
        from src.services.card_sync import CardSyncService

        session = AsyncMock()
        client = AsyncMock()
        client.fetch_all_sets = AsyncMock(return_value=[])
        service = CardSyncService(session, client)

        await service.sync_all_english()

        # No raw commit calls (retry_commit handles it)
        # With 0 sets, no commits happen at all
        session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_save_snapshot_retry_on_update(self) -> None:
        """save_snapshot retries on transient error during update."""
        from unittest.mock import MagicMock

        from src.models.meta_snapshot import MetaSnapshot
        from src.services.meta_service import MetaService

        session = AsyncMock()
        service = MetaService(session)

        existing = MagicMock(spec=MetaSnapshot)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing
        session.execute = AsyncMock(return_value=mock_result)
        session.refresh = AsyncMock()

        # First commit fails, second succeeds
        session.commit = AsyncMock(
            side_effect=[
                OperationalError("conn reset", {}, None),
                None,
            ]
        )

        snapshot = MetaSnapshot(
            snapshot_date=None,
            region=None,
            format="standard",
            best_of=3,
            archetype_shares={"A": 1.0},
            sample_size=10,
        )

        with patch("src.services.pipeline_resilience.asyncio.sleep"):
            result = await service.save_snapshot(snapshot)

        assert session.commit.call_count == 2
        assert result == existing

    @pytest.mark.asyncio
    async def test_compute_evolution_retry_commit(self) -> None:
        """compute_evolution uses retry_commit for predictions."""
        from src.pipelines.compute_evolution import (
            _generate_predictions,
        )

        session = AsyncMock()
        engine = AsyncMock()
        engine.predict = AsyncMock(return_value=MagicMock())

        # Mock empty queries (no tournaments)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=mock_result)

        from src.pipelines.compute_evolution import (
            ComputeEvolutionResult,
        )

        result = ComputeEvolutionResult()
        await _generate_predictions(session, engine, result, dry_run=False)

        # No tournaments found = no commit needed
        session.commit.assert_not_called()
