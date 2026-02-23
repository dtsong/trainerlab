"""Async client for Official Pokemon Players Club.

Scrapes tournament data from the official Players Club site
at players.pokemon-card.com. The site is a JavaScript SPA;
this client uses Kernel cloud browser to render pages and
BeautifulSoup to parse the resulting HTML.
"""

import asyncio
import logging
import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any, Self

import httpx
from bs4 import BeautifulSoup, Tag

from src.clients.kernel_browser import KernelBrowser, KernelBrowserError
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
    """A tournament from the Players Club event list."""

    tournament_id: str
    name: str
    date: date
    event_type: str | None = None
    league: str | None = None
    prefecture: str | None = None
    participant_count: int | None = None
    source_url: str | None = None


@dataclass
class PlayersClubPlacement:
    """A placement from a Players Club tournament."""

    placement: int
    player_name: str | None = None
    player_id: str | None = None
    prefecture: str | None = None
    archetype_name: str | None = None
    deck_code: str | None = None


@dataclass
class PlayersClubTournamentDetail:
    """Detailed tournament data with placements."""

    tournament: PlayersClubTournament
    placements: list[PlayersClubPlacement] = field(
        default_factory=list,
    )


# Regex to extract 10-digit player ID from profile text
_PLAYER_ID_RE = re.compile(r"プレイヤーID[：:]?\s*(\d{10})")

# Regex to extract deck code from deck URL
_DECK_CODE_RE = re.compile(r"deckID/([A-Za-z0-9-]+)")

# Regex to extract event ID from result URL
_EVENT_ID_RE = re.compile(r"/event/detail/(\d+)/result")


class PlayersClubClient:
    """Async client for Official Pokemon Players Club.

    Conservative rate limiting (5 req/min) since this is an
    official Pokemon site. Uses Kernel cloud browser to render
    JS SPA pages and BeautifulSoup for HTML parsing.
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
                wait_time = 60 - (now - oldest) + 0.1
                if wait_time > 0:
                    logger.info(
                        "Players Club rate limiting: waiting %.1fs",
                        wait_time,
                    )
                    await asyncio.sleep(wait_time)

            self._request_times.append(asyncio.get_running_loop().time())

    async def _get(self, endpoint: str) -> httpx.Response:
        """Make a GET request with retry and rate limiting."""
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

    async def _get_rendered(
        self,
        endpoint: str,
        wait_selector: str | None = None,
    ) -> str:
        """Fetch a page using a cloud browser for JS-rendered content.

        Args:
            endpoint: Path relative to BASE_URL.
            wait_selector: Optional CSS selector to wait for.

        Returns:
            Rendered HTML string.

        Raises:
            PlayersClubError: On fetch failure.
        """
        await self._wait_for_rate_limit()
        url = f"{self.BASE_URL}{endpoint}"
        try:
            async with KernelBrowser() as kb:
                return await kb.fetch_rendered(url, wait_selector=wait_selector)
        except KernelBrowserError as e:
            raise PlayersClubError(f"Rendered fetch failed for {endpoint}: {e}") from e

    async def fetch_event_list(
        self,
        days: int = 30,
        max_pages: int = 5,
        event_types: list[str] | None = None,
    ) -> list[PlayersClubTournament]:
        """Fetch recent events from the rendered event result list.

        Args:
            days: Only include events from last N days.
            max_pages: Maximum pagination pages to follow.
            event_types: Filter by event type (e.g. ["CL", "シティリーグ"]).

        Returns:
            List of tournament metadata.
        """
        tournaments: list[PlayersClubTournament] = []
        cutoff = date.today() - timedelta(days=days)
        seen_ids: set[str] = set()

        for page in range(1, max_pages + 1):
            endpoint = "/event/result/list"
            if page > 1:
                endpoint = f"/event/result/list?page={page}"

            try:
                html = await self._get_rendered(
                    endpoint, wait_selector=".event-list-item"
                )
            except PlayersClubError:
                if page == 1:
                    raise
                logger.info("No more pages after page %d", page - 1)
                break

            page_tournaments = self._parse_event_list_html(html)

            if not page_tournaments:
                break

            hit_cutoff = False
            for t in page_tournaments:
                if t.tournament_id in seen_ids:
                    continue
                seen_ids.add(t.tournament_id)

                if t.date < cutoff:
                    hit_cutoff = True
                    continue

                if event_types and not self._matches_event_type(t, event_types):
                    continue

                tournaments.append(t)

            if hit_cutoff:
                break

        return tournaments

    def _matches_event_type(
        self,
        tournament: PlayersClubTournament,
        event_types: list[str],
    ) -> bool:
        """Check if tournament matches any of the given event types."""
        if not tournament.event_type:
            return False
        t_lower = tournament.event_type.lower()
        return any(et.lower() in t_lower for et in event_types)

    def _parse_event_list_html(self, html: str) -> list[PlayersClubTournament]:
        """Parse the event result list HTML into tournament objects."""
        soup = BeautifulSoup(html, "html.parser")
        tournaments: list[PlayersClubTournament] = []

        items = soup.select(".event-list-item")
        for item in items:
            tournament = self._parse_event_list_item(item)
            if tournament:
                tournaments.append(tournament)

        return tournaments

    def _parse_event_list_item(self, item: Tag) -> PlayersClubTournament | None:
        """Parse a single event list item element."""
        try:
            # Extract event ID from result link
            link = item.select_one("a[href*='/event/detail/']")
            if not link:
                return None

            href_raw = link.get("href", "")
            href = href_raw[0] if isinstance(href_raw, list) else str(href_raw)

            match = _EVENT_ID_RE.search(href)
            if not match:
                return None
            event_id = match.group(1)

            # Extract event name
            name_el = item.select_one(".event-list-item__name, .event-title, h3, h4")
            name = name_el.get_text(strip=True) if name_el else ""
            if not name:
                name = link.get_text(strip=True)

            # Extract date
            date_el = item.select_one(".event-list-item__date, .event-date, time")
            event_date: date | None = None
            if date_el:
                date_text = date_el.get_text(strip=True)
                event_date = self._parse_date(date_text)
                if not event_date:
                    dt_raw = date_el.get("datetime", "")
                    datetime_attr = (
                        dt_raw[0] if isinstance(dt_raw, list) else str(dt_raw)
                    )
                    if datetime_attr:
                        event_date = self._parse_date(datetime_attr)
            if not event_date:
                # Try to find date in item text
                text = item.get_text()
                date_match = re.search(r"(\d{4})[/年](\d{1,2})[/月](\d{1,2})", text)
                if date_match:
                    event_date = date(
                        int(date_match.group(1)),
                        int(date_match.group(2)),
                        int(date_match.group(3)),
                    )
            if not event_date:
                return None

            # Extract event type and league from text/classes
            event_type = self._extract_event_type(item)
            league = self._extract_league(item)
            prefecture = self._extract_prefecture(item)

            return PlayersClubTournament(
                tournament_id=event_id,
                name=name,
                date=event_date,
                event_type=event_type,
                league=league,
                prefecture=prefecture,
                source_url=(f"{self.BASE_URL}/event/detail/{event_id}/result"),
            )
        except (ValueError, AttributeError):
            logger.warning(
                "Failed to parse event list item",
                exc_info=True,
            )
            return None

    def _extract_event_type(self, item: Tag) -> str | None:
        """Extract event type (CL, Gym Battle, etc.) from item."""
        text = item.get_text()
        if "シティリーグ" in text or "CL" in text:
            return "シティリーグ"
        if "ジムバトル" in text:
            return "ジムバトル"
        if "トレーナーズリーグ" in text:
            return "トレーナーズリーグ"
        type_el = item.select_one(".event-list-item__type, .event-type")
        if type_el:
            return type_el.get_text(strip=True)
        return None

    def _extract_league(self, item: Tag) -> str | None:
        """Extract league division from item."""
        text = item.get_text()
        if "マスター" in text or "Master" in text:
            return "Master"
        if "シニア" in text or "Senior" in text:
            return "Senior"
        if "ジュニア" in text or "Junior" in text:
            return "Junior"
        if "オープン" in text or "Open" in text:
            return "Open"
        return None

    def _extract_prefecture(self, item: Tag) -> str | None:
        """Extract prefecture from item."""
        pref_el = item.select_one(
            ".event-list-item__prefecture, .event-area, .prefecture"
        )
        if pref_el:
            return pref_el.get_text(strip=True)
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

        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00")).date()
        except ValueError:
            return None

    async def fetch_event_detail(self, event_id: str) -> PlayersClubTournamentDetail:
        """Fetch detailed event results from rendered page.

        Args:
            event_id: The event identifier from the event list.

        Returns:
            Tournament detail with placements.
        """
        endpoint = f"/event/detail/{event_id}/result"

        html = await self._get_rendered(endpoint, wait_selector=".c-rankTable")

        return self._parse_event_detail_html(html, event_id)

    def _parse_event_detail_html(
        self, html: str, event_id: str
    ) -> PlayersClubTournamentDetail:
        """Parse event detail page HTML."""
        soup = BeautifulSoup(html, "html.parser")

        # Extract tournament metadata from page header
        name = ""
        name_el = soup.select_one(".event-detail__name, .event-title, h1, h2")
        if name_el:
            name = name_el.get_text(strip=True)

        event_date: date | None = None
        date_el = soup.select_one(".event-detail__date, .event-date, time")
        if date_el:
            date_text = date_el.get_text(strip=True)
            event_date = self._parse_date(date_text)
            if not event_date:
                dt_raw = date_el.get("datetime", "")
                datetime_attr = dt_raw[0] if isinstance(dt_raw, list) else str(dt_raw)
                if datetime_attr:
                    event_date = self._parse_date(datetime_attr)

        if not event_date:
            text = soup.get_text()
            date_match = re.search(r"(\d{4})[/年](\d{1,2})[/月](\d{1,2})", text)
            if date_match:
                event_date = date(
                    int(date_match.group(1)),
                    int(date_match.group(2)),
                    int(date_match.group(3)),
                )

        if not event_date:
            event_date = date.today()

        tournament = PlayersClubTournament(
            tournament_id=event_id,
            name=name or f"Event {event_id}",
            date=event_date,
            source_url=(f"{self.BASE_URL}/event/detail/{event_id}/result"),
        )

        # Parse rank table
        placements = self._parse_rank_table(soup)

        tournament.participant_count = len(placements) or None

        return PlayersClubTournamentDetail(
            tournament=tournament,
            placements=placements,
        )

    def _parse_rank_table(self, soup: BeautifulSoup) -> list[PlayersClubPlacement]:
        """Parse the c-rankTable for placement data."""
        placements: list[PlayersClubPlacement] = []

        table = soup.select_one(".c-rankTable")
        if not table:
            return placements

        rows = table.select("tr")
        for row in rows:
            cells = row.select("td")
            if not cells:
                continue

            placement = self._parse_rank_row(cells)
            if placement:
                placements.append(placement)

        return placements

    def _parse_rank_row(self, cells: list[Tag]) -> PlayersClubPlacement | None:
        """Parse a single rank table row."""
        try:
            if len(cells) < 2:
                return None

            # First cell: placement rank (順位)
            rank_text = cells[0].get_text(strip=True)
            rank_match = re.search(r"(\d+)", rank_text)
            if not rank_match:
                return None
            rank = int(rank_match.group(1))

            player_name: str | None = None
            player_id: str | None = None
            prefecture: str | None = None
            deck_code: str | None = None

            # Parse remaining cells
            for cell in cells[1:]:
                cell_text = cell.get_text(separator=" ")

                # Check for player name element
                name_el = cell.select_one(".player-name, .username")
                if name_el and not player_name:
                    player_name = name_el.get_text(strip=True)

                # Check for player ID pattern
                pid_match = _PLAYER_ID_RE.search(cell_text)
                if pid_match:
                    player_id = pid_match.group(1)

                # Check for deck code link
                deck_link = cell.select_one(
                    "a[href*='deckID/'], a[href*='deck/confirm']"
                )
                if deck_link:
                    deck_href_raw = deck_link.get("href", "")
                    deck_href = (
                        deck_href_raw[0]
                        if isinstance(deck_href_raw, list)
                        else str(deck_href_raw)
                    )
                    code_match = _DECK_CODE_RE.search(deck_href)
                    if code_match:
                        deck_code = code_match.group(1)

                # Extract prefecture (エリア)
                text = cell.get_text(strip=True)
                if "県" in text or "都" in text or "府" in text:
                    prefecture = text
                area_el = cell.select_one(".area, .prefecture")
                if area_el:
                    prefecture = area_el.get_text(strip=True)

            return PlayersClubPlacement(
                placement=rank,
                player_name=player_name,
                player_id=player_id,
                prefecture=prefecture,
                deck_code=deck_code,
            )
        except (ValueError, AttributeError):
            logger.warning(
                "Failed to parse rank row",
                exc_info=True,
            )
            return None
