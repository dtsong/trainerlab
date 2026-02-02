"""Pydantic schemas for API request/response models."""

from src.schemas.card import (
    AttackSchema,
    CardResponse,
    CardSummaryResponse,
    SetSummaryResponse,
)
from src.schemas.deck import (
    CardInDeck,
    DeckCreate,
    DeckImportRequest,
    DeckImportResponse,
    DeckResponse,
    DeckStatsResponse,
    DeckSummaryResponse,
    DeckUpdate,
    EnergyCurvePoint,
    TypeBreakdown,
    UnmatchedCard,
    UserSummary,
)
from src.schemas.meta import (
    ArchetypeDetailResponse,
    ArchetypeHistoryPoint,
    ArchetypeResponse,
    CardUsageSummary,
    FormatNotes,
    KeyCardResponse,
    MetaHistoryResponse,
    MetaSnapshotResponse,
    SampleDeckResponse,
)
from src.schemas.pagination import PaginatedResponse
from src.schemas.pipeline import (
    ComputeMetaRequest,
    ComputeMetaResult,
    PipelineRequest,
    ScrapeRequest,
    ScrapeResult,
    SyncCardsRequest,
    SyncCardsResult,
)
from src.schemas.set import SetResponse
from src.schemas.tournament import BestOf, TopPlacement, TournamentSummary
from src.schemas.usage import CardUsageResponse, UsageTrendPoint
from src.schemas.user import UserPreferencesUpdate, UserResponse

__all__ = [
    "ArchetypeDetailResponse",
    "ArchetypeHistoryPoint",
    "ArchetypeResponse",
    "AttackSchema",
    "BestOf",
    "CardInDeck",
    "CardResponse",
    "CardSummaryResponse",
    "CardUsageResponse",
    "CardUsageSummary",
    "ComputeMetaRequest",
    "ComputeMetaResult",
    "DeckCreate",
    "DeckImportRequest",
    "DeckImportResponse",
    "DeckResponse",
    "DeckStatsResponse",
    "DeckSummaryResponse",
    "DeckUpdate",
    "EnergyCurvePoint",
    "FormatNotes",
    "KeyCardResponse",
    "MetaHistoryResponse",
    "MetaSnapshotResponse",
    "PaginatedResponse",
    "PipelineRequest",
    "SampleDeckResponse",
    "ScrapeRequest",
    "ScrapeResult",
    "SetResponse",
    "SetSummaryResponse",
    "SyncCardsRequest",
    "SyncCardsResult",
    "TopPlacement",
    "TournamentSummary",
    "TypeBreakdown",
    "UnmatchedCard",
    "UsageTrendPoint",
    "UserPreferencesUpdate",
    "UserResponse",
    "UserSummary",
]
