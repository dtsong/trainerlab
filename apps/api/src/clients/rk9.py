"""Async HTTP client for RK9.gg scraping.

Scrapes Pokemon TCG event data from rk9.gg including:
- Upcoming event listings
- Event registration status and capacity
"""

import asyncio
import logging
import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Self

import httpx
from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)


class RK9Error(Exception):
    """Exception raised for RK9 scraping errors."""


class RK9RateLimitError(RK9Error):
    """Exception raised when rate limited by RK9."""


@dataclass
class RegistrationStatus:
    """Registration status for an RK9 event."""

    is_open: bool
    opens_at: datetime | None = None
    closes_at: datetime | None = None
    capacity: int | None = None
    registered_count: int | None = None


@dataclass
class RK9Event:
    """An event listing from RK9.gg."""

    name: str
    date: date
    end_date: date | None = None
    city: str | None = None
    venue: str | None = None
    country: str | None = None
    registration_url: str | None = None
    status: str = "upcoming"
    source_url: str = ""


class RK9Client:
    """Async HTTP client for RK9.gg scraping.

    Implements rate limiting and retry logic. Conservative rate
    limiting (10 req/min) to be respectful of their servers.
    """

    BASE_URL = "https://rk9.gg"

    def __init__(
        self,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 2.0,
        requests_per_minute: int = 10,
        max_concurrent: int = 2,
    ):
        """Initialize RK9 client.

        Args:
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retries on errors.
            retry_delay: Initial delay between retries (exponential backoff).
            requests_per_minute: Maximum requests per minute.
            max_concurrent: Maximum concurrent requests.
        """
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
                "Accept": "text/html,application/xhtml+xml",
            },
            follow_redirects=True,
        )

    async def __aenter__(self) -> Self:
        """Enter async context."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Exit async context and close client."""
        await self.close()

    async def close(self) -> None:
        """Close HTTP client."""
        await self._client.aclose()

    async def _wait_for_rate_limit(self) -> None:
        """Wait if necessary to respect rate limit."""
        async with self._lock:
            now = asyncio.get_running_loop().time()
            self._request_times = [t for t in self._request_times if now - t < 60]

            if len(self._request_times) >= self._requests_per_minute:
                oldest = self._request_times[0]
                wait_time = 60 - (now - oldest) + 0.1
                if wait_time > 0:
                    logger.info("RK9 rate limiting: waiting %.1fs", wait_time)
                    await asyncio.sleep(wait_time)

            self._request_times.append(now)

    async def _get(self, endpoint: str) -> str:
        """Make GET request with rate limiting and retries.

        Args:
            endpoint: URL path.

        Returns:
            HTML response content.

        Raises:
            RK9Error: On error after retries exhausted.
        """
        async with self._semaphore:
            last_error: Exception | None = None

            for attempt in range(self._max_retries):
                await self._wait_for_rate_limit()

                try:
                    response = await self._client.get(endpoint)

                    if response.status_code == 429:
                        delay = self._retry_delay * (2**attempt)
                        logger.warning(
                            "RK9 rate limited (429) on %s, "
                            "retrying in %.1fs (attempt %d)",
                            endpoint,
                            delay,
                            attempt + 1,
                        )
                        await asyncio.sleep(delay)
                        last_error = RK9RateLimitError("Rate limited")
                        continue

                    if response.status_code == 503:
                        delay = self._retry_delay * (2**attempt)
                        logger.warning(
                            "RK9 unavailable (503) on %s, retrying in %.1fs",
                            endpoint,
                            delay,
                        )
                        await asyncio.sleep(delay)
                        last_error = RK9Error("Service unavailable")
                        continue

                    response.raise_for_status()
                    return response.text

                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 404:
                        raise RK9Error(f"Not found: {endpoint}") from e
                    last_error = e
                    delay = self._retry_delay * (2**attempt)
                    logger.warning(
                        "RK9 HTTP error %d on %s, retrying in %.1fs",
                        e.response.status_code,
                        endpoint,
                        delay,
                    )
                    await asyncio.sleep(delay)

                except httpx.RequestError as e:
                    last_error = e
                    delay = self._retry_delay * (2**attempt)
                    logger.warning(
                        "RK9 request error on %s: %s, retrying in %.1fs",
                        endpoint,
                        e,
                        delay,
                    )
                    await asyncio.sleep(delay)

            raise RK9Error(f"Max retries exceeded for {endpoint}") from last_error

    # =================================================================
    # Event Listings
    # =================================================================

    async def fetch_upcoming_events(self) -> list[RK9Event]:
        """Fetch upcoming Pokemon TCG events from RK9.gg.

        Scrapes the events listing page filtered by Pokemon TCG.

        Returns:
            List of upcoming RK9 events.
        """
        endpoint = "/events/pokemon"
        html = await self._get(endpoint)
        soup = BeautifulSoup(html, "lxml")

        events: list[RK9Event] = []

        # RK9 lists events in card-style containers or table rows
        event_cards = soup.select(
            ".event-card, .event-row, [class*='event'], tr[data-event]"
        )

        if not event_cards:
            # Fallback: look for links to event detail pages
            event_cards = self._find_event_containers(soup)

        for card in event_cards:
            try:
                event = self._parse_event_card(card)
                if event:
                    events.append(event)
            except (ValueError, KeyError, AttributeError):
                logger.warning(
                    "Error parsing RK9 event card",
                    exc_info=True,
                )
                continue

        logger.info("Fetched %d upcoming events from RK9", len(events))
        return events

    def _find_event_containers(self, soup: BeautifulSoup) -> list[Tag]:
        """Find event containers when standard selectors fail.

        Falls back to looking for links to /events/ detail pages
        and returns their parent containers.

        Args:
            soup: Parsed HTML document.

        Returns:
            List of container Tags that likely hold event data.
        """
        containers: list[Tag] = []
        seen_hrefs: set[str] = set()

        for link in soup.select("a[href*='/events/']"):
            href = str(link.get("href", ""))
            # Skip the main listing link itself
            if href in ("/events/pokemon", "/events/"):
                continue
            if href in seen_hrefs:
                continue
            seen_hrefs.add(href)

            # Walk up to find a meaningful container
            parent = link.parent
            while parent and parent.name in ("span", "small"):
                parent = parent.parent
            if parent and parent not in containers:
                containers.append(parent)

        return containers

    def _parse_event_card(self, card: Tag) -> RK9Event | None:
        """Parse an event card/row into an RK9Event.

        Handles multiple possible HTML structures from RK9.

        Args:
            card: BeautifulSoup Tag for the event container.

        Returns:
            RK9Event or None if parsing fails.
        """
        # Find event link and name
        link = card.select_one("a[href*='/events/']")
        if not link:
            return None

        href = str(link.get("href", ""))
        if not href or href in ("/events/pokemon", "/events/"):
            return None

        name = link.get_text(strip=True)
        if not name:
            # Try finding a heading or title element
            title_elem = card.select_one("h2, h3, h4, .event-name, .title")
            if title_elem:
                name = title_elem.get_text(strip=True)
        if not name:
            return None

        source_url = f"{self.BASE_URL}{href}" if href.startswith("/") else href

        # Extract date
        event_date = self._extract_date(card)
        if not event_date:
            return None

        # Extract end date (if range is shown)
        end_date = self._extract_end_date(card)

        # Extract location
        city, venue, country = self._extract_location(card)

        # Extract registration URL
        reg_url = self._extract_registration_url(card)

        # Extract status
        status = self._extract_status(card)

        return RK9Event(
            name=name,
            date=event_date,
            end_date=end_date,
            city=city,
            venue=venue,
            country=country,
            registration_url=reg_url,
            status=status,
            source_url=source_url,
        )

    def _extract_date(self, card: Tag) -> date | None:
        """Extract event date from a card element.

        Args:
            card: BeautifulSoup Tag.

        Returns:
            Parsed date or None.
        """
        # Try data attributes first
        data_date = card.get("data-date") or card.get("data-start-date")
        if data_date:
            try:
                return self._parse_date(str(data_date))
            except ValueError:
                pass

        # Try date-specific elements
        date_elem = card.select_one(".event-date, .date, time, [datetime]")
        if date_elem:
            # Try datetime attribute first
            dt_attr = date_elem.get("datetime")
            if dt_attr:
                try:
                    return self._parse_date(str(dt_attr))
                except ValueError:
                    pass
            # Try text content
            date_text = date_elem.get_text(strip=True)
            if date_text:
                try:
                    return self._parse_date(date_text)
                except ValueError:
                    pass

        # Scan all text for date patterns
        text = card.get_text(" ", strip=True)
        date_match = re.search(r"(\w+ \d{1,2},?\s*\d{4})", text)
        if date_match:
            try:
                return self._parse_date(date_match.group(1))
            except ValueError:
                pass

        # Try ISO format in text
        iso_match = re.search(r"(\d{4}-\d{2}-\d{2})", text)
        if iso_match:
            try:
                return self._parse_date(iso_match.group(1))
            except ValueError:
                pass

        return None

    def _extract_end_date(self, card: Tag) -> date | None:
        """Extract event end date if a date range is shown.

        Args:
            card: BeautifulSoup Tag.

        Returns:
            Parsed end date or None.
        """
        data_end = card.get("data-end-date")
        if data_end:
            try:
                return self._parse_date(str(data_end))
            except ValueError:
                pass

        # Look for date range patterns like "Jan 10 - Jan 12, 2026"
        text = card.get_text(" ", strip=True)
        range_match = re.search(
            r"(\w+ \d{1,2})\s*[-–]\s*(\w+ \d{1,2},?\s*\d{4})",
            text,
        )
        if range_match:
            try:
                return self._parse_date(range_match.group(2))
            except ValueError:
                pass

        return None

    def _extract_location(self, card: Tag) -> tuple[str | None, str | None, str | None]:
        """Extract city, venue, and country from event card.

        Args:
            card: BeautifulSoup Tag.

        Returns:
            Tuple of (city, venue, country).
        """
        city = None
        venue = None
        country = None

        # Try specific location elements
        loc_elem = card.select_one(".event-location, .location, .venue, .address")
        if loc_elem:
            loc_text = loc_elem.get_text(strip=True)
            city, country = self._parse_location_text(loc_text)

        venue_elem = card.select_one(".event-venue, .venue-name")
        if venue_elem:
            venue = venue_elem.get_text(strip=True)

        # If venue not found separately, it may be part of location
        if not venue and loc_elem:
            # Check for nested venue element
            inner_venue = loc_elem.select_one(".venue")
            if inner_venue:
                venue = inner_venue.get_text(strip=True)

        return city, venue, country

    @staticmethod
    def _parse_location_text(
        text: str,
    ) -> tuple[str | None, str | None]:
        """Parse city and country from a location string.

        Handles formats like:
        - "Sacramento, CA, US"
        - "London, United Kingdom"
        - "Sao Paulo, Brazil"

        Args:
            text: Location string.

        Returns:
            Tuple of (city, country).
        """
        if not text:
            return None, None

        parts = [p.strip() for p in text.split(",")]
        city = parts[0] if parts else None

        # Last part is typically country or state abbreviation
        country = parts[-1] if len(parts) >= 2 else None

        return city, country

    def _extract_registration_url(self, card: Tag) -> str | None:
        """Extract registration URL from event card.

        Args:
            card: BeautifulSoup Tag.

        Returns:
            Registration URL or None.
        """
        reg_link = card.select_one(
            "a[href*='register'], "
            "a[href*='registration'], "
            "a.register-btn, "
            "a.registration-link"
        )
        if reg_link:
            href = str(reg_link.get("href", ""))
            if href:
                if href.startswith("/"):
                    return f"{self.BASE_URL}{href}"
                return href
        return None

    def _extract_status(self, card: Tag) -> str:
        """Extract event status from card element.

        Args:
            card: BeautifulSoup Tag.

        Returns:
            Status string (upcoming, registration_open,
            registration_closed, in_progress, completed).
        """
        status_elem = card.select_one(".event-status, .status, .badge, .label")
        if status_elem:
            status_text = status_elem.get_text(strip=True).lower()
            if "open" in status_text:
                return "registration_open"
            if "closed" in status_text:
                return "registration_closed"
            if "progress" in status_text or "live" in status_text:
                return "in_progress"
            if "complete" in status_text or "finished" in status_text:
                return "completed"

        # Check full card text for status indicators
        text = card.get_text(" ", strip=True).lower()
        if "registration open" in text:
            return "registration_open"
        if "registration closed" in text:
            return "registration_closed"
        if "completed" in text:
            return "completed"

        return "upcoming"

    # =================================================================
    # Event Registration Status
    # =================================================================

    async def fetch_event_registration_status(
        self, event_url: str
    ) -> RegistrationStatus:
        """Fetch registration status for a specific event.

        Args:
            event_url: Full URL or path to event detail page.

        Returns:
            RegistrationStatus with available details.

        Raises:
            RK9Error: On fetch or parse errors.
        """
        if event_url.startswith(self.BASE_URL):
            endpoint = event_url[len(self.BASE_URL) :]
        else:
            endpoint = event_url

        html = await self._get(endpoint)
        soup = BeautifulSoup(html, "lxml")

        return self._parse_registration_status(soup)

    def _parse_registration_status(self, soup: BeautifulSoup) -> RegistrationStatus:
        """Parse registration status from event detail page.

        Args:
            soup: Parsed HTML of event detail page.

        Returns:
            RegistrationStatus with available details.
        """
        is_open = False
        opens_at = None
        closes_at = None
        capacity = None
        registered_count = None

        # Check for registration status indicators
        reg_section = soup.select_one(
            ".registration, .registration-info, [class*='registration']"
        )

        page_text = (
            reg_section.get_text(" ", strip=True).lower()
            if reg_section
            else soup.get_text(" ", strip=True).lower()
        )

        if "registration open" in page_text:
            is_open = True
        elif "registration closed" in page_text:
            is_open = False

        # Extract capacity and registered count
        cap_match = re.search(r"capacity[:\s]*(\d+)", page_text)
        if cap_match:
            capacity = int(cap_match.group(1))

        reg_match = re.search(r"registered[:\s]*(\d+)", page_text)
        if not reg_match:
            reg_match = re.search(
                r"(\d+)\s*(?:of\s*\d+\s*)?registered",
                page_text,
            )
        if reg_match:
            registered_count = int(reg_match.group(1))

        # Extract dates from time elements or text
        for time_elem in soup.select("time[datetime], [data-opens], [data-closes]"):
            dt_str = str(
                time_elem.get("datetime")
                or time_elem.get("data-opens")
                or time_elem.get("data-closes")
                or ""
            )
            if not dt_str:
                continue

            try:
                dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                label = time_elem.get_text(strip=True).lower()
                parent_text = ""
                if time_elem.parent:
                    parent_text = time_elem.parent.get_text(strip=True).lower()

                if "open" in label or "open" in parent_text:
                    opens_at = dt
                elif "close" in label or "close" in parent_text:
                    closes_at = dt
            except ValueError:
                continue

        return RegistrationStatus(
            is_open=is_open,
            opens_at=opens_at,
            closes_at=closes_at,
            capacity=capacity,
            registered_count=registered_count,
        )

    # =================================================================
    # Date Parsing
    # =================================================================

    @staticmethod
    def _parse_date(date_str: str) -> date:
        """Parse date from various RK9 formats.

        Args:
            date_str: Date string in various possible formats.

        Returns:
            Parsed date.

        Raises:
            ValueError: If date cannot be parsed.
        """
        date_str = date_str.strip()

        # Handle ISO 8601 with time component
        if "T" in date_str:
            # Strip fractional seconds and timezone suffix
            clean = re.sub(r"[.\d]*[Zz]?$", "", date_str.split("+")[0])
            return datetime.fromisoformat(clean).date()

        formats = [
            "%Y-%m-%d",
            "%B %d, %Y",
            "%B %d %Y",
            "%b %d, %Y",
            "%b %d %Y",
            "%m/%d/%Y",
            "%d/%m/%Y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue

        raise ValueError(f"Could not parse date '{date_str}'")
