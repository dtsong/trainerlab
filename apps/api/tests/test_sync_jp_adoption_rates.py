"""Tests for JP card adoption rate sync pipeline."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from src.clients.pokecabook import (
    PokecabookAdoptionEntry,
    PokecabookAdoptionRates,
    PokecabookClient,
    PokecabookError,
)
from src.models.jp_card_adoption_rate import JPCardAdoptionRate
from src.pipelines.sync_jp_adoption_rates import (
    SyncAdoptionRatesResult,
    _generate_card_id,
    sync_adoption_rates,
)


@pytest.fixture
def sample_adoption_data() -> PokecabookAdoptionRates:
    """Create sample adoption rate data for testing."""
    return PokecabookAdoptionRates(
        date=date.today(),
        entries=[
            PokecabookAdoptionEntry(
                card_name_jp="ナンジャモ",
                inclusion_rate=0.85,
                card_name_en="Iono",
                avg_copies=2.5,
                archetype="general",
            ),
            PokecabookAdoptionEntry(
                card_name_jp="ボスの指令",
                inclusion_rate=0.72,
                card_name_en="Boss's Orders",
                avg_copies=2.0,
                archetype="general",
            ),
            PokecabookAdoptionEntry(
                card_name_jp="リザードンex",
                inclusion_rate=0.45,
                card_name_en="Charizard ex",
                avg_copies=2.0,
                archetype="charizard",
            ),
        ],
        source_url="https://pokecabook.com/adoption/",
    )


class TestSyncAdoptionRatesResult:
    """Tests for SyncAdoptionRatesResult dataclass."""

    def test_success_with_no_errors(self):
        """Result is successful when errors list is empty."""
        result = SyncAdoptionRatesResult()
        assert result.success is True

    def test_failure_with_errors(self):
        """Result is not successful when errors list is non-empty."""
        result = SyncAdoptionRatesResult(errors=["Fetch failed"])
        assert result.success is False

    def test_default_values(self):
        """Default values are all zero with empty error list."""
        result = SyncAdoptionRatesResult()
        assert result.rates_fetched == 0
        assert result.rates_created == 0
        assert result.rates_updated == 0
        assert result.rates_skipped == 0
        assert result.errors == []


class TestSyncAdoptionRatesDryRun:
    """Tests for sync_adoption_rates in dry run mode."""

    @pytest.mark.asyncio
    async def test_dry_run_does_not_save(self, sample_adoption_data):
        """Verify dry run mode fetches but does not write to database."""
        mock_client = AsyncMock(spec=PokecabookClient)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.fetch_adoption_rates.return_value = sample_adoption_data

        with patch(
            "src.pipelines.sync_jp_adoption_rates.PokecabookClient",
            return_value=mock_client,
        ):
            result = await sync_adoption_rates(dry_run=True)

        assert result.success
        assert result.rates_fetched == 3
        assert result.rates_created == 0
        assert result.rates_updated == 0

    @pytest.mark.asyncio
    async def test_dry_run_does_not_open_db_session(self, sample_adoption_data):
        """Verify dry run never opens a database session."""
        mock_client = AsyncMock(spec=PokecabookClient)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.fetch_adoption_rates.return_value = sample_adoption_data

        mock_session_factory = AsyncMock()

        with (
            patch(
                "src.pipelines.sync_jp_adoption_rates.PokecabookClient",
                return_value=mock_client,
            ),
            patch(
                "src.pipelines.sync_jp_adoption_rates.async_session_factory",
                mock_session_factory,
            ),
        ):
            await sync_adoption_rates(dry_run=True)

        mock_session_factory.assert_not_called()


class TestSyncAdoptionRatesLive:
    """Tests for sync_adoption_rates in live mode."""

    @pytest.mark.asyncio
    async def test_creates_new_rates(self, sample_adoption_data):
        """Verify new adoption rates are created in database."""
        mock_client = AsyncMock(spec=PokecabookClient)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.fetch_adoption_rates.return_value = sample_adoption_data

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        # No existing rates found
        mock_existing_result = MagicMock()
        mock_existing_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_existing_result

        with (
            patch(
                "src.pipelines.sync_jp_adoption_rates.PokecabookClient",
                return_value=mock_client,
            ),
            patch(
                "src.pipelines.sync_jp_adoption_rates.async_session_factory",
                return_value=mock_session,
            ),
        ):
            result = await sync_adoption_rates(dry_run=False)

        assert result.success
        assert result.rates_created == 3
        assert result.rates_updated == 0
        assert mock_session.add.call_count == 3
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_updates_existing_rates(self, sample_adoption_data):
        """Verify existing rates are updated with new data."""
        mock_client = AsyncMock(spec=PokecabookClient)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.fetch_adoption_rates.return_value = sample_adoption_data

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        # All entries already exist
        existing_rate = MagicMock(spec=JPCardAdoptionRate)
        mock_existing_result = MagicMock()
        mock_existing_result.scalar_one_or_none.return_value = existing_rate
        mock_session.execute.return_value = mock_existing_result

        with (
            patch(
                "src.pipelines.sync_jp_adoption_rates.PokecabookClient",
                return_value=mock_client,
            ),
            patch(
                "src.pipelines.sync_jp_adoption_rates.async_session_factory",
                return_value=mock_session,
            ),
        ):
            result = await sync_adoption_rates(dry_run=False)

        assert result.success
        assert result.rates_updated == 3
        assert result.rates_created == 0
        # session.add should not be called for updates
        mock_session.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_entries_with_no_card_name(self):
        """Verify entries without card_name_jp are skipped."""
        adoption_data = PokecabookAdoptionRates(
            date=date.today(),
            entries=[
                PokecabookAdoptionEntry(
                    card_name_jp="",
                    inclusion_rate=0.5,
                ),
                PokecabookAdoptionEntry(
                    card_name_jp="",
                    inclusion_rate=0.5,
                ),
            ],
            source_url="https://pokecabook.com/adoption/",
        )

        mock_client = AsyncMock(spec=PokecabookClient)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.fetch_adoption_rates.return_value = adoption_data

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with (
            patch(
                "src.pipelines.sync_jp_adoption_rates.PokecabookClient",
                return_value=mock_client,
            ),
            patch(
                "src.pipelines.sync_jp_adoption_rates.async_session_factory",
                return_value=mock_session,
            ),
        ):
            result = await sync_adoption_rates(dry_run=False)

        assert result.rates_skipped == 2
        assert result.rates_created == 0

    @pytest.mark.asyncio
    async def test_skips_entries_with_zero_inclusion_rate(self):
        """Verify entries with inclusion_rate <= 0 are skipped."""
        adoption_data = PokecabookAdoptionRates(
            date=date.today(),
            entries=[
                PokecabookAdoptionEntry(
                    card_name_jp="テストカード",
                    inclusion_rate=0.0,
                ),
                PokecabookAdoptionEntry(
                    card_name_jp="テストカード2",
                    inclusion_rate=-0.1,
                ),
            ],
            source_url="https://pokecabook.com/adoption/",
        )

        mock_client = AsyncMock(spec=PokecabookClient)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.fetch_adoption_rates.return_value = adoption_data

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with (
            patch(
                "src.pipelines.sync_jp_adoption_rates.PokecabookClient",
                return_value=mock_client,
            ),
            patch(
                "src.pipelines.sync_jp_adoption_rates.async_session_factory",
                return_value=mock_session,
            ),
        ):
            result = await sync_adoption_rates(dry_run=False)

        assert result.rates_skipped == 2
        assert result.rates_created == 0


class TestSyncAdoptionRatesErrors:
    """Tests for error handling in sync_adoption_rates."""

    @pytest.mark.asyncio
    async def test_handles_pokecabook_error(self):
        """Verify PokecabookError is caught and recorded."""
        mock_client = AsyncMock(spec=PokecabookClient)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.fetch_adoption_rates.side_effect = PokecabookError("Site down")

        with patch(
            "src.pipelines.sync_jp_adoption_rates.PokecabookClient",
            return_value=mock_client,
        ):
            result = await sync_adoption_rates(dry_run=False)

        assert not result.success
        assert len(result.errors) == 1
        assert "Error fetching adoption rates" in result.errors[0]

    @pytest.mark.asyncio
    async def test_handles_generic_exception(self):
        """Verify unexpected exceptions are caught and recorded."""
        mock_client = AsyncMock(spec=PokecabookClient)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.fetch_adoption_rates.side_effect = RuntimeError("unexpected")

        with patch(
            "src.pipelines.sync_jp_adoption_rates.PokecabookClient",
            return_value=mock_client,
        ):
            result = await sync_adoption_rates(dry_run=False)

        assert not result.success
        assert len(result.errors) == 1
        assert "Pipeline error" in result.errors[0]

    @pytest.mark.asyncio
    async def test_handles_sqlalchemy_error_per_entry(self, sample_adoption_data):
        """Verify SQLAlchemy errors on individual entries are recorded but continue."""
        mock_client = AsyncMock(spec=PokecabookClient)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.fetch_adoption_rates.return_value = sample_adoption_data

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        # First DB write path fails, subsequent calls succeed.
        mock_no_existing = MagicMock()
        mock_no_existing.scalar_one_or_none.return_value = None
        mock_no_existing.first.return_value = None
        mock_no_existing.scalars.return_value.all.return_value = []

        call_count = {"n": 0}

        async def execute_side_effect(*_args, **_kwargs):
            call_count["n"] += 1
            if call_count["n"] == 1:
                raise SQLAlchemyError("DB error")
            return mock_no_existing

        mock_session.execute.side_effect = execute_side_effect

        with (
            patch(
                "src.pipelines.sync_jp_adoption_rates.PokecabookClient",
                return_value=mock_client,
            ),
            patch(
                "src.pipelines.sync_jp_adoption_rates.async_session_factory",
                return_value=mock_session,
            ),
        ):
            result = await sync_adoption_rates(dry_run=False)

        assert not result.success
        assert len(result.errors) == 1
        assert "Error saving rate for ナンジャモ" in result.errors[0]
        # Other two should still be processed
        assert result.rates_created == 2
        mock_session.commit.assert_called_once()


class TestSyncAdoptionRatesMappingMetrics:
    """Tests for mapping coverage diagnostics."""

    @pytest.mark.asyncio
    async def test_tracks_unresolved_mapping_coverage(self):
        adoption_data = PokecabookAdoptionRates(
            date=date.today(),
            entries=[
                PokecabookAdoptionEntry(
                    card_name_jp="未知カード",
                    card_name_en="Unknown Card",
                    inclusion_rate=0.33,
                    avg_copies=1.0,
                )
            ],
            source_url="https://pokecabook.com/adoption/",
        )

        mock_client = AsyncMock(spec=PokecabookClient)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.fetch_adoption_rates.return_value = adoption_data

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        empty_result = MagicMock()
        empty_result.first.return_value = None
        empty_result.scalar_one_or_none.return_value = None
        empty_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = empty_result

        with (
            patch(
                "src.pipelines.sync_jp_adoption_rates.PokecabookClient",
                return_value=mock_client,
            ),
            patch(
                "src.pipelines.sync_jp_adoption_rates.async_session_factory",
                return_value=mock_session,
            ),
        ):
            result = await sync_adoption_rates(dry_run=False)

        assert result.mapping_unresolved == 1
        assert result.mapping_resolved == 0
        assert result.mapping_coverage == 0.0
        assert result.unmapped_by_source["https://pokecabook.com/adoption/"] == 1
        assert "未知カード" in result.unmapped_card_samples


class TestGenerateCardId:
    """Tests for _generate_card_id helper function."""

    def test_generates_stable_id(self):
        """Same input always produces same output."""
        id1 = _generate_card_id("ナンジャモ")
        id2 = _generate_card_id("ナンジャモ")
        assert id1 == id2

    def test_generates_prefixed_id(self):
        """Generated ID starts with 'jp-' prefix."""
        card_id = _generate_card_id("テストカード")
        assert card_id.startswith("jp-")

    def test_different_names_produce_different_ids(self):
        """Different card names produce different IDs."""
        id1 = _generate_card_id("ナンジャモ")
        id2 = _generate_card_id("ボスの指令")
        assert id1 != id2

    def test_id_has_correct_format(self):
        """Generated ID is 'jp-' followed by 8 hex characters."""
        card_id = _generate_card_id("テスト")
        assert len(card_id) == 11  # "jp-" (3) + 8 hex chars
        hex_part = card_id[3:]
        assert all(c in "0123456789abcdef" for c in hex_part)
