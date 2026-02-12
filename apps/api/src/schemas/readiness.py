"""Operational readiness schemas."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class TPCIReadinessResponse(BaseModel):
    """Readiness signal for post-major fast-follow operations."""

    status: Literal["pass", "fail"] = Field(
        description="Whether the system meets expected post-major readiness"
    )
    checked_at: date = Field(description="Date readiness was evaluated (UTC)")

    latest_major_end_date: date | None = Field(
        default=None,
        description="Latest known major event end date (UTC date)",
    )
    deadline_date: date | None = Field(
        default=None,
        description="Tuesday UTC readiness deadline derived from latest major end",
    )

    snapshot_date: date | None = Field(
        default=None,
        description="Latest official snapshot date used for evaluation",
    )
    sample_size: int | None = Field(
        default=None,
        ge=0,
        description="Official snapshot sample size",
    )

    meets_partial_threshold: bool = Field(
        description="Whether official snapshot meets partial threshold (>=8)"
    )
    meets_fresh_threshold: bool = Field(
        description="Whether official snapshot meets fresh threshold (>=64)"
    )
    deadline_missed: bool = Field(
        description=(
            "Whether Tuesday UTC deadline has passed without meeting fresh threshold"
        )
    )

    message: str = Field(description="Human-readable operational guidance")
