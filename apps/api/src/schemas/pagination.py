"""Pagination schemas for API responses."""

import math
from typing import Generic, TypeVar

from pydantic import BaseModel, computed_field

from src.schemas.freshness import DataFreshness

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper.

    Example usage:
        PaginatedResponse[CardSummaryResponse](
            items=[...],
            total=100,
            page=1,
            limit=10,
            has_next=True,
            has_prev=False,
        )
    """

    items: list[T]
    total: int
    page: int
    limit: int
    has_next: bool
    has_prev: bool
    next_cursor: str | None = None
    freshness: DataFreshness | None = None

    @computed_field
    @property
    def total_pages(self) -> int:
        """Calculate total number of pages."""
        if self.limit <= 0:
            return 0
        return math.ceil(self.total / self.limit)
