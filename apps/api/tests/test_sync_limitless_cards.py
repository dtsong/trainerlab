"""Tests for the sync_limitless_cards pipeline."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.clients.limitless import LimitlessENCard, LimitlessError
from src.pipelines.sync_limitless_cards import (
    SyncLimitlessCardsResult,
    sync_limitless_cards,
)


def _make_mock_client(
    set_codes: list[str] | None = None,
    cards_by_set: dict[str, list[LimitlessENCard]] | None = None,
) -> AsyncMock:
    """Build a mock LimitlessClient configured for common test scenarios."""
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    if set_codes is not None:
        mock_client.fetch_en_sets.return_value = set_codes

    if cards_by_set is not None:

        async def fetch_set_cards(set_code: str) -> list[LimitlessENCard]:
            return cards_by_set.get(set_code, [])

        mock_client.fetch_en_set_cards.side_effect = fetch_set_cards

    return mock_client


def _make_mock_session(matched_card_id: str | None = None) -> AsyncMock:
    """Build a mock AsyncSession.

    If matched_card_id is provided, the first session.execute() call
    returns a result whose .first() yields (matched_card_id,).
    Subsequent calls return an empty result (for the UPDATE statement).
    """
    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    if matched_card_id is not None:
        found_result = MagicMock()
        found_result.first.return_value = (matched_card_id,)
        empty_result = MagicMock()
        empty_result.first.return_value = None
        # SELECT returns match; UPDATE result is not inspected by the pipeline
        mock_session.execute.side_effect = [found_result, empty_result]
    else:
        empty_result = MagicMock()
        empty_result.first.return_value = None
        mock_session.execute.return_value = empty_result

    return mock_session


class TestSyncLimitlessCardsResult:
    """Unit tests for the SyncLimitlessCardsResult dataclass."""

    def test_success_when_no_errors(self) -> None:
        result = SyncLimitlessCardsResult()
        assert result.success is True

    def test_failure_when_errors_present(self) -> None:
        result = SyncLimitlessCardsResult(errors=["Something broke"])
        assert result.success is False

    def test_default_field_values(self) -> None:
        result = SyncLimitlessCardsResult()
        assert result.sets_processed == 0
        assert result.cards_found == 0
        assert result.cards_mapped == 0
        assert result.cards_unmatched == 0
        assert result.errors == []


class TestSyncMapsCardsCorrectly:
    """Test that the pipeline correctly maps matched cards and counts unmatched."""

    @pytest.mark.asyncio
    async def test_sync_maps_cards_correctly(self) -> None:
        """One set, two cards: one matched in DB, one unmatched."""
        cards = [
            LimitlessENCard(set_code="OBF", card_number="125"),
            LimitlessENCard(set_code="OBF", card_number="200"),
        ]

        mock_client = _make_mock_client(
            set_codes=["OBF"],
            cards_by_set={"OBF": cards},
        )

        # First SELECT hits a match; second SELECT finds nothing
        found_result = MagicMock()
        found_result.first.return_value = ("sv3-125",)
        not_found_result = MagicMock()
        not_found_result.first.return_value = None
        # Two SELECTs + one UPDATE (order: SELECT card1, UPDATE card1, SELECT card2)
        update_result = MagicMock()
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.execute.side_effect = [
            found_result,
            update_result,
            not_found_result,
        ]

        with (
            patch(
                "src.pipelines.sync_limitless_cards.LimitlessClient",
                return_value=mock_client,
            ),
            patch(
                "src.pipelines.sync_limitless_cards.async_session_factory",
                return_value=mock_session,
            ),
        ):
            result = await sync_limitless_cards()

        assert result.sets_processed == 1
        assert result.cards_found == 2
        assert result.cards_mapped == 1
        assert result.cards_unmatched == 1
        assert result.success is True


class TestSyncHandlesMissingSets:
    """Test that a LimitlessError when fetching set list is captured."""

    @pytest.mark.asyncio
    async def test_sync_handles_missing_sets(self) -> None:
        """LimitlessError on fetch_en_sets is captured in result.errors."""
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.fetch_en_sets.side_effect = LimitlessError("Network error")

        with patch(
            "src.pipelines.sync_limitless_cards.LimitlessClient",
            return_value=mock_client,
        ):
            result = await sync_limitless_cards()

        assert result.success is False
        assert len(result.errors) == 1
        assert "Failed to fetch EN sets" in result.errors[0]
        assert result.sets_processed == 0
        assert result.cards_mapped == 0


class TestSyncIdempotentRerun:
    """Test that running the sync twice yields the same cards_mapped count."""

    @pytest.mark.asyncio
    async def test_sync_idempotent_rerun(self) -> None:
        """Two successive runs produce the same cards_mapped result."""
        card = LimitlessENCard(set_code="OBF", card_number="125")

        def _build_client() -> AsyncMock:
            return _make_mock_client(
                set_codes=["OBF"],
                cards_by_set={"OBF": [card]},
            )

        def _build_session() -> AsyncMock:
            return _make_mock_session(matched_card_id="sv3-125")

        with (
            patch(
                "src.pipelines.sync_limitless_cards.LimitlessClient",
            ) as mock_client_cls,
            patch(
                "src.pipelines.sync_limitless_cards.async_session_factory",
            ) as mock_sf,
        ):
            mock_client_cls.return_value = _build_client()
            mock_sf.return_value = _build_session()
            result_first = await sync_limitless_cards()

            mock_client_cls.return_value = _build_client()
            mock_sf.return_value = _build_session()
            result_second = await sync_limitless_cards()

        assert result_first.cards_mapped == result_second.cards_mapped
        assert result_first.cards_mapped == 1


class TestSyncDryRunDoesNotCommit:
    """Test that dry_run=True rolls back instead of committing."""

    @pytest.mark.asyncio
    async def test_sync_dry_run_does_not_commit(self) -> None:
        """With dry_run=True, session.rollback is called and commit is not."""
        card = LimitlessENCard(set_code="OBF", card_number="125")
        mock_client = _make_mock_client(
            set_codes=["OBF"],
            cards_by_set={"OBF": [card]},
        )
        mock_session = _make_mock_session(matched_card_id="sv3-125")

        with (
            patch(
                "src.pipelines.sync_limitless_cards.LimitlessClient",
                return_value=mock_client,
            ),
            patch(
                "src.pipelines.sync_limitless_cards.async_session_factory",
                return_value=mock_session,
            ),
        ):
            result = await sync_limitless_cards(dry_run=True)

        mock_session.rollback.assert_called_once()
        mock_session.commit.assert_not_called()
        assert result.cards_mapped == 1


class TestSyncSpecificSets:
    """Test that passing sets= restricts processing to those sets only."""

    @pytest.mark.asyncio
    async def test_sync_specific_sets(self) -> None:
        """Only the requested set is processed; fetch_en_sets is not called."""
        card = LimitlessENCard(set_code="OBF", card_number="125")
        mock_client = _make_mock_client(
            cards_by_set={"OBF": [card]},
        )
        mock_session = _make_mock_session(matched_card_id="sv3-125")

        with (
            patch(
                "src.pipelines.sync_limitless_cards.LimitlessClient",
                return_value=mock_client,
            ),
            patch(
                "src.pipelines.sync_limitless_cards.async_session_factory",
                return_value=mock_session,
            ),
        ):
            result = await sync_limitless_cards(sets=["OBF"])

        # fetch_en_sets must NOT have been called when sets= is provided
        mock_client.fetch_en_sets.assert_not_called()
        mock_client.fetch_en_set_cards.assert_called_once_with("OBF")

        assert result.sets_processed == 1
        assert result.cards_mapped == 1

    @pytest.mark.asyncio
    async def test_sync_specific_sets_normalises_to_upper(self) -> None:
        """Lowercase set codes in sets= are normalised to uppercase."""
        mock_client = _make_mock_client(
            cards_by_set={"OBF": []},
        )
        mock_session = _make_mock_session()

        with (
            patch(
                "src.pipelines.sync_limitless_cards.LimitlessClient",
                return_value=mock_client,
            ),
            patch(
                "src.pipelines.sync_limitless_cards.async_session_factory",
                return_value=mock_session,
            ),
        ):
            await sync_limitless_cards(sets=["obf"])

        mock_client.fetch_en_set_cards.assert_called_once_with("OBF")
