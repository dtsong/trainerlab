"""Format and rotation Pydantic schemas."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RotatingCard(BaseModel):
    """Single card that is rotating out of format."""

    model_config = ConfigDict(from_attributes=True)

    card_name: str = Field(description="Card name")
    card_id: str | None = Field(default=None, description="Card ID if known")
    count: int = Field(ge=1, le=4, description="Typical count in deck")
    role: str | None = Field(
        default=None, description="Role in deck (e.g., 'search', 'attacker', 'support')"
    )
    replacement: str | None = Field(
        default=None, description="Suggested replacement card if any"
    )


class RotationDetails(BaseModel):
    """Rotation details for an upcoming format."""

    model_config = ConfigDict(from_attributes=True)

    rotating_out_sets: list[str] = Field(
        description="Set codes rotating out (e.g., ['SVI', 'PAL', 'OBF'])"
    )
    new_set: str | None = Field(
        default=None, description="New set code being added (e.g., 'POR')"
    )


class FormatConfigResponse(BaseModel):
    """Format configuration response."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Format ID (UUID)")
    name: str = Field(description="Format name (e.g., 'svi-asc', 'tef-por')")
    display_name: str = Field(description="Display name (e.g., 'SVI-ASC', 'TEF-POR')")
    legal_sets: list[str] = Field(description="Legal set codes")
    start_date: date | None = Field(default=None, description="Format start date")
    end_date: date | None = Field(default=None, description="Format end date")
    is_current: bool = Field(description="Whether this is the current format")
    is_upcoming: bool = Field(description="Whether this is an upcoming format")
    rotation_details: RotationDetails | None = Field(
        default=None, description="Rotation details if upcoming format"
    )


class UpcomingFormatResponse(BaseModel):
    """Upcoming format with countdown information."""

    model_config = ConfigDict(from_attributes=True)

    format: FormatConfigResponse = Field(
        description="The upcoming format configuration"
    )
    days_until_rotation: int = Field(
        ge=0, description="Days until this format becomes active"
    )
    rotation_date: date = Field(description="Date when rotation occurs")


SurvivalRating = Literal["dies", "crippled", "adapts", "thrives", "unknown"]


class RotationImpactResponse(BaseModel):
    """Per-archetype rotation impact analysis."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Impact ID (UUID)")
    format_transition: str = Field(
        description="Format transition (e.g., 'svi-asc-to-tef-por')"
    )
    archetype_id: str = Field(description="Archetype ID (e.g., 'charizard-ex')")
    archetype_name: str = Field(description="Archetype name (e.g., 'Charizard ex')")
    survival_rating: SurvivalRating = Field(
        description="How the archetype survives rotation"
    )
    rotating_cards: list[RotatingCard] | None = Field(
        default=None, description="Cards rotating out with details"
    )
    analysis: str | None = Field(
        default=None, description="Detailed analysis (Research Pass content)"
    )
    jp_evidence: str | None = Field(default=None, description="Evidence from JP meta")
    jp_survival_share: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Meta share in JP post-rotation"
    )


class RotationImpactListResponse(BaseModel):
    """List of all archetype rotation impacts for a format transition."""

    model_config = ConfigDict(from_attributes=True)

    format_transition: str = Field(
        description="Format transition (e.g., 'svi-asc-to-tef-por')"
    )
    impacts: list[RotationImpactResponse] = Field(
        description="List of archetype impacts"
    )
    total_archetypes: int = Field(description="Total number of archetypes analyzed")
