"""Tests for SQLAlchemy models."""

from datetime import date
from uuid import uuid4

from src.models import (
    Card,
    Deck,
    MetaSnapshot,
    Set,
    Tournament,
    TournamentPlacement,
    User,
)


def test_set_model() -> None:
    """Test Set model instantiation."""
    card_set = Set(
        id="sv4",
        name="Paradox Rift",
        series="Scarlet & Violet",
        card_count=182,
    )
    assert card_set.id == "sv4"
    assert card_set.name == "Paradox Rift"


def test_card_model() -> None:
    """Test Card model instantiation."""
    card = Card(
        id="sv4-6",
        local_id="6",
        name="Charizard ex",
        supertype="Pokemon",
        subtypes=["Stage 2", "ex"],
        types=["Fire"],
        hp=330,
        set_id="sv4",
    )
    assert card.id == "sv4-6"
    assert card.name == "Charizard ex"
    assert card.hp == 330


def test_user_model() -> None:
    """Test User model instantiation."""
    user = User(
        id=uuid4(),
        auth_provider_id="google-123",
        email="trainer@example.com",
        display_name="Ash Ketchum",
    )
    assert user.email == "trainer@example.com"


def test_deck_model() -> None:
    """Test Deck model instantiation."""
    deck = Deck(
        id=uuid4(),
        user_id=uuid4(),
        name="Charizard ex Deck",
        cards=[{"card_id": "sv4-6", "quantity": 3}],
        format="standard",
        archetype="Charizard ex",
    )
    assert deck.name == "Charizard ex Deck"
    assert len(deck.cards) == 1


def test_tournament_model() -> None:
    """Test Tournament model instantiation."""
    tournament = Tournament(
        id=uuid4(),
        name="LAIC 2024",
        date=date(2024, 11, 15),
        region="NA",
        format="standard",
        best_of=3,
        participant_count=1200,
    )
    assert tournament.name == "LAIC 2024"
    assert tournament.best_of == 3


def test_tournament_placement_model() -> None:
    """Test TournamentPlacement model instantiation."""
    placement = TournamentPlacement(
        id=uuid4(),
        tournament_id=uuid4(),
        placement=1,
        player_name="Winner",
        archetype="Charizard ex",
    )
    assert placement.placement == 1
    assert placement.archetype == "Charizard ex"


def test_meta_snapshot_model() -> None:
    """Test MetaSnapshot model instantiation."""
    snapshot = MetaSnapshot(
        id=uuid4(),
        snapshot_date=date(2024, 11, 20),
        region="NA",
        format="standard",
        best_of=3,
        archetype_shares={"Charizard ex": 0.15, "Lugia VSTAR": 0.12},
        sample_size=500,
    )
    assert snapshot.format == "standard"
    assert snapshot.archetype_shares["Charizard ex"] == 0.15
