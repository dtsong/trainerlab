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
from datetime import date, datetime
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
        formats = [
            "%Y-%m-%d",
            "%B %d, %Y",
            "%b %d, %Y",
            "%d/%m/%Y",
            "%m/%d/%Y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt).date()
            except ValueError:
                continue

        raise ValueError(f"Could not parse date '{date_str}' in any known format")


# Limitless set code to TCGdex set ID mapping
LIMITLESS_SET_MAPPING: dict[str, str] = {
    # Scarlet & Violet era
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
        # Construct URL based on region
        if region == "jp":
            endpoint = f"/tournaments/pokemon/japan?format={game_format}&page={page}"
        else:
            endpoint = f"/tournaments/pokemon?format={game_format}&page={page}"

        html = await self._get(endpoint)
        soup = BeautifulSoup(html, "lxml")

        tournaments: list[LimitlessTournament] = []

        # Find tournament rows
        rows = soup.select("table.striped tbody tr")
        if not rows:
            # Alternative selector
            rows = soup.select(".tournament-list .tournament-row")

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

        Args:
            row: BeautifulSoup Tag for the table row.
            region: Region code.
            game_format: Game format.

        Returns:
            LimitlessTournament or None if parsing fails.
        """
        # Extract tournament link
        link = row.select_one("a[href*='/tournament/']")
        if not link:
            return None

        name = link.get_text(strip=True)
        href = str(link.get("href", ""))
        url = f"{self.BASE_URL}{href}" if href.startswith("/") else href

        # Extract date
        date_cell = row.select_one("td:nth-child(2)")
        date_str = date_cell.get_text(strip=True) if date_cell else ""

        # Extract participant count
        players_cell = row.select_one("td:nth-child(3)")
        players_text = players_cell.get_text(strip=True) if players_cell else "0"
        match = re.search(r"\d+", players_text)
        participant_count = int(match.group()) if match else 0

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

        # Find placement rows
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
