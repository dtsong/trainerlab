"""Shared freshness payload schema for data responses."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

FreshnessStatus = Literal["fresh", "stale", "partial", "no_data"]
CadenceProfile = Literal[
    "jp_daily_cadence",
    "grassroots_daily_cadence",
    "tpci_event_cadence",
    "default_cadence",
]


class DataFreshness(BaseModel):
    """Freshness metadata for API payloads consumed by UI surfaces."""

    status: FreshnessStatus = Field(description="Freshness status classification")
    cadence_profile: CadenceProfile = Field(
        description="Cadence profile used for freshness evaluation"
    )
    snapshot_date: date | None = Field(
        default=None,
        description="Date of latest dataset snapshot represented by response",
    )
    sample_size: int | None = Field(
        default=None,
        ge=0,
        description="Sample size represented by latest snapshot",
    )
    staleness_days: int | None = Field(
        default=None,
        ge=0,
        description="Days since latest snapshot date",
    )
    source_coverage: list[str] | None = Field(
        default=None,
        description="Optional data source coverage notes",
    )
    message: str | None = Field(
        default=None,
        description="Human-readable freshness guidance",
    )
