"""Tests for sync_cards pipeline — covers dry_run paths and sync_all."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.card_sync import SyncResult


class TestSyncEnglishCards:
    """Tests for sync_english_cards."""

    @pytest.mark.asyncio
    async def test_dry_run_returns_empty_result(self) -> None:
        """Should return empty SyncResult on dry_run (lines 25-28)."""
        from src.pipelines.sync_cards import sync_english_cards

        result = await sync_english_cards(dry_run=True)
        assert isinstance(result, SyncResult)

    @pytest.mark.asyncio
    async def test_runs_sync(self) -> None:
        """Should call sync_all_english when not dry_run (lines 30-33)."""
        from src.pipelines.sync_cards import sync_english_cards

        mock_sync_result = SyncResult()

        with (
            patch("src.pipelines.sync_cards.TCGdexClient") as mock_client_cls,
            patch("src.pipelines.sync_cards.async_session_factory") as mock_sf,
            patch("src.pipelines.sync_cards.CardSyncService") as mock_svc_cls,
        ):
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=None)

            mock_session = AsyncMock()
            mock_sf.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_sf.return_value.__aexit__ = AsyncMock(return_value=None)

            mock_svc = AsyncMock()
            mock_svc.sync_all_english.return_value = mock_sync_result
            mock_svc_cls.return_value = mock_svc

            result = await sync_english_cards(dry_run=False)
            assert result is mock_sync_result
            mock_svc.sync_all_english.assert_called_once()


class TestSyncJapaneseNames:
    """Tests for sync_japanese_names."""

    @pytest.mark.asyncio
    async def test_dry_run_returns_zero(self) -> None:
        """Should return 0 on dry_run (lines 53-55)."""
        from src.pipelines.sync_cards import sync_japanese_names

        result = await sync_japanese_names(dry_run=True)
        assert result == 0

    @pytest.mark.asyncio
    async def test_runs_sync_with_sets(self) -> None:
        """Should fetch JP sets and update names (lines 58-90)."""
        from src.pipelines.sync_cards import sync_japanese_names

        mock_set = MagicMock()
        mock_set.id = "sv1"

        mock_card = MagicMock()
        mock_card.id = "sv1-001"
        mock_card.name = "リザードンex"

        with (
            patch("src.pipelines.sync_cards.TCGdexClient") as mock_client_cls,
            patch("src.pipelines.sync_cards.async_session_factory") as mock_sf,
            patch("src.pipelines.sync_cards.CardSyncService") as mock_svc_cls,
        ):
            mock_client = AsyncMock()
            mock_client.fetch_all_sets.return_value = [mock_set]
            mock_client.fetch_cards_for_set.return_value = [mock_card]
            mock_client_cls.return_value.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=None)

            mock_session = AsyncMock()
            mock_sf.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_sf.return_value.__aexit__ = AsyncMock(return_value=None)

            mock_svc = AsyncMock()
            mock_svc.update_japanese_names.return_value = 5
            mock_svc_cls.return_value = mock_svc

            result = await sync_japanese_names(dry_run=False)
            assert result == 5
            mock_client.fetch_all_sets.assert_called_once_with(language="ja")
            mock_svc.update_japanese_names.assert_called_once()

    @pytest.mark.asyncio
    async def test_handles_set_fetch_error(self) -> None:
        """Should continue on TCGdex error for individual sets (lines 78-80)."""
        from src.clients.tcgdex import TCGdexError
        from src.pipelines.sync_cards import sync_japanese_names

        mock_set1 = MagicMock()
        mock_set1.id = "sv1"
        mock_set2 = MagicMock()
        mock_set2.id = "sv2"

        mock_card = MagicMock()
        mock_card.id = "sv2-001"
        mock_card.name = "テスト"

        with (
            patch("src.pipelines.sync_cards.TCGdexClient") as mock_client_cls,
            patch("src.pipelines.sync_cards.async_session_factory") as mock_sf,
            patch("src.pipelines.sync_cards.CardSyncService") as mock_svc_cls,
        ):
            mock_client = AsyncMock()
            mock_client.fetch_all_sets.return_value = [mock_set1, mock_set2]
            # First set fetch fails, second succeeds
            mock_client.fetch_cards_for_set.side_effect = [
                TCGdexError("Not found"),
                [mock_card],
            ]
            mock_client_cls.return_value.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=None)

            mock_session = AsyncMock()
            mock_sf.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_sf.return_value.__aexit__ = AsyncMock(return_value=None)

            mock_svc = AsyncMock()
            mock_svc.update_japanese_names.return_value = 1
            mock_svc_cls.return_value = mock_svc

            result = await sync_japanese_names(dry_run=False)
            assert result == 1


class TestSyncAll:
    """Tests for sync_all."""

    @pytest.mark.asyncio
    async def test_dry_run(self) -> None:
        """Should call both pipelines in dry_run (lines 93-108)."""
        from src.pipelines.sync_cards import sync_all

        result = await sync_all(dry_run=True)
        english_result, jp_count = result
        assert isinstance(english_result, SyncResult)
        assert jp_count == 0
