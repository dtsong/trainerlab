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
from src.schemas.set import SetResponse
from src.schemas.tournament import TopPlacement, TournamentSummary
from src.schemas.usage import CardUsageResponse, UsageTrendPoint

__all__ = [
    "ArchetypeDetailResponse",
    "ArchetypeHistoryPoint",
    "ArchetypeResponse",
    "AttackSchema",
    "CardInDeck",
    "CardResponse",
    "CardSummaryResponse",
    "CardUsageResponse",
    "CardUsageSummary",
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
    "SampleDeckResponse",
    "SetResponse",
    "SetSummaryResponse",
    "TopPlacement",
    "TournamentSummary",
    "TypeBreakdown",
    "UnmatchedCard",
    "UsageTrendPoint",
    "UserSummary",
]
