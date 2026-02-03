"""Card reprint mappings for treating the same card across sets as identical.

Maps card_id to a canonical card name so that reprints/alt arts are treated
as the same card when computing consensus decklists and diffs.
"""

# Maps card_id → canonical card name for cards with known reprints.
# Only needs to cover cards that appear across multiple sets in competitive play.
# Cards not in this mapping fall back to their decklist-provided name.
CARD_REPRINTS: dict[str, str] = {
    # Boss's Orders (various prints)
    "sv2-172": "Boss's Orders",
    "sv3-172": "Boss's Orders",
    "sv4-172": "Boss's Orders",
    "swsh9-132": "Boss's Orders",
    "swsh11-154": "Boss's Orders",
    # Professor's Research (various prints)
    "sv1-190": "Professor's Research",
    "sv2-189": "Professor's Research",
    "sv4-168": "Professor's Research",
    "swsh12pt5-78": "Professor's Research",
    # Rare Candy
    "sv1-191": "Rare Candy",
    "sv4-191": "Rare Candy",
    "swsh12pt5-69": "Rare Candy",
    # Ultra Ball
    "sv1-196": "Ultra Ball",
    "sv4-196": "Ultra Ball",
    "swsh9-150": "Ultra Ball",
    # Nest Ball
    "sv1-181": "Nest Ball",
    "sv5-181": "Nest Ball",
    # Switch
    "sv1-194": "Switch",
    "sv3-194": "Switch",
    # Super Rod
    "sv2-188": "Super Rod",
    "sv5-188": "Super Rod",
    # Iono
    "sv1-185": "Iono",
    "sv4pt5-80": "Iono",
    "sv6-178": "Iono",
    # Arven
    "sv1-166": "Arven",
    "sv3-166": "Arven",
    # Energy (basic energy reprints across sets)
    "sv1-svE-1": "Basic Fire Energy",
    "sv1-svE-2": "Basic Water Energy",
    "sv1-svE-3": "Basic Grass Energy",
    "sv1-svE-4": "Basic Lightning Energy",
    "sv1-svE-5": "Basic Psychic Energy",
    "sv1-svE-6": "Basic Fighting Energy",
    "sv1-svE-7": "Basic Darkness Energy",
    "sv1-svE-8": "Basic Metal Energy",
}
