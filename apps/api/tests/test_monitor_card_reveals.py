"""Tests for JP card reveal monitoring pipeline."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from src.clients.limitless import LimitlessClient, LimitlessError, LimitlessJPCard
from src.models.jp_unreleased_card import JPUnreleasedCard
from src.pipelines.monitor_card_reveals import (
    MonitorCardRevealsResult,
    _estimate_impact,
    _should_update,
    check_card_reveals,
)


@pytest.fixture
def sample_unreleased_cards() -> list[LimitlessJPCard]:
    """Create sample unreleased JP cards for testing."""
    return [
        LimitlessJPCard(
            card_id="SV10-001",
            name_jp="リザードンex",
            name_en="Charizard ex",
            set_id="SV10",
            card_type="Pokemon",
            is_unreleased=True,
        ),
        LimitlessJPCard(
            card_id="SV10-045",
            name_jp="ナンジャモ",
            name_en=None,
            set_id="SV10",
            card_type="Trainer",
            is_unreleased=True,
        ),
        LimitlessJPCard(
            card_id="SV10-078",
            name_jp="テツノカイナex",
            name_en="Iron Hands ex",
            set_id="SV10",
            card_type="Pokemon",
            is_unreleased=True,
        ),
    ]


class TestMonitorCardRevealsResult:
    """Tests for MonitorCardRevealsResult dataclass."""

    def test_success_with_no_errors(self):
        """Result is successful when errors list is empty."""
        result = MonitorCardRevealsResult()
        assert result.success is True

    def test_failure_with_errors(self):
        """Result is not successful when errors list is non-empty."""
        result = MonitorCardRevealsResult(errors=["Something went wrong"])
        assert result.success is False

    def test_default_values(self):
        """Default values are all zero with empty error list."""
        result = MonitorCardRevealsResult()
        assert result.cards_checked == 0
        assert result.new_cards_found == 0
        assert result.cards_updated == 0
        assert result.cards_marked_released == 0
        assert result.errors == []


class TestCheckCardRevealsDryRun:
    """Tests for check_card_reveals in dry run mode."""

    @pytest.mark.asyncio
    async def test_dry_run_does_not_save(self, sample_unreleased_cards):
        """Verify dry run mode fetches but does not write to database."""
        mock_client = AsyncMock(spec=LimitlessClient)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.fetch_unreleased_cards.return_value = sample_unreleased_cards

        with patch(
            "src.pipelines.monitor_card_reveals.LimitlessClient",
            return_value=mock_client,
        ):
            result = await check_card_reveals(dry_run=True)

        assert result.success
        assert result.cards_checked == len(sample_unreleased_cards)
        assert result.new_cards_found == 0
        assert result.cards_updated == 0
        assert result.cards_marked_released == 0

    @pytest.mark.asyncio
    async def test_dry_run_does_not_open_db_session(self, sample_unreleased_cards):
        """Verify dry run never opens a database session."""
        mock_client = AsyncMock(spec=LimitlessClient)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.fetch_unreleased_cards.return_value = sample_unreleased_cards

        mock_session_factory = AsyncMock()

        with (
            patch(
                "src.pipelines.monitor_card_reveals.LimitlessClient",
                return_value=mock_client,
            ),
            patch(
                "src.pipelines.monitor_card_reveals.async_session_factory",
                mock_session_factory,
            ),
        ):
            await check_card_reveals(dry_run=True)

        mock_session_factory.assert_not_called()

    @pytest.mark.asyncio
    async def test_dry_run_with_empty_cards(self):
        """Verify dry run handles empty card list."""
        mock_client = AsyncMock(spec=LimitlessClient)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.fetch_unreleased_cards.return_value = []

        with patch(
            "src.pipelines.monitor_card_reveals.LimitlessClient",
            return_value=mock_client,
        ):
            result = await check_card_reveals(dry_run=True)

        assert result.success
        assert result.cards_checked == 0


class TestCheckCardRevealsLive:
    """Tests for check_card_reveals in live mode."""

    @pytest.mark.asyncio
    async def test_inserts_new_cards(self, sample_unreleased_cards):
        """Verify new cards are inserted into the database."""
        mock_client = AsyncMock(spec=LimitlessClient)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.fetch_unreleased_cards.return_value = sample_unreleased_cards

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        # No existing cards found for any query
        mock_existing_result = MagicMock()
        mock_existing_result.scalar_one_or_none.return_value = None
        # Tracked cards query returns empty
        mock_tracked_result = MagicMock()
        mock_tracked_result.scalars.return_value.all.return_value = []
        mock_session.execute.side_effect = [
            mock_existing_result,  # card 1 lookup
            mock_existing_result,  # card 2 lookup
            mock_existing_result,  # card 3 lookup
            mock_tracked_result,  # tracked cards query
        ]

        with (
            patch(
                "src.pipelines.monitor_card_reveals.LimitlessClient",
                return_value=mock_client,
            ),
            patch(
                "src.pipelines.monitor_card_reveals.async_session_factory",
                return_value=mock_session,
            ),
        ):
            result = await check_card_reveals(dry_run=False)

        assert result.success
        assert result.new_cards_found == 3
        assert result.cards_updated == 0
        assert mock_session.add.call_count == 3
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_updates_existing_card_with_new_en_name(
        self, sample_unreleased_cards
    ):
        """Verify existing cards are updated when new EN name is available."""
        mock_client = AsyncMock(spec=LimitlessClient)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        # Only one card for simplicity
        card = sample_unreleased_cards[0]
        mock_client.fetch_unreleased_cards.return_value = [card]

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        # Existing card without EN name
        existing_card = MagicMock(spec=JPUnreleasedCard)
        existing_card.jp_card_id = card.card_id
        existing_card.name_en = None  # No EN name yet
        existing_card.card_type = "Pokemon"
        existing_card.jp_set_id = "SV10"

        mock_existing_result = MagicMock()
        mock_existing_result.scalar_one_or_none.return_value = existing_card
        mock_tracked_result = MagicMock()
        mock_tracked_result.scalars.return_value.all.return_value = []
        mock_session.execute.side_effect = [
            mock_existing_result,
            mock_tracked_result,
        ]

        with (
            patch(
                "src.pipelines.monitor_card_reveals.LimitlessClient",
                return_value=mock_client,
            ),
            patch(
                "src.pipelines.monitor_card_reveals.async_session_factory",
                return_value=mock_session,
            ),
        ):
            result = await check_card_reveals(dry_run=False)

        assert result.success
        assert result.cards_updated == 1
        assert result.new_cards_found == 0
        assert existing_card.name_en == "Charizard ex"

    @pytest.mark.asyncio
    async def test_marks_released_cards(self, sample_unreleased_cards):
        """Verify cards no longer in unreleased list are marked as released."""
        mock_client = AsyncMock(spec=LimitlessClient)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        # Return empty unreleased list (all cards now released)
        mock_client.fetch_unreleased_cards.return_value = []

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        # Previously tracked unreleased cards in DB
        tracked_card = MagicMock(spec=JPUnreleasedCard)
        tracked_card.jp_card_id = "SV9-055"
        tracked_card.name_jp = "ピカチュウ"
        tracked_card.is_released = False

        mock_tracked_result = MagicMock()
        mock_tracked_result.scalars.return_value.all.return_value = [tracked_card]
        mock_session.execute.return_value = mock_tracked_result

        with (
            patch(
                "src.pipelines.monitor_card_reveals.LimitlessClient",
                return_value=mock_client,
            ),
            patch(
                "src.pipelines.monitor_card_reveals.async_session_factory",
                return_value=mock_session,
            ),
        ):
            result = await check_card_reveals(dry_run=False)

        assert result.success
        assert result.cards_marked_released == 1
        assert tracked_card.is_released is True

    @pytest.mark.asyncio
    async def test_does_not_mark_still_unreleased_cards(self):
        """Verify cards still in unreleased list are not marked released."""
        card = LimitlessJPCard(
            card_id="SV10-001",
            name_jp="リザードンex",
            set_id="SV10",
            card_type="Pokemon",
        )

        mock_client = AsyncMock(spec=LimitlessClient)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.fetch_unreleased_cards.return_value = [card]

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        # Card exists and is still unreleased
        existing_card = MagicMock(spec=JPUnreleasedCard)
        existing_card.jp_card_id = "SV10-001"
        existing_card.name_en = "Charizard ex"
        existing_card.card_type = "Pokemon"
        existing_card.jp_set_id = "SV10"
        existing_card.is_released = False

        mock_existing_result = MagicMock()
        mock_existing_result.scalar_one_or_none.return_value = existing_card
        mock_tracked_result = MagicMock()
        mock_tracked_result.scalars.return_value.all.return_value = [existing_card]
        mock_session.execute.side_effect = [
            mock_existing_result,
            mock_tracked_result,
        ]

        with (
            patch(
                "src.pipelines.monitor_card_reveals.LimitlessClient",
                return_value=mock_client,
            ),
            patch(
                "src.pipelines.monitor_card_reveals.async_session_factory",
                return_value=mock_session,
            ),
        ):
            result = await check_card_reveals(dry_run=False)

        assert result.cards_marked_released == 0
        assert existing_card.is_released is False


class TestCheckCardRevealsErrors:
    """Tests for error handling in check_card_reveals."""

    @pytest.mark.asyncio
    async def test_handles_limitless_error(self):
        """Verify LimitlessError is caught and recorded."""
        mock_client = AsyncMock(spec=LimitlessClient)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.fetch_unreleased_cards.side_effect = LimitlessError("API down")

        with patch(
            "src.pipelines.monitor_card_reveals.LimitlessClient",
            return_value=mock_client,
        ):
            result = await check_card_reveals(dry_run=False)

        assert not result.success
        assert len(result.errors) == 1
        assert "Error fetching unreleased cards" in result.errors[0]

    @pytest.mark.asyncio
    async def test_handles_generic_exception(self):
        """Verify unexpected exceptions are caught and recorded."""
        mock_client = AsyncMock(spec=LimitlessClient)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.fetch_unreleased_cards.side_effect = RuntimeError("unexpected")

        with patch(
            "src.pipelines.monitor_card_reveals.LimitlessClient",
            return_value=mock_client,
        ):
            result = await check_card_reveals(dry_run=False)

        assert not result.success
        assert len(result.errors) == 1
        assert "Pipeline error" in result.errors[0]

    @pytest.mark.asyncio
    async def test_handles_sqlalchemy_error_per_card(self):
        """Verify SQLAlchemy errors per card are recorded but pipeline continues."""
        card = LimitlessJPCard(
            card_id="SV10-001",
            name_jp="リザードンex",
            set_id="SV10",
            card_type="Pokemon",
        )

        mock_client = AsyncMock(spec=LimitlessClient)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.fetch_unreleased_cards.return_value = [card]

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        # First execute (card lookup) raises SQLAlchemy error
        mock_tracked_result = MagicMock()
        mock_tracked_result.scalars.return_value.all.return_value = []
        mock_session.execute.side_effect = [
            SQLAlchemyError("DB constraint violation"),
            mock_tracked_result,
        ]

        with (
            patch(
                "src.pipelines.monitor_card_reveals.LimitlessClient",
                return_value=mock_client,
            ),
            patch(
                "src.pipelines.monitor_card_reveals.async_session_factory",
                return_value=mock_session,
            ),
        ):
            result = await check_card_reveals(dry_run=False)

        assert not result.success
        assert len(result.errors) == 1
        assert "Error saving card SV10-001" in result.errors[0]
        # Pipeline should still commit tracked cards check
        mock_session.commit.assert_called_once()


class TestShouldUpdate:
    """Tests for _should_update helper function."""

    def test_update_when_en_name_added(self):
        """Should update when existing has no EN name but card does."""
        existing = MagicMock(spec=JPUnreleasedCard)
        existing.name_en = None
        existing.card_type = "Pokemon"
        existing.jp_set_id = "SV10"
        card = LimitlessJPCard(
            card_id="SV10-001", name_jp="テスト", name_en="Test", set_id="SV10"
        )
        assert _should_update(existing, card) is True

    def test_update_when_card_type_added(self):
        """Should update when existing has no card_type but card does."""
        existing = MagicMock(spec=JPUnreleasedCard)
        existing.name_en = "Test"
        existing.card_type = None
        existing.jp_set_id = "SV10"
        card = LimitlessJPCard(
            card_id="SV10-001",
            name_jp="テスト",
            name_en="Test",
            set_id="SV10",
            card_type="Pokemon",
        )
        assert _should_update(existing, card) is True

    def test_update_when_set_id_added(self):
        """Should update when existing has no jp_set_id but card does."""
        existing = MagicMock(spec=JPUnreleasedCard)
        existing.name_en = "Test"
        existing.card_type = "Pokemon"
        existing.jp_set_id = None
        card = LimitlessJPCard(
            card_id="SV10-001",
            name_jp="テスト",
            name_en="Test",
            set_id="SV10",
            card_type="Pokemon",
        )
        assert _should_update(existing, card) is True

    def test_no_update_when_data_same(self):
        """Should not update when existing already has all fields."""
        existing = MagicMock(spec=JPUnreleasedCard)
        existing.name_en = "Test"
        existing.card_type = "Pokemon"
        existing.jp_set_id = "SV10"
        card = LimitlessJPCard(
            card_id="SV10-001",
            name_jp="テスト",
            name_en="Test",
            set_id="SV10",
            card_type="Pokemon",
        )
        assert _should_update(existing, card) is False


class TestEstimateImpact:
    """Tests for _estimate_impact helper function."""

    def test_ex_card_high_impact(self):
        """Cards with 'ex' in name should have impact 4."""
        card = LimitlessJPCard(card_id="SV10-001", name_jp="リザードンex")
        assert _estimate_impact(card) == 4

    def test_vstar_card_high_impact(self):
        """Cards with 'vstar' in name should have impact 4."""
        card = LimitlessJPCard(card_id="SV10-001", name_jp="ギラティナVSTAR")
        assert _estimate_impact(card) == 4

    def test_ace_card_type_high_impact(self):
        """Cards with 'ace' card_type should have impact 4."""
        card = LimitlessJPCard(
            card_id="SV10-001", name_jp="プライムキャッチャー", card_type="ACE SPEC"
        )
        assert _estimate_impact(card) == 4

    def test_trainer_keyword_medium_impact(self):
        """Cards with trainer keywords should have impact 3."""
        card = LimitlessJPCard(card_id="SV10-001", name_jp="サポートカード")
        assert _estimate_impact(card) == 3

    def test_default_impact(self):
        """Cards without special keywords default to impact 3."""
        card = LimitlessJPCard(card_id="SV10-001", name_jp="ピカチュウ")
        assert _estimate_impact(card) == 3
