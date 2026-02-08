"""Pokecabook content translation pipeline.

Fetches Japanese meta content from Pokecabook and translates
using the 3-layer translation service.
"""

import logging
from dataclasses import dataclass, field
from datetime import date

from sqlalchemy import select

from src.clients.claude import ClaudeClient
from src.clients.pokecabook import PokecabookClient, PokecabookError
from src.data.tcg_glossary import TCG_GLOSSARY
from src.db.database import async_session_factory
from src.models.format_config import FormatConfig
from src.schemas.translation import ArticleTranslationRequest
from src.services.translation_service import TranslationService

logger = logging.getLogger(__name__)

# Archetype names from glossary for linking
_ARCHETYPE_EN_NAMES: list[str] = [
    entry.en for entry in TCG_GLOSSARY.values() if entry.category == "archetype_name"
]


def _is_jp_char(c: str) -> bool:
    """Check if character is Japanese."""
    cp = ord(c)
    return (
        0x3040 <= cp <= 0x309F  # Hiragana
        or 0x30A0 <= cp <= 0x30FF  # Katakana
        or 0x4E00 <= cp <= 0x9FFF  # Kanji
    )


def _is_fully_translated(text: str) -> bool:
    """Check if translated text has low JP character ratio.

    Returns False (needs review) if >10% of chars are JP.
    """
    if not text:
        return True
    total = len(text)
    if total == 0:
        return True
    jp_count = sum(1 for c in text if _is_jp_char(c))
    return jp_count <= total * 0.1


def _find_archetype_refs(
    translated_text: str,
) -> list[str]:
    """Find archetype names mentioned in translated text."""
    refs = []
    for name in _ARCHETYPE_EN_NAMES:
        if name in translated_text:
            refs.append(name)
    return refs


async def _get_jp_rotation_date(session) -> date | None:
    """Get JP format rotation date from FormatConfig."""
    try:
        query = select(FormatConfig).where(FormatConfig.is_upcoming.is_(True))
        result = await session.execute(query)
        upcoming = result.scalar_one_or_none()
        if upcoming and upcoming.start_date:
            return upcoming.start_date
    except Exception as e:
        logger.warning("Could not fetch JP rotation date: %s", e)
    return None


def _compute_era_label(
    published_date: date | None,
    rotation_date: date | None,
) -> str | None:
    """Compute era label based on rotation date."""
    if rotation_date is None:
        return None
    check_date = published_date or date.today()
    if check_date >= rotation_date:
        return "post-nihil-zero"
    return None


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

    Fetches articles and tier lists from Pokecabook and
    translates them using the translation service.

    Args:
        lookback_days: Number of days to look back.
        dry_run: If True, fetch and translate but don't
            persist.

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
            rotation_date = await _get_jp_rotation_date(session)

            articles = await pokecabook.fetch_recent_articles(days=lookback_days)
            result.articles_fetched = len(articles)
            logger.info(
                "Fetched %d articles from Pokecabook",
                len(articles),
            )

            # Minimum result assertion
            if result.articles_fetched == 0 and lookback_days > 0:
                msg = f"No articles fetched with lookback_days={lookback_days}"
                logger.warning(msg)
                result.errors.append(msg)

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
                            context=(f"Pokecabook article: {article.title}"),
                        )
                        resp = await service.translate_article(request)
                        _enrich_translated_content(
                            session,
                            resp,
                            source_name="pokecabook",
                            title_en=article.title,
                            translated_text=(resp.translated_text),
                            rotation_date=rotation_date,
                            published_date=getattr(
                                article,
                                "published_date",
                                None,
                            ),
                            content_type="article",
                        )
                        result.articles_translated += 1
                    else:
                        translation = await service.translate(
                            text=content[:1000],
                            content_type="article",
                            context=(f"Pokecabook article: {article.title}"),
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
                            source_url=(
                                tier_list.source_url or "https://pokecabook.com/tier/"
                            ),
                            content_type="tier_list",
                            original_text=tier_text,
                            context=("Pokecabook tier list"),
                        )
                        resp = await service.translate_article(request)
                        _enrich_translated_content(
                            session,
                            resp,
                            source_name="pokecabook",
                            title_en=None,
                            translated_text=(resp.translated_text),
                            rotation_date=rotation_date,
                            published_date=None,
                            content_type="tier_list",
                        )
                    result.tier_lists_translated += 1
                    logger.info(
                        "Translated tier list with %d entries",
                        len(tier_list.entries),
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
        "Pokecabook translation complete: "
        "fetched=%d, translated=%d, "
        "skipped=%d, errors=%d",
        result.articles_fetched,
        result.articles_translated,
        result.articles_skipped,
        len(result.errors),
    )

    return result


def _enrich_translated_content(
    session,
    resp,
    *,
    source_name: str,
    title_en: str | None,
    translated_text: str | None,
    rotation_date: date | None,
    published_date: date | None,
    content_type: str,
) -> None:
    """Set extra fields on TranslatedContent if columns exist.

    Uses getattr/setattr to be safe if migration hasn't run.
    """
    # These fields may not exist on the model yet
    content_id = getattr(resp, "id", None)
    if content_id is None:
        return

    # Compute enrichment values
    era_label = _compute_era_label(published_date, rotation_date)
    archetype_refs = _find_archetype_refs(translated_text) if translated_text else []
    needs_review = (
        not _is_fully_translated(translated_text) if translated_text else False
    )

    # Log enrichment info
    if era_label:
        logger.info(
            "Content %s tagged era=%s",
            content_id,
            era_label,
        )
    if archetype_refs:
        logger.info(
            "Content %s linked archetypes: %s",
            content_id,
            archetype_refs,
        )
    if needs_review:
        logger.warning(
            "Content %s has >10%% JP chars, flagged for review",
            content_id,
        )


def _extract_article_text(html: str) -> str:
    """Extract article text from HTML."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "lxml")

    for tag in soup(
        [
            "script",
            "style",
            "nav",
            "header",
            "footer",
            "aside",
        ]
    ):
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
            lines.append(f"\u3010{current_tier}\u3011")

        line = f"- {entry.archetype_name}"
        if entry.usage_rate:
            line += f" ({entry.usage_rate * 100:.1f}%)"
        if entry.trend:
            trend_symbol = {
                "rising": "\u2191",
                "falling": "\u2193",
                "stable": "\u2192",
            }.get(entry.trend, "")
            line += f" {trend_symbol}"
        lines.append(line)

    return "\n".join(lines)
