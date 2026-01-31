"""Tournament Pydantic schemas."""

from datetime import date as date_type
from enum import IntEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

GameFormat = Literal["standard", "expanded"]


class BestOf(IntEnum):
    """Match format options."""

    BO1 = 1
    BO3 = 3


class TopPlacement(BaseModel):
    """Top placement info for tournament summary."""

    model_config = ConfigDict(from_attributes=True)

    placement: int = Field(ge=1, description="Placement (1st, 2nd, etc.)")
    player_name: str | None = Field(default=None, description="Player name")
    archetype: str = Field(description="Deck archetype")


class TournamentSummary(BaseModel):
    """Tournament summary for list views."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Tournament ID")
    name: str = Field(description="Tournament name")
    date: date_type = Field(description="Tournament date")
    region: str = Field(description="Region (NA, EU, JP, etc.)")
    country: str | None = Field(default=None, description="Country")
    format: GameFormat = Field(description="Game format")
    best_of: Literal[1, 3] = Field(description="Match format (1 for BO1, 3 for BO3)")
    participant_count: int | None = Field(
        default=None, description="Number of participants"
    )
    top_placements: list[TopPlacement] = Field(
        default_factory=list, description="Top placements (top 8)"
    )
