"""Tests for widgets router."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.models.user import User
from src.models.widget import Widget
from src.routers.widgets import (
    create_widget,
    delete_widget,
    get_embed_code,
    get_widget,
    list_widgets,
    update_widget,
)
from src.schemas.pagination import PaginatedResponse
from src.schemas.widget import WidgetCreate, WidgetUpdate


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
def mock_widget(mock_creator_user):
    """Create a mock widget."""
    widget = MagicMock(spec=Widget)
    widget.id = "w_abc123"
    widget.user_id = str(mock_creator_user.id)
    widget.type = "meta_snapshot"
    widget.config = {"region": None}
    widget.theme = "dark"
    widget.accent_color = None
    widget.show_attribution = True
    widget.embed_count = 0
    widget.view_count = 10
    widget.is_active = True
    widget.created_at = datetime.now(UTC)
    widget.updated_at = datetime.now(UTC)
    return widget


class TestCreateWidget:
    """Tests for POST /api/v1/widgets."""

    @pytest.mark.asyncio
    async def test_creates_widget_successfully(
        self, mock_session, mock_creator_user, mock_widget
    ):
        """Test creating widget successfully."""
        widget_data = WidgetCreate(
            type="meta_snapshot",
            config={"region": None},
            theme="dark",
        )

        with patch("src.routers.widgets.WidgetService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.create_widget = AsyncMock(return_value=mock_widget)
            mock_service_class.return_value = mock_service

            response = await create_widget(mock_session, mock_creator_user, widget_data)

        assert response.id == "w_abc123"
        mock_service.create_widget.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_400_for_invalid_config(
        self, mock_session, mock_creator_user
    ):
        """Test returning 400 for invalid config."""
        from fastapi import HTTPException

        widget_data = WidgetCreate(type="meta_snapshot", config={"invalid": "config"})

        with patch("src.routers.widgets.WidgetService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.create_widget = AsyncMock(
                side_effect=ValueError("Invalid widget configuration")
            )
            mock_service_class.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                await create_widget(mock_session, mock_creator_user, widget_data)

        assert exc_info.value.status_code == 400


class TestListWidgets:
    """Tests for GET /api/v1/widgets."""

    @pytest.mark.asyncio
    async def test_lists_widgets(self, mock_session, mock_creator_user, mock_widget):
        """Test listing widgets."""
        paginated = PaginatedResponse(
            items=[mock_widget],
            total=1,
            page=1,
            limit=20,
            has_next=False,
            has_prev=False,
        )

        with patch("src.routers.widgets.WidgetService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.list_user_widgets = AsyncMock(return_value=paginated)
            mock_service_class.return_value = mock_service

            response = await list_widgets(
                mock_session, mock_creator_user, page=1, limit=20
            )

        assert response.total == 1
        assert len(response.items) == 1


class TestGetWidget:
    """Tests for GET /api/v1/widgets/{widget_id}."""

    @pytest.mark.asyncio
    async def test_gets_widget(self, mock_session, mock_creator_user, mock_widget):
        """Test getting a specific widget."""
        with patch("src.routers.widgets.WidgetService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_widget_for_owner = AsyncMock(return_value=mock_widget)
            mock_service_class.return_value = mock_service

            response = await get_widget(mock_session, mock_creator_user, "w_abc123")

        assert response.id == "w_abc123"

    @pytest.mark.asyncio
    async def test_returns_404_when_not_found(self, mock_session, mock_creator_user):
        """Test returning 404 when widget not found."""
        from fastapi import HTTPException

        with patch("src.routers.widgets.WidgetService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_widget_for_owner = AsyncMock(return_value=None)
            mock_service_class.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                await get_widget(mock_session, mock_creator_user, "w_notfound")

        assert exc_info.value.status_code == 404


class TestUpdateWidget:
    """Tests for PATCH /api/v1/widgets/{widget_id}."""

    @pytest.mark.asyncio
    async def test_updates_widget(self, mock_session, mock_creator_user, mock_widget):
        """Test updating a widget."""
        widget_update = WidgetUpdate(theme="light")

        with patch("src.routers.widgets.WidgetService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.update_widget = AsyncMock(return_value=mock_widget)
            mock_service_class.return_value = mock_service

            response = await update_widget(
                mock_session, mock_creator_user, "w_abc123", widget_update
            )

        assert response.id == "w_abc123"

    @pytest.mark.asyncio
    async def test_returns_404_when_not_found(self, mock_session, mock_creator_user):
        """Test returning 404 when widget not found."""
        from fastapi import HTTPException

        widget_update = WidgetUpdate(theme="light")

        with patch("src.routers.widgets.WidgetService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.update_widget = AsyncMock(return_value=None)
            mock_service_class.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                await update_widget(
                    mock_session, mock_creator_user, "w_notfound", widget_update
                )

        assert exc_info.value.status_code == 404


class TestDeleteWidget:
    """Tests for DELETE /api/v1/widgets/{widget_id}."""

    @pytest.mark.asyncio
    async def test_deletes_widget(self, mock_session, mock_creator_user):
        """Test deleting a widget."""
        with patch("src.routers.widgets.WidgetService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.delete_widget = AsyncMock(return_value=True)
            mock_service_class.return_value = mock_service

            # Should not raise
            await delete_widget(mock_session, mock_creator_user, "w_abc123")

    @pytest.mark.asyncio
    async def test_returns_404_when_not_found(self, mock_session, mock_creator_user):
        """Test returning 404 when widget not found."""
        from fastapi import HTTPException

        with patch("src.routers.widgets.WidgetService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.delete_widget = AsyncMock(return_value=False)
            mock_service_class.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                await delete_widget(mock_session, mock_creator_user, "w_notfound")

        assert exc_info.value.status_code == 404


class TestGetEmbedCode:
    """Tests for GET /api/v1/widgets/{widget_id}/embed-code."""

    @pytest.mark.asyncio
    async def test_gets_embed_code(self, mock_session, mock_creator_user, mock_widget):
        """Test getting embed code for a widget."""
        with patch("src.routers.widgets.WidgetService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_widget_for_owner = AsyncMock(return_value=mock_widget)
            mock_service.generate_embed_code = MagicMock(
                side_effect=["<iframe></iframe>", "<script></script>"]
            )
            mock_service_class.return_value = mock_service

            response = await get_embed_code(mock_session, mock_creator_user, "w_abc123")

        assert response.iframe_code == "<iframe></iframe>"
        assert response.script_code == "<script></script>"

    @pytest.mark.asyncio
    async def test_returns_404_when_not_found(self, mock_session, mock_creator_user):
        """Test returning 404 when widget not found."""
        from fastapi import HTTPException

        with patch("src.routers.widgets.WidgetService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_widget_for_owner = AsyncMock(return_value=None)
            mock_service_class.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                await get_embed_code(mock_session, mock_creator_user, "w_notfound")

        assert exc_info.value.status_code == 404
