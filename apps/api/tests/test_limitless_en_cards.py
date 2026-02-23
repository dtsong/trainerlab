"""Tests for LimitlessENCard dataclass and EN card database methods."""

from unittest.mock import AsyncMock, patch

import pytest

from src.clients.limitless import LimitlessClient, LimitlessENCard

SETS_PAGE_HTML = """\
<html><body>
<a href="/cards/en/OBF/">Obsidian Flames</a>
<a href="/cards/en/SCR/">Stellar Crown</a>
<a href="/cards/en/OBF/">Obsidian Flames</a>
</body></html>
"""

SET_CARDS_HTML = """\
<html><body>
<a href="/cards/en/OBF/1"><img class="card" /></a>
<a href="/cards/en/OBF/125"><img class="card" /></a>
<a href="/cards/en/OBF/125"><img class="card" /></a>
<a href="/cards/en/OBF/200"><img class="card" /></a>
</body></html>
"""


class TestLimitlessENCard:
    """Tests for LimitlessENCard dataclass."""

    def test_limitless_id_combines_set_code_and_card_number(self) -> None:
        """limitless_id should return '{set_code}-{card_number}'."""
        card = LimitlessENCard(set_code="OBF", card_number="125")
        assert card.limitless_id == "OBF-125"

    def test_limitless_id_single_digit_card_number(self) -> None:
        """limitless_id should work with single-digit card numbers."""
        card = LimitlessENCard(set_code="OBF", card_number="1")
        assert card.limitless_id == "OBF-1"

    def test_limitless_id_different_set_codes(self) -> None:
        """limitless_id should use whichever set code is stored."""
        card = LimitlessENCard(set_code="SCR", card_number="200")
        assert card.limitless_id == "SCR-200"

    def test_stores_set_code_and_card_number(self) -> None:
        """Dataclass fields should be accessible directly."""
        card = LimitlessENCard(set_code="TWM", card_number="042")
        assert card.set_code == "TWM"
        assert card.card_number == "042"


class TestFetchEnSets:
    """Tests for LimitlessClient.fetch_en_sets()."""

    @pytest.fixture
    def client(self) -> LimitlessClient:
        return LimitlessClient(requests_per_minute=100, max_concurrent=10)

    @pytest.mark.asyncio
    async def test_parses_set_codes_from_href(self, client: LimitlessClient) -> None:
        """Should extract set codes from /cards/en/<SET>/ href patterns."""
        with patch.object(client, "_get_official", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = SETS_PAGE_HTML

            sets = await client.fetch_en_sets()

            assert "OBF" in sets
            assert "SCR" in sets

    @pytest.mark.asyncio
    async def test_deduplicates_set_codes(self, client: LimitlessClient) -> None:
        """Should not return duplicate set codes when links repeat."""
        with patch.object(client, "_get_official", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = SETS_PAGE_HTML

            sets = await client.fetch_en_sets()

            assert sets.count("OBF") == 1

    @pytest.mark.asyncio
    async def test_returns_correct_count(self, client: LimitlessClient) -> None:
        """Should return exactly as many unique set codes as are in the page."""
        with patch.object(client, "_get_official", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = SETS_PAGE_HTML

            sets = await client.fetch_en_sets()

            # OBF and SCR — OBF appears twice but deduplicated
            assert len(sets) == 2

    @pytest.mark.asyncio
    async def test_calls_correct_endpoint(self, client: LimitlessClient) -> None:
        """Should request the /cards/en endpoint."""
        with patch.object(client, "_get_official", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = SETS_PAGE_HTML

            await client.fetch_en_sets()

            mock_get.assert_called_once_with("/cards/en")

    @pytest.mark.asyncio
    async def test_returns_empty_list_for_page_with_no_set_links(
        self, client: LimitlessClient
    ) -> None:
        """Should return an empty list when no matching hrefs are present."""
        with patch.object(client, "_get_official", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = "<html><body><p>Nothing here</p></body></html>"

            sets = await client.fetch_en_sets()

            assert sets == []


class TestFetchEnSetCards:
    """Tests for LimitlessClient.fetch_en_set_cards()."""

    @pytest.fixture
    def client(self) -> LimitlessClient:
        return LimitlessClient(requests_per_minute=100, max_concurrent=10)

    @pytest.mark.asyncio
    async def test_returns_limitless_en_card_objects(
        self, client: LimitlessClient
    ) -> None:
        """Should return a list of LimitlessENCard instances."""
        with patch.object(client, "_get_official", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = SET_CARDS_HTML

            cards = await client.fetch_en_set_cards("OBF")

            assert all(isinstance(c, LimitlessENCard) for c in cards)

    @pytest.mark.asyncio
    async def test_parses_card_numbers_from_hrefs(
        self, client: LimitlessClient
    ) -> None:
        """Should extract card numbers from /cards/en/OBF/<number> hrefs."""
        with patch.object(client, "_get_official", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = SET_CARDS_HTML

            cards = await client.fetch_en_set_cards("OBF")

            card_numbers = [c.card_number for c in cards]
            assert "1" in card_numbers
            assert "125" in card_numbers
            assert "200" in card_numbers

    @pytest.mark.asyncio
    async def test_deduplicates_cards(self, client: LimitlessClient) -> None:
        """Should not return duplicate cards when links repeat."""
        with patch.object(client, "_get_official", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = SET_CARDS_HTML

            cards = await client.fetch_en_set_cards("OBF")

            card_ids = [c.limitless_id for c in cards]
            assert card_ids.count("OBF-125") == 1

    @pytest.mark.asyncio
    async def test_returns_correct_count_after_dedup(
        self, client: LimitlessClient
    ) -> None:
        """Should return 3 unique cards (card 125 appears twice in HTML)."""
        with patch.object(client, "_get_official", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = SET_CARDS_HTML

            cards = await client.fetch_en_set_cards("OBF")

            assert len(cards) == 3

    @pytest.mark.asyncio
    async def test_cards_have_correct_set_code(self, client: LimitlessClient) -> None:
        """Each returned card should have the requested set code."""
        with patch.object(client, "_get_official", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = SET_CARDS_HTML

            cards = await client.fetch_en_set_cards("OBF")

            assert all(c.set_code == "OBF" for c in cards)

    @pytest.mark.asyncio
    async def test_limitless_id_format_on_parsed_cards(
        self, client: LimitlessClient
    ) -> None:
        """Parsed cards' limitless_id should be 'SET-NUMBER'."""
        with patch.object(client, "_get_official", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = SET_CARDS_HTML

            cards = await client.fetch_en_set_cards("OBF")

            ids = {c.limitless_id for c in cards}
            assert "OBF-125" in ids
            assert "OBF-1" in ids
            assert "OBF-200" in ids

    @pytest.mark.asyncio
    async def test_calls_correct_endpoint(self, client: LimitlessClient) -> None:
        """Should request /cards/en/<set_code> for the given set."""
        with patch.object(client, "_get_official", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = SET_CARDS_HTML

            await client.fetch_en_set_cards("OBF")

            mock_get.assert_called_once_with("/cards/en/OBF")

    @pytest.mark.asyncio
    async def test_returns_empty_list_for_page_with_no_card_links(
        self, client: LimitlessClient
    ) -> None:
        """Should return an empty list when no card hrefs are found."""
        with patch.object(client, "_get_official", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = "<html><body><p>No cards</p></body></html>"

            cards = await client.fetch_en_set_cards("OBF")

            assert cards == []
