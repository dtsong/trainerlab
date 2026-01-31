"""Deck import service for parsing deck lists."""

import logging
import re
from dataclasses import dataclass

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.card import Card
from src.schemas import CardInDeck, DeckImportResponse, UnmatchedCard

logger = logging.getLogger(__name__)


@dataclass
class ParsedCard:
    """A card parsed from a deck list line."""

    line: str
    name: str
    set_code: str
    number: str
    quantity: int


class DeckImportService:
    """Service for importing decks from text formats."""

    # PTCGO format: * 4 Charizard ex SV4 6
    PTCGO_PATTERN = re.compile(
        r"^\*\s*(\d+)\s+(.+?)\s+([A-Za-z0-9]+)\s+(\d+[A-Za-z]?)$"
    )
    # Pokemon Card Live format: 4 Charizard ex SV4 6
    PCL_PATTERN = re.compile(r"^(\d+)\s+(.+?)\s+([A-Za-z0-9]+)\s+(\d+[A-Za-z]?)$")

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def import_deck(self, deck_list: str) -> DeckImportResponse:
        """Parse a deck list and match cards.

        Args:
            deck_list: Deck list text in PTCGO or Pokemon Card Live format

        Returns:
            DeckImportResponse with matched cards and unmatched cards
        """
        # Parse all lines
        parsed_cards = self._parse_deck_list(deck_list)

        if not parsed_cards:
            return DeckImportResponse(cards=[], unmatched=[], total_cards=0)

        # Match cards against database
        matched_cards, unmatched_cards = await self._match_cards(parsed_cards)

        # Calculate total
        total = sum(card.quantity for card in matched_cards)

        return DeckImportResponse(
            cards=matched_cards,
            unmatched=unmatched_cards,
            total_cards=total,
        )

    def _parse_deck_list(self, deck_list: str) -> list[ParsedCard]:
        """Parse a deck list into individual card entries.

        Args:
            deck_list: Raw deck list text

        Returns:
            List of parsed cards
        """
        parsed: list[ParsedCard] = []

        for line in deck_list.strip().split("\n"):
            line = line.strip()

            # Skip empty lines and section headers
            if not line or line.startswith("#") or line.startswith("***"):
                continue

            # Skip total lines
            if line.lower().startswith("total"):
                continue

            # Try PTCGO format first
            match = self.PTCGO_PATTERN.match(line)
            if match:
                parsed.append(
                    ParsedCard(
                        line=line,
                        quantity=int(match.group(1)),
                        name=match.group(2),
                        set_code=match.group(3).lower(),
                        number=match.group(4),
                    )
                )
                continue

            # Try Pokemon Card Live format
            match = self.PCL_PATTERN.match(line)
            if match:
                parsed.append(
                    ParsedCard(
                        line=line,
                        quantity=int(match.group(1)),
                        name=match.group(2),
                        set_code=match.group(3).lower(),
                        number=match.group(4),
                    )
                )
                continue

            # If neither pattern matches, log and skip
            logger.debug("Could not parse line: %s", line)

        return parsed

    async def _match_cards(
        self, parsed_cards: list[ParsedCard]
    ) -> tuple[list[CardInDeck], list[UnmatchedCard]]:
        """Match parsed cards against the database.

        Args:
            parsed_cards: List of parsed card entries

        Returns:
            Tuple of (matched cards, unmatched cards)
        """
        matched: list[CardInDeck] = []
        unmatched: list[UnmatchedCard] = []

        # Build a list of (set_id, number) tuples to query
        # We need to match by set_id (lowercase) and number
        conditions = []
        for card in parsed_cards:
            conditions.append(
                and_(
                    func.lower(Card.set_id) == card.set_code.lower(),
                    Card.number == card.number,
                )
            )

        if not conditions:
            return matched, unmatched

        # Query all potentially matching cards
        from sqlalchemy import or_

        query = select(Card).where(or_(*conditions))
        result = await self.session.execute(query)
        db_cards = result.scalars().all()

        # Build lookup by (set_id_lower, number)
        card_lookup: dict[tuple[str, str], Card] = {}
        for card in db_cards:
            key = (card.set_id.lower(), card.number or "")
            card_lookup[key] = card

        # Match each parsed card
        for parsed in parsed_cards:
            key = (parsed.set_code.lower(), parsed.number)
            db_card = card_lookup.get(key)

            if db_card:
                matched.append(CardInDeck(card_id=db_card.id, quantity=parsed.quantity))
            else:
                unmatched.append(
                    UnmatchedCard(
                        line=parsed.line,
                        name=parsed.name,
                        set_code=parsed.set_code.upper(),
                        number=parsed.number,
                        quantity=parsed.quantity,
                    )
                )

        return matched, unmatched
