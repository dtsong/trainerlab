"""Widget service for creator embeddable widgets."""

import hashlib
import html
import logging
from typing import Any
from uuid import uuid4

from sqlalchemy import Select, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User
from src.models.widget import Widget, generate_widget_id
from src.models.widget_view import WidgetView
from src.schemas.pagination import PaginatedResponse
from src.services.widget_resolvers import get_resolver

logger = logging.getLogger(__name__)


class WidgetService:
    """Service for widget CRUD and data resolution."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_widget(
        self,
        user: User,
        widget_type: str,
        config: dict[str, Any],
        theme: str = "dark",
        accent_color: str | None = None,
        show_attribution: bool = True,
    ) -> Widget:
        """Create a new widget.

        Args:
            user: The authenticated creator user
            widget_type: Widget type (e.g., "meta_snapshot")
            config: Widget configuration
            theme: "light" or "dark"
            accent_color: Optional accent color hex
            show_attribution: Whether to show TrainerLab attribution

        Returns:
            Created Widget model

        Raises:
            ValueError: If widget type is invalid
        """
        resolver = get_resolver(widget_type)
        if resolver is None:
            raise ValueError(f"Invalid widget type: {widget_type}")

        # Retry on ID collision (extremely rare with 6 alphanumeric chars)
        for _ in range(3):
            widget = Widget(
                id=generate_widget_id(),
                user_id=user.id,
                type=widget_type,
                config=config,
                theme=theme,
                accent_color=accent_color,
                show_attribution=show_attribution,
            )
            try:
                self.session.add(widget)
                await self.session.flush()
                break
            except IntegrityError:
                await self.session.rollback()
                logger.warning("Widget ID collision, retrying")
        else:
            raise RuntimeError("Failed to generate unique widget ID")

        await self.session.commit()
        await self.session.refresh(widget)
        logger.info("Created widget %s for user %s", widget.id, user.id)
        return widget

    async def get_widget(self, widget_id: str) -> Widget | None:
        """Get a widget by ID.

        Args:
            widget_id: Widget ID

        Returns:
            Widget if found and active, None otherwise
        """
        query = select(Widget).where(
            Widget.id == widget_id,
            Widget.is_active == True,  # noqa: E712
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_widget_for_owner(self, widget_id: str, user: User) -> Widget | None:
        """Get a widget by ID, verifying ownership.

        Args:
            widget_id: Widget ID
            user: The authenticated user (must own the widget)

        Returns:
            Widget if found and owned, None otherwise
        """
        query = select(Widget).where(
            Widget.id == widget_id,
            Widget.user_id == user.id,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_widget_data(self, widget_id: str) -> dict[str, Any]:
        """Get resolved widget data for rendering.

        Args:
            widget_id: Widget ID

        Returns:
            Resolved data from appropriate resolver
        """
        widget = await self.get_widget(widget_id)
        if not widget:
            return {"error": "Widget not found"}

        resolver_class = get_resolver(widget.type)
        if resolver_class is None:
            return {"error": f"Unknown widget type: {widget.type}"}

        resolver = resolver_class()
        try:
            data = await resolver.resolve(self.session, widget.config or {})
            return {
                "widget_id": widget.id,
                "type": widget.type,
                "theme": widget.theme,
                "accent_color": widget.accent_color,
                "show_attribution": widget.show_attribution,
                "data": data,
            }
        except Exception as e:
            logger.exception("Failed to resolve widget %s", widget_id)
            return {"error": str(e)}

    async def list_user_widgets(
        self,
        user: User,
        page: int = 1,
        limit: int = 20,
    ) -> PaginatedResponse:
        """List widgets for a user.

        Args:
            user: The authenticated user
            page: Page number (1-indexed)
            limit: Items per page

        Returns:
            Paginated response with widgets
        """
        query = (
            select(Widget)
            .where(Widget.user_id == user.id)
            .order_by(Widget.created_at.desc())
        )

        total = await self._get_total_count(query)

        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

        result = await self.session.execute(query)
        widgets = list(result.scalars().all())

        return PaginatedResponse(
            items=widgets,
            total=total,
            page=page,
            limit=limit,
            has_next=page * limit < total,
            has_prev=page > 1,
        )

    async def update_widget(
        self,
        widget_id: str,
        user: User,
        config: dict[str, Any] | None = None,
        theme: str | None = None,
        accent_color: str | None = None,
        show_attribution: bool | None = None,
        is_active: bool | None = None,
    ) -> Widget | None:
        """Update a widget.

        Args:
            widget_id: Widget ID
            user: The authenticated user (must own the widget)
            config: New config (optional)
            theme: New theme (optional)
            accent_color: New accent color (optional)
            show_attribution: New attribution setting (optional)
            is_active: New active status (optional)

        Returns:
            Updated Widget if found and owned, None otherwise
        """
        widget = await self.get_widget_for_owner(widget_id, user)
        if not widget:
            return None

        if config is not None:
            widget.config = config
        if theme is not None:
            widget.theme = theme
        if accent_color is not None:
            widget.accent_color = accent_color
        if show_attribution is not None:
            widget.show_attribution = show_attribution
        if is_active is not None:
            widget.is_active = is_active

        await self.session.commit()
        await self.session.refresh(widget)
        return widget

    async def delete_widget(self, widget_id: str, user: User) -> bool:
        """Delete a widget (soft delete by setting inactive).

        Args:
            widget_id: Widget ID
            user: The authenticated user (must own the widget)

        Returns:
            True if deleted, False if not found or not owned
        """
        widget = await self.get_widget_for_owner(widget_id, user)
        if not widget:
            return False

        widget.is_active = False
        await self.session.commit()
        logger.info("Deleted widget %s for user %s", widget_id, user.id)
        return True

    async def record_view(
        self,
        widget_id: str,
        referrer: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """Record a widget view.

        Args:
            widget_id: Widget ID
            referrer: HTTP referrer
            ip_address: Client IP (will be hashed)
            user_agent: Client user agent
        """
        widget = await self.get_widget(widget_id)
        if not widget:
            return

        # Hash IP for privacy
        ip_hash = None
        if ip_address:
            ip_hash = hashlib.sha256(ip_address.encode()).hexdigest()

        view = WidgetView(
            id=uuid4(),
            widget_id=widget_id,
            referrer=referrer[:500] if referrer else None,
            ip_hash=ip_hash,
            user_agent=user_agent[:500] if user_agent else None,
        )
        self.session.add(view)

        # Increment view counter
        widget.view_count += 1

        await self.session.commit()

    def generate_embed_code(
        self,
        widget: Widget,
        embed_format: str = "iframe",
        base_url: str = "https://trainerlab.gg",
    ) -> str:
        """Generate embed code for a widget.

        Args:
            widget: Widget model
            embed_format: "iframe" or "script"
            base_url: Base URL for embed

        Returns:
            HTML embed code
        """
        embed_url = f"{base_url}/embed/{widget.id}"

        if embed_format == "script":
            return f"""<div id="trainerlab-widget-{widget.id}"></div>
<script src="{base_url}/embed.js" data-widget="{widget.id}"></script>"""

        # Default: iframe
        return f"""<iframe
  src="{html.escape(embed_url)}"
  width="100%"
  height="400"
  frameborder="0"
  loading="lazy"
  title="TrainerLab Widget"
></iframe>"""

    async def _get_total_count(self, query: Select) -> int:
        """Get total count for a query (without pagination)."""
        count_query = select(func.count()).select_from(query.subquery())
        result = await self.session.execute(count_query)
        return result.scalar() or 0
