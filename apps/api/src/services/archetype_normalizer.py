"""Archetype normalization service with priority-chain resolution.

Resolves archetype labels from sprite images, signature cards, and text
labels. Priority order:

1. sprite_lookup — known sprite-key → archetype mapping
2. auto_derive — generate name from sprite filenames
3. signature_card — detect from decklist via ArchetypeDetector
4. text_label — normalize raw text via alias table
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Literal

from src.data.signature_cards import normalize_archetype
from src.services.archetype_detector import ArchetypeDetector

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

DetectionMethod = Literal[
    "sprite_lookup", "auto_derive", "signature_card", "text_label"
]

# Known sprite-key → canonical archetype name.
# Keys are lowercase, hyphen-joined Pokemon filenames extracted from sprite
# URLs (e.g. "charizard-pidgeot").
#
# Maintained manually. For DB-backed overrides see the archetype_sprites
# table which takes priority when a session is provided.
SPRITE_ARCHETYPE_MAP: dict[str, str] = {
    # --- Charizard variants ---
    "charizard": "Charizard ex",
    "charizard-pidgeot": "Charizard ex",
    "charizard-dusknoir": "Charizard ex",
    # --- Dragapult variants ---
    "dragapult": "Dragapult ex",
    "dragapult-pidgeot": "Dragapult ex",
    # --- Gardevoir ---
    "gardevoir": "Gardevoir ex",
    # --- Raging Bolt ---
    "raging-bolt": "Raging Bolt ex",
    "raging-bolt-ogerpon": "Raging Bolt ex",
    # --- Gholdengo ---
    "gholdengo": "Gholdengo ex",
    # --- Terapagos ---
    "terapagos": "Terapagos ex",
    # --- Archaludon ---
    "archaludon": "Archaludon ex",
    # --- Pidgeot Control ---
    "pidgeot": "Pidgeot ex Control",
    # --- Miraidon ---
    "miraidon": "Miraidon ex",
    # --- Koraidon ---
    "koraidon": "Koraidon ex",
    # --- Iron Hands ---
    "iron-hands": "Iron Hands ex",
    # --- Iron Valiant ---
    "iron-valiant": "Iron Valiant ex",
    # --- Roaring Moon ---
    "roaring-moon": "Roaring Moon ex",
    # --- Chien-Pao ---
    "chien-pao": "Chien-Pao ex",
    "chien-pao-baxcalibur": "Chien-Pao ex",
    # --- Lost Zone ---
    "giratina-comfey": "Lost Zone Giratina",
    "comfey-sableye": "Lost Zone Box",
    "sableye-comfey": "Lost Zone Box",
    # --- VSTAR era (rotated but present in historical data) ---
    "lugia": "Lugia VSTAR",
    "palkia": "Origin Forme Palkia VSTAR",
    "giratina": "Giratina VSTAR",
    "arceus": "Arceus VSTAR",
    "regidrago": "Regidrago VSTAR",
    # --- Mega Evolution archetypes (JP Mega Dream / Nihil Zero) ---
    "absol-mega": "Mega Absol ex",
    "kangaskhan-mega": "Mega Kangaskhan ex",
    "starmie-mega": "Mega Starmie ex",
    "froslass-mega": "Mega Froslass ex",
    "mewtwo-mega": "Mega Mewtwo ex",
    "gengar-mega": "Mega Gengar ex",
    "gardevoir-mega": "Mega Gardevoir ex",
    "sableye-mega": "Mega Sableye ex",
    # --- Current JP meta (>0.5% share) ---
    "grimmsnarl": "Grimmsnarl ex",
    "noctowl": "Noctowl Box",
    "zoroark": "Zoroark ex",
    "ceruledge": "Ceruledge ex",
    "flareon": "Flareon ex",
    "joltik": "Joltik Box",
    "alakazam": "Alakazam ex",
    "crustle": "Crustle ex",
    "greninja": "Greninja ex",
    "froslass": "Froslass ex",
    "froslass-munkidori": "Froslass Munkidori",
    "snorlax": "Snorlax Stall",
    "cinderace": "Cinderace ex",
    "klawf": "Klawf ex",
}

_FILENAME_RE = re.compile(r"/([a-zA-Z0-9_-]+)\.png")


class ArchetypeNormalizer:
    """Resolves archetype labels through a priority chain."""

    def __init__(
        self,
        detector: ArchetypeDetector | None = None,
        sprite_map: dict[str, str] | None = None,
    ) -> None:
        self.detector = detector or ArchetypeDetector()
        # Copy so DB overrides don't mutate the module-level constant.
        self.sprite_map: dict[str, str] = dict(
            sprite_map if sprite_map is not None else SPRITE_ARCHETYPE_MAP
        )
        self._db_loaded = False

    async def load_db_sprites(self, session: AsyncSession) -> int:
        """Load sprite mappings from the archetype_sprites DB table.

        DB entries take priority over in-memory defaults. Call once
        before processing a batch of placements.

        Falls back gracefully to the in-memory sprite map on DB
        errors (e.g. missing table, connection issues).

        Returns:
            Number of DB entries loaded (0 on failure).
        """
        from sqlalchemy import select

        from src.models.archetype_sprite import ArchetypeSprite

        try:
            result = await session.execute(
                select(
                    ArchetypeSprite.sprite_key,
                    ArchetypeSprite.archetype_name,
                )
            )
        except Exception:
            logger.warning(
                "load_db_sprites_failed",
                exc_info=True,
            )
            return 0
        rows = result.all()
        for sprite_key, archetype_name in rows:
            self.sprite_map[sprite_key] = archetype_name
        self._db_loaded = True
        logger.info(
            "loaded_db_sprites",
            extra={"count": len(rows)},
        )
        return len(rows)

    @staticmethod
    async def seed_db_sprites(session: AsyncSession) -> int:
        """Seed the archetype_sprites table from SPRITE_ARCHETYPE_MAP.

        Only inserts keys that don't already exist in the DB.

        Returns:
            Number of new entries inserted.
        """
        from uuid import uuid4

        from sqlalchemy import select

        from src.models.archetype_sprite import ArchetypeSprite

        result = await session.execute(select(ArchetypeSprite.sprite_key))
        existing = {row[0] for row in result.all()}

        inserted = 0
        for sprite_key, archetype_name in SPRITE_ARCHETYPE_MAP.items():
            if sprite_key not in existing:
                session.add(
                    ArchetypeSprite(
                        id=uuid4(),
                        sprite_key=sprite_key,
                        archetype_name=archetype_name,
                        sprite_urls=[],
                        pokemon_names=[sprite_key],
                    )
                )
                inserted += 1
        if inserted:
            await session.flush()
        logger.info(
            "seeded_db_sprites",
            extra={"inserted": inserted, "existing": len(existing)},
        )
        return inserted

    def resolve(
        self,
        sprite_urls: list[str],
        html_archetype: str,
        decklist: list[dict] | None = None,
    ) -> tuple[str, str, DetectionMethod]:
        """Resolve archetype through priority chain.

        Args:
            sprite_urls: Sprite image URLs from the placement.
            html_archetype: Raw archetype text from HTML scraping.
            decklist: Optional decklist for signature-card detection.

        Returns:
            Tuple of (archetype, raw_archetype, detection_method).
        """
        raw_archetype = html_archetype
        sprite_key = ""
        archetype: str
        method: DetectionMethod

        # Priority 1: sprite_lookup
        if sprite_urls:
            sprite_key = self.build_sprite_key(sprite_urls)
            if sprite_key and sprite_key in self.sprite_map:
                archetype = self.sprite_map[sprite_key]
                method = "sprite_lookup"
                logger.debug(
                    "archetype_resolved",
                    extra={
                        "sprite_key": sprite_key,
                        "archetype": archetype,
                        "method": method,
                        "raw": raw_archetype,
                    },
                )
                return archetype, raw_archetype, method

            # Priority 2: auto_derive
            if sprite_key:
                derived = self.derive_name_from_key(sprite_key)
                if derived:
                    logger.debug(
                        "archetype_resolved",
                        extra={
                            "sprite_key": sprite_key,
                            "archetype": derived,
                            "method": "auto_derive",
                            "raw": raw_archetype,
                        },
                    )
                    return derived, raw_archetype, "auto_derive"

        # Priority 3: signature_card
        if decklist:
            try:
                detected = self.detector.detect(decklist)
            except Exception:
                logger.warning(
                    "signature_card_detection_failed",
                    exc_info=True,
                    extra={
                        "sprite_key": sprite_key,
                        "raw": raw_archetype,
                    },
                )
                detected = "Rogue"
            if detected != "Rogue":
                logger.debug(
                    "archetype_resolved",
                    extra={
                        "sprite_key": sprite_key,
                        "archetype": detected,
                        "method": "signature_card",
                        "raw": raw_archetype,
                    },
                )
                return detected, raw_archetype, "signature_card"

        # Priority 4: text_label
        normalized = normalize_archetype(html_archetype)
        logger.debug(
            "archetype_resolved",
            extra={
                "sprite_key": sprite_key,
                "archetype": normalized,
                "method": "text_label",
                "raw": raw_archetype,
            },
        )
        return normalized, raw_archetype, "text_label"

    @staticmethod
    def build_sprite_key(sprite_urls: list[str]) -> str:
        """Build a canonical sprite key from image URLs.

        Extracts the filename stem from each URL, lowercases, and joins
        with hyphens. Underscores in filenames are converted to hyphens.

        Examples:
            ["https://r2.limitlesstcg.net/.../charizard.png"]
            → "charizard"

            ["https://example.com/dragapult.png",
             "https://example.com/pidgeot.png"]
            → "dragapult-pidgeot"
        """
        names: list[str] = []
        for url in sprite_urls:
            match = _FILENAME_RE.search(url)
            if match:
                name = match.group(1).lower().replace("_", "-")
                names.append(name)
            else:
                logger.warning(
                    "sprite_url_no_match",
                    extra={"url": url},
                )
        return "-".join(names)

    @staticmethod
    def derive_name_from_key(sprite_key: str) -> str:
        """Derive a human-readable archetype name from a sprite key.

        Splits on hyphens, capitalizes each part, and joins with spaces.

        Examples:
            "charizard" → "Charizard"
            "dragapult-pidgeot" → "Dragapult Pidgeot"
        """
        if not sprite_key:
            return ""
        parts = sprite_key.split("-")
        return " ".join(p.capitalize() for p in parts if p)
