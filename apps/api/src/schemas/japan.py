"""Japan intelligence Pydantic schemas."""

from datetime import date as date_type
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

AdoptionTrend = Literal["rising", "stable", "falling"]
PredictionOutcome = Literal["correct", "partial", "incorrect"]
PredictionConfidence = Literal["high", "medium", "low"]


class JPCardInnovationResponse(BaseModel):
    """JP card innovation tracker response."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Innovation ID (UUID)")
    card_id: str = Field(description="Card ID")
    card_name: str = Field(description="Card name (EN)")
    card_name_jp: str | None = Field(default=None, description="Card name (JP)")
    set_code: str = Field(description="Set code")
    set_release_jp: date_type | None = Field(
        default=None, description="JP release date"
    )
    set_release_en: date_type | None = Field(
        default=None, description="EN release date"
    )
    is_legal_en: bool = Field(description="Whether card is legal in EN")
    adoption_rate: float = Field(ge=0.0, le=1.0, description="JP adoption rate")
    adoption_trend: AdoptionTrend | None = Field(
        default=None, description="Adoption trend"
    )
    archetypes_using: list[str] | None = Field(
        default=None, description="Archetypes using this card"
    )
    competitive_impact_rating: int = Field(
        ge=1, le=5, description="Impact rating (1-5)"
    )
    sample_size: int = Field(description="Sample size for adoption calculation")


class JPCardInnovationDetailResponse(JPCardInnovationResponse):
    """Full JP card innovation with analysis."""

    impact_analysis: str | None = Field(
        default=None, description="Impact analysis (Research Pass)"
    )


class JPCardInnovationListResponse(BaseModel):
    """List of JP card innovations."""

    model_config = ConfigDict(from_attributes=True)

    items: list[JPCardInnovationResponse] = Field(description="Card innovations")
    total: int = Field(description="Total count")


class CityLeagueResult(BaseModel):
    """City League tournament result."""

    model_config = ConfigDict(from_attributes=True)

    tournament: str = Field(description="Tournament name")
    date: date_type = Field(description="Tournament date")
    placements: list[int] = Field(description="Placements achieved")


class JPNewArchetypeResponse(BaseModel):
    """JP-only archetype response."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Archetype ID (UUID)")
    archetype_id: str = Field(description="Archetype slug ID")
    name: str = Field(description="Archetype name (EN)")
    name_jp: str | None = Field(default=None, description="Archetype name (JP)")
    key_cards: list[str] | None = Field(
        default=None, description="Key card IDs defining this archetype"
    )
    enabled_by_set: str | None = Field(
        default=None, description="Set that enabled this archetype"
    )
    jp_meta_share: float = Field(ge=0.0, le=1.0, description="JP meta share")
    jp_trend: AdoptionTrend | None = Field(default=None, description="Meta trend")
    city_league_results: list[CityLeagueResult] | None = Field(
        default=None, description="City League results"
    )
    estimated_en_legal_date: date_type | None = Field(
        default=None, description="Estimated EN legal date"
    )
    analysis: str | None = Field(default=None, description="Analysis (Research Pass)")


class JPNewArchetypeListResponse(BaseModel):
    """List of JP-only archetypes."""

    model_config = ConfigDict(from_attributes=True)

    items: list[JPNewArchetypeResponse] = Field(description="New archetypes")
    total: int = Field(description="Total count")


class MetaBreakdown(BaseModel):
    """Simple meta breakdown."""

    model_config = ConfigDict(from_attributes=True)

    archetype: str = Field(description="Archetype name")
    share: float = Field(ge=0.0, le=1.0, description="Meta share")


class JPSetImpactResponse(BaseModel):
    """JP set impact response."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Impact ID (UUID)")
    set_code: str = Field(description="Set code")
    set_name: str = Field(description="Set name")
    jp_release_date: date_type = Field(description="JP release date")
    en_release_date: date_type | None = Field(
        default=None, description="EN release date"
    )
    jp_meta_before: list[MetaBreakdown] | None = Field(
        default=None, description="JP meta before set release"
    )
    jp_meta_after: list[MetaBreakdown] | None = Field(
        default=None, description="JP meta after set release"
    )
    key_innovations: list[str] | None = Field(
        default=None, description="Key innovative cards from set"
    )
    new_archetypes: list[str] | None = Field(
        default=None, description="New archetypes enabled by set"
    )
    analysis: str | None = Field(default=None, description="Impact analysis")


class JPSetImpactListResponse(BaseModel):
    """List of JP set impacts."""

    model_config = ConfigDict(from_attributes=True)

    items: list[JPSetImpactResponse] = Field(description="Set impacts")
    total: int = Field(description="Total count")


class PredictionResponse(BaseModel):
    """Prediction with outcome."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Prediction ID (UUID)")
    prediction_text: str = Field(description="Prediction text")
    target_event: str = Field(description="Target event")
    target_date: datetime | None = Field(default=None, description="Target date")
    created_at: datetime = Field(description="When prediction was made")
    resolved_at: datetime | None = Field(default=None, description="When resolved")
    outcome: PredictionOutcome | None = Field(
        default=None, description="Prediction outcome"
    )
    confidence: PredictionConfidence | None = Field(
        default=None, description="Confidence level"
    )
    category: str | None = Field(default=None, description="Prediction category")
    reasoning: str | None = Field(default=None, description="Reasoning")
    outcome_notes: str | None = Field(default=None, description="Outcome explanation")


class PredictionListResponse(BaseModel):
    """List of predictions with accuracy stats."""

    model_config = ConfigDict(from_attributes=True)

    items: list[PredictionResponse] = Field(description="Predictions")
    total: int = Field(description="Total predictions")
    resolved: int = Field(description="Resolved predictions")
    correct: int = Field(description="Correct predictions")
    partial: int = Field(description="Partially correct predictions")
    incorrect: int = Field(description="Incorrect predictions")
    accuracy_rate: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Overall accuracy (correct/resolved)"
    )


class CardCountDataPoint(BaseModel):
    """A single data point in card count evolution."""

    model_config = ConfigDict(from_attributes=True)

    snapshot_date: date_type = Field(description="Week bucket date")
    avg_copies: float = Field(ge=0.0, description="Average copies in decks")
    inclusion_rate: float = Field(
        ge=0.0, le=1.0, description="Fraction of decks including this card"
    )
    sample_size: int = Field(ge=0, description="Number of decks in sample")


class CardCountEvolution(BaseModel):
    """Card count evolution for a single card."""

    model_config = ConfigDict(from_attributes=True)

    card_id: str = Field(description="Card ID")
    card_name: str = Field(description="Card name")
    data_points: list[CardCountDataPoint] = Field(
        default_factory=list, description="Data points over time"
    )
    total_change: float = Field(
        description="Absolute change in avg copies from first to last"
    )
    current_avg: float = Field(ge=0.0, description="Most recent avg copies")


class CardCountEvolutionResponse(BaseModel):
    """Card count evolution response for an archetype."""

    model_config = ConfigDict(from_attributes=True)

    archetype: str = Field(description="Archetype name")
    cards: list[CardCountEvolution] = Field(
        default_factory=list, description="Card evolution data"
    )
    tournaments_analyzed: int = Field(
        ge=0, description="Number of tournaments analyzed"
    )


class JPContentItem(BaseModel):
    """Translated JP content item."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Content ID (UUID)")
    source_url: str = Field(description="Original source URL")
    content_type: str = Field(description="Content type (article, tier_list)")
    title_en: str | None = Field(default=None, description="English title")
    title_jp: str | None = Field(default=None, description="Japanese title")
    translated_text: str | None = Field(
        default=None, description="Translated content (excerpt)"
    )
    published_date: date_type | None = Field(
        default=None, description="Publication date"
    )
    source_name: str | None = Field(default=None, description="Source name")
    tags: list[str] | None = Field(default=None, description="Content tags")
    archetype_refs: list[str] | None = Field(
        default=None, description="Referenced archetypes"
    )
    era_label: str | None = Field(default=None, description="Era label")
    review_status: str = Field(default="auto_approved", description="Review status")
    translated_at: datetime | None = Field(
        default=None, description="Translation timestamp"
    )


class JPContentListResponse(BaseModel):
    """List of translated JP content."""

    model_config = ConfigDict(from_attributes=True)

    items: list[JPContentItem] = Field(description="Content items")
    total: int = Field(description="Total count")
