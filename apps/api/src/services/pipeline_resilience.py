"""Shared resilience utilities for pipeline operations.

Provides retry logic for transient DB errors and timeout wrappers
for long-running pipeline steps. Follows the existing manual-retry
pattern used in HTTP clients (tcgdex.py, pokecabook.py).
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Coroutine
from typing import Any

from sqlalchemy.exc import OperationalError

logger = logging.getLogger(__name__)

# Retry defaults
DEFAULT_MAX_RETRIES = 3
DEFAULT_BASE_DELAY = 1.0  # seconds

# Per-pipeline timeout defaults (seconds)
PIPELINE_TIMEOUTS: dict[str, int] = {
    "compute_meta": 300,
    "compute_evolution": 600,
    "sync_cards_en": 300,
    "sync_cards_jp": 300,
    "sync_jp_adoption_rates": 120,
}
DEFAULT_TIMEOUT = 300


async def retry_commit(
    session: Any,
    *,
    max_retries: int = DEFAULT_MAX_RETRIES,
    base_delay: float = DEFAULT_BASE_DELAY,
    context: str = "",
) -> None:
    """Retry session.commit() on transient DB errors.

    Uses exponential backoff. Only retries on OperationalError
    (connection resets, lock timeouts, deadlocks). IntegrityError
    and other errors are re-raised immediately.

    Args:
        session: SQLAlchemy AsyncSession.
        max_retries: Maximum number of attempts.
        base_delay: Initial delay in seconds (doubles each retry).
        context: Description for log messages (e.g. "save_snapshot").
    """
    label = f" [{context}]" if context else ""

    for attempt in range(max_retries):
        try:
            await session.commit()
            return
        except OperationalError as e:
            if attempt < max_retries - 1:
                delay = base_delay * (2**attempt)
                logger.warning(
                    "Transient DB error (attempt %d/%d)%s: %s. Retrying in %.1fs...",
                    attempt + 1,
                    max_retries,
                    label,
                    str(e)[:200],
                    delay,
                )
                await asyncio.sleep(delay)
            else:
                logger.error(
                    "DB commit failed after %d attempts%s: %s",
                    max_retries,
                    label,
                    str(e)[:200],
                )
                raise


async def with_timeout(
    coro: Coroutine[Any, Any, Any],
    timeout_seconds: float,
    *,
    pipeline: str = "",
    step: str = "",
) -> Any:
    """Wrap an async operation with a timeout.

    Logs timeout events with pipeline context before re-raising.

    Args:
        coro: The coroutine to run.
        timeout_seconds: Max seconds to wait.
        pipeline: Pipeline name for logging.
        step: Step description for logging.

    Returns:
        The coroutine's return value.

    Raises:
        TimeoutError: If the operation exceeds the timeout.
    """
    try:
        async with asyncio.timeout(timeout_seconds):
            return await coro
    except TimeoutError:
        logger.error(
            "Pipeline timeout after %ds: pipeline=%s step=%s",
            timeout_seconds,
            pipeline,
            step,
        )
        raise
