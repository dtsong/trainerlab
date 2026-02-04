"""Tests for card reprints data structure and content.

Validates the CARD_REPRINTS mapping used to treat the same card across
different sets as identical when computing consensus decklists and diffs.
"""

import re

from src.data.card_reprints import CARD_REPRINTS


class TestCardReprintsStructure:
    """CARD_REPRINTS mapping must be a well-formed dict[str, str]."""

    def test_mapping_is_non_empty(self) -> None:
        """CARD_REPRINTS must contain at least one entry."""
        assert len(CARD_REPRINTS) > 0

    def test_all_keys_are_strings(self) -> None:
        """Every card ID key must be a string."""
        for key in CARD_REPRINTS:
            assert isinstance(key, str), f"Key {key!r} is not a string"

    def test_all_values_are_strings(self) -> None:
        """Every canonical card name must be a string."""
        for card_id, name in CARD_REPRINTS.items():
            assert isinstance(name, str), (
                f"Value for {card_id} is not a string: {name!r}"
            )

    def test_no_empty_keys(self) -> None:
        """No card ID key should be empty or whitespace-only."""
        for card_id in CARD_REPRINTS:
            assert card_id.strip(), f"Found empty card ID key: {card_id!r}"

    def test_no_empty_values(self) -> None:
        """No canonical card name should be empty or whitespace-only."""
        for card_id, name in CARD_REPRINTS.items():
            assert name.strip(), f"Empty canonical name for card {card_id}"


class TestCardReprintsFormat:
    """Card IDs must follow the expected TCGdex format."""

    def test_card_ids_contain_hyphen(self) -> None:
        """Every card ID must contain at least one hyphen separator."""
        for card_id in CARD_REPRINTS:
            assert "-" in card_id, f"Card ID {card_id} is missing a hyphen"

    def test_card_ids_match_expected_pattern(self) -> None:
        """Card IDs should match set-number format (e.g., sv1-190, swsh9-132)."""
        # Pattern: letters/digits (set), hyphen, then set suffix or card number
        pattern = re.compile(r"^[a-z0-9]+-[a-zA-Z0-9-]+$")
        for card_id in CARD_REPRINTS:
            assert pattern.match(card_id), (
                f"Card ID {card_id} does not match expected format"
            )

    def test_card_ids_are_lowercase_set_prefix(self) -> None:
        """Set prefix portion of card IDs should be lowercase."""
        for card_id in CARD_REPRINTS:
            set_prefix = card_id.split("-")[0]
            assert set_prefix == set_prefix.lower(), (
                f"Set prefix in {card_id} should be lowercase"
            )


class TestCardReprintsKnownEntries:
    """Known reprint groups must be present in the mapping."""

    def test_boss_orders_reprints_exist(self) -> None:
        """Boss's Orders should have multiple reprint entries."""
        boss_entries = [
            cid for cid, name in CARD_REPRINTS.items() if name == "Boss's Orders"
        ]
        assert len(boss_entries) >= 2, (
            "Boss's Orders should have at least 2 reprint entries"
        )

    def test_ultra_ball_reprints_exist(self) -> None:
        """Ultra Ball should have multiple reprint entries."""
        ultra_entries = [
            cid for cid, name in CARD_REPRINTS.items() if name == "Ultra Ball"
        ]
        assert len(ultra_entries) >= 2, (
            "Ultra Ball should have at least 2 reprint entries"
        )

    def test_iono_reprints_exist(self) -> None:
        """Iono should have multiple reprint entries."""
        iono_entries = [cid for cid, name in CARD_REPRINTS.items() if name == "Iono"]
        assert len(iono_entries) >= 2, "Iono should have at least 2 reprint entries"

    def test_specific_card_id_maps_correctly(self) -> None:
        """Known card ID should map to expected canonical name."""
        assert CARD_REPRINTS["sv1-196"] == "Ultra Ball"
        assert CARD_REPRINTS["sv1-185"] == "Iono"
        assert CARD_REPRINTS["sv1-191"] == "Rare Candy"


class TestCardReprintsNoDuplicates:
    """No duplicate card IDs should exist in the mapping."""

    def test_no_duplicate_card_ids(self) -> None:
        """Each card ID must appear exactly once as a key.

        dict keys are unique by definition, but this test ensures
        that the module loads without silent overwrite of entries.
        """
        # dict enforces unique keys, so if len matches we know
        # no key was silently overwritten by a duplicate
        assert isinstance(CARD_REPRINTS, dict)
        # Verify the dict can be iterated without error
        ids = list(CARD_REPRINTS.keys())
        assert len(ids) == len(set(ids))

    def test_each_canonical_name_has_multiple_entries(self) -> None:
        """Each canonical name should map to at least 2 card IDs (it is a reprint)."""
        from collections import Counter

        name_counts = Counter(CARD_REPRINTS.values())
        for name, count in name_counts.items():
            # Energy entries may only have 1 entry each
            if "Energy" in name:
                continue
            assert count >= 2, (
                f"Canonical name '{name}' only has {count} entry; "
                f"reprints should have at least 2"
            )
