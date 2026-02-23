"""Tests for _batch_lookup_cards Step 0: direct limitless_id lookup."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.routers.meta import _batch_lookup_cards


def _make_limitless_row(
    limitless_id: str,
    name: str,
    japanese_name: str | None,
    image_small: str | None,
) -> MagicMock:
    """Create a mock Row returned by the limitless_id SELECT."""
    row = MagicMock()
    row.limitless_id = limitless_id
    row.name = name
    row.japanese_name = japanese_name
    row.image_small = image_small
    return row


def _make_variant_row(
    card_id: str,
    name: str,
    japanese_name: str | None,
    image_small: str | None,
) -> MagicMock:
    """Create a mock Row returned by the Card.id SELECT (Step 1)."""
    row = MagicMock()
    row.id = card_id
    row.name = name
    row.japanese_name = japanese_name
    row.image_small = image_small
    return row


def _make_execute_result(rows: list) -> MagicMock:
    """Wrap a list of rows in a mock execute result."""
    result = MagicMock()
    result.all.return_value = rows
    return result


@pytest.mark.asyncio
async def test_resolves_via_limitless_id() -> None:
    """Card with limitless_id resolves immediately without variant fallback."""
    db = AsyncMock()

    limitless_row = _make_limitless_row(
        limitless_id="OBF-125",
        name="Gardevoir ex",
        japanese_name=None,
        image_small="https://example.com/gardevoir.webp",
    )

    # Step 0 returns the card; short-circuit means no further execute calls.
    db.execute.return_value = _make_execute_result([limitless_row])

    result = await _batch_lookup_cards(["OBF-125"], db)

    assert result == {
        "OBF-125": ("Gardevoir ex", "https://example.com/gardevoir.webp"),
    }
    # Only one DB round-trip (Step 0 short-circuits).
    assert db.execute.call_count == 1


@pytest.mark.asyncio
async def test_falls_through_to_variant_lookup() -> None:
    """Card without limitless_id still resolves via variant matching (Step 1)."""
    db = AsyncMock()

    # Step 0: limitless_id lookup returns nothing.
    limitless_result = _make_execute_result([])

    # Step 1: variant-based Card.id lookup returns the card.
    # sv3-125 generates variants including sv03-125; DB stores sv03-125.
    variant_row = _make_variant_row(
        card_id="sv03-125",
        name="Pidgeot ex",
        japanese_name=None,
        image_small="https://example.com/pidgeot.webp",
    )
    variant_result = _make_execute_result([variant_row])

    # Step 2: no missing IDs after Step 1, so mapping query is never called.
    # Use side_effect to return different results per execute call.
    db.execute.side_effect = [limitless_result, variant_result]

    result = await _batch_lookup_cards(["sv3-125"], db)

    assert "sv3-125" in result
    assert result["sv3-125"] == ("Pidgeot ex", "https://example.com/pidgeot.webp")


@pytest.mark.asyncio
async def test_mixed_limitless_and_variant() -> None:
    """IDs that have limitless_id resolve via Step 0; others via Step 1."""
    db = AsyncMock()

    # "OBF-125" resolves via limitless_id; "sv3-76" does not.
    limitless_row = _make_limitless_row(
        limitless_id="OBF-125",
        name="Gardevoir ex",
        japanese_name=None,
        image_small="https://example.com/gardevoir.webp",
    )
    limitless_result = _make_execute_result([limitless_row])

    # Step 1: sv3-76 -> DB stores sv03-076
    variant_row = _make_variant_row(
        card_id="sv03-076",
        name="Charizard ex",
        japanese_name=None,
        image_small="https://example.com/charizard.webp",
    )
    variant_result = _make_execute_result([variant_row])

    db.execute.side_effect = [limitless_result, variant_result]

    result = await _batch_lookup_cards(["OBF-125", "sv3-76"], db)

    assert result["OBF-125"] == (
        "Gardevoir ex",
        "https://example.com/gardevoir.webp",
    )
    assert result["sv3-76"] == (
        "Charizard ex",
        "https://example.com/charizard.webp",
    )


@pytest.mark.asyncio
async def test_empty_card_ids_returns_empty() -> None:
    """Empty input list returns an empty dict without touching the DB."""
    db = AsyncMock()

    result = await _batch_lookup_cards([], db)

    assert result == {}
    db.execute.assert_not_called()
