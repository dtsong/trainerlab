"""Tests for the Pokekameshi meta scrape pipeline."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.clients.pokekameshi import (
    PokekameshiClient,
    PokekameshiError,
    PokekameshiMetaReport,
    PokekameshiMetaShare,
)
from src.pipelines.scrape_pokekameshi import (
    scrape_pokekameshi_meta,
)


def _make_report(
    shares: list[PokekameshiMetaShare] | None = None,
    report_date: date | None = None,
) -> PokekameshiMetaReport:
    """Build a test meta report."""
    return PokekameshiMetaReport(
        date=report_date or date(2026, 2, 22),
        event_name="Test Event",
        shares=shares or [],
        total_entries=100,
        source_url="https://pokekameshi.com/meta/",
    )


def _make_share(
    name: str = "ルギア",
    rate: float = 0.15,
    name_en: str | None = None,
    count: int | None = 30,
) -> PokekameshiMetaShare:
    return PokekameshiMetaShare(
        archetype_name=name,
        share_rate=rate,
        archetype_name_en=name_en,
        count=count,
    )


@pytest.mark.asyncio
async def test_scrape_happy_path():
    """Mock client returns report with shares, verify counts."""
    shares = [
        _make_share("ルギア", 0.15, count=30),
        _make_share("ピジョット", 0.10, count=20),
    ]
    report = _make_report(shares=shares)

    mock_client = AsyncMock()
    mock_client.fetch_meta_percentages = AsyncMock(return_value=report)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    mock_session = AsyncMock()

    # No existing records
    mock_result = MagicMock()
    mock_result.first.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    mock_session_ctx = AsyncMock()
    mock_session_ctx.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_ctx.__aexit__ = AsyncMock(return_value=None)

    with (
        patch(
            "src.pipelines.scrape_pokekameshi.PokekameshiClient",
            return_value=mock_client,
        ),
        patch(
            "src.pipelines.scrape_pokekameshi.async_session_factory",
            return_value=mock_session_ctx,
        ),
    ):
        result = await scrape_pokekameshi_meta(dry_run=False)

    assert result.success is True
    assert result.reports_fetched == 1
    assert result.shares_recorded == 2
    assert result.shares_skipped == 0
    assert result.errors == []
    assert mock_session.add.call_count == 2
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_duplicate_shares_skipped():
    """Existing records are skipped."""
    shares = [_make_share("ルギア", 0.15)]
    report = _make_report(shares=shares)

    mock_client = AsyncMock()
    mock_client.fetch_meta_percentages = AsyncMock(return_value=report)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    mock_session = AsyncMock()

    # Existing record found
    mock_result = MagicMock()
    mock_result.first.return_value = (uuid4(),)
    mock_session.execute = AsyncMock(return_value=mock_result)

    mock_session_ctx = AsyncMock()
    mock_session_ctx.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_ctx.__aexit__ = AsyncMock(return_value=None)

    with (
        patch(
            "src.pipelines.scrape_pokekameshi.PokekameshiClient",
            return_value=mock_client,
        ),
        patch(
            "src.pipelines.scrape_pokekameshi.async_session_factory",
            return_value=mock_session_ctx,
        ),
    ):
        result = await scrape_pokekameshi_meta(dry_run=False)

    assert result.success is True
    assert result.reports_fetched == 1
    assert result.shares_recorded == 0
    assert result.shares_skipped == 1
    mock_session.add.assert_not_called()


@pytest.mark.asyncio
async def test_dry_run_skips_persistence():
    """Verify no DB writes in dry run."""
    shares = [_make_share("ルギア", 0.15)]
    report = _make_report(shares=shares)

    mock_client = AsyncMock()
    mock_client.fetch_meta_percentages = AsyncMock(return_value=report)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch(
        "src.pipelines.scrape_pokekameshi.PokekameshiClient",
        return_value=mock_client,
    ):
        result = await scrape_pokekameshi_meta(dry_run=True)

    assert result.success is True
    assert result.reports_fetched == 1
    assert result.shares_recorded == 0
    assert result.shares_skipped == 0


@pytest.mark.asyncio
async def test_fetch_error_returns_error():
    """PokekameshiError is caught and returned."""
    mock_client = AsyncMock()
    mock_client.fetch_meta_percentages = AsyncMock(
        side_effect=PokekameshiError("Connection failed")
    )
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch(
        "src.pipelines.scrape_pokekameshi.PokekameshiClient",
        return_value=mock_client,
    ):
        result = await scrape_pokekameshi_meta(dry_run=False)

    assert result.success is False
    assert result.reports_fetched == 0
    assert len(result.errors) == 1
    assert "Connection failed" in result.errors[0]


@pytest.mark.asyncio
async def test_empty_shares():
    """Report with no shares returns zero counts."""
    report = _make_report(shares=[])

    mock_client = AsyncMock()
    mock_client.fetch_meta_percentages = AsyncMock(return_value=report)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch(
        "src.pipelines.scrape_pokekameshi.PokekameshiClient",
        return_value=mock_client,
    ):
        result = await scrape_pokekameshi_meta(dry_run=False)

    assert result.success is True
    assert result.reports_fetched == 1
    assert result.shares_recorded == 0
    assert result.shares_skipped == 0


@pytest.mark.asyncio
async def test_multiple_shares_recorded():
    """Verify all shares from report are recorded."""
    shares = [
        _make_share("ルギア", 0.15, count=30),
        _make_share("ピジョット", 0.10, count=20),
        _make_share("リザードン", 0.08, count=16),
        _make_share("ミライドン", 0.07, count=14),
    ]
    report = _make_report(shares=shares)

    mock_client = AsyncMock()
    mock_client.fetch_meta_percentages = AsyncMock(return_value=report)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    mock_session = AsyncMock()

    mock_result = MagicMock()
    mock_result.first.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    mock_session_ctx = AsyncMock()
    mock_session_ctx.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_ctx.__aexit__ = AsyncMock(return_value=None)

    with (
        patch(
            "src.pipelines.scrape_pokekameshi.PokekameshiClient",
            return_value=mock_client,
        ),
        patch(
            "src.pipelines.scrape_pokekameshi.async_session_factory",
            return_value=mock_session_ctx,
        ),
    ):
        result = await scrape_pokekameshi_meta(dry_run=False)

    assert result.success is True
    assert result.reports_fetched == 1
    assert result.shares_recorded == 4
    assert result.shares_skipped == 0
    assert mock_session.add.call_count == 4

    # Verify the added records have correct archetype names
    added_records = [call.args[0] for call in mock_session.add.call_args_list]
    archetype_names = [r.archetype_name_jp for r in added_records]
    assert "ルギア" in archetype_names
    assert "ピジョット" in archetype_names
    assert "リザードン" in archetype_names
    assert "ミライドン" in archetype_names


class TestPokekameshiRenderedFetch:
    @pytest.mark.asyncio
    async def test_get_rendered_calls_kernel_browser(self):
        """_get_rendered delegates to KernelBrowser.fetch_rendered."""
        with patch("src.clients.pokekameshi.KernelBrowser") as mock_kb_cls:
            mock_kb = AsyncMock()
            mock_kb.fetch_rendered = AsyncMock(return_value="<html>Rendered</html>")
            mock_kb_cls.return_value.__aenter__ = AsyncMock(return_value=mock_kb)
            mock_kb_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            client = PokekameshiClient()
            client._wait_for_rate_limit = AsyncMock()

            html = await client._get_rendered("/test/")

        assert html == "<html>Rendered</html>"
        mock_kb.fetch_rendered.assert_awaited_once_with(
            "https://pokekameshi.com/test/",
            wait_selector=None,
        )

    @pytest.mark.asyncio
    async def test_get_rendered_wraps_kernel_error(self):
        from src.clients.kernel_browser import KernelBrowserError

        with patch("src.clients.pokekameshi.KernelBrowser") as mock_kb_cls:
            mock_kb = AsyncMock()
            mock_kb.fetch_rendered = AsyncMock(
                side_effect=KernelBrowserError("Browser failed")
            )
            mock_kb_cls.return_value.__aenter__ = AsyncMock(return_value=mock_kb)
            mock_kb_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            client = PokekameshiClient()
            client._wait_for_rate_limit = AsyncMock()

            with pytest.raises(PokekameshiError, match="Rendered fetch failed"):
                await client._get_rendered("/test/")
