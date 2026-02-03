"""Tests for the DecklistDiffEngine."""

import pytest

from src.services.decklist_diff import DecklistDiffEngine, DecklistDiffResult


class TestNormalizeCardName:
    """Tests for card name normalization and reprint handling."""

    @pytest.fixture
    def engine(self) -> DecklistDiffEngine:
        return DecklistDiffEngine()

    def test_normalizes_known_reprint_by_card_id(
        self, engine: DecklistDiffEngine
    ) -> None:
        """Should return canonical name for a known reprint card_id."""
        entry = {"card_id": "sv2-172", "name": "Boss's Orders (Ghetsis)", "quantity": 2}
        assert engine.normalize_card_name(entry) == "Boss's Orders"

    def test_falls_back_to_name_for_unknown_card_id(
        self, engine: DecklistDiffEngine
    ) -> None:
        """Should use the name field when card_id is not in reprint mapping."""
        entry = {"card_id": "sv7-144", "name": "Terapagos ex", "quantity": 3}
        assert engine.normalize_card_name(entry) == "Terapagos ex"

    def test_falls_back_to_card_id_when_no_name(
        self, engine: DecklistDiffEngine
    ) -> None:
        """Should use card_id when name is missing and card_id is not in reprints."""
        entry = {"card_id": "sv99-1", "quantity": 1}
        assert engine.normalize_card_name(entry) == "sv99-1"

    def test_returns_unknown_when_no_fields(self, engine: DecklistDiffEngine) -> None:
        """Should return 'Unknown' when both card_id and name are missing."""
        assert engine.normalize_card_name({}) == "Unknown"

    def test_different_prints_normalize_to_same_name(
        self, engine: DecklistDiffEngine
    ) -> None:
        """Should normalize different prints of Iono to the same canonical name."""
        entries = [
            {"card_id": "sv1-185", "name": "Iono", "quantity": 4},
            {"card_id": "sv4pt5-80", "name": "Iono (alt art)", "quantity": 4},
            {"card_id": "sv6-178", "name": "Iono", "quantity": 4},
        ]
        names = [engine.normalize_card_name(e) for e in entries]
        assert all(n == "Iono" for n in names)


class TestComputeConsensusList:
    """Tests for consensus decklist computation."""

    @pytest.fixture
    def engine(self) -> DecklistDiffEngine:
        return DecklistDiffEngine()

    def test_empty_input_returns_empty(self, engine: DecklistDiffEngine) -> None:
        """Should return empty list for no decklists."""
        assert engine.compute_consensus_list([]) == []

    def test_single_decklist_returns_all_cards(
        self, engine: DecklistDiffEngine
    ) -> None:
        """Single decklist should include all cards at 100% inclusion."""
        decklist = [
            {"card_id": "sv7-144", "name": "Terapagos ex", "quantity": 3},
            {"card_id": "sv1-185", "name": "Iono", "quantity": 4},
        ]
        result = engine.compute_consensus_list([decklist])
        assert len(result) == 2
        for card in result:
            assert card["inclusion_rate"] == 1.0

    def test_median_quantity_computed_correctly(
        self, engine: DecklistDiffEngine
    ) -> None:
        """Should compute median count from decklists that include the card."""
        decklists = [
            [{"card_id": "a", "name": "CardA", "quantity": 4}],
            [{"card_id": "a", "name": "CardA", "quantity": 2}],
            [{"card_id": "a", "name": "CardA", "quantity": 3}],
        ]
        result = engine.compute_consensus_list(decklists)
        card_a = next(c for c in result if c["name"] == "CardA")
        assert card_a["quantity"] == 3  # median of [4, 2, 3] = 3

    def test_inclusion_threshold_filters_cards(
        self, engine: DecklistDiffEngine
    ) -> None:
        """Cards below the inclusion threshold should be excluded."""
        decklists = [
            [
                {"card_id": "a", "name": "Common", "quantity": 4},
                {"card_id": "b", "name": "Rare", "quantity": 1},
            ],
            [
                {"card_id": "a", "name": "Common", "quantity": 4},
            ],
            [
                {"card_id": "a", "name": "Common", "quantity": 4},
            ],
        ]
        # Rare only in 1/3 = 33%, below 50% threshold
        result = engine.compute_consensus_list(decklists, inclusion_threshold=0.5)
        names = [c["name"] for c in result]
        assert "Common" in names
        assert "Rare" not in names

    def test_inclusion_threshold_custom_value(self, engine: DecklistDiffEngine) -> None:
        """Should respect custom inclusion threshold."""
        decklists = [
            [{"card_id": "a", "name": "CardA", "quantity": 2}],
            [{"card_id": "a", "name": "CardA", "quantity": 2}],
            [{"card_id": "b", "name": "CardB", "quantity": 1}],
            [{"card_id": "b", "name": "CardB", "quantity": 1}],
            [{"card_id": "c", "name": "CardC", "quantity": 1}],
        ]
        # CardA: 2/5=40%, CardB: 2/5=40%, CardC: 1/5=20%
        result = engine.compute_consensus_list(decklists, inclusion_threshold=0.3)
        names = [c["name"] for c in result]
        assert "CardA" in names
        assert "CardB" in names
        assert "CardC" not in names

    def test_reprints_treated_as_same_card(self, engine: DecklistDiffEngine) -> None:
        """Different prints of the same card should be merged in consensus."""
        decklists = [
            [{"card_id": "sv1-185", "name": "Iono", "quantity": 4}],
            [{"card_id": "sv4pt5-80", "name": "Iono (alt)", "quantity": 4}],
            [{"card_id": "sv6-178", "name": "Iono (full art)", "quantity": 3}],
        ]
        result = engine.compute_consensus_list(decklists)
        # All three should be normalized to "Iono"
        iono_cards = [c for c in result if c["name"] == "Iono"]
        assert len(iono_cards) == 1
        assert iono_cards[0]["inclusion_rate"] == 1.0
        assert iono_cards[0]["quantity"] == 4  # median of [4, 4, 3]

    def test_same_card_different_entries_aggregated(
        self, engine: DecklistDiffEngine
    ) -> None:
        """Multiple entries for the same card in one decklist should be summed."""
        decklists = [
            [
                {"card_id": "sv1-185", "name": "Iono", "quantity": 2},
                {"card_id": "sv4pt5-80", "name": "Iono (alt)", "quantity": 2},
            ],
        ]
        result = engine.compute_consensus_list(decklists)
        iono = next(c for c in result if c["name"] == "Iono")
        assert iono["quantity"] == 4  # 2 + 2 from same decklist

    def test_sorted_by_inclusion_then_quantity_then_name(
        self, engine: DecklistDiffEngine
    ) -> None:
        """Results should be sorted by inclusion rate desc, quantity desc, name asc."""
        decklists = [
            [
                {"card_id": "a", "name": "Zzz", "quantity": 4},
                {"card_id": "b", "name": "Aaa", "quantity": 4},
                {"card_id": "c", "name": "Mmm", "quantity": 1},
            ],
            [
                {"card_id": "a", "name": "Zzz", "quantity": 4},
                {"card_id": "b", "name": "Aaa", "quantity": 4},
            ],
        ]
        result = engine.compute_consensus_list(decklists)
        # Zzz and Aaa: 100% inclusion, qty 4 → sorted by name: Aaa, Zzz
        # Mmm: 50% inclusion
        assert result[0]["name"] == "Aaa"
        assert result[1]["name"] == "Zzz"
        assert result[2]["name"] == "Mmm"


class TestDiff:
    """Tests for diffing two consensus decklists."""

    @pytest.fixture
    def engine(self) -> DecklistDiffEngine:
        return DecklistDiffEngine()

    def test_identical_lists_produce_no_changes(
        self, engine: DecklistDiffEngine
    ) -> None:
        """Diffing identical lists should produce no changes."""
        consensus = [
            {"name": "CardA", "quantity": 4, "inclusion_rate": 1.0},
            {"name": "CardB", "quantity": 2, "inclusion_rate": 0.8},
        ]
        result = engine.diff(consensus, consensus)
        assert not result.has_changes
        assert result.added == []
        assert result.removed == []
        assert result.changed == []

    def test_detects_added_cards(self, engine: DecklistDiffEngine) -> None:
        """Should detect cards present in new but not old."""
        old = [{"name": "CardA", "quantity": 4, "inclusion_rate": 1.0}]
        new = [
            {"name": "CardA", "quantity": 4, "inclusion_rate": 1.0},
            {"name": "CardB", "quantity": 2, "inclusion_rate": 0.7},
        ]
        result = engine.diff(old, new)
        assert len(result.added) == 1
        assert result.added[0].card_name == "CardB"
        assert result.added[0].new_quantity == 2

    def test_detects_removed_cards(self, engine: DecklistDiffEngine) -> None:
        """Should detect cards present in old but not new."""
        old = [
            {"name": "CardA", "quantity": 4, "inclusion_rate": 1.0},
            {"name": "CardB", "quantity": 2, "inclusion_rate": 0.7},
        ]
        new = [{"name": "CardA", "quantity": 4, "inclusion_rate": 1.0}]
        result = engine.diff(old, new)
        assert len(result.removed) == 1
        assert result.removed[0].card_name == "CardB"
        assert result.removed[0].old_quantity == 2

    def test_detects_quantity_changes(self, engine: DecklistDiffEngine) -> None:
        """Should detect cards whose quantity changed."""
        old = [{"name": "CardA", "quantity": 4, "inclusion_rate": 1.0}]
        new = [{"name": "CardA", "quantity": 3, "inclusion_rate": 1.0}]
        result = engine.diff(old, new)
        assert len(result.changed) == 1
        assert result.changed[0].card_name == "CardA"
        assert result.changed[0].change == -1

    def test_complex_diff_with_all_change_types(
        self, engine: DecklistDiffEngine
    ) -> None:
        """Should handle a mix of added, removed, and changed cards."""
        old = [
            {"name": "Stays", "quantity": 4, "inclusion_rate": 1.0},
            {"name": "Removed", "quantity": 2, "inclusion_rate": 0.8},
            {"name": "Changed", "quantity": 3, "inclusion_rate": 0.9},
        ]
        new = [
            {"name": "Stays", "quantity": 4, "inclusion_rate": 1.0},
            {"name": "Added", "quantity": 1, "inclusion_rate": 0.6},
            {"name": "Changed", "quantity": 4, "inclusion_rate": 1.0},
        ]
        result = engine.diff(old, new)
        assert len(result.added) == 1
        assert result.added[0].card_name == "Added"
        assert len(result.removed) == 1
        assert result.removed[0].card_name == "Removed"
        assert len(result.changed) == 1
        assert result.changed[0].card_name == "Changed"
        assert result.changed[0].change == 1

    def test_empty_old_all_cards_are_added(self, engine: DecklistDiffEngine) -> None:
        """Diffing from empty should show all new cards as added."""
        new = [
            {"name": "CardA", "quantity": 4, "inclusion_rate": 1.0},
            {"name": "CardB", "quantity": 2, "inclusion_rate": 0.8},
        ]
        result = engine.diff([], new)
        assert len(result.added) == 2
        assert result.removed == []

    def test_empty_new_all_cards_are_removed(self, engine: DecklistDiffEngine) -> None:
        """Diffing to empty should show all old cards as removed."""
        old = [
            {"name": "CardA", "quantity": 4, "inclusion_rate": 1.0},
            {"name": "CardB", "quantity": 2, "inclusion_rate": 0.8},
        ]
        result = engine.diff(old, [])
        assert len(result.removed) == 2
        assert result.added == []

    def test_has_changes_property(self, engine: DecklistDiffEngine) -> None:
        """has_changes should return True when there are any changes."""
        result = DecklistDiffResult()
        assert not result.has_changes

        old = [{"name": "A", "quantity": 1, "inclusion_rate": 1.0}]
        new = [{"name": "A", "quantity": 2, "inclusion_rate": 1.0}]
        diff_result = engine.diff(old, new)
        assert diff_result.has_changes


class TestCardChange:
    """Tests for CardChange dataclass."""

    def test_change_property_positive(self) -> None:
        """Change should be positive when quantity increased."""
        from src.services.decklist_diff import CardChange

        change = CardChange("Test", 2, 4)
        assert change.change == 2

    def test_change_property_negative(self) -> None:
        """Change should be negative when quantity decreased."""
        from src.services.decklist_diff import CardChange

        change = CardChange("Test", 4, 2)
        assert change.change == -2
