"""Tests for ArchetypeNormalizer service."""

from unittest.mock import MagicMock

import pytest

from src.services.archetype_normalizer import ArchetypeNormalizer


class TestBuildSpriteKey:
    """Tests for ArchetypeNormalizer.build_sprite_key."""

    def test_r2_cdn_single_url(self) -> None:
        """Should extract name from r2 CDN URL."""
        urls = ["https://r2.limitlesstcg.net/pokemon/gen9/charizard.png"]
        assert ArchetypeNormalizer.build_sprite_key(urls) == "charizard"

    def test_r2_cdn_two_urls(self) -> None:
        """Should join names from multiple r2 CDN URLs."""
        urls = [
            "https://r2.limitlesstcg.net/pokemon/gen9/dragapult.png",
            "https://r2.limitlesstcg.net/pokemon/gen9/pidgeot.png",
        ]
        assert ArchetypeNormalizer.build_sprite_key(urls) == "dragapult-pidgeot"

    def test_old_url_pattern(self) -> None:
        """Should extract name from old limitlesstcg URL pattern."""
        urls = [
            "https://limitlesstcg.com/img/pokemon/grimmsnarl.png",
            "https://limitlesstcg.com/img/pokemon/froslass.png",
        ]
        assert ArchetypeNormalizer.build_sprite_key(urls) == "grimmsnarl-froslass"

    def test_empty_urls(self) -> None:
        """Should return empty string for empty list."""
        assert ArchetypeNormalizer.build_sprite_key([]) == ""

    def test_non_png_url_ignored(self) -> None:
        """Should ignore URLs without .png filename."""
        urls = ["https://example.com/image.jpg"]
        assert ArchetypeNormalizer.build_sprite_key(urls) == ""

    def test_underscores_converted_to_hyphens(self) -> None:
        """Should convert underscores in filenames to hyphens."""
        urls = [
            "https://example.com/raging_bolt.png",
        ]
        assert ArchetypeNormalizer.build_sprite_key(urls) == "raging-bolt"

    def test_names_lowercased(self) -> None:
        """Should lowercase extracted names."""
        urls = [
            "https://example.com/Charizard.png",
        ]
        assert ArchetypeNormalizer.build_sprite_key(urls) == "charizard"


class TestDeriveNameFromKey:
    """Tests for ArchetypeNormalizer.derive_name_from_key."""

    def test_two_part_key(self) -> None:
        """Should capitalize and join two-part key."""
        assert (
            ArchetypeNormalizer.derive_name_from_key("dragapult-pidgeot")
            == "Dragapult Pidgeot"
        )

    def test_single_part_key(self) -> None:
        """Should capitalize single-part key."""
        assert ArchetypeNormalizer.derive_name_from_key("charizard") == "Charizard"

    def test_empty_key(self) -> None:
        """Should return empty string for empty key."""
        assert ArchetypeNormalizer.derive_name_from_key("") == ""

    def test_hyphenated_pokemon_name(self) -> None:
        """Should capitalize each hyphen-separated segment."""
        result = ArchetypeNormalizer.derive_name_from_key("chien-pao-baxcalibur")
        assert result == "Chien Pao Baxcalibur"


class TestResolve:
    """Tests for ArchetypeNormalizer.resolve priority chain."""

    @pytest.fixture
    def normalizer(self) -> ArchetypeNormalizer:
        detector = MagicMock()
        detector.detect.return_value = "Rogue"
        return ArchetypeNormalizer(detector=detector)

    def test_priority1_sprite_lookup(self, normalizer: ArchetypeNormalizer) -> None:
        """Should use sprite_lookup when key is in sprite map."""
        urls = ["https://r2.limitlesstcg.net/pokemon/gen9/charizard.png"]
        archetype, raw, method = normalizer.resolve(urls, "Unknown", None)

        assert archetype == "Charizard ex"
        assert raw == "Unknown"
        assert method == "sprite_lookup"

    def test_priority2_auto_derive(self, normalizer: ArchetypeNormalizer) -> None:
        """Should auto-derive when sprites exist but key not in map."""
        urls = [
            "https://example.com/grimmsnarl.png",
            "https://example.com/froslass.png",
        ]
        archetype, raw, method = normalizer.resolve(urls, "Unknown", None)

        assert archetype == "Grimmsnarl Froslass"
        assert method == "auto_derive"

    def test_priority3_signature_card(self) -> None:
        """Should use signature_card when no sprites but decklist match."""
        detector = MagicMock()
        detector.detect.return_value = "Charizard ex"
        normalizer = ArchetypeNormalizer(detector=detector)

        decklist = [{"card_id": "sv3-125", "quantity": 2}]
        archetype, raw, method = normalizer.resolve([], "Rogue", decklist)

        assert archetype == "Charizard ex"
        assert method == "signature_card"

    def test_priority4_text_label(self, normalizer: ArchetypeNormalizer) -> None:
        """Should fall back to text_label when nothing else matches."""
        archetype, raw, method = normalizer.resolve([], "Charizard", None)

        assert archetype == "Charizard ex"  # normalized via alias
        assert raw == "Charizard"
        assert method == "text_label"

    def test_text_label_passthrough(self, normalizer: ArchetypeNormalizer) -> None:
        """Should pass through unrecognized text labels as-is."""
        archetype, raw, method = normalizer.resolve([], "Some Custom Deck", None)

        assert archetype == "Some Custom Deck"
        assert method == "text_label"

    def test_sprites_override_text(self, normalizer: ArchetypeNormalizer) -> None:
        """Sprite lookup should override HTML text label."""
        urls = [
            "https://example.com/charizard.png",
            "https://example.com/pidgeot.png",
        ]
        archetype, raw, method = normalizer.resolve(urls, "Wrong Label", None)

        assert archetype == "Charizard ex"
        assert raw == "Wrong Label"
        assert method == "sprite_lookup"

    def test_signature_card_skipped_when_rogue(self) -> None:
        """Should skip signature_card when detector returns Rogue."""
        detector = MagicMock()
        detector.detect.return_value = "Rogue"
        normalizer = ArchetypeNormalizer(detector=detector)

        decklist = [{"card_id": "unknown-999", "quantity": 4}]
        _, _, method = normalizer.resolve([], "Rogue", decklist)

        assert method == "text_label"

    def test_custom_sprite_map(self) -> None:
        """Should use custom sprite map when provided."""
        custom_map = {"test-mon": "Test Archetype"}
        normalizer = ArchetypeNormalizer(sprite_map=custom_map)

        urls = ["https://example.com/test-mon.png"]
        archetype, _, method = normalizer.resolve(urls, "?", None)

        assert archetype == "Test Archetype"
        assert method == "sprite_lookup"
