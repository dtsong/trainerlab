"""Pokecabook content translation pipeline.

Fetches Japanese meta content from Pokecabook and translates
using the 3-layer translation service.
"""

import logging
from dataclasses import dataclass, field
from datetime import date

from src.clients.claude import ClaudeClient
from src.clients.pokecabook import PokecabookClient, PokecabookError
from src.db.database import async_session_factory
from src.schemas.translation import ArticleTranslationRequest
from src.services.translation_service import TranslationService

logger = logging.getLogger(__name__)


@dataclass
class TranslatePokecabookResult:
    """Result of Pokecabook translation pipeline."""

    articles_fetched: int = 0
    articles_translated: int = 0
    articles_skipped: int = 0
    tier_lists_translated: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return len(self.errors) == 0


async def translate_pokecabook_content(
    lookback_days: int = 7,
    dry_run: bool = False,
) -> TranslatePokecabookResult:
    """Translate recent Pokecabook content.

    Fetches articles and tier lists from Pokecabook and translates
    them using the translation service.

    Args:
        lookback_days: Number of days to look back for articles.
        dry_run: If True, fetch and translate but don't persist.

    Returns:
        TranslatePokecabookResult with statistics.
    """
    result = TranslatePokecabookResult()

    logger.info(
        "Starting Pokecabook translation: lookback_days=%d, dry_run=%s",
        lookback_days,
        dry_run,
    )

    try:
        async with (
            PokecabookClient() as pokecabook,
            ClaudeClient() as claude,
            async_session_factory() as session,
        ):
            service = TranslationService(session, claude)

            articles = await pokecabook.fetch_recent_articles(days=lookback_days)
            result.articles_fetched = len(articles)
            logger.info("Fetched %d articles from Pokecabook", len(articles))

            for article in articles:
                try:
                    if not article.url or not article.title:
                        result.articles_skipped += 1
                        continue

                    detail = await pokecabook.fetch_article_detail(article.url)
                    if not detail.raw_html:
                        result.articles_skipped += 1
                        continue

                    content = _extract_article_text(detail.raw_html)
                    if not content or len(content) < 50:
                        result.articles_skipped += 1
                        continue

                    source_id = _url_to_source_id(article.url)

                    if not dry_run:
                        request = ArticleTranslationRequest(
                            source_id=source_id,
                            source_url=article.url,
                            content_type="article",
                            original_text=content,
                            context=f"Pokecabook article: {article.title}",
                        )
                        await service.translate_article(request)
                        result.articles_translated += 1
                    else:
                        translation = await service.translate(
                            text=content[:1000],
                            content_type="article",
                            context=f"Pokecabook article: {article.title}",
                        )
                        logger.info(
                            "DRY RUN: Would translate article %s (layer=%s)",
                            source_id,
                            translation.layer_used,
                        )
                        result.articles_translated += 1

                except PokecabookError as e:
                    error_msg = f"Error fetching article {article.url}: {e}"
                    logger.warning(error_msg)
                    result.errors.append(error_msg)
                except Exception as e:
                    error_msg = f"Error translating article {article.url}: {e}"
                    logger.error(error_msg, exc_info=True)
                    result.errors.append(error_msg)

            try:
                tier_list = await pokecabook.fetch_tier_list()
                if tier_list.entries:
                    tier_text = _format_tier_list_text(tier_list)

                    if not dry_run:
                        source_id = f"pokecabook-tier-{date.today().isoformat()}"
                        request = ArticleTranslationRequest(
                            source_id=source_id,
                            source_url=tier_list.source_url or "https://pokecabook.com/tier/",
                            content_type="tier_list",
                            original_text=tier_text,
                            context="Pokecabook tier list",
                        )
                        await service.translate_article(request)
                    result.tier_lists_translated += 1
                    logger.info(
                        "Translated tier list with %d entries", len(tier_list.entries)
                    )

            except PokecabookError as e:
                error_msg = f"Error fetching tier list: {e}"
                logger.warning(error_msg)
                result.errors.append(error_msg)

    except Exception as e:
        error_msg = f"Pipeline error: {e}"
        logger.error(error_msg, exc_info=True)
        result.errors.append(error_msg)

    logger.info(
        "Pokecabook translation complete: fetched=%d, translated=%d, "
        "skipped=%d, errors=%d",
        result.articles_fetched,
        result.articles_translated,
        result.articles_skipped,
        len(result.errors),
    )

    return result


def _extract_article_text(html: str) -> str:
    """Extract article text from HTML."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "lxml")

    for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
        tag.decompose()

    content_elem = soup.select_one(
        "article, .entry-content, .post-content, .article-content, main"
    )
    if content_elem:
        return content_elem.get_text(separator="\n", strip=True)

    body = soup.body
    if body:
        return body.get_text(separator="\n", strip=True)

    return soup.get_text(separator="\n", strip=True)


def _url_to_source_id(url: str) -> str:
    """Convert URL to a source ID."""
    import re
    match = re.search(r"pokecabook\.com/([^?#]+)", url)
    if match:
        path = match.group(1).strip("/").replace("/", "-")
        return f"pokecabook-{path}"
    return f"pokecabook-{hash(url) % 100000}"


def _format_tier_list_text(tier_list) -> str:
    """Format tier list as text for translation."""
    lines = [f"Pokecabook Tier List - {tier_list.date.isoformat()}"]
    lines.append("")

    current_tier = None
    for entry in tier_list.entries:
        if entry.tier != current_tier:
            current_tier = entry.tier
            lines.append(f"【{current_tier}】")

        line = f"- {entry.archetype_name}"
        if entry.usage_rate:
            line += f" ({entry.usage_rate * 100:.1f}%)"
        if entry.trend:
            trend_symbol = {"rising": "↑", "falling": "↓", "stable": "→"}.get(
                entry.trend, ""
            )
            line += f" {trend_symbol}"
        lines.append(line)

    return "\n".join(lines)
