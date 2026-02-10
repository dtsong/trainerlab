"""Async HTTP client for Pokemon official events.

Scrapes Pokemon TCG championship event data from the official
Pokemon events site including:
- Regional Championships schedule
- International Championships and Worlds
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


class PokemonEventsError(Exception):
    """Exception raised for Pokemon Events scraping errors."""


class PokemonEventsRateLimitError(PokemonEventsError):
    """Exception raised when rate limited."""


@dataclass
class PokemonEvent:
    """An official Pokemon TCG championship event."""

    name: str
    date: date
    end_date: date | None = None
    city: str | None = None
    country: str | None = None
    region: str | None = None
    venue: str | None = None
    registration_url: str | None = None
    source_url: str = ""
    tier: str = "regional"


class PokemonEventsClient:
    """Async HTTP client for official Pokemon events.

    Scrapes the Pokemon championships site for event schedules.
    Uses conservative rate limiting (10 req/min) since events
    change infrequently.
    """

    BASE_URL = "https://www.pokemon.com"
    EVENTS_PATH = "/en/play-pokemon/pokemon-events"

    def __init__(
        self,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 2.0,
        requests_per_minute: int = 10,
        max_concurrent: int = 2,
    ):
        """Initialize Pokemon Events client.

        Args:
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retries on errors.
            retry_delay: Initial delay between retries.
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
                    logger.info(
                        "Pokemon Events rate limiting: waiting %.1fs",
                        wait_time,
                    )
                    await asyncio.sleep(wait_time)

            self._request_times.append(now)

    async def _get(self, endpoint: str) -> str:
        """Make GET request with rate limiting and retries.

        Args:
            endpoint: URL path.

        Returns:
            HTML response content.

        Raises:
            PokemonEventsError: On error after retries exhausted.
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
                            "Pokemon Events rate limited (429) "
                            "on %s, retrying in %.1fs "
                            "(attempt %d)",
                            endpoint,
                            delay,
                            attempt + 1,
                        )
                        await asyncio.sleep(delay)
                        last_error = PokemonEventsRateLimitError("Rate limited")
                        continue

                    if response.status_code == 503:
                        delay = self._retry_delay * (2**attempt)
                        logger.warning(
                            "Pokemon Events unavailable (503) on %s, retrying in %.1fs",
                            endpoint,
                            delay,
                        )
                        await asyncio.sleep(delay)
                        last_error = PokemonEventsError("Service unavailable")
                        continue

                    response.raise_for_status()
                    return response.text

                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 404:
                        raise PokemonEventsError(f"Not found: {endpoint}") from e
                    last_error = e
                    delay = self._retry_delay * (2**attempt)
                    logger.warning(
                        "Pokemon Events HTTP error %d on %s, retrying in %.1fs",
                        e.response.status_code,
                        endpoint,
                        delay,
                    )
                    await asyncio.sleep(delay)

                except httpx.RequestError as e:
                    last_error = e
                    delay = self._retry_delay * (2**attempt)
                    logger.warning(
                        "Pokemon Events request error on %s: %s, retrying in %.1fs",
                        endpoint,
                        e,
                        delay,
                    )
                    await asyncio.sleep(delay)

            raise PokemonEventsError(
                f"Max retries exceeded for {endpoint}"
            ) from last_error

    # =================================================================
    # Regional Championships
    # =================================================================

    async def fetch_regional_championships(
        self,
    ) -> list[PokemonEvent]:
        """Fetch Regional Championship schedule.

        Scrapes the official Pokemon events page for Regional
        Championship listings.

        Returns:
            List of Regional Championship events.
        """
        endpoint = f"{self.EVENTS_PATH}/pokemon-regionals-pokemon-tcg"
        try:
            html = await self._get(endpoint)
        except PokemonEventsError:
            logger.warning("Failed to fetch regionals page")
            return []

        soup = BeautifulSoup(html, "lxml")
        events = self._parse_event_listings(soup, tier="regional")

        logger.info("Fetched %d Regional Championships", len(events))
        return events

    # =================================================================
    # International Championships & Worlds
    # =================================================================

    async def fetch_international_championships(
        self,
    ) -> list[PokemonEvent]:
        """Fetch International Championship and Worlds schedule.

        Scrapes the official Pokemon events page for IC and
        Worlds listings.

        Returns:
            List of IC/Worlds events.
        """
        endpoint = f"{self.EVENTS_PATH}/pokemon-internationals-pokemon-tcg"
        try:
            html = await self._get(endpoint)
        except PokemonEventsError:
            logger.warning("Failed to fetch ICs page")
            return []

        soup = BeautifulSoup(html, "lxml")
        events = self._parse_event_listings(soup, tier="international")

        # Also try to find Worlds
        worlds_endpoint = f"{self.EVENTS_PATH}/pokemon-worlds"
        try:
            worlds_html = await self._get(worlds_endpoint)
            worlds_soup = BeautifulSoup(worlds_html, "lxml")
            worlds_events = self._parse_event_listings(worlds_soup, tier="worlds")
            events.extend(worlds_events)
        except PokemonEventsError:
            logger.warning("No separate Worlds page found")

        logger.info(
            "Fetched %d International Championships/Worlds",
            len(events),
        )
        return events

    # =================================================================
    # All Events
    # =================================================================

    async def fetch_all_events(self) -> list[PokemonEvent]:
        """Fetch all official championship events.

        Combines Regional Championships, ICs, and Worlds into
        a single list.

        Returns:
            Combined list of all official events.
        """
        regionals, internationals = await asyncio.gather(
            self.fetch_regional_championships(),
            self.fetch_international_championships(),
            return_exceptions=True,
        )

        events: list[PokemonEvent] = []

        if isinstance(regionals, list):
            events.extend(regionals)
        else:
            logger.warning(
                "Failed to fetch regionals: %s",
                regionals,
                exc_info=regionals,
            )

        if isinstance(internationals, list):
            events.extend(internationals)
        else:
            logger.warning(
                "Failed to fetch internationals: %s",
                internationals,
                exc_info=internationals,
            )

        return events

    # =================================================================
    # Parsing
    # =================================================================

    def _parse_event_listings(
        self, soup: BeautifulSoup, tier: str = "regional"
    ) -> list[PokemonEvent]:
        """Parse event listings from a Pokemon events page.

        Handles multiple possible HTML structures used by the
        Pokemon website.

        Args:
            soup: Parsed HTML document.
            tier: Event tier to assign (regional, international,
                  worlds).

        Returns:
            List of parsed PokemonEvent objects.
        """
        events: list[PokemonEvent] = []

        # Try structured event containers
        containers = soup.select(
            ".event-card, .event-listing, "
            ".schedule-item, [class*='event-item'], "
            ".event-info, article.event"
        )

        if not containers:
            # Fallback: look for sections with date + location
            containers = self._find_event_sections(soup)

        for container in containers:
            try:
                event = self._parse_event_container(container, tier)
                if event:
                    events.append(event)
            except (ValueError, KeyError, AttributeError):
                logger.warning(
                    "Error parsing Pokemon event",
                    exc_info=True,
                )
                continue

        return events

    def _find_event_sections(self, soup: BeautifulSoup) -> list[Tag]:
        """Find event sections using fallback heuristics.

        Looks for sections containing both date-like and
        location-like content.

        Args:
            soup: Parsed HTML document.

        Returns:
            List of Tags that likely contain event info.
        """
        sections: list[Tag] = []

        # Look for heading + content patterns
        for heading in soup.select("h2, h3, h4"):
            text = heading.get_text(strip=True).lower()
            if any(
                kw in text
                for kw in (
                    "regional",
                    "international",
                    "championship",
                    "worlds",
                )
            ):
                # Get the parent section or next siblings
                parent = heading.parent
                if parent and parent.name in (
                    "div",
                    "section",
                    "article",
                ):
                    sections.append(parent)

        # Also look for table rows with event data
        for row in soup.select("table tr"):
            cells = row.select("td")
            if len(cells) >= 2:
                text = row.get_text(" ", strip=True)
                if re.search(r"\d{4}", text) and re.search(r"[A-Z][a-z]+ \d", text):
                    sections.append(row)

        return sections

    def _parse_event_container(self, container: Tag, tier: str) -> PokemonEvent | None:
        """Parse a single event from its container element.

        Args:
            container: BeautifulSoup Tag for the event.
            tier: Event tier to assign.

        Returns:
            PokemonEvent or None if parsing fails.
        """
        # Extract event name
        name = self._extract_name(container)
        if not name:
            return None

        # Extract date
        event_date = self._extract_date(container)
        if not event_date:
            return None

        # Extract end date
        end_date = self._extract_end_date(container)

        # Extract location
        city, country, region = self._extract_location(container)

        # Extract venue
        venue = self._extract_venue(container)

        # Extract registration/detail URL
        source_url, reg_url = self._extract_urls(container)

        # Infer tier from name if not explicitly set
        inferred_tier = self._infer_tier(name, tier)

        return PokemonEvent(
            name=name,
            date=event_date,
            end_date=end_date,
            city=city,
            country=country,
            region=region,
            venue=venue,
            registration_url=reg_url,
            source_url=source_url,
            tier=inferred_tier,
        )

    def _extract_name(self, container: Tag) -> str | None:
        """Extract event name from container.

        Args:
            container: BeautifulSoup Tag.

        Returns:
            Event name or None.
        """
        # Try heading elements
        for selector in (
            "h2",
            "h3",
            "h4",
            ".event-name",
            ".title",
            "a",
        ):
            elem = container.select_one(selector)
            if elem:
                text = elem.get_text(strip=True)
                if text and len(text) > 3:
                    return text
        return None

    def _extract_date(self, container: Tag) -> date | None:
        """Extract event date from container.

        Args:
            container: BeautifulSoup Tag.

        Returns:
            Parsed date or None.
        """
        # Try data attributes
        for attr in ("data-date", "data-start-date"):
            val = container.get(attr)
            if val:
                try:
                    return self._parse_date(str(val))
                except ValueError:
                    pass

        # Try time/date elements
        for elem in container.select("time[datetime], .date, .event-date"):
            dt_attr = elem.get("datetime")
            if dt_attr:
                try:
                    return self._parse_date(str(dt_attr))
                except ValueError:
                    pass
            text = elem.get_text(strip=True)
            if text:
                try:
                    return self._parse_date(text)
                except ValueError:
                    pass

        # Scan text for date patterns
        text = container.get_text(" ", strip=True)
        # "January 10, 2026" or "Jan 10, 2026"
        date_match = re.search(r"(\w+ \d{1,2},?\s*\d{4})", text)
        if date_match:
            try:
                return self._parse_date(date_match.group(1))
            except ValueError:
                pass

        # ISO format
        iso_match = re.search(r"(\d{4}-\d{2}-\d{2})", text)
        if iso_match:
            try:
                return self._parse_date(iso_match.group(1))
            except ValueError:
                pass

        return None

    def _extract_end_date(self, container: Tag) -> date | None:
        """Extract event end date from container.

        Args:
            container: BeautifulSoup Tag.

        Returns:
            Parsed end date or None.
        """
        val = container.get("data-end-date")
        if val:
            try:
                return self._parse_date(str(val))
            except ValueError:
                pass

        # Date range pattern
        text = container.get_text(" ", strip=True)
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

    def _extract_location(
        self, container: Tag
    ) -> tuple[str | None, str | None, str | None]:
        """Extract city, country, and region from container.

        Args:
            container: BeautifulSoup Tag.

        Returns:
            Tuple of (city, country, region).
        """
        city = None
        country = None
        region = None

        loc_elem = container.select_one(".location, .event-location, .venue, .address")
        if loc_elem:
            loc_text = loc_elem.get_text(strip=True)
            city, country = self._parse_location_text(loc_text)

        # Infer region from country
        if country:
            region = self._country_to_region(country)

        # Check name for region hints
        if not region:
            name_text = container.get_text(" ", strip=True).lower()
            if "europe" in name_text or "euic" in name_text:
                region = "EU"
            elif "latin" in name_text or "laic" in name_text:
                region = "LATAM"
            elif "oceania" in name_text or "oce" in name_text:
                region = "OCE"
            elif "north america" in name_text:
                region = "NA"
            elif "japan" in name_text:
                region = "JP"

        return city, country, region

    def _extract_venue(self, container: Tag) -> str | None:
        """Extract venue name from container.

        Args:
            container: BeautifulSoup Tag.

        Returns:
            Venue name or None.
        """
        venue_elem = container.select_one(".venue, .venue-name, .event-venue")
        if venue_elem:
            return venue_elem.get_text(strip=True)
        return None

    def _extract_urls(self, container: Tag) -> tuple[str, str | None]:
        """Extract source URL and registration URL.

        Args:
            container: BeautifulSoup Tag.

        Returns:
            Tuple of (source_url, registration_url).
        """
        source_url = ""
        reg_url = None

        # Find event detail link
        detail_link = container.select_one("a[href*='event'], a[href*='championship']")
        if detail_link:
            href = str(detail_link.get("href", ""))
            if href:
                source_url = f"{self.BASE_URL}{href}" if href.startswith("/") else href

        # Find registration link
        reg_link = container.select_one(
            "a[href*='register'], a[href*='registration'], a[href*='rk9']"
        )
        if reg_link:
            href = str(reg_link.get("href", ""))
            if href:
                reg_url = f"{self.BASE_URL}{href}" if href.startswith("/") else href

        # Fallback: use first link as source URL
        if not source_url:
            first_link = container.select_one("a[href]")
            if first_link:
                href = str(first_link.get("href", ""))
                if href and href.startswith(("http", "/")):
                    source_url = (
                        f"{self.BASE_URL}{href}" if href.startswith("/") else href
                    )

        return source_url, reg_url

    # =================================================================
    # Helpers
    # =================================================================

    @staticmethod
    def _infer_tier(name: str, default: str) -> str:
        """Infer event tier from its name.

        Args:
            name: Event name.
            default: Default tier if inference fails.

        Returns:
            Tier string.
        """
        lower = name.lower()
        if "worlds" in lower or "world championship" in lower:
            return "worlds"
        if "international" in lower:
            return "international"
        if "regional" in lower:
            return "regional"
        if "special" in lower or "special event" in lower:
            return "special"
        return default

    @staticmethod
    def _parse_location_text(
        text: str,
    ) -> tuple[str | None, str | None]:
        """Parse city and country from location string.

        Args:
            text: Location text.

        Returns:
            Tuple of (city, country).
        """
        if not text:
            return None, None

        parts = [p.strip() for p in text.split(",")]
        city = parts[0] if parts else None
        country = parts[-1] if len(parts) >= 2 else None

        return city, country

    @staticmethod
    def _country_to_region(country: str) -> str | None:
        """Map country to Pokemon TCG region.

        Args:
            country: Country name or code.

        Returns:
            Region code or None.
        """
        country_lower = country.lower().strip()

        na = {
            "us",
            "usa",
            "united states",
            "canada",
            "ca",
        }
        eu = {
            "uk",
            "gb",
            "united kingdom",
            "germany",
            "de",
            "france",
            "fr",
            "italy",
            "it",
            "spain",
            "es",
            "netherlands",
            "nl",
            "belgium",
            "be",
            "austria",
            "at",
            "switzerland",
            "ch",
            "poland",
            "pl",
            "sweden",
            "se",
            "norway",
            "no",
            "denmark",
            "dk",
            "finland",
            "fi",
            "portugal",
            "pt",
            "ireland",
            "ie",
            "czech republic",
            "cz",
        }
        latam = {
            "brazil",
            "br",
            "mexico",
            "mx",
            "argentina",
            "ar",
            "chile",
            "cl",
            "colombia",
            "co",
            "peru",
            "pe",
        }
        oce = {
            "australia",
            "au",
            "new zealand",
            "nz",
        }
        jp = {"japan", "jp"}

        if country_lower in na:
            return "NA"
        if country_lower in eu:
            return "EU"
        if country_lower in latam:
            return "LATAM"
        if country_lower in oce:
            return "OCE"
        if country_lower in jp:
            return "JP"
        return None

    @staticmethod
    def _parse_date(date_str: str) -> date:
        """Parse date from various formats.

        Args:
            date_str: Date string.

        Returns:
            Parsed date.

        Raises:
            ValueError: If date cannot be parsed.
        """
        date_str = date_str.strip()

        # Handle ISO 8601 with time
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
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue

        # Handle ambiguous slash-separated dates.
        # Prefer %m/%d/%Y (US format, typical for Pokemon events).
        # Fall back to %d/%m/%Y when month value exceeds 12.
        slash_match = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})$", date_str)
        if slash_match:
            a, b = int(slash_match.group(1)), int(slash_match.group(2))
            if a <= 12:
                return datetime.strptime(date_str, "%m/%d/%Y").date()
            if b <= 12:
                return datetime.strptime(date_str, "%d/%m/%Y").date()

        raise ValueError(f"Could not parse date '{date_str}'")
