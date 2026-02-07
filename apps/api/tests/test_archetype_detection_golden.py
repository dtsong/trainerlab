"""Golden dataset regression tests for archetype detection.

Curated dataset of known placements with verified archetypes.
Rich diagnostic output on failure for debugging.
"""

from __future__ import annotations

import json

import pytest

from src.services.archetype_normalizer import (
    SPRITE_ARCHETYPE_MAP,
    ArchetypeNormalizer,
)

# Golden dataset: each entry has sprite_urls, html_archetype,
# expected_archetype, and expected_method.
GOLDEN_DATASET = [
    # --- Charizard variants ---
    {
        "name": "Charizard single sprite",
        "sprite_urls": ["https://r2.limitlesstcg.net/pokemon/gen9/charizard.png"],
        "html_archetype": "Charizard ex",
        "expected_archetype": "Charizard ex",
        "expected_method": "sprite_lookup",
    },
    {
        "name": "Charizard Pidgeot composite",
        "sprite_urls": [
            "https://r2.limitlesstcg.net/pokemon/gen9/charizard.png",
            "https://r2.limitlesstcg.net/pokemon/gen9/pidgeot.png",
        ],
        "html_archetype": "Unknown",
        "expected_archetype": "Charizard ex",
        "expected_method": "sprite_lookup",
    },
    {
        "name": "Charizard Dusknoir composite",
        "sprite_urls": [
            "https://r2.limitlesstcg.net/pokemon/gen9/charizard.png",
            "https://r2.limitlesstcg.net/pokemon/gen9/dusknoir.png",
        ],
        "html_archetype": "Unknown",
        "expected_archetype": "Charizard ex",
        "expected_method": "sprite_lookup",
    },
    # --- Dragapult variants ---
    {
        "name": "Dragapult single",
        "sprite_urls": ["https://r2.limitlesstcg.net/pokemon/gen9/dragapult.png"],
        "html_archetype": "Dragapult ex",
        "expected_archetype": "Dragapult ex",
        "expected_method": "sprite_lookup",
    },
    {
        "name": "Dragapult Pidgeot",
        "sprite_urls": [
            "https://r2.limitlesstcg.net/pokemon/gen9/dragapult.png",
            "https://r2.limitlesstcg.net/pokemon/gen9/pidgeot.png",
        ],
        "html_archetype": "Unknown",
        "expected_archetype": "Dragapult ex",
        "expected_method": "sprite_lookup",
    },
    # --- Gardevoir ---
    {
        "name": "Gardevoir",
        "sprite_urls": ["https://r2.limitlesstcg.net/pokemon/gen9/gardevoir.png"],
        "html_archetype": "Gardevoir ex",
        "expected_archetype": "Gardevoir ex",
        "expected_method": "sprite_lookup",
    },
    # --- Raging Bolt ---
    {
        "name": "Raging Bolt",
        "sprite_urls": ["https://r2.limitlesstcg.net/pokemon/gen9/raging-bolt.png"],
        "html_archetype": "Raging Bolt ex",
        "expected_archetype": "Raging Bolt ex",
        "expected_method": "sprite_lookup",
    },
    {
        "name": "Ogerpon Raging Bolt",
        "sprite_urls": [
            "https://r2.limitlesstcg.net/pokemon/gen9/ogerpon.png",
            "https://r2.limitlesstcg.net/pokemon/gen9/raging-bolt.png",
        ],
        "html_archetype": "Unknown",
        "expected_archetype": "Raging Bolt ex",
        "expected_method": "sprite_lookup",
    },
    # --- Gholdengo ---
    {
        "name": "Gholdengo",
        "sprite_urls": ["https://r2.limitlesstcg.net/pokemon/gen9/gholdengo.png"],
        "html_archetype": "Gholdengo ex",
        "expected_archetype": "Gholdengo ex",
        "expected_method": "sprite_lookup",
    },
    # --- Terapagos ---
    {
        "name": "Terapagos",
        "sprite_urls": ["https://r2.limitlesstcg.net/pokemon/gen9/terapagos.png"],
        "html_archetype": "Terapagos ex",
        "expected_archetype": "Terapagos ex",
        "expected_method": "sprite_lookup",
    },
    # --- Archaludon ---
    {
        "name": "Archaludon",
        "sprite_urls": ["https://r2.limitlesstcg.net/pokemon/gen9/archaludon.png"],
        "html_archetype": "Archaludon ex",
        "expected_archetype": "Archaludon ex",
        "expected_method": "sprite_lookup",
    },
    # --- Pidgeot Control ---
    {
        "name": "Pidgeot Control",
        "sprite_urls": ["https://r2.limitlesstcg.net/pokemon/gen9/pidgeot.png"],
        "html_archetype": "Pidgeot ex",
        "expected_archetype": "Pidgeot ex Control",
        "expected_method": "sprite_lookup",
    },
    # --- Lost Zone ---
    {
        "name": "Lost Zone Giratina",
        "sprite_urls": [
            "https://r2.limitlesstcg.net/pokemon/gen9/comfey.png",
            "https://r2.limitlesstcg.net/pokemon/gen9/giratina.png",
        ],
        "html_archetype": "Unknown",
        "expected_archetype": "Lost Zone Giratina",
        "expected_method": "sprite_lookup",
    },
    {
        "name": "Lost Zone Box",
        "sprite_urls": [
            "https://r2.limitlesstcg.net/pokemon/gen9/comfey.png",
            "https://r2.limitlesstcg.net/pokemon/gen9/sableye.png",
        ],
        "html_archetype": "Unknown",
        "expected_archetype": "Lost Zone Box",
        "expected_method": "sprite_lookup",
    },
    # --- Chien-Pao ---
    {
        "name": "Chien-Pao",
        "sprite_urls": ["https://r2.limitlesstcg.net/pokemon/gen9/chien-pao.png"],
        "html_archetype": "Chien-Pao ex",
        "expected_archetype": "Chien-Pao ex",
        "expected_method": "sprite_lookup",
    },
    {
        "name": "Baxcalibur Chien-Pao",
        "sprite_urls": [
            "https://r2.limitlesstcg.net/pokemon/gen9/baxcalibur.png",
            "https://r2.limitlesstcg.net/pokemon/gen9/chien-pao.png",
        ],
        "html_archetype": "Unknown",
        "expected_archetype": "Chien-Pao ex",
        "expected_method": "sprite_lookup",
    },
    # --- Mega archetypes (JP) ---
    {
        "name": "Mega Absol",
        "sprite_urls": ["https://r2.limitlesstcg.net/pokemon/gen9/absol-mega.png"],
        "html_archetype": "Unknown",
        "expected_archetype": "Mega Absol ex",
        "expected_method": "sprite_lookup",
    },
    {
        "name": "Mega Absol Box (composite)",
        "sprite_urls": [
            "https://r2.limitlesstcg.net/pokemon/gen9/absol-mega.png",
            "https://r2.limitlesstcg.net/pokemon/gen9/kangaskhan-mega.png",
        ],
        "html_archetype": "Unknown",
        "expected_archetype": "Mega Absol Box",
        "expected_method": "sprite_lookup",
    },
    # --- JP meta archetypes ---
    {
        "name": "Grimmsnarl",
        "sprite_urls": ["https://r2.limitlesstcg.net/pokemon/gen9/grimmsnarl.png"],
        "html_archetype": "Grimmsnarl",
        "expected_archetype": "Grimmsnarl ex",
        "expected_method": "sprite_lookup",
    },
    {
        "name": "Noctowl Box",
        "sprite_urls": ["https://r2.limitlesstcg.net/pokemon/gen9/noctowl.png"],
        "html_archetype": "Noctowl",
        "expected_archetype": "Noctowl Box",
        "expected_method": "sprite_lookup",
    },
    {
        "name": "Ceruledge",
        "sprite_urls": ["https://r2.limitlesstcg.net/pokemon/gen9/ceruledge.png"],
        "html_archetype": "Ceruledge",
        "expected_archetype": "Ceruledge ex",
        "expected_method": "sprite_lookup",
    },
    {
        "name": "Froslass Munkidori",
        "sprite_urls": [
            "https://r2.limitlesstcg.net/pokemon/gen9/froslass.png",
            "https://r2.limitlesstcg.net/pokemon/gen9/munkidori.png",
        ],
        "html_archetype": "Unknown",
        "expected_archetype": "Froslass Munkidori",
        "expected_method": "sprite_lookup",
    },
    # --- Auto-derive (unknown sprite key) ---
    {
        "name": "Unknown single sprite falls to auto_derive",
        "sprite_urls": ["https://r2.limitlesstcg.net/pokemon/gen9/newpokemon.png"],
        "html_archetype": "Unknown",
        "expected_archetype": "Newpokemon",
        "expected_method": "auto_derive",
    },
    {
        "name": "Unknown composite falls to auto_derive",
        "sprite_urls": [
            "https://r2.limitlesstcg.net/pokemon/gen9/alpha.png",
            "https://r2.limitlesstcg.net/pokemon/gen9/beta.png",
        ],
        "html_archetype": "Unknown",
        "expected_archetype": "Alpha Beta",
        "expected_method": "auto_derive",
    },
    # --- Text label fallback (no sprites) ---
    {
        "name": "No sprites, text label",
        "sprite_urls": [],
        "html_archetype": "Some Deck Name",
        "expected_archetype": "Some Deck Name",
        "expected_method": "text_label",
    },
    {
        "name": "Empty sprites, Unknown text",
        "sprite_urls": [],
        "html_archetype": "Unknown",
        "expected_archetype": "Unknown",
        "expected_method": "text_label",
    },
]


def _build_test_id(entry: dict) -> str:
    return entry["name"].lower().replace(" ", "_")


@pytest.mark.parametrize(
    "entry",
    GOLDEN_DATASET,
    ids=[_build_test_id(e) for e in GOLDEN_DATASET],
)
def test_golden_archetype_detection(entry: dict) -> None:
    """Verify archetype detection against curated golden dataset."""
    normalizer = ArchetypeNormalizer()
    archetype, _raw, method = normalizer.resolve(
        entry["sprite_urls"],
        entry["html_archetype"],
    )

    if archetype != entry["expected_archetype"] or method != entry["expected_method"]:
        # Build sprite key for diagnostics
        sprite_key = normalizer.build_sprite_key(entry["sprite_urls"])
        diagnostic = {
            "test": entry["name"],
            "expected_archetype": entry["expected_archetype"],
            "got_archetype": archetype,
            "expected_method": entry["expected_method"],
            "got_method": method,
            "sprite_urls": entry["sprite_urls"],
            "sprite_key": sprite_key,
            "in_sprite_map": sprite_key in SPRITE_ARCHETYPE_MAP,
            "sprite_map_value": SPRITE_ARCHETYPE_MAP.get(sprite_key),
        }
        pytest.fail(f"Archetype mismatch:\n{json.dumps(diagnostic, indent=2)}")
