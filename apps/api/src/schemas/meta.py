"""Meta snapshot Pydantic schemas."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ArchetypeResponse(BaseModel):
    """Single archetype in meta snapshot."""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(description="Archetype name (e.g., 'Charizard ex')")
    share: float = Field(ge=0.0, le=1.0, description="Meta share percentage (0.0-1.0)")
    sample_decks: list[str] | None = Field(
        default=None, description="Sample deck IDs for this archetype"
    )
    key_cards: list[str] | None = Field(
        default=None, description="Key card IDs that define this archetype"
    )


class CardUsageSummary(BaseModel):
    """Card usage statistics in meta snapshot."""

    model_config = ConfigDict(from_attributes=True)

    card_id: str = Field(description="Card ID")
    inclusion_rate: float = Field(
        ge=0.0, le=1.0, description="Rate of decks including this card (0.0-1.0)"
    )
    avg_copies: float = Field(ge=0.0, description="Average copies when included")


class FormatNotes(BaseModel):
    """Format-specific notes and context."""

    model_config = ConfigDict(from_attributes=True)

    tie_rules: str | None = Field(
        default=None,
        description="How ties are handled in this format",
    )
    typical_regions: list[str] | None = Field(
        default=None,
        description="Regions where this format is typically used",
    )
    notes: str | None = Field(
        default=None,
        description="Additional context about this format",
    )


class MetaSnapshotResponse(BaseModel):
    """Full meta snapshot response."""

    model_config = ConfigDict(from_attributes=True)

    snapshot_date: date = Field(description="Date of the snapshot")
    region: str | None = Field(
        default=None, description="Region (NA, EU, JP, etc.) or null for global"
    )
    format: Literal["standard", "expanded"] = Field(description="Game format")
    best_of: int = Field(description="Match format (1 for BO1, 3 for BO3)")
    archetype_breakdown: list[ArchetypeResponse] = Field(
        description="List of archetypes with their meta shares"
    )
    card_usage: list[CardUsageSummary] = Field(
        default_factory=list, description="Card usage statistics"
    )
    sample_size: int = Field(ge=0, description="Number of placements in sample")
    tournaments_included: list[str] | None = Field(
        default=None, description="Tournament IDs included in the snapshot"
    )
    format_notes: FormatNotes | None = Field(
        default=None,
        description="Format-specific notes (e.g., Japan BO1 tie rules)",
    )


class MetaHistoryResponse(BaseModel):
    """Meta history response with multiple snapshots."""

    model_config = ConfigDict(from_attributes=True)

    snapshots: list[MetaSnapshotResponse] = Field(
        description="List of meta snapshots ordered by date descending"
    )


class ArchetypeHistoryPoint(BaseModel):
    """Single point in archetype history."""

    model_config = ConfigDict(from_attributes=True)

    snapshot_date: date = Field(description="Date of the snapshot")
    share: float = Field(ge=0.0, le=1.0, description="Meta share at this date")
    sample_size: int = Field(ge=0, description="Number of placements in sample")


class KeyCardResponse(BaseModel):
    """Key card with usage stats for an archetype."""

    model_config = ConfigDict(from_attributes=True)

    card_id: str = Field(description="Card ID")
    inclusion_rate: float = Field(
        ge=0.0, le=1.0, description="Rate of archetype decks including this card"
    )
    avg_copies: float = Field(ge=0.0, description="Average copies when included")


class SampleDeckResponse(BaseModel):
    """Sample deck for an archetype."""

    model_config = ConfigDict(from_attributes=True)

    deck_id: str = Field(description="Deck or placement ID")
    tournament_name: str | None = Field(default=None, description="Tournament name")
    placement: int | None = Field(default=None, description="Tournament placement")
    player_name: str | None = Field(
        default=None, description="Player name if available"
    )


class ArchetypeDetailResponse(BaseModel):
    """Detailed archetype information with history."""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(description="Archetype name")
    current_share: float = Field(
        ge=0.0, le=1.0, description="Current meta share percentage"
    )
    history: list[ArchetypeHistoryPoint] = Field(
        description="Historical meta share over time"
    )
    key_cards: list[KeyCardResponse] = Field(description="Key cards with usage stats")
    sample_decks: list[SampleDeckResponse] = Field(
        default_factory=list, description="Sample decklists from tournaments"
    )
