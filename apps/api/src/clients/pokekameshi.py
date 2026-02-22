"""Async HTTP client for Pokekameshi scraping.

Scrapes Japanese Pokemon TCG tier data from pokekameshi.com including:
- Tier tables with CSP points and deck power ratings
- Meta percentage reports from tournaments
"""

import asyncio
import logging
import re
from dataclasses import dataclass, field
from datetime import date
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


class PokekameshiError(Exception):
    """Exception raised for Pokekameshi scraping errors."""


class PokekameshiRateLimitError(PokekameshiError):
    """Exception raised when rate limited by Pokekameshi."""


@dataclass
class PokekameshiTierEntry:
    """A single tier table entry with ratings."""

    archetype_name: str
    archetype_name_en: str | None = None
    tier: str = "unknown"
    share_rate: float | None = None
    csp_points: int | None = None
    deck_power: float | None = None
    trend: str | None = None


@dataclass
class PokekameshiTierTable:
    """A complete tier table from Pokekameshi."""

    date: date
    environment_name: str | None = None
    entries: list[PokekameshiTierEntry] = field(default_factory=list)
    source_url: str | None = None
    raw_html: str | None = None


@dataclass
class PokekameshiMetaShare:
    """A single archetype's meta share."""

    archetype_name: str
    share_rate: float
    archetype_name_en: str | None = None
    count: int | None = None


@dataclass
class PokekameshiMetaReport:
    """Meta share report from a tournament or time period."""

    date: date
    event_name: str | None = None
    shares: list[PokekameshiMetaShare] = field(default_factory=list)
    total_entries: int | None = None
    source_url: str | None = None
    raw_html: str | None = None


@dataclass
class PokekameshiDeckEntry:
    """A deck entry from a tournament article."""

    placement: int
    archetype_name: str
    player_name: str | None = None
    meta_share: float | None = None


@dataclass
class PokekameshiTournamentArticle:
    """Structured tournament data from a Pokekameshi article."""

    title: str
    url: str
    event_name: str | None = None
    published_date: date | None = None
    deck_entries: list[PokekameshiDeckEntry] = field(default_factory=list)
    meta_shares: list[PokekameshiMetaShare] | None = None
    raw_html: str | None = None


# Placement label mappings for JP tournament articles.
# Order matters: longer/more specific labels must come first
# to avoid "準優勝" matching "優勝".
_JP_PLACEMENT_LABELS: list[tuple[str, int]] = [
    ("準優勝", 2),
    ("優勝", 1),
    ("ベスト16", 9),
    ("ベスト8", 5),
    ("ベスト4", 3),
]


class PokekameshiClient:
    """Async HTTP client for Pokekameshi scraping.

    Implements rate limiting and retry logic. Conservative 10 req/min
    to be respectful of their servers.
    """

    BASE_URL = "https://pokekameshi.com"

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
                    logger.info("Pokekameshi rate limiting: waiting %.1fs", wait_time)
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
                        raise PokekameshiError(f"Not found: {endpoint}")

                    if is_retryable_status(response.status_code):
                        delay = backoff_delay_seconds(self._retry_delay, attempt)
                        logger.warning(
                            "pokekameshi_retry status=%d category=%s endpoint=%s "
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
                            last_error = PokekameshiRateLimitError("Rate limited")
                        else:
                            last_error = PokekameshiError(
                                f"Transient HTTP {response.status_code}"
                            )
                        continue

                    response.raise_for_status()
                    return response.text

                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 404:
                        raise PokekameshiError(f"Not found: {endpoint}") from e
                    if is_retryable_status(e.response.status_code):
                        delay = backoff_delay_seconds(self._retry_delay, attempt)
                        logger.warning(
                            "pokekameshi_retry exception_status=%d category=%s "
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
                    raise PokekameshiError(
                        f"HTTP error {e.response.status_code} on {endpoint}"
                    ) from e

                except httpx.RequestError as e:
                    last_error = e
                    delay = backoff_delay_seconds(self._retry_delay, attempt)
                    logger.warning(
                        "pokekameshi_retry request_error=%s endpoint=%s "
                        "attempt=%d/%d delay=%.2fs",
                        type(e).__name__,
                        endpoint,
                        attempt + 1,
                        self._max_retries,
                        delay,
                    )
                    await asyncio.sleep(delay)

            raise PokekameshiError(
                f"Max retries exceeded for {endpoint}"
            ) from last_error

    async def fetch_tier_tables(self) -> PokekameshiTierTable:
        """Fetch the current tier table.

        Pokekameshi's tier tables include unique metrics like CSP points
        and deck power ratings alongside traditional tier rankings.

        Returns:
            Current tier table with entries.
        """
        endpoint = "/tier/"
        html = await self._get(endpoint)
        soup = BeautifulSoup(html, "lxml")

        entries: list[PokekameshiTierEntry] = []

        env_elem = soup.select_one(".environment-name, h1, .page-title")
        environment_name = None
        if env_elem:
            env_text = env_elem.get_text(strip=True)
            if "環境" in env_text:
                environment_name = env_text

        tables = soup.select("table")
        for table in tables:
            parsed_entries = self._parse_tier_table(table)
            entries.extend(parsed_entries)

        if not entries:
            tier_sections = soup.select(".tier-section, .tier-group, section")
            current_tier = "unknown"

            for section in tier_sections:
                tier_header = section.select_one("h2, h3, .tier-name")
                if tier_header:
                    tier_text = tier_header.get_text(strip=True).upper()
                    if any(t in tier_text for t in ["TIER", "S", "A", "B", "C"]):
                        current_tier = tier_text

                deck_items = section.select(".deck-item, li, .archetype")
                for item in deck_items:
                    entry = self._parse_tier_entry(item, current_tier)
                    if entry:
                        entries.append(entry)

        return PokekameshiTierTable(
            date=date.today(),
            environment_name=environment_name,
            entries=entries,
            source_url=f"{self.BASE_URL}{endpoint}",
            raw_html=html,
        )

    def _parse_tier_table(self, table: Tag) -> list[PokekameshiTierEntry]:
        entries: list[PokekameshiTierEntry] = []

        headers = table.select("th")
        col_map: dict[str, int] = {}

        for i, header in enumerate(headers):
            text = header.get_text(strip=True).lower()
            if "パワー" in text or "power" in text:
                col_map["power"] = i
            elif (
                "デッキ名" in text
                or "アーキタイプ" in text
                or "デッキ" in text
                and "name" not in col_map
            ):
                col_map["name"] = i
            elif "tier" in text or "ティア" in text:
                col_map["tier"] = i
            elif "シェア" in text or "使用率" in text or "rate" in text:
                col_map["share"] = i
            elif "csp" in text or "ポイント" in text:
                col_map["csp"] = i
            elif "トレンド" in text or "trend" in text:
                col_map["trend"] = i

        if "name" not in col_map:
            col_map["name"] = 0

        rows = table.select("tr")
        for row in rows[1:]:
            cells = row.select("td")
            if not cells:
                continue

            name_idx = col_map.get("name", 0)
            if name_idx >= len(cells):
                continue

            name = cells[name_idx].get_text(strip=True)
            if not name or len(name) < 2:
                continue

            tier = "unknown"
            if "tier" in col_map and col_map["tier"] < len(cells):
                tier = cells[col_map["tier"]].get_text(strip=True).upper()

            share_rate = None
            if "share" in col_map and col_map["share"] < len(cells):
                share_text = cells[col_map["share"]].get_text(strip=True)
                rate_match = re.search(r"(\d+(?:\.\d+)?)", share_text)
                if rate_match:
                    val = float(rate_match.group(1))
                    share_rate = val / 100.0 if val > 1 else val

            csp_points = None
            if "csp" in col_map and col_map["csp"] < len(cells):
                csp_text = cells[col_map["csp"]].get_text(strip=True)
                csp_match = re.search(r"(\d+)", csp_text)
                if csp_match:
                    csp_points = int(csp_match.group(1))

            deck_power = None
            if "power" in col_map and col_map["power"] < len(cells):
                power_text = cells[col_map["power"]].get_text(strip=True)
                power_match = re.search(r"(\d+(?:\.\d+)?)", power_text)
                if power_match:
                    deck_power = float(power_match.group(1))

            trend = None
            if "trend" in col_map and col_map["trend"] < len(cells):
                trend_cell = cells[col_map["trend"]]
                trend_text = trend_cell.get_text(strip=True)
                classes = trend_cell.get("class") or []
                trend_class = " ".join(str(c) for c in classes)

                if "up" in trend_class or "↑" in trend_text or "上昇" in trend_text:
                    trend = "rising"
                elif "down" in trend_class or "↓" in trend_text or "下降" in trend_text:
                    trend = "falling"
                elif trend_text:
                    trend = "stable"

            entries.append(
                PokekameshiTierEntry(
                    archetype_name=name,
                    tier=tier,
                    share_rate=share_rate,
                    csp_points=csp_points,
                    deck_power=deck_power,
                    trend=trend,
                )
            )

        return entries

    def _parse_tier_entry(self, elem: Tag, tier: str) -> PokekameshiTierEntry | None:
        name_elem = elem.select_one("a, .deck-name, .archetype-name, span")
        if not name_elem:
            name_text = elem.get_text(strip=True)
            if name_text and len(name_text) >= 2:
                return PokekameshiTierEntry(archetype_name=name_text, tier=tier)
            return None

        name = name_elem.get_text(strip=True)
        if not name or len(name) < 2:
            return None

        return PokekameshiTierEntry(archetype_name=name, tier=tier)

    async def fetch_meta_percentages(
        self, event_date: date | None = None
    ) -> PokekameshiMetaReport:
        """Fetch meta share percentages.

        Args:
            event_date: Optional specific date to fetch data for.

        Returns:
            Meta share report.
        """
        endpoint = f"/meta/{event_date.isoformat()}/" if event_date else "/meta/"

        try:
            html = await self._get(endpoint)
        except PokekameshiError:
            endpoint = "/share/"
            html = await self._get(endpoint)

        soup = BeautifulSoup(html, "lxml")

        shares: list[PokekameshiMetaShare] = []
        total_entries = None
        event_name = None

        title_elem = soup.select_one("h1, .page-title, .event-name")
        if title_elem:
            event_name = title_elem.get_text(strip=True)

        total_elem = soup.select_one(".total-entries, .participant-count")
        if total_elem:
            total_match = re.search(r"(\d+)", total_elem.get_text(strip=True))
            if total_match:
                total_entries = int(total_match.group(1))

        tables = soup.select("table")
        for table in tables:
            parsed_shares = self._parse_meta_table(table)
            shares.extend(parsed_shares)

        if not shares:
            chart_data = soup.select(".chart-item, .meta-item, .share-item")
            for item in chart_data:
                share = self._parse_meta_item(item)
                if share:
                    shares.append(share)

        return PokekameshiMetaReport(
            date=event_date or date.today(),
            event_name=event_name,
            shares=shares,
            total_entries=total_entries,
            source_url=f"{self.BASE_URL}{endpoint}",
            raw_html=html,
        )

    def _parse_meta_table(self, table: Tag) -> list[PokekameshiMetaShare]:
        shares: list[PokekameshiMetaShare] = []

        headers = table.select("th")
        col_map: dict[str, int] = {}

        for i, header in enumerate(headers):
            text = header.get_text(strip=True).lower()
            if "デッキ" in text or "name" in text or "アーキタイプ" in text:
                col_map["name"] = i
            elif "シェア" in text or "率" in text or "%" in text:
                col_map["share"] = i
            elif "数" in text or "count" in text:
                col_map["count"] = i

        if "name" not in col_map:
            col_map["name"] = 0
        if "share" not in col_map:
            col_map["share"] = 1

        rows = table.select("tr")
        for row in rows[1:]:
            cells = row.select("td")
            if len(cells) < 2:
                continue

            name_idx = col_map.get("name", 0)
            share_idx = col_map.get("share", 1)

            if name_idx >= len(cells) or share_idx >= len(cells):
                continue

            name = cells[name_idx].get_text(strip=True)
            if not name:
                continue

            share_text = cells[share_idx].get_text(strip=True)
            rate_match = re.search(r"(\d+(?:\.\d+)?)", share_text)
            if not rate_match:
                continue

            val = float(rate_match.group(1))
            share_rate = val / 100.0 if val > 1 else val

            count = None
            if "count" in col_map and col_map["count"] < len(cells):
                count_text = cells[col_map["count"]].get_text(strip=True)
                count_match = re.search(r"(\d+)", count_text)
                if count_match:
                    count = int(count_match.group(1))

            shares.append(
                PokekameshiMetaShare(
                    archetype_name=name,
                    share_rate=share_rate,
                    count=count,
                )
            )

        return shares

    def _parse_meta_item(self, elem: Tag) -> PokekameshiMetaShare | None:
        name_elem = elem.select_one(".name, .archetype-name, a")
        if not name_elem:
            return None

        name = name_elem.get_text(strip=True)
        if not name:
            return None

        rate_elem = elem.select_one(".rate, .share, .percentage")
        if not rate_elem:
            return None

        rate_text = rate_elem.get_text(strip=True)
        rate_match = re.search(r"(\d+(?:\.\d+)?)", rate_text)
        if not rate_match:
            return None

        val = float(rate_match.group(1))
        share_rate = val / 100.0 if val > 1 else val

        count = None
        count_elem = elem.select_one(".count, .number")
        if count_elem:
            count_match = re.search(r"(\d+)", count_elem.get_text(strip=True))
            if count_match:
                count = int(count_match.group(1))

        return PokekameshiMetaShare(
            archetype_name=name,
            share_rate=share_rate,
            count=count,
        )

    async def fetch_tournament_article(self, url: str) -> PokekameshiTournamentArticle:
        """Fetch and parse a tournament article for deck entries.

        Extracts placement data and meta shares from tournament
        result articles. Pokekameshi articles typically have
        tables with deck names and share percentages.

        Args:
            url: Full URL to the tournament article.

        Returns:
            Parsed article with deck entries (may be empty).
        """
        endpoint = url[len(self.BASE_URL) :] if url.startswith(self.BASE_URL) else url
        html = await self._get(endpoint)
        soup = BeautifulSoup(html, "lxml")

        title_elem = soup.select_one("h1, .entry-title, .post-title")
        title = title_elem.get_text(strip=True) if title_elem else "Untitled"

        event_name = None
        event_elem = soup.select_one(".event-name, .tournament-name")
        if event_elem:
            event_name = event_elem.get_text(strip=True)

        date_elem = soup.select_one("time, .post-date, .entry-date")
        published_date = None
        if date_elem:
            dt_attr = date_elem.get("datetime")
            if dt_attr:
                published_date = self._parse_datetime_attr(dt_attr)

        deck_entries = self._extract_deck_entries(soup)

        # Also extract meta shares if present
        meta_shares: list[PokekameshiMetaShare] | None = None
        tables = soup.select("table")
        for table in tables:
            parsed = self._parse_meta_table(table)
            if parsed:
                meta_shares = parsed
                break

        return PokekameshiTournamentArticle(
            title=title,
            url=url,
            event_name=event_name,
            published_date=published_date,
            deck_entries=deck_entries,
            meta_shares=meta_shares,
            raw_html=html,
        )

    def _extract_deck_entries(self, soup: BeautifulSoup) -> list[PokekameshiDeckEntry]:
        """Extract deck entries from article HTML."""
        entries: list[PokekameshiDeckEntry] = []

        # Strategy 1: headings with placement labels
        headings = soup.select("h2, h3, h4")
        for heading in headings:
            text = heading.get_text(strip=True)
            placement = self._parse_placement_label(text)
            if placement is None:
                continue
            archetype = self._extract_archetype(text)
            if not archetype:
                continue
            share = self._extract_share_near(heading)
            entries.append(
                PokekameshiDeckEntry(
                    placement=placement,
                    archetype_name=archetype,
                    meta_share=share,
                )
            )

        if entries:
            return entries

        # Strategy 2: tables with placement data
        tables = soup.select("table")
        for table in tables:
            rows = table.select("tr")
            for row in rows[1:]:
                cells = row.select("td")
                if len(cells) < 2:
                    continue
                first = cells[0].get_text(strip=True)
                placement = self._parse_placement_label(first)
                if placement is None:
                    num_match = re.match(r"(\d+)", first)
                    if num_match:
                        placement = int(num_match.group(1))
                    else:
                        continue
                archetype = cells[1].get_text(strip=True)
                if not archetype:
                    continue
                share = None
                if len(cells) >= 3:
                    share_text = cells[2].get_text(strip=True)
                    rate_match = re.search(r"(\d+(?:\.\d+)?)", share_text)
                    if rate_match:
                        val = float(rate_match.group(1))
                        share = val / 100.0 if val > 1 else val
                player = None
                if len(cells) >= 4:
                    player = cells[3].get_text(strip=True) or None
                entries.append(
                    PokekameshiDeckEntry(
                        placement=placement,
                        archetype_name=archetype,
                        player_name=player,
                        meta_share=share,
                    )
                )

        return entries

    def _parse_placement_label(self, text: str) -> int | None:
        """Parse JP placement labels to numeric placement."""
        for label, placement in _JP_PLACEMENT_LABELS:
            if label in text:
                return placement
        match = re.search(r"(\d+)\s*位", text)
        if match:
            return int(match.group(1))
        return None

    def _extract_archetype(self, text: str) -> str | None:
        """Extract archetype name from heading text."""
        cleaned = text
        for label, _ in _JP_PLACEMENT_LABELS:
            cleaned = cleaned.replace(label, "")
        cleaned = re.sub(r"\d+\s*位", "", cleaned)
        cleaned = re.sub(r"^[\s：:【】\[\]「」\-/]+", "", cleaned)
        cleaned = re.sub(r"[\s：:【】\[\]「」\-/]+$", "", cleaned)
        cleaned = cleaned.strip()
        return cleaned if cleaned else None

    def _extract_share_near(self, heading: Tag) -> float | None:
        """Try to extract share percentage near heading."""
        sibling = heading.find_next_sibling()
        if sibling:
            text = sibling.get_text(strip=True)
            match = re.search(r"(\d+(?:\.\d+)?)\s*%", text)
            if match:
                return float(match.group(1)) / 100.0
        return None

    def _parse_datetime_attr(
        self, datetime_attr: str | list[str] | None
    ) -> date | None:
        """Parse datetime attribute to date."""
        if not datetime_attr:
            return None
        try:
            from datetime import datetime as dt_cls

            return dt_cls.fromisoformat(
                str(datetime_attr).replace("Z", "+00:00")
            ).date()
        except ValueError:
            return None
