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


class TrendInfo(BaseModel):
    """Trend information for an archetype."""

    model_config = ConfigDict(from_attributes=True)

    change: float = Field(
        ge=-1.0, le=1.0, description="Week-over-week change in share (-1.0 to 1.0)"
    )
    direction: Literal["up", "down", "stable"] = Field(
        description="Trend direction based on change"
    )
    previous_share: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Previous week's share"
    )


class DivergentArchetype(BaseModel):
    """Detailed divergence info for a single archetype between JP and EN meta."""

    model_config = ConfigDict(from_attributes=True)

    archetype: str = Field(description="Archetype name")
    jp_share: float = Field(ge=0.0, le=1.0, description="Meta share in JP")
    en_share: float = Field(ge=0.0, le=1.0, description="Meta share in EN")
    diff: float = Field(ge=-1.0, le=1.0, description="Difference (jp_share - en_share)")


class JPSignals(BaseModel):
    """JP vs EN meta divergence signals."""

    model_config = ConfigDict(from_attributes=True)

    rising: list[str] = Field(
        default_factory=list,
        description="Archetypes with higher share in JP than EN (>5% diff)",
    )
    falling: list[str] = Field(
        default_factory=list,
        description="Archetypes with lower share in JP than EN (>5% diff)",
    )
    divergent: list[DivergentArchetype] = Field(
        default_factory=list,
        description="Detailed divergence info for each divergent archetype",
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
    # Enhanced meta fields
    diversity_index: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Simpson's diversity index (0-1, higher = more diverse meta)",
    )
    tier_assignments: dict[str, str] | None = Field(
        default=None,
        description="Archetype tier mapping: {archetype: tier} (S/A/B/C/Rogue)",
    )
    jp_signals: JPSignals | None = Field(
        default=None, description="JP vs EN meta divergence signals"
    )
    trends: dict[str, TrendInfo] | None = Field(
        default=None, description="Week-over-week trends per archetype"
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


class MatchupResponse(BaseModel):
    """Matchup data between two archetypes."""

    model_config = ConfigDict(from_attributes=True)

    opponent: str = Field(description="Opponent archetype name")
    win_rate: float = Field(
        ge=0.0, le=1.0, description="Win rate against opponent (0.0-1.0)"
    )
    sample_size: int = Field(ge=0, description="Number of games in sample")
    confidence: Literal["high", "medium", "low"] = Field(
        description="Confidence level based on sample size"
    )


class MatchupSpreadResponse(BaseModel):
    """Full matchup spread for an archetype."""

    model_config = ConfigDict(from_attributes=True)

    archetype: str = Field(description="Subject archetype name")
    matchups: list[MatchupResponse] = Field(
        description="List of matchups against other archetypes"
    )
    overall_win_rate: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Overall win rate across all matchups"
    )
    total_games: int = Field(ge=0, description="Total games in sample")


class ConfidenceIndicator(BaseModel):
    """Data quality confidence indicator."""

    model_config = ConfigDict(from_attributes=True)

    sample_size: int = Field(ge=0, description="Number of placements")
    data_freshness_days: int = Field(ge=0, description="Days since snapshot")
    confidence: Literal["high", "medium", "low"] = Field(description="Confidence level")


class ArchetypeComparison(BaseModel):
    """Single archetype comparison between two regions."""

    model_config = ConfigDict(from_attributes=True)

    archetype: str = Field(description="Archetype name")
    region_a_share: float = Field(ge=0.0, le=1.0, description="Share in region A")
    region_b_share: float = Field(ge=0.0, le=1.0, description="Share in region B")
    divergence: float = Field(description="Percentage point difference (A - B)")
    region_a_tier: str | None = Field(default=None, description="Tier in region A")
    region_b_tier: str | None = Field(default=None, description="Tier in region B")
    sprite_urls: list[str] = Field(
        default_factory=list, description="Sprite image URLs"
    )


class LagAnalysis(BaseModel):
    """Lag-adjusted comparison (JP from N days ago vs EN now)."""

    model_config = ConfigDict(from_attributes=True)

    lag_days: int = Field(ge=0, description="Days of lag applied")
    jp_snapshot_date: date = Field(description="JP snapshot date (lagged)")
    en_snapshot_date: date = Field(description="EN snapshot date (current)")
    lagged_comparisons: list[ArchetypeComparison] = Field(
        description="Comparisons using lagged JP data"
    )


class MetaComparisonResponse(BaseModel):
    """Full meta comparison between two regions."""

    model_config = ConfigDict(from_attributes=True)

    region_a: str = Field(description="First region")
    region_b: str = Field(description="Second region (Global)")
    region_a_snapshot_date: date = Field(description="Snapshot date for region A")
    region_b_snapshot_date: date = Field(description="Snapshot date for region B")
    comparisons: list[ArchetypeComparison] = Field(description="Archetype comparisons")
    region_a_confidence: ConfidenceIndicator = Field(
        description="Region A data quality"
    )
    region_b_confidence: ConfidenceIndicator = Field(
        description="Region B data quality"
    )
    lag_analysis: LagAnalysis | None = Field(
        default=None, description="Optional lag-adjusted analysis"
    )


class FormatForecastEntry(BaseModel):
    """Single archetype in format forecast."""

    model_config = ConfigDict(from_attributes=True)

    archetype: str = Field(description="Archetype name")
    jp_share: float = Field(ge=0.0, le=1.0, description="JP meta share")
    en_share: float = Field(ge=0.0, le=1.0, description="Global meta share")
    divergence: float = Field(description="PP difference (jp_share - en_share)")
    tier: str | None = Field(default=None, description="JP tier")
    trend_direction: Literal["up", "down", "stable"] | None = Field(
        default=None, description="JP trend direction"
    )
    sprite_urls: list[str] = Field(
        default_factory=list, description="Sprite image URLs"
    )
    confidence: Literal["high", "medium", "low"] = Field(description="Data confidence")


class FormatForecastResponse(BaseModel):
    """Format forecast showing JP archetypes to watch."""

    model_config = ConfigDict(from_attributes=True)

    forecast_archetypes: list[FormatForecastEntry] = Field(
        description="Archetypes to watch from JP"
    )
    jp_snapshot_date: date = Field(description="JP snapshot date")
    en_snapshot_date: date = Field(description="Global snapshot date")
    jp_sample_size: int = Field(ge=0, description="JP placement count")
    en_sample_size: int = Field(ge=0, description="Global placement count")
