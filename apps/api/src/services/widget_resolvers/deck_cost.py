"""Deck Cost widget resolver."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.card import Card
from src.models.deck import Deck
from src.services.widget_resolvers import register_resolver


@register_resolver("deck_cost")
class DeckCostResolver:
    """Resolves deck cost estimation data.

    Note: This is a placeholder implementation. Actual price data
    would need to come from TCGPlayer API or similar service.
    """

    async def resolve(
        self, session: AsyncSession, config: dict[str, Any]
    ) -> dict[str, Any]:
        """Resolve deck cost data.

        Config options:
            deck_id: Deck UUID (required if no archetype)
            archetype: Archetype name to show average cost
            include_breakdown: Whether to include per-card costs (default: true)
        """
        deck_id = config.get("deck_id")
        archetype = config.get("archetype")
        include_breakdown = config.get("include_breakdown", True)

        if not deck_id and not archetype:
            return {"error": "Either deck_id or archetype is required"}

        # For now, return placeholder data structure
        # Real implementation would integrate with pricing API
        if deck_id:
            query = select(Deck).where(Deck.id == deck_id, Deck.is_public == True)  # noqa: E712
            result = await session.execute(query)
            deck = result.scalar_one_or_none()

            if not deck:
                return {"error": "Deck not found or not public"}

            # Get card IDs from deck
            card_ids = [
                entry.get("card_id") for entry in deck.cards if entry.get("card_id")
            ]
            card_query = select(Card).where(Card.id.in_(card_ids))
            card_result = await session.execute(card_query)
            cards = {c.id: c for c in card_result.scalars().all()}

            breakdown = []
            if include_breakdown:
                for entry in deck.cards:
                    card_id = entry.get("card_id")
                    quantity = entry.get("quantity", 1)
                    card = cards.get(card_id)
                    if card:
                        breakdown.append(
                            {
                                "card_id": card_id,
                                "name": card.name,
                                "quantity": quantity,
                                "price_estimate": None,  # Would come from pricing API
                                "rarity": card.rarity,
                            }
                        )

            return {
                "deck_id": str(deck_id),
                "deck_name": deck.name,
                "archetype": deck.archetype,
                "total_estimate": None,  # Would be calculated from pricing API
                "currency": "USD",
                "breakdown": breakdown if include_breakdown else None,
                "price_source": "unavailable",
                "last_updated": None,
            }

        # Archetype average cost would require aggregating across decks
        return {
            "archetype": archetype,
            "average_cost": None,
            "currency": "USD",
            "sample_size": 0,
            "price_source": "unavailable",
            "note": "Archetype pricing not yet implemented",
        }
