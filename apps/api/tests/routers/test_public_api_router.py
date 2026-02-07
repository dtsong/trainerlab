"""Tests for public API router."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.models.api_key import ApiKey
from src.models.meta_snapshot import MetaSnapshot
from src.models.tournament import Tournament
from src.routers.public_api import (
    get_archetype_detail,
    get_jp_comparison,
    get_meta_history,
    get_meta_snapshot,
    list_tournaments,
)


@pytest.fixture
def mock_session() -> AsyncMock:
    """Create a mock database session."""
    return AsyncMock()


@pytest.fixture
def mock_api_key():
    """Create a mock API key."""
    api_key = MagicMock(spec=ApiKey)
    api_key.id = uuid4()
    api_key.user_id = uuid4()
    api_key.is_active = True
    api_key.monthly_limit = 1000
    api_key.requests_this_month = 50
    return api_key


@pytest.fixture
def mock_meta_snapshot():
    """Create a mock meta snapshot."""
    snapshot = MagicMock(spec=MetaSnapshot)
    snapshot.snapshot_date = date(2024, 1, 15)
    snapshot.format = "standard"
    snapshot.best_of = 3
    snapshot.region = None
    snapshot.archetype_shares = {
        "Charizard ex": 0.15,
        "Gardevoir ex": 0.12,
        "Lugia VSTAR": 0.10,
    }
    snapshot.tier_assignments = {
        "Charizard ex": "S",
        "Gardevoir ex": "S",
    }
    snapshot.trends = {
        "Charizard ex": {"direction": "up", "change": 0.02},
    }
    snapshot.diversity_index = 0.85
    snapshot.sample_size = 1500
    return snapshot


@pytest.fixture
def mock_tournament():
    """Create a mock tournament."""
    tournament = MagicMock(spec=Tournament)
    tournament.id = uuid4()
    tournament.name = "Test Regional"
    tournament.date = date(2024, 1, 20)
    tournament.region = "NA"
    tournament.format = "standard"
    tournament.tier = "major"
    tournament.participant_count = 500
    return tournament


class TestGetMetaSnapshot:
    """Tests for GET /api/v1/public/meta."""

    @pytest.mark.asyncio
    async def test_gets_meta_snapshot(
        self, mock_session, mock_api_key, mock_meta_snapshot
    ):
        """Test getting current meta snapshot."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_meta_snapshot
        mock_session.execute.return_value = mock_result

        response = await get_meta_snapshot(
            mock_session,
            mock_api_key,
            region=None,
            format="standard",
            best_of=3,
        )

        assert response.snapshot_date == "2024-01-15"
        assert len(response.archetypes) == 3
        assert response.archetypes[0].name == "Charizard ex"
        assert response.archetypes[0].share == 0.15

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_data(self, mock_session, mock_api_key):
        """Test returning empty response when no data available."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        response = await get_meta_snapshot(
            mock_session,
            mock_api_key,
            region=None,
            format="standard",
            best_of=3,
        )

        assert response.archetypes == []
        assert response.sample_size == 0

    @pytest.mark.asyncio
    async def test_filters_by_region(
        self, mock_session, mock_api_key, mock_meta_snapshot
    ):
        """Test filtering by region."""
        mock_meta_snapshot.region = "NA"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_meta_snapshot
        mock_session.execute.return_value = mock_result

        response = await get_meta_snapshot(
            mock_session,
            mock_api_key,
            region="NA",
            format="standard",
            best_of=3,
        )

        assert response.region == "NA"

    @pytest.mark.asyncio
    async def test_includes_tier_and_trend(
        self, mock_session, mock_api_key, mock_meta_snapshot
    ):
        """Test that tier and trend data are included."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_meta_snapshot
        mock_session.execute.return_value = mock_result

        response = await get_meta_snapshot(
            mock_session,
            mock_api_key,
            region=None,
            format="standard",
            best_of=3,
        )

        charizard = next(a for a in response.archetypes if a.name == "Charizard ex")
        assert charizard.tier == "S"
        assert charizard.trend == "up"


class TestGetMetaHistory:
    """Tests for GET /api/v1/public/meta/history."""

    @pytest.mark.asyncio
    async def test_gets_meta_history(
        self, mock_session, mock_api_key, mock_meta_snapshot
    ):
        """Test getting meta history."""
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_meta_snapshot]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        response = await get_meta_history(
            mock_session,
            mock_api_key,
            region=None,
            format="standard",
            best_of=3,
            days=7,
        )

        assert response.days == 7
        assert len(response.history) == 1
        assert response.history[0].date == "2024-01-15"

    @pytest.mark.asyncio
    async def test_returns_empty_history(self, mock_session, mock_api_key):
        """Test returning empty history when no data."""
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        response = await get_meta_history(
            mock_session,
            mock_api_key,
            region=None,
            format="standard",
            best_of=3,
            days=30,
        )

        assert response.history == []


class TestGetArchetypeDetail:
    """Tests for GET /api/v1/public/archetypes/{archetype}."""

    @pytest.mark.asyncio
    async def test_gets_archetype_detail(
        self, mock_session, mock_api_key, mock_meta_snapshot
    ):
        """Test getting archetype detail."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_meta_snapshot
        mock_session.execute.return_value = mock_result

        response = await get_archetype_detail(
            mock_session,
            mock_api_key,
            archetype="Charizard ex",
            region=None,
            format="standard",
            best_of=3,
        )

        assert response.name == "Charizard ex"
        assert response.share == 0.15
        assert response.tier == "S"
        assert response.rank == 1

    @pytest.mark.asyncio
    async def test_returns_zero_share_for_unknown(
        self, mock_session, mock_api_key, mock_meta_snapshot
    ):
        """Test returning zero share for unknown archetype."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_meta_snapshot
        mock_session.execute.return_value = mock_result

        response = await get_archetype_detail(
            mock_session,
            mock_api_key,
            archetype="Unknown Deck",
            region=None,
            format="standard",
            best_of=3,
        )

        assert response.share == 0
        assert response.rank is None

    @pytest.mark.asyncio
    async def test_returns_zero_when_no_snapshot(self, mock_session, mock_api_key):
        """Test returning zero share when no snapshot available."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        response = await get_archetype_detail(
            mock_session,
            mock_api_key,
            archetype="Charizard ex",
            region=None,
            format="standard",
            best_of=3,
        )

        assert response.share == 0

    @pytest.mark.asyncio
    async def test_calculates_rank_correctly(
        self, mock_session, mock_api_key, mock_meta_snapshot
    ):
        """Test that rank is calculated correctly."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_meta_snapshot
        mock_session.execute.return_value = mock_result

        response = await get_archetype_detail(
            mock_session,
            mock_api_key,
            archetype="Gardevoir ex",
            region=None,
            format="standard",
            best_of=3,
        )

        assert response.rank == 2


class TestListTournaments:
    """Tests for GET /api/v1/public/tournaments."""

    @pytest.mark.asyncio
    async def test_lists_tournaments(self, mock_session, mock_api_key, mock_tournament):
        """Test listing tournaments."""
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_tournament]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        response = await list_tournaments(
            mock_session,
            mock_api_key,
            region=None,
            format=None,
            limit=20,
            offset=0,
        )

        assert response.total == 1
        assert response.items[0].name == "Test Regional"
        assert response.items[0].participant_count == 500

    @pytest.mark.asyncio
    async def test_filters_by_region(self, mock_session, mock_api_key, mock_tournament):
        """Test filtering tournaments by region."""
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_tournament]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        response = await list_tournaments(
            mock_session,
            mock_api_key,
            region="NA",
            format=None,
            limit=20,
            offset=0,
        )

        assert response.total == 1

    @pytest.mark.asyncio
    async def test_filters_by_format(self, mock_session, mock_api_key, mock_tournament):
        """Test filtering tournaments by format."""
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_tournament]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        response = await list_tournaments(
            mock_session,
            mock_api_key,
            region=None,
            format="standard",
            limit=20,
            offset=0,
        )

        assert response.total == 1

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_tournaments(self, mock_session, mock_api_key):
        """Test returning empty list when no tournaments."""
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        response = await list_tournaments(
            mock_session,
            mock_api_key,
            region=None,
            format=None,
            limit=20,
            offset=0,
        )

        assert response.total == 0
        assert response.items == []


class TestJPComparison:
    """Tests for GET /api/v1/public/japan/comparison."""

    @pytest.mark.asyncio
    async def test_gets_jp_comparison(self, mock_session, mock_api_key):
        """Test getting JP vs EN comparison."""
        jp_snapshot = MagicMock(spec=MetaSnapshot)
        jp_snapshot.snapshot_date = date(2024, 1, 15)
        jp_snapshot.archetype_shares = {
            "Charizard ex": 0.20,
            "Gardevoir ex": 0.08,
        }

        en_snapshot = MagicMock(spec=MetaSnapshot)
        en_snapshot.snapshot_date = date(2024, 1, 15)
        en_snapshot.archetype_shares = {
            "Charizard ex": 0.15,
            "Gardevoir ex": 0.12,
        }

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.side_effect = [jp_snapshot, en_snapshot]
        mock_session.execute.return_value = mock_result

        response = await get_jp_comparison(
            mock_session,
            mock_api_key,
            format="standard",
            top_n=10,
        )

        assert response.jp_date == "2024-01-15"
        assert response.en_date == "2024-01-15"
        assert len(response.comparisons) > 0

    @pytest.mark.asyncio
    async def test_handles_missing_jp_data(self, mock_session, mock_api_key):
        """Test handling when JP data is missing."""
        en_snapshot = MagicMock(spec=MetaSnapshot)
        en_snapshot.snapshot_date = date(2024, 1, 15)
        en_snapshot.archetype_shares = {
            "Charizard ex": 0.15,
        }

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.side_effect = [None, en_snapshot]
        mock_session.execute.return_value = mock_result

        response = await get_jp_comparison(
            mock_session,
            mock_api_key,
            format="standard",
            top_n=10,
        )

        assert response.jp_date is None
        assert response.en_date == "2024-01-15"

    @pytest.mark.asyncio
    async def test_handles_missing_en_data(self, mock_session, mock_api_key):
        """Test handling when EN data is missing."""
        jp_snapshot = MagicMock(spec=MetaSnapshot)
        jp_snapshot.snapshot_date = date(2024, 1, 15)
        jp_snapshot.archetype_shares = {
            "Charizard ex": 0.20,
        }

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.side_effect = [jp_snapshot, None]
        mock_session.execute.return_value = mock_result

        response = await get_jp_comparison(
            mock_session,
            mock_api_key,
            format="standard",
            top_n=10,
        )

        assert response.jp_date == "2024-01-15"
        assert response.en_date is None

    @pytest.mark.asyncio
    async def test_handles_both_missing(self, mock_session, mock_api_key):
        """Test handling when both datasets are missing."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.side_effect = [None, None]
        mock_session.execute.return_value = mock_result

        response = await get_jp_comparison(
            mock_session,
            mock_api_key,
            format="standard",
            top_n=10,
        )

        assert response.jp_date is None
        assert response.en_date is None
        assert response.comparisons == []

    @pytest.mark.asyncio
    async def test_respects_top_n(self, mock_session, mock_api_key):
        """Test respecting top_n parameter."""
        jp_snapshot = MagicMock(spec=MetaSnapshot)
        jp_snapshot.snapshot_date = date(2024, 1, 15)
        jp_snapshot.archetype_shares = {
            f"Archetype {i}": 0.10 - i * 0.01 for i in range(10)
        }

        en_snapshot = MagicMock(spec=MetaSnapshot)
        en_snapshot.snapshot_date = date(2024, 1, 15)
        en_snapshot.archetype_shares = {
            f"Archetype {i}": 0.10 - i * 0.01 for i in range(10)
        }

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.side_effect = [jp_snapshot, en_snapshot]
        mock_session.execute.return_value = mock_result

        response = await get_jp_comparison(
            mock_session,
            mock_api_key,
            format="standard",
            top_n=5,
        )

        assert len(response.comparisons) == 5
