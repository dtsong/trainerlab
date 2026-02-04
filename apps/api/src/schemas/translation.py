"""Translation service Pydantic schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ContentType = Literal[
    "article",
    "tournament_result",
    "tier_list",
    "deck_list",
    "meta_report",
    "card_text",
]

TranslationStatus = Literal["pending", "completed", "failed"]
TranslationLayer = Literal["glossary", "template", "claude"]
Confidence = Literal["high", "medium", "low"]


class TranslationRequest(BaseModel):
    """Request to translate text."""

    text: str = Field(description="Japanese text to translate")
    content_type: ContentType = Field(description="Content type being translated")
    context: str | None = Field(default=None, description="Additional context")


class TranslationResponse(BaseModel):
    """Response from translation."""

    model_config = ConfigDict(from_attributes=True)

    original_text: str = Field(description="Original Japanese text")
    translated_text: str = Field(description="Translated English text")
    layer_used: TranslationLayer = Field(description="Layer that produced result")
    confidence: Confidence = Field(description="Translation confidence")
    glossary_terms_used: list[str] = Field(
        default_factory=list, description="Glossary terms applied"
    )
    uncertainties: list[str] = Field(
        default_factory=list, description="Terms with uncertain translations"
    )


class ArticleTranslationRequest(BaseModel):
    """Request to translate and store an article."""

    source_id: str = Field(description="Unique identifier at source")
    source_url: str = Field(description="URL of source article")
    content_type: ContentType = Field(default="article")
    original_text: str = Field(description="Japanese article text")
    context: str | None = Field(default=None, description="Additional context")


class ArticleTranslationResponse(BaseModel):
    """Response from article translation."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Translated content ID")
    source_id: str = Field(description="Source identifier")
    source_url: str = Field(description="Source URL")
    original_text: str = Field(description="Original text")
    translated_text: str | None = Field(description="Translated text")
    status: TranslationStatus = Field(description="Translation status")
    translated_at: datetime | None = Field(description="When translation completed")
    uncertainties: list[str] = Field(default_factory=list)


class BatchTranslationItem(BaseModel):
    """Single item in a batch translation request."""

    id: str = Field(description="Client-provided ID for tracking")
    text: str = Field(description="Japanese text to translate")
    content_type: ContentType = Field(default="article")
    context: str | None = Field(default=None)


class BatchTranslationResult(BaseModel):
    """Result for a single batch item."""

    id: str = Field(description="Client-provided ID")
    translated_text: str = Field(description="Translated text")
    layer_used: TranslationLayer = Field(description="Layer that produced result")
    confidence: Confidence = Field(description="Translation confidence")


class BatchTranslationResponse(BaseModel):
    """Response from batch translation."""

    results: list[BatchTranslationResult] = Field(description="Translation results")
    total: int = Field(description="Total items processed")
    layer_breakdown: dict[str, int] = Field(
        default_factory=dict,
        description="Count of items translated by each layer",
    )


class TournamentStandingRow(BaseModel):
    """Parsed tournament standing row."""

    placement: int = Field(description="Final placement (1st, 2nd, etc.)")
    deck_name_jp: str = Field(description="Japanese deck name")
    deck_name_en: str = Field(description="English deck name")
    record: str | None = Field(default=None, description="Win-loss record")
    player_name: str | None = Field(default=None, description="Player name")


class TournamentStandingsTranslation(BaseModel):
    """Translated tournament standings."""

    model_config = ConfigDict(from_attributes=True)

    event_name_jp: str | None = Field(default=None)
    event_name_en: str | None = Field(default=None)
    standings: list[TournamentStandingRow] = Field(default_factory=list)
    participant_count: int | None = Field(default=None)
    date: str | None = Field(default=None)


class GlossaryTermResponse(BaseModel):
    """A glossary term with all its info."""

    model_config = ConfigDict(from_attributes=True)

    jp: str = Field(description="Japanese term")
    romaji: str = Field(description="Romanized pronunciation")
    en: str = Field(description="English translation")
    context: str = Field(description="Usage context")
    category: str = Field(description="Term category")


class GlossaryResponse(BaseModel):
    """Full glossary response."""

    terms: list[GlossaryTermResponse] = Field(description="All glossary terms")
    total: int = Field(description="Total term count")
    by_category: dict[str, int] = Field(description="Count by category")
