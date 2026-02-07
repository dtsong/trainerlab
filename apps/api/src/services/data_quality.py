"""Fail-open data quality validation for pipeline placements.

Validates placement data and returns warnings without ever blocking
saves. All validation errors are caught and logged — never raised.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


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
