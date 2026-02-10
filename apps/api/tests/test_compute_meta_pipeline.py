"""Tests for meta snapshot computation pipeline functions."""

from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from src.models.meta_snapshot import MetaSnapshot
from src.pipelines.compute_meta import (
    FORMATS,
    REGION_BEST_OF,
    REGIONS,
    TOURNAMENT_TYPES,
    ComputeMetaResult,
    compute_daily_snapshots,
    compute_single_snapshot,
)


@pytest.fixture
def sample_snapshot() -> MetaSnapshot:
    """Create a sample meta snapshot for testing."""
    return MetaSnapshot(
        snapshot_date=date.today(),
        region=None,
        format="standard",
        best_of=3,
        archetype_shares={"Charizard ex": 0.20, "Lugia VSTAR": 0.15},
        card_usage={"sv3-125": 0.45, "sv2-67": 0.30},
        sample_size=100,
        tournaments_included=5,
        diversity_index=Decimal("0.85"),
        tier_assignments={"Charizard ex": "S", "Lugia VSTAR": "A"},
    )


@pytest.fixture
def empty_snapshot() -> MetaSnapshot:
    """Create an empty meta snapshot for testing."""
    return MetaSnapshot(
        snapshot_date=date.today(),
        region=None,
        format="standard",
        best_of=3,
        archetype_shares={},
        card_usage={},
        sample_size=0,
        tournaments_included=0,
        diversity_index=None,
    )


class TestComputeDailySnapshots:
    """Tests for compute_daily_snapshots function."""

    @pytest.mark.asyncio
    async def test_iterates_all_region_format_combinations(self, sample_snapshot):
        """Verify pipeline iterates through all region/format/best_of combinations."""
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_service = AsyncMock()
        mock_service.compute_enhanced_meta_snapshot.return_value = sample_snapshot
        mock_service.save_snapshot.return_value = sample_snapshot

        with (
            patch(
                "src.pipelines.compute_meta.async_session_factory",
                return_value=mock_session,
            ),
            patch(
                "src.pipelines.compute_meta.MetaService",
                return_value=mock_service,
            ),
        ):
            result = await compute_daily_snapshots(dry_run=False)

        # Count expected combinations (region × format × best_of × tournament_type)
        expected_count = 0
        for region in REGIONS:
            best_of_options = REGION_BEST_OF.get(region, [3])
            expected_count += (
                len(FORMATS) * len(best_of_options) * len(TOURNAMENT_TYPES)
            )

        assert result.snapshots_computed == expected_count
        assert mock_service.compute_enhanced_meta_snapshot.call_count == expected_count

    @pytest.mark.asyncio
    async def test_dry_run_skips_save(self, sample_snapshot):
        """Verify dry run computes but doesn't save snapshots."""
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_service = AsyncMock()
        mock_service.compute_enhanced_meta_snapshot.return_value = sample_snapshot

        with (
            patch(
                "src.pipelines.compute_meta.async_session_factory",
                return_value=mock_session,
            ),
            patch(
                "src.pipelines.compute_meta.MetaService",
                return_value=mock_service,
            ),
        ):
            result = await compute_daily_snapshots(dry_run=True)

        assert result.snapshots_computed > 0
        assert result.snapshots_saved == 0
        mock_service.save_snapshot.assert_not_called()

    @pytest.mark.asyncio
    async def test_saves_snapshots_when_not_dry_run(self, sample_snapshot):
        """Verify snapshots are saved when dry_run=False."""
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_service = AsyncMock()
        mock_service.compute_enhanced_meta_snapshot.return_value = sample_snapshot
        mock_service.save_snapshot.return_value = sample_snapshot

        with (
            patch(
                "src.pipelines.compute_meta.async_session_factory",
                return_value=mock_session,
            ),
            patch(
                "src.pipelines.compute_meta.MetaService",
                return_value=mock_service,
            ),
        ):
            result = await compute_daily_snapshots(dry_run=False)

        assert result.snapshots_saved > 0
        assert mock_service.save_snapshot.call_count == result.snapshots_saved

    @pytest.mark.asyncio
    async def test_skips_empty_snapshots(self, sample_snapshot, empty_snapshot):
        """Verify empty snapshots are counted as skipped."""
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_service = AsyncMock()
        # Return empty snapshot - should be skipped
        mock_service.compute_enhanced_meta_snapshot.return_value = empty_snapshot
        mock_service.save_snapshot.return_value = sample_snapshot

        with (
            patch(
                "src.pipelines.compute_meta.async_session_factory",
                return_value=mock_session,
            ),
            patch(
                "src.pipelines.compute_meta.MetaService",
                return_value=mock_service,
            ),
        ):
            result = await compute_daily_snapshots(
                dry_run=False,
                regions=[None],  # Only global
                formats=["standard"],
            )

        # Global only has BO3, so 3 combinations for standard
        # (all/official/grassroots tournament types)
        # Empty snapshot should be skipped (not saved)
        assert result.snapshots_computed == 3
        assert result.snapshots_skipped == 3
        assert result.snapshots_saved == 0
        mock_service.save_snapshot.assert_not_called()

    @pytest.mark.asyncio
    async def test_continues_on_individual_errors(self, sample_snapshot):
        """Verify pipeline continues processing after individual errors."""
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_service = AsyncMock()
        # First fails, rest succeed
        # 2 regions × 1 format × 1 BO × 3 tournament types = 6 combos
        mock_service.compute_enhanced_meta_snapshot.side_effect = [
            SQLAlchemyError("DB error"),
            sample_snapshot,
            sample_snapshot,
            sample_snapshot,
            sample_snapshot,
            sample_snapshot,
        ]
        mock_service.save_snapshot.return_value = sample_snapshot

        with (
            patch(
                "src.pipelines.compute_meta.async_session_factory",
                return_value=mock_session,
            ),
            patch(
                "src.pipelines.compute_meta.MetaService",
                return_value=mock_service,
            ),
        ):
            result = await compute_daily_snapshots(
                dry_run=False,
                regions=[None, "NA"],  # 2 regions
                formats=["standard"],  # 1 format
            )

        # Should have 1 error but still process others
        assert len(result.errors) == 1
        assert "DB error" in result.errors[0]
        assert result.snapshots_computed >= 1

    @pytest.mark.asyncio
    async def test_respects_custom_regions_filter(self, sample_snapshot):
        """Verify custom regions filter is applied."""
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_service = AsyncMock()
        mock_service.compute_enhanced_meta_snapshot.return_value = sample_snapshot
        mock_service.save_snapshot.return_value = sample_snapshot

        with (
            patch(
                "src.pipelines.compute_meta.async_session_factory",
                return_value=mock_session,
            ),
            patch(
                "src.pipelines.compute_meta.MetaService",
                return_value=mock_service,
            ),
        ):
            result = await compute_daily_snapshots(
                regions=["JP"],  # Only JP
                formats=["standard"],
            )

        # JP has BO1, so 3 combinations for standard
        # (all/official/grassroots tournament types)
        assert result.snapshots_computed == 3

        # Verify JP region was used
        call_kwargs = mock_service.compute_enhanced_meta_snapshot.call_args.kwargs
        assert call_kwargs["region"] == "JP"
        assert call_kwargs["best_of"] == 1  # JP uses BO1

    @pytest.mark.asyncio
    async def test_respects_custom_formats_filter(self, sample_snapshot):
        """Verify custom formats filter is applied."""
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_service = AsyncMock()
        mock_service.compute_enhanced_meta_snapshot.return_value = sample_snapshot
        mock_service.save_snapshot.return_value = sample_snapshot

        with (
            patch(
                "src.pipelines.compute_meta.async_session_factory",
                return_value=mock_session,
            ),
            patch(
                "src.pipelines.compute_meta.MetaService",
                return_value=mock_service,
            ),
        ):
            result = await compute_daily_snapshots(
                regions=[None],  # Global only
                formats=["expanded"],  # Only expanded
            )

        # Global has BO3, so 3 combinations
        # (all/official/grassroots tournament types)
        assert result.snapshots_computed == 3
        call_kwargs = mock_service.compute_enhanced_meta_snapshot.call_args.kwargs
        assert call_kwargs["game_format"] == "expanded"

    @pytest.mark.asyncio
    async def test_uses_custom_snapshot_date(self, sample_snapshot):
        """Verify custom snapshot date is passed through."""
        custom_date = date(2025, 12, 15)

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_service = AsyncMock()
        mock_service.compute_enhanced_meta_snapshot.return_value = sample_snapshot
        mock_service.save_snapshot.return_value = sample_snapshot

        with (
            patch(
                "src.pipelines.compute_meta.async_session_factory",
                return_value=mock_session,
            ),
            patch(
                "src.pipelines.compute_meta.MetaService",
                return_value=mock_service,
            ),
        ):
            await compute_daily_snapshots(
                snapshot_date=custom_date,
                regions=[None],
                formats=["standard"],
            )

        call_kwargs = mock_service.compute_enhanced_meta_snapshot.call_args.kwargs
        assert call_kwargs["snapshot_date"] == custom_date

    @pytest.mark.asyncio
    async def test_defaults_to_today_when_no_date(self, sample_snapshot):
        """Verify snapshot date defaults to today."""
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_service = AsyncMock()
        mock_service.compute_enhanced_meta_snapshot.return_value = sample_snapshot

        with (
            patch(
                "src.pipelines.compute_meta.async_session_factory",
                return_value=mock_session,
            ),
            patch(
                "src.pipelines.compute_meta.MetaService",
                return_value=mock_service,
            ),
        ):
            await compute_daily_snapshots(
                snapshot_date=None,  # Should default to today
                regions=[None],
                formats=["standard"],
                dry_run=True,
            )

        call_kwargs = mock_service.compute_enhanced_meta_snapshot.call_args.kwargs
        assert call_kwargs["snapshot_date"] == date.today()


class TestComputeSingleSnapshot:
    """Tests for compute_single_snapshot function."""

    @pytest.mark.asyncio
    async def test_computes_single_combination(self, sample_snapshot):
        """Verify single snapshot computation works."""
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_service = AsyncMock()
        mock_service.compute_enhanced_meta_snapshot.return_value = sample_snapshot
        mock_service.save_snapshot.return_value = sample_snapshot

        with (
            patch(
                "src.pipelines.compute_meta.async_session_factory",
                return_value=mock_session,
            ),
            patch(
                "src.pipelines.compute_meta.MetaService",
                return_value=mock_service,
            ),
        ):
            result = await compute_single_snapshot(
                snapshot_date=date.today(),
                region="NA",
                game_format="standard",
                best_of=3,
                dry_run=False,
            )

        assert result.snapshots_computed == 1
        assert result.snapshots_saved == 1
        assert result.success

    @pytest.mark.asyncio
    async def test_dry_run_mode(self, sample_snapshot):
        """Verify dry run doesn't save snapshot."""
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_service = AsyncMock()
        mock_service.compute_enhanced_meta_snapshot.return_value = sample_snapshot

        with (
            patch(
                "src.pipelines.compute_meta.async_session_factory",
                return_value=mock_session,
            ),
            patch(
                "src.pipelines.compute_meta.MetaService",
                return_value=mock_service,
            ),
        ):
            result = await compute_single_snapshot(
                snapshot_date=date.today(),
                region="NA",
                game_format="standard",
                best_of=3,
                dry_run=True,
            )

        assert result.snapshots_computed == 1
        assert result.snapshots_saved == 0
        mock_service.save_snapshot.assert_not_called()

    @pytest.mark.asyncio
    async def test_handles_empty_result(self, empty_snapshot):
        """Verify empty snapshot is handled correctly."""
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_service = AsyncMock()
        mock_service.compute_enhanced_meta_snapshot.return_value = empty_snapshot

        with (
            patch(
                "src.pipelines.compute_meta.async_session_factory",
                return_value=mock_session,
            ),
            patch(
                "src.pipelines.compute_meta.MetaService",
                return_value=mock_service,
            ),
        ):
            result = await compute_single_snapshot(
                snapshot_date=date.today(),
                region="NA",
                game_format="standard",
                best_of=3,
                dry_run=False,
            )

        assert result.snapshots_computed == 1
        assert result.snapshots_saved == 0
        assert result.snapshots_skipped == 1
        mock_service.save_snapshot.assert_not_called()

    @pytest.mark.asyncio
    async def test_handles_computation_error(self):
        """Verify errors are captured correctly."""
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_service = AsyncMock()
        mock_service.compute_enhanced_meta_snapshot.side_effect = ValueError(
            "Invalid data"
        )

        with (
            patch(
                "src.pipelines.compute_meta.async_session_factory",
                return_value=mock_session,
            ),
            patch(
                "src.pipelines.compute_meta.MetaService",
                return_value=mock_service,
            ),
        ):
            result = await compute_single_snapshot(
                snapshot_date=date.today(),
                region="NA",
                game_format="standard",
                best_of=3,
            )

        assert not result.success
        assert len(result.errors) == 1
        assert "Invalid data" in result.errors[0]

    @pytest.mark.asyncio
    async def test_passes_lookback_days(self, sample_snapshot):
        """Verify lookback_days parameter is passed through."""
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_service = AsyncMock()
        mock_service.compute_enhanced_meta_snapshot.return_value = sample_snapshot

        with (
            patch(
                "src.pipelines.compute_meta.async_session_factory",
                return_value=mock_session,
            ),
            patch(
                "src.pipelines.compute_meta.MetaService",
                return_value=mock_service,
            ),
        ):
            await compute_single_snapshot(
                snapshot_date=date.today(),
                region="NA",
                game_format="standard",
                best_of=3,
                lookback_days=180,
                dry_run=True,
            )

        call_kwargs = mock_service.compute_enhanced_meta_snapshot.call_args.kwargs
        assert call_kwargs["lookback_days"] == 180


class TestComputeMetaResult:
    """Tests for ComputeMetaResult dataclass."""

    def test_success_when_no_errors(self):
        """Verify success is True when errors list is empty."""
        result = ComputeMetaResult(
            snapshots_computed=5,
            snapshots_saved=5,
            errors=[],
        )
        assert result.success

    def test_not_success_when_has_errors(self):
        """Verify success is False when errors exist."""
        result = ComputeMetaResult(
            snapshots_computed=5,
            snapshots_saved=4,
            errors=["One error occurred"],
        )
        assert not result.success

    def test_default_values(self):
        """Verify default values are correct."""
        result = ComputeMetaResult()
        assert result.snapshots_computed == 0
        assert result.snapshots_saved == 0
        assert result.snapshots_skipped == 0
        assert result.errors == []
        assert result.success
