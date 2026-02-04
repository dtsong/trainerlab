"""Widget endpoints for content creators."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.dependencies import CreatorUser
from src.schemas.widget import (
    WidgetCreate,
    WidgetDataResponse,
    WidgetEmbedCodeResponse,
    WidgetListResponse,
    WidgetResponse,
    WidgetUpdate,
)
from src.services.widget_service import WidgetService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/widgets", tags=["widgets"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_widget(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CreatorUser,
    widget_data: WidgetCreate,
) -> WidgetResponse:
    """Create a new embeddable widget.

    Requires creator access.
    """
    service = WidgetService(db)
    try:
        widget = await service.create_widget(
            user=current_user,
            widget_type=widget_data.type,
            config=widget_data.config,
            theme=widget_data.theme,
            accent_color=widget_data.accent_color,
            show_attribution=widget_data.show_attribution,
        )
        return WidgetResponse.model_validate(widget)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.get("")
async def list_widgets(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CreatorUser,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> WidgetListResponse:
    """List widgets for the current creator.

    Requires creator access.
    """
    service = WidgetService(db)
    result = await service.list_user_widgets(current_user, page=page, limit=limit)
    return WidgetListResponse(
        items=[WidgetResponse.model_validate(w) for w in result.items],
        total=result.total,
        page=result.page,
        limit=result.limit,
        has_next=result.has_next,
        has_prev=result.has_prev,
    )


@router.get("/{widget_id}")
async def get_widget(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CreatorUser,
    widget_id: str,
) -> WidgetResponse:
    """Get a widget by ID.

    Requires creator access and ownership.
    """
    service = WidgetService(db)
    widget = await service.get_widget_for_owner(widget_id, current_user)
    if widget is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Widget not found"
        )
    return WidgetResponse.model_validate(widget)


@router.get("/{widget_id}/data")
async def get_widget_data(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    widget_id: str,
) -> WidgetDataResponse:
    """Get resolved widget data for embedding.

    Public endpoint - no authentication required.
    Records view analytics.
    """
    service = WidgetService(db)

    # Record view
    referrer = request.headers.get("referer")
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    await service.record_view(widget_id, referrer, ip_address, user_agent)

    # Resolve data
    data = await service.get_widget_data(widget_id)
    if "error" in data and data.get("error") == "Widget not found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Widget not found"
        )

    return WidgetDataResponse(**data)


@router.get("/{widget_id}/embed-code")
async def get_embed_code(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CreatorUser,
    widget_id: str,
) -> WidgetEmbedCodeResponse:
    """Get embed code for a widget.

    Requires creator access and ownership.
    """
    service = WidgetService(db)
    widget = await service.get_widget_for_owner(widget_id, current_user)
    if widget is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Widget not found"
        )

    iframe_code = service.generate_embed_code(widget, embed_format="iframe")
    script_code = service.generate_embed_code(widget, embed_format="script")

    return WidgetEmbedCodeResponse(
        widget_id=widget.id,
        iframe_code=iframe_code,
        script_code=script_code,
    )


@router.patch("/{widget_id}")
async def update_widget(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CreatorUser,
    widget_id: str,
    widget_data: WidgetUpdate,
) -> WidgetResponse:
    """Update a widget.

    Requires creator access and ownership.
    """
    service = WidgetService(db)
    widget = await service.update_widget(
        widget_id=widget_id,
        user=current_user,
        config=widget_data.config,
        theme=widget_data.theme,
        accent_color=widget_data.accent_color,
        show_attribution=widget_data.show_attribution,
        is_active=widget_data.is_active,
    )
    if widget is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Widget not found"
        )
    return WidgetResponse.model_validate(widget)


@router.delete("/{widget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_widget(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CreatorUser,
    widget_id: str,
) -> None:
    """Delete a widget (soft delete).

    Requires creator access and ownership.
    """
    service = WidgetService(db)
    deleted = await service.delete_widget(widget_id, current_user)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Widget not found"
        )
