"""Async HTTP client for Pokecabook scraping.

Scrapes Japanese Pokemon TCG meta data from pokecabook.com including:
- Tier lists and rankings
- Card adoption rates
- Articles about the JP meta
"""

import asyncio
import logging
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Self

import httpx
from bs4 import BeautifulSoup, Tag

from src.clients.retry_policy import (
    DEFAULT_MAX_RETRIES,
    DEFAULT_RETRY_DELAY_SECONDS,
    DEFAULT_TIMEOUT_SECONDS,
    backoff_delay_seconds,
    classify_status,
    is_retryable_status,
)

logger = logging.getLogger(__name__)


class PokecabookError(Exception):
    """Exception raised for Pokecabook scraping errors."""


class PokecabookRateLimitError(PokecabookError):
    """Exception raised when rate limited by Pokecabook."""


@dataclass
class PokecabookArticle:
    """An article from Pokecabook."""

    url: str
    title: str
    category: str | None = None
    published_date: date | None = None
    excerpt: str | None = None
    raw_html: str | None = None


@dataclass
class PokecabookTierEntry:
    """A single tier list entry."""

    archetype_name: str
    archetype_name_en: str | None = None
    tier: str = "unknown"
    usage_rate: float | None = None
    trend: str | None = None
    representative_cards: list[str] = field(default_factory=list)


@dataclass
class PokecabookTierList:
    """A complete tier list from Pokecabook."""

    date: date
    entries: list[PokecabookTierEntry] = field(default_factory=list)
    source_url: str | None = None
    raw_html: str | None = None


@dataclass
class PokecabookAdoptionEntry:
    """A card's adoption rate data."""

    card_name_jp: str
    inclusion_rate: float
    card_name_en: str | None = None
    avg_copies: float | None = None
    archetype: str | None = None


@dataclass
class PokecabookAdoptionRates:
    """Card adoption rates from Pokecabook."""

    date: date
    entries: list[PokecabookAdoptionEntry] = field(default_factory=list)
    source_url: str | None = None
    raw_html: str | None = None


class PokecabookClient:
    """Async HTTP client for Pokecabook scraping.

    Implements rate limiting and retry logic. Conservative 10 req/min
    to be respectful of their servers.
    """

    BASE_URL = "https://pokecabook.com"

    def __init__(
        self,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY_SECONDS,
        requests_per_minute: int = 10,
        max_concurrent: int = 2,
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
                "User-Agent": "TrainerLab/1.0 (Pokemon TCG Meta Analysis)",
                "Accept": "text/html,application/xhtml+xml",
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
                    logger.info("Pokecabook rate limiting: waiting %.1fs", wait_time)
                    await asyncio.sleep(wait_time)

            self._request_times.append(now)

    async def _get(self, endpoint: str) -> str:
        async with self._semaphore:
            last_error: Exception | None = None

            for attempt in range(self._max_retries):
                await self._wait_for_rate_limit()

                try:
                    response = await self._client.get(endpoint)

                    if response.status_code == 404:
                        raise PokecabookError(f"Not found: {endpoint}")

                    if is_retryable_status(response.status_code):
                        delay = backoff_delay_seconds(self._retry_delay, attempt)
                        logger.warning(
                            "pokecabook_retry status=%d category=%s endpoint=%s "
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
                            last_error = PokecabookRateLimitError("Rate limited")
                        else:
                            last_error = PokecabookError(
                                f"Transient HTTP {response.status_code}"
                            )
                        continue

                    response.raise_for_status()
                    return response.text

                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 404:
                        raise PokecabookError(f"Not found: {endpoint}") from e
                    if is_retryable_status(e.response.status_code):
                        delay = backoff_delay_seconds(self._retry_delay, attempt)
                        logger.warning(
                            "pokecabook_retry exception_status=%d category=%s "
                            "endpoint=%s attempt=%d/%d delay=%.2fs",
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
                    raise PokecabookError(
                        f"HTTP error {e.response.status_code} on {endpoint}"
                    ) from e

                except httpx.RequestError as e:
                    last_error = e
                    delay = backoff_delay_seconds(self._retry_delay, attempt)
                    logger.warning(
                        "pokecabook_retry request_error=%s endpoint=%s "
                        "attempt=%d/%d delay=%.2fs",
                        type(e).__name__,
                        endpoint,
                        attempt + 1,
                        self._max_retries,
                        delay,
                    )
                    await asyncio.sleep(delay)

            raise PokecabookError(
                f"Max retries exceeded for {endpoint}"
            ) from last_error

    async def fetch_recent_articles(
        self,
        category: str | None = None,
        days: int = 30,
    ) -> list[PokecabookArticle]:
        """Fetch recent articles from Pokecabook.

        Args:
            category: Optional category filter (e.g., "tier", "deck").
            days: Only include articles from last N days.

        Returns:
            List of article metadata.
        """
        endpoint = f"/category/{category}/" if category else "/category/pokeca-article/"

        html = await self._get(endpoint)
        soup = BeautifulSoup(html, "lxml")

        articles: list[PokecabookArticle] = []
        cutoff_date = date.today() - __import__("datetime").timedelta(days=days)

        article_elements = soup.select("article, .post-item, .entry-card")

        for elem in article_elements:
            try:
                article = self._parse_article_element(elem)
                if article:
                    in_range = (
                        article.published_date and article.published_date >= cutoff_date
                    )
                    if in_range or not article.published_date:
                        articles.append(article)
            except (ValueError, AttributeError) as e:
                logger.warning("Error parsing Pokecabook article: %s", e)
                continue

        return articles

    def _parse_article_element(self, elem: Tag) -> PokecabookArticle | None:
        link = elem.select_one("a[href]")
        if not link:
            return None

        href = str(link.get("href", ""))
        if not href or self.BASE_URL not in href and not href.startswith("/"):
            return None

        url = href if href.startswith("http") else f"{self.BASE_URL}{href}"

        title_elem = elem.select_one("h2, h3, .entry-title, .post-title")
        title = title_elem.get_text(strip=True) if title_elem else ""
        if not title:
            title = link.get_text(strip=True)

        if not title:
            return None

        date_elem = elem.select_one("time, .post-date, .entry-date")
        published_date = None
        if date_elem:
            datetime_attr = date_elem.get("datetime")
            if datetime_attr:
                published_date = self._parse_datetime_attr(datetime_attr)
            if not published_date:
                date_text = date_elem.get_text(strip=True)
                published_date = self._parse_jp_date(date_text)

        excerpt_elem = elem.select_one(".excerpt, .entry-summary, p")
        excerpt = excerpt_elem.get_text(strip=True) if excerpt_elem else None

        category_elem = elem.select_one(".category, .cat-label")
        category = category_elem.get_text(strip=True) if category_elem else None

        return PokecabookArticle(
            url=url,
            title=title,
            category=category,
            published_date=published_date,
            excerpt=excerpt,
        )

    def _parse_jp_date(self, date_text: str) -> date | None:
        formats = [
            "%Y年%m月%d日",
            "%Y/%m/%d",
            "%Y-%m-%d",
            "%m月%d日",
        ]

        for fmt in formats:
            try:
                parsed = datetime.strptime(date_text.strip(), fmt)
                if parsed.year < 2000:
                    parsed = parsed.replace(year=date.today().year)
                return parsed.date()
            except ValueError:
                continue

        return None

    def _parse_datetime_attr(
        self, datetime_attr: str | list[str] | None
    ) -> date | None:
        if not datetime_attr:
            return None
        try:
            return datetime.fromisoformat(
                str(datetime_attr).replace("Z", "+00:00")
            ).date()
        except ValueError:
            return None

    async def fetch_article_detail(self, url: str) -> PokecabookArticle:
        """Fetch full article content.

        Args:
            url: Full URL to the article.

        Returns:
            Article with raw_html populated.
        """
        endpoint = url[len(self.BASE_URL) :] if url.startswith(self.BASE_URL) else url

        html = await self._get(endpoint)
        soup = BeautifulSoup(html, "lxml")

        title_elem = soup.select_one("h1, .entry-title, .post-title")
        title = title_elem.get_text(strip=True) if title_elem else "Untitled"

        date_elem = soup.select_one("time, .post-date, .entry-date")
        published_date = None
        if date_elem:
            datetime_attr = date_elem.get("datetime")
            if datetime_attr:
                published_date = self._parse_datetime_attr(datetime_attr)

        return PokecabookArticle(
            url=url,
            title=title,
            published_date=published_date,
            raw_html=html,
        )

    async def fetch_tier_list(self) -> PokecabookTierList:
        """Fetch the current tier list.

        Returns:
            Current tier list with entries.
        """
        endpoint = "/tier/"
        html = await self._get(endpoint)
        soup = BeautifulSoup(html, "lxml")

        entries: list[PokecabookTierEntry] = []

        tier_sections = soup.select(".tier-section, .tier-group, section")

        current_tier = "unknown"
        for section in tier_sections:
            tier_header = section.select_one("h2, h3, .tier-name")
            if tier_header:
                tier_text = tier_header.get_text(strip=True).upper()
                if "TIER" in tier_text or tier_text in ["S", "A", "B", "C", "D"]:
                    current_tier = tier_text

            deck_items = section.select(".deck-item, .archetype, li")
            for item in deck_items:
                entry = self._parse_tier_entry(item, current_tier)
                if entry:
                    entries.append(entry)

        if not entries:
            entries = self._parse_tier_table(soup)

        return PokecabookTierList(
            date=date.today(),
            entries=entries,
            source_url=f"{self.BASE_URL}{endpoint}",
            raw_html=html,
        )

    def _parse_tier_entry(self, elem: Tag, tier: str) -> PokecabookTierEntry | None:
        name_elem = elem.select_one("a, .deck-name, .archetype-name, span")
        if not name_elem:
            return None

        name = name_elem.get_text(strip=True)
        if not name or len(name) < 2:
            return None

        rate_elem = elem.select_one(".usage-rate, .rate, .percentage")
        usage_rate = None
        if rate_elem:
            rate_text = rate_elem.get_text(strip=True)
            rate_match = re.search(r"(\d+(?:\.\d+)?)", rate_text)
            if rate_match:
                usage_rate = float(rate_match.group(1)) / 100.0

        trend_elem = elem.select_one(".trend, .arrow")
        trend = None
        if trend_elem:
            classes = trend_elem.get("class") or []
            trend_class = " ".join(str(c) for c in classes)
            if "up" in trend_class or "↑" in trend_elem.get_text():
                trend = "rising"
            elif "down" in trend_class or "↓" in trend_elem.get_text():
                trend = "falling"
            else:
                trend = "stable"

        return PokecabookTierEntry(
            archetype_name=name,
            tier=tier,
            usage_rate=usage_rate,
            trend=trend,
        )

    def _parse_tier_table(self, soup: BeautifulSoup) -> list[PokecabookTierEntry]:
        entries: list[PokecabookTierEntry] = []

        tables = soup.select("table")
        for table in tables:
            rows = table.select("tr")
            for row in rows[1:]:
                cells = row.select("td")
                if len(cells) < 2:
                    continue

                name = cells[0].get_text(strip=True)
                if not name:
                    continue

                tier = "unknown"
                usage_rate = None

                tier_values = ["S", "A", "B", "C", "D", "TIER1", "TIER2", "TIER3"]
                for cell in cells[1:]:
                    text = cell.get_text(strip=True)
                    if text.upper() in tier_values:
                        tier = text.upper()
                    elif "%" in text or re.match(r"^\d+(?:\.\d+)?$", text):
                        rate_match = re.search(r"(\d+(?:\.\d+)?)", text)
                        if rate_match:
                            val = float(rate_match.group(1))
                            usage_rate = val / 100.0 if val > 1 else val

                entries.append(
                    PokecabookTierEntry(
                        archetype_name=name,
                        tier=tier,
                        usage_rate=usage_rate,
                    )
                )

        return entries

    async def fetch_adoption_rates(
        self, deck_type: str | None = None
    ) -> PokecabookAdoptionRates:
        """Fetch card adoption rates.

        Args:
            deck_type: Optional deck type filter.

        Returns:
            Adoption rate data.
        """
        endpoint = f"/adoption/{deck_type}/" if deck_type else "/adoption/"

        try:
            html = await self._get(endpoint)
        except PokecabookError:
            endpoint = "/card-usage/"
            html = await self._get(endpoint)

        soup = BeautifulSoup(html, "lxml")

        entries: list[PokecabookAdoptionEntry] = []

        tables = soup.select("table")
        for table in tables:
            rows = table.select("tr")

            headers = table.select("th")
            name_idx = 0
            rate_idx = 1
            copies_idx = 2

            for i, header in enumerate(headers):
                header_text = header.get_text(strip=True).lower()
                if "カード" in header_text or "name" in header_text:
                    name_idx = i
                elif "採用率" in header_text or "rate" in header_text:
                    rate_idx = i
                elif "枚数" in header_text or "copies" in header_text:
                    copies_idx = i

            for row in rows[1:]:
                cells = row.select("td")
                if len(cells) < 2:
                    continue

                if name_idx < len(cells):
                    card_name = cells[name_idx].get_text(strip=True)
                else:
                    card_name = ""
                if not card_name:
                    continue

                if rate_idx < len(cells):
                    rate_text = cells[rate_idx].get_text(strip=True)
                else:
                    rate_text = "0"
                rate_match = re.search(r"(\d+(?:\.\d+)?)", rate_text)
                inclusion_rate = 0.0
                if rate_match:
                    val = float(rate_match.group(1))
                    inclusion_rate = val / 100.0 if val > 1 else val

                avg_copies = None
                if copies_idx < len(cells):
                    copies_text = cells[copies_idx].get_text(strip=True)
                    copies_match = re.search(r"(\d+(?:\.\d+)?)", copies_text)
                    if copies_match:
                        avg_copies = float(copies_match.group(1))

                entries.append(
                    PokecabookAdoptionEntry(
                        card_name_jp=card_name,
                        inclusion_rate=inclusion_rate,
                        avg_copies=avg_copies,
                        archetype=deck_type,
                    )
                )

        card_items = soup.select(".card-item, .adoption-card")
        for item in card_items:
            name_elem = item.select_one(".card-name, a")
            if not name_elem:
                continue

            card_name = name_elem.get_text(strip=True)

            rate_elem = item.select_one(".rate, .percentage")
            inclusion_rate = 0.0
            if rate_elem:
                rate_text = rate_elem.get_text(strip=True)
                rate_match = re.search(r"(\d+(?:\.\d+)?)", rate_text)
                if rate_match:
                    val = float(rate_match.group(1))
                    inclusion_rate = val / 100.0 if val > 1 else val

            copies_elem = item.select_one(".copies, .count")
            avg_copies = None
            if copies_elem:
                copies_text = copies_elem.get_text(strip=True)
                copies_match = re.search(r"(\d+(?:\.\d+)?)", copies_text)
                if copies_match:
                    avg_copies = float(copies_match.group(1))

            entries.append(
                PokecabookAdoptionEntry(
                    card_name_jp=card_name,
                    inclusion_rate=inclusion_rate,
                    avg_copies=avg_copies,
                    archetype=deck_type,
                )
            )

        return PokecabookAdoptionRates(
            date=date.today(),
            entries=entries,
            source_url=f"{self.BASE_URL}{endpoint}",
            raw_html=html,
        )
