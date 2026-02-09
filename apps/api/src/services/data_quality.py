"""Fail-open data quality validation for pipeline outputs.

Validates placement data and meta snapshots, returning warnings
without ever blocking saves. All validation errors are caught and
logged — never raised.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Any

logger = logging.getLogger(__name__)

VALID_TIERS = {"S", "A", "B", "C", "Rogue"}
VALID_DIRECTIONS = {"up", "down", "stable"}
SHARE_SUM_TOLERANCE = 0.05


def validate_placement(placement: Any) -> list[str]:
    """Return quality warnings for a placement. Never raises.

    Args:
        placement: An object with archetype, raw_archetype_sprites,
            archetype_confidence, and archetype_detection_method attrs.

    Returns:
        List of warning strings. Empty list means no issues found.
    """
    try:
        warnings: list[str] = []

        archetype = getattr(placement, "archetype", None)
        sprites = getattr(placement, "raw_archetype_sprites", None)
        confidence = getattr(placement, "archetype_confidence", None)
        method = getattr(placement, "archetype_detection_method", None)

        # Sprites present but archetype is Unknown
        if archetype == "Unknown" and sprites:
            warnings.append(f"sprites_present_but_unknown: {sprites}")

        # Low confidence score
        if confidence is not None and confidence < 0.5:
            warnings.append(f"low_confidence: {confidence}")

        # text_label fallback with sprites available
        if method == "text_label" and sprites:
            warnings.append(f"text_label_with_sprites: {sprites}")

        if warnings:
            logger.warning(
                "placement_quality_warnings",
                extra={
                    "archetype": archetype,
                    "method": method,
                    "confidence": confidence,
                    "warnings": warnings,
                },
            )

        return warnings

    except Exception:
        # Fail open — never block the pipeline
        return []


def validate_snapshot(snapshot: Any) -> list[str]:
    """Return quality warnings for a meta snapshot. Never raises.

    Checks archetype_shares sum, share ranges, tier validity,
    trend directions, sample size, and snapshot date.

    Args:
        snapshot: A MetaSnapshot-like object.

    Returns:
        List of warning strings. Empty list means no issues.
    """
    try:
        warnings: list[str] = []

        # -- archetype_shares --
        shares = getattr(snapshot, "archetype_shares", None)
        if shares and isinstance(shares, dict):
            for arch, share in shares.items():
                if not isinstance(share, int | float):
                    warnings.append(f"non_numeric_share: {arch}={share}")
                elif share < 0 or share > 1:
                    warnings.append(f"share_out_of_range: {arch}={share}")
                if not arch or not arch.strip():
                    warnings.append("empty_archetype_name_in_shares")

            total = sum(v for v in shares.values() if isinstance(v, int | float))
            if abs(total - 1.0) > SHARE_SUM_TOLERANCE:
                warnings.append(f"shares_sum_off: {total:.4f} (expected ~1.0)")

        # -- sample_size --
        sample_size = getattr(snapshot, "sample_size", None)
        if sample_size is not None and sample_size < 0:
            warnings.append(f"negative_sample_size: {sample_size}")

        # -- snapshot_date --
        snapshot_date = getattr(snapshot, "snapshot_date", None)
        if isinstance(snapshot_date, date) and snapshot_date > date.today():
            warnings.append(f"future_snapshot_date: {snapshot_date}")

        # -- tier_assignments --
        tiers = getattr(snapshot, "tier_assignments", None)
        if tiers and isinstance(tiers, dict):
            for arch, tier in tiers.items():
                if tier not in VALID_TIERS:
                    warnings.append(f"invalid_tier: {arch}={tier}")

        # -- trends --
        trends = getattr(snapshot, "trends", None)
        if trends and isinstance(trends, dict):
            for arch, trend in trends.items():
                if isinstance(trend, dict):
                    direction = trend.get("direction")
                    if direction and direction not in VALID_DIRECTIONS:
                        warnings.append(f"invalid_trend_direction: {arch}={direction}")

        if warnings:
            logger.warning(
                "snapshot_quality_warnings",
                extra={
                    "snapshot_date": str(getattr(snapshot, "snapshot_date", None)),
                    "region": getattr(snapshot, "region", None),
                    "warnings": warnings,
                },
            )

        return warnings

    except Exception:
        return []
