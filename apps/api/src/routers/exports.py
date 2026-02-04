"""Data export endpoints for content creators."""

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.dependencies import CreatorUser
from src.schemas.export import (
    ExportCreate,
    ExportDownloadResponse,
    ExportListResponse,
    ExportResponse,
)
from src.services.data_export_service import DataExportService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/exports", tags=["exports"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_export(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CreatorUser,
    export_data: ExportCreate,
) -> ExportResponse:
    """Request a new data export.

    Requires creator access. Exports are available for 24 hours.
    """
    service = DataExportService(db)
    try:
        export = await service.create_export(
            user=current_user,
            export_type=export_data.export_type,
            config=export_data.config,
            format=export_data.format,
        )
        return ExportResponse.model_validate(export)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except Exception as e:
        logger.exception("Failed to create export")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create export",
        ) from e


@router.get("")
async def list_exports(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CreatorUser,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ExportListResponse:
    """List exports for the current creator.

    Requires creator access.
    """
    service = DataExportService(db)
    exports = await service.list_user_exports(current_user, limit=limit)
    return ExportListResponse(
        items=[ExportResponse.model_validate(e) for e in exports],
        total=len(exports),
    )


@router.get("/{export_id}")
async def get_export(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CreatorUser,
    export_id: UUID,
) -> ExportResponse:
    """Get an export by ID.

    Requires creator access and ownership.
    """
    service = DataExportService(db)
    export = await service.get_export(export_id, current_user)
    if export is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Export not found"
        )
    return ExportResponse.model_validate(export)


@router.get("/{export_id}/download")
async def get_download_url(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CreatorUser,
    export_id: UUID,
) -> ExportDownloadResponse:
    """Get a signed download URL for an export.

    Requires creator access and ownership. URL expires in 24 hours.
    """
    service = DataExportService(db)
    download_url = await service.generate_download_url(export_id, current_user)
    if download_url is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export not found or expired",
        )
    return ExportDownloadResponse(
        export_id=export_id,
        download_url=download_url,
        expires_in_hours=24,
    )
