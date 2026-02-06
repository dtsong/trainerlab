"""Tests for JP-to-EN card ID mapping sync pipeline."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.clients.limitless import CardEquivalent, LimitlessClient, LimitlessError
from src.models.card_id_mapping import CardIdMapping
from src.pipelines.sync_card_mappings import (
    SyncMappingsResult,
    get_en_to_jp_mapping,
    get_jp_to_en_mapping,
    sync_all_card_mappings,
    sync_card_mappings_for_set,
    sync_recent_jp_sets,
)


@pytest.fixture
def sample_equivalents() -> list[CardEquivalent]:
    """Create sample card equivalents for testing."""
    return [
        CardEquivalent(
            jp_card_id="SV7-018",
            en_card_id="sv7-28",
            card_name_en="Charizard ex",
            jp_set_id="SV7",
            en_set_id="sv7",
        ),
        CardEquivalent(
            jp_card_id="SV7-055",
            en_card_id="sv7-65",
            card_name_en="Iron Valiant ex",
            jp_set_id="SV7",
            en_set_id="sv7",
        ),
        CardEquivalent(
            jp_card_id="SV7-072",
            en_card_id="sv7-80",
            card_name_en="Iono",
            jp_set_id="SV7",
            en_set_id="sv7",
        ),
    ]


class TestSyncMappingsResult:
    """Tests for SyncMappingsResult dataclass."""

    def test_success_with_no_errors(self):
        """Result is successful when errors list is empty."""
        result = SyncMappingsResult()
        assert result.success is True

    def test_failure_with_errors(self):
        """Result is not successful when errors list is non-empty."""
        result = SyncMappingsResult(errors=["Failed to sync set"])
        assert result.success is False

    def test_default_values(self):
        """Default values are all zero with empty error list."""
        result = SyncMappingsResult()
        assert result.sets_processed == 0
        assert result.mappings_found == 0
        assert result.mappings_inserted == 0
        assert result.mappings_updated == 0
        assert result.errors == []


class TestSyncCardMappingsForSet:
    """Tests for sync_card_mappings_for_set function."""

    @pytest.mark.asyncio
    async def test_inserts_new_mappings(self, sample_equivalents):
        """Verify new mappings are inserted when none exist."""
        mock_session = AsyncMock()
        mock_client = AsyncMock(spec=LimitlessClient)
        mock_client.fetch_card_equivalents.return_value = sample_equivalents

        # No existing mappings in DB
        mock_existing_result = MagicMock()
        mock_existing_result.__iter__ = MagicMock(return_value=iter([]))
        mock_session.execute.return_value = mock_existing_result

        inserted, updated = await sync_card_mappings_for_set(
            mock_session, mock_client, "SV7"
        )

        assert inserted == 3
        assert updated == 0
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_updates_existing_mappings(self, sample_equivalents):
        """Verify existing mappings are counted as updates."""
        mock_session = AsyncMock()
        mock_client = AsyncMock(spec=LimitlessClient)
        mock_client.fetch_card_equivalents.return_value = sample_equivalents

        # Two of three already exist in DB
        existing_rows = [("SV7-018",), ("SV7-055",)]
        mock_existing_result = MagicMock()
        mock_existing_result.__iter__ = MagicMock(return_value=iter(existing_rows))
        mock_session.execute.return_value = mock_existing_result

        inserted, updated = await sync_card_mappings_for_set(
            mock_session, mock_client, "SV7"
        )

        assert inserted == 1
        assert updated == 2
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_zero_for_empty_equivalents(self):
        """Verify zero counts when no equivalents found."""
        mock_session = AsyncMock()
        mock_client = AsyncMock(spec=LimitlessClient)
        mock_client.fetch_card_equivalents.return_value = []

        inserted, updated = await sync_card_mappings_for_set(
            mock_session, mock_client, "SV7"
        )

        assert inserted == 0
        assert updated == 0
        mock_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_calls_fetch_card_equivalents_with_set_id(self):
        """Verify correct set ID is passed to client."""
        mock_session = AsyncMock()
        mock_client = AsyncMock(spec=LimitlessClient)
        mock_client.fetch_card_equivalents.return_value = []

        await sync_card_mappings_for_set(mock_session, mock_client, "SV9a")

        mock_client.fetch_card_equivalents.assert_called_once_with("SV9a")


class TestSyncAllCardMappings:
    """Tests for sync_all_card_mappings function."""

    @pytest.mark.asyncio
    async def test_dry_run_returns_early(self):
        """Verify dry run returns immediately without opening clients."""
        result = await sync_all_card_mappings(dry_run=True)

        assert result.success
        assert result.sets_processed == 0

    @pytest.mark.asyncio
    async def test_syncs_provided_sets(self, sample_equivalents):
        """Verify sync processes each provided set."""
        mock_client = AsyncMock(spec=LimitlessClient)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.fetch_card_equivalents.return_value = sample_equivalents

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        # Existing ID query returns empty each time
        mock_existing_result = MagicMock()
        mock_existing_result.__iter__ = MagicMock(return_value=iter([]))
        mock_session.execute.return_value = mock_existing_result

        with (
            patch(
                "src.pipelines.sync_card_mappings.LimitlessClient",
                return_value=mock_client,
            ),
            patch(
                "src.pipelines.sync_card_mappings.async_session_factory",
                return_value=mock_session,
            ),
        ):
            result = await sync_all_card_mappings(jp_sets=["SV7", "SV8"], dry_run=False)

        assert result.sets_processed == 2
        assert mock_client.fetch_card_equivalents.call_count == 2

    @pytest.mark.asyncio
    async def test_fetches_sets_from_client_when_none_provided(self):
        """Verify client.fetch_jp_sets is called when jp_sets is None."""
        mock_client = AsyncMock(spec=LimitlessClient)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.fetch_jp_sets.return_value = ["SV7"]
        mock_client.fetch_card_equivalents.return_value = []

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.execute.return_value = MagicMock(
            __iter__=MagicMock(return_value=iter([]))
        )

        with (
            patch(
                "src.pipelines.sync_card_mappings.LimitlessClient",
                return_value=mock_client,
            ),
            patch(
                "src.pipelines.sync_card_mappings.async_session_factory",
                return_value=mock_session,
            ),
        ):
            result = await sync_all_card_mappings(jp_sets=None, dry_run=False)

        mock_client.fetch_jp_sets.assert_called_once()
        assert result.sets_processed == 1

    @pytest.mark.asyncio
    async def test_handles_limitless_error_fetching_sets(self):
        """Verify LimitlessError when fetching set list is handled."""
        mock_client = AsyncMock(spec=LimitlessClient)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.fetch_jp_sets.side_effect = LimitlessError("Fetch failed")

        with patch(
            "src.pipelines.sync_card_mappings.LimitlessClient",
            return_value=mock_client,
        ):
            result = await sync_all_card_mappings(jp_sets=None, dry_run=False)

        assert not result.success
        assert len(result.errors) == 1
        assert "Error fetching JP set list" in result.errors[0]

    @pytest.mark.asyncio
    async def test_handles_limitless_error_per_set(self):
        """Verify LimitlessError on individual sets is recorded and continues."""
        mock_client = AsyncMock(spec=LimitlessClient)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.fetch_card_equivalents.side_effect = LimitlessError("Set error")

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with (
            patch(
                "src.pipelines.sync_card_mappings.LimitlessClient",
                return_value=mock_client,
            ),
            patch(
                "src.pipelines.sync_card_mappings.async_session_factory",
                return_value=mock_session,
            ),
        ):
            result = await sync_all_card_mappings(jp_sets=["SV7", "SV8"], dry_run=False)

        assert not result.success
        assert len(result.errors) == 2
        assert result.sets_processed == 0

    @pytest.mark.asyncio
    async def test_accumulates_stats_across_sets(self, sample_equivalents):
        """Verify statistics are accumulated across multiple sets."""
        mock_client = AsyncMock(spec=LimitlessClient)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.fetch_card_equivalents.return_value = sample_equivalents

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_existing_result = MagicMock()
        mock_existing_result.__iter__ = MagicMock(return_value=iter([]))
        mock_session.execute.return_value = mock_existing_result

        with (
            patch(
                "src.pipelines.sync_card_mappings.LimitlessClient",
                return_value=mock_client,
            ),
            patch(
                "src.pipelines.sync_card_mappings.async_session_factory",
                return_value=mock_session,
            ),
        ):
            result = await sync_all_card_mappings(jp_sets=["SV7", "SV8"], dry_run=False)

        assert result.sets_processed == 2
        # 3 equivalents per set * 2 sets
        assert result.mappings_found == 6
        assert result.mappings_inserted == 6


class TestSyncRecentJpSets:
    """Tests for sync_recent_jp_sets function."""

    @pytest.mark.asyncio
    async def test_fetches_and_syncs_recent_sets(self):
        """Verify it fetches all sets and syncs only recent ones."""
        all_sets = ["SV10", "SV9a", "SV9", "SV8a", "SV8", "SV7", "SV6"]

        mock_client = AsyncMock(spec=LimitlessClient)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.fetch_jp_sets.return_value = all_sets

        mock_sync_all = AsyncMock(return_value=SyncMappingsResult(sets_processed=3))

        with (
            patch(
                "src.pipelines.sync_card_mappings.LimitlessClient",
                return_value=mock_client,
            ),
            patch(
                "src.pipelines.sync_card_mappings.sync_all_card_mappings",
                mock_sync_all,
            ),
        ):
            result = await sync_recent_jp_sets(lookback_sets=3, dry_run=False)

        # Should pass first 3 sets to sync_all
        mock_sync_all.assert_called_once_with(
            jp_sets=["SV10", "SV9a", "SV9"], dry_run=False
        )
        assert result.sets_processed == 3

    @pytest.mark.asyncio
    async def test_handles_error_fetching_sets(self):
        """Verify error fetching sets list is handled."""
        mock_client = AsyncMock(spec=LimitlessClient)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.fetch_jp_sets.side_effect = LimitlessError("Connection failed")

        with patch(
            "src.pipelines.sync_card_mappings.LimitlessClient",
            return_value=mock_client,
        ):
            result = await sync_recent_jp_sets(lookback_sets=5, dry_run=False)

        assert not result.success
        assert len(result.errors) == 1
        assert "Error fetching JP set list" in result.errors[0]

    @pytest.mark.asyncio
    async def test_default_lookback_is_five(self):
        """Verify default lookback_sets parameter is 5."""
        all_sets = ["SV10", "SV9a", "SV9", "SV8a", "SV8", "SV7"]

        mock_client = AsyncMock(spec=LimitlessClient)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.fetch_jp_sets.return_value = all_sets

        mock_sync_all = AsyncMock(return_value=SyncMappingsResult())

        with (
            patch(
                "src.pipelines.sync_card_mappings.LimitlessClient",
                return_value=mock_client,
            ),
            patch(
                "src.pipelines.sync_card_mappings.sync_all_card_mappings",
                mock_sync_all,
            ),
        ):
            await sync_recent_jp_sets(dry_run=False)

        mock_sync_all.assert_called_once_with(
            jp_sets=["SV10", "SV9a", "SV9", "SV8a", "SV8"], dry_run=False
        )


class TestGetJpToEnMapping:
    """Tests for get_jp_to_en_mapping function."""

    @pytest.mark.asyncio
    async def test_returns_mapping_dict(self):
        """Verify correct dict mapping from JP to EN card IDs."""
        mock_session = AsyncMock()
        mock_rows = [
            MagicMock(jp_card_id="SV7-018", en_card_id="sv7-28"),
            MagicMock(jp_card_id="SV7-055", en_card_id="sv7-65"),
        ]
        mock_result = MagicMock()
        mock_result.__iter__ = MagicMock(return_value=iter(mock_rows))
        mock_session.execute.return_value = mock_result

        mapping = await get_jp_to_en_mapping(mock_session)

        assert mapping == {"SV7-018": "sv7-28", "SV7-055": "sv7-65"}

    @pytest.mark.asyncio
    async def test_returns_empty_dict_when_no_mappings(self):
        """Verify empty dict when no mappings in database."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.__iter__ = MagicMock(return_value=iter([]))
        mock_session.execute.return_value = mock_result

        mapping = await get_jp_to_en_mapping(mock_session)

        assert mapping == {}


class TestGetEnToJpMapping:
    """Tests for get_en_to_jp_mapping function."""

    @pytest.mark.asyncio
    async def test_returns_mapping_with_lists(self):
        """Verify EN-to-JP mapping returns lists of JP card IDs."""
        mock_session = AsyncMock()
        mock_rows = [
            MagicMock(en_card_id="sv7-28", jp_card_id="SV7-018"),
            MagicMock(en_card_id="sv7-28", jp_card_id="SV7a-010"),
            MagicMock(en_card_id="sv7-65", jp_card_id="SV7-055"),
        ]
        mock_result = MagicMock()
        mock_result.__iter__ = MagicMock(return_value=iter(mock_rows))
        mock_session.execute.return_value = mock_result

        mapping = await get_en_to_jp_mapping(mock_session)

        assert mapping == {
            "sv7-28": ["SV7-018", "SV7a-010"],
            "sv7-65": ["SV7-055"],
        }

    @pytest.mark.asyncio
    async def test_returns_empty_dict_when_no_mappings(self):
        """Verify empty dict when no mappings in database."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.__iter__ = MagicMock(return_value=iter([]))
        mock_session.execute.return_value = mock_result

        mapping = await get_en_to_jp_mapping(mock_session)

        assert mapping == {}


class TestCardIdMappingConfidence:
    """Tests for confidence column on CardIdMapping."""

    def test_confidence_column_exists(self):
        """CardIdMapping model should have a confidence column."""
        columns = CardIdMapping.__table__.columns
        assert "confidence" in columns

    def test_confidence_defaults_to_one(self):
        """Confidence server_default should be 1.0."""
        col = CardIdMapping.__table__.columns["confidence"]
        assert col.server_default.arg == "1.0"

    def test_confidence_not_nullable(self):
        """Confidence column should not be nullable."""
        col = CardIdMapping.__table__.columns["confidence"]
        assert col.nullable is False
