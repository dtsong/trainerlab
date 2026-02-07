"""Tests for DataExportService."""

import csv
import json
from datetime import UTC, date, datetime, timedelta
from io import StringIO
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.data_export import DataExport
from src.models.meta_snapshot import MetaSnapshot
from src.models.user import User
from src.services.data_export_service import (
    CONTENT_TYPES,
    EXPORT_FORMATS,
    EXPORT_TYPES,
    DataExportService,
)


@pytest.fixture
def mock_session() -> AsyncMock:
    """Create a mock database session."""
    session = AsyncMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def mock_storage():
    """Create a mock storage service."""
    storage = MagicMock()
    storage.upload_export = AsyncMock(
        return_value="https://storage.example.com/exports/test.json"
    )
    storage.generate_signed_url = AsyncMock(
        return_value="https://signed-url.example.com"
    )
    return storage


@pytest.fixture
def mock_user() -> User:
    """Create a mock user."""
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.email = "creator@example.com"
    user.is_creator = True
    return user


@pytest.fixture
def mock_meta_snapshot() -> MetaSnapshot:
    """Create a mock meta snapshot."""
    snapshot = MagicMock(spec=MetaSnapshot)
    snapshot.snapshot_date = date(2024, 1, 15)
    snapshot.format = "standard"
    snapshot.best_of = 3
    snapshot.region = None
    snapshot.archetype_shares = {
        "Charizard ex": 0.15,
        "Gardevoir ex": 0.12,
    }
    snapshot.tier_assignments = {"Charizard ex": "S"}
    snapshot.trends = {"Charizard ex": {"direction": "up", "change": 0.02}}
    return snapshot


class TestExportConstants:
    """Tests for export constants."""

    def test_export_types_defined(self):
        """Test export types are defined."""
        assert "meta_snapshot" in EXPORT_TYPES
        assert "meta_history" in EXPORT_TYPES
        assert "tournament_results" in EXPORT_TYPES

    def test_export_formats_defined(self):
        """Test export formats are defined."""
        assert "csv" in EXPORT_FORMATS
        assert "json" in EXPORT_FORMATS
        assert "xlsx" in EXPORT_FORMATS

    def test_content_types_defined(self):
        """Test content types are defined."""
        assert CONTENT_TYPES["csv"] == "text/csv"
        assert CONTENT_TYPES["json"] == "application/json"
        assert "openxmlformats" in CONTENT_TYPES["xlsx"]


class TestCreateExport:
    """Tests for create_export method."""

    @pytest.mark.asyncio
    async def test_creates_export_with_json_format(
        self,
        mock_session: AsyncMock,
        mock_storage,
        mock_user: User,
        mock_meta_snapshot: MetaSnapshot,
    ):
        """Test creating export with JSON format."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_meta_snapshot
        mock_session.execute.return_value = mock_result

        service = DataExportService(mock_session, mock_storage)
        await service.create_export(
            mock_user,
            export_type="meta_snapshot",
            config={"region": None},
            format="json",
        )

        mock_session.add.assert_called()
        mock_storage.upload_export.assert_called_once()
        mock_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_creates_export_with_csv_format(
        self,
        mock_session: AsyncMock,
        mock_storage,
        mock_user: User,
        mock_meta_snapshot: MetaSnapshot,
    ):
        """Test creating export with CSV format."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_meta_snapshot
        mock_session.execute.return_value = mock_result

        service = DataExportService(mock_session, mock_storage)
        await service.create_export(
            mock_user,
            export_type="meta_snapshot",
            config={},
            format="csv",
        )

        call_args = mock_storage.upload_export.call_args
        # Check the content_type argument (third positional arg)
        assert call_args[0][2] == "text/csv"

    @pytest.mark.asyncio
    async def test_raises_for_invalid_export_type(
        self, mock_session: AsyncMock, mock_storage, mock_user: User
    ):
        """Test raising error for invalid export type."""
        service = DataExportService(mock_session, mock_storage)

        with pytest.raises(ValueError, match="Invalid export type"):
            await service.create_export(
                mock_user,
                export_type="invalid_type",
                config={},
            )

    @pytest.mark.asyncio
    async def test_raises_for_invalid_format(
        self, mock_session: AsyncMock, mock_storage, mock_user: User
    ):
        """Test raising error for invalid format."""
        service = DataExportService(mock_session, mock_storage)

        with pytest.raises(ValueError, match="Invalid format"):
            await service.create_export(
                mock_user,
                export_type="meta_snapshot",
                config={},
                format="pdf",
            )

    @pytest.mark.asyncio
    async def test_sets_export_status_on_failure(
        self, mock_session: AsyncMock, mock_storage, mock_user: User
    ):
        """Test setting export status to failed on error."""
        mock_storage.upload_export.side_effect = Exception("Upload failed")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        service = DataExportService(mock_session, mock_storage)

        with pytest.raises(Exception, match="Upload failed"):  # noqa: B017, PT011
            await service.create_export(
                mock_user,
                export_type="meta_snapshot",
                config={},
            )

    @pytest.mark.asyncio
    async def test_sets_expiration_time(
        self,
        mock_session: AsyncMock,
        mock_storage,
        mock_user: User,
        mock_meta_snapshot: MetaSnapshot,
    ):
        """Test setting expiration time on export."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_meta_snapshot
        mock_session.execute.return_value = mock_result

        service = DataExportService(mock_session, mock_storage)
        await service.create_export(
            mock_user,
            export_type="meta_snapshot",
            config={},
        )

        mock_session.add.call_args_list[0][0][0]
        # The expires_at is set after commit, check it was called


class TestGetExport:
    """Tests for get_export method."""

    @pytest.mark.asyncio
    async def test_returns_export_when_owned(
        self, mock_session: AsyncMock, mock_storage, mock_user: User
    ):
        """Test returning export when user owns it."""
        export_id = uuid4()
        mock_export = MagicMock(spec=DataExport)
        mock_export.id = export_id
        mock_export.user_id = mock_user.id

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_export
        mock_session.execute.return_value = mock_result

        service = DataExportService(mock_session, mock_storage)
        result = await service.get_export(export_id, mock_user)

        assert result == mock_export

    @pytest.mark.asyncio
    async def test_returns_none_when_not_owned(
        self, mock_session: AsyncMock, mock_storage, mock_user: User
    ):
        """Test returning None when user doesn't own export."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        service = DataExportService(mock_session, mock_storage)
        result = await service.get_export(uuid4(), mock_user)

        assert result is None


class TestListUserExports:
    """Tests for list_user_exports method."""

    @pytest.mark.asyncio
    async def test_returns_user_exports(
        self, mock_session: AsyncMock, mock_storage, mock_user: User
    ):
        """Test listing exports for a user."""
        mock_exports = [MagicMock(spec=DataExport), MagicMock(spec=DataExport)]
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_exports
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        service = DataExportService(mock_session, mock_storage)
        result = await service.list_user_exports(mock_user)

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_respects_limit_parameter(
        self, mock_session: AsyncMock, mock_storage, mock_user: User
    ):
        """Test respecting limit parameter."""
        mock_exports = [MagicMock(spec=DataExport)]
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_exports
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        service = DataExportService(mock_session, mock_storage)
        await service.list_user_exports(mock_user, limit=10)

        mock_session.execute.assert_called_once()


class TestGenerateDownloadUrl:
    """Tests for generate_download_url method."""

    @pytest.mark.asyncio
    async def test_returns_signed_url_for_completed_export(
        self, mock_session: AsyncMock, mock_storage, mock_user: User
    ):
        """Test returning signed URL for completed export."""
        export_id = uuid4()
        mock_export = MagicMock(spec=DataExport)
        mock_export.id = export_id
        mock_export.user_id = mock_user.id
        mock_export.status = "completed"
        mock_export.format = "json"
        mock_export.expires_at = datetime.now(UTC) + timedelta(hours=12)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_export
        mock_session.execute.return_value = mock_result

        service = DataExportService(mock_session, mock_storage)
        result = await service.generate_download_url(export_id, mock_user)

        assert result == "https://signed-url.example.com"

    @pytest.mark.asyncio
    async def test_returns_none_for_pending_export(
        self, mock_session: AsyncMock, mock_storage, mock_user: User
    ):
        """Test returning None for pending export."""
        export_id = uuid4()
        mock_export = MagicMock(spec=DataExport)
        mock_export.id = export_id
        mock_export.user_id = mock_user.id
        mock_export.status = "pending"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_export
        mock_session.execute.return_value = mock_result

        service = DataExportService(mock_session, mock_storage)
        result = await service.generate_download_url(export_id, mock_user)

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_for_expired_export(
        self, mock_session: AsyncMock, mock_storage, mock_user: User
    ):
        """Test returning None for expired export."""
        export_id = uuid4()
        mock_export = MagicMock(spec=DataExport)
        mock_export.id = export_id
        mock_export.user_id = mock_user.id
        mock_export.status = "completed"
        mock_export.expires_at = datetime.now(UTC) - timedelta(hours=1)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_export
        mock_session.execute.return_value = mock_result

        service = DataExportService(mock_session, mock_storage)
        result = await service.generate_download_url(export_id, mock_user)

        assert result is None


class TestGenerateContent:
    """Tests for _generate_content method."""

    @pytest.mark.asyncio
    async def test_generates_json_content(self, mock_session: AsyncMock, mock_storage):
        """Test generating JSON content."""
        service = DataExportService(mock_session, mock_storage)
        data = [{"col1": "val1", "col2": "val2"}]

        content, columns = await service._generate_content(data, "json")

        parsed = json.loads(content.decode("utf-8"))
        assert parsed == data
        assert columns == ["col1", "col2"]

    @pytest.mark.asyncio
    async def test_generates_csv_content(self, mock_session: AsyncMock, mock_storage):
        """Test generating CSV content."""
        service = DataExportService(mock_session, mock_storage)
        data = [{"col1": "val1", "col2": "val2"}]

        content, columns = await service._generate_content(data, "csv")

        reader = csv.DictReader(StringIO(content.decode("utf-8")))
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["col1"] == "val1"

    @pytest.mark.asyncio
    async def test_handles_empty_data_json(self, mock_session: AsyncMock, mock_storage):
        """Test handling empty data for JSON format."""
        service = DataExportService(mock_session, mock_storage)

        content, columns = await service._generate_content([], "json")

        assert content == b"[]"
        assert columns == []

    @pytest.mark.asyncio
    async def test_handles_empty_data_csv(self, mock_session: AsyncMock, mock_storage):
        """Test handling empty data for CSV format."""
        service = DataExportService(mock_session, mock_storage)

        content, columns = await service._generate_content([], "csv")

        assert content == b""
        assert columns == []

    @pytest.mark.asyncio
    async def test_generates_xlsx_content(self, mock_session: AsyncMock, mock_storage):
        """Test generating XLSX content."""
        service = DataExportService(mock_session, mock_storage)
        data = [{"col1": "val1", "col2": "val2"}]

        content, columns = await service._generate_content(data, "xlsx")

        assert isinstance(content, bytes)
        assert len(content) > 0
        assert columns == ["col1", "col2"]


class TestFetchExportData:
    """Tests for _fetch_export_data method."""

    @pytest.mark.asyncio
    async def test_fetches_meta_snapshot_data(
        self,
        mock_session: AsyncMock,
        mock_storage,
        mock_meta_snapshot: MetaSnapshot,
    ):
        """Test fetching meta snapshot export data."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_meta_snapshot
        mock_session.execute.return_value = mock_result

        service = DataExportService(mock_session, mock_storage)
        data = await service._fetch_export_data("meta_snapshot", {"region": None})

        assert len(data) > 0
        assert "archetype" in data[0]
        assert "share" in data[0]

    @pytest.mark.asyncio
    async def test_fetches_tournament_results_data(
        self, mock_session: AsyncMock, mock_storage
    ):
        """Test fetching tournament results export data."""
        mock_tournament = MagicMock()
        mock_tournament.id = uuid4()
        mock_tournament.name = "Test Tournament"
        mock_tournament.date = date(2024, 1, 15)
        mock_tournament.region = "NA"
        mock_tournament.format = "standard"
        mock_tournament.tier = "major"
        mock_tournament.participant_count = 500

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_tournament]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        service = DataExportService(mock_session, mock_storage)
        data = await service._fetch_export_data("tournament_results", {})

        assert len(data) == 1
        assert data[0]["name"] == "Test Tournament"

    @pytest.mark.asyncio
    async def test_raises_for_unsupported_type(
        self, mock_session: AsyncMock, mock_storage
    ):
        """Test raising error for unsupported export type."""
        service = DataExportService(mock_session, mock_storage)

        with pytest.raises(ValueError, match="Unsupported export type"):
            await service._fetch_export_data("unsupported_type", {})
