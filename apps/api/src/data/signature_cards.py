"""Signature card mappings for archetype detection.

Maps card IDs to their archetype names. These are the primary identity cards
that define a deck's archetype. A deck containing a signature card is classified
as that archetype.

Card IDs follow TCGdex format: "{set_id}-{card_number}"
"""

# Scarlet & Violet era signature cards
SIGNATURE_CARDS: dict[str, str] = {
    # Stellar Crown (sv7)
    "sv7-144": "Terapagos ex",
    "sv7-175": "Terapagos ex",  # Secret rare
    "sv7-161": "Archaludon ex",
    # Shrouded Fable (sv6pt5)
    "sv6pt5-99": "Dragapult ex",
    "sv6pt5-TG21": "Dragapult ex",
    # Twilight Masquerade (sv6)
    "sv6-88": "Dragapult ex",
    "sv6-130": "Dragapult ex",
    "sv6-178": "Dragapult ex",
    "sv6-91": "Greninja ex",
    "sv6-132": "Greninja ex",
    "sv6-125": "Bloodmoon Ursaluna ex",
    "sv6-95": "Cinderace ex",
    # Temporal Forces (sv5)
    "sv5-76": "Iron Thorns ex",
    "sv5-186": "Iron Thorns ex",
    "sv5-128": "Walking Wake ex",
    "sv5-173": "Walking Wake ex",
    "sv5-87": "Raging Bolt ex",
    "sv5-179": "Raging Bolt ex",
    "sv5-123": "Gouging Fire ex",
    # Paldean Fates (sv4pt5)
    "sv4pt5-55": "Charizard ex",
    # Paradox Rift (sv4)
    "sv4-76": "Iron Hands ex",
    "sv4-182": "Iron Hands ex",
    "sv4-69": "Iron Valiant ex",
    "sv4-180": "Iron Valiant ex",
    "sv4-223": "Roaring Moon ex",
    "sv4-109": "Roaring Moon ex",
    "sv4-181": "Roaring Moon ex",
    "sv4-124": "Ancient Box",  # Ancient Koraidon Box identifier
    "sv4-229": "Gholdengo ex",
    "sv4-139": "Gholdengo ex",
    # Obsidian Flames (sv3)
    "sv3-125": "Charizard ex",
    "sv3-183": "Charizard ex",
    "sv3-199": "Charizard ex",
    "sv3-223": "Charizard ex",
    "sv3-131": "Tyranitar ex",
    "sv3-201": "Tyranitar ex",
    # Paldea Evolved (sv2)
    "sv2-86": "Gardevoir ex",
    "sv2-171": "Gardevoir ex",
    "sv2-240": "Gardevoir ex",
    "sv2-245": "Gardevoir ex",
    "sv2-182": "Chien-Pao ex",
    "sv2-243": "Chien-Pao ex",
    "sv2-61": "Chien-Pao ex",
    # Scarlet & Violet Base (sv1)
    "sv1-54": "Miraidon ex",
    "sv1-227": "Miraidon ex",
    "sv1-244": "Miraidon ex",
    "sv1-81": "Koraidon ex",
    "sv1-247": "Koraidon ex",
    "sv1-231": "Koraidon ex",
    "sv1-208": "Lugia VSTAR",
    "sv1-211": "Arceus VSTAR",
    # SWSH-era cards still in Standard
    "swsh12pt5-46": "Lugia VSTAR",
    "swsh12pt5-139": "Lugia VSTAR",
    "swsh11-123": "Lugia VSTAR",
    "swsh11-186": "Lugia VSTAR",
    "swsh11-211": "Lugia VSTAR",
    "swsh9-114": "Origin Forme Palkia VSTAR",
    "swsh9-208": "Origin Forme Palkia VSTAR",
    "swsh9-167": "Origin Forme Palkia VSTAR",
    "swsh10-114": "Giratina VSTAR",
    "swsh10-131": "Giratina VSTAR",
    "swsh10-193": "Giratina VSTAR",
    # Common engines
    "sv3pt5-12": "Pidgeot ex Control",  # Pidgeot ex
    "sv3pt5-164": "Pidgeot ex Control",
    "sv3pt5-197": "Pidgeot ex Control",
    # Lost Zone Box
    "swsh11-95": "Lost Zone Box",  # Comfey (Lost Zone engine)
    "sv3pt5-9": "Lost Zone Box",  # Sableye
    # Regidrago VSTAR
    "swsh12pt5-109": "Regidrago VSTAR",
    "swsh12pt5-136": "Regidrago VSTAR",
    "swsh12pt5-GG11": "Regidrago VSTAR",
}

# Mapping from generic names to normalized archetype
# Includes JP image-extracted labels and common abbreviations
ARCHETYPE_ALIASES: dict[str, str] = {
    # Charizard ex
    "Zard": "Charizard ex",
    "Zard ex": "Charizard ex",
    "Charizard": "Charizard ex",
    "リザードンex": "Charizard ex",
    # Gardevoir ex
    "Gard": "Gardevoir ex",
    "Gardevoir": "Gardevoir ex",
    "サーナイトex": "Gardevoir ex",
    # Chien-Pao ex
    "Pao": "Chien-Pao ex",
    "Chien-Pao": "Chien-Pao ex",
    "パオジアンex": "Chien-Pao ex",
    # Origin Forme Palkia VSTAR
    "Palkia": "Origin Forme Palkia VSTAR",
    "Palkia VSTAR": "Origin Forme Palkia VSTAR",
    "パルキアVSTAR": "Origin Forme Palkia VSTAR",
    # Giratina VSTAR
    "Tina": "Giratina VSTAR",
    "Giratina": "Giratina VSTAR",
    "ギラティナVSTAR": "Giratina VSTAR",
    # Lost Zone Box
    "LZB": "Lost Zone Box",
    "Lost Box": "Lost Zone Box",
    "LostBox": "Lost Zone Box",
    "ロストバレット": "Lost Zone Box",
    # Raging Bolt ex
    "Raging Bolt": "Raging Bolt ex",
    "Bolt": "Raging Bolt ex",
    "タケルライコex": "Raging Bolt ex",
    # Dragapult ex
    "Dragapult": "Dragapult ex",
    "Draga": "Dragapult ex",
    "ドラパルトex": "Dragapult ex",
    # Cinderace ex (the deck causing issues)
    "Cinderace": "Cinderace ex",
    "エースバーンex": "Cinderace ex",
    # Terapagos ex
    "Terapagos": "Terapagos ex",
    "テラパゴスex": "Terapagos ex",
    # Archaludon ex
    "Archaludon": "Archaludon ex",
    "ブリジュラスex": "Archaludon ex",
    # Bloodmoon Ursaluna ex
    "Bloodmoon Ursaluna": "Bloodmoon Ursaluna ex",
    "Ursaluna": "Bloodmoon Ursaluna ex",
    "ガチグマex": "Bloodmoon Ursaluna ex",
    # Greninja ex
    "Greninja": "Greninja ex",
    "ゲッコウガex": "Greninja ex",
    # Iron Thorns ex
    "Iron Thorns": "Iron Thorns ex",
    "テツノイバラex": "Iron Thorns ex",
    # Walking Wake ex
    "Walking Wake": "Walking Wake ex",
    "ウネルミナモex": "Walking Wake ex",
    # Gouging Fire ex
    "Gouging Fire": "Gouging Fire ex",
    "タギングルex": "Gouging Fire ex",
    # Iron Hands ex
    "Iron Hands": "Iron Hands ex",
    "テツノカイナex": "Iron Hands ex",
    # Iron Valiant ex
    "Iron Valiant": "Iron Valiant ex",
    "テツノブジンex": "Iron Valiant ex",
    # Roaring Moon ex
    "Roaring Moon": "Roaring Moon ex",
    "トドロクツキex": "Roaring Moon ex",
    # Gholdengo ex
    "Gholdengo": "Gholdengo ex",
    "サーフゴーex": "Gholdengo ex",
    # Tyranitar ex
    "Tyranitar": "Tyranitar ex",
    "バンギラスex": "Tyranitar ex",
    # Miraidon ex
    "Miraidon": "Miraidon ex",
    "ミライドンex": "Miraidon ex",
    # Koraidon ex
    "Koraidon": "Koraidon ex",
    "コライドンex": "Koraidon ex",
    # Lugia VSTAR
    "Lugia": "Lugia VSTAR",
    "ルギアVSTAR": "Lugia VSTAR",
    # Arceus VSTAR
    "Arceus": "Arceus VSTAR",
    "アルセウスVSTAR": "Arceus VSTAR",
    # Pidgeot ex Control
    "Pidgeot": "Pidgeot ex Control",
    "Pidgeot ex": "Pidgeot ex Control",
    "ピジョットex": "Pidgeot ex Control",
    # Regidrago VSTAR
    "Regidrago": "Regidrago VSTAR",
    "レジドラゴVSTAR": "Regidrago VSTAR",
}

# Build a case-insensitive lookup from the aliases
_ALIASES_LOWER: dict[str, str] = {k.lower(): v for k, v in ARCHETYPE_ALIASES.items()}


def normalize_archetype(archetype: str) -> str:
    """Normalize an archetype name to its canonical form.

    Performs case-insensitive alias lookup. Returns "Unknown" for
    empty or whitespace-only input.

    Args:
        archetype: The archetype name to normalize.

    Returns:
        The normalized archetype name.
    """
    if not archetype or not archetype.strip():
        return "Unknown"
    return _ALIASES_LOWER.get(archetype.lower(), archetype)
