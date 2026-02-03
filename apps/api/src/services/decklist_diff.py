"""Decklist diff engine for computing consensus lists and diffs.

Pure logic module with no DB or async dependencies.
Works at card_name level so reprints across sets are treated as the same card.
"""

from dataclasses import dataclass, field
from statistics import median

from src.data.card_reprints import CARD_REPRINTS


@dataclass
class CardChange:
    """A single card change between two consensus lists."""

    card_name: str
    old_quantity: float
    new_quantity: float

    @property
    def change(self) -> float:
        return self.new_quantity - self.old_quantity


@dataclass
class DecklistDiffResult:
    """Result of diffing two consensus decklists."""

    added: list[CardChange] = field(default_factory=list)
    removed: list[CardChange] = field(default_factory=list)
    changed: list[CardChange] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)


class DecklistDiffEngine:
    """Engine for computing consensus decklists and diffs between snapshots.

    Operates at the card_name level, normalizing reprints so the same card
    printed across multiple sets is treated identically.
    """

    def normalize_card_name(self, card_entry: dict) -> str:
        """Normalize a card entry to a canonical card name.

        Checks the reprint mapping first (by card_id), then falls back
        to the name field in the card entry.

        Args:
            card_entry: Dict with at least "card_id" and/or "name" keys.

        Returns:
            Canonical card name string.
        """
        card_id = card_entry.get("card_id", "")
        if card_id and card_id in CARD_REPRINTS:
            return CARD_REPRINTS[card_id]
        return card_entry.get("name", card_id or "Unknown")

    def _aggregate_decklist(self, decklist: list[dict]) -> dict[str, int]:
        """Aggregate a decklist into {card_name: total_quantity}.

        Handles cases where the same card appears multiple times in a list
        (e.g., different prints of the same card).

        Args:
            decklist: List of card entries with card_id, name, quantity.

        Returns:
            Dict mapping canonical card name to total quantity.
        """
        aggregated: dict[str, int] = {}
        for card in decklist:
            name = self.normalize_card_name(card)
            quantity = card.get("quantity", 0)
            aggregated[name] = aggregated.get(name, 0) + quantity
        return aggregated

    def compute_consensus_list(
        self,
        decklists: list[list[dict]],
        inclusion_threshold: float = 0.5,
    ) -> list[dict]:
        """Compute a consensus decklist from multiple decklists.

        For each card, computes:
        - inclusion_rate: fraction of decklists that include it
        - quantity: median count across decklists that include it

        Only cards above the inclusion threshold are included.

        Args:
            decklists: List of decklists, each being a list of card dicts.
            inclusion_threshold: Minimum fraction of decklists a card must
                appear in to be included in the consensus (default 0.5 = 50%).

        Returns:
            Sorted list of consensus card dicts with name, quantity, inclusion_rate.
        """
        if not decklists:
            return []

        total_lists = len(decklists)

        # Aggregate each decklist and collect counts per card
        card_counts: dict[str, list[int]] = {}
        for decklist in decklists:
            aggregated = self._aggregate_decklist(decklist)
            for card_name, quantity in aggregated.items():
                if card_name not in card_counts:
                    card_counts[card_name] = []
                card_counts[card_name].append(quantity)

        # Build consensus
        consensus: list[dict] = []
        for card_name, counts in card_counts.items():
            inclusion_rate = len(counts) / total_lists
            if inclusion_rate >= inclusion_threshold:
                median_count = median(counts)
                consensus.append(
                    {
                        "name": card_name,
                        "quantity": round(median_count),
                        "inclusion_rate": round(inclusion_rate, 3),
                    }
                )

        # Sort by inclusion rate (desc), then quantity (desc), then name
        consensus.sort(key=lambda c: (-c["inclusion_rate"], -c["quantity"], c["name"]))
        return consensus

    def diff(
        self,
        old_consensus: list[dict],
        new_consensus: list[dict],
    ) -> DecklistDiffResult:
        """Compute the diff between two consensus decklists.

        Identifies cards that were added, removed, or had their quantity changed.

        Args:
            old_consensus: Previous consensus list.
            new_consensus: Current consensus list.

        Returns:
            DecklistDiffResult with added, removed, and changed cards.
        """
        result = DecklistDiffResult()

        old_map: dict[str, float] = {c["name"]: c["quantity"] for c in old_consensus}
        new_map: dict[str, float] = {c["name"]: c["quantity"] for c in new_consensus}

        all_cards = set(old_map.keys()) | set(new_map.keys())

        for card_name in sorted(all_cards):
            old_qty = old_map.get(card_name, 0)
            new_qty = new_map.get(card_name, 0)

            if old_qty == 0 and new_qty > 0:
                result.added.append(CardChange(card_name, old_qty, new_qty))
            elif old_qty > 0 and new_qty == 0:
                result.removed.append(CardChange(card_name, old_qty, new_qty))
            elif old_qty != new_qty:
                result.changed.append(CardChange(card_name, old_qty, new_qty))

        return result
