"""API Key service for creator programmatic access."""

import logging
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.api_key import ApiKey, generate_api_key, get_key_prefix, hash_api_key
from src.models.user import User

logger = logging.getLogger(__name__)


class ApiKeyService:
    """Service for API key CRUD operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_api_key(
        self,
        user: User,
        name: str,
        monthly_limit: int = 1000,
    ) -> tuple[ApiKey, str]:
        """Create a new API key for a user.

        Args:
            user: The authenticated creator user
            name: Display name for the key
            monthly_limit: Monthly request limit (default 1000)

        Returns:
            Tuple of (ApiKey model, full plain text key)
            The full key is only returned on creation.
        """
        full_key = generate_api_key()
        key_hash = hash_api_key(full_key)
        key_prefix = get_key_prefix(full_key)

        api_key = ApiKey(
            id=uuid4(),
            user_id=user.id,
            key_hash=key_hash,
            key_prefix=key_prefix,
            name=name,
            monthly_limit=monthly_limit,
            requests_this_month=0,
            is_active=True,
        )

        self.session.add(api_key)
        await self.session.commit()
        await self.session.refresh(api_key)

        logger.info("Created API key %s for user %s", api_key.id, user.id)
        return api_key, full_key

    async def get_api_key_by_hash(self, key_hash: str) -> ApiKey | None:
        """Get an API key by its hash.

        Args:
            key_hash: SHA-256 hash of the API key

        Returns:
            ApiKey if found and active, None otherwise
        """
        query = select(ApiKey).where(
            ApiKey.key_hash == key_hash,
            ApiKey.is_active == True,  # noqa: E712
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_user_api_keys(self, user: User) -> list[ApiKey]:
        """List all API keys for a user.

        Args:
            user: The authenticated user

        Returns:
            List of API keys (active and inactive)
        """
        query = (
            select(ApiKey)
            .where(ApiKey.user_id == user.id)
            .order_by(ApiKey.created_at.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_api_key(self, key_id: UUID, user: User) -> ApiKey | None:
        """Get a specific API key by ID.

        Args:
            key_id: The API key ID
            user: The authenticated user (must own the key)

        Returns:
            ApiKey if found and owned by user, None otherwise
        """
        query = select(ApiKey).where(
            ApiKey.id == key_id,
            ApiKey.user_id == user.id,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def revoke_api_key(self, key_id: UUID, user: User) -> bool:
        """Revoke an API key.

        Args:
            key_id: The API key ID
            user: The authenticated user (must own the key)

        Returns:
            True if revoked, False if not found or not owned
        """
        api_key = await self.get_api_key(key_id, user)
        if api_key is None:
            return False

        api_key.is_active = False
        await self.session.commit()
        logger.info("Revoked API key %s for user %s", key_id, user.id)
        return True

    async def update_monthly_limit(
        self, key_id: UUID, user: User, new_limit: int
    ) -> ApiKey | None:
        """Update the monthly limit for an API key.

        Args:
            key_id: The API key ID
            user: The authenticated user (must own the key)
            new_limit: The new monthly request limit

        Returns:
            Updated ApiKey if found, None otherwise
        """
        api_key = await self.get_api_key(key_id, user)
        if api_key is None:
            return None

        api_key.monthly_limit = new_limit
        await self.session.commit()
        await self.session.refresh(api_key)
        return api_key
