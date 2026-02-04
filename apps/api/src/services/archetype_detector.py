"""Archetype detection service for identifying deck archetypes.

Detects deck archetypes by matching cards in a decklist against known
signature cards. Falls back to "Rogue" if no signature cards are found.

Supports JP tournament decklists by translating JP card IDs to EN card IDs
before matching against signature cards.
"""

from collections import Counter

from src.data.signature_cards import SIGNATURE_CARDS, normalize_archetype


class ArchetypeDetector:
    """Detects deck archetypes from decklists.

    Uses signature card matching to identify the primary archetype of a deck.
    When multiple archetypes have signature cards present, selects the archetype
    with the highest combined quantity of its signature cards.

    For JP tournament decklists, pass a jp_to_en_mapping to translate JP card
    IDs before matching against signature cards.
    """

    def __init__(
        self,
        signature_cards: dict[str, str] | None = None,
        jp_to_en_mapping: dict[str, str] | None = None,
    ) -> None:
        """Initialize the detector.

        Args:
            signature_cards: Optional custom signature card mapping.
                           Defaults to the built-in SIGNATURE_CARDS.
            jp_to_en_mapping: Optional mapping from JP card IDs to EN card IDs.
                            When provided, JP card IDs in decklists are translated
                            before signature card lookup.
        """
        self.signature_cards = signature_cards or SIGNATURE_CARDS
        self.jp_to_en_mapping = jp_to_en_mapping or {}

    def detect(self, decklist: list[dict]) -> str:
        """Detect the archetype of a decklist.

        Args:
            decklist: List of card entries, each with "card_id" and "quantity" keys.
                     Example: [{"card_id": "sv3-125", "quantity": 2}]

        Returns:
            The detected archetype name, or "Rogue" if no signature cards found.
        """
        if not decklist:
            return "Rogue"

        archetype_counts: Counter[str] = Counter()

        for card_entry in decklist:
            if not isinstance(card_entry, dict):
                continue

            card_id = card_entry.get("card_id", "")
            if not card_id:
                continue

            lookup_id = self._translate_card_id(card_id)
            archetype = self.signature_cards.get(lookup_id)
            if archetype:
                quantity = self._parse_quantity(card_entry.get("quantity", 1))
                archetype_counts[archetype] += quantity

        if not archetype_counts:
            return "Rogue"

        most_common = archetype_counts.most_common(1)
        return most_common[0][0]

    def _translate_card_id(self, card_id: str) -> str:
        """Translate a card ID from JP to EN if mapping exists.

        Args:
            card_id: Card ID (may be JP or EN format).

        Returns:
            EN card ID if mapping found, otherwise the original ID.
        """
        if not self.jp_to_en_mapping:
            return card_id
        return self.jp_to_en_mapping.get(card_id, card_id)

    def detect_with_confidence(
        self, decklist: list[dict]
    ) -> tuple[str, dict[str, int]]:
        """Detect archetype with confidence details.

        Args:
            decklist: List of card entries with "card_id" and "quantity" keys.

        Returns:
            Tuple of (archetype_name, signature_card_counts) where
            signature_card_counts maps each found archetype to its total quantity.
        """
        if not decklist:
            return "Rogue", {}

        archetype_counts: Counter[str] = Counter()

        for card_entry in decklist:
            if not isinstance(card_entry, dict):
                continue

            card_id = card_entry.get("card_id", "")
            if not card_id:
                continue

            lookup_id = self._translate_card_id(card_id)
            archetype = self.signature_cards.get(lookup_id)
            if archetype:
                quantity = self._parse_quantity(card_entry.get("quantity", 1))
                archetype_counts[archetype] += quantity

        if not archetype_counts:
            return "Rogue", {}

        most_common = archetype_counts.most_common(1)
        return most_common[0][0], dict(archetype_counts)

    def detect_from_existing_archetype(
        self, decklist: list[dict], existing_archetype: str
    ) -> str:
        """Detect archetype, using existing archetype as fallback.

        Useful when we have a human-labeled archetype but want to normalize it
        or verify it against signature cards.

        Args:
            decklist: List of card entries with "card_id" and "quantity" keys.
            existing_archetype: The existing archetype label from source.

        Returns:
            Detected archetype if signature cards found, otherwise
            the normalized existing archetype.
        """
        detected = self.detect(decklist)
        if detected != "Rogue":
            return detected

        # Fall back to normalized existing archetype
        return normalize_archetype(existing_archetype)

    def _parse_quantity(self, value: int | str | None) -> int:
        """Parse a quantity value to int.

        Args:
            value: The quantity value (int, str, or None).

        Returns:
            The parsed quantity, defaulting to 1 for invalid values.
        """
        if value is None:
            return 1

        try:
            qty = int(value)
            return max(1, qty)
        except (TypeError, ValueError):
            return 1


# Module-level singleton for convenience
_detector: ArchetypeDetector | None = None


def get_detector() -> ArchetypeDetector:
    """Get the module-level archetype detector singleton."""
    global _detector
    if _detector is None:
        _detector = ArchetypeDetector()
    return _detector


def detect_archetype(decklist: list[dict]) -> str:
    """Convenience function to detect archetype using the default detector.

    Args:
        decklist: List of card entries with "card_id" and "quantity" keys.

    Returns:
        The detected archetype name.
    """
    return get_detector().detect(decklist)
