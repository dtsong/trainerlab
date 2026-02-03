"""Evolution API Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AdaptationResponse(BaseModel):
    """Single adaptation in a snapshot."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Adaptation ID")
    type: str = Field(
        description="Adaptation type (tech, consistency, engine, removal)"
    )
    description: str | None = Field(
        default=None, description="Human-readable description"
    )
    cards_added: list[dict] | None = Field(
        default=None, description="Cards added in this adaptation"
    )
    cards_removed: list[dict] | None = Field(
        default=None, description="Cards removed in this adaptation"
    )
    target_archetype: str | None = Field(
        default=None, description="Target archetype if tech choice"
    )
    confidence: float | None = Field(
        default=None, description="Classification confidence"
    )
    source: str | None = Field(
        default=None,
        description="Classification source (diff, claude)",
    )


class EvolutionSnapshotResponse(BaseModel):
    """Evolution snapshot for a single tournament."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Snapshot ID")
    archetype: str = Field(description="Archetype name")
    tournament_id: UUID = Field(description="Tournament ID")
    meta_share: float | None = Field(
        default=None, description="Meta share at tournament"
    )
    top_cut_conversion: float | None = Field(
        default=None, description="Top cut conversion rate"
    )
    best_placement: int | None = Field(
        default=None, description="Best placement achieved"
    )
    deck_count: int = Field(description="Number of decks in sample")
    consensus_list: list[dict] | None = Field(
        default=None, description="Consensus decklist"
    )
    meta_context: str | None = Field(
        default=None, description="AI-generated meta context"
    )
    adaptations: list[AdaptationResponse] = Field(
        default_factory=list, description="Adaptations detected"
    )
    created_at: datetime | None = Field(
        default=None, description="Snapshot creation time"
    )


class EvolutionTimelineResponse(BaseModel):
    """Timeline of evolution snapshots for an archetype."""

    model_config = ConfigDict(from_attributes=True)

    archetype: str = Field(description="Archetype name")
    snapshots: list[EvolutionSnapshotResponse] = Field(
        description="Snapshots ordered by tournament date (most recent first)"
    )


class PredictionResponse(BaseModel):
    """Archetype prediction for a tournament."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Prediction ID")
    archetype_id: str = Field(description="Archetype name")
    target_tournament_id: UUID = Field(description="Target tournament ID")
    predicted_meta_share: dict | None = Field(
        default=None, description="Predicted meta share range {low, mid, high}"
    )
    predicted_day2_rate: dict | None = Field(
        default=None, description="Predicted day 2 rate range {low, mid, high}"
    )
    predicted_tier: str | None = Field(
        default=None, description="Predicted tier (S, A, B, C, Rogue)"
    )
    likely_adaptations: list[dict] | None = Field(
        default=None, description="Expected adaptations"
    )
    confidence: float | None = Field(default=None, description="Prediction confidence")
    methodology: str | None = Field(default=None, description="Prediction methodology")
    actual_meta_share: float | None = Field(
        default=None, description="Actual meta share (backfilled post-event)"
    )
    accuracy_score: float | None = Field(
        default=None, description="Accuracy score (0-1, backfilled post-event)"
    )
    created_at: datetime | None = Field(
        default=None, description="Prediction creation time"
    )


class EvolutionArticleListItem(BaseModel):
    """Summary of an evolution article for list endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Article ID")
    archetype_id: str = Field(description="Archetype name")
    slug: str = Field(description="URL slug")
    title: str = Field(description="Article title")
    excerpt: str | None = Field(default=None, description="Article excerpt")
    status: str = Field(description="Article status (draft, review, published)")
    is_premium: bool = Field(default=False, description="Whether article is premium")
    published_at: datetime | None = Field(
        default=None, description="Publication timestamp"
    )


class EvolutionArticleResponse(BaseModel):
    """Full evolution article response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Article ID")
    archetype_id: str = Field(description="Archetype name")
    slug: str = Field(description="URL slug")
    title: str = Field(description="Article title")
    excerpt: str | None = Field(default=None, description="Article excerpt")
    introduction: str | None = Field(default=None, description="Article introduction")
    conclusion: str | None = Field(default=None, description="Article conclusion")
    status: str = Field(description="Article status")
    is_premium: bool = Field(default=False, description="Whether article is premium")
    published_at: datetime | None = Field(
        default=None, description="Publication timestamp"
    )
    view_count: int = Field(default=0, description="View count")
    share_count: int = Field(default=0, description="Share count")
    snapshots: list[EvolutionSnapshotResponse] = Field(
        default_factory=list, description="Linked snapshots"
    )


class PredictionAccuracyResponse(BaseModel):
    """Prediction accuracy tracking summary."""

    model_config = ConfigDict(from_attributes=True)

    total_predictions: int = Field(description="Total predictions made")
    scored_predictions: int = Field(description="Predictions with accuracy scores")
    average_accuracy: float | None = Field(
        default=None, description="Average accuracy score"
    )
    predictions: list[PredictionResponse] = Field(
        default_factory=list, description="Recent scored predictions"
    )
