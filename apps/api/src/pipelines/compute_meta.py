"""Meta snapshot computation pipeline.

Computes daily meta snapshots for all region/format/best_of combinations.
"""

import logging
from dataclasses import dataclass, field
from datetime import date
from typing import Literal
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from src.db.database import async_session_factory
from src.models import FormatConfig
from src.services.meta_service import MetaService

logger = logging.getLogger(__name__)

# Regions to compute snapshots for (None = global)
REGIONS: list[str | None] = [None, "NA", "EU", "JP", "LATAM", "OCE"]

# Formats to compute
FORMATS: list[Literal["standard", "expanded"]] = ["standard", "expanded"]

# Best-of configurations
# JP uses BO1, international uses BO3
REGION_BEST_OF: dict[str | None, list[Literal[1, 3]]] = {
    None: [3],  # Global only BO3
    "NA": [3],
    "EU": [3],
    "JP": [1],  # Japan uses BO1
    "LATAM": [3],
    "OCE": [3],
}


@dataclass
class ComputeMetaResult:
    """Result of compute_meta pipeline."""

    snapshots_computed: int = 0
    snapshots_saved: int = 0
    snapshots_skipped: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return len(self.errors) == 0


async def compute_daily_snapshots(
    snapshot_date: date | None = None,
    dry_run: bool = False,
    lookback_days: int = 90,
    regions: list[str | None] | None = None,
    formats: list[Literal["standard", "expanded"]] | None = None,
    start_date_floor: date | None = None,
) -> ComputeMetaResult:
    """Compute and save daily meta snapshots for all combinations.

    Computes enhanced meta snapshots (with diversity index, tiers, trends)
    for each region × format × best_of combination.

    Args:
        snapshot_date: Date for the snapshot. Defaults to today.
        dry_run: If True, compute but don't save to database.
        lookback_days: Days to look back for tournament data.
        regions: Override regions to compute. Defaults to all.
        formats: Override formats to compute. Defaults to all.

    Returns:
        ComputeMetaResult with stats and any errors.
    """
    if snapshot_date is None:
        snapshot_date = date.today()

    target_regions = regions if regions is not None else REGIONS
    target_formats = formats if formats is not None else FORMATS

    result = ComputeMetaResult()
    run_id = str(uuid4())
    _extra = {"pipeline": "compute-meta", "run_id": run_id}

    logger.info(
        "Starting daily meta computation: date=%s, dry_run=%s, lookback=%d",
        snapshot_date,
        dry_run,
        lookback_days,
        extra=_extra,
    )

    async with async_session_factory() as session:
        service = MetaService(session)

        for region in target_regions:
            best_of_options = REGION_BEST_OF.get(region, [3])

            # Auto-derive start_date_floor for JP
            region_floor = start_date_floor
            region_era = None
            if region == "JP" and region_floor is None:
                try:
                    floor_cutoff = date.fromordinal(
                        snapshot_date.toordinal() - lookback_days
                    )
                    fc_query = (
                        select(FormatConfig)
                        .where(
                            FormatConfig.is_current.is_(True),
                            FormatConfig.start_date >= floor_cutoff,
                            FormatConfig.start_date <= snapshot_date,
                        )
                        .order_by(FormatConfig.start_date.desc())
                        .limit(1)
                    )
                    fc_result = await session.execute(fc_query)
                    fc = fc_result.scalar_one_or_none()
                    if fc:
                        region_floor = fc.start_date
                        region_era = f"post-{fc.name}"
                        logger.info(
                            "JP floor derived from FormatConfig: %s (start=%s, era=%s)",
                            fc.name,
                            fc.start_date,
                            region_era,
                        )
                except Exception:
                    logger.warning(
                        "Failed to derive JP floor from FormatConfig",
                        exc_info=True,
                    )

            for game_format in target_formats:
                for best_of in best_of_options:
                    combo = f"{region or 'global'}/{game_format}/BO{best_of}"

                    try:
                        logger.info("Computing snapshot: %s", combo)

                        snapshot = await service.compute_enhanced_meta_snapshot(
                            snapshot_date=snapshot_date,
                            region=region,
                            game_format=game_format,
                            best_of=best_of,
                            lookback_days=lookback_days,
                            start_date_floor=region_floor,
                            era_label=region_era,
                        )

                        result.snapshots_computed += 1

                        if snapshot.sample_size == 0:
                            logger.info("Skipping empty snapshot: %s", combo)
                            result.snapshots_skipped += 1
                            continue

                        logger.info(
                            "Computed snapshot: %s (sample_size=%d, diversity=%.4f)",
                            combo,
                            snapshot.sample_size,
                            float(snapshot.diversity_index or 0),
                        )

                        if not dry_run:
                            await service.save_snapshot(snapshot)
                            result.snapshots_saved += 1
                            logger.info("Saved snapshot: %s", combo)
                        else:
                            logger.info("DRY RUN - would save snapshot: %s", combo)

                    except (SQLAlchemyError, ValueError, TypeError) as e:
                        error_msg = f"Error computing {combo}: {e}"
                        logger.error(error_msg, exc_info=True)
                        result.errors.append(error_msg)

    logger.info(
        "Meta computation complete: computed=%d, saved=%d, skipped=%d, errors=%d",
        result.snapshots_computed,
        result.snapshots_saved,
        result.snapshots_skipped,
        len(result.errors),
        extra=_extra,
    )

    # Tail step: compute JP intelligence (non-fatal)
    if not dry_run:
        try:
            from src.pipelines.compute_jp_intelligence import (
                compute_jp_intelligence,
            )

            jp_result = await compute_jp_intelligence(dry_run=False)
            logger.info(
                "JP intelligence tail step: archetypes=%d/%d, "
                "innovations=%d/%d, errors=%d",
                jp_result.new_archetypes_found,
                jp_result.new_archetypes_removed,
                jp_result.innovations_found,
                jp_result.innovations_removed,
                len(jp_result.errors),
                extra=_extra,
            )
        except Exception:
            logger.warning(
                "JP intelligence tail step failed (non-fatal)",
                exc_info=True,
                extra=_extra,
            )

    return result


async def compute_single_snapshot(
    snapshot_date: date,
    region: str | None,
    game_format: Literal["standard", "expanded"],
    best_of: Literal[1, 3],
    dry_run: bool = False,
    lookback_days: int = 90,
    start_date_floor: date | None = None,
    era_label: str | None = None,
) -> ComputeMetaResult:
    """Compute a single meta snapshot.

    Useful for recomputing specific snapshots or testing.

    Args:
        snapshot_date: Date for the snapshot.
        region: Region or None for global.
        game_format: Game format.
        best_of: Match format.
        dry_run: If True, don't save to database.
        lookback_days: Days to look back.

    Returns:
        ComputeMetaResult with stats.
    """
    result = ComputeMetaResult()
    combo = f"{region or 'global'}/{game_format}/BO{best_of}"

    logger.info(
        "Computing single snapshot: %s, date=%s, dry_run=%s",
        combo,
        snapshot_date,
        dry_run,
    )

    async with async_session_factory() as session:
        service = MetaService(session)

        try:
            snapshot = await service.compute_enhanced_meta_snapshot(
                snapshot_date=snapshot_date,
                region=region,
                game_format=game_format,
                best_of=best_of,
                lookback_days=lookback_days,
                start_date_floor=start_date_floor,
                era_label=era_label,
            )

            result.snapshots_computed = 1

            if snapshot.sample_size == 0:
                result.snapshots_skipped = 1
                logger.info("Snapshot has no data: %s", combo)
                return result

            if not dry_run:
                await service.save_snapshot(snapshot)
                result.snapshots_saved = 1
                logger.info("Saved snapshot: %s", combo)
            else:
                logger.info("DRY RUN - would save: %s", combo)

        except (SQLAlchemyError, ValueError, TypeError) as e:
            error_msg = f"Error computing {combo}: {e}"
            logger.error(error_msg, exc_info=True)
            result.errors.append(error_msg)

    return result
