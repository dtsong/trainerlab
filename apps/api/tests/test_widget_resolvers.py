"""Tests for widget resolvers."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.meta_snapshot import MetaSnapshot
from src.services.widget_resolvers import get_all_widget_types, get_resolver, register_resolver
from src.services.widget_resolvers.archetype_card import ArchetypeCardResolver
from src.services.widget_resolvers.meta_pie import MetaPieResolver
from src.services.widget_resolvers.meta_snapshot import MetaSnapshotResolver


@pytest.fixture
def mock_session() -> AsyncMock:
    """Create a mock database session."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_meta_snapshot() -> MetaSnapshot:
    """Create a mock meta snapshot."""
    snapshot = MagicMock(spec=MetaSnapshot)
    snapshot.snapshot_date = date(2024, 1, 15)
    snapshot.format = "standard"
    snapshot.best_of = 3
    snapshot.region = None
    snapshot.archetype_shares = {
        "Charizard ex": 0.25,
        "Gardevoir ex": 0.20,
        "Lugia VSTAR": 0.15,
        "Lost Zone Box": 0.10,
        "Chien-Pao ex": 0.08,
        "Roaring Moon ex": 0.07,
        "Raging Bolt ex": 0.06,
        "Gholdengo ex": 0.05,
        "Miraidon ex": 0.03,
        "Other": 0.01,
    }
    snapshot.tier_assignments = {
        "Charizard ex": "S",
        "Gardevoir ex": "S",
        "Lugia VSTAR": "A",
    }
    snapshot.trends = {
        "Charizard ex": {"direction": "up", "change": 0.02},
        "Gardevoir ex": {"direction": "stable", "change": 0.0},
    }
    snapshot.diversity_index = 0.85
    snapshot.sample_size = 1500
    return snapshot


class TestResolverRegistry:
    """Tests for resolver registry functions."""

    def test_get_resolver_returns_registered_resolver(self):
        """Test getting a registered resolver."""
        resolver = get_resolver("meta_snapshot")
        assert resolver is MetaSnapshotResolver

    def test_get_resolver_returns_none_for_unknown(self):
        """Test returning None for unknown type."""
        resolver = get_resolver("unknown_type")
        assert resolver is None

    def test_get_all_widget_types_returns_list(self):
        """Test getting all widget types."""
        types = get_all_widget_types()
        assert isinstance(types, list)
        assert "meta_snapshot" in types
        assert "archetype_card" in types
        assert "meta_pie" in types

    def test_register_resolver_adds_to_registry(self):
        """Test registering a new resolver."""

        @register_resolver("test_widget")
        class TestResolver:
            async def resolve(self, session, config):
                return {}

        assert get_resolver("test_widget") is TestResolver


class TestMetaSnapshotResolver:
    """Tests for MetaSnapshotResolver."""

    @pytest.mark.asyncio
    async def test_resolve_returns_meta_data(
        self, mock_session: AsyncMock, mock_meta_snapshot: MetaSnapshot
    ):
        """Test resolving meta snapshot data."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_meta_snapshot
        mock_session.execute.return_value = mock_result

        resolver = MetaSnapshotResolver()
        result = await resolver.resolve(mock_session, {"format": "standard"})

        assert result["snapshot_date"] == "2024-01-15"
        assert result["format"] == "standard"
        assert len(result["archetypes"]) > 0
        assert result["archetypes"][0]["name"] == "Charizard ex"
        assert result["archetypes"][0]["share"] == 0.25

    @pytest.mark.asyncio
    async def test_resolve_with_region_filter(
        self, mock_session: AsyncMock, mock_meta_snapshot: MetaSnapshot
    ):
        """Test resolving with region filter."""
        mock_meta_snapshot.region = "NA"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_meta_snapshot
        mock_session.execute.return_value = mock_result

        resolver = MetaSnapshotResolver()
        result = await resolver.resolve(
            mock_session, {"format": "standard", "region": "NA"}
        )

        assert result["region"] == "NA"

    @pytest.mark.asyncio
    async def test_resolve_with_top_n_limit(
        self, mock_session: AsyncMock, mock_meta_snapshot: MetaSnapshot
    ):
        """Test resolving with top_n limit."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_meta_snapshot
        mock_session.execute.return_value = mock_result

        resolver = MetaSnapshotResolver()
        result = await resolver.resolve(mock_session, {"top_n": 3})

        assert len(result["archetypes"]) == 3

    @pytest.mark.asyncio
    async def test_resolve_returns_error_when_no_data(self, mock_session: AsyncMock):
        """Test returning error when no data available."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        resolver = MetaSnapshotResolver()
        result = await resolver.resolve(mock_session, {})

        assert "error" in result
        assert result["error"] == "No data available"

    @pytest.mark.asyncio
    async def test_resolve_includes_tier_and_trend(
        self, mock_session: AsyncMock, mock_meta_snapshot: MetaSnapshot
    ):
        """Test that tier and trend data are included."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_meta_snapshot
        mock_session.execute.return_value = mock_result

        resolver = MetaSnapshotResolver()
        result = await resolver.resolve(mock_session, {})

        charizard = next(a for a in result["archetypes"] if a["name"] == "Charizard ex")
        assert charizard["tier"] == "S"
        assert charizard["trend"] == "up"
        assert charizard["trend_change"] == 0.02


class TestArchetypeCardResolver:
    """Tests for ArchetypeCardResolver."""

    @pytest.mark.asyncio
    async def test_resolve_returns_archetype_data(
        self, mock_session: AsyncMock, mock_meta_snapshot: MetaSnapshot
    ):
        """Test resolving archetype card data."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_meta_snapshot
        mock_session.execute.return_value = mock_result

        resolver = ArchetypeCardResolver()
        result = await resolver.resolve(mock_session, {"archetype": "Charizard ex"})

        assert result["archetype"] == "Charizard ex"
        assert result["share"] == 0.25
        assert result["tier"] == "S"
        assert result["rank"] == 1

    @pytest.mark.asyncio
    async def test_resolve_requires_archetype(self, mock_session: AsyncMock):
        """Test that archetype is required."""
        resolver = ArchetypeCardResolver()
        result = await resolver.resolve(mock_session, {})

        assert "error" in result
        assert "required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_resolve_returns_error_for_unknown_archetype(
        self, mock_session: AsyncMock, mock_meta_snapshot: MetaSnapshot
    ):
        """Test returning error for unknown archetype."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_meta_snapshot
        mock_session.execute.return_value = mock_result

        resolver = ArchetypeCardResolver()
        result = await resolver.resolve(mock_session, {"archetype": "Unknown Deck"})

        assert "error" in result
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_resolve_calculates_rank_correctly(
        self, mock_session: AsyncMock, mock_meta_snapshot: MetaSnapshot
    ):
        """Test that rank is calculated correctly."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_meta_snapshot
        mock_session.execute.return_value = mock_result

        resolver = ArchetypeCardResolver()

        result1 = await resolver.resolve(mock_session, {"archetype": "Charizard ex"})
        assert result1["rank"] == 1

        result2 = await resolver.resolve(mock_session, {"archetype": "Gardevoir ex"})
        assert result2["rank"] == 2


class TestMetaPieResolver:
    """Tests for MetaPieResolver."""

    @pytest.mark.asyncio
    async def test_resolve_returns_pie_slices(
        self, mock_session: AsyncMock, mock_meta_snapshot: MetaSnapshot
    ):
        """Test resolving pie chart slices."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_meta_snapshot
        mock_session.execute.return_value = mock_result

        resolver = MetaPieResolver()
        result = await resolver.resolve(mock_session, {"top_n": 5})

        assert "slices" in result
        assert len(result["slices"]) <= 6  # top_n + Others

    @pytest.mark.asyncio
    async def test_resolve_groups_others(
        self, mock_session: AsyncMock, mock_meta_snapshot: MetaSnapshot
    ):
        """Test grouping remaining archetypes as Others."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_meta_snapshot
        mock_session.execute.return_value = mock_result

        resolver = MetaPieResolver()
        result = await resolver.resolve(
            mock_session, {"top_n": 3, "group_others": True}
        )

        others = next((s for s in result["slices"] if s["name"] == "Others"), None)
        assert others is not None
        assert others["share"] > 0

    @pytest.mark.asyncio
    async def test_resolve_without_others_grouping(
        self, mock_session: AsyncMock, mock_meta_snapshot: MetaSnapshot
    ):
        """Test resolving without grouping Others."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_meta_snapshot
        mock_session.execute.return_value = mock_result

        resolver = MetaPieResolver()
        result = await resolver.resolve(
            mock_session, {"top_n": 3, "group_others": False}
        )

        others = next((s for s in result["slices"] if s["name"] == "Others"), None)
        assert others is None
        assert len(result["slices"]) == 3

    @pytest.mark.asyncio
    async def test_resolve_includes_total_archetypes(
        self, mock_session: AsyncMock, mock_meta_snapshot: MetaSnapshot
    ):
        """Test including total archetypes count."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_meta_snapshot
        mock_session.execute.return_value = mock_result

        resolver = MetaPieResolver()
        result = await resolver.resolve(mock_session, {})

        assert "total_archetypes" in result
        assert result["total_archetypes"] == len(mock_meta_snapshot.archetype_shares)

    @pytest.mark.asyncio
    async def test_resolve_returns_error_when_no_data(self, mock_session: AsyncMock):
        """Test returning error when no data available."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        resolver = MetaPieResolver()
        result = await resolver.resolve(mock_session, {})

        assert "error" in result


class TestResolverProtocol:
    """Tests for resolver protocol compliance."""

    def test_all_resolvers_have_resolve_method(self):
        """Test that all registered resolvers have resolve method."""
        widget_types = get_all_widget_types()
        for widget_type in widget_types:
            resolver_class = get_resolver(widget_type)
            assert resolver_class is not None
            assert hasattr(resolver_class, "resolve")

    @pytest.mark.asyncio
    async def test_resolvers_return_dict(self, mock_session: AsyncMock):
        """Test that all resolvers return a dict."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        widget_types = ["meta_snapshot", "archetype_card", "meta_pie"]
        for widget_type in widget_types:
            resolver_class = get_resolver(widget_type)
            resolver = resolver_class()
            result = await resolver.resolve(mock_session, {})
            assert isinstance(result, dict)
