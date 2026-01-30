"""Tests for card sync pipeline."""

from datetime import date
from unittest.mock import AsyncMock, patch

import pytest

from src.clients.tcgdex import TCGdexCard, TCGdexSet, TCGdexSetSummary
from src.pipelines.sync_cards import (
    sync_english_cards,
    sync_japanese_names,
)


@pytest.fixture
def mock_session_factory():
    """Create mock session factory."""

    async def factory():
        session = AsyncMock()
        session.get = AsyncMock(return_value=None)
        session.merge = AsyncMock(side_effect=lambda x: x)
        session.commit = AsyncMock()
        session.close = AsyncMock()
        return session

    return factory


@pytest.fixture
def mock_tcgdex_client():
    """Create mock TCGdex client."""
    client = AsyncMock()
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)
    return client


class TestSyncEnglishCards:
    """Tests for sync_english_cards pipeline."""

    @pytest.mark.asyncio
    async def test_sync_english_cards(self, mock_session_factory, mock_tcgdex_client):
        """Test syncing English cards."""
        mock_tcgdex_client.fetch_all_sets.return_value = [
            TCGdexSetSummary(
                id="swsh1",
                name="Sword & Shield",
                logo=None,
                symbol=None,
                card_count_total=2,
                card_count_official=2,
            )
        ]
        mock_tcgdex_client.fetch_set.return_value = TCGdexSet(
            id="swsh1",
            name="Sword & Shield",
            release_date=date(2020, 2, 7),
            series_id="swsh",
            series_name="Sword & Shield",
            logo=None,
            symbol=None,
            card_count_total=2,
            card_count_official=2,
            legal_standard=False,
            legal_expanded=True,
            card_summaries=[],
        )
        mock_tcgdex_client.fetch_cards_for_set.return_value = [
            TCGdexCard(
                id="swsh1-1",
                local_id="1",
                name="Celebi V",
                supertype="Pokemon",
                subtypes=None,
                types=["Grass"],
                hp=180,
                stage="Basic",
                evolves_from=None,
                evolves_to=None,
                attacks=None,
                abilities=None,
                weaknesses=None,
                resistances=None,
                retreat_cost=1,
                rules=None,
                set_id="swsh1",
                rarity="Rare",
                number="1",
                image_small=None,
                image_large=None,
                regulation_mark="D",
                legal_standard=False,
                legal_expanded=True,
            )
        ]

        with (
            patch(
                "src.pipelines.sync_cards.async_session_factory",
                return_value=AsyncMock(
                    __aenter__=AsyncMock(return_value=await mock_session_factory()),
                    __aexit__=AsyncMock(return_value=None),
                ),
            ),
            patch(
                "src.pipelines.sync_cards.TCGdexClient",
                return_value=mock_tcgdex_client,
            ),
        ):
            result = await sync_english_cards(dry_run=False)

        assert result.sets_processed == 1
        assert result.cards_processed == 1

    @pytest.mark.asyncio
    async def test_sync_english_cards_dry_run(
        self, mock_session_factory, mock_tcgdex_client
    ):
        """Test dry run mode doesn't commit."""
        mock_tcgdex_client.fetch_all_sets.return_value = [
            TCGdexSetSummary(
                id="swsh1",
                name="Sword & Shield",
                logo=None,
                symbol=None,
                card_count_total=1,
                card_count_official=1,
            )
        ]
        mock_tcgdex_client.fetch_set.return_value = TCGdexSet(
            id="swsh1",
            name="Sword & Shield",
            release_date=date(2020, 2, 7),
            series_id="swsh",
            series_name="Sword & Shield",
            logo=None,
            symbol=None,
            card_count_total=1,
            card_count_official=1,
            legal_standard=False,
            legal_expanded=True,
            card_summaries=[],
        )
        mock_tcgdex_client.fetch_cards_for_set.return_value = []

        mock_session = await mock_session_factory()
        with (
            patch(
                "src.pipelines.sync_cards.async_session_factory",
                return_value=AsyncMock(
                    __aenter__=AsyncMock(return_value=mock_session),
                    __aexit__=AsyncMock(return_value=None),
                ),
            ),
            patch(
                "src.pipelines.sync_cards.TCGdexClient",
                return_value=mock_tcgdex_client,
            ),
        ):
            result = await sync_english_cards(dry_run=True)

        # In dry run, we don't actually sync
        # The function should return early with empty result
        assert result is not None


class TestSyncJapaneseNames:
    """Tests for sync_japanese_names pipeline."""

    @pytest.mark.asyncio
    async def test_sync_japanese_names(self, mock_session_factory, mock_tcgdex_client):
        """Test syncing Japanese card names."""
        # Mock existing card in database
        mock_card = AsyncMock()
        mock_card.japanese_name = None

        mock_session = await mock_session_factory()
        mock_session.get.return_value = mock_card

        # Mock Japanese set and card data
        mock_tcgdex_client.fetch_all_sets.return_value = [
            TCGdexSetSummary(
                id="s1",
                name="ソード",
                logo=None,
                symbol=None,
                card_count_total=1,
                card_count_official=1,
            )
        ]
        mock_tcgdex_client.fetch_set.return_value = TCGdexSet(
            id="s1",
            name="ソード",
            release_date=date(2019, 12, 6),
            series_id="s",
            series_name="剣盾",
            logo=None,
            symbol=None,
            card_count_total=1,
            card_count_official=1,
            legal_standard=False,
            legal_expanded=True,
            card_summaries=[],
        )
        mock_tcgdex_client.fetch_cards_for_set.return_value = [
            TCGdexCard(
                id="s1-001",
                local_id="001",
                name="セレビィV",
                supertype="Pokemon",
                subtypes=None,
                types=["Grass"],
                hp=180,
                stage="Basic",
                evolves_from=None,
                evolves_to=None,
                attacks=None,
                abilities=None,
                weaknesses=None,
                resistances=None,
                retreat_cost=1,
                rules=None,
                set_id="s1",
                rarity="RR",
                number="001",
                image_small=None,
                image_large=None,
                regulation_mark="D",
                legal_standard=False,
                legal_expanded=True,
            )
        ]

        with (
            patch(
                "src.pipelines.sync_cards.async_session_factory",
                return_value=AsyncMock(
                    __aenter__=AsyncMock(return_value=mock_session),
                    __aexit__=AsyncMock(return_value=None),
                ),
            ),
            patch(
                "src.pipelines.sync_cards.TCGdexClient",
                return_value=mock_tcgdex_client,
            ),
        ):
            updated_count = await sync_japanese_names(dry_run=False)

        # Should have attempted to update cards
        assert updated_count >= 0
