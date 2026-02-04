"""Async HTTP client for Limitless TCG scraping.

Scrapes tournament data from play.limitlesstcg.com including:
- Tournament listings
- Tournament details (placements, player names)
- Decklists when available
"""

import asyncio
import contextlib
import logging
import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any, Self

import httpx
from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)


class LimitlessError(Exception):
    """Exception raised for Limitless scraping errors."""

    pass


class LimitlessRateLimitError(LimitlessError):
    """Exception raised when rate limited by Limitless."""

    pass


@dataclass
class LimitlessDecklist:
    """A decklist from Limitless."""

    cards: list[dict[str, Any]] = field(default_factory=list)
    source_url: str | None = None

    @property
    def is_valid(self) -> bool:
        """Check if decklist has valid cards."""
        return len(self.cards) > 0


@dataclass
class LimitlessPlacement:
    """A tournament placement from Limitless."""

    placement: int
    player_name: str | None
    country: str | None
    archetype: str
    decklist: LimitlessDecklist | None = None
    decklist_url: str | None = None


@dataclass
class LimitlessJPCard:
    """A Japanese card from Limitless."""

    card_id: str
    name_jp: str
    name_en: str | None = None
    set_id: str | None = None
    card_type: str | None = None
    is_unreleased: bool = False


@dataclass
class CardEquivalent:
    """Card ID equivalent mapping between JP and EN."""

    jp_card_id: str
    en_card_id: str
    card_name_en: str | None = None
    jp_set_id: str | None = None
    en_set_id: str | None = None


@dataclass
class LimitlessTournament:
    """Tournament data from Limitless."""

    name: str
    tournament_date: date
    region: str
    game_format: str  # "standard" or "expanded"
    best_of: int  # 1 for JP, 3 for international
    participant_count: int
    source_url: str
    placements: list[LimitlessPlacement] = field(default_factory=list)

    @classmethod
    def from_listing(
        cls,
        name: str,
        date_str: str,
        region: str,
        game_format: str,
        participant_count: int,
        url: str,
        best_of: int = 3,
    ) -> Self:
        """Create tournament from listing data."""
        # Parse date (Limitless uses various formats)
        tournament_date = cls._parse_date(date_str)

        return cls(
            name=name,
            tournament_date=tournament_date,
            region=region,
            game_format=game_format.lower(),
            best_of=best_of,
            participant_count=participant_count,
            source_url=url,
        )

    @staticmethod
    def _parse_date(date_str: str) -> date:
        """Parse date from various Limitless formats.

        Args:
            date_str: Date string in various possible formats.

        Returns:
            Parsed date.

        Raises:
            ValueError: If date cannot be parsed in any known format.
        """
        date_str = date_str.strip()

        # Try ISO 8601 format first (2026-02-02T10:00:00.000Z)
        if "T" in date_str:
            try:
                # Handle milliseconds and Z suffix
                clean = date_str.replace("Z", "+00:00")
                if "." in clean:
                    # Remove milliseconds for simpler parsing
                    clean = clean.split(".")[0] + "+00:00"
                return datetime.fromisoformat(clean.replace("+00:00", "")).date()
            except ValueError:
                pass

        formats = [
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%B %d, %Y",
            "%b %d, %Y",
            "%d %b %y",  # 01 Feb 26 (JP City League format)
            "%d/%m/%Y",
            "%m/%d/%Y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue

        raise ValueError(f"Could not parse date '{date_str}' in any known format")


# Limitless set code to TCGdex set ID mapping
LIMITLESS_SET_MAPPING: dict[str, str] = {
    # Mega Evolution era (ME block)
    "ASC": "me02.5",  # Ascended Heroes
    "PFL": "me02",  # Phantasmal Flames
    "MEG": "me01",  # Mega Evolution (base set)
    "MEE": "mee",  # Mega Evolution Energy
    "MEP": "mep",  # Mega Promos
    # Scarlet & Violet era - Main sets
    "BLK": "sv10.5b",  # Black Bolt
    "WHT": "sv10.5w",  # White Flare
    "DRI": "sv10",  # Destined Rivals
    "JTG": "sv09",  # Journey Together
    "PRE": "sv08.5",  # Prismatic Evolutions
    "SSP": "sv08",  # Surging Sparks
    "SCR": "sv7",  # Stellar Crown
    "SFA": "sv6pt5",  # Shrouded Fable
    "TWM": "sv6",  # Twilight Masquerade
    "TEF": "sv5",  # Temporal Forces
    "PAF": "sv4pt5",  # Paldean Fates
    "PAR": "sv4",  # Paradox Rift
    "MEW": "sv3pt5",  # 151
    "OBF": "sv3",  # Obsidian Flames
    "PAL": "sv2",  # Paldea Evolved
    "SVI": "sv1",  # Scarlet & Violet Base
    "SVE": "sve",  # Scarlet & Violet Energy
    "SVP": "svp",  # SV Promos
    # Sword & Shield era (still legal in expanded)
    "CRZ": "swsh12pt5",  # Crown Zenith
    "SIT": "swsh12",  # Silver Tempest
    "LOR": "swsh11",  # Lost Origin
    "PGO": "swsh10pt5",  # Pokemon GO
    "ASR": "swsh10",  # Astral Radiance
    "BRS": "swsh9",  # Brilliant Stars
    "FST": "swsh8",  # Fusion Strike
    "CEL": "swsh7pt5",  # Celebrations
    "EVS": "swsh7",  # Evolving Skies
    "CRE": "swsh6",  # Chilling Reign
    "BST": "swsh5",  # Battle Styles
    "SHF": "swsh4pt5",  # Shining Fates
    "VIV": "swsh4",  # Vivid Voltage
    "CPA": "swsh3pt5",  # Champion's Path
    "DAA": "swsh3",  # Darkness Ablaze
    "RCL": "swsh2",  # Rebel Clash
    "SSH": "swsh1",  # Sword & Shield Base
    "PR": "ssp",  # SW/SH Promos
    # Basic energy
    "ENE": "energy",
    "Energy": "energy",
}


def map_set_code(limitless_code: str) -> str:
    """Map Limitless set code to TCGdex set ID.

    Args:
        limitless_code: Set code from Limitless (e.g., "TWM", "PAR").

    Returns:
        TCGdex set ID (e.g., "sv6", "sv4").
    """
    return LIMITLESS_SET_MAPPING.get(limitless_code, limitless_code.lower())


def parse_card_line(line: str) -> dict[str, Any] | None:
    """Parse a decklist line into card data.

    Limitless uses format: "4 Card Name SET 123"
    Example: "4 Charizard ex OBF 125"

    Args:
        line: A line from the decklist.

    Returns:
        Dict with card_id and quantity, or None if parsing fails.
    """
    line = line.strip()
    if not line:
        return None

    # Match pattern: quantity, name, set code, card number
    # Pattern accounts for various card name formats
    pattern = r"^(\d+)\s+(.+?)\s+([A-Z]{2,4}|Energy)\s+(\d+|[A-Z]+\d*)$"
    match = re.match(pattern, line)

    if not match:
        # Try without card number (basic energy)
        energy_pattern = r"^(\d+)\s+(.+?)\s+(Energy)$"
        energy_match = re.match(energy_pattern, line)
        if energy_match:
            quantity = int(energy_match.group(1))
            name = energy_match.group(2).strip()
            # Basic energy doesn't have a set ID in our system
            return {
                "card_id": f"energy-{name.lower().replace(' ', '-')}",
                "quantity": quantity,
                "name": name,
            }
        return None

    quantity = int(match.group(1))
    name = match.group(2).strip()
    set_code = match.group(3)
    card_number = match.group(4)

    # Map set code to TCGdex format
    tcgdex_set = map_set_code(set_code)
    card_id = f"{tcgdex_set}-{card_number}"

    return {
        "card_id": card_id,
        "quantity": quantity,
        "name": name,
        "set_code": set_code,
        "card_number": card_number,
    }


class LimitlessClient:
    """Async HTTP client for Limitless TCG scraping.

    Implements rate limiting and retry logic to be respectful
    of the Limitless servers.
    """

    BASE_URL = "https://play.limitlesstcg.com"
    OFFICIAL_BASE_URL = "https://limitlesstcg.com"

    def __init__(
        self,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 2.0,
        requests_per_minute: int = 30,
        max_concurrent: int = 5,
    ):
        """Initialize Limitless client.

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
        self._max_concurrent = max_concurrent

        # Rate limiting state
        self._request_times: list[float] = []
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._lock = asyncio.Lock()

        _headers = {
            "User-Agent": "TrainerLab/1.0 (Pokemon TCG Meta Analysis)",
            "Accept": "text/html,application/xhtml+xml",
        }

        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=timeout,
            headers=_headers,
            follow_redirects=True,
        )

        self._official_client = httpx.AsyncClient(
            base_url=self.OFFICIAL_BASE_URL,
            timeout=timeout,
            headers=_headers,
            follow_redirects=True,
        )

    async def __aenter__(self) -> Self:
        """Enter async context."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Exit async context and close client."""
        await self.close()

    async def close(self) -> None:
        """Close HTTP clients."""
        await self._client.aclose()
        await self._official_client.aclose()

    async def _wait_for_rate_limit(self) -> None:
        """Wait if necessary to respect rate limit."""
        async with self._lock:
            now = asyncio.get_running_loop().time()

            # Remove timestamps older than 1 minute
            self._request_times = [t for t in self._request_times if now - t < 60]

            if len(self._request_times) >= self._requests_per_minute:
                # Need to wait
                oldest = self._request_times[0]
                wait_time = 60 - (now - oldest) + 0.1
                if wait_time > 0:
                    logger.info(f"Rate limiting: waiting {wait_time:.1f}s")
                    await asyncio.sleep(wait_time)

            self._request_times.append(now)

    async def _get(self, endpoint: str) -> str:
        """Make GET request with rate limiting and retries.

        Args:
            endpoint: URL path.

        Returns:
            HTML response content.

        Raises:
            LimitlessError: On error after retries exhausted.
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
                            f"Rate limited (429) on {endpoint}, "
                            f"retrying in {delay}s (attempt {attempt + 1})"
                        )
                        await asyncio.sleep(delay)
                        last_error = LimitlessRateLimitError("Rate limited")
                        continue

                    if response.status_code == 503:
                        delay = self._retry_delay * (2**attempt)
                        logger.warning(
                            f"Service unavailable (503) on {endpoint}, "
                            f"retrying in {delay}s"
                        )
                        await asyncio.sleep(delay)
                        last_error = LimitlessError("Service unavailable")
                        continue

                    response.raise_for_status()
                    return response.text

                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 404:
                        raise LimitlessError(f"Not found: {endpoint}") from e
                    last_error = e
                    delay = self._retry_delay * (2**attempt)
                    logger.warning(
                        f"HTTP error {e.response.status_code} on {endpoint}, "
                        f"retrying in {delay}s"
                    )
                    await asyncio.sleep(delay)

                except httpx.RequestError as e:
                    last_error = e
                    delay = self._retry_delay * (2**attempt)
                    logger.warning(
                        f"Request error on {endpoint}: {e}, retrying in {delay}s"
                    )
                    await asyncio.sleep(delay)

            raise LimitlessError(f"Max retries exceeded for {endpoint}") from last_error

    async def fetch_tournament_listings(
        self,
        region: str = "en",
        game_format: str = "standard",
        page: int = 1,
    ) -> list[LimitlessTournament]:
        """Fetch tournament listings from the tournaments page.

        Args:
            region: Region code ("en", "jp", "eu", etc.).
            game_format: Game format ("standard", "expanded").
            page: Page number (1-indexed).

        Returns:
            List of tournament metadata (without placements).
        """
        # Construct URL based on region - use /completed for finished tournaments
        base = "/tournaments/completed?game=PTCG"
        if region == "jp":
            endpoint = f"{base}&region=JP&format={game_format}&page={page}"
        else:
            endpoint = f"{base}&format={game_format}&page={page}"

        html = await self._get(endpoint)
        soup = BeautifulSoup(html, "lxml")

        tournaments: list[LimitlessTournament] = []

        # Find tournament rows - Limitless tables may or may not have tbody
        # Try multiple selectors in order of specificity
        rows = soup.select("table tbody tr")
        if not rows:
            rows = soup.select("table tr")
        if not rows:
            rows = soup.select(".tournament-list .tournament-row")

        logger.debug(f"Found {len(rows)} tournament rows on page {page}")

        for row in rows:
            try:
                tournament = self._parse_tournament_row(row, region, game_format)
                if tournament:
                    tournaments.append(tournament)
            except (ValueError, KeyError, AttributeError) as e:
                logger.warning(
                    "Error parsing tournament row: %s",
                    e,
                    exc_info=True,
                )
                continue

        return tournaments

    def _parse_tournament_row(
        self, row: Tag, region: str, game_format: str
    ) -> LimitlessTournament | None:
        """Parse a tournament row from the listings page.

        Handles multiple Limitless table formats:
        - Upcoming: Date | Name | Organizer | Registration
        - Completed: Name | Organizer | Players | Winner

        Args:
            row: BeautifulSoup Tag for the table row.
            region: Region code.
            game_format: Game format.

        Returns:
            LimitlessTournament or None if parsing fails.
        """
        # Skip header rows or empty rows
        cells = row.select("td")
        if not cells:
            return None

        # Find all tournament links (multiple may exist - icon link, name link, etc.)
        links = row.select("a[href*='/tournament/']")
        if not links:
            return None

        # Find the link with actual text (the tournament name)
        # First link might be an icon/image for upcoming tournaments
        name = ""
        href = ""
        for link in links:
            link_text = link.get_text(strip=True)
            if link_text:
                name = link_text
                href = str(link.get("href", ""))
                break

        if not name:
            return None

        if not href or "/tournament/" not in href:
            # Use first link's href if we found a name but not a valid href
            href = str(links[0].get("href", ""))
            if not href or "/tournament/" not in href:
                return None

        url = f"{self.BASE_URL}{href}" if href.startswith("/") else href

        # Extract date from multiple possible sources
        date_str = ""

        # Try a.date or a.time elements (Limitless uses these for localization)
        date_elem = row.select_one("a.date, a.time")
        if date_elem:
            date_text = date_elem.get_text(strip=True)
            # Try parsing the text first
            if date_text:
                date_str = date_text

        # If no date element found, check data attributes on the row
        if not date_str:
            data_date = row.get("data-date")
            if data_date:
                date_str = str(data_date)

        # Fallback: use today's date for completed tournaments
        if not date_str:
            date_str = date.today().isoformat()
            logger.debug(f"No date found for tournament '{name}', using today's date")

        # Extract participant count - look for standalone numbers in cells
        participant_count = 0
        for cell in cells:
            cell_text = cell.get_text(strip=True)
            # Skip if it contains links (not a player count cell)
            if cell.select_one("a"):
                continue
            # Look for standalone numeric content
            if cell_text.isdigit():
                participant_count = int(cell_text)
                break

        # If not found, try to find any number in the row
        if participant_count == 0:
            for cell in cells:
                cell_text = cell.get_text(strip=True)
                # Skip cells with links or date patterns
                if cell.select_one("a") or re.match(r"\d{4}-\d{2}-\d{2}", cell_text):
                    continue
                match = re.search(r"(\d+)", cell_text)
                if match:
                    participant_count = int(match.group(1))
                    break

        # Determine best_of based on region
        best_of = 1 if region == "jp" else 3

        # Normalize region code
        region_map = {
            "en": None,  # Global/mixed
            "na": "NA",
            "eu": "EU",
            "jp": "JP",
            "latam": "LATAM",
            "oce": "OCE",
        }
        normalized_region = region_map.get(region.lower(), region.upper())

        return LimitlessTournament.from_listing(
            name=name,
            date_str=date_str,
            region=normalized_region or "NA",
            game_format=game_format,
            participant_count=participant_count,
            url=url,
            best_of=best_of,
        )

    async def fetch_tournament_placements(
        self,
        tournament_url: str,
        max_placements: int = 32,
    ) -> list[LimitlessPlacement]:
        """Fetch placements for a tournament.

        Args:
            tournament_url: Full URL to the tournament page.
            max_placements: Maximum number of placements to fetch.

        Returns:
            List of placements with archetypes.
        """
        # Extract tournament path from URL
        if tournament_url.startswith(self.BASE_URL):
            endpoint = tournament_url[len(self.BASE_URL) :]
        else:
            endpoint = tournament_url

        # Ensure we're fetching standings
        if "/standings" not in endpoint:
            endpoint = f"{endpoint}/standings"

        html = await self._get(endpoint)
        soup = BeautifulSoup(html, "lxml")

        placements: list[LimitlessPlacement] = []

        # Find placement rows — Limitless uses "table.standings"
        rows = soup.select("table.standings tbody tr")
        if not rows:
            rows = soup.select("table.standings tr")
        if not rows:
            rows = soup.select("table.striped tbody tr")
        if not rows:
            rows = soup.select(".standings-row")

        for row in rows[:max_placements]:
            try:
                placement = self._parse_placement_row(row)
                if placement:
                    placements.append(placement)
            except (ValueError, KeyError, AttributeError) as e:
                logger.warning(
                    "Error parsing placement row: %s",
                    e,
                    exc_info=True,
                )
                continue

        return placements

    def _parse_placement_row(self, row: Tag) -> LimitlessPlacement | None:
        """Parse a placement row from the standings page.

        Args:
            row: BeautifulSoup Tag for the table row.

        Returns:
            LimitlessPlacement or None if parsing fails.
        """
        cells = row.select("td")
        if len(cells) < 3:
            return None

        # Extract placement number
        placement_text = cells[0].get_text(strip=True)
        placement_match = re.search(r"\d+", placement_text)
        if not placement_match:
            return None
        placement = int(placement_match.group())

        # Extract player name
        player_cell = cells[1]
        player_link = player_cell.select_one("a")
        player_name = (
            player_link.get_text(strip=True)
            if player_link
            else player_cell.get_text(strip=True)
        )

        # Extract country flag (if present)
        flag = player_cell.select_one("img.flag, .flag")
        country: str | None = None
        if flag:
            alt_val = flag.get("alt")
            if isinstance(alt_val, str):
                country = alt_val

        # Extract archetype
        archetype_cell = cells[2] if len(cells) > 2 else None
        archetype = "Unknown"
        decklist_url: str | None = None

        if archetype_cell:
            archetype_link = archetype_cell.select_one("a")
            if archetype_link:
                archetype = archetype_link.get_text(strip=True) or "Unknown"
                href = str(archetype_link.get("href", ""))
                if href and "/decks/" in href:
                    decklist_url = (
                        f"{self.BASE_URL}{href}" if href.startswith("/") else href
                    )
            else:
                archetype_text = archetype_cell.get_text(strip=True)
                if archetype_text:
                    archetype = archetype_text

        return LimitlessPlacement(
            placement=placement,
            player_name=player_name if player_name else None,
            country=country,
            archetype=archetype,
            decklist_url=decklist_url,
        )

    async def fetch_decklist(self, decklist_url: str) -> LimitlessDecklist | None:
        """Fetch a decklist from its URL.

        Handles two page formats:
        - Official site (limitlesstcg.com): card images with quantity PNGs
        - Play site (play.limitlesstcg.com): text-based or structured HTML

        Args:
            decklist_url: Full URL to the decklist page.

        Returns:
            LimitlessDecklist or None if not available.
        """
        if not decklist_url:
            return None

        try:
            # Route to the correct fetcher based on domain
            is_official = self.OFFICIAL_BASE_URL in decklist_url
            if is_official:
                endpoint = decklist_url.replace(self.OFFICIAL_BASE_URL, "")
                html = await self._get_official(endpoint)
            elif decklist_url.startswith(self.BASE_URL):
                endpoint = decklist_url[len(self.BASE_URL) :]
                html = await self._get(endpoint)
            else:
                html = await self._get(decklist_url)

            soup = BeautifulSoup(html, "lxml")

            has_card_links = bool(soup.select("a[href*='/cards/']"))
            logger.info(
                "fetch_decklist %s: html_length=%d, has_card_links=%s",
                decklist_url,
                len(html),
                has_card_links,
            )

            # Try official site format first: <a href="/cards/SET/NUM">
            # with quantity encoded in image src (decklist/N.png)
            result = self._parse_official_decklist(soup, decklist_url)
            if result:
                return result

            # Try play site format: structured divs
            result = self._parse_play_decklist(soup, decklist_url)
            if result:
                return result

            # Fallback: text-based decklist
            text_content = soup.get_text("\n", strip=True)
            result = self._parse_text_decklist(text_content, decklist_url)
            if result:
                return result

            # All parsers failed — log diagnostic info
            page_title = soup.title.string if soup.title else "(no title)"
            logger.warning(
                "All decklist parsers failed for %s — title=%r, "
                "first 500 chars: %.500s",
                decklist_url,
                page_title,
                html,
            )
            return None

        except LimitlessError:
            logger.warning("Could not fetch decklist: %s", decklist_url)
            return None

    def _parse_official_decklist(
        self, soup: BeautifulSoup, source_url: str
    ) -> LimitlessDecklist | None:
        """Parse a decklist from the official Limitless site.

        Official site uses image-based layout:
        <a href="/cards/SET/NUMBER">
            <img alt="CardName" src="...card image...">
            <img src=".../decklist/QUANTITY.png">
        </a>

        Args:
            soup: Parsed HTML.
            source_url: URL where the decklist was found.

        Returns:
            LimitlessDecklist or None if format doesn't match.
        """
        cards: list[dict[str, Any]] = []

        # Find all card links matching /cards/SET/NUMBER
        card_links = soup.select("a[href^='/cards/']")
        if not card_links:
            # Fallback: handles absolute hrefs (e.g. https://limitlesstcg.com/cards/...)
            card_links = soup.select("a[href*='/cards/']")
        if not card_links:
            page_title = soup.title.string if soup.title else "(no title)"
            logger.warning(
                "No card links found in official decklist — title=%r, url=%s",
                page_title,
                source_url,
            )
            return None

        for link in card_links:
            href = str(link.get("href", ""))
            # Parse /cards/SET/NUMBER
            card_match = re.match(r"/cards/([A-Za-z0-9]+)/(\d+)", href)
            if not card_match:
                continue

            set_code = card_match.group(1)
            card_number = card_match.group(2)

            # Extract quantity from the decklist image src
            quantity = 1
            imgs = link.select("img")
            for img in imgs:
                src = str(img.get("src", ""))
                qty_match = re.search(r"/decklist/(\d+)\.png", src)
                if qty_match:
                    quantity = int(qty_match.group(1))
                    break

            # Extract card name from alt text of card image
            name = ""
            for img in imgs:
                alt = img.get("alt")
                if alt and "decklist" not in str(img.get("src", "")):
                    name = str(alt)
                    break

            tcgdex_set = map_set_code(set_code)
            card_id = f"{tcgdex_set}-{card_number}"
            cards.append(
                {
                    "card_id": card_id,
                    "quantity": quantity,
                    "name": name,
                    "set_code": set_code,
                    "card_number": card_number,
                }
            )

        if cards:
            logger.info(
                "Parsed official decklist: %d unique cards from %s",
                len(cards),
                source_url,
            )
            return LimitlessDecklist(cards=cards, source_url=source_url)
        return None

    def _parse_play_decklist(
        self, soup: BeautifulSoup, source_url: str
    ) -> LimitlessDecklist | None:
        """Parse a decklist from the play.limitlesstcg.com site.

        Play site uses structured HTML with CSS classes for card entries.

        Args:
            soup: Parsed HTML.
            source_url: URL where the decklist was found.

        Returns:
            LimitlessDecklist or None if format doesn't match.
        """
        decklist_div = soup.select_one(".decklist-pokemon")
        if not decklist_div:
            decklist_div = soup.select_one("pre.decklist")
        if not decklist_div:
            decklist_text = soup.select_one(".deck-text, .decklist-text")
            if decklist_text:
                return self._parse_text_decklist(decklist_text.get_text(), source_url)
            return None

        cards: list[dict[str, Any]] = []
        card_entries = decklist_div.select(".deck-card, .card-entry")

        for entry in card_entries:
            qty_elem = entry.select_one(".quantity, .card-qty")
            quantity = 1
            if qty_elem:
                qty_text = qty_elem.get_text(strip=True)
                with contextlib.suppress(ValueError):
                    quantity = int(qty_text)

            name_elem = entry.select_one(".card-name, .name")
            set_elem = entry.select_one(".card-set, .set")

            if name_elem:
                name = name_elem.get_text(strip=True)
                set_code = set_elem.get_text(strip=True) if set_elem else ""
                number_match = re.search(r"(\d+)$", name)
                card_number = number_match.group(1) if number_match else ""

                if set_code and card_number:
                    tcgdex_set = map_set_code(set_code)
                    card_id = f"{tcgdex_set}-{card_number}"
                    cards.append(
                        {
                            "card_id": card_id,
                            "quantity": quantity,
                            "name": name,
                        }
                    )

        if cards:
            return LimitlessDecklist(cards=cards, source_url=source_url)

        text_content = decklist_div.get_text("\n", strip=True)
        return self._parse_text_decklist(text_content, source_url)

    def _parse_text_decklist(
        self, text: str, source_url: str
    ) -> LimitlessDecklist | None:
        """Parse a text-format decklist.

        Args:
            text: Raw decklist text.
            source_url: URL where the decklist was found.

        Returns:
            LimitlessDecklist or None if parsing fails.
        """
        cards: list[dict[str, Any]] = []

        for line in text.split("\n"):
            card = parse_card_line(line)
            if card:
                cards.append(card)

        if cards:
            return LimitlessDecklist(cards=cards, source_url=source_url)
        return None

    # =========================================================================
    # Official Tournament Database (limitlesstcg.com)
    # =========================================================================

    async def _get_official(self, endpoint: str) -> str:
        """Make GET request to official Limitless database.

        Uses a dedicated httpx client with base_url pointed at the official
        site so that cookies, connection pooling, and redirect handling all
        work correctly (as opposed to passing absolute URLs through the
        play-site client).

        Args:
            endpoint: URL path (e.g., "/tournaments").

        Returns:
            HTML response content.
        """
        async with self._semaphore:
            last_error: Exception | None = None

            for attempt in range(self._max_retries):
                await self._wait_for_rate_limit()

                try:
                    response = await self._official_client.get(endpoint)

                    if response.status_code == 429:
                        delay = self._retry_delay * (2**attempt)
                        logger.warning(
                            f"Rate limited (429) on official {endpoint}, "
                            f"retrying in {delay}s"
                        )
                        await asyncio.sleep(delay)
                        last_error = LimitlessRateLimitError("Rate limited")
                        continue

                    response.raise_for_status()
                    return response.text

                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 404:
                        raise LimitlessError(f"Not found: {endpoint}") from e
                    last_error = e
                    delay = self._retry_delay * (2**attempt)
                    await asyncio.sleep(delay)

                except httpx.RequestError as e:
                    last_error = e
                    delay = self._retry_delay * (2**attempt)
                    await asyncio.sleep(delay)

            raise LimitlessError(
                f"Max retries exceeded for official {endpoint}"
            ) from last_error

    async def fetch_official_tournament_listings(
        self,
        game_format: str = "standard",
    ) -> list[LimitlessTournament]:
        """Fetch official tournament listings from limitlesstcg.com.

        This fetches major competitive events (Regionals, ICs, Champions League)
        from the main Limitless database, which is separate from the grassroots
        tournament platform.

        Args:
            game_format: Game format ("standard", "expanded").

        Returns:
            List of official tournament metadata.
        """
        endpoint = "/tournaments"
        html = await self._get_official(endpoint)
        soup = BeautifulSoup(html, "lxml")

        tournaments: list[LimitlessTournament] = []

        # Find completed tournaments table
        table = soup.select_one("table.completed-tournaments")
        if not table:
            logger.warning("Could not find completed-tournaments table")
            return tournaments

        rows = table.select("tr[data-date]")
        logger.debug(f"Found {len(rows)} official tournament rows")

        for row in rows:
            try:
                tournament = self._parse_official_tournament_row(row, game_format)
                if tournament:
                    tournaments.append(tournament)
            except (ValueError, KeyError, AttributeError) as e:
                logger.warning(f"Error parsing official tournament row: {e}")
                continue

        return tournaments

    def _parse_official_tournament_row(
        self, row: Tag, target_format: str
    ) -> LimitlessTournament | None:
        """Parse an official tournament row from limitlesstcg.com.

        Args:
            row: BeautifulSoup Tag for the table row.
            target_format: Target game format to filter by.

        Returns:
            LimitlessTournament or None if parsing fails or format doesn't match.
        """
        # Extract data attributes
        date_str = row.get("data-date")
        country = row.get("data-country")
        name = row.get("data-name")
        row_format = row.get("data-format")
        players_str = row.get("data-players")

        if not all([date_str, name, row_format]):
            return None

        # Filter by format (standard, expanded, standard-jp)
        format_lower = str(row_format).lower()
        standard_formats = ("standard", "standard-jp")
        if target_format == "standard" and format_lower not in standard_formats:
            return None
        if target_format == "expanded" and format_lower != "expanded":
            return None

        # Extract tournament URL
        link = row.select_one("td a[href^='/tournaments/']")
        if not link:
            return None
        href = str(link.get("href", ""))
        url = f"{self.OFFICIAL_BASE_URL}{href}"

        # Parse values
        participant_count = int(str(players_str)) if players_str else 0

        # Determine region from country code
        region = self._country_to_region(str(country) if country else "")

        # Determine best_of (JP uses BO1)
        best_of = 1 if format_lower == "standard-jp" or country == "JP" else 3

        return LimitlessTournament.from_listing(
            name=str(name),
            date_str=str(date_str),
            region=region,
            game_format="standard" if "standard" in format_lower else format_lower,
            participant_count=participant_count,
            url=url,
            best_of=best_of,
        )

    def _country_to_region(self, country: str) -> str:
        """Map country code to region.

        Args:
            country: ISO country code (e.g., "US", "JP", "GB").

        Returns:
            Region code (NA, EU, JP, LATAM, OCE).
        """
        na_countries = {"US", "CA"}
        eu_countries = {
            "GB",
            "DE",
            "FR",
            "IT",
            "ES",
            "NL",
            "BE",
            "AT",
            "CH",
            "PL",
            "SE",
            "NO",
            "DK",
            "FI",
            "PT",
            "IE",
            "CZ",
            "HU",
            "RO",
            "GR",
        }
        latam_countries = {"MX", "BR", "AR", "CL", "CO", "PE", "EC", "VE"}
        oce_countries = {"AU", "NZ"}
        jp_countries = {"JP"}
        asia_countries = {"KR", "TW", "SG", "MY", "TH", "PH", "ID"}

        if country in jp_countries:
            return "JP"
        if country in na_countries:
            return "NA"
        if country in eu_countries:
            return "EU"
        if country in latam_countries:
            return "LATAM"
        if country in oce_countries:
            return "OCE"
        if country in asia_countries:
            return "APAC"

        # Default to NA for unknown
        return "NA"

    async def fetch_official_tournament_placements(
        self,
        tournament_url: str,
        max_placements: int = 64,
    ) -> list[LimitlessPlacement]:
        """Fetch placements for an official tournament.

        Args:
            tournament_url: Full URL to the tournament page on limitlesstcg.com.
            max_placements: Maximum number of placements to fetch.

        Returns:
            List of placements with archetypes.
        """
        # Extract path from URL
        if tournament_url.startswith(self.OFFICIAL_BASE_URL):
            endpoint = tournament_url[len(self.OFFICIAL_BASE_URL) :]
        else:
            endpoint = tournament_url

        html = await self._get_official(endpoint)
        soup = BeautifulSoup(html, "lxml")

        placements: list[LimitlessPlacement] = []

        # Find standings table - official site uses class "standings"
        table = soup.select_one("table.standings, table.striped")
        if not table:
            # Fallback: first <table> with 3+ rows containing <td> cells
            for candidate in soup.select("table"):
                data_rows = [tr for tr in candidate.select("tr") if tr.select("td")]
                if len(data_rows) >= 3:
                    table = candidate
                    logger.info(
                        "Using fallback table (%d data rows) for %s",
                        len(data_rows),
                        tournament_url,
                    )
                    break
        if not table:
            page_title = soup.title.string if soup.title else "(no title)"
            table_count = len(soup.select("table"))
            logger.warning(
                "No standings table found for %s — title=%r, tables_on_page=%d",
                tournament_url,
                page_title,
                table_count,
            )
            return placements

        rows = table.select("tbody tr")
        if not rows:
            rows = table.select("tr")[1:]  # Skip header row

        for row in rows[:max_placements]:
            try:
                placement = self._parse_official_placement_row(row)
                if placement:
                    placements.append(placement)
            except (ValueError, KeyError, AttributeError) as e:
                logger.warning(f"Error parsing official placement row: {e}")
                continue

        return placements

    def _parse_official_placement_row(self, row: Tag) -> LimitlessPlacement | None:
        """Parse a placement row from an official tournament page.

        Args:
            row: BeautifulSoup Tag for the table row.

        Returns:
            LimitlessPlacement or None if parsing fails.
        """
        cells = row.select("td")
        if len(cells) < 3:
            return None

        # Extract placement (first cell)
        placement_text = cells[0].get_text(strip=True)
        placement_match = re.search(r"\d+", placement_text)
        if not placement_match:
            return None
        placement = int(placement_match.group())

        # Extract player name (second cell usually)
        player_cell = cells[1]
        player_link = player_cell.select_one("a")
        player_name = (
            player_link.get_text(strip=True)
            if player_link
            else player_cell.get_text(strip=True)
        )

        # Extract country from flag image
        flag = player_cell.select_one("img.flag")
        country = str(flag.get("alt", "")) if flag else None

        # Extract archetype (usually 3rd or later cell with deck link)
        archetype = "Unknown"
        decklist_url: str | None = None

        for cell in cells[2:]:
            deck_link = cell.select_one("a[href*='/decks/']")
            if deck_link:
                archetype = deck_link.get_text(strip=True)
                # JP pages use Pokemon images instead of text
                if not archetype:
                    archetype = self._extract_archetype_from_images(deck_link)
                href = str(deck_link.get("href", ""))
                if href:
                    decklist_url = (
                        f"{self.OFFICIAL_BASE_URL}{href}"
                        if href.startswith("/")
                        else href
                    )
                break

        # If no deck link, try to get archetype from cell text
        if archetype == "Unknown" and len(cells) > 2:
            archetype_text = cells[2].get_text(strip=True)
            if archetype_text:
                archetype = archetype_text

        return LimitlessPlacement(
            placement=placement,
            player_name=player_name if player_name else None,
            country=country,
            archetype=archetype,
            decklist_url=decklist_url,
        )

    @staticmethod
    def _extract_archetype_from_images(link_tag: Tag) -> str:
        """Extract archetype name from Pokemon images inside a link.

        JP tournament pages show Pokemon card images instead of text labels.
        This extracts names from ``<img alt="PokemonName">`` or from the
        image filename (e.g. ``.../grimmsnarl.png``).

        Args:
            link_tag: An ``<a>`` tag that may contain ``<img>`` children.

        Returns:
            Archetype string like ``"Grimmsnarl / Froslass"`` or
            ``"Unknown"`` if no names could be extracted.
        """
        names: list[str] = []
        for img in link_tag.select("img"):
            alt = img.get("alt")
            if isinstance(alt, str) and alt.strip():
                names.append(alt.strip())
                continue
            # Fallback: extract from filename
            src = str(img.get("src", ""))
            filename_match = re.search(r"/([a-zA-Z_-]+)\.png", src)
            if filename_match:
                raw = filename_match.group(1)
                # Convert filenames like "grimmsnarl" → "Grimmsnarl"
                name = raw.replace("-", " ").replace("_", " ").title()
                names.append(name)
        if names:
            return " / ".join(names)
        return "Unknown"

    # =========================================================================
    # Japanese City League (limitlesstcg.com/tournaments/jp)
    # =========================================================================

    async def fetch_jp_city_league_listings(
        self,
        lookback_days: int = 90,
        max_pages: int = 10,
    ) -> list[LimitlessTournament]:
        """Fetch JP City League listings from limitlesstcg.com.

        Japanese City Leagues are listed on a separate page from international
        events, with columns: Date | Prefecture | Shop | Winner.

        Paginates through results using ``?show=100&page=N`` until all pages
        are exhausted or all rows on a page fall outside the lookback window.

        Args:
            lookback_days: Only return tournaments from last N days.
            max_pages: Maximum number of pages to fetch.

        Returns:
            List of JP City League tournament metadata.
        """
        tournaments: list[LimitlessTournament] = []
        cutoff_date = date.today() - timedelta(days=lookback_days)
        logger.info(
            "JP City League: cutoff_date=%s, max_pages=%d", cutoff_date, max_pages
        )

        for page in range(1, max_pages + 1):
            endpoint = f"/tournaments/jp?show=100&page={page}"
            html = await self._get_official(endpoint)
            soup = BeautifulSoup(html, "lxml")

            # Find table rows — JP page uses a simple table with tournament links
            rows = soup.select("table tr")
            logger.info("Page %d: found %d table rows", page, len(rows))

            if not rows:
                logger.info("Page %d: no rows found, stopping pagination", page)
                break

            page_tournaments: list[LimitlessTournament] = []
            all_past_cutoff = True
            skipped_no_cells = 0
            skipped_no_link = 0
            skipped_no_date = 0
            skipped_past_cutoff = 0
            parse_errors = 0

            for row in rows:
                try:
                    tournament = self._parse_jp_city_league_row(row, cutoff_date)
                    if tournament:
                        page_tournaments.append(tournament)
                        all_past_cutoff = False
                    else:
                        # Count skip reasons from row structure
                        cells = row.select("td")
                        if len(cells) < 3:
                            skipped_no_cells += 1
                        elif not row.select_one("a[href*='/tournaments/jp/']"):
                            skipped_no_link += 1
                        else:
                            # Has cells and link — likely date issue
                            date_link = cells[0].select_one("a")
                            if date_link:
                                date_text = date_link.get_text(strip=True)
                                try:
                                    parsed = LimitlessTournament._parse_date(date_text)
                                    if parsed < cutoff_date:
                                        skipped_past_cutoff += 1
                                    else:
                                        skipped_no_date += 1
                                except ValueError:
                                    skipped_no_date += 1
                            else:
                                skipped_no_date += 1
                except (ValueError, KeyError, AttributeError) as e:
                    parse_errors += 1
                    logger.warning("Error parsing JP City League row: %s", e)
                    continue

            tournaments.extend(page_tournaments)

            logger.info(
                "Page %d: parsed=%d, past_cutoff=%d, no_cells=%d, "
                "no_link=%d, no_date=%d, errors=%d",
                page,
                len(page_tournaments),
                skipped_past_cutoff,
                skipped_no_cells,
                skipped_no_link,
                skipped_no_date,
                parse_errors,
            )

            # Stop paginating if every row on this page was older than cutoff
            if all_past_cutoff:
                logger.info(
                    "Page %d: no tournaments within cutoff, stopping pagination",
                    page,
                )
                break

        logger.info(
            "JP City League total: %d tournaments within %d day lookback",
            len(tournaments),
            lookback_days,
        )
        return tournaments

    def _parse_jp_city_league_row(
        self, row: Tag, cutoff_date: date
    ) -> LimitlessTournament | None:
        """Parse a row from the JP City League listings page.

        Columns: Date | Prefecture | Shop | Winner

        Args:
            row: BeautifulSoup Tag for the table row.
            cutoff_date: Earliest date to include.

        Returns:
            LimitlessTournament or None if parsing fails or too old.
        """
        cells = row.select("td")
        if len(cells) < 3:
            return None

        # Find tournament link — pattern: /tournaments/jp/[ID]
        link = row.select_one("a[href*='/tournaments/jp/']")
        if not link:
            return None
        href = str(link.get("href", ""))
        if not href:
            return None

        url = f"{self.OFFICIAL_BASE_URL}{href}" if href.startswith("/") else href

        # Extract date from first cell link text (format: "01 Feb 26")
        date_link = cells[0].select_one("a")
        if not date_link:
            logger.debug("JP row: no date link in first cell for %s", url)
            return None
        date_text = date_link.get_text(strip=True)
        if not date_text:
            logger.debug("JP row: empty date text for %s", url)
            return None

        tournament_date = LimitlessTournament._parse_date(date_text)
        if tournament_date < cutoff_date:
            return None

        # Extract prefecture from second cell
        prefecture = cells[1].get_text(strip=True) if len(cells) > 1 else ""

        # Build tournament name: "City League {Prefecture}"
        name = f"City League {prefecture}" if prefecture else "City League"

        return LimitlessTournament.from_listing(
            name=name,
            date_str=date_text,
            region="JP",
            game_format="standard",
            participant_count=0,  # JP listings don't show player count
            url=url,
            best_of=1,  # JP uses BO1
        )

    async def fetch_jp_city_league_placements(
        self,
        tournament_url: str,
        max_placements: int = 32,
    ) -> list[LimitlessPlacement]:
        """Fetch placements for a JP City League tournament.

        Uses the same parsing as official tournaments since the detail
        page structure is similar (rank | player | deck).

        Args:
            tournament_url: Full URL (e.g. limitlesstcg.com/tournaments/jp/3954).
            max_placements: Maximum placements to fetch.

        Returns:
            List of placements.
        """
        # Reuse the official tournament placement parser — same page structure
        return await self.fetch_official_tournament_placements(
            tournament_url, max_placements
        )

    # =========================================================================
    # Japanese Card Data (limitlesstcg.com/cards/jp)
    # =========================================================================

    async def fetch_unreleased_cards(
        self,
        translate: bool = True,
    ) -> list[LimitlessJPCard]:
        """Fetch Japanese cards not yet released internationally.

        Args:
            translate: If True, include English translations where available.

        Returns:
            List of unreleased JP cards.
        """
        endpoint = "/cards/jp"
        params = "?q=is:unreleased"
        if translate:
            params += "&translate=en"

        html = await self._get_official(f"{endpoint}{params}")
        return self._parse_card_list(html, f"{self.OFFICIAL_BASE_URL}{endpoint}")

    async def fetch_set_cards(
        self,
        set_code: str,
        translate: bool = True,
    ) -> list[LimitlessJPCard]:
        """Fetch all cards from a specific Japanese set.

        Args:
            set_code: JP set code (e.g., "SV10", "SVIP").
            translate: If True, include English translations where available.

        Returns:
            List of cards from the set.
        """
        endpoint = f"/cards/jp/{set_code}"
        params = "?translate=en" if translate else ""

        html = await self._get_official(f"{endpoint}{params}")
        return self._parse_card_list(html, f"{self.OFFICIAL_BASE_URL}{endpoint}")

    def _parse_card_list(self, html: str, source_url: str) -> list[LimitlessJPCard]:
        """Parse a card list page from Limitless.

        Args:
            html: Raw HTML content.
            source_url: URL where the content was fetched.

        Returns:
            List of parsed JP cards.
        """
        soup = BeautifulSoup(html, "lxml")
        cards: list[LimitlessJPCard] = []

        card_elements = soup.select(".card-item, .card, [data-card-id]")
        if not card_elements:
            card_elements = soup.select("table tr[data-card]")

        for elem in card_elements:
            card = self._parse_card_element(elem)
            if card:
                cards.append(card)

        if not cards:
            cards = self._parse_card_table(soup)

        logger.info("Parsed %d cards from %s", len(cards), source_url)
        return cards

    def _parse_card_element(self, elem: Tag) -> LimitlessJPCard | None:
        """Parse a single card element.

        Args:
            elem: BeautifulSoup Tag for the card element.

        Returns:
            LimitlessJPCard or None if parsing fails.
        """
        card_id = elem.get("data-card-id")
        if not card_id:
            link = elem.select_one("a[href*='/cards/']")
            if link:
                href = str(link.get("href", ""))
                match = re.search(r"/cards/(?:jp/)?([^/]+)/(\d+)", href)
                if match:
                    card_id = f"{match.group(1)}-{match.group(2)}"

        if not card_id:
            return None

        name_jp_elem = elem.select_one(".card-name-jp, .name-jp, [data-name-jp]")
        name_jp = ""
        if name_jp_elem:
            name_jp = name_jp_elem.get("data-name-jp") or name_jp_elem.get_text(
                strip=True
            )
            if isinstance(name_jp, list):
                name_jp = name_jp[0] if name_jp else ""
        if not name_jp:
            name_elem = elem.select_one(".card-name, .name")
            if name_elem:
                name_jp = name_elem.get_text(strip=True)

        name_en_elem = elem.select_one(".card-name-en, .name-en, [data-name-en]")
        name_en = None
        if name_en_elem:
            name_en = name_en_elem.get("data-name-en") or name_en_elem.get_text(
                strip=True
            )
            if isinstance(name_en, list):
                name_en = name_en[0] if name_en else None

        set_id = None
        set_elem = elem.select_one(".card-set, .set, [data-set]")
        if set_elem:
            set_id = set_elem.get("data-set") or set_elem.get_text(strip=True)
            if isinstance(set_id, list):
                set_id = set_id[0] if set_id else None

        card_type = None
        type_elem = elem.select_one(".card-type, .type, [data-type]")
        if type_elem:
            card_type = type_elem.get("data-type") or type_elem.get_text(strip=True)
            if isinstance(card_type, list):
                card_type = card_type[0] if card_type else None

        is_unreleased = bool(
            elem.select_one(".unreleased, .jp-only")
            or "unreleased" in str(elem.get("class", []))
        )

        return LimitlessJPCard(
            card_id=str(card_id),
            name_jp=str(name_jp) if name_jp else "",
            name_en=str(name_en) if name_en else None,
            set_id=str(set_id) if set_id else None,
            card_type=str(card_type) if card_type else None,
            is_unreleased=is_unreleased,
        )

    def _parse_card_table(self, soup: BeautifulSoup) -> list[LimitlessJPCard]:
        """Parse cards from a table layout.

        Args:
            soup: Parsed HTML document.

        Returns:
            List of parsed JP cards.
        """
        cards: list[LimitlessJPCard] = []

        tables = soup.select("table")
        for table in tables:
            headers = table.select("th")
            col_map: dict[str, int] = {}

            for i, header in enumerate(headers):
                text = header.get_text(strip=True).lower()
                if "name" in text or "カード" in text:
                    col_map["name"] = i
                elif "set" in text or "セット" in text:
                    col_map["set"] = i
                elif "type" in text or "タイプ" in text:
                    col_map["type"] = i
                elif "en" in text or "英語" in text:
                    col_map["name_en"] = i

            rows = table.select("tr")
            for row in rows[1:]:
                cells = row.select("td")
                if not cells:
                    continue

                link = row.select_one("a[href*='/cards/']")
                card_id = None
                if link:
                    href = str(link.get("href", ""))
                    match = re.search(r"/cards/(?:jp/)?([^/]+)/(\d+)", href)
                    if match:
                        card_id = f"{match.group(1)}-{match.group(2)}"

                if not card_id:
                    continue

                name_idx = col_map.get("name", 0)
                name_jp = ""
                if name_idx < len(cells):
                    name_jp = cells[name_idx].get_text(strip=True)

                name_en = None
                if "name_en" in col_map and col_map["name_en"] < len(cells):
                    name_en = cells[col_map["name_en"]].get_text(strip=True)

                set_id = None
                if "set" in col_map and col_map["set"] < len(cells):
                    set_id = cells[col_map["set"]].get_text(strip=True)

                card_type = None
                if "type" in col_map and col_map["type"] < len(cells):
                    card_type = cells[col_map["type"]].get_text(strip=True)

                cards.append(
                    LimitlessJPCard(
                        card_id=card_id,
                        name_jp=name_jp,
                        name_en=name_en if name_en else None,
                        set_id=set_id if set_id else None,
                        card_type=card_type if card_type else None,
                        is_unreleased=True,
                    )
                )

        return cards

    # =========================================================================
    # Card ID Equivalents (JP <-> EN mappings)
    # =========================================================================

    async def fetch_card_equivalents(
        self,
        jp_set_id: str,
    ) -> list[CardEquivalent]:
        """Fetch JP-to-EN card ID mappings for a Japanese set.

        Scrapes each card's detail page to extract the "Int. Prints" section
        which lists equivalent English card IDs.

        Args:
            jp_set_id: Japanese set code (e.g., "SV7", "SV7a").

        Returns:
            List of CardEquivalent mappings.
        """
        equivalents: list[CardEquivalent] = []

        jp_cards = await self.fetch_set_cards(jp_set_id, translate=True)
        logger.info(
            "Fetching equivalents for %d cards in JP set %s", len(jp_cards), jp_set_id
        )

        for card in jp_cards:
            try:
                card_equiv = await self._fetch_single_card_equivalent(
                    card.card_id, jp_set_id, card.name_en
                )
                if card_equiv:
                    equivalents.append(card_equiv)
            except LimitlessError as e:
                logger.warning("Error fetching equivalent for %s: %s", card.card_id, e)
                continue

        logger.info(
            "Found %d card equivalents for JP set %s", len(equivalents), jp_set_id
        )
        return equivalents

    async def _fetch_single_card_equivalent(
        self,
        jp_card_id: str,
        jp_set_id: str,
        card_name_en: str | None = None,
    ) -> CardEquivalent | None:
        """Fetch EN equivalent for a single JP card.

        Parses the card detail page at /cards/jp/{SET}/{NUMBER} to find
        the "Int. Prints" section containing English equivalents.

        Args:
            jp_card_id: Japanese card ID (e.g., "SV7-18").
            jp_set_id: Japanese set ID.
            card_name_en: English card name if known.

        Returns:
            CardEquivalent or None if no EN equivalent found.
        """
        parts = jp_card_id.split("-")
        if len(parts) < 2:
            return None
        card_number = parts[-1]

        endpoint = f"/cards/jp/{jp_set_id}/{card_number}"
        try:
            html = await self._get_official(endpoint)
        except LimitlessError:
            return None

        soup = BeautifulSoup(html, "lxml")
        en_card_id = self._parse_international_prints(soup)

        if not en_card_id:
            return None

        en_set_id = en_card_id.split("-")[0] if "-" in en_card_id else None

        return CardEquivalent(
            jp_card_id=jp_card_id,
            en_card_id=en_card_id,
            card_name_en=card_name_en,
            jp_set_id=jp_set_id,
            en_set_id=en_set_id,
        )

    def _parse_international_prints(self, soup: BeautifulSoup) -> str | None:
        """Parse the International Prints section from a JP card page.

        The page structure includes a section like:
        <div class="prints">
            <h3>Int. Prints</h3>
            <a href="/cards/SCR/28">SCR 28</a>
        </div>

        Args:
            soup: Parsed HTML of the card detail page.

        Returns:
            First EN card ID found (e.g., "SCR-28") or None.
        """
        prints_sections = soup.select(".prints, .card-prints, [class*='print']")

        for section in prints_sections:
            header = section.select_one("h3, h4, .section-title")
            if header:
                header_text = header.get_text(strip=True).lower()
                if "int" in header_text or "english" in header_text:
                    links = section.select("a[href*='/cards/']")
                    for link in links:
                        href = str(link.get("href", ""))
                        en_match = re.search(r"/cards/([A-Z]+)/(\d+)", href)
                        if en_match:
                            set_code = en_match.group(1)
                            number = en_match.group(2)
                            tcgdex_set = map_set_code(set_code)
                            return f"{tcgdex_set}-{number}"

        all_links = soup.select("a[href*='/cards/']")
        for link in all_links:
            href = str(link.get("href", ""))
            if "/cards/jp/" in href:
                continue
            en_match = re.search(r"/cards/([A-Z]{2,4})/(\d+)", href)
            if en_match:
                set_code = en_match.group(1)
                number = en_match.group(2)
                tcgdex_set = map_set_code(set_code)
                return f"{tcgdex_set}-{number}"

        return None

    async def fetch_jp_sets(self) -> list[str]:
        """Fetch list of available Japanese set codes.

        Returns:
            List of JP set codes (e.g., ["SV7", "SV7a", "SV6"]).
        """
        endpoint = "/cards/jp"
        html = await self._get_official(endpoint)
        soup = BeautifulSoup(html, "lxml")

        set_codes: list[str] = []

        set_links = soup.select("a[href*='/cards/jp/']")
        for link in set_links:
            href = str(link.get("href", ""))
            match = re.search(r"/cards/jp/([A-Za-z0-9]+)/?$", href)
            if match:
                set_code = match.group(1).upper()
                if set_code not in set_codes:
                    set_codes.append(set_code)

        logger.info("Found %d JP sets", len(set_codes))
        return set_codes
