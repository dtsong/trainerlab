"""Archetype detection service for identifying deck archetypes.

Detects deck archetypes by matching cards in a decklist against known
signature cards. Falls back to "Rogue" if no signature cards are found.
"""

from collections import Counter

from src.data.signature_cards import SIGNATURE_CARDS, normalize_archetype


class ArchetypeDetector:
    """Detects deck archetypes from decklists.

    Uses signature card matching to identify the primary archetype of a deck.
    When multiple signature cards are present, uses the one with highest quantity.
    """

    def __init__(self, signature_cards: dict[str, str] | None = None) -> None:
        """Initialize the detector.

        Args:
            signature_cards: Optional custom signature card mapping.
                           Defaults to the built-in SIGNATURE_CARDS.
        """
        self.signature_cards = signature_cards or SIGNATURE_CARDS

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

            archetype = self.signature_cards.get(card_id)
            if archetype:
                quantity = self._parse_quantity(card_entry.get("quantity", 1))
                archetype_counts[archetype] += quantity

        if not archetype_counts:
            return "Rogue"

        # Return archetype with highest total quantity
        most_common = archetype_counts.most_common(1)
        return most_common[0][0]

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

            archetype = self.signature_cards.get(card_id)
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
