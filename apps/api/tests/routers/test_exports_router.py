"""Tests for exports router."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.models.data_export import DataExport
from src.models.user import User
from src.routers.exports import (
    create_export,
    get_download_url,
    get_export,
    list_exports,
)
from src.schemas.export import ExportCreate


@pytest.fixture
def mock_session() -> AsyncMock:
    """Create a mock database session."""
    return AsyncMock()


@pytest.fixture
def mock_creator_user():
    """Create a mock creator user."""
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.email = "creator@example.com"
    user.is_creator = True
    return user


@pytest.fixture
def mock_export(mock_creator_user):
    """Create a mock export."""
    export = MagicMock(spec=DataExport)
    export.id = uuid4()
    export.user_id = mock_creator_user.id
    export.export_type = "meta_snapshot"
    export.config = {"region": None}
    export.format = "json"
    export.status = "completed"
    export.file_path = "https://storage.example.com/exports/test.json"
    export.file_size_bytes = 1024
    export.expires_at = datetime.now(UTC) + timedelta(hours=12)
    export.error_message = None
    export.created_at = datetime.now(UTC)
    export.updated_at = datetime.now(UTC)
    return export


class TestCreateExport:
    """Tests for POST /api/v1/exports."""

    @pytest.mark.asyncio
    async def test_creates_export_successfully(
        self, mock_session, mock_creator_user, mock_export
    ):
        """Test creating export successfully."""
        export_data = ExportCreate(
            export_type="meta_snapshot",
            config={"region": None},
            format="json",
        )

        with patch("src.routers.exports.DataExportService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.create_export = AsyncMock(return_value=mock_export)
            mock_service_class.return_value = mock_service

            response = await create_export(mock_session, mock_creator_user, export_data)

        assert response.export_type == "meta_snapshot"
        assert response.status == "completed"
        mock_service.create_export.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_400_for_invalid_export_type(
        self, mock_session, mock_creator_user
    ):
        """Test returning 400 for invalid export type."""
        from fastapi import HTTPException

        export_data = ExportCreate(
            export_type="meta_snapshot",
            config={},
            format="json",
        )

        with patch("src.routers.exports.DataExportService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.create_export = AsyncMock(
                side_effect=ValueError("Invalid export type")
            )
            mock_service_class.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                await create_export(mock_session, mock_creator_user, export_data)

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_returns_500_on_unexpected_error(
        self, mock_session, mock_creator_user
    ):
        """Test returning 500 on unexpected error."""
        from fastapi import HTTPException

        export_data = ExportCreate(
            export_type="meta_snapshot",
            config={},
            format="json",
        )

        with patch("src.routers.exports.DataExportService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.create_export = AsyncMock(
                side_effect=Exception("Unexpected error")
            )
            mock_service_class.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                await create_export(mock_session, mock_creator_user, export_data)

        assert exc_info.value.status_code == 500


class TestListExports:
    """Tests for GET /api/v1/exports."""

    @pytest.mark.asyncio
    async def test_lists_exports(self, mock_session, mock_creator_user, mock_export):
        """Test listing exports."""
        with patch("src.routers.exports.DataExportService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.list_user_exports = AsyncMock(return_value=[mock_export])
            mock_service_class.return_value = mock_service

            response = await list_exports(mock_session, mock_creator_user, limit=20)

        assert response.total == 1
        assert len(response.items) == 1

    @pytest.mark.asyncio
    async def test_respects_limit_parameter(
        self, mock_session, mock_creator_user, mock_export
    ):
        """Test respecting limit parameter."""
        with patch("src.routers.exports.DataExportService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.list_user_exports = AsyncMock(return_value=[mock_export])
            mock_service_class.return_value = mock_service

            await list_exports(mock_session, mock_creator_user, limit=10)

            mock_service.list_user_exports.assert_called_once_with(
                mock_creator_user, limit=10
            )


class TestGetExport:
    """Tests for GET /api/v1/exports/{export_id}."""

    @pytest.mark.asyncio
    async def test_gets_export(self, mock_session, mock_creator_user, mock_export):
        """Test getting a specific export."""
        with patch("src.routers.exports.DataExportService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_export = AsyncMock(return_value=mock_export)
            mock_service_class.return_value = mock_service

            response = await get_export(mock_session, mock_creator_user, mock_export.id)

        assert response.id == mock_export.id

    @pytest.mark.asyncio
    async def test_returns_404_when_not_found(self, mock_session, mock_creator_user):
        """Test returning 404 when export not found."""
        from fastapi import HTTPException

        with patch("src.routers.exports.DataExportService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_export = AsyncMock(return_value=None)
            mock_service_class.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                await get_export(mock_session, mock_creator_user, uuid4())

        assert exc_info.value.status_code == 404


class TestGetDownloadUrl:
    """Tests for GET /api/v1/exports/{export_id}/download."""

    @pytest.mark.asyncio
    async def test_gets_download_url(
        self, mock_session, mock_creator_user, mock_export
    ):
        """Test getting download URL for an export."""
        with patch("src.routers.exports.DataExportService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.generate_download_url = AsyncMock(
                return_value="https://signed-url.example.com"
            )
            mock_service_class.return_value = mock_service

            response = await get_download_url(
                mock_session, mock_creator_user, mock_export.id
            )

        assert response.download_url == "https://signed-url.example.com"
        assert response.expires_in_hours == 24

    @pytest.mark.asyncio
    async def test_returns_404_when_not_found_or_expired(
        self, mock_session, mock_creator_user
    ):
        """Test returning 404 when export not found or expired."""
        from fastapi import HTTPException

        with patch("src.routers.exports.DataExportService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.generate_download_url = AsyncMock(return_value=None)
            mock_service_class.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                await get_download_url(mock_session, mock_creator_user, uuid4())

        assert exc_info.value.status_code == 404
