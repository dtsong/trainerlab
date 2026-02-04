"""Tests for lab notes router endpoints."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from src.db.database import get_db
from src.main import app
from src.schemas.lab_note import (
    LabNoteListResponse,
    LabNoteResponse,
    LabNoteSummaryResponse,
)
from src.services.lab_note_service import (
    LabNoteError,
    LabNoteNotFoundError,
)


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
        with patch("src.routers.lab_notes.LabNoteService") as MockService:
            mock_service = AsyncMock()
            mock_service.list_notes.return_value = mock_list_response
            MockService.return_value = mock_service

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
        with patch("src.routers.lab_notes.LabNoteService") as MockService:
            mock_service = AsyncMock()
            mock_service.list_notes.return_value = mock_list_response
            MockService.return_value = mock_service

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
        with patch("src.routers.lab_notes.LabNoteService") as MockService:
            mock_service = AsyncMock()
            mock_service.list_notes.return_value = mock_list_response
            MockService.return_value = mock_service

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
        with patch("src.routers.lab_notes.LabNoteService") as MockService:
            mock_service = AsyncMock()
            mock_service.list_notes.return_value = mock_list_response
            MockService.return_value = mock_service

            response = client.get(
                "/api/v1/lab-notes",
                params={"page": 2, "limit": 10},
            )

        assert response.status_code == status.HTTP_200_OK
        call_kwargs = mock_service.list_notes.call_args.kwargs
        assert call_kwargs["page"] == 2
        assert call_kwargs["limit"] == 10

    def test_returns_503_on_service_error(self, client: TestClient) -> None:
        with patch("src.routers.lab_notes.LabNoteService") as MockService:
            mock_service = AsyncMock()
            mock_service.list_notes.side_effect = LabNoteError("DB error")
            MockService.return_value = mock_service

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
        with patch("src.routers.lab_notes.LabNoteService") as MockService:
            mock_service = AsyncMock()
            mock_service.get_by_slug.return_value = mock_lab_note_response
            MockService.return_value = mock_service

            response = client.get("/api/v1/lab-notes/charizard-meta-analysis")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["slug"] == "charizard-meta-analysis"

    def test_returns_404_when_not_found(self, client: TestClient) -> None:
        with patch("src.routers.lab_notes.LabNoteService") as MockService:
            mock_service = AsyncMock()
            mock_service.get_by_slug.side_effect = LabNoteNotFoundError("Not found")
            MockService.return_value = mock_service

            response = client.get("/api/v1/lab-notes/nonexistent")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_returns_503_on_service_error(self, client: TestClient) -> None:
        with patch("src.routers.lab_notes.LabNoteService") as MockService:
            mock_service = AsyncMock()
            mock_service.get_by_slug.side_effect = LabNoteError("DB error")
            MockService.return_value = mock_service

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
