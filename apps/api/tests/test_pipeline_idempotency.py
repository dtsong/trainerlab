"""Tests for pipeline idempotency.

Verifies that running each pipeline's core operation twice
produces the same result without creating duplicates.
"""

from dataclasses import dataclass
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.models.card import Card
from src.models.meta_snapshot import MetaSnapshot
from src.models.set import Set
from src.services.card_sync import CardSyncService, SyncResult


class TestCardSyncIdempotency:
    """EN card sync upsert is idempotent via session.merge()."""

    @pytest.mark.asyncio
    async def test_upsert_cards_twice_no_duplicates(self) -> None:
        """Merging the same cards twice should not create duplicates."""
        session = AsyncMock()
        client = AsyncMock()
        service = CardSyncService(session, client)

        cards = [
            Card(
                id="sv09-1",
                local_id="1",
                name="Charizard ex",
                set_id="sv09",
            ),
            Card(
                id="sv09-2",
                local_id="2",
                name="Pikachu",
                set_id="sv09",
            ),
        ]

        # First run
        await service.upsert_cards(cards)
        first_processed = service.result.cards_processed

        # Second run — same cards
        await service.upsert_cards(cards)
        second_processed = service.result.cards_processed

        # Both runs processed same count (cumulative)
        assert second_processed == first_processed * 2
        # merge was called for each card in each run
        assert session.merge.call_count == 4

    @pytest.mark.asyncio
    async def test_upsert_set_twice_is_idempotent(self) -> None:
        """Upserting the same set twice updates rather than duplicates."""
        session = AsyncMock()
        client = AsyncMock()
        service = CardSyncService(session, client)

        db_set = Set(id="sv09", name="Paradise Dragona")

        # First run — insert
        session.get = AsyncMock(return_value=None)
        await service.upsert_set(db_set)
        assert service.result.sets_inserted == 1

        # Second run — update (existing found)
        existing_set = Set(id="sv09", name="Old Name")
        session.get = AsyncMock(return_value=existing_set)
        await service.upsert_set(db_set)
        assert service.result.sets_updated == 1
        assert existing_set.name == "Paradise Dragona"


class TestJPSyncIdempotency:
    """JP sync backfill is idempotent."""

    @pytest.mark.asyncio
    async def test_jp_backfill_twice_no_duplicates(self) -> None:
        """Running JP sync twice on a card with japanese_name set
        should not overwrite it."""
        session = AsyncMock()
        client = AsyncMock()
        service = CardSyncService(session, client)

        # Mock fetch_set
        mock_set = MagicMock()
        mock_set.name = "Test Set"
        mock_set.series_name = "SV"
        mock_set.release_date = None
        mock_set.card_count_official = 100
        mock_set.logo = None
        mock_set.symbol = None
        client.fetch_set = AsyncMock(return_value=mock_set)

        # Mock fetch_cards_for_set
        mock_card = MagicMock()
        mock_card.id = "SV9-001"
        mock_card.local_id = "001"
        mock_card.name = "リザードンex"
        mock_card.supertype = None
        mock_card.subtypes = None
        mock_card.types = None
        mock_card.hp = None
        mock_card.stage = None
        mock_card.evolves_from = None
        mock_card.evolves_to = None
        mock_card.attacks = None
        mock_card.abilities = None
        mock_card.weaknesses = None
        mock_card.resistances = None
        mock_card.retreat_cost = None
        mock_card.rules = None
        mock_card.rarity = None
        mock_card.number = None
        mock_card.image_small = None
        mock_card.image_large = None
        mock_card.regulation_mark = None
        client.fetch_cards_for_set = AsyncMock(return_value=[mock_card])

        # First run — card doesn't exist → insert
        session.get = AsyncMock(side_effect=[None, None])
        await service.sync_jp_set("SV9")
        assert service.result.cards_inserted == 1

        # Second run — card exists with japanese_name already set
        existing_card = MagicMock()
        existing_card.japanese_name = "リザードンex"
        session.get = AsyncMock(side_effect=[None, existing_card])

        service.result = SyncResult()
        await service.sync_jp_set("SV9")
        # Should update (not insert) and NOT overwrite japanese_name
        assert service.result.cards_updated == 1
        assert service.result.cards_inserted == 0


class TestMetaSnapshotIdempotency:
    """save_snapshot upserts on (date, region, format, best_of)."""

    @pytest.mark.asyncio
    async def test_save_snapshot_twice_updates(self) -> None:
        """Saving the same snapshot dimensions twice should update."""
        from src.services.meta_service import MetaService

        session = AsyncMock()
        service = MetaService(session)

        snapshot = MetaSnapshot(
            id=uuid4(),
            snapshot_date=date(2025, 1, 15),
            region=None,
            format="standard",
            best_of=3,
            archetype_shares={"Charizard ex": 0.6, "Lugia VSTAR": 0.4},
            sample_size=100,
        )

        # First save — no existing
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute = AsyncMock(return_value=mock_result)
        session.refresh = AsyncMock()

        await service.save_snapshot(snapshot)
        session.add.assert_called_once()

        # Second save — existing found
        existing = MagicMock(spec=MetaSnapshot)
        mock_result2 = MagicMock()
        mock_result2.scalar_one_or_none.return_value = existing
        session.execute = AsyncMock(return_value=mock_result2)
        session.refresh = AsyncMock()

        snapshot.archetype_shares = {
            "Charizard ex": 0.55,
            "Lugia VSTAR": 0.45,
        }
        await service.save_snapshot(snapshot)

        # Updated existing, not added new
        assert existing.archetype_shares == {
            "Charizard ex": 0.55,
            "Lugia VSTAR": 0.45,
        }


class TestSeedDataIdempotency:
    """seed_reference_data skips existing formats."""

    @pytest.mark.asyncio
    async def test_seed_formats_twice_no_duplicates(self) -> None:
        from src.pipelines.seed_data import seed_reference_data

        mock_session = AsyncMock()
        mock_session.add = MagicMock()

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)

        fixtures = {
            "formats": [
                {
                    "name": "H-regulation",
                    "display_name": "H Regulation",
                    "legal_sets": ["sv09"],
                    "is_current": True,
                },
            ],
        }

        with (
            patch(
                "src.pipelines.seed_data.async_session_factory",
                return_value=mock_ctx,
            ),
            patch(
                "src.pipelines.seed_data._load_fixtures",
                return_value=fixtures,
            ),
            patch(
                "src.pipelines.seed_data.ArchetypeNormalizer.seed_db_sprites",
                new_callable=AsyncMock,
                return_value=10,
            ),
        ):
            # First run — format doesn't exist
            not_found = MagicMock()
            not_found.scalar_one_or_none.return_value = None
            mock_session.execute = AsyncMock(return_value=not_found)

            result1 = await seed_reference_data(dry_run=False)
            assert result1.formats_seeded == 1

            # Second run — format exists
            found = MagicMock()
            found.scalar_one_or_none.return_value = MagicMock()
            mock_session.execute = AsyncMock(return_value=found)

            result2 = await seed_reference_data(dry_run=False)
            assert result2.formats_seeded == 0


class TestSyncCardMappingsIdempotency:
    """ON CONFLICT DO UPDATE ensures idempotency."""

    @pytest.mark.asyncio
    async def test_sync_same_set_twice(self) -> None:
        from src.pipelines.sync_card_mappings import (
            sync_card_mappings_for_set,
        )

        session = AsyncMock()
        client = AsyncMock()

        @dataclass
        class MockEquiv:
            jp_card_id: str
            en_card_id: str
            card_name_en: str
            jp_set_id: str
            en_set_id: str

        equivalents = [
            MockEquiv("sv9-001", "sv09-1", "Charizard", "SV9", "sv09"),
            MockEquiv("sv9-002", "sv09-2", "Pikachu", "SV9", "sv09"),
        ]

        client.fetch_card_equivalents = AsyncMock(return_value=equivalents)

        # First run — no existing IDs
        empty_result = MagicMock()
        empty_result.__iter__ = MagicMock(return_value=iter([]))
        session.execute = AsyncMock(return_value=empty_result)

        inserted1, updated1 = await sync_card_mappings_for_set(session, client, "SV9")
        assert inserted1 == 2
        assert updated1 == 0

        # Second run — same IDs now exist
        existing_result = MagicMock()
        existing_result.__iter__ = MagicMock(
            return_value=iter([("sv9-001",), ("sv9-002",)])
        )
        # First call returns existing IDs, rest are execute calls
        call_count = 0

        async def side_effect(stmt):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return existing_result
            return MagicMock()

        session.execute = AsyncMock(side_effect=side_effect)

        inserted2, updated2 = await sync_card_mappings_for_set(session, client, "SV9")
        assert inserted2 == 0
        assert updated2 == 2


class TestMonitorCardRevealsIdempotency:
    """Existing cards are updated, not duplicated."""

    @pytest.mark.asyncio
    async def test_monitor_same_cards_twice(self) -> None:
        from src.pipelines.monitor_card_reveals import (
            check_card_reveals,
        )

        @dataclass
        class MockJPCard:
            card_id: str
            set_id: str
            name_jp: str
            name_en: str | None
            card_type: str | None

        cards = [
            MockJPCard("sv9-001", "SV9", "リザードンex", None, "Pokemon"),
        ]

        mock_session = AsyncMock()
        mock_session.add = MagicMock()

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)

        mock_limitless = AsyncMock()
        mock_limitless.fetch_unreleased_cards = AsyncMock(return_value=cards)

        mock_limitless_ctx = AsyncMock()
        mock_limitless_ctx.__aenter__ = AsyncMock(return_value=mock_limitless)
        mock_limitless_ctx.__aexit__ = AsyncMock(return_value=False)

        # First run — card doesn't exist
        not_found = MagicMock()
        not_found.scalar_one_or_none.return_value = None
        tracked_result = MagicMock()
        tracked_result.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(side_effect=[not_found, tracked_result])

        with (
            patch(
                "src.pipelines.monitor_card_reveals.LimitlessClient",
                return_value=mock_limitless_ctx,
            ),
            patch(
                "src.pipelines.monitor_card_reveals.async_session_factory",
                return_value=mock_ctx,
            ),
        ):
            result1 = await check_card_reveals(dry_run=False)

        assert result1.new_cards_found == 1

        # Second run — card exists
        existing_card = MagicMock()
        existing_card.name_en = None
        existing_card.card_type = "Pokemon"
        existing_card.jp_set_id = "SV9"
        existing_card.jp_card_id = "sv9-001"
        existing_card.is_released = False

        found = MagicMock()
        found.scalar_one_or_none.return_value = existing_card
        tracked_result2 = MagicMock()
        tracked_result2.scalars.return_value.all.return_value = [existing_card]
        mock_session.execute = AsyncMock(side_effect=[found, tracked_result2])

        with (
            patch(
                "src.pipelines.monitor_card_reveals.LimitlessClient",
                return_value=mock_limitless_ctx,
            ),
            patch(
                "src.pipelines.monitor_card_reveals.async_session_factory",
                return_value=mock_ctx,
            ),
        ):
            result2 = await check_card_reveals(dry_run=False)

        assert result2.new_cards_found == 0
        # No duplicate — card was found, not inserted again
        assert result2.cards_updated == 0  # name_en still None
