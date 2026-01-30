"""Deck export service for various formats."""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.card import Card
from src.models.deck import Deck
from src.models.user import User

logger = logging.getLogger(__name__)


class DeckExportService:
    """Service for exporting decks to various formats."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def export_ptcgo(
        self,
        deck_id: UUID,
        user: User | None = None,
    ) -> str | None:
        """Export a deck to PTCGO format.

        Args:
            deck_id: The deck ID
            user: The authenticated user (optional, for private deck access)

        Returns:
            PTCGO formatted string if deck found and accessible, None otherwise

        The PTCGO format:
            ****** Pokémon Trading Card Game Deck List ******

            ##Pokémon - 10
            * 4 Charizard ex SV4 6
            ...

            ##Trainer Cards - 30
            * 4 Professor's Research SV4 189
            ...

            ##Energy - 10
            * 10 Fire Energy SVE 2
            ...

            Total Cards - 60
        """
        query = select(Deck).where(Deck.id == deck_id)
        result = await self.session.execute(query)
        deck = result.scalar_one_or_none()

        if deck is None:
            return None

        # Check access
        if not deck.is_public and (user is None or deck.user_id != user.id):
            return None

        card_entries = deck.cards
        if not card_entries:
            return self._build_ptcgo_empty()

        # Build card_id -> quantity mapping
        card_quantities: dict[str, int] = {}
        for entry in card_entries:
            card_id = entry.get("card_id", "")
            quantity = entry.get("quantity", 0)
            card_quantities[card_id] = quantity

        # Fetch actual card data
        card_ids = list(card_quantities.keys())
        card_query = select(Card).where(Card.id.in_(card_ids))
        card_result = await self.session.execute(card_query)
        cards = card_result.scalars().all()

        # Warn if any cards are missing from the database
        found_ids = {card.id for card in cards}
        missing_ids = set(card_ids) - found_ids
        if missing_ids:
            logger.warning(
                "Deck %s export: %d card(s) not found in database: %s",
                deck_id,
                len(missing_ids),
                sorted(missing_ids),
            )

        # Group cards by supertype
        pokemon_lines: list[str] = []
        trainer_lines: list[str] = []
        energy_lines: list[str] = []

        pokemon_count = 0
        trainer_count = 0
        energy_count = 0

        for card in cards:
            qty = card_quantities.get(card.id, 1)
            line = self._format_card_line(card, qty)
            supertype = card.supertype or ""

            if supertype == "Pokemon":
                pokemon_lines.append(line)
                pokemon_count += qty
            elif supertype == "Trainer":
                trainer_lines.append(line)
                trainer_count += qty
            elif supertype == "Energy":
                energy_lines.append(line)
                energy_count += qty

        total = pokemon_count + trainer_count + energy_count

        return self._build_ptcgo_output(
            pokemon_lines=pokemon_lines,
            trainer_lines=trainer_lines,
            energy_lines=energy_lines,
            pokemon_count=pokemon_count,
            trainer_count=trainer_count,
            energy_count=energy_count,
            total=total,
        )

    def _format_card_line(self, card: Card, quantity: int) -> str:
        """Format a single card line for PTCGO export.

        Format: * {quantity} {name} {set_code} {card_number}
        Example: * 4 Charizard ex SV4 6
        """
        name = card.name
        # Use set_id as set code (convert to uppercase)
        set_code = card.set_id.upper() if card.set_id else "UNK"
        card_number = card.number or card.local_id or "1"

        return f"* {quantity} {name} {set_code} {card_number}"

    def _build_ptcgo_empty(self) -> str:
        """Build PTCGO output for an empty deck."""
        lines = [
            "****** Pokémon Trading Card Game Deck List ******",
            "",
            "##Pokémon - 0",
            "",
            "##Trainer Cards - 0",
            "",
            "##Energy - 0",
            "",
            "Total Cards - 0",
        ]
        return "\n".join(lines)

    def _build_ptcgo_output(
        self,
        pokemon_lines: list[str],
        trainer_lines: list[str],
        energy_lines: list[str],
        pokemon_count: int,
        trainer_count: int,
        energy_count: int,
        total: int,
    ) -> str:
        """Build the full PTCGO output string."""
        lines = ["****** Pokémon Trading Card Game Deck List ******", ""]

        # Pokemon section
        lines.append(f"##Pokémon - {pokemon_count}")
        lines.extend(pokemon_lines)
        lines.append("")

        # Trainer section
        lines.append(f"##Trainer Cards - {trainer_count}")
        lines.extend(trainer_lines)
        lines.append("")

        # Energy section
        lines.append(f"##Energy - {energy_count}")
        lines.extend(energy_lines)
        lines.append("")

        # Total
        lines.append(f"Total Cards - {total}")

        return "\n".join(lines)
