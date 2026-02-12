"""Tests for users router."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.db.database import get_db
from src.dependencies.auth import get_current_user
from src.main import app
from src.models.user import User


class TestGetCurrentUserInfo:
    """Tests for GET /api/v1/users/me."""

    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def mock_user(self) -> MagicMock:
        user = MagicMock(spec=User)
        user.id = uuid4()
        user.email = "testuser@trainerlab.gg"
        user.display_name = "Test User"
        user.avatar_url = "https://example.com/avatar.png"
        user.is_beta_tester = False
        user.is_creator = False
        user.is_subscriber = False
        user.preferences = {"theme": "dark"}
        user.created_at = datetime.now(UTC)
        user.updated_at = datetime.now(UTC)
        return user

    @pytest.fixture
    def client(self, mock_db: AsyncMock, mock_user: MagicMock) -> TestClient:
        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = lambda: mock_user
        yield TestClient(app)
        app.dependency_overrides.clear()

    @pytest.fixture
    def unauthed_client(self, mock_db: AsyncMock) -> TestClient:
        """Client without auth override (uses real auth dependency)."""

        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        # Do not override get_current_user so auth is enforced
        yield TestClient(app)
        app.dependency_overrides.clear()

    def test_returns_current_user(
        self, client: TestClient, mock_user: MagicMock
    ) -> None:
        """Test that GET /me returns the authenticated user's profile."""
        response = client.get("/api/v1/users/me")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "testuser@trainerlab.gg"
        assert data["display_name"] == "Test User"
        assert data["avatar_url"] == "https://example.com/avatar.png"

    def test_returns_user_id_as_string(
        self, client: TestClient, mock_user: MagicMock
    ) -> None:
        """Test that user ID is serialized as a string in the response."""
        response = client.get("/api/v1/users/me")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(mock_user.id)

    def test_returns_preferences_in_response(
        self, client: TestClient, mock_user: MagicMock
    ) -> None:
        """Test that preferences dict is included in the response."""
        response = client.get("/api/v1/users/me")
        assert response.status_code == 200
        data = response.json()
        assert data["preferences"] == {"theme": "dark"}

    def test_returns_401_without_auth(self, unauthed_client: TestClient) -> None:
        """Test that 401 is returned when no auth header is provided."""
        response = unauthed_client.get("/api/v1/users/me")
        assert response.status_code == 401


class TestGetUserPreferences:
    """Tests for GET /api/v1/users/me/preferences."""

    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def mock_user(self) -> MagicMock:
        user = MagicMock(spec=User)
        user.id = uuid4()
        user.email = "testuser@trainerlab.gg"
        user.display_name = "Test User"
        user.avatar_url = None
        user.is_beta_tester = False
        user.is_creator = False
        user.is_subscriber = False
        user.preferences = {"theme": "dark", "default_format": "standard"}
        user.created_at = datetime.now(UTC)
        user.updated_at = datetime.now(UTC)
        return user

    @pytest.fixture
    def client(self, mock_db: AsyncMock, mock_user: MagicMock) -> TestClient:
        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = lambda: mock_user
        yield TestClient(app)
        app.dependency_overrides.clear()

    @pytest.fixture
    def unauthed_client(self, mock_db: AsyncMock) -> TestClient:
        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        yield TestClient(app)
        app.dependency_overrides.clear()

    def test_returns_user_preferences(
        self, client: TestClient, mock_user: MagicMock
    ) -> None:
        """Test that preferences endpoint returns the user's preferences."""
        with patch("src.routers.users.UserService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_preferences = AsyncMock(
                return_value={"theme": "dark", "default_format": "standard"}
            )
            mock_service_class.return_value = mock_service

            response = client.get("/api/v1/users/me/preferences")

        assert response.status_code == 200
        data = response.json()
        assert data["theme"] == "dark"
        assert data["default_format"] == "standard"

    def test_returns_empty_dict_when_no_preferences(
        self, client: TestClient, mock_user: MagicMock
    ) -> None:
        """Test that empty dict is returned when user has no preferences."""
        with patch("src.routers.users.UserService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_preferences = AsyncMock(return_value={})
            mock_service_class.return_value = mock_service

            response = client.get("/api/v1/users/me/preferences")

        assert response.status_code == 200
        assert response.json() == {}

    def test_returns_401_without_auth(self, unauthed_client: TestClient) -> None:
        """Test that 401 is returned when no auth header is provided."""
        response = unauthed_client.get("/api/v1/users/me/preferences")
        assert response.status_code == 401


class TestUpdateUserPreferences:
    """Tests for PUT /api/v1/users/me/preferences."""

    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def mock_user(self) -> MagicMock:
        user = MagicMock(spec=User)
        user.id = uuid4()
        user.email = "testuser@trainerlab.gg"
        user.display_name = "Test User"
        user.avatar_url = None
        user.is_beta_tester = False
        user.is_creator = False
        user.is_subscriber = False
        user.preferences = {}
        user.created_at = datetime.now(UTC)
        user.updated_at = datetime.now(UTC)
        return user

    @pytest.fixture
    def client(self, mock_db: AsyncMock, mock_user: MagicMock) -> TestClient:
        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = lambda: mock_user
        yield TestClient(app)
        app.dependency_overrides.clear()

    @pytest.fixture
    def unauthed_client(self, mock_db: AsyncMock) -> TestClient:
        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        yield TestClient(app)
        app.dependency_overrides.clear()

    def test_updates_theme_preference(
        self, client: TestClient, mock_user: MagicMock
    ) -> None:
        """Test updating the theme preference."""
        with patch("src.routers.users.UserService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.update_preferences = AsyncMock(return_value={"theme": "light"})
            mock_service_class.return_value = mock_service

            response = client.put(
                "/api/v1/users/me/preferences",
                json={"theme": "light"},
            )

        assert response.status_code == 200
        assert response.json() == {"theme": "light"}

    def test_updates_multiple_preferences(
        self, client: TestClient, mock_user: MagicMock
    ) -> None:
        """Test updating multiple preferences at once."""
        updated = {
            "theme": "dark",
            "default_format": "expanded",
            "email_notifications": False,
        }
        with patch("src.routers.users.UserService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.update_preferences = AsyncMock(return_value=updated)
            mock_service_class.return_value = mock_service

            response = client.put(
                "/api/v1/users/me/preferences",
                json={
                    "theme": "dark",
                    "default_format": "expanded",
                    "email_notifications": False,
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["theme"] == "dark"
        assert data["default_format"] == "expanded"
        assert data["email_notifications"] is False

    def test_rejects_invalid_theme_value(self, client: TestClient) -> None:
        """Test that an invalid theme value is rejected by validation."""
        response = client.put(
            "/api/v1/users/me/preferences",
            json={"theme": "invalid_theme"},
        )
        assert response.status_code == 422

    def test_rejects_invalid_format_value(self, client: TestClient) -> None:
        """Test that an invalid default_format value is rejected by validation."""
        response = client.put(
            "/api/v1/users/me/preferences",
            json={"default_format": "legacy"},
        )
        assert response.status_code == 422

    def test_returns_503_on_database_error(
        self, client: TestClient, mock_user: MagicMock
    ) -> None:
        """Test that 503 is returned when a database error occurs."""
        from src.services.user_service import DatabaseError

        with patch("src.routers.users.UserService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.update_preferences = AsyncMock(
                side_effect=DatabaseError("Connection lost")
            )
            mock_service_class.return_value = mock_service

            response = client.put(
                "/api/v1/users/me/preferences",
                json={"theme": "dark"},
            )

        assert response.status_code == 503
        assert "temporarily unavailable" in response.json()["detail"].lower()

    def test_returns_401_without_auth(self, unauthed_client: TestClient) -> None:
        """Test that 401 is returned when no auth header is provided."""
        response = unauthed_client.put(
            "/api/v1/users/me/preferences",
            json={"theme": "dark"},
        )
        assert response.status_code == 401

    def test_accepts_empty_body(self, client: TestClient) -> None:
        """Test that an empty body (no fields to update) is accepted."""
        with patch("src.routers.users.UserService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.update_preferences = AsyncMock(return_value={})
            mock_service_class.return_value = mock_service

            response = client.put(
                "/api/v1/users/me/preferences",
                json={},
            )

        assert response.status_code == 200
