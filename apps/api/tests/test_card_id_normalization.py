"""Tests for card ID normalization in meta router.

Verifies that _generate_card_id_variants() and _batch_lookup_cards()
handle the format mismatch between Limitless (sv3-125) and TCGdex (sv03-125).
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.routers.meta import _batch_lookup_cards, _generate_card_id_variants


class TestGenerateCardIdVariants:
    """Tests for _generate_card_id_variants()."""

    def test_unpadded_sv_set(self) -> None:
        """sv3-125 should generate sv03-125 variant."""
        variants = _generate_card_id_variants("sv3-125")
        assert "sv3-125" in variants
        assert "sv03-125" in variants

    def test_padded_sv_set(self) -> None:
        """sv03-125 should generate sv3-125 variant."""
        variants = _generate_card_id_variants("sv03-125")
        assert "sv03-125" in variants
        assert "sv3-125" in variants

    def test_single_digit_sets(self) -> None:
        """All single-digit SV sets should generate padded variants."""
        for n in range(1, 10):
            variants = _generate_card_id_variants(f"sv{n}-1")
            assert f"sv{n}-1" in variants
            assert f"sv{n:02d}-1" in variants

    def test_two_digit_set_no_spurious_variants(self) -> None:
        """sv10-1 should not generate sv010-1 (already 2 digits)."""
        variants = _generate_card_id_variants("sv10-1")
        assert "sv10-1" in variants
        # 02d of 10 is still "10", so only one unique variant
        assert len(variants) == 1

    def test_pt_suffix_set(self) -> None:
        """sv4pt5-10 should generate sv04pt5-10 variant."""
        variants = _generate_card_id_variants("sv4pt5-10")
        assert "sv4pt5-10" in variants
        assert "sv04pt5-10" in variants

    def test_swsh_sets(self) -> None:
        """swsh12-50 should generate swsh12-50 (already 2+ digits)."""
        variants = _generate_card_id_variants("swsh12-50")
        assert "swsh12-50" in variants

    def test_swsh_single_digit(self) -> None:
        """swsh1-10 should generate swsh01-10 variant."""
        variants = _generate_card_id_variants("swsh1-10")
        assert "swsh1-10" in variants
        assert "swsh01-10" in variants

    def test_non_matching_id_returns_original(self) -> None:
        """IDs that don't match the pattern are returned as-is."""
        variants = _generate_card_id_variants("energy-fire")
        assert variants == ["energy-fire"]

    def test_no_duplicates(self) -> None:
        """Already-padded IDs should not produce duplicates."""
        variants = _generate_card_id_variants("sv03-125")
        assert len(variants) == len(set(variants))

    def test_sve_energy_set(self) -> None:
        """sve-1 (no digits in set) should return original."""
        variants = _generate_card_id_variants("sve-1")
        # "sve" has no trailing digit group, so pattern won't match
        # Actually: prefix="sv", num="0" from "e"? No, "e" is not a digit.
        # The regex requires digits after prefix letters, so "sve-1" won't match.
        assert "sve-1" in variants

    def test_mep_promos(self) -> None:
        """mep-1 should return original (no digit in set code)."""
        variants = _generate_card_id_variants("mep-1")
        assert "mep-1" in variants


class TestBatchLookupCardsNormalization:
    """Tests for _batch_lookup_cards() with ID normalization."""

    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_unpadded_id_finds_padded_card(self, mock_db: AsyncMock) -> None:
        """Looking up sv3-125 should find Card with id=sv03-125."""
        card_row = MagicMock()
        card_row.id = "sv03-125"
        card_row.name = "Charizard ex"
        card_row.japanese_name = None
        card_row.image_small = "https://assets.tcgdex.net/en/sv/sv03/125"

        mock_result = MagicMock()
        mock_result.all.return_value = [card_row]
        mock_db.execute.return_value = mock_result

        result = await _batch_lookup_cards(["sv3-125"], mock_db)

        # Result should be keyed by the original (caller's) ID
        assert "sv3-125" in result
        assert result["sv3-125"] == (
            "Charizard ex",
            "https://assets.tcgdex.net/en/sv/sv03/125",
        )

    @pytest.mark.asyncio
    async def test_padded_id_finds_padded_card(self, mock_db: AsyncMock) -> None:
        """Looking up sv03-125 should find Card with id=sv03-125."""
        card_row = MagicMock()
        card_row.id = "sv03-125"
        card_row.name = "Charizard ex"
        card_row.japanese_name = None
        card_row.image_small = "https://assets.tcgdex.net/en/sv/sv03/125"

        mock_result = MagicMock()
        mock_result.all.return_value = [card_row]
        mock_db.execute.return_value = mock_result

        result = await _batch_lookup_cards(["sv03-125"], mock_db)

        assert "sv03-125" in result
        assert result["sv03-125"][0] == "Charizard ex"

    @pytest.mark.asyncio
    async def test_multiple_mismatched_ids(self, mock_db: AsyncMock) -> None:
        """Multiple unpadded IDs should all resolve to padded DB entries."""
        rows = []
        for set_id, name in [
            ("sv03-125", "Charizard ex"),
            ("sv04-6", "Iron Hands ex"),
            ("sv05-10", "Temporal Forces Card"),
        ]:
            row = MagicMock()
            row.id = set_id
            row.name = name
            row.japanese_name = None
            row.image_small = f"https://assets.tcgdex.net/{set_id}"
            rows.append(row)

        mock_result = MagicMock()
        mock_result.all.return_value = rows
        mock_db.execute.return_value = mock_result

        result = await _batch_lookup_cards(["sv3-125", "sv4-6", "sv5-10"], mock_db)

        assert "sv3-125" in result
        assert result["sv3-125"][0] == "Charizard ex"
        assert "sv4-6" in result
        assert result["sv4-6"][0] == "Iron Hands ex"
        assert "sv5-10" in result
        assert result["sv5-10"][0] == "Temporal Forces Card"

    @pytest.mark.asyncio
    async def test_empty_card_ids(self, mock_db: AsyncMock) -> None:
        """Empty input should return empty dict without DB query."""
        result = await _batch_lookup_cards([], mock_db)
        assert result == {}
        mock_db.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_match_falls_through_to_mapping(self, mock_db: AsyncMock) -> None:
        """IDs with no card match should fall through to JP mapping lookup."""
        # First call: card lookup returns empty
        empty_result = MagicMock()
        empty_result.all.return_value = []

        # Second call: mapping lookup returns empty
        empty_mapping = MagicMock()
        empty_mapping.all.return_value = []

        mock_db.execute.side_effect = [empty_result, empty_mapping]

        result = await _batch_lookup_cards(["unknown-999"], mock_db)
        assert result == {}
        # Two DB calls: card lookup + mapping lookup
        assert mock_db.execute.call_count == 2
