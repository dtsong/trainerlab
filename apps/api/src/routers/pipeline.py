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
from src.pipelines.monitor_card_reveals import (
    MonitorCardRevealsResult as MonitorCardRevealsResultInternal,
)
from src.pipelines.monitor_card_reveals import (
    check_card_reveals,
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
from src.pipelines.sync_jp_adoption_rates import (
    SyncAdoptionRatesResult as SyncAdoptionRatesResultInternal,
)
from src.pipelines.sync_jp_adoption_rates import (
    sync_adoption_rates,
)
from src.pipelines.translate_pokecabook import (
    TranslatePokecabookResult as TranslatePokecabookResultInternal,
)
from src.pipelines.translate_pokecabook import (
    translate_pokecabook_content,
)
from src.pipelines.translate_tier_lists import (
    TranslateTierListsResult as TranslateTierListsResultInternal,
)
from src.pipelines.translate_tier_lists import (
    translate_tier_lists,
)
from src.schemas.pipeline import (
    ComputeEvolutionRequest,
    ComputeEvolutionResult,
    ComputeMetaRequest,
    ComputeMetaResult,
    DiscoverRequest,
    DiscoverResult,
    MonitorCardRevealsRequest,
    MonitorCardRevealsResult,
    ProcessTournamentRequest,
    ScrapeResult,
    SyncCardsRequest,
    SyncCardsResult,
    SyncJPAdoptionRequest,
    SyncJPAdoptionResult,
    TranslatePokecabookRequest,
    TranslatePokecabookResult,
    TranslateTierListsRequest,
    TranslateTierListsResult,
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


# Translation pipelines


def _convert_translate_pokecabook_result(
    internal: TranslatePokecabookResultInternal,
) -> TranslatePokecabookResult:
    """Convert internal TranslatePokecabookResult to API schema."""
    return TranslatePokecabookResult(
        articles_fetched=internal.articles_fetched,
        articles_translated=internal.articles_translated,
        articles_skipped=internal.articles_skipped,
        tier_lists_translated=internal.tier_lists_translated,
        errors=internal.errors,
        success=internal.success,
    )


def _convert_sync_jp_adoption_result(
    internal: SyncAdoptionRatesResultInternal,
) -> SyncJPAdoptionResult:
    """Convert internal SyncAdoptionRatesResult to API schema."""
    return SyncJPAdoptionResult(
        rates_fetched=internal.rates_fetched,
        rates_created=internal.rates_created,
        rates_updated=internal.rates_updated,
        rates_skipped=internal.rates_skipped,
        errors=internal.errors,
        success=internal.success,
    )


def _convert_translate_tier_lists_result(
    internal: TranslateTierListsResultInternal,
) -> TranslateTierListsResult:
    """Convert internal TranslateTierListsResult to API schema."""
    return TranslateTierListsResult(
        pokecabook_entries=internal.pokecabook_entries,
        pokekameshi_entries=internal.pokekameshi_entries,
        translations_saved=internal.translations_saved,
        errors=internal.errors,
        success=internal.success,
    )


def _convert_monitor_card_reveals_result(
    internal: MonitorCardRevealsResultInternal,
) -> MonitorCardRevealsResult:
    """Convert internal MonitorCardRevealsResult to API schema."""
    return MonitorCardRevealsResult(
        cards_checked=internal.cards_checked,
        new_cards_found=internal.new_cards_found,
        cards_updated=internal.cards_updated,
        cards_marked_released=internal.cards_marked_released,
        errors=internal.errors,
        success=internal.success,
    )


@router.post("/translate-pokecabook", response_model=TranslatePokecabookResult)
async def translate_pokecabook_endpoint(
    request: TranslatePokecabookRequest,
) -> TranslatePokecabookResult:
    """Translate Pokecabook content.

    Called by Cloud Scheduler 3x/week (MWF) to translate Japanese
    meta content from Pokecabook.
    """
    logger.info(
        "Starting Pokecabook translation: lookback_days=%d, dry_run=%s",
        request.lookback_days,
        request.dry_run,
    )

    result = await translate_pokecabook_content(
        lookback_days=request.lookback_days,
        dry_run=request.dry_run,
    )

    logger.info(
        "Pokecabook translation complete: fetched=%d, translated=%d, errors=%d",
        result.articles_fetched,
        result.articles_translated,
        len(result.errors),
    )

    return _convert_translate_pokecabook_result(result)


@router.post("/sync-jp-adoption", response_model=SyncJPAdoptionResult)
async def sync_jp_adoption_endpoint(
    request: SyncJPAdoptionRequest,
) -> SyncJPAdoptionResult:
    """Sync JP card adoption rates.

    Called by Cloud Scheduler 3x/week (TTS) to sync card adoption
    rate data from Pokecabook.
    """
    logger.info("Starting JP adoption rate sync: dry_run=%s", request.dry_run)

    result = await sync_adoption_rates(dry_run=request.dry_run)

    logger.info(
        "JP adoption sync complete: fetched=%d, created=%d, updated=%d, errors=%d",
        result.rates_fetched,
        result.rates_created,
        result.rates_updated,
        len(result.errors),
    )

    return _convert_sync_jp_adoption_result(result)


@router.post("/translate-tier-lists", response_model=TranslateTierListsResult)
async def translate_tier_lists_endpoint(
    request: TranslateTierListsRequest,
) -> TranslateTierListsResult:
    """Translate JP tier lists.

    Called by Cloud Scheduler weekly (Sunday) to translate tier list
    data from Pokecabook and Pokekameshi.
    """
    logger.info("Starting tier list translation: dry_run=%s", request.dry_run)

    result = await translate_tier_lists(dry_run=request.dry_run)

    logger.info(
        "Tier list translation: pokecabook=%d, pokekameshi=%d, saved=%d, errors=%d",
        result.pokecabook_entries,
        result.pokekameshi_entries,
        result.translations_saved,
        len(result.errors),
    )

    return _convert_translate_tier_lists_result(result)


@router.post("/monitor-card-reveals", response_model=MonitorCardRevealsResult)
async def monitor_card_reveals_endpoint(
    request: MonitorCardRevealsRequest,
) -> MonitorCardRevealsResult:
    """Monitor JP card reveals.

    Called by Cloud Scheduler 4x/day (every 6 hours) to track new
    JP card reveals and update release status.
    """
    logger.info("Starting card reveal monitor: dry_run=%s", request.dry_run)

    result = await check_card_reveals(dry_run=request.dry_run)

    logger.info(
        "Card reveal monitor complete: checked=%d, new=%d, released=%d, errors=%d",
        result.cards_checked,
        result.new_cards_found,
        result.cards_marked_released,
        len(result.errors),
    )

    return _convert_monitor_card_reveals_result(result)
