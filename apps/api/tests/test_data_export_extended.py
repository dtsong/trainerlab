"""Extended tests for DataExportService."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.meta_snapshot import MetaSnapshot
from src.models.tournament import Tournament
from src.services.data_export_service import DataExportService


@pytest.fixture
def mock_session() -> AsyncMock:
    """Create a mock database session."""
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.fixture
def mock_storage():
    """Create a mock storage service."""
    return MagicMock()


class TestFetchMetaHistory:
    """Tests for _fetch_meta_history covering lines 258-292."""

    @pytest.mark.asyncio
    async def test_fetches_meta_history_with_region(
        self, mock_session: AsyncMock, mock_storage
    ) -> None:
        """Should fetch meta history data with a specific region."""
        snapshot = MagicMock(spec=MetaSnapshot)
        snapshot.snapshot_date = date(2026, 1, 15)
        snapshot.format = "standard"
        snapshot.best_of = 3
        snapshot.region = "NA"
        snapshot.archetype_shares = {
            "Charizard ex": 0.15,
            "Gardevoir ex": 0.10,
        }

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [snapshot]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        service = DataExportService(mock_session, mock_storage)
        data = await service._fetch_meta_history({"region": "NA", "days": 7})

        assert len(data) == 2
        assert data[0]["region"] == "NA"
        assert data[0]["date"] == "2026-01-15"
        assert data[0]["format"] == "standard"

    @pytest.mark.asyncio
    async def test_fetches_meta_history_global(
        self, mock_session: AsyncMock, mock_storage
    ) -> None:
        """Should fetch global meta history when region is None."""
        snapshot = MagicMock(spec=MetaSnapshot)
        snapshot.snapshot_date = date(2026, 1, 10)
        snapshot.archetype_shares = {"Lugia VSTAR": 0.08}

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [snapshot]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        service = DataExportService(mock_session, mock_storage)
        data = await service._fetch_meta_history({"region": None})

        assert len(data) == 1
        assert data[0]["region"] == "Global"

    @pytest.mark.asyncio
    async def test_fetches_meta_history_empty(
        self, mock_session: AsyncMock, mock_storage
    ) -> None:
        """Should return empty list when no snapshots."""
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        service = DataExportService(mock_session, mock_storage)
        data = await service._fetch_meta_history({})

        assert data == []


class TestFetchJpData:
    """Tests for _fetch_jp_data covering lines 336-364."""

    @pytest.mark.asyncio
    async def test_fetches_jp_data(self, mock_session: AsyncMock, mock_storage) -> None:
        """Should fetch JP meta data with BO1 filter."""
        snapshot = MagicMock(spec=MetaSnapshot)
        snapshot.snapshot_date = date(2026, 1, 20)
        snapshot.archetype_shares = {
            "リザードンex": 0.18,
            "サーナイトex": 0.14,
        }
        snapshot.tier_assignments = {"リザードンex": "S", "サーナイトex": "A"}

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [snapshot]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        service = DataExportService(mock_session, mock_storage)
        data = await service._fetch_jp_data({"days": 14})

        assert len(data) == 2
        assert data[0]["archetype"] in ("リザードンex", "サーナイトex")
        assert data[0]["date"] == "2026-01-20"
        # Verify tier_assignments lookup
        tiers = {d["archetype"]: d["tier"] for d in data}
        assert tiers["リザードンex"] == "S"
        assert tiers["サーナイトex"] == "A"

    @pytest.mark.asyncio
    async def test_fetches_jp_data_no_tier_assignments(
        self, mock_session: AsyncMock, mock_storage
    ) -> None:
        """Should handle None tier_assignments gracefully."""
        snapshot = MagicMock(spec=MetaSnapshot)
        snapshot.snapshot_date = date(2026, 1, 20)
        snapshot.archetype_shares = {"DeckA": 0.10}
        snapshot.tier_assignments = None

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [snapshot]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        service = DataExportService(mock_session, mock_storage)
        data = await service._fetch_jp_data({})

        assert len(data) == 1
        assert data[0]["tier"] is None


class TestFetchExportDataRouting:
    """Tests for _fetch_export_data routing."""

    @pytest.mark.asyncio
    async def test_routes_to_meta_history(
        self, mock_session: AsyncMock, mock_storage
    ) -> None:
        """Should route meta_history to _fetch_meta_history."""
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        service = DataExportService(mock_session, mock_storage)
        data = await service._fetch_export_data("meta_history", {})
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_routes_to_jp_data(
        self, mock_session: AsyncMock, mock_storage
    ) -> None:
        """Should route jp_data to _fetch_jp_data."""
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        service = DataExportService(mock_session, mock_storage)
        data = await service._fetch_export_data("jp_data", {})
        assert isinstance(data, list)


class TestGenerateContentXlsx:
    """Tests for _generate_content xlsx edge cases."""

    @pytest.mark.asyncio
    async def test_empty_xlsx(self, mock_session: AsyncMock, mock_storage) -> None:
        """Should generate empty xlsx for empty data (lines 378-379)."""
        service = DataExportService(mock_session, mock_storage)
        content, columns = await service._generate_content([], "xlsx")

        assert isinstance(content, bytes)
        assert len(content) > 0
        assert columns == []

    @pytest.mark.asyncio
    async def test_unknown_format_raises(
        self, mock_session: AsyncMock, mock_storage
    ) -> None:
        """Should raise ValueError for unknown format (line 400)."""
        service = DataExportService(mock_session, mock_storage)

        with pytest.raises(ValueError, match="Unknown format"):
            await service._generate_content([{"a": 1}], "parquet")


class TestFetchTournamentResultsExtended:
    """Extended tests for _fetch_tournament_results covering filter branches."""

    @pytest.mark.asyncio
    async def test_with_region_and_format_filters(
        self, mock_session: AsyncMock, mock_storage
    ) -> None:
        """Should apply region and format filters (lines 306, 308)."""
        mock_tournament = MagicMock(spec=Tournament)
        mock_tournament.id = "t1"
        mock_tournament.name = "Filtered Tournament"
        mock_tournament.date = date(2026, 1, 15)
        mock_tournament.region = "EU"
        mock_tournament.format = "expanded"
        mock_tournament.tier = "regional"
        mock_tournament.participant_count = 200

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_tournament]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        service = DataExportService(mock_session, mock_storage)
        data = await service._fetch_tournament_results(
            {"region": "EU", "format": "expanded", "limit": 50}
        )

        assert len(data) == 1
        assert data[0]["region"] == "EU"
        assert data[0]["format"] == "expanded"

    @pytest.mark.asyncio
    async def test_tournament_with_none_date(
        self, mock_session: AsyncMock, mock_storage
    ) -> None:
        """Should handle tournament with None date."""
        mock_tournament = MagicMock(spec=Tournament)
        mock_tournament.id = "t2"
        mock_tournament.name = "TBD Tournament"
        mock_tournament.date = None
        mock_tournament.region = "NA"
        mock_tournament.format = "standard"
        mock_tournament.tier = "league"
        mock_tournament.participant_count = 32

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_tournament]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        service = DataExportService(mock_session, mock_storage)
        data = await service._fetch_tournament_results({})

        assert data[0]["date"] is None


class TestFetchMetaSnapshotExtended:
    """Extended tests for _fetch_meta_snapshot covering region filter branch."""

    @pytest.mark.asyncio
    async def test_with_region_filter(
        self, mock_session: AsyncMock, mock_storage
    ) -> None:
        """Should filter by region when specified (line 221)."""
        snapshot = MagicMock(spec=MetaSnapshot)
        snapshot.snapshot_date = date(2026, 1, 15)
        snapshot.archetype_shares = {"Charizard ex": 0.12}
        snapshot.tier_assignments = {"Charizard ex": "A"}
        snapshot.trends = {"Charizard ex": {"direction": "down", "change": -0.01}}

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = snapshot
        mock_session.execute.return_value = mock_result

        service = DataExportService(mock_session, mock_storage)
        data = await service._fetch_meta_snapshot({"region": "EU"})

        assert len(data) == 1
        assert data[0]["region"] == "EU"
        assert data[0]["trend"] == "down"
        assert data[0]["trend_change"] == -0.01
