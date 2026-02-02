"""Lab Note service layer."""

import logging
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import LabNote
from src.schemas.lab_note import (
    LabNoteCreate,
    LabNoteListResponse,
    LabNoteResponse,
    LabNoteSummaryResponse,
    LabNoteType,
    LabNoteUpdate,
    RelatedContent,
)

logger = logging.getLogger(__name__)


class LabNoteError(Exception):
    """Base exception for lab note operations."""

    pass


class LabNoteNotFoundError(LabNoteError):
    """Lab note not found."""

    pass


class LabNoteDuplicateSlugError(LabNoteError):
    """Duplicate slug error."""

    pass


class LabNoteService:
    """Service for lab note operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def _to_summary_response(self, note: LabNote) -> LabNoteSummaryResponse:
        """Convert model to summary response."""
        return LabNoteSummaryResponse(
            id=str(note.id),
            slug=note.slug,
            note_type=note.note_type,  # type: ignore[arg-type]
            title=note.title,
            summary=note.summary,
            author_name=note.author_name,
            is_published=note.is_published,
            published_at=note.published_at,
            featured_image_url=note.featured_image_url,
            tags=list(note.tags) if note.tags else None,
            is_premium=note.is_premium,
            created_at=note.created_at,
        )

    def _to_response(self, note: LabNote) -> LabNoteResponse:
        """Convert model to full response."""
        related = None
        if note.related_content:
            related = RelatedContent(
                archetypes=note.related_content.get("archetypes", []),
                cards=note.related_content.get("cards", []),
                sets=note.related_content.get("sets", []),
            )

        return LabNoteResponse(
            id=str(note.id),
            slug=note.slug,
            note_type=note.note_type,  # type: ignore[arg-type]
            title=note.title,
            summary=note.summary,
            content=note.content,
            author_name=note.author_name,
            is_published=note.is_published,
            published_at=note.published_at,
            meta_description=note.meta_description,
            featured_image_url=note.featured_image_url,
            tags=list(note.tags) if note.tags else None,
            related_content=related,
            is_premium=note.is_premium,
            created_at=note.created_at,
            updated_at=note.updated_at,
        )

    async def list_notes(
        self,
        page: int = 1,
        limit: int = 20,
        note_type: LabNoteType | None = None,
        tag: str | None = None,
        published_only: bool = True,
    ) -> LabNoteListResponse:
        """List lab notes with pagination and filtering."""
        query = select(LabNote)

        if published_only:
            query = query.where(LabNote.is_published.is_(True))

        if note_type:
            query = query.where(LabNote.note_type == note_type)

        if tag:
            query = query.where(LabNote.tags.contains([tag]))

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        try:
            count_result = await self.db.execute(count_query)
            total = count_result.scalar() or 0
        except SQLAlchemyError:
            logger.error("Database error counting lab notes", exc_info=True)
            raise LabNoteError("Failed to count lab notes") from None

        # Get paginated results
        offset = (page - 1) * limit
        query = (
            query.order_by(LabNote.published_at.desc().nulls_last())
            .offset(offset)
            .limit(limit)
        )

        try:
            result = await self.db.execute(query)
            notes = result.scalars().all()
        except SQLAlchemyError:
            logger.error("Database error listing lab notes", exc_info=True)
            raise LabNoteError("Failed to list lab notes") from None

        return LabNoteListResponse(
            items=[self._to_summary_response(note) for note in notes],
            total=total,
            page=page,
            limit=limit,
            has_next=(page * limit) < total,
            has_prev=page > 1,
        )

    async def get_by_slug(
        self, slug: str, published_only: bool = True
    ) -> LabNoteResponse:
        """Get a lab note by slug."""
        query = select(LabNote).where(LabNote.slug == slug)

        if published_only:
            query = query.where(LabNote.is_published.is_(True))

        try:
            result = await self.db.execute(query)
            note = result.scalar_one_or_none()
        except SQLAlchemyError:
            logger.error(
                "Database error getting lab note: slug=%s", slug, exc_info=True
            )
            raise LabNoteError("Failed to get lab note") from None

        if note is None:
            raise LabNoteNotFoundError(f"Lab note not found: {slug}")

        return self._to_response(note)

    async def get_by_id(
        self, note_id: UUID, published_only: bool = True
    ) -> LabNoteResponse:
        """Get a lab note by ID."""
        query = select(LabNote).where(LabNote.id == note_id)

        if published_only:
            query = query.where(LabNote.is_published.is_(True))

        try:
            result = await self.db.execute(query)
            note = result.scalar_one_or_none()
        except SQLAlchemyError:
            logger.error(
                "Database error getting lab note: id=%s", note_id, exc_info=True
            )
            raise LabNoteError("Failed to get lab note") from None

        if note is None:
            raise LabNoteNotFoundError(f"Lab note not found: {note_id}")

        return self._to_response(note)

    async def create(
        self, data: LabNoteCreate, author_id: UUID | None = None
    ) -> LabNoteResponse:
        """Create a new lab note."""
        related_dict = None
        if data.related_content:
            related_dict = {
                "archetypes": data.related_content.archetypes,
                "cards": data.related_content.cards,
                "sets": data.related_content.sets,
            }

        note = LabNote(
            id=uuid4(),
            slug=data.slug,
            note_type=data.note_type,
            title=data.title,
            summary=data.summary,
            content=data.content,
            author_id=author_id,
            author_name=data.author_name,
            is_published=data.is_published,
            published_at=datetime.now(UTC) if data.is_published else None,
            meta_description=data.meta_description,
            featured_image_url=data.featured_image_url,
            tags=data.tags,
            related_content=related_dict,
            is_premium=data.is_premium,
        )

        try:
            self.db.add(note)
            await self.db.commit()
            await self.db.refresh(note)
        except IntegrityError as e:
            await self.db.rollback()
            if "slug" in str(e):
                raise LabNoteDuplicateSlugError(
                    f"Slug already exists: {data.slug}"
                ) from None
            logger.error("Integrity error creating lab note", exc_info=True)
            raise LabNoteError("Failed to create lab note") from None
        except SQLAlchemyError:
            await self.db.rollback()
            logger.error("Database error creating lab note", exc_info=True)
            raise LabNoteError("Failed to create lab note") from None

        return self._to_response(note)

    async def update(self, note_id: UUID, data: LabNoteUpdate) -> LabNoteResponse:
        """Update a lab note."""
        query = select(LabNote).where(LabNote.id == note_id)

        try:
            result = await self.db.execute(query)
            note = result.scalar_one_or_none()
        except SQLAlchemyError:
            logger.error(
                "Database error getting lab note for update: id=%s",
                note_id,
                exc_info=True,
            )
            raise LabNoteError("Failed to update lab note") from None

        if note is None:
            raise LabNoteNotFoundError(f"Lab note not found: {note_id}")

        # Apply updates
        update_data = data.model_dump(exclude_unset=True)

        if "related_content" in update_data and data.related_content:
            update_data["related_content"] = {
                "archetypes": data.related_content.archetypes,
                "cards": data.related_content.cards,
                "sets": data.related_content.sets,
            }

        # Handle publish state change
        if "is_published" in update_data:
            if update_data["is_published"] and not note.is_published:
                # Publishing for the first time
                note.published_at = datetime.now(UTC)
            elif not update_data["is_published"]:
                # Unpublishing - keep published_at for history
                pass

        for key, value in update_data.items():
            if key != "related_content" or value is not None:
                setattr(note, key, value)

        try:
            await self.db.commit()
            await self.db.refresh(note)
        except SQLAlchemyError:
            await self.db.rollback()
            logger.error(
                "Database error updating lab note: id=%s", note_id, exc_info=True
            )
            raise LabNoteError("Failed to update lab note") from None

        return self._to_response(note)

    async def delete(self, note_id: UUID) -> bool:
        """Delete a lab note."""
        query = select(LabNote).where(LabNote.id == note_id)

        try:
            result = await self.db.execute(query)
            note = result.scalar_one_or_none()
        except SQLAlchemyError:
            logger.error(
                "Database error getting lab note for delete: id=%s",
                note_id,
                exc_info=True,
            )
            raise LabNoteError("Failed to delete lab note") from None

        if note is None:
            return False

        try:
            await self.db.delete(note)
            await self.db.commit()
        except SQLAlchemyError:
            await self.db.rollback()
            logger.error(
                "Database error deleting lab note: id=%s", note_id, exc_info=True
            )
            raise LabNoteError("Failed to delete lab note") from None

        return True
