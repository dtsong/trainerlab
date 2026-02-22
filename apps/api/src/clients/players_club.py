"""Async HTTP client for Official Pokemon Players Club.

Scrapes tournament data from the official Players Club site
at players.pokemon-card.com. The site is a JavaScript SPA;
this client targets the underlying API endpoints.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any, Self

import httpx

from src.clients.retry_policy import (
    DEFAULT_MAX_RETRIES,
    DEFAULT_RETRY_DELAY_SECONDS,
    DEFAULT_TIMEOUT_SECONDS,
    backoff_delay_seconds,
    classify_status,
    is_retryable_status,
)

logger = logging.getLogger(__name__)


class PlayersClubError(Exception):
    """Exception raised for Players Club scraping errors."""


class PlayersClubRateLimitError(PlayersClubError):
    """Exception raised when rate limited."""


@dataclass
class PlayersClubTournament:
    """A tournament from the Players Club."""

    tournament_id: str
    name: str
    date: date
    prefecture: str | None = None
    participant_count: int | None = None
    source_url: str | None = None


@dataclass
class PlayersClubPlacement:
    """A placement from a Players Club tournament."""

    placement: int
    player_name: str | None = None
    archetype_name: str | None = None
    deck_code: str | None = None


@dataclass
class PlayersClubTournamentDetail:
    """Detailed tournament data with placements."""

    tournament: PlayersClubTournament
    placements: list[PlayersClubPlacement] = field(
        default_factory=list,
    )


class PlayersClubClient:
    """Async HTTP client for Official Pokemon Players Club.

    Conservative rate limiting (5 req/min) since this is an
    official Pokemon site. Targets the underlying JSON API
    endpoints.
    """

    BASE_URL = "https://players.pokemon-card.com"

    def __init__(
        self,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY_SECONDS,
        requests_per_minute: int = 5,
        max_concurrent: int = 1,
    ):
        self._timeout = timeout
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._requests_per_minute = requests_per_minute

        self._request_times: list[float] = []
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._lock = asyncio.Lock()

        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=timeout,
            headers={
                "User-Agent": ("TrainerLab/1.0 (Pokemon TCG Meta Analysis)"),
                "Accept": "application/json, text/html",
                "Accept-Language": "ja,en;q=0.9",
            },
            follow_redirects=True,
        )

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def close(self) -> None:
        await self._client.aclose()

    async def _wait_for_rate_limit(self) -> None:
        async with self._lock:
            now = asyncio.get_running_loop().time()
            self._request_times = [t for t in self._request_times if now - t < 60]

            if len(self._request_times) >= self._requests_per_minute:
                oldest = self._request_times[0]
                wait_time = 60 - (now - oldest) + 0.1  # buffer to avoid edge-case
                if wait_time > 0:
                    logger.info(
                        "Players Club rate limiting: waiting %.1fs",
                        wait_time,
                    )
                    await asyncio.sleep(wait_time)

            # Record post-wait time so the window reflects actual request spacing
            self._request_times.append(asyncio.get_running_loop().time())

    async def _get(self, endpoint: str) -> httpx.Response:
        """Make a GET request with retry and rate limiting.

        Returns the full response (caller decides JSON vs HTML).
        """
        async with self._semaphore:
            last_error: Exception | None = None

            for attempt in range(self._max_retries):
                await self._wait_for_rate_limit()

                try:
                    response = await self._client.get(
                        endpoint,
                    )

                    if response.status_code == 404:
                        raise PlayersClubError(f"Not found: {endpoint}")

                    if is_retryable_status(
                        response.status_code,
                    ):
                        delay = backoff_delay_seconds(self._retry_delay, attempt)
                        logger.warning(
                            "players_club_retry "
                            "status=%d category=%s "
                            "endpoint=%s "
                            "attempt=%d/%d delay=%.2fs",
                            response.status_code,
                            classify_status(response.status_code),
                            endpoint,
                            attempt + 1,
                            self._max_retries,
                            delay,
                        )
                        await asyncio.sleep(delay)
                        if response.status_code == 429:
                            last_error = PlayersClubRateLimitError("Rate limited")
                        else:
                            last_error = PlayersClubError(
                                f"Transient HTTP {response.status_code}"
                            )
                        continue

                    response.raise_for_status()
                    return response

                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 404:
                        raise PlayersClubError(f"Not found: {endpoint}") from e
                    if is_retryable_status(e.response.status_code):
                        delay = backoff_delay_seconds(self._retry_delay, attempt)
                        logger.warning(
                            "players_club_retry "
                            "exception_status=%d "
                            "category=%s "
                            "endpoint=%s "
                            "attempt=%d/%d delay=%.2fs",
                            e.response.status_code,
                            classify_status(e.response.status_code),
                            endpoint,
                            attempt + 1,
                            self._max_retries,
                            delay,
                        )
                        await asyncio.sleep(delay)
                        last_error = e
                        continue
                    last_error = e
                    raise PlayersClubError(
                        f"HTTP error {e.response.status_code} on {endpoint}"
                    ) from e

                except httpx.RequestError as e:
                    last_error = e
                    delay = backoff_delay_seconds(self._retry_delay, attempt)
                    logger.warning(
                        "players_club_retry "
                        "request_error=%s endpoint=%s "
                        "attempt=%d/%d delay=%.2fs",
                        type(e).__name__,
                        endpoint,
                        attempt + 1,
                        self._max_retries,
                        delay,
                    )
                    await asyncio.sleep(delay)

            raise PlayersClubError(
                f"Max retries exceeded for {endpoint}"
            ) from last_error

    async def fetch_recent_tournaments(
        self, days: int = 30
    ) -> list[PlayersClubTournament]:
        """Fetch recent tournament listings.

        Args:
            days: Only include tournaments from last N days.

        Returns:
            List of tournament metadata.

        Note:
            API endpoints are not yet confirmed. This method
            will be updated once the SPA's underlying API is
            reverse-engineered.
        """
        # TODO: Replace with actual API endpoint once
        # discovered. The SPA at players.pokemon-card.com
        # likely calls JSON endpoints for tournament data.
        endpoint = "/api/tournament/list"

        try:
            response = await self._get(endpoint)
        except PlayersClubError as e:
            if "Not found" in str(e):
                logger.warning(
                    "Tournament list endpoint not available (404). "
                    "API discovery pending."
                )
                return []
            raise

        try:
            data = response.json()
        except Exception as e:
            raise PlayersClubError(f"Failed to parse tournament list JSON: {e}") from e

        tournaments: list[PlayersClubTournament] = []
        items = (
            data
            if isinstance(data, list)
            else data.get("tournaments", data.get("items", []))
        )

        cutoff = date.today() - timedelta(days=days)

        for item in items:
            tournament = self._parse_tournament(item)
            if tournament and tournament.date >= cutoff:
                tournaments.append(tournament)

        return tournaments

    def _parse_tournament(self, data: dict[str, Any]) -> PlayersClubTournament | None:
        """Parse a tournament from API response data."""
        try:
            # Try multiple key names since API schema is not yet confirmed
            tid = str(data.get("id") or data.get("tournament_id", ""))
            name = str(data.get("name") or data.get("title", ""))
            date_str = str(data.get("date") or data.get("event_date", ""))

            if not tid or not name or not date_str:
                return None

            tournament_date = self._parse_date(date_str)
            if not tournament_date:
                return None

            return PlayersClubTournament(
                tournament_id=tid,
                name=name,
                date=tournament_date,
                prefecture=data.get("prefecture"),
                participant_count=data.get("participant_count"),
                source_url=(f"{self.BASE_URL}/event/{tid}"),
            )
        except (ValueError, KeyError, TypeError):
            logger.warning(
                "Failed to parse tournament data: %s",
                data,
                exc_info=True,
            )
            return None

    def _parse_date(self, date_str: str) -> date | None:
        """Parse date from various formats."""
        formats = [
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%Y年%m月%d日",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt).date()
            except ValueError:
                continue

        # Try ISO format
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00")).date()
        except ValueError:
            return None

    async def fetch_tournament_detail(
        self, tournament_id: str
    ) -> PlayersClubTournamentDetail:
        """Fetch detailed tournament results.

        Args:
            tournament_id: The tournament identifier.

        Returns:
            Tournament detail with placements.

        Note:
            API endpoints are not yet confirmed.
        """
        endpoint = f"/api/tournament/{tournament_id}"

        response = await self._get(endpoint)
        try:
            data = response.json()
        except Exception as e:
            raise PlayersClubError(
                f"Failed to parse tournament detail JSON for {tournament_id}: {e}"
            ) from e

        tournament_data = data.get("tournament", data)
        tournament = self._parse_tournament(
            tournament_data,
        )
        if not tournament:
            raise PlayersClubError(
                f"Could not parse tournament metadata for {tournament_id}"
            )

        placements: list[PlayersClubPlacement] = []
        results = data.get(
            "results",
            data.get("placements", []),
        )

        for item in results:
            placement = self._parse_placement(item)
            if placement:
                placements.append(placement)

        return PlayersClubTournamentDetail(
            tournament=tournament,
            placements=placements,
        )

    def _parse_placement(self, data: dict[str, Any]) -> PlayersClubPlacement | None:
        """Parse placement from API response data."""
        try:
            rank = data.get("rank", data.get("placement"))
            if rank is None:
                return None

            return PlayersClubPlacement(
                placement=int(rank),
                player_name=data.get("player_name"),
                archetype_name=data.get(
                    "deck_name",
                    data.get("archetype"),
                ),
                deck_code=data.get("deck_code"),
            )
        except (ValueError, TypeError):
            logger.warning(
                "Failed to parse placement data: %s",
                data,
                exc_info=True,
            )
            return None
