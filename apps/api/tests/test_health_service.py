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


class TestScrapeHealthVeryOld:
    """Scrape beyond stale threshold → missing."""

    @pytest.mark.asyncio
    async def test_scrape_very_old(self) -> None:
        from src.services.health_service import SCRAPE_STALE_DAYS

        session = make_mock_session()
        very_old = datetime.now(UTC) - timedelta(days=SCRAPE_STALE_DAYS + 5)
        scrape_result = MagicMock()
        scrape_result.one.return_value = (very_old, 0)
        region_result = MagicMock()
        region_result.all.return_value = []

        session.execute = AsyncMock(side_effect=[scrape_result, region_result])

        service = PipelineHealthService(session)
        result = await service.get_scrape_health()

        assert result.status == "missing"
        assert result.days_since_scrape is not None
        assert result.days_since_scrape > SCRAPE_STALE_DAYS


class TestMetaHealthMissing:
    """No meta data at all."""

    @pytest.mark.asyncio
    async def test_meta_missing(self) -> None:
        session = make_mock_session()
        date_result = MagicMock()
        date_result.scalar.return_value = None
        region_result = MagicMock()
        region_result.all.return_value = []

        session.execute = AsyncMock(side_effect=[date_result, region_result])

        service = PipelineHealthService(session)
        result = await service.get_meta_health()

        assert result.status == "missing"
        assert result.latest_snapshot_date is None


class TestMetaHealthVeryOld:
    """Meta beyond stale threshold → missing."""

    @pytest.mark.asyncio
    async def test_meta_very_old(self) -> None:
        from src.services.health_service import META_STALE_DAYS

        session = make_mock_session()
        very_old = date.today() - timedelta(days=META_STALE_DAYS + 5)
        date_result = MagicMock()
        date_result.scalar.return_value = very_old
        region_result = MagicMock()
        region_result.all.return_value = [(None,)]

        session.execute = AsyncMock(side_effect=[date_result, region_result])

        service = PipelineHealthService(session)
        result = await service.get_meta_health()

        assert result.status == "missing"


class TestArchetypeHealthOk:
    """Archetype detection within OK threshold."""

    @pytest.mark.asyncio
    async def test_archetype_ok(self) -> None:
        session = make_mock_session()
        # 5% unknown rate (below OK threshold)
        rows = [
            ("Charizard ex", "sprite_lookup"),
        ] * 95 + [
            ("Unknown", "text_label"),
        ] * 5

        result_mock = MagicMock()
        result_mock.all.return_value = rows
        session.execute = AsyncMock(return_value=result_mock)

        service = PipelineHealthService(session)
        result = await service.get_archetype_health()

        assert result.status == "ok"
        assert result.unknown_rate <= ARCHETYPE_UNKNOWN_OK
        assert result.sample_size == 100


class TestArchetypeHealthEmpty:
    """No placement data at all."""

    @pytest.mark.asyncio
    async def test_archetype_empty(self) -> None:
        session = make_mock_session()
        result_mock = MagicMock()
        result_mock.all.return_value = []
        session.execute = AsyncMock(return_value=result_mock)

        service = PipelineHealthService(session)
        result = await service.get_archetype_health()

        assert result.status == "ok"
        assert result.sample_size == 0


class TestArchetypeHealthUncoveredSprites:
    """text_label fallbacks produce uncovered sprite keys."""

    @pytest.mark.asyncio
    async def test_uncovered_sprites(self) -> None:
        session = make_mock_session()
        rows = (
            [
                ("Charizard ex", "sprite_lookup"),
            ]
            * 80
            + [
                ("Unknown", "text_label"),
            ]
            * 5
            + [
                ("Rogue", "text_label"),
            ]
            * 5
            + [
                ("Cinderace ex", "text_label"),
            ]
            * 5
            + [
                ("Dragapult ex", "text_label"),
            ]
            * 5
        )

        result_mock = MagicMock()
        result_mock.all.return_value = rows
        session.execute = AsyncMock(return_value=result_mock)

        service = PipelineHealthService(session)
        result = await service.get_archetype_health()

        # "Unknown" and "Rogue" are filtered from uncovered
        assert "Cinderace ex" in result.uncovered_sprite_keys
        assert "Dragapult ex" in result.uncovered_sprite_keys
        assert "Unknown" not in result.uncovered_sprite_keys
        assert "Rogue" not in result.uncovered_sprite_keys


class TestArchetypeMethodDistribution:
    """Method distribution is calculated correctly."""

    @pytest.mark.asyncio
    async def test_method_distribution(self) -> None:
        session = make_mock_session()
        rows = (
            [
                ("A", "sprite_lookup"),
            ]
            * 60
            + [
                ("B", "auto_derive"),
            ]
            * 30
            + [
                ("C", "text_label"),
            ]
            * 10
        )

        result_mock = MagicMock()
        result_mock.all.return_value = rows
        session.execute = AsyncMock(return_value=result_mock)

        service = PipelineHealthService(session)
        result = await service.get_archetype_health()

        assert result.method_distribution["sprite_lookup"] == 0.6
        assert result.method_distribution["auto_derive"] == 0.3
        assert result.method_distribution["text_label"] == 0.1


class TestVerboseArchetypeDetail:
    """Verbose mode returns unknown placements, fallbacks, and trends."""

    @pytest.mark.asyncio
    async def test_verbose_returns_unknown_placements(self) -> None:
        session = make_mock_session()
        # Unknown placements query
        unknown_result = MagicMock()
        unknown_result.all.return_value = [
            (
                "https://limitless.com/t/123",
                ["charizard.png"],
                "raw_arch",
                "text_label",
            ),
        ]
        # text_label fallback query
        text_result = MagicMock()
        text_result.all.return_value = [
            ("Cinderace ex", 5),
        ]
        # trend query
        trend_result = MagicMock()
        trend_result.all.return_value = [
            ("2025-01-01", "sprite_lookup", 80),
            ("2025-01-01", "text_label", 20),
        ]

        session.execute = AsyncMock(
            side_effect=[unknown_result, text_result, trend_result]
        )

        service = PipelineHealthService(session)
        result = await service.get_verbose_archetype_detail()

        assert len(result.unknown_placements) == 1
        assert result.unknown_placements[0].raw_archetype == "raw_arch"
        assert len(result.text_label_fallbacks) == 1
        assert result.text_label_fallbacks[0].resolved_archetype == "Cinderace ex"
        assert len(result.method_trends) == 1
        assert result.method_trends[0].date == "2025-01-01"

    @pytest.mark.asyncio
    async def test_verbose_empty_results(self) -> None:
        session = make_mock_session()
        empty_result = MagicMock()
        empty_result.all.return_value = []

        session.execute = AsyncMock(return_value=empty_result)

        service = PipelineHealthService(session)
        result = await service.get_verbose_archetype_detail()

        assert result.unknown_placements == []
        assert result.text_label_fallbacks == []
        assert result.method_trends == []


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

    @pytest.mark.asyncio
    async def test_overall_unhealthy(self) -> None:
        from src.services.health_service import META_STALE_DAYS

        session = make_mock_session()
        recent = datetime.now(UTC) - timedelta(days=1)
        very_old = date.today() - timedelta(days=META_STALE_DAYS + 5)

        # Scrape: ok
        scrape_result = MagicMock()
        scrape_result.one.return_value = (recent, 5)
        scrape_region = MagicMock()
        scrape_region.all.return_value = [("JP",)]

        # Meta: missing (beyond stale threshold)
        meta_date = MagicMock()
        meta_date.scalar.return_value = very_old
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

        assert result.status == "unhealthy"
        assert result.meta.status == "missing"

    @pytest.mark.asyncio
    async def test_verbose_mode_includes_detail(self) -> None:
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

        # Archetype: ok
        arch_result = MagicMock()
        arch_result.all.return_value = [
            ("Charizard ex", "sprite_lookup"),
        ] * 50

        # Verbose queries
        unknown_result = MagicMock()
        unknown_result.all.return_value = []
        text_result = MagicMock()
        text_result.all.return_value = []
        trend_result = MagicMock()
        trend_result.all.return_value = []

        session.execute = AsyncMock(
            side_effect=[
                scrape_result,
                scrape_region,
                meta_date,
                meta_region,
                arch_result,
                unknown_result,
                text_result,
                trend_result,
            ]
        )

        service = PipelineHealthService(session)
        result = await service.get_pipeline_health(verbose=True)

        assert result.status == "healthy"
        assert result.verbose is not None

    @pytest.mark.asyncio
    async def test_non_verbose_omits_detail(self) -> None:
        session = make_mock_session()
        recent = datetime.now(UTC) - timedelta(days=1)
        recent_date = date.today() - timedelta(days=1)

        scrape_result = MagicMock()
        scrape_result.one.return_value = (recent, 5)
        scrape_region = MagicMock()
        scrape_region.all.return_value = [("JP",)]
        meta_date = MagicMock()
        meta_date.scalar.return_value = recent_date
        meta_region = MagicMock()
        meta_region.all.return_value = [(None,)]
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
        result = await service.get_pipeline_health(verbose=False)

        assert result.verbose is None


class TestSourceHealthDetail:
    """Source-level health visibility is included in pipeline health."""

    @pytest.mark.asyncio
    async def test_pipeline_health_includes_sources(self) -> None:
        session = make_mock_session()
        recent = datetime.now(UTC) - timedelta(days=1)
        recent_date = date.today() - timedelta(days=1)

        scrape_result = MagicMock()
        scrape_result.one.return_value = (recent, 5)
        scrape_region = MagicMock()
        scrape_region.all.return_value = [("JP",)]

        meta_date = MagicMock()
        meta_date.scalar.return_value = recent_date
        meta_region = MagicMock()
        meta_region.all.return_value = [(None,)]

        arch_result = MagicMock()
        arch_result.all.return_value = [("Charizard ex", "sprite_lookup")] * 50

        session.execute = AsyncMock(
            side_effect=[
                scrape_result,
                scrape_region,
                meta_date,
                meta_region,
                arch_result,
            ]
        )
        session.scalar = AsyncMock(
            side_effect=[
                datetime.now(UTC),  # tcgdex
                date.today(),  # limitless
                datetime.now(UTC),  # rk9
                datetime.now(UTC),  # pokemon_events
                None,  # pokecabook
                None,  # pokekameshi
            ]
        )

        service = PipelineHealthService(session)
        result = await service.get_pipeline_health()

        assert len(result.sources) == 6
        by_source = {item.source: item for item in result.sources}
        assert by_source["tcgdex"].status == "ok"
        assert by_source["limitless"].status == "ok"
        assert by_source["pokecabook"].status == "missing"
        assert by_source["pokecabook"].failure_reason == "no_recent_source_data"
