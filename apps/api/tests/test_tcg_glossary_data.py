"""Tests for TCG glossary data structure, content, and utility functions.

Validates TCG_GLOSSARY entries, GlossaryEntry dataclass fields, category
filtering, term lookup, and the Claude glossary export function.
"""

import pytest

from src.data.tcg_glossary import (
    TCG_GLOSSARY,
    GlossaryEntry,
    get_claude_glossary,
    get_terms_by_category,
    lookup_term,
)


class TestGlossaryStructure:
    """TCG_GLOSSARY must be a well-formed, non-empty mapping."""

    def test_glossary_is_non_empty(self) -> None:
        """TCG_GLOSSARY must contain entries."""
        assert len(TCG_GLOSSARY) > 0

    def test_all_keys_are_strings(self) -> None:
        """Every glossary key must be a string."""
        for key in TCG_GLOSSARY:
            assert isinstance(key, str), f"Key {key!r} is not a string"

    def test_all_values_are_glossary_entries(self) -> None:
        """Every value must be a GlossaryEntry instance."""
        for key, entry in TCG_GLOSSARY.items():
            assert isinstance(entry, GlossaryEntry), (
                f"Value for {key} is not a GlossaryEntry: {type(entry)}"
            )

    def test_no_empty_keys(self) -> None:
        """No glossary key should be empty or whitespace-only."""
        for key in TCG_GLOSSARY:
            assert key.strip(), f"Found empty glossary key: {key!r}"


class TestGlossaryEntryFields:
    """Each GlossaryEntry must have all required fields populated."""

    def test_all_entries_have_jp_field(self) -> None:
        """Every entry must have a non-empty jp field."""
        for key, entry in TCG_GLOSSARY.items():
            assert entry.jp, f"Entry {key} has empty jp field"

    def test_all_entries_have_romaji_field(self) -> None:
        """Every entry must have a non-empty romaji field."""
        for key, entry in TCG_GLOSSARY.items():
            assert entry.romaji, f"Entry {key} has empty romaji field"

    def test_all_entries_have_en_field(self) -> None:
        """Every entry must have a non-empty en (English) field."""
        for key, entry in TCG_GLOSSARY.items():
            assert entry.en, f"Entry {key} has empty en field"

    def test_all_entries_have_context_field(self) -> None:
        """Every entry must have a non-empty context field."""
        for key, entry in TCG_GLOSSARY.items():
            assert entry.context, f"Entry {key} has empty context field"

    def test_all_entries_have_valid_category(self) -> None:
        """Every entry must have a category from the allowed set."""
        valid_categories = {
            "game_term",
            "card_type",
            "tournament_term",
            "meta_term",
            "strategic_term",
        }
        for key, entry in TCG_GLOSSARY.items():
            assert entry.category in valid_categories, (
                f"Entry {key} has invalid category: {entry.category}"
            )

    def test_key_matches_jp_field(self) -> None:
        """The dict key should match the entry's jp field."""
        for key, entry in TCG_GLOSSARY.items():
            assert key == entry.jp, (
                f"Key {key!r} does not match entry jp field {entry.jp!r}"
            )

    def test_entries_are_frozen(self) -> None:
        """GlossaryEntry instances should be immutable (frozen dataclass)."""
        entry = next(iter(TCG_GLOSSARY.values()))
        with pytest.raises(AttributeError):
            entry.en = "modified"  # type: ignore[misc]


class TestGlossaryKnownTerms:
    """Known TCG terms must be present in the glossary."""

    def test_ex_term_present(self) -> None:
        """Card type 'ex' should be in the glossary."""
        assert "ex" in TCG_GLOSSARY
        assert TCG_GLOSSARY["ex"].en == "ex"
        assert TCG_GLOSSARY["ex"].category == "card_type"

    def test_vstar_term_present(self) -> None:
        """Card type 'VSTAR' should be in the glossary."""
        assert "VSTAR" in TCG_GLOSSARY
        assert TCG_GLOSSARY["VSTAR"].en == "VSTAR"
        assert TCG_GLOSSARY["VSTAR"].category == "card_type"

    def test_vmax_term_present(self) -> None:
        """Card type 'VMAX' should be in the glossary."""
        assert "VMAX" in TCG_GLOSSARY
        assert TCG_GLOSSARY["VMAX"].en == "VMAX"

    def test_ace_spec_term_present(self) -> None:
        """Card type 'ACE SPEC' should be in the glossary."""
        assert "ACE SPEC" in TCG_GLOSSARY
        assert TCG_GLOSSARY["ACE SPEC"].en == "ACE SPEC"

    def test_supporter_term_present(self) -> None:
        """Supporter card type should be in the glossary."""
        assert "\u30b5\u30dd\u30fc\u30c8" in TCG_GLOSSARY
        entry = TCG_GLOSSARY["\u30b5\u30dd\u30fc\u30c8"]
        assert entry.en == "Supporter"
        assert entry.category == "card_type"

    def test_lost_zone_term_present(self) -> None:
        """Lost Zone game term should be in the glossary."""
        assert "\u30ed\u30b9\u30c8\u30be\u30fc\u30f3" in TCG_GLOSSARY
        assert TCG_GLOSSARY["\u30ed\u30b9\u30c8\u30be\u30fc\u30f3"].en == "Lost Zone"


class TestGlossaryCategoryDistribution:
    """Glossary should contain entries across all defined categories."""

    @pytest.fixture
    def categories_in_glossary(self) -> set[str]:
        """Set of all unique categories found in the glossary."""
        return {entry.category for entry in TCG_GLOSSARY.values()}

    def test_has_game_terms(self, categories_in_glossary: set[str]) -> None:
        """Glossary must include game_term entries."""
        assert "game_term" in categories_in_glossary

    def test_has_card_types(self, categories_in_glossary: set[str]) -> None:
        """Glossary must include card_type entries."""
        assert "card_type" in categories_in_glossary

    def test_has_tournament_terms(self, categories_in_glossary: set[str]) -> None:
        """Glossary must include tournament_term entries."""
        assert "tournament_term" in categories_in_glossary

    def test_has_meta_terms(self, categories_in_glossary: set[str]) -> None:
        """Glossary must include meta_term entries."""
        assert "meta_term" in categories_in_glossary

    def test_has_strategic_terms(self, categories_in_glossary: set[str]) -> None:
        """Glossary must include strategic_term entries."""
        assert "strategic_term" in categories_in_glossary


class TestLookupTerm:
    """lookup_term must correctly find or miss glossary entries."""

    def test_lookup_existing_term(self) -> None:
        """Should return GlossaryEntry for a known Japanese term."""
        result = lookup_term("ex")
        assert result is not None
        assert isinstance(result, GlossaryEntry)
        assert result.en == "ex"

    def test_lookup_jp_term(self) -> None:
        """Should return GlossaryEntry for a Japanese-language key."""
        result = lookup_term("\u30ef\u30b6")
        assert result is not None
        assert result.en == "Attack"

    def test_lookup_missing_term_returns_none(self) -> None:
        """Should return None for a term not in the glossary."""
        result = lookup_term("nonexistent_term_xyz")
        assert result is None

    def test_lookup_empty_string_returns_none(self) -> None:
        """Should return None for empty string input."""
        result = lookup_term("")
        assert result is None


class TestGetTermsByCategory:
    """get_terms_by_category must filter entries correctly."""

    def test_returns_only_matching_category(self) -> None:
        """All returned entries must belong to the requested category."""
        entries = get_terms_by_category("card_type")
        assert len(entries) > 0
        for entry in entries:
            assert entry.category == "card_type", (
                f"Entry {entry.jp} has category {entry.category}, expected card_type"
            )

    def test_game_terms_not_empty(self) -> None:
        """game_term category should have entries."""
        entries = get_terms_by_category("game_term")
        assert len(entries) > 0

    def test_tournament_terms_not_empty(self) -> None:
        """tournament_term category should have entries."""
        entries = get_terms_by_category("tournament_term")
        assert len(entries) > 0

    def test_strategic_terms_not_empty(self) -> None:
        """strategic_term category should have entries."""
        entries = get_terms_by_category("strategic_term")
        assert len(entries) > 0

    def test_returns_list_of_glossary_entries(self) -> None:
        """Return type should be a list of GlossaryEntry objects."""
        entries = get_terms_by_category("meta_term")
        assert isinstance(entries, list)
        for entry in entries:
            assert isinstance(entry, GlossaryEntry)


class TestGetClaudeGlossary:
    """get_claude_glossary must return a clean {jp: en} mapping."""

    def test_returns_dict(self) -> None:
        """Should return a dict."""
        result = get_claude_glossary()
        assert isinstance(result, dict)

    def test_returns_non_empty_dict(self) -> None:
        """Should return a non-empty dict."""
        result = get_claude_glossary()
        assert len(result) > 0

    def test_maps_jp_to_en(self) -> None:
        """Keys should be Japanese terms, values English translations."""
        result = get_claude_glossary()
        # Check a known entry
        assert result["ex"] == "ex"
        assert result["VSTAR"] == "VSTAR"

    def test_returns_a_copy(self) -> None:
        """Should return a copy, not the internal dict."""
        result1 = get_claude_glossary()
        result2 = get_claude_glossary()
        # Mutating one should not affect the other
        result1["test_key"] = "test_value"
        assert "test_key" not in result2

    def test_has_same_count_as_glossary(self) -> None:
        """Claude glossary should have the same number of entries as TCG_GLOSSARY."""
        result = get_claude_glossary()
        assert len(result) == len(TCG_GLOSSARY)
