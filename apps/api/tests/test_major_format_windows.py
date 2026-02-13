"""Tests for official major format windows."""

import json
from datetime import date
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.models import Tournament
from src.models.major_format_window import MajorFormatWindow
from src.pipelines.backfill_major_format_windows import backfill_major_format_windows
from src.services.major_format_windows import (
    resolve_major_window_for_date,
    validate_major_window_sequence,
)


def _window(
    key: str,
    start_date: date,
    end_date: date | None,
) -> MajorFormatWindow:
    return MajorFormatWindow(
        id=uuid4(),
        key=key,
        display_name=key.upper(),
        set_range_label=key,
        start_date=start_date,
        end_date=end_date,
        is_active=True,
    )


class TestMajorWindowValidation:
    def test_valid_contiguous_sequence_has_no_warnings(self) -> None:
        windows = [
            _window("svi-pfl", date(2026, 2, 1), date(2026, 2, 28)),
            _window("svi-asc", date(2026, 3, 1), date(2026, 3, 31)),
            _window("tef-por", date(2026, 4, 1), date(2026, 6, 4)),
            _window("chaos-rising", date(2026, 6, 5), None),
        ]

        warnings = validate_major_window_sequence(windows)
        assert warnings == []

    def test_overlap_is_flagged(self) -> None:
        windows = [
            _window("a", date(2026, 2, 1), date(2026, 2, 28)),
            _window("b", date(2026, 2, 20), date(2026, 3, 31)),
        ]

        warnings = validate_major_window_sequence(windows)
        assert any("Overlap detected" in warning for warning in warnings)

    def test_gap_is_flagged(self) -> None:
        windows = [
            _window("a", date(2026, 2, 1), date(2026, 2, 28)),
            _window("b", date(2026, 3, 2), date(2026, 3, 31)),
        ]

        warnings = validate_major_window_sequence(windows)
        assert any("Gap detected" in warning for warning in warnings)


class TestMajorWindowResolution:
    def test_resolves_boundary_dates(self) -> None:
        windows = [
            _window("svi-pfl", date(2026, 2, 1), date(2026, 2, 28)),
            _window("svi-asc", date(2026, 3, 1), date(2026, 3, 31)),
            _window("tef-por", date(2026, 4, 1), date(2026, 6, 4)),
            _window("chaos-rising", date(2026, 6, 5), None),
        ]

        feb_window = resolve_major_window_for_date(windows, date(2026, 2, 28))
        mar_window = resolve_major_window_for_date(windows, date(2026, 3, 1))
        jun4_window = resolve_major_window_for_date(windows, date(2026, 6, 4))
        jun5_window = resolve_major_window_for_date(windows, date(2026, 6, 5))

        assert feb_window is not None
        assert feb_window.key == "svi-pfl"
        assert mar_window is not None
        assert mar_window.key == "svi-asc"
        assert jun4_window is not None
        assert jun4_window.key == "tef-por"
        assert jun5_window is not None
        assert jun5_window.key == "chaos-rising"


class TestMajorWindowBackfill:
    @pytest.mark.asyncio
    async def test_backfill_tags_official_and_skips_non_official(self) -> None:
        session = AsyncMock()
        windows_result = MagicMock()
        windows_result.scalars.return_value.all.return_value = [
            _window("svi-asc", date(2026, 3, 1), date(2026, 3, 31))
        ]

        official = Tournament(
            id=uuid4(),
            name="Regional Championship",
            date=date(2026, 3, 20),
            status="completed",
            region="NA",
            format="standard",
            best_of=3,
            tier="major",
        )
        grassroots = Tournament(
            id=uuid4(),
            name="Local League Challenge",
            date=date(2026, 3, 20),
            status="completed",
            region="NA",
            format="standard",
            best_of=3,
            tier="league",
            major_format_key="svi-asc",
            major_format_label="SVI-ASC",
        )
        tournaments_result = MagicMock()
        tournaments_result.scalars.return_value.all.return_value = [
            official,
            grassroots,
        ]
        session.execute = AsyncMock(side_effect=[windows_result, tournaments_result])

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=session)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "src.pipelines.backfill_major_format_windows.async_session_factory",
            return_value=mock_ctx,
        ):
            result = await backfill_major_format_windows(dry_run=False)

        assert result.success
        assert result.tournaments_scanned == 2
        assert result.tournaments_updated == 2
        assert official.major_format_key == "svi-asc"
        assert grassroots.major_format_key is None

    @pytest.mark.asyncio
    async def test_backfill_is_idempotent(self) -> None:
        session = AsyncMock()
        window = _window("svi-asc", date(2026, 3, 1), date(2026, 3, 31))
        windows_result = MagicMock()
        windows_result.scalars.return_value.all.return_value = [window]

        tagged = Tournament(
            id=uuid4(),
            name="Regional Championship",
            date=date(2026, 3, 20),
            status="completed",
            region="NA",
            format="standard",
            best_of=3,
            tier="major",
            major_format_key="svi-asc",
            major_format_label="SVI-ASC",
        )
        tournaments_result = MagicMock()
        tournaments_result.scalars.return_value.all.return_value = [tagged]
        session.execute = AsyncMock(side_effect=[windows_result, tournaments_result])

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=session)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "src.pipelines.backfill_major_format_windows.async_session_factory",
            return_value=mock_ctx,
        ):
            result = await backfill_major_format_windows(dry_run=False)

        assert result.success
        assert result.tournaments_updated == 0
        assert result.tournaments_skipped == 1


class TestMajorWindowFixtures:
    def test_major_windows_exist_in_format_fixture(self) -> None:
        fixtures_path = Path(__file__).parent.parent / "fixtures" / "formats.json"
        with open(fixtures_path) as f:
            data = json.load(f)

        windows = data.get("major_format_windows")
        assert isinstance(windows, list)
        assert len(windows) == 4

        keys = {window["key"] for window in windows}
        assert keys == {"svi-pfl", "svi-asc", "tef-por", "chaos-rising"}

    def test_chaos_rising_starts_on_legality_date(self) -> None:
        fixtures_path = Path(__file__).parent.parent / "fixtures" / "formats.json"
        with open(fixtures_path) as f:
            data = json.load(f)

        windows = data["major_format_windows"]
        chaos = next(window for window in windows if window["key"] == "chaos-rising")
        assert chaos["start_date"] == "2026-06-05"
