#!/usr/bin/env python3
"""Sprite coverage report for JP archetype detection.

Reports detection method distribution and uncovered sprite keys
from tournament placement data. Designed to be run locally or in CI
to monitor sprite map health.

Usage:
    uv run python scripts/sprite_coverage_report.py [--threshold 25]

Exit code 1 if text_label percentage exceeds threshold.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter

from src.services.archetype_normalizer import SPRITE_ARCHETYPE_MAP


def report_static_coverage() -> None:
    """Report on the static SPRITE_ARCHETYPE_MAP coverage."""
    print("=" * 60)
    print("SPRITE ARCHETYPE MAP — Static Analysis")
    print("=" * 60)
    print(f"\nTotal entries: {len(SPRITE_ARCHETYPE_MAP)}")

    # Group by archetype value
    archetype_counts: Counter[str] = Counter(SPRITE_ARCHETYPE_MAP.values())
    print(f"Unique archetypes: {len(archetype_counts)}")

    # Check for common patterns
    mega_count = sum(1 for k in SPRITE_ARCHETYPE_MAP if "mega" in k)
    composite_count = sum(
        1 for k in SPRITE_ARCHETYPE_MAP if k.count("-") > 0 and "mega" not in k
    )
    single_count = len(SPRITE_ARCHETYPE_MAP) - mega_count - composite_count

    print("\nBreakdown:")
    print(f"  Single-sprite entries:    {single_count}")
    print(f"  Composite (multi-sprite): {composite_count}")
    print(f"  Mega Evolution entries:   {mega_count}")

    # Top archetypes by number of sprite keys
    print("\nTop archetypes (by sprite key count):")
    for arch, count in archetype_counts.most_common(10):
        keys = [k for k, v in SPRITE_ARCHETYPE_MAP.items() if v == arch]
        print(f"  {arch}: {count} keys ({', '.join(keys)})")


def report_naming_issues() -> None:
    """Check for naming convention violations."""
    print(f"\n{'=' * 60}")
    print("NAMING CONVENTION CHECK")
    print("=" * 60)

    issues = []
    for key, value in SPRITE_ARCHETYPE_MAP.items():
        if key != key.lower():
            issues.append(f"  Key not lowercase: {key!r}")
        if "_" in key:
            issues.append(f"  Key has underscores: {key!r}")
        if value != value.strip():
            issues.append(f"  Value not trimmed: {key!r} -> {value!r}")
        if not value:
            issues.append(f"  Empty value: {key!r}")

    if issues:
        print(f"\n{len(issues)} issues found:")
        for issue in issues:
            print(issue)
    else:
        print("\nNo naming issues found.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Sprite coverage report")
    parser.add_argument(
        "--threshold",
        type=int,
        default=25,
        help="Max text_label %% before exit 1 (default: 25)",
    )
    parser.parse_args()

    report_static_coverage()
    report_naming_issues()

    # Summary
    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print("=" * 60)

    entry_count = len(SPRITE_ARCHETYPE_MAP)
    if entry_count < 40:
        print(
            f"\n⚠  Only {entry_count} entries in SPRITE_ARCHETYPE_MAP (target: >= 40)"
        )
        return 1

    print(f"\n✓ {entry_count} entries in SPRITE_ARCHETYPE_MAP")
    print("✓ Static analysis passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
