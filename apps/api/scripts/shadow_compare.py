"""Shadow comparison: current archetype labels vs normalizer output.

Read-only script that compares existing archetype labels in the database
against what ArchetypeNormalizer.resolve() would produce today. Outputs
a JSON report to stdout.

Go/no-go thresholds for historical reprocess:
  - <5% changed   -> PROCEED (safe to reprocess)
  - 5-20% changed -> REVIEW (inspect changes before proceeding)
  - >20% changed  -> INVESTIGATE (likely regression or data issue)

Usage:
    uv run python apps/api/scripts/shadow_compare.py
    uv run python apps/api/scripts/shadow_compare.py --days 30
    uv run python apps/api/scripts/shadow_compare.py --days 90 --verbose
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

# Add the API root to sys.path so we can import src.*
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.config import get_settings  # noqa: E402
from src.models.tournament import Tournament  # noqa: E402
from src.models.tournament_placement import (  # noqa: E402
    TournamentPlacement,
)
from src.services.archetype_normalizer import (  # noqa: E402
    ArchetypeNormalizer,
)

logger = logging.getLogger(__name__)


async def run_comparison(
    days: int,
    verbose: bool,
) -> dict:
    """Run shadow comparison against the database.

    Args:
        days: Number of days to look back.
        verbose: Whether to log verbose output.

    Returns:
        Comparison report as a dict (serializable to JSON).
    """
    settings = get_settings()
    engine = create_async_engine(
        settings.effective_database_url,
        echo=False,
        pool_pre_ping=True,
    )
    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    cutoff = date.today() - timedelta(days=days)

    async with session_factory() as session:
        # Load normalizer with DB sprites
        normalizer = ArchetypeNormalizer()
        db_sprite_count = await normalizer.load_db_sprites(session)
        logger.info(
            "Loaded %d DB sprite overrides",
            db_sprite_count,
        )

        # Query JP placements from the last N days
        query = (
            select(TournamentPlacement)
            .join(Tournament)
            .where(
                Tournament.region == "JP",
                Tournament.date >= cutoff,
            )
        )
        result = await session.execute(query)
        placements = result.scalars().all()

        logger.info(
            "Found %d JP placements in last %d days",
            len(placements),
            days,
        )

    await engine.dispose()

    # Compare each placement
    total = len(placements)
    changed = 0
    unchanged = 0
    changes: list[dict] = []
    transition_counts: Counter[str] = Counter()

    for p in placements:
        sprite_urls = p.raw_archetype_sprites or []
        html_archetype = p.raw_archetype or p.archetype

        new_archetype, _, new_method = normalizer.resolve(
            sprite_urls,
            html_archetype,
            p.decklist,
        )

        old_method = p.archetype_detection_method or "unknown"

        if new_archetype != p.archetype:
            changed += 1
            transition_key = f"{old_method} -> {new_method}"
            transition_counts[transition_key] += 1
            changes.append(
                {
                    "placement_id": str(p.id),
                    "old_archetype": p.archetype,
                    "new_archetype": new_archetype,
                    "old_method": old_method,
                    "new_method": new_method,
                    "sprite_urls": sprite_urls,
                    "raw_archetype": p.raw_archetype,
                }
            )
            if verbose:
                logger.info(
                    "CHANGED: %s -> %s [%s -> %s]",
                    p.archetype,
                    new_archetype,
                    old_method,
                    new_method,
                )
        else:
            unchanged += 1

    change_pct = (changed / total * 100) if total > 0 else 0.0

    if change_pct < 5:
        recommendation = "PROCEED"
    elif change_pct <= 20:
        recommendation = "REVIEW"
    else:
        recommendation = "INVESTIGATE"

    report = {
        "days": days,
        "total": total,
        "changed_count": changed,
        "unchanged_count": unchanged,
        "change_pct": round(change_pct, 2),
        "recommendation": recommendation,
        "transitions": dict(transition_counts),
        "changes": changes,
    }
    return report


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Compare current archetype labels against ArchetypeNormalizer output."
        ),
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days to look back (default: 30)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose (DEBUG) logging",
    )
    return parser.parse_args()


async def main() -> None:
    """Run the shadow comparison and print JSON report."""
    args = parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stderr,
    )

    report = await run_comparison(
        days=args.days,
        verbose=args.verbose,
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
