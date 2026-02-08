"""Tests for ArchetypeNormalizer service."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.archetype_normalizer import (
    SPRITE_ARCHETYPE_MAP,
    ArchetypeNormalizer,
)


class TestBuildSpriteKey:
    """Tests for ArchetypeNormalizer.build_sprite_key."""

    def test_r2_cdn_single_url(self) -> None:
        """Should extract name from r2 CDN URL."""
        urls = ["https://r2.limitlesstcg.net/pokemon/gen9/charizard.png"]
        assert ArchetypeNormalizer.build_sprite_key(urls) == "charizard"

    def test_r2_cdn_two_urls(self) -> None:
        """Should join names from multiple r2 CDN URLs (sorted)."""
        urls = [
            "https://r2.limitlesstcg.net/pokemon/gen9/dragapult.png",
            "https://r2.limitlesstcg.net/pokemon/gen9/pidgeot.png",
        ]
        assert ArchetypeNormalizer.build_sprite_key(urls) == "dragapult-pidgeot"

    def test_names_sorted_alphabetically(self) -> None:
        """Should sort names alphabetically regardless of URL order."""
        urls = [
            "https://example.com/pidgeot.png",
            "https://example.com/dragapult.png",
        ]
        assert ArchetypeNormalizer.build_sprite_key(urls) == "dragapult-pidgeot"

    def test_reverse_order_same_key(self) -> None:
        """Both orderings should produce the same canonical key."""
        urls_a = [
            "https://example.com/kangaskhan-mega.png",
            "https://example.com/absol-mega.png",
        ]
        urls_b = [
            "https://example.com/absol-mega.png",
            "https://example.com/kangaskhan-mega.png",
        ]
        assert ArchetypeNormalizer.build_sprite_key(
            urls_a
        ) == ArchetypeNormalizer.build_sprite_key(urls_b)

    def test_old_url_pattern(self) -> None:
        """Should extract name from old limitlesstcg URL pattern (sorted)."""
        urls = [
            "https://limitlesstcg.com/img/pokemon/grimmsnarl.png",
            "https://limitlesstcg.com/img/pokemon/froslass.png",
        ]
        assert ArchetypeNormalizer.build_sprite_key(urls) == "froslass-grimmsnarl"

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

    def test_mega_prefix_single(self) -> None:
        """Should put Mega as a prefix for single Mega Pokemon."""
        assert (
            ArchetypeNormalizer.derive_name_from_key("lucario-mega") == "Mega Lucario"
        )

    def test_mega_prefix_composite(self) -> None:
        """Mega Pokemon should be first with Mega prefix."""
        assert (
            ArchetypeNormalizer.derive_name_from_key("hariyama-lucario-mega")
            == "Mega Lucario Hariyama"
        )

    def test_mega_prefix_dual_mega(self) -> None:
        """Both Mega Pokemon should have Mega prefix."""
        assert (
            ArchetypeNormalizer.derive_name_from_key("froslass-mega-starmie-mega")
            == "Mega Froslass Mega Starmie"
        )


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
            "https://example.com/weezing.png",
            "https://example.com/slowking.png",
        ]
        archetype, raw, method = normalizer.resolve(urls, "Unknown", None)

        # Sorted: slowking < weezing, so key is "slowking-weezing"
        assert archetype == "Slowking Weezing"
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


class TestExpandedSpriteMap:
    """Tests for expanded SPRITE_ARCHETYPE_MAP coverage."""

    def test_mega_absol(self) -> None:
        """Should resolve absol-mega to Mega Absol ex."""
        normalizer = ArchetypeNormalizer()
        urls = ["https://r2.limitlesstcg.net/pokemon/gen9/absol-mega.png"]
        archetype, _, method = normalizer.resolve(urls, "?", None)
        assert archetype == "Mega Absol ex"
        assert method == "sprite_lookup"

    def test_mega_kangaskhan(self) -> None:
        """Should resolve kangaskhan-mega to Mega Kangaskhan ex."""
        normalizer = ArchetypeNormalizer()
        urls = ["https://r2.limitlesstcg.net/pokemon/gen9/kangaskhan-mega.png"]
        archetype, _, method = normalizer.resolve(urls, "?", None)
        assert archetype == "Mega Kangaskhan ex"
        assert method == "sprite_lookup"

    def test_noctowl_box(self) -> None:
        """Should resolve noctowl to Noctowl Box."""
        normalizer = ArchetypeNormalizer()
        urls = ["https://r2.limitlesstcg.net/pokemon/gen9/noctowl.png"]
        archetype, _, method = normalizer.resolve(urls, "?", None)
        assert archetype == "Noctowl Box"
        assert method == "sprite_lookup"

    def test_chien_pao_baxcalibur(self) -> None:
        """Should resolve baxcalibur+chien-pao to Chien-Pao ex (sorted key)."""
        normalizer = ArchetypeNormalizer()
        urls = [
            "https://example.com/chien-pao.png",
            "https://example.com/baxcalibur.png",
        ]
        archetype, _, method = normalizer.resolve(urls, "?", None)
        assert archetype == "Chien-Pao ex"
        assert method == "sprite_lookup"

    def test_cinderace(self) -> None:
        """Should resolve cinderace (the original bug)."""
        normalizer = ArchetypeNormalizer()
        urls = ["https://r2.limitlesstcg.net/pokemon/gen9/cinderace.png"]
        archetype, _, method = normalizer.resolve(urls, "?", None)
        assert archetype == "Cinderace ex"
        assert method == "sprite_lookup"

    def test_pidgeot_control(self) -> None:
        """Should resolve pidgeot alone to Pidgeot ex Control."""
        normalizer = ArchetypeNormalizer()
        urls = ["https://r2.limitlesstcg.net/pokemon/gen9/pidgeot.png"]
        archetype, _, method = normalizer.resolve(urls, "?", None)
        assert archetype == "Pidgeot ex Control"
        assert method == "sprite_lookup"

    def test_snorlax_stall(self) -> None:
        """Should resolve snorlax to Snorlax Stall."""
        normalizer = ArchetypeNormalizer()
        urls = ["https://r2.limitlesstcg.net/pokemon/gen9/snorlax.png"]
        archetype, _, method = normalizer.resolve(urls, "?", None)
        assert archetype == "Snorlax Stall"
        assert method == "sprite_lookup"

    def test_mega_lopunny(self) -> None:
        """Should resolve lopunny-mega to Mega Lopunny ex."""
        normalizer = ArchetypeNormalizer()
        urls = ["https://r2.limitlesstcg.net/pokemon/gen9/lopunny-mega.png"]
        archetype, _, method = normalizer.resolve(urls, "?", None)
        assert archetype == "Mega Lopunny ex"
        assert method == "sprite_lookup"

    def test_mega_lucario(self) -> None:
        """Should resolve lucario-mega to Mega Lucario ex."""
        normalizer = ArchetypeNormalizer()
        urls = ["https://r2.limitlesstcg.net/pokemon/gen9/lucario-mega.png"]
        archetype, _, method = normalizer.resolve(urls, "?", None)
        assert archetype == "Mega Lucario ex"
        assert method == "sprite_lookup"

    def test_composite_mega_absol_box(self) -> None:
        """Should resolve absol-mega + kangaskhan-mega to Mega Absol Box."""
        normalizer = ArchetypeNormalizer()
        urls = [
            "https://example.com/absol-mega.png",
            "https://example.com/kangaskhan-mega.png",
        ]
        archetype, _, method = normalizer.resolve(urls, "?", None)
        assert archetype == "Mega Absol Box"
        assert method == "sprite_lookup"

    def test_composite_mega_absol_box_reverse_order(self) -> None:
        """Should resolve kangaskhan-mega + absol-mega to Mega Absol Box."""
        normalizer = ArchetypeNormalizer()
        urls = [
            "https://example.com/kangaskhan-mega.png",
            "https://example.com/absol-mega.png",
        ]
        archetype, _, method = normalizer.resolve(urls, "?", None)
        assert archetype == "Mega Absol Box"
        assert method == "sprite_lookup"

    def test_composite_tera_box(self) -> None:
        """Should resolve noctowl + ogerpon-wellspring to Tera Box."""
        normalizer = ArchetypeNormalizer()
        urls = [
            "https://example.com/noctowl.png",
            "https://example.com/ogerpon-wellspring.png",
        ]
        archetype, _, method = normalizer.resolve(urls, "?", None)
        assert archetype == "Tera Box"
        assert method == "sprite_lookup"

    def test_composite_tera_box_reverse_order(self) -> None:
        """Reversed URL order should still resolve to Tera Box."""
        normalizer = ArchetypeNormalizer()
        urls = [
            "https://example.com/ogerpon-wellspring.png",
            "https://example.com/noctowl.png",
        ]
        archetype, _, method = normalizer.resolve(urls, "?", None)
        assert archetype == "Tera Box"
        assert method == "sprite_lookup"

    def test_composite_joltik_box(self) -> None:
        """Should resolve joltik + pikachu to Joltik Box."""
        normalizer = ArchetypeNormalizer()
        urls = [
            "https://example.com/pikachu.png",
            "https://example.com/joltik.png",
        ]
        archetype, _, method = normalizer.resolve(urls, "?", None)
        assert archetype == "Joltik Box"
        assert method == "sprite_lookup"

    def test_composite_ho_oh_armarouge(self) -> None:
        """Should resolve ho-oh + armarouge to Ho-Oh Armarouge."""
        normalizer = ArchetypeNormalizer()
        urls = [
            "https://example.com/ho-oh.png",
            "https://example.com/armarouge.png",
        ]
        archetype, _, method = normalizer.resolve(urls, "?", None)
        assert archetype == "Ho-Oh Armarouge"
        assert method == "sprite_lookup"

    def test_map_has_minimum_40_entries(self) -> None:
        """Sprite map should have at least 40 entries."""
        assert len(SPRITE_ARCHETYPE_MAP) >= 40


class TestBuildSpriteKeyDigits:
    """Tests for digit-handling in sprite key extraction."""

    def test_filename_with_digits(self) -> None:
        """Should handle filenames containing digits."""
        urls = ["https://example.com/mewtwo2.png"]
        assert ArchetypeNormalizer.build_sprite_key(urls) == "mewtwo2"

    def test_gen_path_with_digits(self) -> None:
        """Should extract name from gen-numbered path."""
        urls = ["https://r2.limitlesstcg.net/pokemon/gen10/charizard.png"]
        assert ArchetypeNormalizer.build_sprite_key(urls) == "charizard"


class TestSpriteMapDoesNotMutate:
    """Ensure the module-level map is not mutated by instances."""

    def test_custom_map_does_not_mutate_default(self) -> None:
        """Custom sprite_map should not change the module-level dict."""
        original_len = len(SPRITE_ARCHETYPE_MAP)
        custom = {"custom-key": "Custom Archetype"}
        normalizer = ArchetypeNormalizer(sprite_map=custom)
        normalizer.sprite_map["another-key"] = "Another"
        assert len(SPRITE_ARCHETYPE_MAP) == original_len

    def test_default_map_is_copied(self) -> None:
        """Default map instance should be a copy."""
        normalizer = ArchetypeNormalizer()
        normalizer.sprite_map["injected-key"] = "Injected"
        assert "injected-key" not in SPRITE_ARCHETYPE_MAP


class TestLoadDbSprites:
    """Tests for DB-backed sprite loading."""

    @pytest.mark.asyncio
    async def test_load_merges_db_over_code(self) -> None:
        """DB entries should override in-code entries."""
        from collections import namedtuple

        row = namedtuple("Row", ["sprite_key", "archetype_name", "display_name"])
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = [
            row("charizard", "DB Charizard Override", None),
            row("new-db-key", "New DB Archetype", None),
        ]
        mock_session.execute.return_value = mock_result

        normalizer = ArchetypeNormalizer()
        count = await normalizer.load_db_sprites(mock_session)

        assert count == 2
        assert normalizer.sprite_map["charizard"] == "DB Charizard Override"
        assert normalizer.sprite_map["new-db-key"] == "New DB Archetype"
        # Original entries still present
        assert "dragapult" in normalizer.sprite_map
        assert normalizer._db_loaded is True

    @pytest.mark.asyncio
    async def test_load_prefers_display_name(self) -> None:
        """display_name should take priority over archetype_name."""
        from collections import namedtuple

        row = namedtuple("Row", ["sprite_key", "archetype_name", "display_name"])
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = [
            row("charizard", "Charizard ex", "Zard"),
            row("gardevoir", "Gardevoir ex", None),
        ]
        mock_session.execute.return_value = mock_result

        normalizer = ArchetypeNormalizer()
        await normalizer.load_db_sprites(mock_session)

        assert normalizer.sprite_map["charizard"] == "Zard"
        assert normalizer.sprite_map["gardevoir"] == "Gardevoir ex"

    @pytest.mark.asyncio
    async def test_load_empty_db(self) -> None:
        """Empty DB should leave in-code map intact."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.execute.return_value = mock_result

        normalizer = ArchetypeNormalizer()
        original_len = len(normalizer.sprite_map)
        count = await normalizer.load_db_sprites(mock_session)

        assert count == 0
        assert len(normalizer.sprite_map) == original_len


class TestSeedDbSprites:
    """Tests for seeding the DB from the in-code map."""

    @pytest.mark.asyncio
    async def test_seed_inserts_missing_keys(self) -> None:
        """Should insert entries not already in DB."""
        mock_session = AsyncMock()
        # Simulate empty DB
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.execute.return_value = mock_result

        with patch(
            "src.services.archetype_normalizer.SPRITE_ARCHETYPE_MAP",
            {"key-a": "Archetype A", "key-b": "Archetype B"},
        ):
            count = await ArchetypeNormalizer.seed_db_sprites(mock_session)

        assert count == 2
        assert mock_session.add.call_count == 2
        mock_session.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_seed_skips_existing_keys(self) -> None:
        """Should not re-insert keys already in DB."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = [("key-a",)]
        mock_session.execute.return_value = mock_result

        with patch(
            "src.services.archetype_normalizer.SPRITE_ARCHETYPE_MAP",
            {"key-a": "Archetype A", "key-b": "Archetype B"},
        ):
            count = await ArchetypeNormalizer.seed_db_sprites(mock_session)

        assert count == 1
        assert mock_session.add.call_count == 1
