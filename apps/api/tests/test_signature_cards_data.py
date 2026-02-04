"""Tests for signature cards data structure, aliases, and normalization.

Validates SIGNATURE_CARDS mapping, ARCHETYPE_ALIASES, and the
normalize_archetype function used for archetype detection.
"""

import re

import pytest

from src.data.signature_cards import (
    ARCHETYPE_ALIASES,
    SIGNATURE_CARDS,
    normalize_archetype,
)


class TestSignatureCardsStructure:
    """SIGNATURE_CARDS mapping must be well-formed and non-empty."""

    def test_mapping_is_non_empty(self) -> None:
        """SIGNATURE_CARDS must contain entries."""
        assert len(SIGNATURE_CARDS) > 0

    def test_all_keys_are_strings(self) -> None:
        """Every card ID key must be a string."""
        for card_id in SIGNATURE_CARDS:
            assert isinstance(card_id, str), f"Key {card_id!r} is not a string"

    def test_all_values_are_strings(self) -> None:
        """Every archetype name must be a string."""
        for card_id, archetype in SIGNATURE_CARDS.items():
            assert isinstance(archetype, str), (
                f"Archetype for {card_id} is not a string: {archetype!r}"
            )

    def test_no_empty_archetype_names(self) -> None:
        """No archetype name should be empty or whitespace-only."""
        for card_id, archetype in SIGNATURE_CARDS.items():
            assert archetype.strip(), f"Empty archetype for card {card_id}"

    def test_no_empty_card_ids(self) -> None:
        """No card ID key should be empty or whitespace-only."""
        for card_id in SIGNATURE_CARDS:
            assert card_id.strip(), f"Found empty card ID key: {card_id!r}"


class TestSignatureCardsFormat:
    """Card IDs must follow the TCGdex format: {set_id}-{card_number}."""

    def test_card_ids_contain_hyphen(self) -> None:
        """Every card ID must contain at least one hyphen."""
        for card_id in SIGNATURE_CARDS:
            assert "-" in card_id, f"Card ID {card_id} missing hyphen"

    def test_card_ids_have_at_least_two_parts(self) -> None:
        """Card IDs split by hyphen must have at least 2 parts."""
        for card_id in SIGNATURE_CARDS:
            parts = card_id.split("-")
            assert len(parts) >= 2, f"Card ID {card_id} has wrong format"

    def test_card_ids_match_expected_pattern(self) -> None:
        """Card IDs should match patterns like sv4-125, swsh12pt5-46, sv3pt5-TG21."""
        pattern = re.compile(r"^[a-z0-9]+(pt\d+)?-[A-Za-z0-9]+$")
        for card_id in SIGNATURE_CARDS:
            assert pattern.match(card_id), (
                f"Card ID {card_id} does not match expected TCGdex format"
            )

    def test_set_prefixes_are_lowercase(self) -> None:
        """Set prefix portion of card IDs should be lowercase."""
        for card_id in SIGNATURE_CARDS:
            set_prefix = card_id.split("-")[0]
            assert set_prefix == set_prefix.lower(), (
                f"Set prefix in {card_id} should be lowercase"
            )


class TestSignatureCardsKnownArchetypes:
    """Known competitive archetypes must be present in the mapping."""

    @pytest.fixture
    def archetypes(self) -> set[str]:
        """Set of all unique archetype names in SIGNATURE_CARDS."""
        return set(SIGNATURE_CARDS.values())

    def test_charizard_ex_present(self, archetypes: set[str]) -> None:
        """Charizard ex must be a known archetype."""
        assert "Charizard ex" in archetypes

    def test_gardevoir_ex_present(self, archetypes: set[str]) -> None:
        """Gardevoir ex must be a known archetype."""
        assert "Gardevoir ex" in archetypes

    def test_lugia_vstar_present(self, archetypes: set[str]) -> None:
        """Lugia VSTAR must be a known archetype."""
        assert "Lugia VSTAR" in archetypes

    def test_dragapult_ex_present(self, archetypes: set[str]) -> None:
        """Dragapult ex must be a known archetype."""
        assert "Dragapult ex" in archetypes

    def test_lost_zone_box_present(self, archetypes: set[str]) -> None:
        """Lost Zone Box must be a known archetype."""
        assert "Lost Zone Box" in archetypes

    def test_giratina_vstar_present(self, archetypes: set[str]) -> None:
        """Giratina VSTAR must be a known archetype."""
        assert "Giratina VSTAR" in archetypes


class TestArchetypeAliases:
    """ARCHETYPE_ALIASES mapping must be well-formed."""

    def test_aliases_is_non_empty(self) -> None:
        """ARCHETYPE_ALIASES must contain entries."""
        assert len(ARCHETYPE_ALIASES) > 0

    def test_all_alias_keys_are_strings(self) -> None:
        """Every alias key must be a string."""
        for alias in ARCHETYPE_ALIASES:
            assert isinstance(alias, str), f"Alias key {alias!r} is not a string"

    def test_all_alias_values_are_strings(self) -> None:
        """Every alias target must be a string."""
        for alias, target in ARCHETYPE_ALIASES.items():
            assert isinstance(target, str), (
                f"Alias target for {alias} is not a string: {target!r}"
            )

    def test_zard_alias_maps_to_charizard_ex(self) -> None:
        """Shorthand 'Zard' should map to 'Charizard ex'."""
        assert ARCHETYPE_ALIASES["Zard"] == "Charizard ex"

    def test_lzb_alias_maps_to_lost_zone_box(self) -> None:
        """Shorthand 'LZB' should map to 'Lost Zone Box'."""
        assert ARCHETYPE_ALIASES["LZB"] == "Lost Zone Box"

    def test_japanese_aliases_exist(self) -> None:
        """Japanese-language aliases should be present."""
        jp_aliases = [a for a in ARCHETYPE_ALIASES if not a.isascii()]
        assert len(jp_aliases) > 0, "Should have Japanese-language aliases"

    def test_jp_charizard_alias(self) -> None:
        """Japanese Charizard alias should map correctly."""
        assert ARCHETYPE_ALIASES["\u30ea\u30b6\u30fc\u30c9\u30f3ex"] == "Charizard ex"

    def test_jp_gardevoir_alias(self) -> None:
        """Japanese Gardevoir alias should map correctly."""
        assert ARCHETYPE_ALIASES["\u30b5\u30fc\u30ca\u30a4\u30c8ex"] == "Gardevoir ex"


class TestNormalizeArchetype:
    """normalize_archetype must handle aliases, casing, and edge cases."""

    def test_normalizes_known_alias(self) -> None:
        """Known alias should resolve to canonical name."""
        assert normalize_archetype("Zard") == "Charizard ex"

    def test_case_insensitive_lookup(self) -> None:
        """Alias lookup should be case-insensitive."""
        assert normalize_archetype("zard") == "Charizard ex"
        assert normalize_archetype("ZARD") == "Charizard ex"
        assert normalize_archetype("lzb") == "Lost Zone Box"

    def test_unknown_name_returned_as_is(self) -> None:
        """Unrecognized archetype names should pass through unchanged."""
        assert normalize_archetype("Some Custom Deck") == "Some Custom Deck"

    def test_empty_string_returns_unknown(self) -> None:
        """Empty string input should return 'Unknown'."""
        assert normalize_archetype("") == "Unknown"

    def test_whitespace_only_returns_unknown(self) -> None:
        """Whitespace-only input should return 'Unknown'."""
        assert normalize_archetype("   ") == "Unknown"

    def test_canonical_name_passes_through(self) -> None:
        """Canonical archetype names should pass through unchanged."""
        assert normalize_archetype("Charizard ex") == "Charizard ex"
        assert normalize_archetype("Lugia VSTAR") == "Lugia VSTAR"

    def test_jp_alias_normalization(self) -> None:
        """Japanese alias should normalize to English canonical name."""
        assert normalize_archetype("\u30c9\u30e9\u30d1\u30eb\u30c8ex") == "Dragapult ex"
        assert (
            normalize_archetype("\u30ed\u30b9\u30c8\u30d0\u30ec\u30c3\u30c8")
            == "Lost Zone Box"
        )
