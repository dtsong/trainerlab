"""Validation gate for JP archetype pipeline.

Runs the pipeline against live Limitless data and reports accuracy.
Pass criteria: >95% sprite-based resolution, zero Cinderace
misidentifications.

Usage:
    uv run python apps/api/scripts/validate_jp_pipeline.py
    uv run python apps/api/scripts/validate_jp_pipeline.py --tournaments 5 --verbose
    uv run python apps/api/scripts/validate_jp_pipeline.py --output json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

# Add the API root to sys.path so we can import src.*
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.clients.limitless import LimitlessClient  # noqa: E402
from src.services.archetype_normalizer import (  # noqa: E402
    ArchetypeNormalizer,
    DetectionMethod,
)

logger = logging.getLogger(__name__)

PASS_THRESHOLD = 0.95
SPRITE_METHODS: set[DetectionMethod] = {
    "sprite_lookup",
    "auto_derive",
}


@dataclass
class PlacementResult:
    """Result of running a single placement through the normalizer."""

    tournament_name: str
    placement: int
    player_name: str | None
    raw_archetype: str
    resolved_archetype: str
    detection_method: DetectionMethod
    sprite_urls: list[str] = field(default_factory=list)


@dataclass
class ValidationResult:
    """Aggregated validation results across all tournaments."""

    total_placements: int = 0
    total_tournaments: int = 0
    method_counts: Counter[str] = field(default_factory=Counter)
    text_label_results: list[PlacementResult] = field(default_factory=list)
    rogue_results: list[PlacementResult] = field(default_factory=list)
    unknown_results: list[PlacementResult] = field(default_factory=list)
    cinderace_text_results: list[PlacementResult] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def sprite_count(self) -> int:
        """Count of placements resolved via sprite methods."""
        return sum(self.method_counts[m] for m in SPRITE_METHODS)

    @property
    def accuracy(self) -> float:
        """Percentage resolved via sprite-based methods."""
        if self.total_placements == 0:
            return 0.0
        return self.sprite_count / self.total_placements

    @property
    def passed(self) -> bool:
        """Whether the validation passes all criteria."""
        return self.accuracy >= PASS_THRESHOLD and len(self.cinderace_text_results) == 0


async def validate_pipeline(
    max_tournaments: int,
    lookback_days: int,
    verbose: bool,
) -> ValidationResult:
    """Run validation against live Limitless data.

    Args:
        max_tournaments: Maximum tournaments to process.
        lookback_days: Lookback window for tournament listings.
        verbose: Whether to log verbose output.

    Returns:
        Aggregated validation results.
    """
    result = ValidationResult()
    normalizer = ArchetypeNormalizer()

    async with LimitlessClient() as client:
        logger.info(
            "Fetching JP City League listings (lookback=%d days)...",
            lookback_days,
        )
        tournaments = await client.fetch_jp_city_league_listings(
            lookback_days=lookback_days,
        )

        if not tournaments:
            result.errors.append("No tournaments found within lookback window")
            return result

        logger.info(
            "Found %d tournaments, processing up to %d",
            len(tournaments),
            max_tournaments,
        )

        for tournament in tournaments[:max_tournaments]:
            logger.info(
                "Processing: %s (%s)",
                tournament.name,
                tournament.source_url,
            )

            try:
                placements = await client.fetch_jp_city_league_placements(
                    tournament.source_url,
                    max_placements=32,
                )
            except Exception as exc:
                msg = f"Error fetching placements for {tournament.name}: {exc}"
                logger.warning(msg)
                result.errors.append(msg)
                continue

            if not placements:
                logger.warning(
                    "No placements found for %s",
                    tournament.name,
                )
                continue

            result.total_tournaments += 1

            for p in placements:
                archetype, raw, method = normalizer.resolve(
                    sprite_urls=p.sprite_urls,
                    html_archetype=p.archetype,
                    decklist=None,
                )

                pr = PlacementResult(
                    tournament_name=tournament.name,
                    placement=p.placement,
                    player_name=p.player_name,
                    raw_archetype=raw,
                    resolved_archetype=archetype,
                    detection_method=method,
                    sprite_urls=p.sprite_urls,
                )

                result.total_placements += 1
                result.method_counts[method] += 1

                if method == "text_label":
                    result.text_label_results.append(pr)

                lower = archetype.lower()
                if lower in ("rogue", "unknown"):
                    if lower == "unknown":
                        result.unknown_results.append(pr)
                    else:
                        result.rogue_results.append(pr)

                if method == "text_label" and "cinderace" in lower:
                    result.cinderace_text_results.append(pr)

                if verbose:
                    logger.debug(
                        "  #%d %s -> %s [%s]",
                        p.placement,
                        raw,
                        archetype,
                        method,
                    )

    return result


def print_table(result: ValidationResult) -> None:
    """Print validation results as a formatted table."""
    print("\n" + "=" * 60)
    print("JP ARCHETYPE PIPELINE VALIDATION REPORT")
    print("=" * 60)

    print(f"\nTournaments processed: {result.total_tournaments}")
    print(f"Total placements:     {result.total_placements}")

    print("\n--- Detection Method Breakdown ---")
    print(f"{'Method':<20} {'Count':>6} {'Pct':>7}")
    print("-" * 35)
    for method in [
        "sprite_lookup",
        "auto_derive",
        "signature_card",
        "text_label",
    ]:
        count = result.method_counts[method]
        total = result.total_placements
        pct = f"{count / total * 100:.1f}%" if total > 0 else "N/A"
        print(f"{method:<20} {count:>6} {pct:>7}")

    sprite_pct = (
        f"{result.accuracy * 100:.1f}%" if result.total_placements > 0 else "N/A"
    )
    print(f"\nSprite-based accuracy: {sprite_pct}")

    if result.text_label_results:
        print(f"\n--- text_label Fallbacks ({len(result.text_label_results)}) ---")
        for pr in result.text_label_results[:20]:
            sprites = ", ".join(pr.sprite_urls) or "(none)"
            print(
                f"  #{pr.placement:<3} "
                f"{pr.resolved_archetype:<25} "
                f"raw={pr.raw_archetype!r}  "
                f"sprites={sprites}"
            )
        remaining = len(result.text_label_results) - 20
        if remaining > 0:
            print(f"  ... and {remaining} more")

    if result.rogue_results:
        print(f"\n--- Rogue Results ({len(result.rogue_results)}) ---")
        for pr in result.rogue_results[:10]:
            print(
                f"  #{pr.placement:<3} {pr.tournament_name}  raw={pr.raw_archetype!r}"
            )

    if result.unknown_results:
        print(f"\n--- Unknown Results ({len(result.unknown_results)}) ---")
        for pr in result.unknown_results[:10]:
            print(
                f"  #{pr.placement:<3} {pr.tournament_name}  raw={pr.raw_archetype!r}"
            )

    if result.cinderace_text_results:
        print("\n--- REGRESSION: Cinderace in text_label ---")
        for pr in result.cinderace_text_results:
            print(
                f"  #{pr.placement:<3} "
                f"{pr.tournament_name}  "
                f"raw={pr.raw_archetype!r}  "
                f"sprites={pr.sprite_urls}"
            )

    if result.errors:
        print(f"\n--- Errors ({len(result.errors)}) ---")
        for err in result.errors:
            print(f"  - {err}")

    print("\n" + "=" * 60)
    status = "PASS" if result.passed else "FAIL"
    print(f"RESULT: {status}")
    threshold_pct = f"{PASS_THRESHOLD * 100:.0f}%"
    print(f"  Sprite accuracy: {sprite_pct} (threshold: {threshold_pct})")
    cinderace_count = len(result.cinderace_text_results)
    print(f"  Cinderace regressions: {cinderace_count} (threshold: 0)")
    print("=" * 60 + "\n")


def print_json(result: ValidationResult) -> None:
    """Print validation results as JSON."""
    data = {
        "total_tournaments": result.total_tournaments,
        "total_placements": result.total_placements,
        "accuracy": round(result.accuracy, 4),
        "passed": result.passed,
        "method_breakdown": dict(result.method_counts),
        "text_label_count": len(result.text_label_results),
        "rogue_count": len(result.rogue_results),
        "unknown_count": len(result.unknown_results),
        "cinderace_regression_count": len(result.cinderace_text_results),
        "error_count": len(result.errors),
        "text_label_results": [
            {
                "tournament": pr.tournament_name,
                "placement": pr.placement,
                "raw": pr.raw_archetype,
                "resolved": pr.resolved_archetype,
                "sprites": pr.sprite_urls,
            }
            for pr in result.text_label_results
        ],
        "rogue_results": [
            {
                "tournament": pr.tournament_name,
                "placement": pr.placement,
                "raw": pr.raw_archetype,
            }
            for pr in result.rogue_results
        ],
        "unknown_results": [
            {
                "tournament": pr.tournament_name,
                "placement": pr.placement,
                "raw": pr.raw_archetype,
            }
            for pr in result.unknown_results
        ],
        "errors": result.errors,
    }
    print(json.dumps(data, indent=2))


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=("Validate JP archetype pipeline against live Limitless data."),
    )
    parser.add_argument(
        "--tournaments",
        type=int,
        default=20,
        help="Number of tournaments to process (default: 20)",
    )
    parser.add_argument(
        "--lookback-days",
        type=int,
        default=90,
        help="Lookback window in days (default: 90)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose (DEBUG) logging",
    )
    parser.add_argument(
        "--output",
        choices=["table", "json"],
        default="table",
        help="Output format (default: table)",
    )
    return parser.parse_args()


async def main() -> int:
    """Run the validation pipeline.

    Returns:
        Exit code: 0 if pass, 1 if fail.
    """
    args = parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    result = await validate_pipeline(
        max_tournaments=args.tournaments,
        lookback_days=args.lookback_days,
        verbose=args.verbose,
    )

    if args.output == "json":
        print_json(result)
    else:
        print_table(result)

    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
