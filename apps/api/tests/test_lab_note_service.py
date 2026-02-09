"""Tests for lab note service."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.models import LabNote, LabNoteRevision
from src.schemas.lab_note import (
    LabNoteCreate,
    LabNoteUpdate,
    RelatedContent,
)
from src.services.lab_note_service import (
    LabNoteDuplicateSlugError,
    LabNoteError,
    LabNoteNotFoundError,
    LabNoteService,
)


class TestGenerateSlug:
    """Tests for slug generation."""

    def test_generates_slug_from_title(self) -> None:
        slug = LabNoteService._generate_slug("Meta Analysis: Charizard ex Dominance")
        assert slug == "meta-analysis-charizard-ex-dominance"

    def test_handles_special_characters(self) -> None:
        slug = LabNoteService._generate_slug("What's New? 10 Cards!")
        assert slug == "whats-new-10-cards"

    def test_handles_multiple_spaces(self) -> None:
        slug = LabNoteService._generate_slug("Hello    World")
        assert slug == "hello-world"

    def test_trims_leading_trailing_dashes(self) -> None:
        slug = LabNoteService._generate_slug("  -Hello World-  ")
        assert slug == "hello-world"

    def test_truncates_long_slugs(self) -> None:
        long_title = "A" * 300
        slug = LabNoteService._generate_slug(long_title)
        assert len(slug) <= 255


class TestEnsureUniqueSlug:
    """Tests for slug uniqueness."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> LabNoteService:
        return LabNoteService(mock_session)

    @pytest.mark.asyncio
    async def test_returns_slug_if_unique(
        self, service: LabNoteService, mock_session: AsyncMock
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        slug = await service._ensure_unique_slug("my-slug")
        assert slug == "my-slug"

    @pytest.mark.asyncio
    async def test_appends_counter_if_not_unique(
        self, service: LabNoteService, mock_session: AsyncMock
    ) -> None:
        mock_result_exists = MagicMock()
        mock_result_exists.scalar_one_or_none.return_value = uuid4()

        mock_result_unique = MagicMock()
        mock_result_unique.scalar_one_or_none.return_value = None

        mock_session.execute.side_effect = [mock_result_exists, mock_result_unique]

        slug = await service._ensure_unique_slug("my-slug")
        assert slug == "my-slug-2"

    @pytest.mark.asyncio
    async def test_increments_counter_until_unique(
        self, service: LabNoteService, mock_session: AsyncMock
    ) -> None:
        mock_result_exists = MagicMock()
        mock_result_exists.scalar_one_or_none.return_value = uuid4()

        mock_result_unique = MagicMock()
        mock_result_unique.scalar_one_or_none.return_value = None

        mock_session.execute.side_effect = [
            mock_result_exists,
            mock_result_exists,
            mock_result_exists,
            mock_result_unique,
        ]

        slug = await service._ensure_unique_slug("my-slug")
        assert slug == "my-slug-4"

    @pytest.mark.asyncio
    async def test_excludes_id_from_uniqueness_check(
        self, service: LabNoteService, mock_session: AsyncMock
    ) -> None:
        note_id = uuid4()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        slug = await service._ensure_unique_slug("my-slug", exclude_id=note_id)
        assert slug == "my-slug"
        mock_session.execute.assert_called_once()


class TestListNotes:
    """Tests for listing lab notes."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> LabNoteService:
        return LabNoteService(mock_session)

    @pytest.fixture
    def sample_note(self) -> LabNote:
        return LabNote(
            id=uuid4(),
            slug="test-note",
            note_type="set_analysis",
            title="Test Note",
            summary="Test summary",
            content="# Test Content",
            author_name="Test Author",
            status="published",
            version=1,
            is_published=True,
            published_at=datetime.now(UTC),
            tags=["meta", "analysis"],
            is_premium=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

    @pytest.mark.asyncio
    async def test_returns_paginated_list(
        self, service: LabNoteService, mock_session: AsyncMock, sample_note: LabNote
    ) -> None:
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_notes_result = MagicMock()
        mock_notes_result.scalars.return_value.all.return_value = [sample_note]

        mock_session.execute.side_effect = [mock_count_result, mock_notes_result]

        result = await service.list_notes()

        assert result.total == 1
        assert len(result.items) == 1
        assert result.items[0].slug == "test-note"

    @pytest.mark.asyncio
    async def test_filters_by_note_type(
        self, service: LabNoteService, mock_session: AsyncMock, sample_note: LabNote
    ) -> None:
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_notes_result = MagicMock()
        mock_notes_result.scalars.return_value.all.return_value = [sample_note]

        mock_session.execute.side_effect = [mock_count_result, mock_notes_result]

        result = await service.list_notes(note_type="set_analysis")

        assert result.total == 1

    @pytest.mark.asyncio
    async def test_filters_by_tag(
        self, service: LabNoteService, mock_session: AsyncMock, sample_note: LabNote
    ) -> None:
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_notes_result = MagicMock()
        mock_notes_result.scalars.return_value.all.return_value = [sample_note]

        mock_session.execute.side_effect = [mock_count_result, mock_notes_result]

        result = await service.list_notes(tag="meta")

        assert result.total == 1

    @pytest.mark.asyncio
    async def test_raises_on_database_error(
        self, service: LabNoteService, mock_session: AsyncMock
    ) -> None:
        mock_session.execute.side_effect = SQLAlchemyError("DB error")

        with pytest.raises(LabNoteError, match="Failed to count lab notes"):
            await service.list_notes()


class TestGetBySlug:
    """Tests for getting a lab note by slug."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> LabNoteService:
        return LabNoteService(mock_session)

    @pytest.fixture
    def sample_note(self) -> LabNote:
        return LabNote(
            id=uuid4(),
            slug="test-note",
            note_type="set_analysis",
            title="Test Note",
            summary="Test summary",
            content="# Test Content",
            author_name="Test Author",
            status="published",
            version=1,
            is_published=True,
            published_at=datetime.now(UTC),
            tags=["meta"],
            is_premium=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

    @pytest.mark.asyncio
    async def test_returns_note_by_slug(
        self, service: LabNoteService, mock_session: AsyncMock, sample_note: LabNote
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_note
        mock_session.execute.return_value = mock_result

        result = await service.get_by_slug("test-note")

        assert result.slug == "test-note"
        assert result.title == "Test Note"

    @pytest.mark.asyncio
    async def test_raises_not_found_when_missing(
        self, service: LabNoteService, mock_session: AsyncMock
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        with pytest.raises(LabNoteNotFoundError):
            await service.get_by_slug("nonexistent")

    @pytest.mark.asyncio
    async def test_raises_on_database_error(
        self, service: LabNoteService, mock_session: AsyncMock
    ) -> None:
        mock_session.execute.side_effect = SQLAlchemyError("DB error")

        with pytest.raises(LabNoteError, match="Failed to get lab note"):
            await service.get_by_slug("test-note")


class TestCreate:
    """Tests for creating lab notes."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        session = AsyncMock()
        session.add = MagicMock()

        async def mock_refresh(obj: LabNote) -> None:
            obj.created_at = datetime.now(UTC)
            obj.updated_at = datetime.now(UTC)

        session.refresh = mock_refresh
        return session

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> LabNoteService:
        return LabNoteService(mock_session)

    @pytest.fixture
    def create_data(self) -> LabNoteCreate:
        return LabNoteCreate(
            note_type="set_analysis",
            title="New Meta Analysis",
            summary="A summary",
            content="# Content",
            author_name="Test Author",
            status="draft",
            is_premium=False,
        )

    @pytest.mark.asyncio
    async def test_creates_note_with_generated_slug(
        self,
        service: LabNoteService,
        mock_session: AsyncMock,
        create_data: LabNoteCreate,
    ) -> None:
        mock_unique_result = MagicMock()
        mock_unique_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_unique_result

        result = await service.create(create_data)

        assert result.slug == "new-meta-analysis"
        assert result.title == "New Meta Analysis"
        assert mock_session.add.call_count == 2  # note + revision

    @pytest.mark.asyncio
    async def test_creates_note_with_provided_slug(
        self,
        service: LabNoteService,
        mock_session: AsyncMock,
        create_data: LabNoteCreate,
    ) -> None:
        create_data.slug = "custom-slug"

        mock_unique_result = MagicMock()
        mock_unique_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_unique_result

        result = await service.create(create_data)

        assert result.slug == "custom-slug"

    @pytest.mark.asyncio
    async def test_sets_published_at_when_status_is_published(
        self,
        service: LabNoteService,
        mock_session: AsyncMock,
        create_data: LabNoteCreate,
    ) -> None:
        create_data.status = "published"

        mock_unique_result = MagicMock()
        mock_unique_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_unique_result

        result = await service.create(create_data)

        assert result.is_published is True
        assert result.published_at is not None

    @pytest.mark.asyncio
    async def test_raises_on_duplicate_slug_integrity_error(
        self,
        service: LabNoteService,
        mock_session: AsyncMock,
        create_data: LabNoteCreate,
    ) -> None:
        mock_unique_result = MagicMock()
        mock_unique_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_unique_result

        mock_session.commit.side_effect = IntegrityError(
            "duplicate", params=None, orig=Exception("slug constraint")
        )

        with pytest.raises(LabNoteDuplicateSlugError):
            await service.create(create_data)

        mock_session.rollback.assert_called_once()


class TestUpdate:
    """Tests for updating lab notes."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        session = AsyncMock()
        session.add = MagicMock()
        return session

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> LabNoteService:
        return LabNoteService(mock_session)

    @pytest.fixture
    def existing_note(self) -> LabNote:
        return LabNote(
            id=uuid4(),
            slug="existing-note",
            note_type="set_analysis",
            title="Existing Note",
            summary="Summary",
            content="# Content",
            author_name="Author",
            status="draft",
            version=1,
            is_published=False,
            published_at=None,
            tags=None,
            is_premium=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

    @pytest.mark.asyncio
    async def test_updates_note_fields(
        self,
        service: LabNoteService,
        mock_session: AsyncMock,
        existing_note: LabNote,
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_note
        mock_session.execute.return_value = mock_result

        update_data = LabNoteUpdate(summary="Updated summary")
        result = await service.update(existing_note.id, update_data)

        assert result.summary == "Updated summary"
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_creates_revision_on_content_change(
        self,
        service: LabNoteService,
        mock_session: AsyncMock,
        existing_note: LabNote,
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_note
        mock_session.execute.return_value = mock_result

        update_data = LabNoteUpdate(content="# New Content")
        await service.update(existing_note.id, update_data)

        assert existing_note.version == 2
        mock_session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_sets_published_at_on_status_change(
        self,
        service: LabNoteService,
        mock_session: AsyncMock,
        existing_note: LabNote,
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_note
        mock_session.execute.return_value = mock_result

        update_data = LabNoteUpdate(status="published")
        result = await service.update(existing_note.id, update_data)

        assert result.is_published is True

    @pytest.mark.asyncio
    async def test_raises_not_found_when_missing(
        self, service: LabNoteService, mock_session: AsyncMock
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        update_data = LabNoteUpdate(summary="Updated")
        with pytest.raises(LabNoteNotFoundError):
            await service.update(uuid4(), update_data)


class TestUpdateStatus:
    """Tests for status transitions."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> LabNoteService:
        return LabNoteService(mock_session)

    @pytest.fixture
    def draft_note(self) -> LabNote:
        return LabNote(
            id=uuid4(),
            slug="draft-note",
            note_type="set_analysis",
            title="Draft Note",
            summary="Summary",
            content="# Content",
            author_name="Author",
            status="draft",
            version=1,
            is_published=False,
            published_at=None,
            tags=None,
            is_premium=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

    @pytest.mark.asyncio
    async def test_transitions_to_published(
        self,
        service: LabNoteService,
        mock_session: AsyncMock,
        draft_note: LabNote,
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = draft_note
        mock_session.execute.return_value = mock_result

        result = await service.update_status(draft_note.id, "published")

        assert result.status == "published"
        assert result.is_published is True

    @pytest.mark.asyncio
    async def test_sets_reviewer_on_review_status(
        self,
        service: LabNoteService,
        mock_session: AsyncMock,
        draft_note: LabNote,
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = draft_note
        mock_session.execute.return_value = mock_result

        user_id = uuid4()
        await service.update_status(draft_note.id, "review", user_id=user_id)

        assert draft_note.reviewer_id == user_id


class TestListRevisions:
    """Tests for listing revisions."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> LabNoteService:
        return LabNoteService(mock_session)

    @pytest.mark.asyncio
    async def test_returns_revisions_for_note(
        self, service: LabNoteService, mock_session: AsyncMock
    ) -> None:
        note_id = uuid4()
        revision = LabNoteRevision(
            id=uuid4(),
            lab_note_id=note_id,
            version=1,
            title="Test",
            content="# Content",
            summary="Summary",
            author_id=None,
            change_description="Initial",
            created_at=datetime.now(UTC),
        )

        mock_note_result = MagicMock()
        mock_note_result.scalar_one_or_none.return_value = note_id

        mock_rev_result = MagicMock()
        mock_rev_result.scalars.return_value.all.return_value = [revision]

        mock_session.execute.side_effect = [mock_note_result, mock_rev_result]

        result = await service.list_revisions(note_id)

        assert len(result) == 1
        assert result[0].version == 1

    @pytest.mark.asyncio
    async def test_raises_not_found_when_note_missing(
        self, service: LabNoteService, mock_session: AsyncMock
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        with pytest.raises(LabNoteNotFoundError):
            await service.list_revisions(uuid4())


class TestDelete:
    """Tests for deleting lab notes."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> LabNoteService:
        return LabNoteService(mock_session)

    @pytest.mark.asyncio
    async def test_deletes_existing_note(
        self, service: LabNoteService, mock_session: AsyncMock
    ) -> None:
        note = LabNote(
            id=uuid4(),
            slug="to-delete",
            note_type="set_analysis",
            title="To Delete",
            summary="Summary",
            content="# Content",
            author_name="Author",
            status="draft",
            version=1,
            is_published=False,
            published_at=None,
            tags=None,
            is_premium=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = note
        mock_session.execute.return_value = mock_result

        result = await service.delete(note.id)

        assert result is True
        mock_session.delete.assert_called_once_with(note)
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_false_when_not_found(
        self, service: LabNoteService, mock_session: AsyncMock
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await service.delete(uuid4())

        assert result is False
        mock_session.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_rollsback_on_error(
        self, service: LabNoteService, mock_session: AsyncMock
    ) -> None:
        note = LabNote(
            id=uuid4(),
            slug="to-delete",
            note_type="set_analysis",
            title="To Delete",
            summary="Summary",
            content="# Content",
            author_name="Author",
            status="draft",
            version=1,
            is_published=False,
            published_at=None,
            tags=None,
            is_premium=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = note
        mock_session.execute.return_value = mock_result
        mock_session.commit.side_effect = SQLAlchemyError("Delete failed")

        with pytest.raises(LabNoteError, match="Failed to delete lab note"):
            await service.delete(note.id)

        mock_session.rollback.assert_called_once()


class TestGetById:
    """Tests for getting a lab note by ID."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> LabNoteService:
        return LabNoteService(mock_session)

    @pytest.fixture
    def sample_note(self) -> LabNote:
        return LabNote(
            id=uuid4(),
            slug="test-note",
            note_type="set_analysis",
            title="Test Note",
            summary="Test summary",
            content="# Test Content",
            author_name="Test Author",
            status="published",
            version=1,
            is_published=True,
            published_at=datetime.now(UTC),
            tags=["meta"],
            is_premium=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

    @pytest.mark.asyncio
    async def test_returns_note_by_id(
        self, service: LabNoteService, mock_session: AsyncMock, sample_note: LabNote
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_note
        mock_session.execute.return_value = mock_result

        result = await service.get_by_id(sample_note.id)

        assert result.title == "Test Note"
        assert result.id == str(sample_note.id)

    @pytest.mark.asyncio
    async def test_raises_not_found(
        self, service: LabNoteService, mock_session: AsyncMock
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        with pytest.raises(LabNoteNotFoundError):
            await service.get_by_id(uuid4())

    @pytest.mark.asyncio
    async def test_raises_on_database_error(
        self, service: LabNoteService, mock_session: AsyncMock
    ) -> None:
        mock_session.execute.side_effect = SQLAlchemyError("DB error")

        with pytest.raises(LabNoteError, match="Failed to get lab note"):
            await service.get_by_id(uuid4())

    @pytest.mark.asyncio
    async def test_unpublished_note_hidden_by_default(
        self, service: LabNoteService, mock_session: AsyncMock
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        with pytest.raises(LabNoteNotFoundError):
            await service.get_by_id(uuid4(), published_only=True)


class TestCreateWithRelatedContent:
    """Tests for create with related_content."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        session = AsyncMock()
        session.add = MagicMock()

        async def mock_refresh(obj: LabNote) -> None:
            obj.created_at = datetime.now(UTC)
            obj.updated_at = datetime.now(UTC)

        session.refresh = mock_refresh
        return session

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> LabNoteService:
        return LabNoteService(mock_session)

    @pytest.mark.asyncio
    async def test_creates_with_related_content(
        self, service: LabNoteService, mock_session: AsyncMock
    ) -> None:
        mock_unique = MagicMock()
        mock_unique.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_unique

        data = LabNoteCreate(
            note_type="set_analysis",
            title="Related Content Test",
            summary="A summary",
            content="# Content",
            author_name="Author",
            status="draft",
            is_premium=False,
            related_content=RelatedContent(
                archetypes=["Charizard ex"],
                cards=["sv09-97"],
                sets=["sv09"],
            ),
        )

        result = await service.create(data)

        assert result.related_content is not None
        assert result.related_content.archetypes == ["Charizard ex"]

    @pytest.mark.asyncio
    async def test_create_general_db_error(
        self, service: LabNoteService, mock_session: AsyncMock
    ) -> None:
        mock_unique = MagicMock()
        mock_unique.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_unique
        mock_session.commit.side_effect = SQLAlchemyError("DB error")

        data = LabNoteCreate(
            note_type="set_analysis",
            title="Error Test",
            summary="A summary",
            content="# Content",
            author_name="Author",
            status="draft",
            is_premium=False,
        )

        with pytest.raises(LabNoteError, match="Failed to create lab note"):
            await service.create(data)

        mock_session.rollback.assert_called_once()


class TestUpdateEdgeCases:
    """Edge cases for update method."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        session = AsyncMock()
        session.add = MagicMock()
        return session

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> LabNoteService:
        return LabNoteService(mock_session)

    @pytest.fixture
    def existing_note(self) -> LabNote:
        return LabNote(
            id=uuid4(),
            slug="existing-note",
            note_type="set_analysis",
            title="Existing Note",
            summary="Summary",
            content="# Content",
            author_name="Author",
            status="draft",
            version=1,
            is_published=False,
            published_at=None,
            tags=None,
            is_premium=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

    @pytest.mark.asyncio
    async def test_title_change_creates_revision(
        self,
        service: LabNoteService,
        mock_session: AsyncMock,
        existing_note: LabNote,
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_note
        mock_session.execute.return_value = mock_result

        update_data = LabNoteUpdate(title="Updated Title")
        await service.update(existing_note.id, update_data)

        assert existing_note.version == 2
        mock_session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_is_published_true_syncs_status(
        self,
        service: LabNoteService,
        mock_session: AsyncMock,
        existing_note: LabNote,
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_note
        mock_session.execute.return_value = mock_result

        update_data = LabNoteUpdate(is_published=True)
        result = await service.update(existing_note.id, update_data)

        assert result.is_published is True
        assert result.status == "published"

    @pytest.mark.asyncio
    async def test_is_published_false_sets_draft(
        self,
        service: LabNoteService,
        mock_session: AsyncMock,
        existing_note: LabNote,
    ) -> None:
        existing_note.status = "published"
        existing_note.is_published = True
        existing_note.published_at = datetime.now(UTC)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_note
        mock_session.execute.return_value = mock_result

        update_data = LabNoteUpdate(is_published=False)
        result = await service.update(existing_note.id, update_data)

        assert result.is_published is False
        assert result.status == "draft"

    @pytest.mark.asyncio
    async def test_update_with_related_content(
        self,
        service: LabNoteService,
        mock_session: AsyncMock,
        existing_note: LabNote,
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_note
        mock_session.execute.return_value = mock_result

        update_data = LabNoteUpdate(
            related_content=RelatedContent(
                archetypes=["Dragapult ex"],
                cards=[],
                sets=[],
            ),
        )
        result = await service.update(existing_note.id, update_data)

        assert result.related_content is not None
        assert result.related_content.archetypes == ["Dragapult ex"]

    @pytest.mark.asyncio
    async def test_update_commit_error_rolls_back(
        self,
        service: LabNoteService,
        mock_session: AsyncMock,
        existing_note: LabNote,
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_note
        mock_session.execute.return_value = mock_result
        mock_session.commit.side_effect = SQLAlchemyError("Commit failed")

        update_data = LabNoteUpdate(summary="New summary")
        with pytest.raises(LabNoteError, match="Failed to update lab note"):
            await service.update(existing_note.id, update_data)

        mock_session.rollback.assert_called_once()


class TestUpdateStatusEdgeCases:
    """Edge cases for update_status method."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> LabNoteService:
        return LabNoteService(mock_session)

    @pytest.mark.asyncio
    async def test_not_found(
        self, service: LabNoteService, mock_session: AsyncMock
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        with pytest.raises(LabNoteNotFoundError):
            await service.update_status(uuid4(), "published")

    @pytest.mark.asyncio
    async def test_db_error_on_get(
        self, service: LabNoteService, mock_session: AsyncMock
    ) -> None:
        mock_session.execute.side_effect = SQLAlchemyError("DB error")

        with pytest.raises(LabNoteError, match="Failed to update lab note status"):
            await service.update_status(uuid4(), "published")

    @pytest.mark.asyncio
    async def test_db_error_on_commit(
        self, service: LabNoteService, mock_session: AsyncMock
    ) -> None:
        note = LabNote(
            id=uuid4(),
            slug="test",
            note_type="set_analysis",
            title="Test",
            summary="Summary",
            content="# Content",
            author_name="Author",
            status="draft",
            version=1,
            is_published=False,
            published_at=None,
            tags=None,
            is_premium=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = note
        mock_session.execute.return_value = mock_result
        mock_session.commit.side_effect = SQLAlchemyError("Commit failed")

        with pytest.raises(LabNoteError, match="Failed to update lab note status"):
            await service.update_status(note.id, "published")

        mock_session.rollback.assert_called_once()


class TestListNotesEdgeCases:
    """Edge cases for list_notes method."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> LabNoteService:
        return LabNoteService(mock_session)

    @pytest.mark.asyncio
    async def test_pagination_has_next(
        self, service: LabNoteService, mock_session: AsyncMock
    ) -> None:
        mock_count = MagicMock()
        mock_count.scalar.return_value = 25
        mock_notes = MagicMock()
        mock_notes.scalars.return_value.all.return_value = []
        mock_session.execute.side_effect = [mock_count, mock_notes]

        result = await service.list_notes(page=1, limit=10)

        assert result.has_next is True
        assert result.has_prev is False

    @pytest.mark.asyncio
    async def test_pagination_has_prev(
        self, service: LabNoteService, mock_session: AsyncMock
    ) -> None:
        mock_count = MagicMock()
        mock_count.scalar.return_value = 25
        mock_notes = MagicMock()
        mock_notes.scalars.return_value.all.return_value = []
        mock_session.execute.side_effect = [mock_count, mock_notes]

        result = await service.list_notes(page=2, limit=10)

        assert result.has_prev is True

    @pytest.mark.asyncio
    async def test_filters_by_status(
        self, service: LabNoteService, mock_session: AsyncMock
    ) -> None:
        mock_count = MagicMock()
        mock_count.scalar.return_value = 0
        mock_notes = MagicMock()
        mock_notes.scalars.return_value.all.return_value = []
        mock_session.execute.side_effect = [mock_count, mock_notes]

        result = await service.list_notes(status="draft")

        assert result.total == 0

    @pytest.mark.asyncio
    async def test_published_only_false(
        self, service: LabNoteService, mock_session: AsyncMock
    ) -> None:
        mock_count = MagicMock()
        mock_count.scalar.return_value = 0
        mock_notes = MagicMock()
        mock_notes.scalars.return_value.all.return_value = []
        mock_session.execute.side_effect = [mock_count, mock_notes]

        result = await service.list_notes(published_only=False)

        assert result.total == 0

    @pytest.mark.asyncio
    async def test_db_error_on_list_query(
        self, service: LabNoteService, mock_session: AsyncMock
    ) -> None:
        mock_count = MagicMock()
        mock_count.scalar.return_value = 5
        mock_session.execute.side_effect = [
            mock_count,
            SQLAlchemyError("List failed"),
        ]

        with pytest.raises(LabNoteError, match="Failed to list lab notes"):
            await service.list_notes()


class TestListRevisionsEdgeCases:
    """Edge cases for list_revisions method."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> LabNoteService:
        return LabNoteService(mock_session)

    @pytest.mark.asyncio
    async def test_db_error_on_note_check(
        self, service: LabNoteService, mock_session: AsyncMock
    ) -> None:
        mock_session.execute.side_effect = SQLAlchemyError("DB error")

        with pytest.raises(LabNoteError, match="Failed to list revisions"):
            await service.list_revisions(uuid4())

    @pytest.mark.asyncio
    async def test_db_error_on_revision_query(
        self, service: LabNoteService, mock_session: AsyncMock
    ) -> None:
        note_id = uuid4()
        mock_note_result = MagicMock()
        mock_note_result.scalar_one_or_none.return_value = note_id

        mock_session.execute.side_effect = [
            mock_note_result,
            SQLAlchemyError("Revision query failed"),
        ]

        with pytest.raises(LabNoteError, match="Failed to list revisions"):
            await service.list_revisions(note_id)


class TestDeleteEdgeCases:
    """Edge cases for delete method."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> LabNoteService:
        return LabNoteService(mock_session)

    @pytest.mark.asyncio
    async def test_db_error_on_get(
        self, service: LabNoteService, mock_session: AsyncMock
    ) -> None:
        mock_session.execute.side_effect = SQLAlchemyError("DB error")

        with pytest.raises(LabNoteError, match="Failed to delete lab note"):
            await service.delete(uuid4())
