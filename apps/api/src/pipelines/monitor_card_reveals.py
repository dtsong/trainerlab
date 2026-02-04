"""JP card reveal monitoring pipeline.

Monitors Limitless for new JP card reveals and tracks unreleased
cards that may impact the meta when released internationally.
"""

import logging
from dataclasses import dataclass, field
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from src.clients.limitless import LimitlessClient, LimitlessError, LimitlessJPCard
from src.db.database import async_session_factory
from src.models.jp_unreleased_card import JPUnreleasedCard

logger = logging.getLogger(__name__)


@dataclass
class MonitorCardRevealsResult:
    """Result of card reveal monitoring pipeline."""

    cards_checked: int = 0
    new_cards_found: int = 0
    cards_updated: int = 0
    cards_marked_released: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return len(self.errors) == 0


async def check_card_reveals(
    dry_run: bool = False,
) -> MonitorCardRevealsResult:
    """Check for new JP card reveals and track unreleased cards.

    Fetches unreleased JP cards from Limitless and updates our tracking
    database. Also checks if previously unreleased cards are now available.

    Args:
        dry_run: If True, fetch data but don't persist.

    Returns:
        MonitorCardRevealsResult with statistics.
    """
    result = MonitorCardRevealsResult()

    logger.info("Starting card reveal monitor: dry_run=%s", dry_run)

    try:
        async with LimitlessClient() as limitless:
            unreleased_cards = await limitless.fetch_unreleased_cards(translate=True)
            result.cards_checked = len(unreleased_cards)
            logger.info("Fetched %d unreleased JP cards", len(unreleased_cards))

            if dry_run:
                logger.info(
                    "DRY RUN: Would process %d unreleased cards",
                    len(unreleased_cards),
                )
                for card in unreleased_cards[:5]:
                    logger.info(
                        "  - %s (%s) [%s]",
                        card.name_jp,
                        card.name_en or "no EN",
                        card.card_id,
                    )
                return result

            async with async_session_factory() as session:
                current_unreleased_ids = {card.card_id for card in unreleased_cards}

                for card in unreleased_cards:
                    try:
                        existing_query = select(JPUnreleasedCard).where(
                            JPUnreleasedCard.jp_card_id == card.card_id
                        )
                        existing_result = await session.execute(existing_query)
                        existing = existing_result.scalar_one_or_none()

                        if existing:
                            if _should_update(existing, card):
                                existing.name_en = card.name_en
                                existing.card_type = card.card_type
                                existing.jp_set_id = card.set_id
                                result.cards_updated += 1
                        else:
                            new_card = JPUnreleasedCard(
                                id=uuid4(),
                                jp_card_id=card.card_id,
                                jp_set_id=card.set_id,
                                name_jp=card.name_jp,
                                name_en=card.name_en,
                                card_type=card.card_type,
                                competitive_impact=_estimate_impact(card),
                                is_released=False,
                            )
                            session.add(new_card)
                            result.new_cards_found += 1
                            logger.info(
                                "New unreleased card: %s (%s)",
                                card.name_jp,
                                card.card_id,
                            )

                    except SQLAlchemyError as e:
                        error_msg = f"Error saving card {card.card_id}: {e}"
                        logger.warning(error_msg)
                        result.errors.append(error_msg)

                tracked_query = select(JPUnreleasedCard).where(
                    JPUnreleasedCard.is_released == False  # noqa: E712
                )
                tracked_result = await session.execute(tracked_query)
                tracked_cards = tracked_result.scalars().all()

                for tracked in tracked_cards:
                    if tracked.jp_card_id not in current_unreleased_ids:
                        tracked.is_released = True
                        result.cards_marked_released += 1
                        logger.info(
                            "Card now released: %s (%s)",
                            tracked.name_jp,
                            tracked.jp_card_id,
                        )

                await session.commit()

    except LimitlessError as e:
        error_msg = f"Error fetching unreleased cards: {e}"
        logger.error(error_msg)
        result.errors.append(error_msg)
    except Exception as e:
        error_msg = f"Pipeline error: {e}"
        logger.error(error_msg, exc_info=True)
        result.errors.append(error_msg)

    logger.info(
        "Card reveal monitor complete: checked=%d, new=%d, updated=%d, "
        "released=%d, errors=%d",
        result.cards_checked,
        result.new_cards_found,
        result.cards_updated,
        result.cards_marked_released,
        len(result.errors),
    )

    return result


def _should_update(existing: JPUnreleasedCard, card: LimitlessJPCard) -> bool:
    """Check if existing record should be updated with new data."""
    if not existing.name_en and card.name_en:
        return True
    if not existing.card_type and card.card_type:
        return True
    return bool(not existing.jp_set_id and card.set_id)


def _estimate_impact(card: LimitlessJPCard) -> int:
    """Estimate competitive impact of a card (1-5 scale).

    This is a simple heuristic that can be refined based on card type
    and known patterns.
    """
    name = card.name_jp or ""
    card_type = (card.card_type or "").lower()

    if "ex" in name.lower() or "ex" in card_type:
        return 4

    if "vstar" in name.lower() or "vstar" in card_type:
        return 4

    if "ace" in card_type:
        return 4

    trainer_keywords = ["サポート", "グッズ", "スタジアム"]
    for keyword in trainer_keywords:
        if keyword in name:
            return 3

    return 3
