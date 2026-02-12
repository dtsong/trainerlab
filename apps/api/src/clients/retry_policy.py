"""Shared retry/backoff policy for external source clients."""

from __future__ import annotations

from typing import Final

# Unified defaults for external source ingestion clients.
DEFAULT_TIMEOUT_SECONDS: Final[float] = 30.0
DEFAULT_MAX_RETRIES: Final[int] = 3
DEFAULT_RETRY_DELAY_SECONDS: Final[float] = 1.0

# Retry only transient conditions.
TRANSIENT_HTTP_STATUS_CODES: Final[set[int]] = {
    408,
    425,
    429,
    500,
    502,
    503,
    504,
}


def is_retryable_status(status_code: int) -> bool:
    """Return True when HTTP status should be retried."""
    return status_code in TRANSIENT_HTTP_STATUS_CODES


def backoff_delay_seconds(base_delay: float, attempt: int) -> float:
    """Exponential backoff delay for zero-based attempt index."""
    return base_delay * (2**attempt)


def classify_status(status_code: int) -> str:
    """Classify status into a coarse error category for logging."""
    if status_code == 429:
        return "rate_limited"
    if status_code in {502, 503, 504}:
        return "upstream_unavailable"
    if status_code >= 500:
        return "upstream_error"
    if status_code >= 400:
        return "client_error"
    return "unknown"
