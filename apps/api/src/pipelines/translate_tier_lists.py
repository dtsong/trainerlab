"""JP tier list translation pipeline.

Fetches tier lists from Pokecabook and Pokekameshi, translates archetype
names, and consolidates into a unified JP meta view.
"""

import logging
from dataclasses import dataclass, field
from datetime import date

from src.clients.claude import ClaudeClient
from src.clients.pokecabook import PokecabookClient, PokecabookError
from src.clients.pokekameshi import PokekameshiClient, PokekameshiError
from src.db.database import async_session_factory
from src.schemas.translation import ArticleTranslationRequest
from src.services.translation_service import TranslationService

logger = logging.getLogger(__name__)


@dataclass
class TranslateTierListsResult:
    """Result of tier list translation pipeline."""

    pokecabook_entries: int = 0
    pokekameshi_entries: int = 0
    translations_saved: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return len(self.errors) == 0


async def translate_tier_lists(
    dry_run: bool = False,
) -> TranslateTierListsResult:
    """Translate JP tier lists from multiple sources.

    Fetches tier data from Pokecabook and Pokekameshi, translates
    archetype names, and saves consolidated tier list content.

    Args:
        dry_run: If True, fetch and translate but don't persist.

    Returns:
        TranslateTierListsResult with statistics.
    """
    result = TranslateTierListsResult()

    logger.info("Starting tier list translation: dry_run=%s", dry_run)

    pokecabook_data = None
    pokekameshi_data = None

    try:
        async with PokecabookClient() as pokecabook:
            pokecabook_tier = await pokecabook.fetch_tier_list()
            pokecabook_data = pokecabook_tier
            result.pokecabook_entries = len(pokecabook_tier.entries)
            logger.info(
                "Fetched %d entries from Pokecabook", len(pokecabook_tier.entries)
            )
    except PokecabookError as e:
        error_msg = f"Error fetching Pokecabook tier list: {e}"
        logger.warning(error_msg)
        result.errors.append(error_msg)

    try:
        async with PokekameshiClient() as pokekameshi:
            pokekameshi_tier = await pokekameshi.fetch_tier_tables()
            pokekameshi_data = pokekameshi_tier
            result.pokekameshi_entries = len(pokekameshi_tier.entries)
            logger.info(
                "Fetched %d entries from Pokekameshi", len(pokekameshi_tier.entries)
            )
    except PokekameshiError as e:
        error_msg = f"Error fetching Pokekameshi tier list: {e}"
        logger.warning(error_msg)
        result.errors.append(error_msg)

    if not pokecabook_data and not pokekameshi_data:
        result.errors.append("No tier list data could be fetched")
        return result

    try:
        async with (
            ClaudeClient() as claude,
            async_session_factory() as session,
        ):
            service = TranslationService(session, claude)

            combined_text = _format_combined_tier_lists(
                pokecabook_data, pokekameshi_data
            )

            if dry_run:
                translation = await service.translate(
                    text=combined_text[:2000],
                    content_type="tier_list",
                    context="JP Pokemon TCG tier list from Pokecabook and Pokekameshi",
                )
                logger.info(
                    "DRY RUN: Would save tier list (layer=%s, confidence=%s)",
                    translation.layer_used,
                    translation.confidence,
                )
                result.translations_saved += 1
            else:
                source_id = f"jp-tier-combined-{date.today().isoformat()}"
                request = ArticleTranslationRequest(
                    source_id=source_id,
                    source_url="https://pokecabook.com/tier/",
                    content_type="tier_list",
                    original_text=combined_text,
                    context="Combined JP tier list from Pokecabook and Pokekameshi",
                )
                await service.translate_article(request)
                result.translations_saved += 1
                logger.info("Saved combined tier list translation")

    except Exception as e:
        error_msg = f"Error translating tier lists: {e}"
        logger.error(error_msg, exc_info=True)
        result.errors.append(error_msg)

    logger.info(
        "Tier list translation: pokecabook=%d, pokekameshi=%d, saved=%d, errors=%d",
        result.pokecabook_entries,
        result.pokekameshi_entries,
        result.translations_saved,
        len(result.errors),
    )

    return result


def _format_combined_tier_lists(pokecabook_data, pokekameshi_data) -> str:
    """Format combined tier list data as text."""
    lines = [f"JP Meta Tier Lists - {date.today().isoformat()}"]
    lines.append("")

    if pokecabook_data and pokecabook_data.entries:
        lines.append("【Pokecabook Tier List】")
        current_tier = None
        for entry in pokecabook_data.entries:
            if entry.tier != current_tier:
                current_tier = entry.tier
                lines.append(f"\n{current_tier}:")

            line = f"  - {entry.archetype_name}"
            if entry.usage_rate:
                line += f" ({entry.usage_rate * 100:.1f}%)"
            lines.append(line)

        lines.append("")

    if pokekameshi_data and pokekameshi_data.entries:
        lines.append("【Pokekameshi Tier Table】")
        if pokekameshi_data.environment_name:
            lines.append(f"環境: {pokekameshi_data.environment_name}")

        current_tier = None
        for entry in pokekameshi_data.entries:
            if entry.tier != current_tier:
                current_tier = entry.tier
                lines.append(f"\n{current_tier}:")

            line = f"  - {entry.archetype_name}"
            parts = []
            if entry.share_rate:
                parts.append(f"{entry.share_rate * 100:.1f}%")
            if entry.csp_points:
                parts.append(f"CSP:{entry.csp_points}")
            if entry.deck_power:
                parts.append(f"Power:{entry.deck_power:.1f}")
            if parts:
                line += f" ({', '.join(parts)})"
            lines.append(line)

    return "\n".join(lines)
