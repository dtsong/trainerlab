"""Tests for lab notes router endpoints."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from src.db.database import get_db
from src.dependencies.admin import require_admin
from src.dependencies.auth import get_current_user
from src.main import app
from src.models.user import User
from src.schemas.lab_note import (
    LabNoteListResponse,
    LabNoteResponse,
    LabNoteRevisionResponse,
    LabNoteSummaryResponse,
)
from src.services.lab_note_service import (
    LabNoteDuplicateSlugError,
    LabNoteError,
    LabNoteNotFoundError,
)


def _make_mock_admin_user() -> MagicMock:
    """Create a mock admin user for dependency overrides."""
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.email = "admin@trainerlab.gg"
    user.display_name = "Admin User"
    user.avatar_url = None
    user.preferences = {}
    user.created_at = datetime.now(UTC)
    user.updated_at = datetime.now(UTC)
    return user


@pytest.fixture
def mock_lab_note_summary() -> LabNoteSummaryResponse:
    """Create a mock lab note summary."""
    return LabNoteSummaryResponse(
        id=str(uuid4()),
        slug="charizard-meta-analysis",
        note_type="set_analysis",
        title="Charizard ex Meta Analysis",
        summary="Deep dive into the Charizard ex archetype",
        author_name="Test Author",
        status="published",
        is_published=True,
        published_at=datetime.now(UTC),
        featured_image_url=None,
        tags=["meta", "charizard"],
        is_premium=False,
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def mock_lab_note_response() -> LabNoteResponse:
    """Create a mock lab note response."""
    return LabNoteResponse(
        id=str(uuid4()),
        slug="charizard-meta-analysis",
        note_type="set_analysis",
        title="Charizard ex Meta Analysis",
        summary="Deep dive into the Charizard ex archetype",
        content="# Charizard ex Analysis\n\nDetailed content here...",
        author_name="Test Author",
        status="published",
        version=1,
        is_published=True,
        published_at=datetime.now(UTC),
        meta_description="Analysis of Charizard ex in the current meta",
        featured_image_url=None,
        tags=["meta", "charizard"],
        related_content=None,
        is_premium=False,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def mock_list_response(
    mock_lab_note_summary: LabNoteSummaryResponse,
) -> LabNoteListResponse:
    """Create a mock list response."""
    return LabNoteListResponse(
        items=[mock_lab_note_summary],
        total=1,
        page=1,
        limit=20,
        has_next=False,
        has_prev=False,
    )


class TestListLabNotes:
    """Tests for GET /api/v1/lab-notes."""

    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def client(self, mock_db: AsyncMock) -> TestClient:
        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        yield TestClient(app)
        app.dependency_overrides.clear()

    def test_returns_published_lab_notes(
        self,
        client: TestClient,
        mock_list_response: LabNoteListResponse,
    ) -> None:
        with patch("src.routers.lab_notes.LabNoteService") as mock_service_cls:
            mock_service = AsyncMock()
            mock_service.list_notes.return_value = mock_list_response
            mock_service_cls.return_value = mock_service

            response = client.get("/api/v1/lab-notes")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1

    def test_filters_by_note_type(
        self,
        client: TestClient,
        mock_list_response: LabNoteListResponse,
    ) -> None:
        with patch("src.routers.lab_notes.LabNoteService") as mock_service_cls:
            mock_service = AsyncMock()
            mock_service.list_notes.return_value = mock_list_response
            mock_service_cls.return_value = mock_service

            response = client.get(
                "/api/v1/lab-notes",
                params={"note_type": "set_analysis"},
            )

        assert response.status_code == status.HTTP_200_OK
        mock_service.list_notes.assert_called_once()
        call_kwargs = mock_service.list_notes.call_args.kwargs
        assert call_kwargs["note_type"] == "set_analysis"

    def test_filters_by_tag(
        self,
        client: TestClient,
        mock_list_response: LabNoteListResponse,
    ) -> None:
        with patch("src.routers.lab_notes.LabNoteService") as mock_service_cls:
            mock_service = AsyncMock()
            mock_service.list_notes.return_value = mock_list_response
            mock_service_cls.return_value = mock_service

            response = client.get(
                "/api/v1/lab-notes",
                params={"tag": "meta"},
            )

        assert response.status_code == status.HTTP_200_OK
        call_kwargs = mock_service.list_notes.call_args.kwargs
        assert call_kwargs["tag"] == "meta"

    def test_paginates_results(
        self,
        client: TestClient,
        mock_list_response: LabNoteListResponse,
    ) -> None:
        with patch("src.routers.lab_notes.LabNoteService") as mock_service_cls:
            mock_service = AsyncMock()
            mock_service.list_notes.return_value = mock_list_response
            mock_service_cls.return_value = mock_service

            response = client.get(
                "/api/v1/lab-notes",
                params={"page": 2, "limit": 10},
            )

        assert response.status_code == status.HTTP_200_OK
        call_kwargs = mock_service.list_notes.call_args.kwargs
        assert call_kwargs["page"] == 2
        assert call_kwargs["limit"] == 10

    def test_returns_503_on_service_error(self, client: TestClient) -> None:
        with patch("src.routers.lab_notes.LabNoteService") as mock_service_cls:
            mock_service = AsyncMock()
            mock_service.list_notes.side_effect = LabNoteError("DB error")
            mock_service_cls.return_value = mock_service

            response = client.get("/api/v1/lab-notes")

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE


class TestGetLabNoteBySlug:
    """Tests for GET /api/v1/lab-notes/{slug}."""

    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def client(self, mock_db: AsyncMock) -> TestClient:
        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        yield TestClient(app)
        app.dependency_overrides.clear()

    def test_returns_lab_note(
        self,
        client: TestClient,
        mock_lab_note_response: LabNoteResponse,
    ) -> None:
        with patch("src.routers.lab_notes.LabNoteService") as mock_service_cls:
            mock_service = AsyncMock()
            mock_service.get_by_slug.return_value = mock_lab_note_response
            mock_service_cls.return_value = mock_service

            response = client.get("/api/v1/lab-notes/charizard-meta-analysis")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["slug"] == "charizard-meta-analysis"

    def test_returns_404_when_not_found(self, client: TestClient) -> None:
        with patch("src.routers.lab_notes.LabNoteService") as mock_service_cls:
            mock_service = AsyncMock()
            mock_service.get_by_slug.side_effect = LabNoteNotFoundError("Not found")
            mock_service_cls.return_value = mock_service

            response = client.get("/api/v1/lab-notes/nonexistent")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_returns_503_on_service_error(self, client: TestClient) -> None:
        with patch("src.routers.lab_notes.LabNoteService") as mock_service_cls:
            mock_service = AsyncMock()
            mock_service.get_by_slug.side_effect = LabNoteError("DB error")
            mock_service_cls.return_value = mock_service

            response = client.get("/api/v1/lab-notes/some-slug")

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE


class TestAdminListLabNotes:
    """Tests for GET /api/v1/lab-notes/admin/all."""

    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def client(self, mock_db: AsyncMock) -> TestClient:
        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        yield TestClient(app)
        app.dependency_overrides.clear()

    def test_requires_admin_auth(self, client: TestClient) -> None:
        response = client.get("/api/v1/lab-notes/admin/all")

        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]


class TestCreateLabNote:
    """Tests for POST /api/v1/lab-notes."""

    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def client(self, mock_db: AsyncMock) -> TestClient:
        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        yield TestClient(app)
        app.dependency_overrides.clear()

    def test_requires_admin_auth(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/lab-notes",
            json={
                "note_type": "set_analysis",
                "title": "New Note",
                "summary": "Summary",
                "content": "Content",
                "author_name": "Author",
                "status": "draft",
            },
        )

        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]


class TestUpdateLabNote:
    """Tests for PATCH /api/v1/lab-notes/{note_id}."""

    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def client(self, mock_db: AsyncMock) -> TestClient:
        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        yield TestClient(app)
        app.dependency_overrides.clear()

    def test_requires_admin_auth(self, client: TestClient) -> None:
        note_id = str(uuid4())
        response = client.patch(
            f"/api/v1/lab-notes/{note_id}",
            json={"title": "Updated Title"},
        )

        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]


class TestDeleteLabNote:
    """Tests for DELETE /api/v1/lab-notes/{note_id}."""

    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def client(self, mock_db: AsyncMock) -> TestClient:
        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        yield TestClient(app)
        app.dependency_overrides.clear()

    def test_requires_admin_auth(self, client: TestClient) -> None:
        note_id = str(uuid4())
        response = client.delete(f"/api/v1/lab-notes/{note_id}")

        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]


class TestListRevisions:
    """Tests for GET /api/v1/lab-notes/{note_id}/revisions."""

    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def client(self, mock_db: AsyncMock) -> TestClient:
        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        yield TestClient(app)
        app.dependency_overrides.clear()

    def test_requires_admin_auth(self, client: TestClient) -> None:
        note_id = str(uuid4())
        response = client.get(f"/api/v1/lab-notes/{note_id}/revisions")

        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]


# ---------------------------------------------------------------------------
# Admin-authenticated endpoint tests
# These tests bypass admin auth to test actual endpoint logic.
# ---------------------------------------------------------------------------


@pytest.fixture
def admin_mock_db() -> AsyncMock:
    """DB session mock for admin tests."""
    return AsyncMock()


@pytest.fixture
def admin_user() -> MagicMock:
    """Admin user mock."""
    return _make_mock_admin_user()


@pytest.fixture
def admin_client(admin_mock_db: AsyncMock, admin_user: MagicMock) -> TestClient:
    """Test client with admin auth bypassed."""

    async def override_get_db():
        yield admin_mock_db

    async def override_get_current_user():
        return admin_user

    async def override_require_admin():
        return admin_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[require_admin] = override_require_admin

    yield TestClient(app)
    app.dependency_overrides.clear()


class TestAdminListAllLabNotesAuthenticated:
    """Tests for GET /api/v1/lab-notes/admin/all with auth bypassed."""

    def test_returns_all_notes_including_unpublished(
        self, admin_client: TestClient
    ) -> None:
        mock_response = LabNoteListResponse(
            items=[
                LabNoteSummaryResponse(
                    id=str(uuid4()),
                    slug="published-note",
                    note_type="weekly_report",
                    title="Published Note",
                    summary=None,
                    author_name=None,
                    status="published",
                    is_published=True,
                    published_at=datetime.now(UTC),
                    featured_image_url=None,
                    tags=None,
                    is_premium=False,
                    created_at=datetime.now(UTC),
                ),
                LabNoteSummaryResponse(
                    id=str(uuid4()),
                    slug="draft-note",
                    note_type="jp_dispatch",
                    title="Draft Note",
                    summary=None,
                    author_name=None,
                    status="draft",
                    is_published=False,
                    published_at=None,
                    featured_image_url=None,
                    tags=None,
                    is_premium=False,
                    created_at=datetime.now(UTC),
                ),
            ],
            total=2,
            page=1,
            limit=20,
            has_next=False,
            has_prev=False,
        )

        with patch("src.routers.lab_notes.LabNoteService") as mock_service_cls:
            mock_service = AsyncMock()
            mock_service.list_notes.return_value = mock_response
            mock_service_cls.return_value = mock_service

            response = admin_client.get("/api/v1/lab-notes/admin/all")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 2

    def test_filters_by_status(self, admin_client: TestClient) -> None:
        mock_response = LabNoteListResponse(
            items=[], total=0, page=1, limit=20, has_next=False, has_prev=False
        )

        with patch("src.routers.lab_notes.LabNoteService") as mock_service_cls:
            mock_service = AsyncMock()
            mock_service.list_notes.return_value = mock_response
            mock_service_cls.return_value = mock_service

            response = admin_client.get("/api/v1/lab-notes/admin/all?status=draft")

        assert response.status_code == status.HTTP_200_OK
        call_kwargs = mock_service.list_notes.call_args.kwargs
        assert call_kwargs["status"] == "draft"
        assert call_kwargs["published_only"] is False

    def test_returns_503_on_service_error(self, admin_client: TestClient) -> None:
        with patch("src.routers.lab_notes.LabNoteService") as mock_service_cls:
            mock_service = AsyncMock()
            mock_service.list_notes.side_effect = LabNoteError("DB error")
            mock_service_cls.return_value = mock_service

            response = admin_client.get("/api/v1/lab-notes/admin/all")

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE


class TestAdminGetNoteByIdAuthenticated:
    """Tests for GET /api/v1/lab-notes/admin/{note_id} with auth bypassed."""

    def test_returns_note_by_id(self, admin_client: TestClient) -> None:
        note_id = uuid4()
        now = datetime.now(UTC)
        mock_note = LabNoteResponse(
            id=str(note_id),
            slug="test-note",
            note_type="weekly_report",
            title="Test Note",
            summary=None,
            content="# Content",
            author_name=None,
            status="draft",
            version=1,
            is_published=False,
            published_at=None,
            meta_description=None,
            featured_image_url=None,
            tags=None,
            related_content=None,
            is_premium=False,
            created_at=now,
            updated_at=now,
        )

        with patch("src.routers.lab_notes.LabNoteService") as mock_service_cls:
            mock_service = AsyncMock()
            mock_service.get_by_id.return_value = mock_note
            mock_service_cls.return_value = mock_service

            response = admin_client.get(f"/api/v1/lab-notes/admin/{note_id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(note_id)

    def test_returns_404_when_not_found(self, admin_client: TestClient) -> None:
        note_id = uuid4()

        with patch("src.routers.lab_notes.LabNoteService") as mock_service_cls:
            mock_service = AsyncMock()
            mock_service.get_by_id.side_effect = LabNoteNotFoundError("not found")
            mock_service_cls.return_value = mock_service

            response = admin_client.get(f"/api/v1/lab-notes/admin/{note_id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_returns_503_on_service_error(self, admin_client: TestClient) -> None:
        note_id = uuid4()

        with patch("src.routers.lab_notes.LabNoteService") as mock_service_cls:
            mock_service = AsyncMock()
            mock_service.get_by_id.side_effect = LabNoteError("DB error")
            mock_service_cls.return_value = mock_service

            response = admin_client.get(f"/api/v1/lab-notes/admin/{note_id}")

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE


class TestAdminCreateLabNoteAuthenticated:
    """Tests for POST /api/v1/lab-notes with auth bypassed."""

    def test_creates_lab_note(self, admin_client: TestClient) -> None:
        now = datetime.now(UTC)
        mock_note = LabNoteResponse(
            id=str(uuid4()),
            slug="new-note",
            note_type="weekly_report",
            title="New Note",
            summary=None,
            content="# New Note\n\nContent.",
            author_name=None,
            status="draft",
            version=1,
            is_published=False,
            published_at=None,
            meta_description=None,
            featured_image_url=None,
            tags=None,
            related_content=None,
            is_premium=False,
            created_at=now,
            updated_at=now,
        )

        with patch("src.routers.lab_notes.LabNoteService") as mock_service_cls:
            mock_service = AsyncMock()
            mock_service.create.return_value = mock_note
            mock_service_cls.return_value = mock_service

            response = admin_client.post(
                "/api/v1/lab-notes",
                json={
                    "note_type": "weekly_report",
                    "title": "New Note",
                    "content": "# New Note\n\nContent.",
                },
            )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == "New Note"

    def test_returns_409_on_duplicate_slug(self, admin_client: TestClient) -> None:
        with patch("src.routers.lab_notes.LabNoteService") as mock_service_cls:
            mock_service = AsyncMock()
            mock_service.create.side_effect = LabNoteDuplicateSlugError("duplicate")
            mock_service_cls.return_value = mock_service

            response = admin_client.post(
                "/api/v1/lab-notes",
                json={
                    "note_type": "weekly_report",
                    "title": "Existing Note",
                    "content": "Content.",
                    "slug": "existing-note",
                },
            )

        assert response.status_code == status.HTTP_409_CONFLICT

    def test_returns_503_on_service_error(self, admin_client: TestClient) -> None:
        with patch("src.routers.lab_notes.LabNoteService") as mock_service_cls:
            mock_service = AsyncMock()
            mock_service.create.side_effect = LabNoteError("DB error")
            mock_service_cls.return_value = mock_service

            response = admin_client.post(
                "/api/v1/lab-notes",
                json={
                    "note_type": "weekly_report",
                    "title": "Test",
                    "content": "Content.",
                },
            )

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE


class TestAdminUpdateLabNoteAuthenticated:
    """Tests for PATCH /api/v1/lab-notes/{note_id} with auth bypassed."""

    def test_updates_lab_note(self, admin_client: TestClient) -> None:
        note_id = uuid4()
        now = datetime.now(UTC)
        mock_note = LabNoteResponse(
            id=str(note_id),
            slug="test-note",
            note_type="weekly_report",
            title="Updated Title",
            summary=None,
            content="# Content",
            author_name=None,
            status="draft",
            version=2,
            is_published=False,
            published_at=None,
            meta_description=None,
            featured_image_url=None,
            tags=None,
            related_content=None,
            is_premium=False,
            created_at=now,
            updated_at=now,
        )

        with patch("src.routers.lab_notes.LabNoteService") as mock_service_cls:
            mock_service = AsyncMock()
            mock_service.update.return_value = mock_note
            mock_service_cls.return_value = mock_service

            response = admin_client.patch(
                f"/api/v1/lab-notes/{note_id}",
                json={"title": "Updated Title"},
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Updated Title"

    def test_returns_404_when_not_found(self, admin_client: TestClient) -> None:
        note_id = uuid4()

        with patch("src.routers.lab_notes.LabNoteService") as mock_service_cls:
            mock_service = AsyncMock()
            mock_service.update.side_effect = LabNoteNotFoundError("not found")
            mock_service_cls.return_value = mock_service

            response = admin_client.patch(
                f"/api/v1/lab-notes/{note_id}",
                json={"title": "Updated"},
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_returns_503_on_service_error(self, admin_client: TestClient) -> None:
        note_id = uuid4()

        with patch("src.routers.lab_notes.LabNoteService") as mock_service_cls:
            mock_service = AsyncMock()
            mock_service.update.side_effect = LabNoteError("DB error")
            mock_service_cls.return_value = mock_service

            response = admin_client.patch(
                f"/api/v1/lab-notes/{note_id}",
                json={"title": "Updated"},
            )

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE


class TestAdminUpdateStatusAuthenticated:
    """Tests for PATCH /api/v1/lab-notes/{note_id}/status with auth bypassed."""

    def test_updates_status(self, admin_client: TestClient) -> None:
        note_id = uuid4()
        now = datetime.now(UTC)
        mock_note = LabNoteResponse(
            id=str(note_id),
            slug="test-note",
            note_type="weekly_report",
            title="Test Note",
            summary=None,
            content="# Content",
            author_name=None,
            status="published",
            version=1,
            is_published=True,
            published_at=now,
            meta_description=None,
            featured_image_url=None,
            tags=None,
            related_content=None,
            is_premium=False,
            created_at=now,
            updated_at=now,
        )

        with patch("src.routers.lab_notes.LabNoteService") as mock_service_cls:
            mock_service = AsyncMock()
            mock_service.update_status.return_value = mock_note
            mock_service_cls.return_value = mock_service

            response = admin_client.patch(
                f"/api/v1/lab-notes/{note_id}/status",
                json={"status": "published"},
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "published"

    def test_returns_404_when_not_found(self, admin_client: TestClient) -> None:
        note_id = uuid4()

        with patch("src.routers.lab_notes.LabNoteService") as mock_service_cls:
            mock_service = AsyncMock()
            mock_service.update_status.side_effect = LabNoteNotFoundError("not found")
            mock_service_cls.return_value = mock_service

            response = admin_client.patch(
                f"/api/v1/lab-notes/{note_id}/status",
                json={"status": "published"},
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_returns_503_on_service_error(self, admin_client: TestClient) -> None:
        note_id = uuid4()

        with patch("src.routers.lab_notes.LabNoteService") as mock_service_cls:
            mock_service = AsyncMock()
            mock_service.update_status.side_effect = LabNoteError("DB error")
            mock_service_cls.return_value = mock_service

            response = admin_client.patch(
                f"/api/v1/lab-notes/{note_id}/status",
                json={"status": "published"},
            )

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_rejects_invalid_status(self, admin_client: TestClient) -> None:
        note_id = uuid4()

        response = admin_client.patch(
            f"/api/v1/lab-notes/{note_id}/status",
            json={"status": "invalid_status"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestAdminListRevisionsAuthenticated:
    """Tests for GET /api/v1/lab-notes/{note_id}/revisions with auth bypassed."""

    def test_returns_revisions(self, admin_client: TestClient) -> None:
        note_id = uuid4()
        now = datetime.now(UTC)
        mock_revisions = [
            LabNoteRevisionResponse(
                id=str(uuid4()),
                lab_note_id=str(note_id),
                version=2,
                title="Updated Title",
                content="Updated content",
                summary=None,
                author_id=None,
                change_description="Updated title",
                created_at=now,
            ),
            LabNoteRevisionResponse(
                id=str(uuid4()),
                lab_note_id=str(note_id),
                version=1,
                title="Original Title",
                content="Original content",
                summary=None,
                author_id=None,
                change_description="Initial version",
                created_at=now,
            ),
        ]

        with patch("src.routers.lab_notes.LabNoteService") as mock_service_cls:
            mock_service = AsyncMock()
            mock_service.list_revisions.return_value = mock_revisions
            mock_service_cls.return_value = mock_service

            response = admin_client.get(f"/api/v1/lab-notes/{note_id}/revisions")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        assert data[0]["version"] == 2

    def test_returns_404_when_not_found(self, admin_client: TestClient) -> None:
        note_id = uuid4()

        with patch("src.routers.lab_notes.LabNoteService") as mock_service_cls:
            mock_service = AsyncMock()
            mock_service.list_revisions.side_effect = LabNoteNotFoundError("not found")
            mock_service_cls.return_value = mock_service

            response = admin_client.get(f"/api/v1/lab-notes/{note_id}/revisions")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_returns_503_on_service_error(self, admin_client: TestClient) -> None:
        note_id = uuid4()

        with patch("src.routers.lab_notes.LabNoteService") as mock_service_cls:
            mock_service = AsyncMock()
            mock_service.list_revisions.side_effect = LabNoteError("DB error")
            mock_service_cls.return_value = mock_service

            response = admin_client.get(f"/api/v1/lab-notes/{note_id}/revisions")

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE


class TestAdminDeleteLabNoteAuthenticated:
    """Tests for DELETE /api/v1/lab-notes/{note_id} with auth bypassed."""

    def test_deletes_lab_note(self, admin_client: TestClient) -> None:
        note_id = uuid4()

        with patch("src.routers.lab_notes.LabNoteService") as mock_service_cls:
            mock_service = AsyncMock()
            mock_service.delete.return_value = True
            mock_service_cls.return_value = mock_service

            response = admin_client.delete(f"/api/v1/lab-notes/{note_id}")

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_returns_404_when_not_found(self, admin_client: TestClient) -> None:
        note_id = uuid4()

        with patch("src.routers.lab_notes.LabNoteService") as mock_service_cls:
            mock_service = AsyncMock()
            mock_service.delete.return_value = False
            mock_service_cls.return_value = mock_service

            response = admin_client.delete(f"/api/v1/lab-notes/{note_id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_returns_503_on_service_error(self, admin_client: TestClient) -> None:
        note_id = uuid4()

        with patch("src.routers.lab_notes.LabNoteService") as mock_service_cls:
            mock_service = AsyncMock()
            mock_service.delete.side_effect = LabNoteError("DB error")
            mock_service_cls.return_value = mock_service

            response = admin_client.delete(f"/api/v1/lab-notes/{note_id}")

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
