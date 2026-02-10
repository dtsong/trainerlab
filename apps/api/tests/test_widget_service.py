"""Tests for WidgetService."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User
from src.models.widget import Widget
from src.services.widget_service import WidgetService


@pytest.fixture
def mock_session() -> AsyncMock:
    """Create a mock database session."""
    session = AsyncMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.flush = AsyncMock()
    session.rollback = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def mock_user() -> User:
    """Create a mock user."""
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.email = "creator@example.com"
    user.is_creator = True
    return user


@pytest.fixture
def mock_widget() -> Widget:
    """Create a mock widget."""
    widget = MagicMock(spec=Widget)
    widget.id = "w_abc123"
    widget.user_id = uuid4()
    widget.type = "meta_snapshot"
    widget.config = {"region": None}
    widget.theme = "dark"
    widget.accent_color = None
    widget.show_attribution = True
    widget.is_active = True
    widget.view_count = 0
    return widget


class TestCreateWidget:
    """Tests for create_widget method."""

    @pytest.mark.asyncio
    async def test_creates_widget_with_valid_type(
        self, mock_session: AsyncMock, mock_user: User
    ):
        """Test creating a widget with valid type."""
        service = WidgetService(mock_session)

        with patch("src.services.widget_service.get_resolver") as mock_resolver:
            mock_resolver.return_value = MagicMock()
            with patch("src.services.widget_service.generate_widget_id") as mock_gen:
                mock_gen.return_value = "w_test12"
                await service.create_widget(
                    mock_user,
                    widget_type="meta_snapshot",
                    config={"region": None},
                )

        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_error_for_invalid_type(
        self, mock_session: AsyncMock, mock_user: User
    ):
        """Test raising ValueError for invalid widget type."""
        service = WidgetService(mock_session)

        with patch("src.services.widget_service.get_resolver") as mock_resolver:
            mock_resolver.return_value = None
            with pytest.raises(ValueError, match="Invalid widget type"):
                await service.create_widget(
                    mock_user, widget_type="invalid_type", config={}
                )

    @pytest.mark.asyncio
    async def test_retries_on_id_collision(
        self, mock_session: AsyncMock, mock_user: User
    ):
        """Test retrying widget creation on ID collision."""
        service = WidgetService(mock_session)

        collision_count = 0

        async def flush_with_collision():
            nonlocal collision_count
            collision_count += 1
            if collision_count < 3:
                raise IntegrityError("duplicate key", None, None)

        mock_session.flush = flush_with_collision

        with patch("src.services.widget_service.get_resolver") as mock_resolver:
            mock_resolver.return_value = MagicMock()
            with patch("src.services.widget_service.generate_widget_id") as mock_gen:
                mock_gen.side_effect = ["w_col1", "w_col2", "w_good"]
                await service.create_widget(
                    mock_user, widget_type="meta_snapshot", config={}
                )

        assert collision_count == 3

    @pytest.mark.asyncio
    async def test_raises_after_max_retries(
        self, mock_session: AsyncMock, mock_user: User
    ):
        """Test raising RuntimeError after max collision retries."""
        service = WidgetService(mock_session)

        async def always_collide():
            raise IntegrityError("duplicate key", None, None)

        mock_session.flush = always_collide

        with patch("src.services.widget_service.get_resolver") as mock_resolver:
            mock_resolver.return_value = MagicMock()
            with pytest.raises(RuntimeError, match="Failed to generate unique"):
                await service.create_widget(
                    mock_user, widget_type="meta_snapshot", config={}
                )


class TestGetWidget:
    """Tests for get_widget method."""

    @pytest.mark.asyncio
    async def test_returns_active_widget(
        self, mock_session: AsyncMock, mock_widget: Widget
    ):
        """Test returning active widget."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_widget
        mock_session.execute.return_value = mock_result

        service = WidgetService(mock_session)
        result = await service.get_widget("w_abc123")

        assert result == mock_widget

    @pytest.mark.asyncio
    async def test_returns_none_for_inactive(self, mock_session: AsyncMock):
        """Test returning None for inactive widget."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        service = WidgetService(mock_session)
        result = await service.get_widget("w_inactive")

        assert result is None


class TestGetWidgetForOwner:
    """Tests for get_widget_for_owner method."""

    @pytest.mark.asyncio
    async def test_returns_widget_when_owned(
        self, mock_session: AsyncMock, mock_user: User, mock_widget: Widget
    ):
        """Test returning widget when user owns it."""
        mock_widget.user_id = mock_user.id
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_widget
        mock_session.execute.return_value = mock_result

        service = WidgetService(mock_session)
        result = await service.get_widget_for_owner("w_abc123", mock_user)

        assert result == mock_widget

    @pytest.mark.asyncio
    async def test_returns_none_when_not_owned(
        self, mock_session: AsyncMock, mock_user: User
    ):
        """Test returning None when user doesn't own widget."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        service = WidgetService(mock_session)
        result = await service.get_widget_for_owner("w_other", mock_user)

        assert result is None


class TestGetWidgetData:
    """Tests for get_widget_data method."""

    @pytest.mark.asyncio
    async def test_returns_resolved_data(
        self, mock_session: AsyncMock, mock_widget: Widget
    ):
        """Test returning resolved widget data."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_widget
        mock_session.execute.return_value = mock_result

        mock_resolver_class = MagicMock()
        mock_resolver_instance = MagicMock()
        mock_resolver_instance.resolve = AsyncMock(
            return_value={"archetypes": [{"name": "Charizard"}]}
        )
        mock_resolver_class.return_value = mock_resolver_instance

        service = WidgetService(mock_session)

        with patch("src.services.widget_service.get_resolver") as mock_get:
            mock_get.return_value = mock_resolver_class
            result = await service.get_widget_data("w_abc123")

        assert "data" in result
        assert result["widget_id"] == "w_abc123"
        assert result["type"] == "meta_snapshot"

    @pytest.mark.asyncio
    async def test_returns_error_when_not_found(self, mock_session: AsyncMock):
        """Test returning error when widget not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        service = WidgetService(mock_session)
        result = await service.get_widget_data("w_notfound")

        assert result == {"error": "Widget not found"}

    @pytest.mark.asyncio
    async def test_returns_error_on_resolver_failure(
        self, mock_session: AsyncMock, mock_widget: Widget
    ):
        """Test returning error when resolver fails."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_widget
        mock_session.execute.return_value = mock_result

        mock_resolver_class = MagicMock()
        mock_resolver_instance = MagicMock()
        mock_resolver_instance.resolve = AsyncMock(side_effect=Exception("DB error"))
        mock_resolver_class.return_value = mock_resolver_instance

        service = WidgetService(mock_session)

        with patch("src.services.widget_service.get_resolver") as mock_get:
            mock_get.return_value = mock_resolver_class
            result = await service.get_widget_data("w_abc123")

        assert "error" in result
        assert result["error"] == "DB error"


class TestListUserWidgets:
    """Tests for list_user_widgets method."""

    @pytest.mark.asyncio
    async def test_returns_paginated_widgets(
        self, mock_session: AsyncMock, mock_user: User
    ):
        """Test returning paginated widgets."""
        mock_widgets = [MagicMock(spec=Widget), MagicMock(spec=Widget)]

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_widgets
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 2

        mock_session.execute.side_effect = [mock_count_result, mock_result]

        service = WidgetService(mock_session)
        result = await service.list_user_widgets(mock_user, page=1, limit=20)

        assert result.total == 2
        assert len(result.items) == 2
        assert result.page == 1
        assert result.has_next is False
        assert result.has_prev is False

    @pytest.mark.asyncio
    async def test_pagination_has_next(self, mock_session: AsyncMock, mock_user: User):
        """Test pagination has_next flag."""
        mock_widgets = [MagicMock(spec=Widget)]

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_widgets
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 25

        mock_session.execute.side_effect = [mock_count_result, mock_result]

        service = WidgetService(mock_session)
        result = await service.list_user_widgets(mock_user, page=1, limit=10)

        assert result.has_next is True


class TestUpdateWidget:
    """Tests for update_widget method."""

    @pytest.mark.asyncio
    async def test_updates_widget_config(
        self, mock_session: AsyncMock, mock_user: User, mock_widget: Widget
    ):
        """Test updating widget config."""
        mock_widget.user_id = mock_user.id
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_widget
        mock_session.execute.return_value = mock_result

        service = WidgetService(mock_session)
        result = await service.update_widget(
            "w_abc123", mock_user, config={"region": "NA"}
        )

        assert result == mock_widget
        assert mock_widget.config == {"region": "NA"}
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_updates_widget_theme(
        self, mock_session: AsyncMock, mock_user: User, mock_widget: Widget
    ):
        """Test updating widget theme."""
        mock_widget.user_id = mock_user.id
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_widget
        mock_session.execute.return_value = mock_result

        service = WidgetService(mock_session)
        await service.update_widget("w_abc123", mock_user, theme="light")

        assert mock_widget.theme == "light"

    @pytest.mark.asyncio
    async def test_returns_none_when_not_owned(
        self, mock_session: AsyncMock, mock_user: User
    ):
        """Test returning None when widget not owned."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        service = WidgetService(mock_session)
        result = await service.update_widget("w_other", mock_user, theme="light")

        assert result is None


class TestDeleteWidget:
    """Tests for delete_widget method."""

    @pytest.mark.asyncio
    async def test_soft_deletes_widget(
        self, mock_session: AsyncMock, mock_user: User, mock_widget: Widget
    ):
        """Test soft deleting widget."""
        mock_widget.user_id = mock_user.id
        mock_widget.is_active = True
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_widget
        mock_session.execute.return_value = mock_result

        service = WidgetService(mock_session)
        result = await service.delete_widget("w_abc123", mock_user)

        assert result is True
        assert mock_widget.is_active is False
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_false_when_not_found(
        self, mock_session: AsyncMock, mock_user: User
    ):
        """Test returning False when widget not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        service = WidgetService(mock_session)
        result = await service.delete_widget("w_notfound", mock_user)

        assert result is False


class TestRecordView:
    """Tests for record_view method."""

    @pytest.mark.asyncio
    async def test_records_view_with_all_data(
        self, mock_session: AsyncMock, mock_widget: Widget
    ):
        """Test recording view with all data."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_widget
        mock_session.execute.return_value = mock_result

        service = WidgetService(mock_session)
        await service.record_view(
            "w_abc123",
            referrer="https://example.com",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
        )

        mock_session.add.assert_called_once()
        assert mock_widget.view_count == 1
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_hashes_ip_address(
        self, mock_session: AsyncMock, mock_widget: Widget
    ):
        """Test that IP address is hashed."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_widget
        mock_session.execute.return_value = mock_result

        service = WidgetService(mock_session)
        await service.record_view("w_abc123", ip_address="192.168.1.1")

        added_view = mock_session.add.call_args[0][0]
        assert added_view.ip_hash is not None
        assert added_view.ip_hash != "192.168.1.1"

    @pytest.mark.asyncio
    async def test_skips_when_widget_not_found(self, mock_session: AsyncMock):
        """Test skipping view recording when widget not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        service = WidgetService(mock_session)
        await service.record_view("w_notfound")

        mock_session.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_truncates_long_referrer(
        self, mock_session: AsyncMock, mock_widget: Widget
    ):
        """Test truncating long referrer URL."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_widget
        mock_session.execute.return_value = mock_result

        service = WidgetService(mock_session)
        long_referrer = "https://example.com/" + "a" * 600
        await service.record_view("w_abc123", referrer=long_referrer)

        added_view = mock_session.add.call_args[0][0]
        assert len(added_view.referrer) == 500


class TestGenerateEmbedCode:
    """Tests for generate_embed_code method."""

    def test_generates_iframe_code(self, mock_session: AsyncMock, mock_widget: Widget):
        """Test generating iframe embed code."""
        service = WidgetService(mock_session)
        code = service.generate_embed_code(mock_widget, embed_format="iframe")

        assert "<iframe" in code
        assert 'src="https://trainerlab.gg/embed/w_abc123"' in code
        assert 'loading="lazy"' in code

    def test_generates_script_code(self, mock_session: AsyncMock, mock_widget: Widget):
        """Test generating script embed code."""
        service = WidgetService(mock_session)
        code = service.generate_embed_code(mock_widget, embed_format="script")

        assert "<script" in code
        assert 'data-widget="w_abc123"' in code
        assert "embed.js" in code

    def test_uses_custom_base_url(self, mock_session: AsyncMock, mock_widget: Widget):
        """Test using custom base URL."""
        service = WidgetService(mock_session)
        code = service.generate_embed_code(
            mock_widget, base_url="https://custom.example.com"
        )

        assert "https://custom.example.com/embed/w_abc123" in code

    def test_escapes_html_in_url(self, mock_session: AsyncMock, mock_widget: Widget):
        """Test HTML escaping in embed URL."""
        mock_widget.id = "w_<script>"
        service = WidgetService(mock_session)
        code = service.generate_embed_code(mock_widget, embed_format="iframe")

        assert "&lt;script&gt;" in code or "<script>" not in code
