"""Tests for archetype detection service."""

import pytest

from src.data.signature_cards import SIGNATURE_CARDS, normalize_archetype
from src.services.archetype_detector import (
    ArchetypeDetector,
    detect_archetype,
    get_detector,
)


class TestArchetypeDetector:
    """Tests for ArchetypeDetector class."""

    @pytest.fixture
    def detector(self) -> ArchetypeDetector:
        return ArchetypeDetector()

    def test_detects_charizard_ex(self, detector: ArchetypeDetector) -> None:
        """Should detect Charizard ex archetype from signature card."""
        decklist = [
            {"card_id": "sv3-125", "quantity": 2},  # Charizard ex
            {"card_id": "some-other-card", "quantity": 4},
        ]
        assert detector.detect(decklist) == "Charizard ex"

    def test_detects_gardevoir_ex(self, detector: ArchetypeDetector) -> None:
        """Should detect Gardevoir ex archetype."""
        decklist = [
            {"card_id": "sv2-86", "quantity": 3},  # Gardevoir ex
        ]
        assert detector.detect(decklist) == "Gardevoir ex"

    def test_detects_lugia_vstar(self, detector: ArchetypeDetector) -> None:
        """Should detect Lugia VSTAR archetype."""
        decklist = [
            {"card_id": "swsh12pt5-46", "quantity": 2},  # Lugia VSTAR
        ]
        assert detector.detect(decklist) == "Lugia VSTAR"

    def test_returns_rogue_for_no_signature_cards(
        self, detector: ArchetypeDetector
    ) -> None:
        """Should return Rogue when no signature cards found."""
        decklist = [
            {"card_id": "random-card-1", "quantity": 4},
            {"card_id": "random-card-2", "quantity": 4},
        ]
        assert detector.detect(decklist) == "Rogue"

    def test_returns_rogue_for_empty_decklist(
        self, detector: ArchetypeDetector
    ) -> None:
        """Should return Rogue for empty decklist."""
        assert detector.detect([]) == "Rogue"

    def test_chooses_highest_quantity_archetype(
        self, detector: ArchetypeDetector
    ) -> None:
        """Should choose archetype with highest total signature card quantity."""
        decklist = [
            {"card_id": "sv3-125", "quantity": 2},  # Charizard ex
            {"card_id": "sv2-86", "quantity": 3},  # Gardevoir ex
        ]
        # Gardevoir has higher quantity
        assert detector.detect(decklist) == "Gardevoir ex"

    def test_handles_multiple_cards_same_archetype(
        self, detector: ArchetypeDetector
    ) -> None:
        """Should sum quantities of multiple cards for same archetype."""
        decklist = [
            {"card_id": "sv3-125", "quantity": 2},  # Charizard ex (base)
            {"card_id": "sv3-183", "quantity": 1},  # Charizard ex (alt art)
            {"card_id": "sv2-86", "quantity": 2},  # Gardevoir ex
        ]
        # Charizard total = 3, Gardevoir = 2
        assert detector.detect(decklist) == "Charizard ex"

    def test_handles_non_dict_entries(self, detector: ArchetypeDetector) -> None:
        """Should skip non-dict entries."""
        decklist = [
            "invalid_string",
            {"card_id": "sv3-125", "quantity": 2},
            None,
            123,
        ]
        assert detector.detect(decklist) == "Charizard ex"

    def test_handles_missing_card_id(self, detector: ArchetypeDetector) -> None:
        """Should skip entries without card_id."""
        decklist = [
            {"quantity": 4},  # Missing card_id
            {"card_id": "sv3-125", "quantity": 2},
        ]
        assert detector.detect(decklist) == "Charizard ex"

    def test_handles_empty_card_id(self, detector: ArchetypeDetector) -> None:
        """Should skip entries with empty card_id."""
        decklist = [
            {"card_id": "", "quantity": 4},
            {"card_id": "sv3-125", "quantity": 2},
        ]
        assert detector.detect(decklist) == "Charizard ex"

    def test_handles_invalid_quantity(self, detector: ArchetypeDetector) -> None:
        """Should default to 1 for invalid quantities."""
        decklist = [
            {"card_id": "sv3-125", "quantity": "invalid"},
        ]
        assert detector.detect(decklist) == "Charizard ex"

    def test_handles_zero_quantity(self, detector: ArchetypeDetector) -> None:
        """Should default to 1 for zero quantity."""
        decklist = [
            {"card_id": "sv3-125", "quantity": 0},
        ]
        assert detector.detect(decklist) == "Charizard ex"

    def test_handles_negative_quantity(self, detector: ArchetypeDetector) -> None:
        """Should default to 1 for negative quantity."""
        decklist = [
            {"card_id": "sv3-125", "quantity": -5},
        ]
        assert detector.detect(decklist) == "Charizard ex"

    def test_handles_none_quantity(self, detector: ArchetypeDetector) -> None:
        """Should default to 1 for None quantity."""
        decklist = [
            {"card_id": "sv3-125", "quantity": None},
        ]
        assert detector.detect(decklist) == "Charizard ex"

    def test_handles_missing_quantity(self, detector: ArchetypeDetector) -> None:
        """Should default to 1 when quantity key missing."""
        decklist = [
            {"card_id": "sv3-125"},
        ]
        assert detector.detect(decklist) == "Charizard ex"


class TestDetectWithConfidence:
    """Tests for detect_with_confidence method."""

    @pytest.fixture
    def detector(self) -> ArchetypeDetector:
        return ArchetypeDetector()

    def test_returns_archetype_and_counts(self, detector: ArchetypeDetector) -> None:
        """Should return archetype and signature card counts."""
        decklist = [
            {"card_id": "sv3-125", "quantity": 2},  # Charizard ex
            {"card_id": "sv2-86", "quantity": 1},  # Gardevoir ex
        ]
        archetype, counts = detector.detect_with_confidence(decklist)

        assert archetype == "Charizard ex"
        assert counts == {"Charizard ex": 2, "Gardevoir ex": 1}

    def test_returns_rogue_and_empty_counts(self, detector: ArchetypeDetector) -> None:
        """Should return Rogue with empty counts when no signatures."""
        decklist = [{"card_id": "random", "quantity": 4}]
        archetype, counts = detector.detect_with_confidence(decklist)

        assert archetype == "Rogue"
        assert counts == {}

    def test_returns_rogue_for_empty_list(self, detector: ArchetypeDetector) -> None:
        """Should return Rogue for empty decklist."""
        archetype, counts = detector.detect_with_confidence([])

        assert archetype == "Rogue"
        assert counts == {}


class TestDetectFromExistingArchetype:
    """Tests for detect_from_existing_archetype method."""

    @pytest.fixture
    def detector(self) -> ArchetypeDetector:
        return ArchetypeDetector()

    def test_uses_detected_over_existing(self, detector: ArchetypeDetector) -> None:
        """Should use detected archetype when signature cards found."""
        decklist = [{"card_id": "sv3-125", "quantity": 2}]
        result = detector.detect_from_existing_archetype(decklist, "Some Other")

        assert result == "Charizard ex"

    def test_falls_back_to_existing(self, detector: ArchetypeDetector) -> None:
        """Should use existing archetype when no signature cards found."""
        decklist = [{"card_id": "random", "quantity": 4}]
        result = detector.detect_from_existing_archetype(decklist, "Custom Archetype")

        assert result == "Custom Archetype"

    def test_normalizes_existing_archetype(self, detector: ArchetypeDetector) -> None:
        """Should normalize existing archetype alias."""
        decklist = [{"card_id": "random", "quantity": 4}]
        result = detector.detect_from_existing_archetype(decklist, "Zard")

        assert result == "Charizard ex"


class TestCustomSignatureCards:
    """Tests for custom signature card mappings."""

    def test_uses_custom_mapping(self) -> None:
        """Should use custom signature card mapping."""
        custom = {"custom-card": "Custom Archetype"}
        detector = ArchetypeDetector(signature_cards=custom)

        decklist = [{"card_id": "custom-card", "quantity": 2}]
        assert detector.detect(decklist) == "Custom Archetype"

    def test_ignores_default_cards_with_custom(self) -> None:
        """Custom mapping should not include default cards."""
        custom = {"custom-card": "Custom Archetype"}
        detector = ArchetypeDetector(signature_cards=custom)

        decklist = [{"card_id": "sv3-125", "quantity": 2}]  # Default Charizard
        assert detector.detect(decklist) == "Rogue"


class TestNormalizeArchetype:
    """Tests for normalize_archetype function."""

    def test_normalizes_zard_alias(self) -> None:
        """Should normalize Zard to Charizard ex."""
        assert normalize_archetype("Zard") == "Charizard ex"

    def test_normalizes_gard_alias(self) -> None:
        """Should normalize Gard to Gardevoir ex."""
        assert normalize_archetype("Gard") == "Gardevoir ex"

    def test_normalizes_lzb_alias(self) -> None:
        """Should normalize LZB to Lost Zone Box."""
        assert normalize_archetype("LZB") == "Lost Zone Box"

    def test_returns_input_for_unknown(self) -> None:
        """Should return input unchanged if not an alias."""
        assert normalize_archetype("Unknown Deck") == "Unknown Deck"

    def test_returns_canonical_name_unchanged(self) -> None:
        """Should return canonical name unchanged."""
        assert normalize_archetype("Charizard ex") == "Charizard ex"


class TestModuleLevelFunctions:
    """Tests for module-level convenience functions."""

    def test_get_detector_returns_singleton(self) -> None:
        """Should return same detector instance."""
        d1 = get_detector()
        d2 = get_detector()
        assert d1 is d2

    def test_detect_archetype_function(self) -> None:
        """Should detect archetype using convenience function."""
        decklist = [{"card_id": "sv3-125", "quantity": 2}]
        assert detect_archetype(decklist) == "Charizard ex"


class TestJPCardIdTranslation:
    """Tests for JP card ID translation functionality."""

    def test_translates_jp_card_id_to_en(self) -> None:
        """Should translate JP card IDs using the mapping."""
        jp_to_en = {
            "SV7-18": "sv7-28",  # JP Cinderace -> EN Cinderace
            "SV6-95": "sv6-95",  # Same ID (self-mapping)
        }
        detector = ArchetypeDetector(jp_to_en_mapping=jp_to_en)

        decklist = [
            {"card_id": "SV7-18", "quantity": 2},  # JP ID that maps to sv7-28
        ]
        assert detector._translate_card_id("SV7-18") == "sv7-28"

    def test_preserves_unmapped_card_ids(self) -> None:
        """Should preserve card IDs not in the mapping."""
        jp_to_en = {"SV7-18": "sv7-28"}
        detector = ArchetypeDetector(jp_to_en_mapping=jp_to_en)

        assert detector._translate_card_id("unknown-card") == "unknown-card"

    def test_detects_archetype_from_jp_decklist(self) -> None:
        """Should detect archetype when JP cards map to EN signature cards."""
        jp_to_en = {
            "SV3-125-JP": "sv3-125",  # Maps to Charizard ex signature
        }
        detector = ArchetypeDetector(jp_to_en_mapping=jp_to_en)

        decklist = [
            {"card_id": "SV3-125-JP", "quantity": 2},
        ]
        assert detector.detect(decklist) == "Charizard ex"

    def test_returns_rogue_for_unmapped_jp_cards(self) -> None:
        """Should return Rogue when JP cards don't map to signatures."""
        jp_to_en = {
            "JP-RANDOM-1": "en-random-1",  # Maps to non-signature card
        }
        detector = ArchetypeDetector(jp_to_en_mapping=jp_to_en)

        decklist = [
            {"card_id": "JP-RANDOM-1", "quantity": 4},
        ]
        assert detector.detect(decklist) == "Rogue"

    def test_empty_mapping_behaves_as_default(self) -> None:
        """Empty mapping should not affect detection."""
        detector = ArchetypeDetector(jp_to_en_mapping={})

        decklist = [
            {"card_id": "sv3-125", "quantity": 2},  # Direct EN ID
        ]
        assert detector.detect(decklist) == "Charizard ex"

    def test_none_mapping_behaves_as_default(self) -> None:
        """None mapping should not affect detection."""
        detector = ArchetypeDetector(jp_to_en_mapping=None)

        decklist = [
            {"card_id": "sv3-125", "quantity": 2},  # Direct EN ID
        ]
        assert detector.detect(decklist) == "Charizard ex"

    def test_detect_with_confidence_uses_translation(self) -> None:
        """detect_with_confidence should also use JP translation."""
        jp_to_en = {
            "SV3-125-JP": "sv3-125",  # Charizard ex
            "SV2-86-JP": "sv2-86",  # Gardevoir ex
        }
        detector = ArchetypeDetector(jp_to_en_mapping=jp_to_en)

        decklist = [
            {"card_id": "SV3-125-JP", "quantity": 2},
            {"card_id": "SV2-86-JP", "quantity": 1},
        ]
        archetype, counts = detector.detect_with_confidence(decklist)

        assert archetype == "Charizard ex"
        assert counts == {"Charizard ex": 2, "Gardevoir ex": 1}


class TestJPAliases:
    """Tests for JP archetype alias normalization."""

    def test_normalizes_cinderace_without_ex(self) -> None:
        """Should normalize 'Cinderace' to 'Cinderace ex'."""
        assert normalize_archetype("Cinderace") == "Cinderace ex"

    def test_normalizes_jp_cinderace(self) -> None:
        """Should normalize Japanese Cinderace name."""
        assert normalize_archetype("エースバーンex") == "Cinderace ex"

    def test_normalizes_jp_charizard(self) -> None:
        """Should normalize Japanese Charizard name."""
        assert normalize_archetype("リザードンex") == "Charizard ex"

    def test_normalizes_dragapult_without_ex(self) -> None:
        """Should normalize 'Dragapult' to 'Dragapult ex'."""
        assert normalize_archetype("Dragapult") == "Dragapult ex"

    def test_normalizes_jp_dragapult(self) -> None:
        """Should normalize Japanese Dragapult name."""
        assert normalize_archetype("ドラパルトex") == "Dragapult ex"

    def test_normalizes_terapagos_without_ex(self) -> None:
        """Should normalize 'Terapagos' to 'Terapagos ex'."""
        assert normalize_archetype("Terapagos") == "Terapagos ex"

    def test_normalizes_jp_lost_zone_box(self) -> None:
        """Should normalize Japanese Lost Zone Box name."""
        assert normalize_archetype("ロストバレット") == "Lost Zone Box"


class TestSignatureCardsData:
    """Tests for signature cards data integrity."""

    def test_signature_cards_not_empty(self) -> None:
        """Should have signature cards defined."""
        assert len(SIGNATURE_CARDS) > 0

    def test_all_values_are_strings(self) -> None:
        """All archetype names should be strings."""
        for card_id, archetype in SIGNATURE_CARDS.items():
            assert isinstance(card_id, str), f"Card ID {card_id} is not a string"
            assert isinstance(archetype, str), f"Archetype for {card_id} is not string"

    def test_no_empty_archetypes(self) -> None:
        """No archetype names should be empty."""
        for card_id, archetype in SIGNATURE_CARDS.items():
            assert archetype.strip(), f"Empty archetype for card {card_id}"

    def test_card_id_format(self) -> None:
        """Card IDs should follow expected format (set-number or set-prefix)."""
        for card_id in SIGNATURE_CARDS:
            assert "-" in card_id, f"Card ID {card_id} missing hyphen"
            parts = card_id.split("-")
            assert len(parts) >= 2, f"Card ID {card_id} has wrong format"
