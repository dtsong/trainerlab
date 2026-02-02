"""Tests for user service and endpoints."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.exc import SQLAlchemyError

from src.models.user import User
from src.schemas.user import UserPreferencesUpdate
from src.services.user_service import DatabaseError, UserService


class TestUserService:
    """Tests for UserService."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Create a mock async session."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> UserService:
        """Create a UserService with mock session."""
        return UserService(mock_session)

    @pytest.fixture
    def sample_user(self) -> MagicMock:
        """Create a sample user mock."""
        user = MagicMock(spec=User)
        user.id = uuid4()
        user.firebase_uid = "firebase-uid-123"
        user.email = "test@example.com"
        user.display_name = "Test User"
        user.avatar_url = "https://example.com/avatar.jpg"
        user.preferences = {"theme": "dark"}
        user.created_at = datetime.now(UTC)
        user.updated_at = datetime.now(UTC)
        return user

    @pytest.mark.asyncio
    async def test_get_or_create_user_existing(
        self, service: UserService, sample_user: MagicMock
    ) -> None:
        """Test getting existing user."""
        # Mock existing user lookup
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        service.db.execute = AsyncMock(return_value=mock_result)

        result = await service.get_or_create_user(
            firebase_uid="firebase-uid-123",
            email="test@example.com",
        )

        assert result == sample_user
        service.db.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_or_create_user_new(self, service: UserService) -> None:
        """Test creating new user when not exists."""
        # Mock no existing user
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        service.db.execute = AsyncMock(return_value=mock_result)
        service.db.add = MagicMock()
        service.db.commit = AsyncMock()
        service.db.refresh = AsyncMock()

        await service.get_or_create_user(
            firebase_uid="new-uid",
            email="new@example.com",
            display_name="New User",
        )

        service.db.add.assert_called_once()
        service.db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_by_id(
        self, service: UserService, sample_user: MagicMock
    ) -> None:
        """Test getting user by ID."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        service.db.execute = AsyncMock(return_value=mock_result)

        result = await service.get_user_by_id(sample_user.id)

        assert result == sample_user

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, service: UserService) -> None:
        """Test getting non-existent user returns None."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        service.db.execute = AsyncMock(return_value=mock_result)

        result = await service.get_user_by_id(uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_update_user(
        self, service: UserService, sample_user: MagicMock
    ) -> None:
        """Test updating user profile."""
        service.db.commit = AsyncMock()
        service.db.refresh = AsyncMock()

        await service.update_user(
            sample_user,
            display_name="Updated Name",
            avatar_url="https://example.com/new-avatar.jpg",
        )

        assert sample_user.display_name == "Updated Name"
        assert sample_user.avatar_url == "https://example.com/new-avatar.jpg"
        service.db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_preferences(
        self, service: UserService, sample_user: MagicMock
    ) -> None:
        """Test getting user preferences."""
        result = await service.get_preferences(sample_user)

        assert result == {"theme": "dark"}

    @pytest.mark.asyncio
    async def test_get_preferences_empty(
        self, service: UserService, sample_user: MagicMock
    ) -> None:
        """Test getting preferences when None."""
        sample_user.preferences = None

        result = await service.get_preferences(sample_user)

        assert result == {}

    @pytest.mark.asyncio
    async def test_update_preferences_merge(
        self, service: UserService, sample_user: MagicMock
    ) -> None:
        """Test preferences are merged, not replaced."""
        sample_user.preferences = {"theme": "dark", "default_format": "standard"}
        service.db.commit = AsyncMock()
        service.db.refresh = AsyncMock()

        prefs = UserPreferencesUpdate(email_notifications=True)
        await service.update_preferences(sample_user, prefs)

        # Should contain original plus new
        assert sample_user.preferences["theme"] == "dark"
        assert sample_user.preferences["default_format"] == "standard"
        assert sample_user.preferences["email_notifications"] is True

    @pytest.mark.asyncio
    async def test_update_preferences_override(
        self, service: UserService, sample_user: MagicMock
    ) -> None:
        """Test preferences can be overridden."""
        sample_user.preferences = {"theme": "dark"}
        service.db.commit = AsyncMock()
        service.db.refresh = AsyncMock()

        prefs = UserPreferencesUpdate(theme="light")
        await service.update_preferences(sample_user, prefs)

        assert sample_user.preferences["theme"] == "light"


class TestUserServiceDatabaseErrors:
    """Tests for UserService database error handling."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Create a mock async session."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> UserService:
        """Create a UserService with mock session."""
        return UserService(mock_session)

    @pytest.fixture
    def sample_user(self) -> MagicMock:
        """Create a sample user mock."""
        user = MagicMock(spec=User)
        user.id = uuid4()
        user.preferences = {"theme": "dark"}
        return user

    @pytest.mark.asyncio
    async def test_get_or_create_user_database_error(
        self, service: UserService
    ) -> None:
        """Test DatabaseError raised on execute failure."""
        service.db.execute = AsyncMock(side_effect=SQLAlchemyError("Connection lost"))
        service.db.rollback = AsyncMock()

        with pytest.raises(DatabaseError, match="Failed to get or create user"):
            await service.get_or_create_user(
                firebase_uid="test-uid",
                email="test@example.com",
            )

        service.db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_or_create_user_commit_error(self, service: UserService) -> None:
        """Test DatabaseError raised on commit failure."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        service.db.execute = AsyncMock(return_value=mock_result)
        service.db.add = MagicMock()
        service.db.commit = AsyncMock(side_effect=SQLAlchemyError("Commit failed"))
        service.db.rollback = AsyncMock()

        with pytest.raises(DatabaseError, match="Failed to get or create user"):
            await service.get_or_create_user(
                firebase_uid="test-uid",
                email="test@example.com",
            )

        service.db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_by_id_database_error(self, service: UserService) -> None:
        """Test DatabaseError raised on execute failure."""
        service.db.execute = AsyncMock(side_effect=SQLAlchemyError("Connection lost"))

        with pytest.raises(DatabaseError, match="Failed to get user"):
            await service.get_user_by_id(uuid4())

    @pytest.mark.asyncio
    async def test_update_user_database_error(
        self, service: UserService, sample_user: MagicMock
    ) -> None:
        """Test DatabaseError raised on commit failure."""
        service.db.commit = AsyncMock(side_effect=SQLAlchemyError("Commit failed"))
        service.db.rollback = AsyncMock()

        with pytest.raises(DatabaseError, match="Failed to update user"):
            await service.update_user(sample_user, display_name="New Name")

        service.db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_preferences_database_error(
        self, service: UserService, sample_user: MagicMock
    ) -> None:
        """Test DatabaseError raised on commit failure."""
        service.db.commit = AsyncMock(side_effect=SQLAlchemyError("Commit failed"))
        service.db.rollback = AsyncMock()

        prefs = UserPreferencesUpdate(theme="light")
        with pytest.raises(DatabaseError, match="Failed to update preferences"):
            await service.update_preferences(sample_user, prefs)

        service.db.rollback.assert_called_once()
