"""User service for managing user accounts and preferences."""

from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User
from src.schemas.user import UserPreferencesUpdate


class UserService:
    """Business logic for user operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_or_create_user(
        self,
        firebase_uid: str,
        email: str,
        display_name: str | None = None,
        avatar_url: str | None = None,
    ) -> User:
        """Get existing user or create new one from Firebase data."""
        query = select(User).where(User.firebase_uid == firebase_uid)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()

        if user is None:
            user = User(
                id=uuid4(),
                firebase_uid=firebase_uid,
                email=email,
                display_name=display_name,
                avatar_url=avatar_url,
                preferences={},
            )
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)

        return user

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        """Get user by their UUID."""
        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_user(
        self,
        user: User,
        display_name: str | None = None,
        avatar_url: str | None = None,
    ) -> User:
        """Update user profile fields."""
        if display_name is not None:
            user.display_name = display_name
        if avatar_url is not None:
            user.avatar_url = avatar_url

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def get_preferences(self, user: User) -> dict:
        """Get user preferences."""
        return user.preferences or {}

    async def update_preferences(
        self, user: User, prefs: UserPreferencesUpdate
    ) -> dict:
        """Update user preferences (merge with existing)."""
        current = user.preferences or {}
        updates = prefs.model_dump(exclude_unset=True)

        # Merge updates into current preferences
        merged = {**current, **updates}
        user.preferences = merged

        await self.db.commit()
        await self.db.refresh(user)
        return user.preferences or {}
