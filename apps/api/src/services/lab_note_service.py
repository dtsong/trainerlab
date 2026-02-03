"""Lab Note service layer."""

import logging
import re
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import LabNote, LabNoteRevision
from src.schemas.lab_note import (
    LabNoteCreate,
    LabNoteListResponse,
    LabNoteResponse,
    LabNoteRevisionResponse,
    LabNoteStatus,
    LabNoteSummaryResponse,
    LabNoteType,
    LabNoteUpdate,
    RelatedContent,
)

logger = logging.getLogger(__name__)

_SLUG_STRIP = re.compile(r"[^a-z0-9\s-]")
_SLUG_SPACES = re.compile(r"\s+")


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

    @staticmethod
    def _generate_slug(title: str) -> str:
        """Generate a URL slug from a title."""
        slug = title.lower().strip()
        slug = _SLUG_STRIP.sub("", slug)
        slug = _SLUG_SPACES.sub("-", slug)
        slug = slug.strip("-")
        return slug[:255]

    async def _ensure_unique_slug(
        self, slug: str, exclude_id: UUID | None = None
    ) -> str:
        """Ensure slug is unique, appending -2, -3, etc. if needed."""
        base_slug = slug
        counter = 1
        while True:
            query = select(LabNote.id).where(LabNote.slug == slug)
            if exclude_id:
                query = query.where(LabNote.id != exclude_id)
            result = await self.db.execute(query)
            if result.scalar_one_or_none() is None:
                return slug
            counter += 1
            slug = f"{base_slug}-{counter}"

    def _to_summary_response(self, note: LabNote) -> LabNoteSummaryResponse:
        """Convert model to summary response."""
        return LabNoteSummaryResponse(
            id=str(note.id),
            slug=note.slug,
            note_type=note.note_type,  # type: ignore[arg-type]
            title=note.title,
            summary=note.summary,
            author_name=note.author_name,
            status=note.status,  # type: ignore[arg-type]
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
            status=note.status,  # type: ignore[arg-type]
            version=note.version,
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

    def _to_revision_response(self, rev: LabNoteRevision) -> LabNoteRevisionResponse:
        """Convert revision model to response."""
        return LabNoteRevisionResponse(
            id=str(rev.id),
            lab_note_id=str(rev.lab_note_id),
            version=rev.version,
            title=rev.title,
            content=rev.content,
            summary=rev.summary,
            author_id=str(rev.author_id) if rev.author_id else None,
            change_description=rev.change_description,
            created_at=rev.created_at,
        )

    async def list_notes(
        self,
        page: int = 1,
        limit: int = 20,
        note_type: LabNoteType | None = None,
        tag: str | None = None,
        published_only: bool = True,
        status: LabNoteStatus | None = None,
    ) -> LabNoteListResponse:
        """List lab notes with pagination and filtering."""
        query = select(LabNote)

        if published_only:
            query = query.where(LabNote.is_published.is_(True))

        if status:
            query = query.where(LabNote.status == status)

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
        # Auto-generate slug from title if not provided
        slug = data.slug if data.slug else self._generate_slug(data.title)
        slug = await self._ensure_unique_slug(slug)

        # Sync is_published with status
        is_published = data.status == "published"

        related_dict = None
        if data.related_content:
            related_dict = {
                "archetypes": data.related_content.archetypes,
                "cards": data.related_content.cards,
                "sets": data.related_content.sets,
            }

        note = LabNote(
            id=uuid4(),
            slug=slug,
            note_type=data.note_type,
            title=data.title,
            summary=data.summary,
            content=data.content,
            author_id=author_id,
            author_name=data.author_name,
            status=data.status,
            version=1,
            is_published=is_published,
            published_at=datetime.now(UTC) if is_published else None,
            meta_description=data.meta_description,
            featured_image_url=data.featured_image_url,
            tags=data.tags,
            related_content=related_dict,
            is_premium=data.is_premium,
        )

        # Create initial revision
        revision = LabNoteRevision(
            id=uuid4(),
            lab_note_id=note.id,
            version=1,
            title=data.title,
            content=data.content,
            summary=data.summary,
            author_id=author_id,
            change_description="Initial version",
        )

        try:
            self.db.add(note)
            self.db.add(revision)
            await self.db.commit()
            await self.db.refresh(note)
        except IntegrityError as e:
            await self.db.rollback()
            if "slug" in str(e):
                raise LabNoteDuplicateSlugError(
                    f"Slug already exists: {slug}"
                ) from None
            logger.error("Integrity error creating lab note", exc_info=True)
            raise LabNoteError("Failed to create lab note") from None
        except SQLAlchemyError:
            await self.db.rollback()
            logger.error("Database error creating lab note", exc_info=True)
            raise LabNoteError("Failed to create lab note") from None

        return self._to_response(note)

    async def update(
        self, note_id: UUID, data: LabNoteUpdate, user_id: UUID | None = None
    ) -> LabNoteResponse:
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

        # Check if content changed (for revision tracking)
        update_data = data.model_dump(exclude_unset=True)
        content_changed = (
            "title" in update_data and update_data["title"] != note.title
        ) or ("content" in update_data and update_data["content"] != note.content)

        if "related_content" in update_data and data.related_content:
            update_data["related_content"] = {
                "archetypes": data.related_content.archetypes,
                "cards": data.related_content.cards,
                "sets": data.related_content.sets,
            }

        # Handle status → is_published sync
        if "status" in update_data:
            new_status = update_data["status"]
            update_data["is_published"] = new_status == "published"
            if new_status == "published" and not note.is_published:
                note.published_at = datetime.now(UTC)
        elif "is_published" in update_data:
            if update_data["is_published"] and not note.is_published:
                note.published_at = datetime.now(UTC)
                update_data["status"] = "published"
            elif not update_data["is_published"] and note.is_published:
                update_data["status"] = "draft"

        for key, value in update_data.items():
            if key != "related_content" or value is not None:
                setattr(note, key, value)

        # Create revision if content changed
        if content_changed:
            note.version += 1
            revision = LabNoteRevision(
                id=uuid4(),
                lab_note_id=note.id,
                version=note.version,
                title=note.title,
                content=note.content,
                summary=note.summary,
                author_id=user_id,
                change_description=None,
            )
            self.db.add(revision)

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

    async def update_status(
        self, note_id: UUID, status: LabNoteStatus, user_id: UUID | None = None
    ) -> LabNoteResponse:
        """Update a lab note's workflow status."""
        query = select(LabNote).where(LabNote.id == note_id)

        try:
            result = await self.db.execute(query)
            note = result.scalar_one_or_none()
        except SQLAlchemyError:
            logger.error(
                "Database error getting lab note for status update: id=%s",
                note_id,
                exc_info=True,
            )
            raise LabNoteError("Failed to update lab note status") from None

        if note is None:
            raise LabNoteNotFoundError(f"Lab note not found: {note_id}")

        note.status = status
        note.is_published = status == "published"

        if status == "published" and not note.published_at:
            note.published_at = datetime.now(UTC)

        if status == "review" and user_id:
            note.reviewer_id = user_id

        try:
            await self.db.commit()
            await self.db.refresh(note)
        except SQLAlchemyError:
            await self.db.rollback()
            logger.error(
                "Database error updating lab note status: id=%s",
                note_id,
                exc_info=True,
            )
            raise LabNoteError("Failed to update lab note status") from None

        return self._to_response(note)

    async def list_revisions(self, note_id: UUID) -> list[LabNoteRevisionResponse]:
        """List revisions for a lab note."""
        # Verify note exists
        note_query = select(LabNote.id).where(LabNote.id == note_id)
        try:
            result = await self.db.execute(note_query)
            if result.scalar_one_or_none() is None:
                raise LabNoteNotFoundError(f"Lab note not found: {note_id}")
        except SQLAlchemyError:
            logger.error(
                "Database error checking lab note: id=%s", note_id, exc_info=True
            )
            raise LabNoteError("Failed to list revisions") from None

        query = (
            select(LabNoteRevision)
            .where(LabNoteRevision.lab_note_id == note_id)
            .order_by(LabNoteRevision.version.desc())
        )

        try:
            result = await self.db.execute(query)
            revisions = result.scalars().all()
        except SQLAlchemyError:
            logger.error(
                "Database error listing revisions: note_id=%s",
                note_id,
                exc_info=True,
            )
            raise LabNoteError("Failed to list revisions") from None

        return [self._to_revision_response(rev) for rev in revisions]

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
