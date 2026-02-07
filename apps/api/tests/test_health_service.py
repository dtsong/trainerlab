"""Tests for PipelineHealthService."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.services.health_service import (
    ARCHETYPE_UNKNOWN_DEGRADED,
    ARCHETYPE_UNKNOWN_OK,
    META_OK_DAYS,
    SCRAPE_OK_DAYS,
    PipelineHealthService,
)


def make_mock_session() -> AsyncMock:
    return AsyncMock()


def make_result(*values):
    """Create a mock result object that returns values."""
    mock = MagicMock()
    mock.one.return_value = values
    mock.scalar.return_value = values[0] if values else None
    mock.all.return_value = [(v,) for v in values]
    return mock


class TestScrapeHealthOk:
    """Scrape within OK threshold."""

    @pytest.mark.asyncio
    async def test_scrape_recent(self) -> None:
        session = make_mock_session()
        recent = datetime.now(UTC) - timedelta(days=1)
        # First execute: max(created_at), count
        scrape_result = MagicMock()
        scrape_result.one.return_value = (recent, 5)
        # Second execute: distinct regions
        region_result = MagicMock()
        region_result.all.return_value = [("JP",), ("NA",)]

        session.execute = AsyncMock(side_effect=[scrape_result, region_result])

        service = PipelineHealthService(session)
        result = await service.get_scrape_health()

        assert result.status == "ok"
        assert result.days_since_scrape is not None
        assert result.days_since_scrape <= SCRAPE_OK_DAYS


class TestScrapeHealthStale:
    """Scrape in stale window."""

    @pytest.mark.asyncio
    async def test_scrape_stale(self) -> None:
        session = make_mock_session()
        stale = datetime.now(UTC) - timedelta(days=SCRAPE_OK_DAYS + 2)
        scrape_result = MagicMock()
        scrape_result.one.return_value = (stale, 1)
        region_result = MagicMock()
        region_result.all.return_value = [("JP",)]

        session.execute = AsyncMock(side_effect=[scrape_result, region_result])

        service = PipelineHealthService(session)
        result = await service.get_scrape_health()

        assert result.status == "stale"


class TestScrapeHealthMissing:
    """No scrape data at all."""

    @pytest.mark.asyncio
    async def test_scrape_missing(self) -> None:
        session = make_mock_session()
        scrape_result = MagicMock()
        scrape_result.one.return_value = (None, 0)
        region_result = MagicMock()
        region_result.all.return_value = []

        session.execute = AsyncMock(side_effect=[scrape_result, region_result])

        service = PipelineHealthService(session)
        result = await service.get_scrape_health()

        assert result.status == "missing"
        assert result.last_scrape_date is None


class TestMetaHealthOk:
    """Meta snapshot within OK threshold."""

    @pytest.mark.asyncio
    async def test_meta_recent(self) -> None:
        session = make_mock_session()
        recent_date = date.today() - timedelta(days=1)

        date_result = MagicMock()
        date_result.scalar.return_value = recent_date
        region_result = MagicMock()
        region_result.all.return_value = [
            (None,),
            ("JP",),
        ]

        session.execute = AsyncMock(side_effect=[date_result, region_result])

        service = PipelineHealthService(session)
        result = await service.get_meta_health()

        assert result.status == "ok"
        assert result.snapshot_age_days is not None
        assert result.snapshot_age_days <= META_OK_DAYS


class TestMetaHealthStale:
    """Meta snapshot in stale window."""

    @pytest.mark.asyncio
    async def test_meta_stale(self) -> None:
        session = make_mock_session()
        stale_date = date.today() - timedelta(days=META_OK_DAYS + 2)

        date_result = MagicMock()
        date_result.scalar.return_value = stale_date
        region_result = MagicMock()
        region_result.all.return_value = [(None,)]

        session.execute = AsyncMock(side_effect=[date_result, region_result])

        service = PipelineHealthService(session)
        result = await service.get_meta_health()

        assert result.status == "stale"


class TestArchetypeHealthDegraded:
    """Archetype detection with elevated unknown rate."""

    @pytest.mark.asyncio
    async def test_archetype_degraded(self) -> None:
        session = make_mock_session()
        # 15% unknown rate (between OK and degraded thresholds)
        rows = [
            ("Charizard ex", "sprite_lookup"),
        ] * 85 + [
            ("Unknown", "text_label"),
        ] * 15

        result_mock = MagicMock()
        result_mock.all.return_value = rows
        session.execute = AsyncMock(return_value=result_mock)

        service = PipelineHealthService(session)
        result = await service.get_archetype_health()

        assert result.status == "degraded"
        assert result.unknown_rate > ARCHETYPE_UNKNOWN_OK
        assert result.unknown_rate <= ARCHETYPE_UNKNOWN_DEGRADED
        assert result.sample_size == 100


class TestArchetypeHealthPoor:
    """Archetype detection with high unknown rate."""

    @pytest.mark.asyncio
    async def test_archetype_poor(self) -> None:
        session = make_mock_session()
        # 30% unknown
        rows = [
            ("Charizard ex", "sprite_lookup"),
        ] * 70 + [
            ("Unknown", "text_label"),
        ] * 30

        result_mock = MagicMock()
        result_mock.all.return_value = rows
        session.execute = AsyncMock(return_value=result_mock)

        service = PipelineHealthService(session)
        result = await service.get_archetype_health()

        assert result.status == "poor"
        assert result.unknown_rate > ARCHETYPE_UNKNOWN_DEGRADED


class TestOverallStatusAggregation:
    """Overall status is the worst component."""

    @pytest.mark.asyncio
    async def test_overall_healthy(self) -> None:
        session = make_mock_session()
        recent = datetime.now(UTC) - timedelta(days=1)
        recent_date = date.today() - timedelta(days=1)

        # Scrape: ok
        scrape_result = MagicMock()
        scrape_result.one.return_value = (recent, 5)
        scrape_region = MagicMock()
        scrape_region.all.return_value = [("JP",)]

        # Meta: ok
        meta_date = MagicMock()
        meta_date.scalar.return_value = recent_date
        meta_region = MagicMock()
        meta_region.all.return_value = [(None,)]

        # Archetype: ok (all sprite_lookup)
        arch_result = MagicMock()
        arch_result.all.return_value = [
            ("Charizard ex", "sprite_lookup"),
        ] * 50

        session.execute = AsyncMock(
            side_effect=[
                scrape_result,
                scrape_region,
                meta_date,
                meta_region,
                arch_result,
            ]
        )

        service = PipelineHealthService(session)
        result = await service.get_pipeline_health()

        assert result.status == "healthy"
        assert result.scrape.status == "ok"
        assert result.meta.status == "ok"
        assert result.archetype.status == "ok"

    @pytest.mark.asyncio
    async def test_overall_degraded(self) -> None:
        session = make_mock_session()
        recent = datetime.now(UTC) - timedelta(days=1)
        stale_date = date.today() - timedelta(days=META_OK_DAYS + 2)

        # Scrape: ok
        scrape_result = MagicMock()
        scrape_result.one.return_value = (recent, 5)
        scrape_region = MagicMock()
        scrape_region.all.return_value = [("JP",)]

        # Meta: stale
        meta_date = MagicMock()
        meta_date.scalar.return_value = stale_date
        meta_region = MagicMock()
        meta_region.all.return_value = [(None,)]

        # Archetype: ok
        arch_result = MagicMock()
        arch_result.all.return_value = [
            ("Charizard ex", "sprite_lookup"),
        ] * 50

        session.execute = AsyncMock(
            side_effect=[
                scrape_result,
                scrape_region,
                meta_date,
                meta_region,
                arch_result,
            ]
        )

        service = PipelineHealthService(session)
        result = await service.get_pipeline_health()

        assert result.status == "degraded"
        assert result.meta.status == "stale"
