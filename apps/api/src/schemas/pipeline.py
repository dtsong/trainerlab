"""Pipeline API schemas."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class PipelineRequest(BaseModel):
    """Base request for pipeline endpoints."""

    dry_run: bool = Field(
        default=False,
        description="If true, run pipeline without saving changes",
    )


class ScrapeRequest(PipelineRequest):
    """Request for scrape pipelines."""

    lookback_days: int = Field(
        default=7,
        ge=1,
        le=365,
        description="Number of days to look back for tournaments",
    )
    game_format: Literal["standard", "expanded"] = Field(
        default="standard",
        description="Game format to scrape",
    )
    max_placements: int = Field(
        default=32,
        ge=8,
        le=128,
        description="Maximum placements to scrape per tournament",
    )
    fetch_decklists: bool = Field(
        default=True,
        description="Whether to fetch full decklists",
    )


class ComputeMetaRequest(PipelineRequest):
    """Request for compute meta pipeline."""

    snapshot_date: date | None = Field(
        default=None,
        description="Date for snapshot (defaults to today)",
    )
    lookback_days: int = Field(
        default=90,
        ge=7,
        le=365,
        description="Days to look back for tournament data",
    )


class SyncCardsRequest(PipelineRequest):
    """Request for card sync pipeline."""

    pass


class ScrapeResult(BaseModel):
    """Result from scrape pipeline."""

    tournaments_scraped: int = Field(ge=0, description="Total tournaments found")
    tournaments_saved: int = Field(ge=0, description="Tournaments saved to database")
    tournaments_skipped: int = Field(ge=0, description="Tournaments already in DB")
    placements_saved: int = Field(ge=0, description="Placements saved")
    decklists_saved: int = Field(ge=0, description="Decklists saved")
    errors: list[str] = Field(default_factory=list, description="Error messages")
    success: bool = Field(description="Whether pipeline completed without errors")


class ComputeMetaResult(BaseModel):
    """Result from compute meta pipeline."""

    snapshots_computed: int = Field(ge=0, description="Snapshots computed")
    snapshots_saved: int = Field(ge=0, description="Snapshots saved to database")
    snapshots_skipped: int = Field(ge=0, description="Snapshots skipped (no data)")
    errors: list[str] = Field(default_factory=list, description="Error messages")
    success: bool = Field(description="Whether pipeline completed without errors")


class DiscoverRequest(PipelineRequest):
    """Request for discovery pipelines."""

    lookback_days: int = Field(
        default=90,
        ge=1,
        le=365,
        description="Number of days to look back for tournaments",
    )
    game_format: Literal["standard", "expanded"] = Field(
        default="standard",
        description="Game format to discover",
    )
    auto_process: bool = Field(
        default=False,
        description="Process synchronously if Cloud Tasks not configured",
    )
    max_auto_process: int = Field(
        default=50,
        ge=1,
        le=200,
        description="Max tournaments to process synchronously",
    )


class DiscoverResult(BaseModel):
    """Result from discovery pipeline."""

    tournaments_discovered: int = Field(ge=0, description="New tournaments found")
    tasks_enqueued: int = Field(ge=0, description="Tasks enqueued to Cloud Tasks")
    tournaments_skipped: int = Field(
        ge=0, description="Tournaments skipped (Cloud Tasks not configured)"
    )
    errors: list[str] = Field(default_factory=list, description="Error messages")
    success: bool = Field(description="Whether pipeline completed without errors")


class ProcessTournamentRequest(BaseModel):
    """Payload for processing a single tournament (from Cloud Tasks)."""

    source_url: str = Field(description="Tournament source URL")
    name: str = Field(description="Tournament name")
    tournament_date: str = Field(description="Tournament date (ISO format)")
    region: str = Field(description="Tournament region")
    game_format: str = Field(default="standard", description="Game format")
    best_of: int = Field(default=3, description="Best-of format")
    participant_count: int = Field(default=0, description="Number of participants")
    is_official: bool = Field(default=False, description="Is official Limitless event")
    is_jp_city_league: bool = Field(
        default=False, description="Is JP City League event"
    )


class SyncCardsResult(BaseModel):
    """Result from card sync pipeline."""

    sets_synced: int = Field(ge=0, description="Number of sets synced")
    cards_synced: int = Field(ge=0, description="Number of cards synced")
    cards_updated: int = Field(ge=0, description="Number of cards updated")
    errors: list[str] = Field(default_factory=list, description="Error messages")
    success: bool = Field(description="Whether sync completed without errors")


class ComputeEvolutionRequest(PipelineRequest):
    """Request for compute evolution pipeline."""

    pass


class ComputeEvolutionResult(BaseModel):
    """Result from compute evolution pipeline."""

    adaptations_classified: int = Field(
        ge=0, description="Adaptations classified by Claude"
    )
    contexts_generated: int = Field(ge=0, description="Meta contexts generated")
    predictions_generated: int = Field(ge=0, description="Predictions generated")
    articles_generated: int = Field(ge=0, description="Articles generated")
    errors: list[str] = Field(default_factory=list, description="Error messages")
    success: bool = Field(description="Whether pipeline completed without errors")


# Translation pipeline schemas


class TranslatePokecabookRequest(PipelineRequest):
    """Request for Pokecabook translation pipeline."""

    lookback_days: int = Field(
        default=7,
        ge=1,
        le=90,
        description="Number of days to look back for articles",
    )


class TranslatePokecabookResult(BaseModel):
    """Result from Pokecabook translation pipeline."""

    articles_fetched: int = Field(ge=0, description="Articles fetched from Pokecabook")
    articles_translated: int = Field(ge=0, description="Articles translated")
    articles_skipped: int = Field(ge=0, description="Articles skipped")
    tier_lists_translated: int = Field(ge=0, description="Tier lists translated")
    errors: list[str] = Field(default_factory=list, description="Error messages")
    success: bool = Field(description="Whether pipeline completed without errors")


class SyncJPAdoptionRequest(PipelineRequest):
    """Request for JP adoption rate sync pipeline."""

    pass


class SyncJPAdoptionResult(BaseModel):
    """Result from JP adoption rate sync pipeline."""

    rates_fetched: int = Field(ge=0, description="Rates fetched from source")
    rates_created: int = Field(ge=0, description="New rates created")
    rates_updated: int = Field(ge=0, description="Existing rates updated")
    rates_skipped: int = Field(ge=0, description="Rates skipped")
    errors: list[str] = Field(default_factory=list, description="Error messages")
    success: bool = Field(description="Whether pipeline completed without errors")


class TranslateTierListsRequest(PipelineRequest):
    """Request for tier list translation pipeline."""

    pass


class TranslateTierListsResult(BaseModel):
    """Result from tier list translation pipeline."""

    pokecabook_entries: int = Field(ge=0, description="Entries from Pokecabook")
    pokekameshi_entries: int = Field(ge=0, description="Entries from Pokekameshi")
    translations_saved: int = Field(ge=0, description="Translations saved")
    errors: list[str] = Field(default_factory=list, description="Error messages")
    success: bool = Field(description="Whether pipeline completed without errors")


class MonitorCardRevealsRequest(PipelineRequest):
    """Request for card reveal monitoring pipeline."""

    pass


class MonitorCardRevealsResult(BaseModel):
    """Result from card reveal monitoring pipeline."""

    cards_checked: int = Field(ge=0, description="Cards checked")
    new_cards_found: int = Field(ge=0, description="New unreleased cards found")
    cards_updated: int = Field(ge=0, description="Existing cards updated")
    cards_marked_released: int = Field(ge=0, description="Cards marked as released")
    errors: list[str] = Field(default_factory=list, description="Error messages")
    success: bool = Field(description="Whether pipeline completed without errors")


class SyncCardMappingsRequest(PipelineRequest):
    """Request for JP-to-EN card ID mapping sync pipeline."""

    recent_only: bool = Field(
        default=True,
        description="Only sync recent JP sets (faster)",
    )
    lookback_sets: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of recent JP sets to sync (when recent_only=True)",
    )


class SyncCardMappingsResult(BaseModel):
    """Result from card ID mapping sync pipeline."""

    sets_processed: int = Field(ge=0, description="JP sets processed")
    mappings_found: int = Field(ge=0, description="Total mappings found")
    mappings_inserted: int = Field(ge=0, description="New mappings inserted")
    mappings_updated: int = Field(ge=0, description="Existing mappings updated")
    errors: list[str] = Field(default_factory=list, description="Error messages")
    success: bool = Field(description="Whether pipeline completed without errors")


class CleanupExportsRequest(PipelineRequest):
    """Request for export cleanup pipeline."""

    max_age_hours: int = Field(
        default=24,
        ge=1,
        le=168,
        description="Maximum age in hours for export files",
    )


class CleanupExportsResult(BaseModel):
    """Result from export cleanup pipeline."""

    files_deleted: int = Field(ge=0, description="Export files deleted")
    errors: list[str] = Field(default_factory=list, description="Error messages")
    success: bool = Field(description="Whether cleanup completed without errors")


class ComputeJPIntelligenceRequest(PipelineRequest):
    """Request for JP intelligence pipeline."""

    pass


class ComputeJPIntelligenceResult(BaseModel):
    """Result from JP intelligence pipeline."""

    new_archetypes_found: int = Field(ge=0, description="JP-only archetypes found")
    new_archetypes_removed: int = Field(
        ge=0, description="Archetypes removed (dropped below threshold)"
    )
    innovations_found: int = Field(ge=0, description="Card innovations found")
    innovations_removed: int = Field(
        ge=0, description="Innovations removed (adoption dropped)"
    )
    errors: list[str] = Field(default_factory=list, description="Error messages")
    success: bool = Field(description="Whether pipeline completed without errors")


class ReprocessArchetypesRequest(PipelineRequest):
    """Request for archetype reprocess pipeline."""

    region: str = Field(
        default="JP",
        description="Tournament region to reprocess",
    )
    batch_size: int = Field(
        default=200,
        ge=1,
        le=1000,
        description="Placements per batch",
    )
    cursor: str | None = Field(
        default=None,
        description="Pagination cursor (placement UUID)",
    )
    force: bool = Field(
        default=False,
        description="Re-run even if detection_method is populated",
    )


class ReprocessArchetypesResult(BaseModel):
    """Result from archetype reprocess pipeline."""

    processed: int = Field(ge=0, description="Placements processed")
    updated: int = Field(ge=0, description="Placements updated")
    skipped: int = Field(ge=0, description="Placements unchanged")
    errors: list[str] = Field(default_factory=list)
    next_cursor: str | None = Field(
        default=None,
        description="Next cursor (None means done)",
    )
    total_remaining: int = Field(ge=0, default=0, description="Approximate remaining")
    success: bool = Field(description="Whether pipeline succeeded")
