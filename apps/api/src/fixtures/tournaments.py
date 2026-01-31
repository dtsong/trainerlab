"""Tournament fixture data structures for seeding.

Defines Pydantic models for tournament fixture format, placement data,
and archetype mapping for meta analysis.
"""

from datetime import date as date_type
from typing import Literal

from pydantic import BaseModel, Field


class PlacementFixture(BaseModel):
    """Placement data for a tournament result.

    Attributes:
        placement: Final standing (1 = winner, 2 = finalist, etc.)
        player_name: Optional player name
        archetype: Deck archetype name (e.g., "Charizard ex", "Lugia VSTAR")
        decklist: Optional deck list as list of {card_id, quantity} dicts
        decklist_source: Optional URL/source for the deck list
    """

    placement: int = Field(..., ge=1, description="Final placement (1 = winner)")
    player_name: str | None = Field(None, description="Player name")
    archetype: str = Field(..., description="Deck archetype name")
    decklist: list[dict[str, str | int]] | None = Field(
        None, description="Deck list as [{card_id, quantity}, ...]"
    )
    decklist_source: str | None = Field(None, description="Source URL for deck list")


class TournamentFixture(BaseModel):
    """Tournament fixture data for seeding.

    Attributes:
        name: Tournament name
        date: Tournament date
        region: Geographic region (NA, EU, JP, LATAM, OCE)
        country: Optional country name
        game_format: Game format (standard, expanded)
        best_of: Match format (1 for Japan BO1, 3 for international BO3)
        participant_count: Optional total participant count
        source: Data source (limitless, rk9, etc.)
        source_url: Optional URL to tournament page
        placements: List of placement results (typically top 8/16/32)
    """

    name: str = Field(..., min_length=1, max_length=255)
    date: date_type = Field(..., description="Tournament date")
    region: Literal["NA", "EU", "JP", "LATAM", "OCE"] = Field(
        ..., description="Geographic region"
    )
    country: str | None = Field(None, max_length=100)
    game_format: Literal["standard", "expanded"] = Field(
        "standard", alias="format", serialization_alias="format"
    )
    best_of: Literal[1, 3] = Field(3, description="BO1 (Japan) or BO3 (international)")
    participant_count: int | None = Field(None, ge=1)
    source: str | None = Field(None, description="Data source name")
    source_url: str | None = Field(None, description="Tournament page URL")
    placements: list[PlacementFixture] = Field(
        default_factory=list, description="Top placements"
    )


# Archetype mapping: common variations -> canonical archetype name
# This helps normalize archetype names across different sources
ARCHETYPE_MAPPING: dict[str, str] = {
    # Charizard variants
    "charizard ex": "Charizard ex",
    "charizard": "Charizard ex",
    "zard": "Charizard ex",
    "charizard ex/pidgeot ex": "Charizard ex",
    "charizard/pidgeot": "Charizard ex",
    # Lugia variants
    "lugia vstar": "Lugia VSTAR",
    "lugia": "Lugia VSTAR",
    "lugia/archeops": "Lugia VSTAR",
    # Gardevoir variants
    "gardevoir ex": "Gardevoir ex",
    "gardevoir": "Gardevoir ex",
    "garde": "Gardevoir ex",
    # Miraidon variants
    "miraidon ex": "Miraidon ex",
    "miraidon": "Miraidon ex",
    "future box": "Miraidon ex",
    # Giratina variants
    "giratina vstar": "Giratina VSTAR",
    "giratina": "Giratina VSTAR",
    "lost box/giratina": "Giratina VSTAR",
    "lostbox giratina": "Giratina VSTAR",
    # Roaring Moon variants
    "roaring moon ex": "Roaring Moon ex",
    "roaring moon": "Roaring Moon ex",
    # Chien-Pao variants
    "chien-pao ex": "Chien-Pao ex",
    "chien-pao": "Chien-Pao ex",
    "chien pao": "Chien-Pao ex",
    "baxcalibur": "Chien-Pao ex",
    # Snorlax variants
    "snorlax stall": "Snorlax Stall",
    "snorlax control": "Snorlax Stall",
    "snorlax": "Snorlax Stall",
    # Lost Box variants
    "lost box": "Lost Box",
    "lost zone box": "Lost Box",
    "lostbox": "Lost Box",
    # Mew variants
    "mew vmax": "Mew VMAX",
    "mew": "Mew VMAX",
    "fusion mew": "Mew VMAX",
    # Iron Thorns variants
    "iron thorns ex": "Iron Thorns ex",
    "iron thorns": "Iron Thorns ex",
    # Raging Bolt variants
    "raging bolt ex": "Raging Bolt ex",
    "raging bolt": "Raging Bolt ex",
    "raging bolt/ogerpon": "Raging Bolt ex",
    # Dragapult variants
    "dragapult ex": "Dragapult ex",
    "dragapult": "Dragapult ex",
    # Ancient Box variants
    "ancient box": "Ancient Box",
    "ancients": "Ancient Box",
    # Regidrago variants
    "regidrago vstar": "Regidrago VSTAR",
    "regidrago": "Regidrago VSTAR",
    # Gholdengo variants
    "gholdengo ex": "Gholdengo ex",
    "gholdengo": "Gholdengo ex",
    # Control/Stall variants
    "control": "Control",
    "stall": "Control",
}


def normalize_archetype(archetype: str) -> str:
    """Normalize an archetype name to its canonical form.

    Input is lowercased and stripped before lookup, so "Charizard EX" and
    " charizard ex " both map to "Charizard ex".

    Args:
        archetype: Raw archetype name from tournament data

    Returns:
        Canonical archetype name, or the original if no mapping exists
    """
    return ARCHETYPE_MAPPING.get(archetype.lower().strip(), archetype)
