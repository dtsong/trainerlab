"""Evolution API Pydantic schemas."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

AdaptationType = Literal["tech", "consistency", "engine", "removal"]
AdaptationSource = Literal["diff", "claude", "manual"]
ArticleStatus = Literal["draft", "review", "published", "archived"]
PredictedTier = Literal["S", "A", "B", "C", "Rogue"]


class AdaptationResponse(BaseModel):
    """Single adaptation in a snapshot."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Adaptation ID")
    type: AdaptationType = Field(
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
        default=None, ge=0.0, le=1.0, description="Classification confidence (0-1)"
    )
    source: AdaptationSource | None = Field(
        default=None,
        description="Classification source (diff, claude, manual)",
    )


class EvolutionSnapshotResponse(BaseModel):
    """Evolution snapshot for a single tournament."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Snapshot ID")
    archetype: str = Field(min_length=1, description="Archetype name")
    tournament_id: UUID = Field(description="Tournament ID")
    meta_share: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Meta share at tournament (0-1)"
    )
    top_cut_conversion: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Top cut conversion rate (0-1)"
    )
    best_placement: int | None = Field(
        default=None, ge=1, description="Best placement achieved"
    )
    deck_count: int = Field(ge=0, description="Number of decks in sample")
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
    archetype_id: str = Field(min_length=1, description="Archetype name")
    target_tournament_id: UUID = Field(description="Target tournament ID")
    predicted_meta_share: dict | None = Field(
        default=None, description="Predicted meta share range {low, mid, high}"
    )
    predicted_day2_rate: dict | None = Field(
        default=None, description="Predicted day 2 rate range {low, mid, high}"
    )
    predicted_tier: PredictedTier | None = Field(
        default=None, description="Predicted tier (S, A, B, C, Rogue)"
    )
    likely_adaptations: list[dict] | None = Field(
        default=None, description="Expected adaptations"
    )
    confidence: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Prediction confidence (0-1)"
    )
    methodology: str | None = Field(default=None, description="Prediction methodology")
    actual_meta_share: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Actual meta share (0-1, backfilled)"
    )
    accuracy_score: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Accuracy score (0-1, backfilled)"
    )
    created_at: datetime | None = Field(
        default=None, description="Prediction creation time"
    )


class EvolutionArticleListItem(BaseModel):
    """Summary of an evolution article for list endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Article ID")
    archetype_id: str = Field(min_length=1, description="Archetype name")
    slug: str = Field(min_length=1, description="URL slug")
    title: str = Field(min_length=1, description="Article title")
    excerpt: str | None = Field(default=None, description="Article excerpt")
    status: ArticleStatus = Field(
        description="Article status (draft, review, published, archived)"
    )
    is_premium: bool = Field(default=False, description="Whether article is premium")
    published_at: datetime | None = Field(
        default=None, description="Publication timestamp"
    )


class EvolutionArticleResponse(BaseModel):
    """Full evolution article response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Article ID")
    archetype_id: str = Field(min_length=1, description="Archetype name")
    slug: str = Field(min_length=1, description="URL slug")
    title: str = Field(min_length=1, description="Article title")
    excerpt: str | None = Field(default=None, description="Article excerpt")
    introduction: str | None = Field(default=None, description="Article introduction")
    conclusion: str | None = Field(default=None, description="Article conclusion")
    status: ArticleStatus = Field(
        description="Article status (draft, review, published, archived)"
    )
    is_premium: bool = Field(default=False, description="Whether article is premium")
    published_at: datetime | None = Field(
        default=None, description="Publication timestamp"
    )
    view_count: int = Field(default=0, ge=0, description="View count")
    share_count: int = Field(default=0, ge=0, description="Share count")
    snapshots: list[EvolutionSnapshotResponse] = Field(
        default_factory=list, description="Linked snapshots"
    )


class PredictionAccuracyResponse(BaseModel):
    """Prediction accuracy tracking summary."""

    model_config = ConfigDict(from_attributes=True)

    total_predictions: int = Field(ge=0, description="Total predictions made")
    scored_predictions: int = Field(
        ge=0, description="Predictions with accuracy scores"
    )
    average_accuracy: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Average accuracy score (0-1)"
    )
    predictions: list[PredictionResponse] = Field(
        default_factory=list, description="Recent scored predictions"
    )
