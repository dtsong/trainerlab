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

LIMITLESS_SPRITE_CDN = "https://r2.limitlesstcg.net/pokemon/gen9"

# Composite sprite keys that map to multiple filenames.
# Most sprite keys are a single pokemon and the filename is the key itself.
# These entries are for multi-sprite composites that can't be split on "-"
# naively because individual pokemon names contain hyphens.
_COMPOSITE_SPRITE_FILENAMES: dict[str, list[str]] = {
    "charizard-pidgeot": ["charizard", "pidgeot"],
    "charizard-dusknoir": ["charizard", "dusknoir"],
    "dragapult-pidgeot": ["dragapult", "pidgeot"],
    "ogerpon-raging-bolt": ["ogerpon", "raging-bolt"],
    "baxcalibur-chien-pao": ["baxcalibur", "chien-pao"],
    "comfey-giratina": ["comfey", "giratina"],
    "comfey-sableye": ["comfey", "sableye"],
    "absol-mega-kangaskhan-mega": ["absol-mega", "kangaskhan-mega"],
    "noctowl-ogerpon-wellspring": ["noctowl", "ogerpon-wellspring"],
    "joltik-pikachu": ["joltik", "pikachu"],
    "armarouge-ho-oh": ["armarouge", "ho-oh"],
    "froslass-munkidori": ["froslass", "munkidori"],
    "iron-valiant": ["iron-valiant"],
    "iron-hands": ["iron-hands"],
    "raging-bolt": ["raging-bolt"],
    "roaring-moon": ["roaring-moon"],
    "chien-pao": ["chien-pao"],
}


def sprite_key_to_filenames(key: str) -> list[str]:
    """Convert a sprite key to a list of sprite filenames.

    Looks up the composite map first; if not found, returns [key].
    """
    if not key:
        return []
    return _COMPOSITE_SPRITE_FILENAMES.get(key, [key])


def sprite_key_to_urls(key: str) -> list[str]:
    """Construct CDN URLs from a sprite key."""
    filenames = sprite_key_to_filenames(key)
    return [f"{LIMITLESS_SPRITE_CDN}/{fn}.png" for fn in filenames]


DetectionMethod = Literal[
    "sprite_lookup", "auto_derive", "signature_card", "text_label"
]

# Confidence scores by detection method
CONFIDENCE_SCORES: dict[str, float] = {
    "sprite_lookup": 0.95,
    "auto_derive": 0.85,
    "signature_card": 0.70,
    "text_label": 0.40,
}

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
    "ogerpon-raging-bolt": "Raging Bolt ex",
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
    "baxcalibur-chien-pao": "Chien-Pao ex",
    # --- Lost Zone ---
    "comfey-giratina": "Lost Zone Giratina",
    "comfey-sableye": "Lost Zone Box",
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
    # --- Multi-sprite composites (JP meta >0.5%) ---
    "absol-mega-kangaskhan-mega": "Mega Absol Box",
    "noctowl-ogerpon-wellspring": "Tera Box",
    "joltik-pikachu": "Joltik Box",
    "armarouge-ho-oh": "Ho-Oh Armarouge",
    # --- Missing Mega entries ---
    "lopunny-mega": "Mega Lopunny ex",
    "lucario-mega": "Mega Lucario ex",
}

# Only matches .png sprite URLs. If Limitless migrates to .webp or adds
# query parameters, this regex and tests must be updated. See
# test_archetype_edge_cases.py for documented limitation tests.
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
                fnames = sprite_key_to_filenames(sprite_key)
                session.add(
                    ArchetypeSprite(
                        id=uuid4(),
                        sprite_key=sprite_key,
                        archetype_name=archetype_name,
                        sprite_urls=sprite_key_to_urls(sprite_key),
                        pokemon_names=fnames,
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
        archetype, raw, method, _confidence = self.resolve_with_confidence(
            sprite_urls, html_archetype, decklist
        )
        return archetype, raw, method

    def resolve_with_confidence(
        self,
        sprite_urls: list[str],
        html_archetype: str,
        decklist: list[dict] | None = None,
    ) -> tuple[str, str, DetectionMethod, float]:
        """Resolve archetype with confidence score.

        Returns:
            Tuple of (archetype, raw_archetype, detection_method, confidence).
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
                return (
                    archetype,
                    raw_archetype,
                    method,
                    CONFIDENCE_SCORES[method],
                )

            # Priority 2: auto_derive
            if sprite_key:
                derived = self.derive_name_from_key(sprite_key)
                if derived:
                    logger.info(
                        "archetype_resolved",
                        extra={
                            "sprite_key": sprite_key,
                            "archetype": derived,
                            "method": "auto_derive",
                            "raw": raw_archetype,
                        },
                    )
                    return (
                        derived,
                        raw_archetype,
                        "auto_derive",
                        CONFIDENCE_SCORES["auto_derive"],
                    )

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
                return (
                    detected,
                    raw_archetype,
                    "signature_card",
                    CONFIDENCE_SCORES["signature_card"],
                )

        # Priority 4: text_label
        normalized = normalize_archetype(html_archetype)
        confidence = CONFIDENCE_SCORES["text_label"]
        if normalized == "Unknown":
            confidence = 0.0
        logger.debug(
            "archetype_resolved",
            extra={
                "sprite_key": sprite_key,
                "archetype": normalized,
                "method": "text_label",
                "raw": raw_archetype,
            },
        )
        return normalized, raw_archetype, "text_label", confidence

    @staticmethod
    def build_sprite_key(sprite_urls: list[str]) -> str:
        """Build a canonical sprite key from image URLs.

        Extracts the filename stem from each URL, lowercases, sorts
        alphabetically, and joins with hyphens. Sorting ensures the
        same key is produced regardless of URL order. Underscores in
        filenames are converted to hyphens.

        Examples:
            ["https://r2.limitlesstcg.net/.../charizard.png"]
            → "charizard"

            ["https://example.com/pidgeot.png",
             "https://example.com/dragapult.png"]
            → "dragapult-pidgeot"  (sorted)
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
        names.sort()
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
