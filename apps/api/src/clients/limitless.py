"""Async HTTP client for Limitless TCG scraping.

Scrapes tournament data from play.limitlesstcg.com including:
- Tournament listings
- Tournament details (placements, player names)
- Decklists when available
"""

import asyncio
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

        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=timeout,
            headers={
                "User-Agent": "TrainerLab/1.0 (Pokemon TCG Meta Analysis)",
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
        """Close the HTTP client."""
        await self._client.aclose()

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
                archetype = archetype_link.get_text(strip=True)
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

        Args:
            decklist_url: Full URL to the decklist page.

        Returns:
            LimitlessDecklist or None if not available.
        """
        if not decklist_url:
            return None

        try:
            # Extract path
            if decklist_url.startswith(self.BASE_URL):
                endpoint = decklist_url[len(self.BASE_URL) :]
            else:
                endpoint = decklist_url

            html = await self._get(endpoint)
            soup = BeautifulSoup(html, "lxml")

            # Find decklist content
            decklist_div = soup.select_one(".decklist-pokemon")
            if not decklist_div:
                decklist_div = soup.select_one("pre.decklist")

            if not decklist_div:
                # Try to find text-based decklist
                decklist_text = soup.select_one(".deck-text, .decklist-text")
                if decklist_text:
                    return self._parse_text_decklist(
                        decklist_text.get_text(), decklist_url
                    )
                return None

            # Parse structured decklist
            cards: list[dict[str, Any]] = []

            # Find all card entries
            card_entries = decklist_div.select(".deck-card, .card-entry")

            for entry in card_entries:
                # Extract quantity
                qty_elem = entry.select_one(".quantity, .card-qty")
                quantity = 1
                if qty_elem:
                    qty_text = qty_elem.get_text(strip=True)
                    try:
                        quantity = int(qty_text)
                    except ValueError:
                        logger.debug(
                            "Could not parse quantity '%s', defaulting to 1",
                            qty_text,
                        )

                # Extract card name and set
                name_elem = entry.select_one(".card-name, .name")
                set_elem = entry.select_one(".card-set, .set")

                if name_elem:
                    name = name_elem.get_text(strip=True)
                    set_code = set_elem.get_text(strip=True) if set_elem else ""

                    # Extract card number from name or separate element
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
                return LimitlessDecklist(cards=cards, source_url=decklist_url)

            # Fallback: try parsing as text
            text_content = decklist_div.get_text("\n", strip=True)
            return self._parse_text_decklist(text_content, decklist_url)

        except LimitlessError:
            logger.warning(f"Could not fetch decklist: {decklist_url}")
            return None

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

    OFFICIAL_BASE_URL = "https://limitlesstcg.com"

    async def _get_official(self, endpoint: str) -> str:
        """Make GET request to official Limitless database.

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
                    # Use absolute URL for official site
                    url = f"{self.OFFICIAL_BASE_URL}{endpoint}"
                    response = await self._client.get(url)

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
            logger.warning(f"Could not find standings table for {tournament_url}")
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

    # =========================================================================
    # Japanese City League (limitlesstcg.com/tournaments/jp)
    # =========================================================================

    async def fetch_jp_city_league_listings(
        self,
        lookback_days: int = 30,
    ) -> list[LimitlessTournament]:
        """Fetch JP City League listings from limitlesstcg.com.

        Japanese City Leagues are listed on a separate page from international
        events, with columns: Date | Prefecture | Shop | Winner.

        Args:
            lookback_days: Only return tournaments from last N days.

        Returns:
            List of JP City League tournament metadata.
        """
        endpoint = "/tournaments/jp"
        html = await self._get_official(endpoint)
        soup = BeautifulSoup(html, "lxml")

        tournaments: list[LimitlessTournament] = []
        cutoff_date = date.today() - timedelta(days=lookback_days)

        # Find table rows — JP page uses a simple table with tournament links
        rows = soup.select("table tr")
        logger.debug(f"Found {len(rows)} rows on JP City League page")

        for row in rows:
            try:
                tournament = self._parse_jp_city_league_row(row, cutoff_date)
                if tournament:
                    tournaments.append(tournament)
            except (ValueError, KeyError, AttributeError) as e:
                logger.warning(f"Error parsing JP City League row: {e}")
                continue

        logger.info(
            f"Found {len(tournaments)} JP City League tournaments "
            f"within {lookback_days} day lookback"
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
            return None
        date_text = date_link.get_text(strip=True)
        if not date_text:
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
