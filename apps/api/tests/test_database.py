"""Tests for database connection and session management."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestGetDb:
    """Tests for get_db async generator dependency."""

    @pytest.mark.asyncio
    @patch("src.db.database.async_session_factory")
    async def test_yields_session(self, mock_factory: MagicMock) -> None:
        """Test that get_db yields an async session."""
        from src.db.database import get_db

        mock_session = AsyncMock()
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        gen = get_db()
        session = await gen.__anext__()

        assert session == mock_session

    @pytest.mark.asyncio
    @patch("src.db.database.async_session_factory")
    async def test_closes_session_on_completion(self, mock_factory: MagicMock) -> None:
        """Test that session.close() is called when generator completes."""
        from src.db.database import get_db

        mock_session = AsyncMock()
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        gen = get_db()
        await gen.__anext__()

        # Exhaust the generator to trigger finally block
        with pytest.raises(StopAsyncIteration):
            await gen.__anext__()

        mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.db.database.async_session_factory")
    async def test_closes_session_on_exception(self, mock_factory: MagicMock) -> None:
        """Test that session.close() is called even when an exception occurs."""
        from src.db.database import get_db

        mock_session = AsyncMock()
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        gen = get_db()
        await gen.__anext__()

        # Throw an exception into the generator to trigger finally block
        with pytest.raises(ValueError, match="test error"):
            await gen.athrow(ValueError("test error"))

        mock_session.close.assert_called_once()
