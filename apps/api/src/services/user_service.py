"""User service for managing user accounts and preferences."""

import logging
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User
from src.schemas.user import UserPreferencesUpdate

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Raised when a database operation fails."""

    pass


class UserService:
    """Business logic for user operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_or_create_user(
        self,
        auth_provider_id: str,
        email: str,
        display_name: str | None = None,
        avatar_url: str | None = None,
    ) -> User:
        """Get existing user or create new one from auth provider data.

        Raises:
            DatabaseError: If the database operation fails.
        """
        try:
            query = select(User).where(User.auth_provider_id == auth_provider_id)
            result = await self.db.execute(query)
            user = result.scalar_one_or_none()

            if user is None:
                user = User(
                    id=uuid4(),
                    auth_provider_id=auth_provider_id,
                    email=email,
                    display_name=display_name,
                    avatar_url=avatar_url,
                    preferences={},
                )
                self.db.add(user)
                await self.db.commit()
                await self.db.refresh(user)

            return user
        except SQLAlchemyError as e:
            logger.error("Database error in get_or_create_user: %s", e)
            await self.db.rollback()
            raise DatabaseError("Failed to get or create user") from e

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        """Get user by their UUID.

        Raises:
            DatabaseError: If the database operation fails.
        """
        try:
            query = select(User).where(User.id == user_id)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error("Database error in get_user_by_id: %s", e)
            raise DatabaseError("Failed to get user") from e

    async def update_user(
        self,
        user: User,
        display_name: str | None = None,
        avatar_url: str | None = None,
    ) -> User:
        """Update user profile fields.

        Raises:
            DatabaseError: If the database operation fails.
        """
        try:
            if display_name is not None:
                user.display_name = display_name
            if avatar_url is not None:
                user.avatar_url = avatar_url

            await self.db.commit()
            await self.db.refresh(user)
            return user
        except SQLAlchemyError as e:
            logger.error("Database error in update_user: %s", e)
            await self.db.rollback()
            raise DatabaseError("Failed to update user") from e

    async def get_preferences(self, user: User) -> dict:
        """Get user preferences."""
        return user.preferences or {}

    async def update_preferences(
        self, user: User, prefs: UserPreferencesUpdate
    ) -> dict:
        """Update user preferences (merge with existing).

        Raises:
            DatabaseError: If the database operation fails.
        """
        try:
            current = user.preferences or {}
            updates = prefs.model_dump(exclude_unset=True)

            # Merge updates into current preferences
            merged = {**current, **updates}
            user.preferences = merged

            await self.db.commit()
            await self.db.refresh(user)
            return user.preferences or {}
        except SQLAlchemyError as e:
            logger.error("Database error in update_preferences: %s", e)
            await self.db.rollback()
            raise DatabaseError("Failed to update preferences") from e
