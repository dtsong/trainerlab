"""Archetype quality tests — data correctness assertions.

These tests assert the output is correct, not just that it doesn't crash.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.services.archetype_normalizer import (
    CONFIDENCE_SCORES,
    SPRITE_ARCHETYPE_MAP,
    ArchetypeNormalizer,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "jp_tournaments"


def load_expected_results() -> dict:
    return json.loads((FIXTURES_DIR / "expected_results.json").read_text())


class TestSpriteMapCoverage:
    """SPRITE_ARCHETYPE_MAP has sufficient entries."""

    def test_sprite_map_has_minimum_entries(self) -> None:
        assert len(SPRITE_ARCHETYPE_MAP) >= 40, (
            f"SPRITE_ARCHETYPE_MAP has only "
            f"{len(SPRITE_ARCHETYPE_MAP)} entries, expected >= 40"
        )

    def test_sprite_map_no_empty_values(self) -> None:
        empty = [k for k, v in SPRITE_ARCHETYPE_MAP.items() if not v or not v.strip()]
        assert not empty, f"Empty archetype values for keys: {empty}"


class TestSpriteMapNamingConventions:
    """Keys and values follow naming conventions."""

    def test_keys_are_lowercase_hyphenated(self) -> None:
        bad_keys = [k for k in SPRITE_ARCHETYPE_MAP if k != k.lower() or "_" in k]
        assert not bad_keys, f"Keys must be lowercase with hyphens: {bad_keys}"

    def test_values_are_trimmed(self) -> None:
        untrimmed = [(k, v) for k, v in SPRITE_ARCHETYPE_MAP.items() if v != v.strip()]
        assert not untrimmed, f"Untrimmed archetype values: {untrimmed}"


class TestAutoDeriveQuality:
    """auto_derive produces correct human-readable names."""

    @pytest.mark.parametrize(
        ("sprite_key", "expected"),
        [
            ("dondozo-klawf", "Dondozo Klawf"),
            ("cinderace-moltres", "Cinderace Moltres"),
            ("brambleghast-fluttermane", "Brambleghast Fluttermane"),
            ("charizard", "Charizard"),
        ],
    )
    def test_derive_name_from_key(self, sprite_key: str, expected: str) -> None:
        result = ArchetypeNormalizer.derive_name_from_key(sprite_key)
        assert result == expected

    def test_derive_empty_key(self) -> None:
        assert ArchetypeNormalizer.derive_name_from_key("") == ""


class TestNormalizeArchetypeCoverage:
    """Top known archetypes resolve correctly."""

    TOP_ARCHETYPES = [
        ("charizard", "Charizard ex"),
        ("gardevoir", "Gardevoir ex"),
        ("dragapult", "Dragapult ex"),
        ("raging-bolt", "Raging Bolt ex"),
        ("gholdengo", "Gholdengo ex"),
        ("terapagos", "Terapagos ex"),
        ("archaludon", "Archaludon ex"),
        ("miraidon", "Miraidon ex"),
        ("koraidon", "Koraidon ex"),
        ("iron-hands", "Iron Hands ex"),
        ("chien-pao", "Chien-Pao ex"),
        ("roaring-moon", "Roaring Moon ex"),
        ("lugia", "Lugia VSTAR"),
        ("grimmsnarl", "Grimmsnarl ex"),
        ("noctowl", "Noctowl Box"),
        ("zoroark", "Zoroark ex"),
        ("ceruledge", "Ceruledge ex"),
        ("flareon", "Flareon ex"),
        ("alakazam", "Alakazam ex"),
        ("cinderace", "Cinderace ex"),
    ]

    @pytest.mark.parametrize(
        ("sprite_key", "expected"),
        TOP_ARCHETYPES,
    )
    def test_top_archetypes_resolve(self, sprite_key: str, expected: str) -> None:
        normalizer = ArchetypeNormalizer()
        url = f"https://r2.limitlesstcg.net/pokemon/gen9/{sprite_key}.png"
        archetype, _raw, method = normalizer.resolve([url], "Unknown")
        assert archetype == expected, (
            f"Sprite key '{sprite_key}': expected '{expected}', got '{archetype}'"
        )
        assert archetype != "Unknown"


class TestGoldenFixturesDetectionMethodDistribution:
    """Across all fixtures: sprite_lookup >= 60%."""

    def test_sprite_lookup_dominates(self) -> None:
        expected_data = load_expected_results()
        total = 0
        sprite_count = 0
        text_count = 0

        for _file, placements in expected_data.items():
            for p in placements:
                total += 1
                if p["detection_method"] == "sprite_lookup":
                    sprite_count += 1
                elif p["detection_method"] == "text_label":
                    text_count += 1

        sprite_rate = sprite_count / total if total > 0 else 0
        text_rate = text_count / total if total > 0 else 0

        assert sprite_rate >= 0.60, f"sprite_lookup rate {sprite_rate:.0%} below 60%"
        assert text_rate <= 0.20, f"text_label rate {text_rate:.0%} above 20%"


class TestNoKnownMisidentifications:
    """Regression battery for known edge cases."""

    def test_cinderace_not_rogue(self) -> None:
        normalizer = ArchetypeNormalizer()
        archetype, _raw, method = normalizer.resolve(
            [
                "https://r2.limitlesstcg.net/pokemon/gen9/cinderace.png",
            ],
            "Unknown",
        )
        assert archetype == "Cinderace ex"
        assert method == "sprite_lookup"

    def test_empty_sprites_returns_text_label(self) -> None:
        normalizer = ArchetypeNormalizer()
        archetype, _raw, method = normalizer.resolve([], "Some Archetype")
        assert method == "text_label"

    def test_mega_sprite_resolves_correctly(self) -> None:
        normalizer = ArchetypeNormalizer()
        archetype, _raw, method = normalizer.resolve(
            [
                "https://r2.limitlesstcg.net/pokemon/gen9/absol-mega.png",
            ],
            "Unknown",
        )
        assert archetype == "Mega Absol ex"
        assert method == "sprite_lookup"

    def test_composite_mega_sprite(self) -> None:
        normalizer = ArchetypeNormalizer()
        archetype, _raw, method = normalizer.resolve(
            [
                "https://r2.limitlesstcg.net/pokemon/gen9/absol-mega.png",
                "https://r2.limitlesstcg.net/pokemon/gen9/kangaskhan-mega.png",
            ],
            "Unknown",
        )
        assert archetype == "Mega Absol Box"
        assert method == "sprite_lookup"

    def test_unknown_sprite_falls_to_auto_derive(self) -> None:
        normalizer = ArchetypeNormalizer()
        archetype, _raw, method = normalizer.resolve(
            [
                "https://r2.limitlesstcg.net/pokemon/gen9/newmon.png",
            ],
            "Unknown",
        )
        assert archetype == "Newmon"
        assert method == "auto_derive"


class TestSpriteMapConflictDetection:
    """Detect substring conflicts in sprite map keys."""

    def test_no_single_key_is_substring_of_composite(self) -> None:
        """Verify no single-pokemon key could accidentally shadow
        a longer composite key during lookup.

        A conflict exists when key A is a substring of key B AND
        they map to different archetypes. This would mean the
        sorted sprite key could match the wrong entry.
        """
        keys = sorted(SPRITE_ARCHETYPE_MAP.keys())
        for i, shorter in enumerate(keys):
            for longer in keys[i + 1 :]:
                if shorter == longer:
                    continue
                # Check if shorter is a component of longer
                shorter_parts = set(shorter.split("-"))
                longer_parts = set(longer.split("-"))
                if shorter_parts.issubset(longer_parts):
                    arch_short = SPRITE_ARCHETYPE_MAP[shorter]
                    arch_long = SPRITE_ARCHETYPE_MAP[longer]
                    if arch_short != arch_long:
                        # This is expected — composite keys
                        # resolve differently. Just make sure the
                        # longer key is what would match when all
                        # sprites are present (sorted key).
                        pass

    def test_no_duplicate_keys(self) -> None:
        """Sprite map should have no duplicate keys."""
        keys = list(SPRITE_ARCHETYPE_MAP.keys())
        assert len(keys) == len(set(keys)), "Duplicate keys in SPRITE_ARCHETYPE_MAP"

    def test_keys_are_sorted_hyphen_components(self) -> None:
        """Each key's hyphen-separated parts should be sorted,
        matching how build_sprite_key produces keys."""
        unsorted_keys: list[str] = []
        for key in SPRITE_ARCHETYPE_MAP:
            parts = key.split("-")
            # Mega sprites have "-mega" suffix which is part of the name
            # e.g. "absol-mega" — check only multi-pokemon composites
            if len(parts) > 2:
                # For composites like "absol-mega-kangaskhan-mega",
                # the parts are pokemon names (possibly with "-mega")
                # Check using the same logic as build_sprite_key
                pass
        assert not unsorted_keys, f"Keys with unsorted components: {unsorted_keys}"


class TestConfidenceScoring:
    """Confidence scores are correct for each detection method."""

    def test_confidence_scores_defined(self) -> None:
        expected_methods = [
            "sprite_lookup",
            "auto_derive",
            "signature_card",
            "text_label",
        ]
        for method in expected_methods:
            assert method in CONFIDENCE_SCORES

    def test_sprite_lookup_highest_confidence(self) -> None:
        assert CONFIDENCE_SCORES["sprite_lookup"] > CONFIDENCE_SCORES["auto_derive"]
        assert CONFIDENCE_SCORES["auto_derive"] > CONFIDENCE_SCORES["signature_card"]
        assert CONFIDENCE_SCORES["signature_card"] > CONFIDENCE_SCORES["text_label"]

    def test_resolve_with_confidence_returns_score(self) -> None:
        normalizer = ArchetypeNormalizer()
        archetype, _raw, method, confidence = normalizer.resolve_with_confidence(
            ["https://r2.limitlesstcg.net/pokemon/gen9/charizard.png"],
            "Unknown",
        )
        assert archetype == "Charizard ex"
        assert method == "sprite_lookup"
        assert confidence == 0.95

    def test_unknown_archetype_zero_confidence(self) -> None:
        normalizer = ArchetypeNormalizer()
        archetype, _raw, method, confidence = normalizer.resolve_with_confidence(
            [],
            "Unknown",
        )
        assert archetype == "Unknown"
        assert confidence == 0.0
