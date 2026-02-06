"""Archetype normalization service with priority-chain resolution.

Resolves archetype labels from sprite images, signature cards, and text
labels. Priority order:

1. sprite_lookup — known sprite-key → archetype mapping
2. auto_derive — generate name from sprite filenames
3. signature_card — detect from decklist via ArchetypeDetector
4. text_label — normalize raw text via alias table
"""

import re

from src.data.signature_cards import normalize_archetype
from src.services.archetype_detector import ArchetypeDetector

# Known sprite-key → canonical archetype name.
# Keys are lowercase, hyphen-joined Pokemon filenames extracted from sprite
# URLs (e.g. "charizard-pidgeot").
SPRITE_ARCHETYPE_MAP: dict[str, str] = {
    "charizard": "Charizard ex",
    "charizard-pidgeot": "Charizard ex",
    "dragapult": "Dragapult ex",
    "dragapult-pidgeot": "Dragapult ex",
    "gardevoir": "Gardevoir ex",
    "raging-bolt": "Raging Bolt ex",
    "raging-bolt-ogerpon": "Raging Bolt ex",
    "lugia": "Lugia VSTAR",
    "palkia": "Origin Forme Palkia VSTAR",
    "giratina": "Giratina VSTAR",
    "giratina-comfey": "Lost Zone Giratina",
    "arceus": "Arceus VSTAR",
    "miraidon": "Miraidon ex",
    "koraidon": "Koraidon ex",
    "iron-hands": "Iron Hands ex",
    "iron-valiant": "Iron Valiant ex",
    "roaring-moon": "Roaring Moon ex",
    "gholdengo": "Gholdengo ex",
    "terapagos": "Terapagos ex",
    "archaludon": "Archaludon ex",
    "regidrago": "Regidrago VSTAR",
    "chien-pao": "Chien-Pao ex",
    "comfey-sableye": "Lost Zone Box",
    "sableye-comfey": "Lost Zone Box",
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
        self.sprite_map = sprite_map or SPRITE_ARCHETYPE_MAP

    def resolve(
        self,
        sprite_urls: list[str],
        html_archetype: str,
        decklist: list[dict] | None = None,
    ) -> tuple[str, str, str]:
        """Resolve archetype through priority chain.

        Args:
            sprite_urls: Sprite image URLs from the placement.
            html_archetype: Raw archetype text from HTML scraping.
            decklist: Optional decklist for signature-card detection.

        Returns:
            Tuple of (archetype, raw_archetype, detection_method).
        """
        raw_archetype = html_archetype

        # Priority 1: sprite_lookup
        if sprite_urls:
            sprite_key = self.build_sprite_key(sprite_urls)
            if sprite_key and sprite_key in self.sprite_map:
                return (
                    self.sprite_map[sprite_key],
                    raw_archetype,
                    "sprite_lookup",
                )

            # Priority 2: auto_derive
            if sprite_key:
                derived = self.derive_name_from_key(sprite_key)
                if derived:
                    return derived, raw_archetype, "auto_derive"

        # Priority 3: signature_card
        if decklist:
            detected = self.detector.detect(decklist)
            if detected != "Rogue":
                return detected, raw_archetype, "signature_card"

        # Priority 4: text_label
        normalized = normalize_archetype(html_archetype)
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
