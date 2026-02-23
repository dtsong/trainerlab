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

    def test_two_digit_set_with_card_number_variants(self) -> None:
        """sv10-1 generates card number variants (01, 001)."""
        variants = _generate_card_id_variants("sv10-1")
        assert "sv10-1" in variants
        assert "sv10-01" in variants
        assert "sv10-001" in variants

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
        """sve-1 (no digits in set) generates card number variants."""
        variants = _generate_card_id_variants("sve-1")
        assert "sve-1" in variants
        assert "sve-01" in variants
        assert "sve-001" in variants

    def test_mep_promos(self) -> None:
        """mep-1 generates card number variants even without set digits."""
        variants = _generate_card_id_variants("mep-1")
        assert "mep-1" in variants
        assert "mep-01" in variants
        assert "mep-001" in variants

    def test_empty_string_returns_empty_list(self) -> None:
        """Empty string input should return empty list."""
        assert _generate_card_id_variants("") == []

    def test_dot_notation_set_generates_card_number_variants(self) -> None:
        """sv08.5-10 generates card number variants but no set variants."""
        variants = _generate_card_id_variants("sv08.5-10")
        assert "sv08.5-10" in variants
        assert "sv08.5-010" in variants
        # No set variants (dot prevents set regex match)
        assert all(v.startswith("sv08.5-") for v in variants)

    def test_dot_notation_with_letter_suffix(self) -> None:
        """sv10.5b-1 generates card number variants."""
        variants = _generate_card_id_variants("sv10.5b-1")
        assert "sv10.5b-1" in variants
        assert "sv10.5b-01" in variants
        assert "sv10.5b-001" in variants

    def test_card_number_padding_sv08_76(self) -> None:
        """sv08-76 should produce sv08-076 variant."""
        variants = _generate_card_id_variants("sv08-76")
        assert "sv08-76" in variants
        assert "sv08-076" in variants
        assert "sv8-76" in variants
        assert "sv8-076" in variants

    def test_card_number_padding_mee_1(self) -> None:
        """mee-1 (no digit in set) should produce mee-001 variant."""
        variants = _generate_card_id_variants("mee-1")
        assert "mee-1" in variants
        assert "mee-01" in variants
        assert "mee-001" in variants

    def test_card_number_padding_me01_114(self) -> None:
        """me01-114 generates set variant me1-114 (114 already 3 digits)."""
        variants = _generate_card_id_variants("me01-114")
        assert "me01-114" in variants
        assert "me1-114" in variants

    def test_cross_product_sv3_5(self) -> None:
        """sv3-5 generates full cross-product of set and card variants."""
        variants = set(_generate_card_id_variants("sv3-5"))
        expected = {
            "sv3-5",
            "sv3-05",
            "sv3-005",
            "sv03-5",
            "sv03-05",
            "sv03-005",
        }
        assert expected == variants

    def test_three_digit_card_number_no_extra_padding(self) -> None:
        """sv03-125: card number 125 already 3 digits, no 4-digit variant."""
        variants = set(_generate_card_id_variants("sv03-125"))
        assert "sv03-125" in variants
        assert "sv3-125" in variants
        # No 4-digit padding
        assert not any(len(v.split("-")[1]) > 3 for v in variants)

    def test_no_hyphen_returns_original(self) -> None:
        """Card ID with no hyphen is returned as-is."""
        variants = _generate_card_id_variants("energyfire")
        assert variants == ["energyfire"]


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
    async def test_padded_to_unpadded_reverse_direction(
        self, mock_db: AsyncMock
    ) -> None:
        """SSP cards: Limitless emits sv08, TCGdex may store as sv8."""
        card_row = MagicMock()
        card_row.id = "sv8-200"
        card_row.name = "Pikachu ex"
        card_row.japanese_name = None
        card_row.image_small = "https://assets.tcgdex.net/sv8-200"

        mock_result = MagicMock()
        mock_result.all.return_value = [card_row]
        mock_db.execute.return_value = mock_result

        result = await _batch_lookup_cards(["sv08-200"], mock_db)

        assert "sv08-200" in result
        assert result["sv08-200"][0] == "Pikachu ex"

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
    async def test_overlapping_variants_both_resolve(self, mock_db: AsyncMock) -> None:
        """Both sv3-125 and sv03-125 in same batch should both resolve."""
        card_row = MagicMock()
        card_row.id = "sv03-125"
        card_row.name = "Charizard ex"
        card_row.japanese_name = None
        card_row.image_small = "https://assets.tcgdex.net/sv03-125"

        mock_result = MagicMock()
        mock_result.all.return_value = [card_row]
        mock_db.execute.return_value = mock_result

        result = await _batch_lookup_cards(["sv3-125", "sv03-125"], mock_db)

        assert "sv3-125" in result
        assert "sv03-125" in result
        assert result["sv3-125"][0] == "Charizard ex"
        assert result["sv03-125"][0] == "Charizard ex"

    @pytest.mark.asyncio
    async def test_empty_card_ids(self, mock_db: AsyncMock) -> None:
        """Empty input should return empty dict without DB query."""
        result = await _batch_lookup_cards([], mock_db)
        assert result == {}
        mock_db.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_match_falls_through_to_mapping(self, mock_db: AsyncMock) -> None:
        """IDs with no card match should fall through to JP mapping lookup."""
        # Step 0: limitless_id lookup returns empty
        empty_limitless = MagicMock()
        empty_limitless.all.return_value = []

        # Step 1: card variant lookup returns empty
        empty_result = MagicMock()
        empty_result.all.return_value = []

        # Step 2: mapping lookup returns empty
        empty_mapping = MagicMock()
        empty_mapping.all.return_value = []

        mock_db.execute.side_effect = [
            empty_limitless,
            empty_result,
            empty_mapping,
        ]

        result = await _batch_lookup_cards(["unknown-999"], mock_db)
        assert result == {}
        # Three DB calls: limitless_id + card variant + JP mapping
        assert mock_db.execute.call_count == 3

    @pytest.mark.asyncio
    async def test_card_number_variant_finds_padded_card(
        self, mock_db: AsyncMock
    ) -> None:
        """sv08-76 should find Card with id=sv08-076 via card number variant."""
        card_row = MagicMock()
        card_row.id = "sv08-076"
        card_row.name = "Test Card"
        card_row.japanese_name = None
        card_row.image_small = "https://assets.tcgdex.net/sv08-076"

        mock_result = MagicMock()
        mock_result.all.return_value = [card_row]
        mock_db.execute.return_value = mock_result

        result = await _batch_lookup_cards(["sv08-76"], mock_db)

        assert "sv08-76" in result
        assert result["sv08-76"] == (
            "Test Card",
            "https://assets.tcgdex.net/sv08-076",
        )

    @pytest.mark.asyncio
    async def test_mapping_fallback_with_card_number_variant(
        self, mock_db: AsyncMock
    ) -> None:
        """JP ID variant matches mapping, EN ID variant matches card."""
        # Step 0: limitless_id lookup misses
        empty_limitless = MagicMock()
        empty_limitless.all.return_value = []

        # Step 1: direct card lookup misses
        empty_result = MagicMock()
        empty_result.all.return_value = []

        # Step 2: mapping lookup — DB stores padded JP ID sv08-076
        mapping_row = MagicMock()
        mapping_row.jp_card_id = "sv08-076"
        mapping_row.en_card_id = "sv08-76"
        mapping_row.card_name_en = "Test Card EN"
        mapping_result = MagicMock()
        mapping_result.all.return_value = [mapping_row]

        # Step 3: EN card lookup — DB stores padded EN ID sv08-076
        en_card_row = MagicMock()
        en_card_row.id = "sv08-076"
        en_card_row.name = "Test Card EN"
        en_card_row.japanese_name = None
        en_card_row.image_small = "https://assets.tcgdex.net/sv08-076"
        en_result = MagicMock()
        en_result.all.return_value = [en_card_row]

        mock_db.execute.side_effect = [
            empty_limitless,
            empty_result,
            mapping_result,
            en_result,
        ]

        # Caller uses unpadded sv08-76
        result = await _batch_lookup_cards(["sv08-76"], mock_db)

        assert "sv08-76" in result
        assert result["sv08-76"] == (
            "Test Card EN",
            "https://assets.tcgdex.net/sv08-076",
        )
