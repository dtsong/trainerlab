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


# Adoption rate schemas


class JPAdoptionRateResponse(BaseModel):
    """JP card adoption rate response."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Record ID")
    card_id: str = Field(description="Card identifier")
    card_name_jp: str | None = Field(description="Japanese card name")
    card_name_en: str | None = Field(description="English card name")
    inclusion_rate: float = Field(description="Inclusion rate (0-1)")
    avg_copies: float | None = Field(description="Average copies when included")
    archetype_context: str | None = Field(description="Archetype context")
    period_start: str = Field(description="Period start date")
    period_end: str = Field(description="Period end date")
    source: str | None = Field(description="Data source")


class JPAdoptionRateListResponse(BaseModel):
    """List of JP adoption rates."""

    rates: list[JPAdoptionRateResponse] = Field(description="Adoption rate data")
    total: int = Field(description="Total count")


# Unreleased card schemas


class JPUnreleasedCardResponse(BaseModel):
    """JP unreleased card response."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Record ID")
    jp_card_id: str = Field(description="JP card identifier")
    jp_set_id: str | None = Field(description="JP set identifier")
    name_jp: str = Field(description="Japanese name")
    name_en: str | None = Field(description="English name translation")
    card_type: str | None = Field(description="Card type")
    competitive_impact: int = Field(description="Competitive impact rating (1-5)")
    affected_archetypes: list[str] | None = Field(description="Affected archetypes")
    notes: str | None = Field(description="Analysis notes")
    expected_release_set: str | None = Field(description="Expected EN release set")
    is_released: bool = Field(description="Whether released internationally")


class JPUnreleasedCardListResponse(BaseModel):
    """List of JP unreleased cards."""

    cards: list[JPUnreleasedCardResponse] = Field(description="Unreleased cards")
    total: int = Field(description="Total count")


# Admin translation schemas


class TranslatedContentResponse(BaseModel):
    """Translated content admin response."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Content ID")
    source_id: str = Field(description="Source identifier")
    source_url: str = Field(description="Source URL")
    content_type: str = Field(description="Content type")
    original_text: str = Field(description="Original Japanese text")
    translated_text: str | None = Field(description="Translated English text")
    status: str = Field(description="Translation status")
    translated_at: datetime | None = Field(description="Translation timestamp")
    uncertainties: list[str] | None = Field(description="Translation uncertainties")


class TranslatedContentListResponse(BaseModel):
    """List of translated content."""

    content: list[TranslatedContentResponse] = Field(description="Content items")
    total: int = Field(description="Total count")


class SubmitTranslationRequest(BaseModel):
    """Request to submit a URL for translation."""

    url: str = Field(description="URL to translate")
    content_type: ContentType = Field(default="article", description="Content type")
    context: str | None = Field(default=None, description="Additional context")


class UpdateTranslationRequest(BaseModel):
    """Request to update a translation."""

    translated_text: str | None = Field(default=None, description="Edited translation")
    status: TranslationStatus | None = Field(default=None, description="New status")


class GlossaryTermCreateRequest(BaseModel):
    """Request to create/update a glossary term override."""

    term_jp: str = Field(description="Japanese term")
    term_en: str = Field(description="English translation")
    context: str | None = Field(default=None, description="Usage context")


class GlossaryTermOverrideResponse(BaseModel):
    """Glossary term override response."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Record ID")
    term_jp: str = Field(description="Japanese term")
    term_en: str = Field(description="English translation")
    context: str | None = Field(description="Usage context")
    source: str | None = Field(description="Term source")
    is_active: bool = Field(description="Whether active")


class GlossaryTermOverrideListResponse(BaseModel):
    """List of glossary term overrides."""

    terms: list[GlossaryTermOverrideResponse] = Field(description="Term overrides")
    total: int = Field(description="Total count")
