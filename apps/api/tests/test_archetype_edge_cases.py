"""Edge case tests for ArchetypeNormalizer.

Tests known limitations and graceful degradation paths.
"""

from src.services.archetype_normalizer import ArchetypeNormalizer


class TestBuildSpriteKeyEdgeCases:
    """Edge cases in sprite key extraction."""

    def test_webp_url_not_matched(self) -> None:
        """Verify .webp URLs are NOT extracted (current .png-only regex)."""
        urls = ["https://r2.limitlesstcg.net/pokemon/gen9/charizard.webp"]
        key = ArchetypeNormalizer.build_sprite_key(urls)
        assert key == ""

    def test_url_with_query_params(self) -> None:
        """Verify query params don't break extraction."""
        urls = ["https://r2.limitlesstcg.net/pokemon/gen9/charizard.png?v=2"]
        key = ArchetypeNormalizer.build_sprite_key(urls)
        assert key == "charizard"

    def test_three_sprite_key(self) -> None:
        """Three sprites produce a three-part key."""
        urls = [
            "https://example.com/a.png",
            "https://example.com/b.png",
            "https://example.com/c.png",
        ]
        key = ArchetypeNormalizer.build_sprite_key(urls)
        assert key == "a-b-c"

    def test_empty_url_list(self) -> None:
        """Empty URL list produces empty key."""
        assert ArchetypeNormalizer.build_sprite_key([]) == ""

    def test_non_png_url_ignored(self) -> None:
        """Non-.png URLs produce warning and empty key part."""
        urls = ["https://example.com/mystery-image"]
        key = ArchetypeNormalizer.build_sprite_key(urls)
        assert key == ""

    def test_mixed_valid_invalid_urls(self) -> None:
        """Mixed URLs: valid ones extracted, invalid ones skipped."""
        urls = [
            "https://example.com/charizard.png",
            "https://example.com/no-extension",
            "https://example.com/pidgeot.png",
        ]
        key = ArchetypeNormalizer.build_sprite_key(urls)
        # Only .png URLs are extracted
        assert "charizard" in key
        assert "pidgeot" in key


class TestResolveEdgeCases:
    """Edge cases in resolve() fallback behavior."""

    def test_unmatched_sprites_fall_to_text_label(self) -> None:
        """When sprite URLs exist but none match regex, fall to text_label."""
        normalizer = ArchetypeNormalizer()
        archetype, raw, method = normalizer.resolve(
            ["https://example.com/mystery-image"],
            "Charizard ex",
        )
        assert method == "text_label"

    def test_empty_sprites_with_text_label(self) -> None:
        """Empty sprite list falls to text_label."""
        normalizer = ArchetypeNormalizer()
        archetype, raw, method = normalizer.resolve(
            [],
            "Gardevoir ex",
        )
        assert method == "text_label"
        assert archetype == "Gardevoir ex"

    def test_unknown_sprite_key_auto_derives(self) -> None:
        """Sprite key not in map falls to auto_derive."""
        normalizer = ArchetypeNormalizer()
        archetype, raw, method = normalizer.resolve(
            ["https://example.com/newpokemon.png"],
            "Some Deck",
        )
        assert method == "auto_derive"
        assert archetype == "Newpokemon"
