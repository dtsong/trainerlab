"""Pipeline endpoints for scheduled data operations.

These endpoints are called by Cloud Scheduler to run periodic data
pipelines like scraping tournaments and computing meta snapshots.
"""

import logging

from fastapi import APIRouter, Depends

from src.dependencies.scheduler_auth import verify_scheduler_auth
from src.pipelines.compute_meta import (
    ComputeMetaResult as ComputeMetaResultInternal,
)
from src.pipelines.compute_meta import (
    compute_daily_snapshots,
)
from src.pipelines.scrape_limitless import (
    scrape_en_tournaments,
    scrape_jp_tournaments,
)
from src.pipelines.sync_cards import sync_english_cards
from src.schemas.pipeline import (
    ComputeMetaRequest,
    ComputeMetaResult,
    ScrapeRequest,
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


@router.post("/scrape-en", response_model=ScrapeResult)
async def scrape_en_endpoint(
    request: ScrapeRequest,
) -> ScrapeResult:
    """Scrape English (international) tournaments from Limitless.

    Called by Cloud Scheduler daily to fetch new tournament results
    from NA, EU, LATAM, and OCE regions.
    """
    logger.info(
        "Starting EN scrape pipeline: dry_run=%s, lookback=%d, format=%s",
        request.dry_run,
        request.lookback_days,
        request.game_format,
    )

    result = await scrape_en_tournaments(
        dry_run=request.dry_run,
        lookback_days=request.lookback_days,
        game_format=request.game_format,
        max_placements=request.max_placements,
        fetch_decklists=request.fetch_decklists,
    )

    logger.info(
        "EN scrape complete: saved=%d, skipped=%d, errors=%d",
        result.tournaments_saved,
        result.tournaments_skipped,
        len(result.errors),
    )

    return _convert_scrape_result(result)


@router.post("/scrape-jp", response_model=ScrapeResult)
async def scrape_jp_endpoint(
    request: ScrapeRequest,
) -> ScrapeResult:
    """Scrape Japanese tournaments from Limitless.

    Called by Cloud Scheduler daily to fetch JP tournament results.
    JP tournaments use BO1 format with different tie rules.
    """
    logger.info(
        "Starting JP scrape pipeline: dry_run=%s, lookback=%d, format=%s",
        request.dry_run,
        request.lookback_days,
        request.game_format,
    )

    result = await scrape_jp_tournaments(
        dry_run=request.dry_run,
        lookback_days=request.lookback_days,
        game_format=request.game_format,
        max_placements=request.max_placements,
        fetch_decklists=request.fetch_decklists,
    )

    logger.info(
        "JP scrape complete: saved=%d, skipped=%d, errors=%d",
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
