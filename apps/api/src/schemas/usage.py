"""Card usage statistics Pydantic schemas."""

from datetime import date

from pydantic import BaseModel


class UsageTrendPoint(BaseModel):
    """A single point in usage trend data."""

    date: date
    inclusion_rate: float
    avg_copies: float | None = None


class CardUsageResponse(BaseModel):
    """Card usage statistics response."""

    card_id: str
    format: str
    inclusion_rate: float
    avg_copies: float | None = None
    trend: list[UsageTrendPoint] = []
    sample_size: int
