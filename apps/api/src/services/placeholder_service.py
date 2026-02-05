"""Service for managing placeholder cards (unreleased JP cards)."""

import logging
import random
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.card_id_mapping import CardIdMapping
from src.models.placeholder_card import PlaceholderCard

logger = logging.getLogger(__name__)


@dataclass
class PlaceholderGenerationResult:
    """Result of placeholder generation operation."""

    placeholders_created: int = 0
    mappings_created: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return len(self.errors) == 0


class PlaceholderService:
    """Service for managing placeholder cards and synthetic mappings."""

    # Set codes
    PLACEHOLDER_SET_CODE = "POR"  # Perfect Order
    OFFICIAL_SET_CODE = "ME03"  # Official TCG code

    def __init__(self, session: AsyncSession):
        self.session = session

    def generate_placeholder_id(self) -> str:
        """Generate a unique placeholder card ID.

        Format: POR-XXX where XXX is a random 3-digit number
        Example: POR-042

        Returns:
            Unique placeholder card ID
        """
        return f"{self.PLACEHOLDER_SET_CODE}-{random.randint(1, 999):03d}"  # noqa: S311

    async def create_placeholder(
        self,
        jp_card_id: str,
        name_jp: str,
        name_en: str,
        supertype: str,
        source: str = "manual",
        **kwargs: Any,
    ) -> PlaceholderCard:
        """Create a new placeholder card.

        Args:
            jp_card_id: Original Japanese card ID (e.g., "SV10-15")
            name_jp: Japanese card name
            name_en: English translated name
            supertype: Card supertype (Pokemon, Trainer, Energy)
            source: Source of translation (limitless, llm_x, llm_bluesky, manual)
            **kwargs: Optional fields (subtypes, hp, types, attacks, etc.)

        Returns:
            Created PlaceholderCard
        """
        # Generate unique placeholder ID
        en_card_id = self.generate_placeholder_id()

        # Check if ID already exists
        existing = await self.session.execute(
            select(PlaceholderCard).where(PlaceholderCard.en_card_id == en_card_id)
        )
        if existing.scalar_one_or_none():
            # Try again with different ID
            en_card_id = self.generate_placeholder_id()

        placeholder = PlaceholderCard(
            id=uuid4(),
            jp_card_id=jp_card_id,
            en_card_id=en_card_id,
            name_jp=name_jp,
            name_en=name_en,
            supertype=supertype,
            subtypes=kwargs.get("subtypes"),
            hp=kwargs.get("hp"),
            types=kwargs.get("types"),
            attacks=kwargs.get("attacks"),
            set_code=self.PLACEHOLDER_SET_CODE,
            official_set_code=self.OFFICIAL_SET_CODE,
            is_unreleased=True,
            is_released=False,
            source=source,
            source_url=kwargs.get("source_url"),
            source_account=kwargs.get("source_account"),
        )

        self.session.add(placeholder)
        await self.session.commit()

        logger.info(
            "Created placeholder card: %s -> %s (%s)",
            jp_card_id,
            en_card_id,
            name_en,
        )

        return placeholder

    async def create_synthetic_mapping(
        self,
        jp_card_id: str,
        placeholder_card: PlaceholderCard,
    ) -> CardIdMapping:
        """Create a synthetic mapping for a placeholder card.

        Args:
            jp_card_id: Japanese card ID
            placeholder_card: Placeholder card to link to

        Returns:
            Created CardIdMapping
        """
        # Check if mapping already exists
        existing = await self.session.execute(
            select(CardIdMapping).where(CardIdMapping.jp_card_id == jp_card_id)
        )
        if existing.scalar_one_or_none():
            logger.debug("Mapping already exists for %s", jp_card_id)
            return existing.scalar_one()

        mapping = CardIdMapping(
            id=uuid4(),
            jp_card_id=jp_card_id,
            en_card_id=placeholder_card.en_card_id,
            card_name_en=placeholder_card.name_en,
            jp_set_id=jp_card_id.split("-")[0] if "-" in jp_card_id else None,
            en_set_id=self.PLACEHOLDER_SET_CODE,
            is_synthetic=True,
            placeholder_card_id=placeholder_card.id,
        )

        self.session.add(mapping)
        await self.session.commit()

        logger.info(
            "Created synthetic mapping: %s -> %s",
            jp_card_id,
            placeholder_card.en_card_id,
        )

        return mapping

    async def generate_for_unreleased_cards(
        self,
        unreleased_cards: list[dict[str, Any]],
        source: str = "limitless",
    ) -> PlaceholderGenerationResult:
        """Generate placeholders for a list of unreleased cards.

        Args:
            unreleased_cards: List of unreleased card data from Limitless
            source: Source identifier

        Returns:
            PlaceholderGenerationResult with statistics
        """
        result = PlaceholderGenerationResult()

        for card_data in unreleased_cards:
            try:
                jp_card_id = card_data.get("card_id")
                if not jp_card_id:
                    continue

                # Check if placeholder already exists
                existing = await self.session.execute(
                    select(PlaceholderCard).where(
                        PlaceholderCard.jp_card_id == jp_card_id
                    )
                )
                if existing.scalar_one_or_none():
                    logger.debug("Placeholder already exists for %s", jp_card_id)
                    continue

                # Create placeholder with minimal data
                # More detailed data will be added via translations
                placeholder = await self.create_placeholder(
                    jp_card_id=jp_card_id,
                    name_jp=card_data.get("name_jp", "Unknown"),
                    name_en=card_data.get("name_en") or f"Card {jp_card_id}",
                    supertype=card_data.get("card_type", "Pokemon"),
                    source=source,
                    source_url=card_data.get("source_url"),
                )

                # Create synthetic mapping
                await self.create_synthetic_mapping(jp_card_id, placeholder)

                result.placeholders_created += 1
                result.mappings_created += 1

            except Exception as e:
                error_msg = f"Error creating placeholder for {card_data}: {e}"
                logger.error(error_msg)
                result.errors.append(error_msg)

        logger.info(
            "Placeholder generation complete: %d created, %d errors",
            result.placeholders_created,
            len(result.errors),
        )

        return result

    async def get_mapping_with_fallback(
        self,
        jp_card_id: str,
    ) -> tuple[str, PlaceholderCard | None]:
        """Get EN card ID with fallback to placeholder.

        First tries to find an official mapping, then falls back to
        placeholder if the card is unreleased.

        Args:
            jp_card_id: Japanese card ID

        Returns:
            Tuple of (en_card_id, placeholder_card or None)
        """
        # First check for official mapping
        result = await self.session.execute(
            select(CardIdMapping).where(CardIdMapping.jp_card_id == jp_card_id)
        )
        mapping = result.scalar_one_or_none()

        if mapping:
            if mapping.is_synthetic:
                # Get placeholder details
                placeholder_result = await self.session.execute(
                    select(PlaceholderCard).where(
                        PlaceholderCard.id == mapping.placeholder_card_id
                    )
                )
                placeholder = placeholder_result.scalar_one_or_none()
                return mapping.en_card_id, placeholder
            else:
                return mapping.en_card_id, None

        # No mapping found - create placeholder on the fly
        logger.warning("No mapping found for %s, creating placeholder", jp_card_id)

        placeholder = await self.create_placeholder(
            jp_card_id=jp_card_id,
            name_jp="Unknown",
            name_en=f"Unknown Card ({jp_card_id})",
            supertype="Pokemon",
            source="auto",
        )

        await self.create_synthetic_mapping(jp_card_id, placeholder)

        return placeholder.en_card_id, placeholder

    async def enrich_decklist(
        self,
        decklist: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Enrich a decklist with placeholder card details.

        Args:
            decklist: Raw decklist with card_id and quantity

        Returns:
            Enriched decklist with card names and metadata
        """
        enriched = []

        for entry in decklist:
            card_id = entry.get("card_id")
            if not card_id:
                continue

            # Check if this is a placeholder
            result = await self.session.execute(
                select(PlaceholderCard).where(PlaceholderCard.en_card_id == card_id)
            )
            placeholder = result.scalar_one_or_none()

            enriched_entry = {
                **entry,
                "is_placeholder": placeholder is not None,
            }

            if placeholder:
                enriched_entry.update(
                    {
                        "name": placeholder.name_en,
                        "name_jp": placeholder.name_jp,
                        "supertype": placeholder.supertype,
                        "types": placeholder.types,
                        "set_code": placeholder.set_code,
                    }
                )

            enriched.append(enriched_entry)

        return enriched

    async def mark_as_released(
        self,
        jp_card_id: str,
        en_card_id: str,
        released_at: datetime | None = None,
    ) -> None:
        """Mark a placeholder card as officially released.

        Args:
            jp_card_id: Japanese card ID
            en_card_id: Official English card ID
            released_at: Release date (defaults to now)
        """
        result = await self.session.execute(
            select(PlaceholderCard).where(PlaceholderCard.jp_card_id == jp_card_id)
        )
        placeholder = result.scalar_one_or_none()

        if placeholder:
            placeholder.is_unreleased = False
            placeholder.is_released = True
            placeholder.released_at = released_at or datetime.now(UTC)

            # Update the mapping to point to official card ID
            mapping_result = await self.session.execute(
                select(CardIdMapping).where(
                    CardIdMapping.jp_card_id == jp_card_id,
                    CardIdMapping.is_synthetic.is_(True),
                )
            )
            mapping = mapping_result.scalar_one_or_none()

            if mapping:
                mapping.en_card_id = en_card_id
                mapping.is_synthetic = False
                mapping.placeholder_card_id = None

            await self.session.commit()

            logger.info(
                "Marked %s as released with official ID %s",
                jp_card_id,
                en_card_id,
            )
