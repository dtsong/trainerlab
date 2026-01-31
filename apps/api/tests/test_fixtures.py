"""Tests for fixture data structures."""

from datetime import date

import pytest
from pydantic import ValidationError

from src.fixtures.tournaments import (
    ARCHETYPE_MAPPING,
    PlacementFixture,
    TournamentFixture,
    normalize_archetype,
)


class TestPlacementFixture:
    """Tests for PlacementFixture model."""

    def test_minimal_placement(self) -> None:
        """Should create placement with minimal required fields."""
        placement = PlacementFixture(placement=1, archetype="Charizard ex")

        assert placement.placement == 1
        assert placement.archetype == "Charizard ex"
        assert placement.player_name is None
        assert placement.decklist is None
        assert placement.decklist_source is None

    def test_full_placement(self) -> None:
        """Should create placement with all fields."""
        decklist = [{"card_id": "sv4-6", "quantity": 4}]
        placement = PlacementFixture(
            placement=1,
            player_name="Test Player",
            archetype="Charizard ex",
            decklist=decklist,
            decklist_source="https://limitlesstcg.com/decks/123",
        )

        assert placement.placement == 1
        assert placement.player_name == "Test Player"
        assert placement.archetype == "Charizard ex"
        assert placement.decklist == decklist
        assert placement.decklist_source == "https://limitlesstcg.com/decks/123"

    def test_invalid_placement_zero(self) -> None:
        """Should reject placement of 0."""
        with pytest.raises(ValidationError):
            PlacementFixture(placement=0, archetype="Charizard ex")

    def test_invalid_placement_negative(self) -> None:
        """Should reject negative placement."""
        with pytest.raises(ValidationError):
            PlacementFixture(placement=-1, archetype="Charizard ex")


class TestTournamentFixture:
    """Tests for TournamentFixture model."""

    def test_minimal_tournament(self) -> None:
        """Should create tournament with minimal required fields."""
        tournament = TournamentFixture(
            name="Test Regional",
            date=date(2024, 6, 15),
            region="NA",
        )

        assert tournament.name == "Test Regional"
        assert tournament.date == date(2024, 6, 15)
        assert tournament.region == "NA"
        assert tournament.country is None
        assert tournament.game_format == "standard"
        assert tournament.best_of == 3
        assert tournament.participant_count is None
        assert tournament.source is None
        assert tournament.source_url is None
        assert tournament.placements == []

    def test_full_tournament(self) -> None:
        """Should create tournament with all fields."""
        placements = [
            PlacementFixture(placement=1, archetype="Charizard ex"),
            PlacementFixture(placement=2, archetype="Lugia VSTAR"),
        ]
        tournament = TournamentFixture(
            name="NAIC 2024",
            date=date(2024, 6, 15),
            region="NA",
            country="USA",
            format="standard",
            best_of=3,
            participant_count=1200,
            source="limitless",
            source_url="https://limitlesstcg.com/tournaments/na/2024/naic",
            placements=placements,
        )

        assert tournament.name == "NAIC 2024"
        assert tournament.region == "NA"
        assert tournament.country == "USA"
        assert tournament.game_format == "standard"
        assert tournament.best_of == 3
        assert tournament.participant_count == 1200
        assert tournament.source == "limitless"
        assert len(tournament.placements) == 2

    def test_japan_bo1(self) -> None:
        """Should support BO1 format for Japan tournaments."""
        tournament = TournamentFixture(
            name="Champions League Yokohama",
            date=date(2024, 5, 1),
            region="JP",
            best_of=1,
        )

        assert tournament.region == "JP"
        assert tournament.best_of == 1

    def test_invalid_region(self) -> None:
        """Should reject invalid region."""
        with pytest.raises(ValidationError):
            TournamentFixture(
                name="Test",
                date=date(2024, 1, 1),
                region="INVALID",  # type: ignore
            )

    def test_invalid_game_format(self) -> None:
        """Should reject invalid game_format via alias."""
        with pytest.raises(ValidationError):
            TournamentFixture.model_validate(
                {
                    "name": "Test",
                    "date": "2024-01-01",
                    "region": "NA",
                    "format": "unlimited",
                }
            )

    def test_invalid_best_of(self) -> None:
        """Should reject invalid best_of value."""
        with pytest.raises(ValidationError):
            TournamentFixture(
                name="Test",
                date=date(2024, 1, 1),
                region="NA",
                best_of=5,  # type: ignore
            )

    def test_empty_name(self) -> None:
        """Should reject empty name."""
        with pytest.raises(ValidationError):
            TournamentFixture(
                name="",
                date=date(2024, 1, 1),
                region="NA",
            )


class TestArchetypeMapping:
    """Tests for archetype mapping."""

    def test_mapping_exists(self) -> None:
        """Should have archetype mapping defined."""
        assert isinstance(ARCHETYPE_MAPPING, dict)
        assert len(ARCHETYPE_MAPPING) > 0

    def test_normalize_known_archetype(self) -> None:
        """Should normalize known archetype variations."""
        assert normalize_archetype("charizard ex") == "Charizard ex"
        assert normalize_archetype("CHARIZARD EX") == "Charizard ex"
        assert normalize_archetype("zard") == "Charizard ex"
        assert normalize_archetype("charizard ex/pidgeot ex") == "Charizard ex"

    def test_normalize_lugia_variants(self) -> None:
        """Should normalize Lugia variants."""
        assert normalize_archetype("lugia vstar") == "Lugia VSTAR"
        assert normalize_archetype("lugia") == "Lugia VSTAR"
        assert normalize_archetype("lugia/archeops") == "Lugia VSTAR"

    def test_normalize_unknown_archetype(self) -> None:
        """Should return original for unknown archetypes."""
        assert normalize_archetype("Some New Deck") == "Some New Deck"
        assert normalize_archetype("Unknown Archetype") == "Unknown Archetype"

    def test_normalize_strips_whitespace(self) -> None:
        """Should strip whitespace before normalizing."""
        assert normalize_archetype("  charizard ex  ") == "Charizard ex"

    def test_normalize_case_insensitive(self) -> None:
        """Should be case insensitive."""
        assert normalize_archetype("GARDEVOIR EX") == "Gardevoir ex"
        assert normalize_archetype("Gardevoir Ex") == "Gardevoir ex"
