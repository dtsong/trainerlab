"""Pipeline to discover and ingest JP tournaments from Pokecabook articles."""

import logging
from dataclasses import dataclass, field

from src.clients.pokecabook import PokecabookClient, PokecabookError
from src.pipelines.ingest_jp_tournament_articles import (
    ingest_jp_tournament_article,
)

logger = logging.getLogger(__name__)

# Keywords that indicate a tournament result article
_TOURNAMENT_KEYWORDS = [
    "\u7d50\u679c",
    "\u30b7\u30c6\u30a3\u30ea\u30fc\u30b0",
    "CL",
    "\u30c1\u30e3\u30f3\u30d4\u30aa\u30f3\u30ba\u30ea\u30fc\u30b0",
    "\u30b8\u30e0\u30d0\u30c8\u30eb",
    "\u30c8\u30ec\u30fc\u30ca\u30fc\u30ba\u30ea\u30fc\u30b0",
    "\u512a\u52dd",
    "\u5165\u8cde",
]


@dataclass
class DiscoverPokecabookResult:
    articles_discovered: int = 0
    articles_filtered: int = 0
    tournaments_created: int = 0
    tournaments_skipped: int = 0
    placements_created: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return len(self.errors) == 0


def _is_tournament_article(title: str) -> bool:
    """Check if article title indicates tournament results."""
    return any(kw in title for kw in _TOURNAMENT_KEYWORDS)


async def discover_pokecabook_tournaments(
    lookback_days: int = 14,
    dry_run: bool = False,
) -> DiscoverPokecabookResult:
    """Discover and ingest tournament articles from Pokecabook.

    Fetches recent articles, filters to tournament-related ones,
    and feeds each into the existing ingestion pipeline.
    """
    result = DiscoverPokecabookResult()

    # Step 1: Fetch recent articles
    try:
        async with PokecabookClient() as client:
            articles = await client.fetch_recent_articles(
                days=lookback_days,
            )
    except PokecabookError as e:
        result.errors.append(f"Failed to fetch articles: {e}")
        return result

    result.articles_discovered = len(articles)

    # Step 2: Filter to tournament articles
    tournament_articles = [a for a in articles if _is_tournament_article(a.title)]
    result.articles_filtered = len(tournament_articles)

    if not tournament_articles:
        logger.info(
            "No tournament articles found in %d articles",
            len(articles),
        )
        return result

    if dry_run:
        logger.info(
            "Dry run: would process %d tournament articles",
            len(tournament_articles),
        )
        return result

    # Step 3: Ingest each tournament article
    for article in tournament_articles:
        try:
            tournament_name = article.title
            tournament_date = article.published_date
            if not tournament_date:
                logger.warning(
                    "Skipping article without date: %s",
                    article.url,
                )
                result.tournaments_skipped += 1
                continue

            ingest_result = await ingest_jp_tournament_article(
                tournament_name=tournament_name,
                tournament_date=tournament_date,
                pokecabook_url=article.url,
            )

            if ingest_result.tournament_created:
                result.tournaments_created += 1
                result.placements_created += ingest_result.placements_created
            else:
                result.tournaments_skipped += 1
                if ingest_result.errors:
                    for err in ingest_result.errors:
                        if "already exists" in err:
                            logger.debug(
                                "Skipping existing: %s",
                                article.title,
                            )
                        else:
                            result.errors.append(err)

        except Exception as e:
            error_msg = f"Error processing article {article.url}: {e}"
            logger.error(error_msg)
            result.errors.append(error_msg)

    return result
