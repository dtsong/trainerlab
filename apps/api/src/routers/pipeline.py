"""Pipeline endpoints for scheduled data operations.

These endpoints are called by Cloud Scheduler to run periodic data
pipelines like scraping tournaments and computing meta snapshots.
"""

import logging

from fastapi import APIRouter, Depends

from src.dependencies.scheduler_auth import verify_scheduler_auth
from src.pipelines.compute_evolution import (
    ComputeEvolutionResult as ComputeEvolutionResultInternal,
)
from src.pipelines.compute_evolution import (
    compute_evolution_intelligence,
)
from src.pipelines.compute_meta import (
    ComputeMetaResult as ComputeMetaResultInternal,
)
from src.pipelines.compute_meta import (
    compute_daily_snapshots,
)
from src.pipelines.scrape_limitless import (
    DiscoverResult as DiscoverResultInternal,
)
from src.pipelines.scrape_limitless import (
    discover_en_tournaments,
    discover_jp_tournaments,
    process_single_tournament,
)
from src.pipelines.sync_cards import sync_english_cards
from src.schemas.pipeline import (
    ComputeEvolutionRequest,
    ComputeEvolutionResult,
    ComputeMetaRequest,
    ComputeMetaResult,
    DiscoverRequest,
    DiscoverResult,
    ProcessTournamentRequest,
    ScrapeResult,
    SyncCardsRequest,
    SyncCardsResult,
)
from src.services.tournament_scrape import ScrapeResult as ScrapeResultInternal

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/pipeline",
    tags=["pipeline"],
    dependencies=[Depends(verify_scheduler_auth)],
)


def _convert_scrape_result(internal: ScrapeResultInternal) -> ScrapeResult:
    """Convert internal ScrapeResult to API schema."""
    return ScrapeResult(
        tournaments_scraped=internal.tournaments_scraped,
        tournaments_saved=internal.tournaments_saved,
        tournaments_skipped=internal.tournaments_skipped,
        placements_saved=internal.placements_saved,
        decklists_saved=internal.decklists_saved,
        errors=internal.errors,
        success=internal.success,
    )


def _convert_meta_result(internal: ComputeMetaResultInternal) -> ComputeMetaResult:
    """Convert internal ComputeMetaResult to API schema."""
    return ComputeMetaResult(
        snapshots_computed=internal.snapshots_computed,
        snapshots_saved=internal.snapshots_saved,
        snapshots_skipped=internal.snapshots_skipped,
        errors=internal.errors,
        success=internal.success,
    )


def _convert_discover_result(internal: DiscoverResultInternal) -> DiscoverResult:
    """Convert internal DiscoverResult to API schema."""
    return DiscoverResult(
        tournaments_discovered=internal.tournaments_discovered,
        tasks_enqueued=internal.tasks_enqueued,
        tournaments_skipped=internal.tournaments_skipped,
        errors=internal.errors,
        success=internal.success,
    )


@router.post("/discover-en", response_model=DiscoverResult)
async def discover_en_endpoint(
    request: DiscoverRequest,
) -> DiscoverResult:
    """Discover new EN tournaments and enqueue for processing.

    Phase 1 of the two-phase pipeline. Discovers new tournaments from
    Limitless and enqueues them as Cloud Tasks for individual processing.
    Designed to complete in <30s.
    """
    logger.info(
        "Starting EN discovery: lookback=%d, format=%s",
        request.lookback_days,
        request.game_format,
    )

    result = await discover_en_tournaments(
        lookback_days=request.lookback_days,
        game_format=request.game_format,
    )

    logger.info(
        "EN discovery complete: discovered=%d, enqueued=%d, errors=%d",
        result.tournaments_discovered,
        result.tasks_enqueued,
        len(result.errors),
    )

    return _convert_discover_result(result)


@router.post("/discover-jp", response_model=DiscoverResult)
async def discover_jp_endpoint(
    request: DiscoverRequest,
) -> DiscoverResult:
    """Discover new JP tournaments and enqueue for processing.

    Phase 1 of the two-phase pipeline for Japanese tournaments.
    """
    logger.info(
        "Starting JP discovery: lookback=%d",
        request.lookback_days,
    )

    result = await discover_jp_tournaments(
        lookback_days=request.lookback_days,
    )

    logger.info(
        "JP discovery complete: discovered=%d, enqueued=%d, errors=%d",
        result.tournaments_discovered,
        result.tasks_enqueued,
        len(result.errors),
    )

    return _convert_discover_result(result)


@router.post("/process-tournament", response_model=ScrapeResult)
async def process_tournament_endpoint(
    request: ProcessTournamentRequest,
) -> ScrapeResult:
    """Process a single tournament (called by Cloud Tasks).

    Phase 2 of the two-phase pipeline. Receives tournament metadata,
    fetches placements and decklists, and saves to database.
    """
    logger.info(
        "Processing tournament: %s (%s)",
        request.name,
        request.source_url,
    )

    result = await process_single_tournament(request.model_dump())

    logger.info(
        "Tournament processed: %s saved=%d, skipped=%d, errors=%d",
        request.name,
        result.tournaments_saved,
        result.tournaments_skipped,
        len(result.errors),
    )

    return _convert_scrape_result(result)


@router.post("/compute-meta", response_model=ComputeMetaResult)
async def compute_meta_endpoint(
    request: ComputeMetaRequest,
) -> ComputeMetaResult:
    """Compute daily meta snapshots.

    Called by Cloud Scheduler daily after scraping to compute
    meta analysis for all region/format/best_of combinations.
    """
    logger.info(
        "Starting compute meta pipeline: dry_run=%s, date=%s, lookback=%d",
        request.dry_run,
        request.snapshot_date,
        request.lookback_days,
    )

    result = await compute_daily_snapshots(
        snapshot_date=request.snapshot_date,
        dry_run=request.dry_run,
        lookback_days=request.lookback_days,
    )

    logger.info(
        "Compute meta complete: computed=%d, saved=%d, skipped=%d, errors=%d",
        result.snapshots_computed,
        result.snapshots_saved,
        result.snapshots_skipped,
        len(result.errors),
    )

    return _convert_meta_result(result)


@router.post("/sync-cards", response_model=SyncCardsResult)
async def sync_cards_endpoint(
    request: SyncCardsRequest,
) -> SyncCardsResult:
    """Sync card data from TCGdex.

    Called by Cloud Scheduler weekly to update card database
    with new sets and cards.
    """
    logger.info("Starting card sync pipeline: dry_run=%s", request.dry_run)

    result = await sync_english_cards(dry_run=request.dry_run)

    logger.info(
        "Card sync complete: sets=%d, cards=%d, updated=%d",
        result.sets_processed,
        result.cards_processed,
        result.cards_updated,
    )

    return SyncCardsResult(
        sets_synced=result.sets_processed,
        cards_synced=result.cards_processed,
        cards_updated=result.cards_updated,
        errors=result.errors,
        success=len(result.errors) == 0,
    )


def _convert_evolution_result(
    internal: ComputeEvolutionResultInternal,
) -> ComputeEvolutionResult:
    """Convert internal ComputeEvolutionResult to API schema."""
    return ComputeEvolutionResult(
        adaptations_classified=internal.adaptations_classified,
        contexts_generated=internal.contexts_generated,
        predictions_generated=internal.predictions_generated,
        articles_generated=internal.articles_generated,
        errors=internal.errors,
        success=internal.success,
    )


@router.post("/compute-evolution", response_model=ComputeEvolutionResult)
async def compute_evolution_endpoint(
    request: ComputeEvolutionRequest,
) -> ComputeEvolutionResult:
    """Run evolution intelligence pipeline.

    Called by Cloud Scheduler daily after compute-meta to classify
    adaptations, generate meta context, update predictions, and
    generate evolution articles.
    """
    logger.info(
        "Starting evolution intelligence pipeline: dry_run=%s",
        request.dry_run,
    )

    result = await compute_evolution_intelligence(
        dry_run=request.dry_run,
    )

    logger.info(
        "Evolution pipeline complete: classified=%d, contexts=%d, "
        "predictions=%d, articles=%d, errors=%d",
        result.adaptations_classified,
        result.contexts_generated,
        result.predictions_generated,
        result.articles_generated,
        len(result.errors),
    )

    return _convert_evolution_result(result)
