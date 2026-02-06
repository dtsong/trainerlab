"""Tests for MetaService comparison and forecast methods."""

from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import ArchetypeSprite, MetaSnapshot
from src.services.meta_service import MetaService


def _make_snapshot(
    *,
    region: str | None = None,
    best_of: int = 3,
    archetype_shares: dict | None = None,
    sample_size: int = 200,
    snapshot_date: date | None = None,
    tier_assignments: dict | None = None,
    trends: dict | None = None,
) -> MetaSnapshot:
    snap = MagicMock(spec=MetaSnapshot)
    snap.id = uuid4()
    snap.snapshot_date = snapshot_date or date.today()
    snap.region = region
    snap.format = "standard"
    snap.best_of = best_of
    snap.archetype_shares = (
        archetype_shares
        if archetype_shares is not None
        else {"Charizard ex": 0.18, "Lugia VSTAR": 0.12}
    )
    snap.card_usage = None
    snap.sample_size = sample_size
    snap.tournaments_included = []
    snap.diversity_index = None
    snap.tier_assignments = tier_assignments
    snap.jp_signals = None
    snap.trends = trends
    return snap


@pytest.fixture
def mock_session():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def service(mock_session):
    return MetaService(mock_session)


class TestConfidenceComputation:
    def test_high_confidence(self, service):
        c = service._compute_confidence(250, 2)
        assert c.confidence == "high"
        assert c.sample_size == 250
        assert c.data_freshness_days == 2

    def test_medium_confidence(self, service):
        c = service._compute_confidence(100, 5)
        assert c.confidence == "medium"

    def test_low_confidence_small_sample(self, service):
        c = service._compute_confidence(30, 2)
        assert c.confidence == "low"

    def test_low_confidence_stale_data(self, service):
        c = service._compute_confidence(200, 10)
        assert c.confidence == "low"

    def test_medium_boundary(self, service):
        c = service._compute_confidence(50, 7)
        assert c.confidence == "medium"

    def test_high_confidence_exact_boundary(self, service):
        """Exactly sample=200, fresh=3 is high."""
        c = service._compute_confidence(200, 3)
        assert c.confidence == "high"

    def test_medium_when_sample_just_below_high(self, service):
        """sample=199, fresh=3 drops to medium."""
        c = service._compute_confidence(199, 3)
        assert c.confidence == "medium"

    def test_medium_when_freshness_just_above_high(self, service):
        """sample=200, fresh=4 drops to medium."""
        c = service._compute_confidence(200, 4)
        assert c.confidence == "medium"

    def test_low_when_sample_just_below_medium(self, service):
        """sample=49, fresh=7 drops to low."""
        c = service._compute_confidence(49, 7)
        assert c.confidence == "low"

    def test_low_when_freshness_just_above_medium(self, service):
        """sample=50, fresh=8 drops to low."""
        c = service._compute_confidence(50, 8)
        assert c.confidence == "low"


class TestBestOfForRegion:
    def test_jp_returns_bo1(self, service):
        assert service._best_of_for_region("JP") == 1

    def test_na_returns_bo3(self, service):
        assert service._best_of_for_region("NA") == 3

    def test_global_returns_bo3(self, service):
        assert service._best_of_for_region(None) == 3


class TestComputeMetaComparison:
    @pytest.mark.asyncio
    async def test_both_regions_have_data(self, service):
        jp_snap = _make_snapshot(
            region="JP",
            best_of=1,
            archetype_shares={
                "Charizard ex": 0.20,
                "Raging Bolt ex": 0.15,
            },
            sample_size=250,
            tier_assignments={"Charizard ex": "S", "Raging Bolt ex": "A"},
        )
        global_snap = _make_snapshot(
            region=None,
            best_of=3,
            archetype_shares={
                "Charizard ex": 0.18,
                "Lugia VSTAR": 0.10,
            },
            sample_size=500,
            tier_assignments={"Charizard ex": "S", "Lugia VSTAR": "A"},
        )

        service._get_latest_snapshot = AsyncMock(side_effect=[jp_snap, global_snap])
        service._get_sprite_urls_for_archetypes = AsyncMock(return_value={})

        result = await service.compute_meta_comparison(region_a="JP", top_n=10)

        assert result.region_a == "JP"
        assert result.region_b == "Global"
        assert len(result.comparisons) > 0
        assert result.region_a_confidence.confidence == "high"
        assert result.lag_analysis is None

    @pytest.mark.asyncio
    async def test_with_lag_days(self, service):
        jp_snap = _make_snapshot(
            region="JP",
            best_of=1,
            sample_size=200,
        )
        global_snap = _make_snapshot(
            region=None,
            best_of=3,
            sample_size=300,
        )
        lagged_jp = _make_snapshot(
            region="JP",
            best_of=1,
            snapshot_date=date.today() - timedelta(days=14),
            archetype_shares={"Charizard ex": 0.22},
            sample_size=180,
        )

        service._get_latest_snapshot = AsyncMock(side_effect=[jp_snap, global_snap])
        service.get_snapshot = AsyncMock(return_value=lagged_jp)
        service._get_sprite_urls_for_archetypes = AsyncMock(return_value={})

        result = await service.compute_meta_comparison(
            region_a="JP", lag_days=14, top_n=5
        )

        assert result.lag_analysis is not None
        assert result.lag_analysis.lag_days == 14

    @pytest.mark.asyncio
    async def test_missing_region_raises(self, service):
        service._get_latest_snapshot = AsyncMock(side_effect=[None, _make_snapshot()])

        with pytest.raises(ValueError, match="No snapshot data"):
            await service.compute_meta_comparison(region_a="JP")

    @pytest.mark.asyncio
    async def test_comparison_divergence_sign(self, service):
        jp_snap = _make_snapshot(
            region="JP",
            best_of=1,
            archetype_shares={"Deck A": 0.20, "Deck B": 0.05},
        )
        en_snap = _make_snapshot(
            region=None,
            best_of=3,
            archetype_shares={"Deck A": 0.10, "Deck B": 0.15},
        )

        service._get_latest_snapshot = AsyncMock(side_effect=[jp_snap, en_snap])
        service._get_sprite_urls_for_archetypes = AsyncMock(return_value={})

        result = await service.compute_meta_comparison(region_a="JP", top_n=10)

        by_name = {c.archetype: c for c in result.comparisons}
        assert by_name["Deck A"].divergence > 0  # JP higher
        assert by_name["Deck B"].divergence < 0  # JP lower

    @pytest.mark.asyncio
    async def test_archetype_only_in_jp(self, service):
        """Archetype in JP but not EN gets en_share=0."""
        jp_snap = _make_snapshot(
            region="JP",
            best_of=1,
            archetype_shares={"JP Exclusive": 0.10},
        )
        en_snap = _make_snapshot(
            region=None,
            best_of=3,
            archetype_shares={"EN Deck": 0.12},
        )

        service._get_latest_snapshot = AsyncMock(side_effect=[jp_snap, en_snap])
        service._get_sprite_urls_for_archetypes = AsyncMock(return_value={})

        result = await service.compute_meta_comparison(region_a="JP", top_n=10)

        by_name = {c.archetype: c for c in result.comparisons}
        assert by_name["JP Exclusive"].region_a_share == 0.10
        assert by_name["JP Exclusive"].region_b_share == 0.0
        assert by_name["JP Exclusive"].divergence > 0

    @pytest.mark.asyncio
    async def test_archetype_only_in_en(self, service):
        """Archetype in EN but not JP gets region_a_share=0."""
        jp_snap = _make_snapshot(
            region="JP",
            best_of=1,
            archetype_shares={"JP Deck": 0.08},
        )
        en_snap = _make_snapshot(
            region=None,
            best_of=3,
            archetype_shares={"EN Only": 0.15},
        )

        service._get_latest_snapshot = AsyncMock(side_effect=[jp_snap, en_snap])
        service._get_sprite_urls_for_archetypes = AsyncMock(return_value={})

        result = await service.compute_meta_comparison(region_a="JP", top_n=10)

        by_name = {c.archetype: c for c in result.comparisons}
        assert by_name["EN Only"].region_a_share == 0.0
        assert by_name["EN Only"].region_b_share == 0.15
        assert by_name["EN Only"].divergence < 0

    @pytest.mark.asyncio
    async def test_top_n_limits_results(self, service):
        """top_n=1 returns only the top archetype."""
        jp_snap = _make_snapshot(
            region="JP",
            best_of=1,
            archetype_shares={
                "Big Deck": 0.25,
                "Small Deck": 0.05,
            },
        )
        en_snap = _make_snapshot(
            region=None,
            best_of=3,
            archetype_shares={
                "Big Deck": 0.20,
                "Small Deck": 0.03,
            },
        )

        service._get_latest_snapshot = AsyncMock(side_effect=[jp_snap, en_snap])
        service._get_sprite_urls_for_archetypes = AsyncMock(return_value={})

        result = await service.compute_meta_comparison(region_a="JP", top_n=1)

        assert len(result.comparisons) == 1
        assert result.comparisons[0].archetype == "Big Deck"

    @pytest.mark.asyncio
    async def test_lag_no_historical_snapshot(self, service):
        """Lag analysis with no historical snapshot produces None."""
        jp_snap = _make_snapshot(region="JP", best_of=1, sample_size=200)
        en_snap = _make_snapshot(region=None, best_of=3, sample_size=300)

        service._get_latest_snapshot = AsyncMock(side_effect=[jp_snap, en_snap])
        service.get_snapshot = AsyncMock(return_value=None)
        service._get_sprite_urls_for_archetypes = AsyncMock(return_value={})

        result = await service.compute_meta_comparison(
            region_a="JP", lag_days=14, top_n=5
        )

        assert result.lag_analysis is None


class TestComputeFormatForecast:
    @pytest.mark.asyncio
    async def test_forecast_with_divergent_archetypes(self, service):
        jp_snap = _make_snapshot(
            region="JP",
            best_of=1,
            archetype_shares={
                "Charizard ex": 0.20,
                "Raging Bolt ex": 0.15,
                "Tiny Deck": 0.005,  # below 1% threshold
            },
            sample_size=200,
            tier_assignments={"Charizard ex": "S"},
            trends={
                "Charizard ex": {
                    "change": 0.02,
                    "direction": "up",
                    "previous_share": 0.18,
                },
            },
        )
        en_snap = _make_snapshot(
            region=None,
            best_of=3,
            archetype_shares={
                "Charizard ex": 0.18,
                "Lugia VSTAR": 0.12,
            },
            sample_size=500,
        )

        service._get_latest_snapshot = AsyncMock(side_effect=[jp_snap, en_snap])
        service._get_sprite_urls_for_archetypes = AsyncMock(
            return_value={"Charizard ex": ["https://example.com/charizard.png"]}
        )

        result = await service.compute_format_forecast(top_n=5)

        assert len(result.forecast_archetypes) == 2
        assert result.forecast_archetypes[0].archetype == "Charizard ex"
        assert result.forecast_archetypes[0].jp_share == 0.20
        assert result.forecast_archetypes[0].tier == "S"
        assert result.forecast_archetypes[0].trend_direction == "up"
        assert len(result.forecast_archetypes[0].sprite_urls) == 1
        # Tiny Deck filtered (< 1%)
        names = [e.archetype for e in result.forecast_archetypes]
        assert "Tiny Deck" not in names

    @pytest.mark.asyncio
    async def test_forecast_filters_below_one_percent(self, service):
        """jp_share=0.009 is excluded (<1%)."""
        jp_snap = _make_snapshot(
            region="JP",
            best_of=1,
            archetype_shares={
                "Big Deck": 0.15,
                "Borderline": 0.009,
            },
            sample_size=200,
        )
        en_snap = _make_snapshot(sample_size=500)

        service._get_latest_snapshot = AsyncMock(side_effect=[jp_snap, en_snap])
        service._get_sprite_urls_for_archetypes = AsyncMock(return_value={})

        result = await service.compute_format_forecast(top_n=10)

        names = [e.archetype for e in result.forecast_archetypes]
        assert "Big Deck" in names
        assert "Borderline" not in names

    @pytest.mark.asyncio
    async def test_forecast_top_n_limits_results(self, service):
        """top_n=1 returns at most 1 entry."""
        jp_snap = _make_snapshot(
            region="JP",
            best_of=1,
            archetype_shares={
                "Deck A": 0.20,
                "Deck B": 0.15,
                "Deck C": 0.10,
            },
            sample_size=200,
        )
        en_snap = _make_snapshot(sample_size=500)

        service._get_latest_snapshot = AsyncMock(side_effect=[jp_snap, en_snap])
        service._get_sprite_urls_for_archetypes = AsyncMock(return_value={})

        result = await service.compute_format_forecast(top_n=1)
        assert len(result.forecast_archetypes) == 1
        assert result.forecast_archetypes[0].archetype == "Deck A"

    @pytest.mark.asyncio
    async def test_forecast_sorted_by_jp_share_desc(self, service):
        """Entries are sorted by jp_share descending."""
        jp_snap = _make_snapshot(
            region="JP",
            best_of=1,
            archetype_shares={
                "Low": 0.05,
                "High": 0.25,
                "Mid": 0.12,
            },
            sample_size=200,
        )
        en_snap = _make_snapshot(sample_size=500)

        service._get_latest_snapshot = AsyncMock(side_effect=[jp_snap, en_snap])
        service._get_sprite_urls_for_archetypes = AsyncMock(return_value={})

        result = await service.compute_format_forecast(top_n=10)
        shares = [e.jp_share for e in result.forecast_archetypes]
        assert shares == sorted(shares, reverse=True)

    @pytest.mark.asyncio
    async def test_forecast_missing_jp_raises(self, service):
        service._get_latest_snapshot = AsyncMock(side_effect=[None, _make_snapshot()])

        with pytest.raises(ValueError, match="JP"):
            await service.compute_format_forecast()

    @pytest.mark.asyncio
    async def test_forecast_empty_jp_returns_empty(self, service):
        jp_snap = _make_snapshot(
            region="JP",
            best_of=1,
            archetype_shares={},
            sample_size=0,
        )
        en_snap = _make_snapshot(sample_size=500)

        service._get_latest_snapshot = AsyncMock(side_effect=[jp_snap, en_snap])
        service._get_sprite_urls_for_archetypes = AsyncMock(return_value={})

        result = await service.compute_format_forecast()
        assert len(result.forecast_archetypes) == 0


class TestGetSpriteUrls:
    @pytest.mark.asyncio
    async def test_returns_sprite_urls(self, service, mock_session):
        sprite = MagicMock(spec=ArchetypeSprite)
        sprite.archetype_name = "Charizard ex"
        sprite.sprite_urls = ["https://example.com/charizard.png"]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sprite]
        mock_session.execute.return_value = mock_result

        urls = await service._get_sprite_urls_for_archetypes(["Charizard ex"])

        assert urls == {"Charizard ex": ["https://example.com/charizard.png"]}

    @pytest.mark.asyncio
    async def test_empty_list_returns_empty(self, service):
        result = await service._get_sprite_urls_for_archetypes([])
        assert result == {}
