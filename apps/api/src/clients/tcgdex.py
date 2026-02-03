"""Async HTTP client for TCGdex API."""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Self
from urllib.parse import quote

import httpx

from src.config import get_settings

logger = logging.getLogger(__name__)


class TCGdexError(Exception):
    """Exception raised for TCGdex API errors."""

    pass


@dataclass
class TCGdexSetSummary:
    """Summary of a set from the sets list endpoint."""

    id: str
    name: str
    logo: str | None
    symbol: str | None
    card_count_total: int
    card_count_official: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Parse set summary from API response."""
        card_count = data.get("cardCount", {})
        return cls(
            id=data["id"],
            name=data["name"],
            logo=data.get("logo"),
            symbol=data.get("symbol"),
            card_count_total=card_count.get("total", 0),
            card_count_official=card_count.get("official", 0),
        )


@dataclass
class TCGdexCardSummary:
    """Summary of a card from the set endpoint."""

    id: str
    local_id: str
    name: str
    image: str | None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Parse card summary from API response."""
        return cls(
            id=data["id"],
            local_id=data.get("localId", ""),
            name=data["name"],
            image=data.get("image"),
        )


@dataclass
class TCGdexSet:
    """Full set details from the set endpoint."""

    id: str
    name: str
    release_date: date | None
    series_id: str
    series_name: str
    logo: str | None
    symbol: str | None
    card_count_total: int
    card_count_official: int
    legal_standard: bool | None
    legal_expanded: bool | None
    card_summaries: list[TCGdexCardSummary] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Parse set from API response."""
        release_date_str = data.get("releaseDate")
        release_date = None
        if release_date_str:
            try:
                release_date = date.fromisoformat(release_date_str)
            except ValueError:
                logger.warning(f"Invalid release date format: {release_date_str}")

        serie = data.get("serie", {})
        legal = data.get("legal", {})
        card_count = data.get("cardCount", {})
        cards_data = data.get("cards", [])

        return cls(
            id=data["id"],
            name=data["name"],
            release_date=release_date,
            series_id=serie.get("id", ""),
            series_name=serie.get("name", ""),
            logo=data.get("logo"),
            symbol=data.get("symbol"),
            card_count_total=card_count.get("total", 0),
            card_count_official=card_count.get("official", 0),
            legal_standard=legal.get("standard"),
            legal_expanded=legal.get("expanded"),
            card_summaries=[TCGdexCardSummary.from_dict(c) for c in cards_data],
        )


@dataclass
class TCGdexCard:
    """Full card details from the card endpoint."""

    id: str
    local_id: str
    name: str
    supertype: str  # Pokemon, Trainer, Energy
    subtypes: list[str] | None
    types: list[str] | None
    hp: int | None
    stage: str | None
    evolves_from: str | None
    evolves_to: list[str] | None
    attacks: list[dict[str, Any]] | None
    abilities: list[dict[str, Any]] | None
    weaknesses: list[dict[str, Any]] | None
    resistances: list[dict[str, Any]] | None
    retreat_cost: int | None
    rules: list[str] | None
    set_id: str
    rarity: str | None
    number: str | None
    image_small: str | None
    image_large: str | None
    regulation_mark: str | None
    legal_standard: bool | None
    legal_expanded: bool | None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Parse card from API response."""
        # Determine subtypes from various fields
        subtypes = None
        if "suffix" in data:
            subtypes = [data["suffix"]]
        elif "trainerType" in data:
            subtypes = [data["trainerType"]]
        elif "energyType" in data:
            subtypes = [data["energyType"]]

        set_data = data.get("set", {})
        legal = data.get("legal", {})
        image_url = data.get("image")

        return cls(
            id=data["id"],
            local_id=data.get("localId", ""),
            name=data["name"],
            supertype=data.get("category", "Unknown"),
            subtypes=subtypes,
            types=data.get("types"),
            hp=data.get("hp"),
            stage=data.get("stage"),
            evolves_from=data.get("evolvesFrom"),
            evolves_to=data.get("evolvesTo"),
            attacks=data.get("attacks"),
            abilities=data.get("abilities"),
            weaknesses=data.get("weaknesses"),
            resistances=data.get("resistances"),
            retreat_cost=data.get("retreat"),
            rules=data.get("rules"),
            set_id=set_data.get("id", ""),
            rarity=data.get("rarity"),
            number=data.get("localId"),
            image_small=image_url,
            image_large=f"{image_url}/high" if image_url else None,
            regulation_mark=data.get("regulationMark"),
            legal_standard=legal.get("standard"),
            legal_expanded=legal.get("expanded"),
        )


class TCGdexClient:
    """Async HTTP client for TCGdex API."""

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """Initialize TCGdex client.

        Args:
            base_url: TCGdex API base URL. Defaults to config setting.
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retries on rate limit.
            retry_delay: Initial delay between retries (exponential backoff).
        """
        settings = get_settings()
        self._base_url = base_url or settings.tcgdex_url
        self._timeout = timeout
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=timeout,
            headers={"Accept": "application/json"},
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

    async def _get(self, endpoint: str) -> Any:
        """Make GET request with retry logic.

        Args:
            endpoint: API endpoint path.

        Returns:
            JSON response data.

        Raises:
            TCGdexError: On API error after retries exhausted.
        """
        last_error: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                response = await self._client.get(endpoint)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    # Rate limited - retry with exponential backoff
                    delay = self._retry_delay * (2**attempt)
                    logger.warning(
                        f"Rate limited on {endpoint}, retrying in {delay}s "
                        f"(attempt {attempt + 1}/{self._max_retries})"
                    )
                    await asyncio.sleep(delay)
                    last_error = e
                elif e.response.status_code == 404:
                    raise TCGdexError(f"Not found: {endpoint}") from e
                else:
                    raise TCGdexError(
                        f"HTTP error {e.response.status_code} on {endpoint}"
                    ) from e
            except httpx.RequestError as e:
                logger.warning(
                    f"Request error on {endpoint}: {e} "
                    f"(attempt {attempt + 1}/{self._max_retries})"
                )
                last_error = e
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(self._retry_delay * (2**attempt))

        raise TCGdexError(f"Max retries exceeded for {endpoint}") from last_error

    async def fetch_all_sets(self, language: str = "en") -> list[TCGdexSetSummary]:
        """Fetch all card sets.

        Args:
            language: Language code (en, ja, fr, etc.).

        Returns:
            List of set summaries.
        """
        data = await self._get(f"/{language}/sets")
        return [TCGdexSetSummary.from_dict(s) for s in data]

    async def fetch_set(self, set_id: str, language: str = "en") -> TCGdexSet:
        """Fetch a single set with card summaries.

        Args:
            set_id: Set ID (e.g., "swsh1").
            language: Language code.

        Returns:
            Set with card summaries.
        """
        data = await self._get(f"/{language}/sets/{set_id}")
        return TCGdexSet.from_dict(data)

    async def fetch_card(self, card_id: str, language: str = "en") -> TCGdexCard:
        """Fetch a single card with full details.

        Args:
            card_id: Card ID (e.g., "swsh1-1").
            language: Language code.

        Returns:
            Full card details.
        """
        encoded_id = quote(card_id, safe="")
        data = await self._get(f"/{language}/cards/{encoded_id}")
        return TCGdexCard.from_dict(data)

    async def fetch_cards_for_set(
        self,
        set_id: str,
        language: str = "en",
        concurrency: int = 10,
    ) -> list[TCGdexCard]:
        """Fetch all cards for a set.

        Args:
            set_id: Set ID (e.g., "swsh1").
            language: Language code.
            concurrency: Maximum concurrent requests.

        Returns:
            List of full card details.
        """
        # First fetch the set to get card IDs
        tcgdex_set = await self.fetch_set(set_id, language)

        # Fetch each card with limited concurrency
        semaphore = asyncio.Semaphore(concurrency)

        async def fetch_with_semaphore(card_summary: TCGdexCardSummary) -> TCGdexCard:
            async with semaphore:
                return await self.fetch_card(card_summary.id, language)

        tasks = [fetch_with_semaphore(cs) for cs in tcgdex_set.card_summaries]
        cards = await asyncio.gather(*tasks)
        return list(cards)
