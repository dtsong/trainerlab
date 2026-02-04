"""Tests for ApiKeyService."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.api_key import ApiKey
from src.models.user import User
from src.services.api_key_service import ApiKeyService


@pytest.fixture
def mock_session() -> AsyncMock:
    """Create a mock database session."""
    session = AsyncMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def mock_user() -> User:
    """Create a mock user."""
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.email = "creator@example.com"
    user.is_creator = True
    return user


class TestCreateApiKey:
    """Tests for create_api_key method."""

    @pytest.mark.asyncio
    async def test_creates_api_key_with_defaults(
        self, mock_session: AsyncMock, mock_user: User
    ):
        """Test creating an API key with default settings."""
        service = ApiKeyService(mock_session)

        with patch("src.services.api_key_service.generate_api_key") as mock_gen:
            mock_gen.return_value = "tl_test123456789abcdef"
            api_key, full_key = await service.create_api_key(mock_user, "Test Key")

        assert full_key == "tl_test123456789abcdef"
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_creates_api_key_with_custom_limit(
        self, mock_session: AsyncMock, mock_user: User
    ):
        """Test creating an API key with custom monthly limit."""
        service = ApiKeyService(mock_session)

        with patch("src.services.api_key_service.generate_api_key") as mock_gen:
            mock_gen.return_value = "tl_test123456789abcdef"
            api_key, _ = await service.create_api_key(
                mock_user, "Test Key", monthly_limit=5000
            )

        added_key = mock_session.add.call_args[0][0]
        assert added_key.monthly_limit == 5000

    @pytest.mark.asyncio
    async def test_creates_api_key_with_correct_fields(
        self, mock_session: AsyncMock, mock_user: User
    ):
        """Test that created API key has correct fields."""
        service = ApiKeyService(mock_session)

        with patch("src.services.api_key_service.generate_api_key") as mock_gen:
            mock_gen.return_value = "tl_test123456789abcdef"
            with patch("src.services.api_key_service.hash_api_key") as mock_hash:
                mock_hash.return_value = "hashed_key"
                with patch("src.services.api_key_service.get_key_prefix") as mock_prefix:
                    mock_prefix.return_value = "tl_test12"
                    await service.create_api_key(mock_user, "My API Key")

        added_key = mock_session.add.call_args[0][0]
        assert added_key.user_id == mock_user.id
        assert added_key.name == "My API Key"
        assert added_key.key_hash == "hashed_key"
        assert added_key.key_prefix == "tl_test12"
        assert added_key.is_active is True
        assert added_key.requests_this_month == 0


class TestGetApiKeyByHash:
    """Tests for get_api_key_by_hash method."""

    @pytest.mark.asyncio
    async def test_returns_api_key_when_found(self, mock_session: AsyncMock):
        """Test returning API key when hash matches."""
        mock_api_key = MagicMock(spec=ApiKey)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_api_key
        mock_session.execute.return_value = mock_result

        service = ApiKeyService(mock_session)
        result = await service.get_api_key_by_hash("test_hash")

        assert result == mock_api_key
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self, mock_session: AsyncMock):
        """Test returning None when hash doesn't match."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        service = ApiKeyService(mock_session)
        result = await service.get_api_key_by_hash("nonexistent_hash")

        assert result is None


class TestListUserApiKeys:
    """Tests for list_user_api_keys method."""

    @pytest.mark.asyncio
    async def test_returns_user_api_keys(
        self, mock_session: AsyncMock, mock_user: User
    ):
        """Test listing API keys for a user."""
        mock_keys = [MagicMock(spec=ApiKey), MagicMock(spec=ApiKey)]
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_keys
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        service = ApiKeyService(mock_session)
        result = await service.list_user_api_keys(mock_user)

        assert len(result) == 2
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_keys(
        self, mock_session: AsyncMock, mock_user: User
    ):
        """Test returning empty list when user has no keys."""
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        service = ApiKeyService(mock_session)
        result = await service.list_user_api_keys(mock_user)

        assert result == []


class TestGetApiKey:
    """Tests for get_api_key method."""

    @pytest.mark.asyncio
    async def test_returns_api_key_when_owned(
        self, mock_session: AsyncMock, mock_user: User
    ):
        """Test returning API key when user owns it."""
        key_id = uuid4()
        mock_api_key = MagicMock(spec=ApiKey)
        mock_api_key.id = key_id
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_api_key
        mock_session.execute.return_value = mock_result

        service = ApiKeyService(mock_session)
        result = await service.get_api_key(key_id, mock_user)

        assert result == mock_api_key

    @pytest.mark.asyncio
    async def test_returns_none_when_not_owned(
        self, mock_session: AsyncMock, mock_user: User
    ):
        """Test returning None when user doesn't own key."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        service = ApiKeyService(mock_session)
        result = await service.get_api_key(uuid4(), mock_user)

        assert result is None


class TestRevokeApiKey:
    """Tests for revoke_api_key method."""

    @pytest.mark.asyncio
    async def test_revokes_api_key_when_owned(
        self, mock_session: AsyncMock, mock_user: User
    ):
        """Test revoking an owned API key."""
        key_id = uuid4()
        mock_api_key = MagicMock(spec=ApiKey)
        mock_api_key.is_active = True
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_api_key
        mock_session.execute.return_value = mock_result

        service = ApiKeyService(mock_session)
        result = await service.revoke_api_key(key_id, mock_user)

        assert result is True
        assert mock_api_key.is_active is False
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_false_when_not_found(
        self, mock_session: AsyncMock, mock_user: User
    ):
        """Test returning False when key not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        service = ApiKeyService(mock_session)
        result = await service.revoke_api_key(uuid4(), mock_user)

        assert result is False
        mock_session.commit.assert_not_called()


class TestUpdateMonthlyLimit:
    """Tests for update_monthly_limit method."""

    @pytest.mark.asyncio
    async def test_updates_limit_when_owned(
        self, mock_session: AsyncMock, mock_user: User
    ):
        """Test updating monthly limit for owned key."""
        key_id = uuid4()
        mock_api_key = MagicMock(spec=ApiKey)
        mock_api_key.monthly_limit = 1000
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_api_key
        mock_session.execute.return_value = mock_result

        service = ApiKeyService(mock_session)
        result = await service.update_monthly_limit(key_id, mock_user, 5000)

        assert result == mock_api_key
        assert mock_api_key.monthly_limit == 5000
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(
        self, mock_session: AsyncMock, mock_user: User
    ):
        """Test returning None when key not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        service = ApiKeyService(mock_session)
        result = await service.update_monthly_limit(uuid4(), mock_user, 5000)

        assert result is None
