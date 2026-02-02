"""Lab Notes endpoints."""

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.dependencies import CurrentUser
from src.schemas.lab_note import (
    LabNoteCreate,
    LabNoteListResponse,
    LabNoteResponse,
    LabNoteType,
    LabNoteUpdate,
)
from src.services.lab_note_service import (
    LabNoteDuplicateSlugError,
    LabNoteError,
    LabNoteNotFoundError,
    LabNoteService,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/lab-notes", tags=["lab-notes"])


@router.get("")
async def list_lab_notes(
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    limit: Annotated[int, Query(ge=1, le=100, description="Page size")] = 20,
    note_type: Annotated[
        LabNoteType | None, Query(description="Filter by note type")
    ] = None,
    tag: Annotated[str | None, Query(description="Filter by tag")] = None,
) -> LabNoteListResponse:
    """List published lab notes with pagination and filtering.

    Returns a paginated list of published lab notes, ordered by publish date
    descending (newest first). Can filter by note type or tag.
    """
    service = LabNoteService(db)
    try:
        return await service.list_notes(
            page=page,
            limit=limit,
            note_type=note_type,
            tag=tag,
            published_only=True,
        )
    except LabNoteError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to retrieve lab notes. Please try again later.",
        ) from None


@router.get("/{slug}")
async def get_lab_note(
    slug: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LabNoteResponse:
    """Get a published lab note by slug.

    Returns the full lab note content including markdown body.
    Only returns published notes.
    """
    service = LabNoteService(db)
    try:
        return await service.get_by_slug(slug, published_only=True)
    except LabNoteNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lab note not found: {slug}",
        ) from None
    except LabNoteError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to retrieve lab note. Please try again later.",
        ) from None


# Admin endpoints (require authentication)


@router.get("/admin/all")
async def list_all_lab_notes(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    limit: Annotated[int, Query(ge=1, le=100, description="Page size")] = 20,
    note_type: Annotated[
        LabNoteType | None, Query(description="Filter by note type")
    ] = None,
    tag: Annotated[str | None, Query(description="Filter by tag")] = None,
) -> LabNoteListResponse:
    """List all lab notes including unpublished (admin only).

    Requires authentication. Returns all notes regardless of publish status.
    """
    service = LabNoteService(db)
    try:
        return await service.list_notes(
            page=page,
            limit=limit,
            note_type=note_type,
            tag=tag,
            published_only=False,
        )
    except LabNoteError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to retrieve lab notes. Please try again later.",
        ) from None


@router.get("/admin/{note_id}")
async def get_lab_note_by_id(
    note_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
) -> LabNoteResponse:
    """Get a lab note by ID (admin only).

    Requires authentication. Returns note regardless of publish status.
    """
    service = LabNoteService(db)
    try:
        return await service.get_by_id(note_id, published_only=False)
    except LabNoteNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lab note not found: {note_id}",
        ) from None
    except LabNoteError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to retrieve lab note. Please try again later.",
        ) from None


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_lab_note(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    data: LabNoteCreate,
) -> LabNoteResponse:
    """Create a new lab note (admin only).

    Requires authentication. Creates a new lab note with the provided data.
    """
    service = LabNoteService(db)
    try:
        return await service.create(data, author_id=current_user.id)
    except LabNoteDuplicateSlugError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Slug already exists: {data.slug}",
        ) from None
    except LabNoteError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to create lab note. Please try again later.",
        ) from None


@router.patch("/{note_id}")
async def update_lab_note(
    note_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    data: LabNoteUpdate,
) -> LabNoteResponse:
    """Update a lab note (admin only).

    Requires authentication. Updates the specified lab note.
    """
    service = LabNoteService(db)
    try:
        return await service.update(note_id, data)
    except LabNoteNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lab note not found: {note_id}",
        ) from None
    except LabNoteError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to update lab note. Please try again later.",
        ) from None


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lab_note(
    note_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
) -> Response:
    """Delete a lab note (admin only).

    Requires authentication. Permanently deletes the specified lab note.
    """
    service = LabNoteService(db)
    try:
        deleted = await service.delete(note_id)
    except LabNoteError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to delete lab note. Please try again later.",
        ) from None

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lab note not found: {note_id}",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
