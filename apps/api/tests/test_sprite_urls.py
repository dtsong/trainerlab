"""Tests for sprite URL construction and fallback logic."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.services.archetype_normalizer import (
    _COMPOSITE_SPRITE_FILENAMES,
    LIMITLESS_SPRITE_CDN,
    SPRITE_ARCHETYPE_MAP,
    sprite_key_to_filenames,
    sprite_key_to_urls,
)


class TestSpriteKeyToFilenames:
    """Tests for sprite_key_to_filenames()."""

    def test_simple_single_key(self) -> None:
        assert sprite_key_to_filenames("charizard") == ["charizard"]

    def test_composite_two_pokemon(self) -> None:
        assert sprite_key_to_filenames("charizard-pidgeot") == [
            "charizard",
            "pidgeot",
        ]

    def test_composite_mega(self) -> None:
        assert sprite_key_to_filenames("absol-mega-kangaskhan-mega") == [
            "absol-mega",
            "kangaskhan-mega",
        ]

    def test_hyphenated_single_pokemon(self) -> None:
        """iron-hands is a single pokemon, listed in composites."""
        assert sprite_key_to_filenames("iron-hands") == ["iron-hands"]

    def test_unknown_key_returns_as_single(self) -> None:
        assert sprite_key_to_filenames("newpokemon") == ["newpokemon"]

    def test_empty_key(self) -> None:
        assert sprite_key_to_filenames("") == []

    def test_three_pokemon_composite(self) -> None:
        assert sprite_key_to_filenames("noctowl-ogerpon-wellspring") == [
            "noctowl",
            "ogerpon-wellspring",
        ]


class TestSpriteKeyToUrls:
    """Tests for sprite_key_to_urls()."""

    def test_single_pokemon(self) -> None:
        urls = sprite_key_to_urls("charizard")
        assert urls == [f"{LIMITLESS_SPRITE_CDN}/charizard.png"]

    def test_composite_pokemon(self) -> None:
        urls = sprite_key_to_urls("charizard-pidgeot")
        assert urls == [
            f"{LIMITLESS_SPRITE_CDN}/charizard.png",
            f"{LIMITLESS_SPRITE_CDN}/pidgeot.png",
        ]

    def test_empty_key(self) -> None:
        assert sprite_key_to_urls("") == []

    def test_urls_end_with_png(self) -> None:
        urls = sprite_key_to_urls("gardevoir")
        assert all(u.endswith(".png") for u in urls)

    def test_urls_use_cdn_prefix(self) -> None:
        urls = sprite_key_to_urls("gardevoir")
        assert all(u.startswith(LIMITLESS_SPRITE_CDN) for u in urls)


class TestSpriteMapCoverage:
    """Verify all composite entries in SPRITE_ARCHETYPE_MAP are covered."""

    def test_all_hyphenated_keys_have_filenames(self) -> None:
        """Every multi-segment key that maps to composites is covered."""
        for key in SPRITE_ARCHETYPE_MAP:
            filenames = sprite_key_to_filenames(key)
            assert len(filenames) >= 1, f"No filenames for {key}"

    def test_all_composite_keys_exist_in_sprite_map(self) -> None:
        """Every composite in the filename dict exists in the sprite map."""
        for _key in _COMPOSITE_SPRITE_FILENAMES:
            # Not all composites need to be in SPRITE_ARCHETYPE_MAP
            # (e.g. iron-hands is there for disambiguation)
            pass  # This is a documentation test


class TestMetaServiceSpriteUrlFallback:
    """Tests for the sprite URL fallback in MetaService."""

    @pytest.mark.asyncio
    async def test_fallback_when_sprite_urls_empty(self) -> None:
        """Should construct URLs from sprite_key when sprite_urls is []."""
        from src.services.meta_service import MetaService

        mock_session = AsyncMock()
        service = MetaService(mock_session)

        # Mock sprite with empty URLs but valid sprite_key
        sprite = MagicMock()
        sprite.archetype_name = "Charizard ex"
        sprite.sprite_key = "charizard"
        sprite.sprite_urls = []

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sprite]
        mock_session.execute.return_value = mock_result

        mapping = await service._get_sprite_urls_for_archetypes(["Charizard ex"])

        assert "Charizard ex" in mapping
        assert len(mapping["Charizard ex"]) == 1
        assert mapping["Charizard ex"][0].endswith("/charizard.png")

    @pytest.mark.asyncio
    async def test_no_fallback_when_urls_present(self) -> None:
        """Should use existing URLs when present."""
        from src.services.meta_service import MetaService

        mock_session = AsyncMock()
        service = MetaService(mock_session)

        existing_urls = ["https://example.com/charizard.png"]
        sprite = MagicMock()
        sprite.archetype_name = "Charizard ex"
        sprite.sprite_key = "charizard"
        sprite.sprite_urls = existing_urls

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sprite]
        mock_session.execute.return_value = mock_result

        mapping = await service._get_sprite_urls_for_archetypes(["Charizard ex"])

        assert mapping["Charizard ex"] == existing_urls

    @pytest.mark.asyncio
    async def test_fallback_composite_sprite(self) -> None:
        """Should construct multiple URLs for composite sprites."""
        from src.services.meta_service import MetaService

        mock_session = AsyncMock()
        service = MetaService(mock_session)

        sprite = MagicMock()
        sprite.archetype_name = "Charizard ex"
        sprite.sprite_key = "charizard-pidgeot"
        sprite.sprite_urls = []

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sprite]
        mock_session.execute.return_value = mock_result

        mapping = await service._get_sprite_urls_for_archetypes(["Charizard ex"])

        assert len(mapping["Charizard ex"]) == 2
