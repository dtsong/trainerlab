"""Tests for deck endpoints and service."""

from datetime import UTC
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.models.card import Card
from src.models.deck import Deck
from src.models.user import User
from src.schemas import CardInDeck, DeckCreate, DeckUpdate, PaginatedResponse
from src.services.deck_export import DeckExportService
from src.services.deck_import import DeckImportService
from src.services.deck_service import CardValidationError, DeckService


class TestDeckService:
    """Tests for DeckService."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Create a mock async session."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> DeckService:
        """Create a DeckService with mock session."""
        return DeckService(mock_session)

    @pytest.fixture
    def sample_user(self) -> MagicMock:
        """Create a sample user mock."""
        user = MagicMock(spec=User)
        user.id = uuid4()
        user.username = "testuser"
        return user

    @pytest.fixture
    def sample_deck(self, sample_user: MagicMock) -> MagicMock:
        """Create a sample deck mock."""
        from datetime import datetime

        deck = MagicMock(spec=Deck)
        deck.id = uuid4()
        deck.user_id = sample_user.id
        deck.name = "Test Deck"
        deck.description = "A test deck"
        deck.cards = [{"card_id": "sv4-6", "quantity": 4}]
        deck.format = "standard"
        deck.archetype = None
        deck.is_public = False
        deck.share_code = None
        deck.created_at = datetime.now(UTC)
        deck.updated_at = datetime.now(UTC)
        deck.user = sample_user
        return deck

    @pytest.mark.asyncio
    async def test_create_deck_success(
        self, service: DeckService, sample_user: MagicMock
    ) -> None:
        """Test creating a deck successfully."""
        from datetime import datetime

        deck_data = DeckCreate(
            name="My New Deck",
            description="A cool deck",
            cards=[],
            format="standard",
            is_public=False,
        )

        # Mock the session operations
        service.session.add = MagicMock()
        service.session.commit = AsyncMock()

        # Mock refresh to set server-side defaults
        async def mock_refresh(obj, attrs=None):
            obj.created_at = datetime.now(UTC)
            obj.updated_at = datetime.now(UTC)

        service.session.refresh = AsyncMock(side_effect=mock_refresh)

        result = await service.create_deck(sample_user, deck_data)

        assert result.name == "My New Deck"
        assert result.description == "A cool deck"
        assert result.format == "standard"
        assert result.is_public is False
        service.session.add.assert_called_once()
        service.session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_deck_with_cards_validates(
        self, service: DeckService, sample_user: MagicMock
    ) -> None:
        """Test that card IDs are validated when creating a deck."""
        from datetime import datetime

        from src.schemas import CardInDeck

        deck_data = DeckCreate(
            name="Deck with Cards",
            cards=[CardInDeck(card_id="sv4-6", quantity=4)],
            format="standard",
            is_public=False,
        )

        # Mock card validation - cards exist
        mock_result = MagicMock()
        mock_result.all.return_value = [("sv4-6",)]
        service.session.execute = AsyncMock(return_value=mock_result)
        service.session.add = MagicMock()
        service.session.commit = AsyncMock()

        # Mock refresh to set server-side defaults
        async def mock_refresh(obj, attrs=None):
            obj.created_at = datetime.now(UTC)
            obj.updated_at = datetime.now(UTC)

        service.session.refresh = AsyncMock(side_effect=mock_refresh)

        result = await service.create_deck(sample_user, deck_data)

        assert result.name == "Deck with Cards"
        assert len(result.cards) == 1
        assert result.cards[0].card_id == "sv4-6"

    @pytest.mark.asyncio
    async def test_create_deck_invalid_card_raises(
        self, service: DeckService, sample_user: MagicMock
    ) -> None:
        """Test that invalid card IDs raise CardValidationError."""
        from src.schemas import CardInDeck

        deck_data = DeckCreate(
            name="Invalid Deck",
            cards=[CardInDeck(card_id="nonexistent-card", quantity=4)],
            format="standard",
            is_public=False,
        )

        # Mock card validation - cards don't exist
        mock_result = MagicMock()
        mock_result.all.return_value = []
        service.session.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(CardValidationError, match="Card IDs not found"):
            await service.create_deck(sample_user, deck_data)

    @pytest.mark.asyncio
    async def test_list_user_decks_empty(
        self, service: DeckService, sample_user: MagicMock
    ) -> None:
        """Test listing decks when user has none."""
        # Mock empty results
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        service.session.execute = AsyncMock(
            side_effect=[
                MagicMock(scalar=MagicMock(return_value=0)),  # count query
                mock_result,  # main query
            ]
        )

        result = await service.list_user_decks(sample_user)

        assert isinstance(result, PaginatedResponse)
        assert result.items == []
        assert result.total == 0
        assert result.page == 1
        assert result.has_next is False
        assert result.has_prev is False

    @pytest.mark.asyncio
    async def test_list_user_decks_with_results(
        self, service: DeckService, sample_user: MagicMock, sample_deck: MagicMock
    ) -> None:
        """Test listing decks with results."""
        # Mock results with one deck
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_deck]
        service.session.execute = AsyncMock(
            side_effect=[
                MagicMock(scalar=MagicMock(return_value=1)),  # count query
                mock_result,  # main query
            ]
        )

        result = await service.list_user_decks(sample_user)

        assert len(result.items) == 1
        assert result.items[0].name == "Test Deck"
        assert result.items[0].card_count == 4  # 1 card with quantity 4
        assert result.total == 1

    @pytest.mark.asyncio
    async def test_list_user_decks_pagination(
        self, service: DeckService, sample_user: MagicMock, sample_deck: MagicMock
    ) -> None:
        """Test pagination calculations for deck listing."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_deck]
        service.session.execute = AsyncMock(
            side_effect=[
                MagicMock(scalar=MagicMock(return_value=50)),  # total count
                mock_result,
            ]
        )

        result = await service.list_user_decks(sample_user, page=2, limit=20)

        assert result.page == 2
        assert result.limit == 20
        assert result.total == 50
        assert result.has_next is True
        assert result.has_prev is True

    @pytest.mark.asyncio
    async def test_list_public_decks(
        self, service: DeckService, sample_deck: MagicMock
    ) -> None:
        """Test listing public decks."""
        sample_deck.is_public = True

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_deck]
        service.session.execute = AsyncMock(
            side_effect=[
                MagicMock(scalar=MagicMock(return_value=1)),  # total count
                mock_result,
            ]
        )

        result = await service.list_public_decks()

        assert len(result.items) == 1
        assert result.total == 1

    @pytest.mark.asyncio
    async def test_list_public_decks_with_filters(
        self, service: DeckService, sample_deck: MagicMock
    ) -> None:
        """Test listing public decks with format filter."""
        sample_deck.is_public = True
        sample_deck.format = "standard"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_deck]
        service.session.execute = AsyncMock(
            side_effect=[
                MagicMock(scalar=MagicMock(return_value=1)),  # total count
                mock_result,
            ]
        )

        result = await service.list_public_decks(format="standard")

        assert len(result.items) == 1

    @pytest.mark.asyncio
    async def test_list_public_decks_with_archetype_filter(
        self, service: DeckService, sample_deck: MagicMock
    ) -> None:
        """Test listing public decks with archetype filter."""
        sample_deck.is_public = True
        sample_deck.archetype = "Charizard"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_deck]
        service.session.execute = AsyncMock(
            side_effect=[
                MagicMock(scalar=MagicMock(return_value=1)),  # total count
                mock_result,
            ]
        )

        result = await service.list_public_decks(archetype="Charizard")

        assert len(result.items) == 1
        assert result.items[0].archetype == "Charizard"

    @pytest.mark.asyncio
    async def test_get_deck_public(
        self, service: DeckService, sample_deck: MagicMock
    ) -> None:
        """Test getting a public deck without authentication."""
        sample_deck.is_public = True

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_deck
        service.session.execute = AsyncMock(return_value=mock_result)

        result = await service.get_deck(sample_deck.id, user=None)

        assert result is not None
        assert result.id == sample_deck.id
        assert result.name == "Test Deck"

    @pytest.mark.asyncio
    async def test_get_deck_private_owner(
        self, service: DeckService, sample_user: MagicMock, sample_deck: MagicMock
    ) -> None:
        """Test getting a private deck as the owner."""
        sample_deck.is_public = False

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_deck
        service.session.execute = AsyncMock(return_value=mock_result)

        result = await service.get_deck(sample_deck.id, user=sample_user)

        assert result is not None
        assert result.id == sample_deck.id

    @pytest.mark.asyncio
    async def test_get_deck_private_not_owner(
        self, service: DeckService, sample_deck: MagicMock
    ) -> None:
        """Test getting a private deck as a different user returns None."""
        sample_deck.is_public = False

        other_user = MagicMock(spec=User)
        other_user.id = uuid4()  # Different user ID

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_deck
        service.session.execute = AsyncMock(return_value=mock_result)

        result = await service.get_deck(sample_deck.id, user=other_user)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_deck_private_no_auth(
        self, service: DeckService, sample_deck: MagicMock
    ) -> None:
        """Test getting a private deck without auth returns None."""
        sample_deck.is_public = False

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_deck
        service.session.execute = AsyncMock(return_value=mock_result)

        result = await service.get_deck(sample_deck.id, user=None)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_deck_not_found(self, service: DeckService) -> None:
        """Test getting a non-existent deck returns None."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        service.session.execute = AsyncMock(return_value=mock_result)

        result = await service.get_deck(uuid4(), user=None)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_deck_stats_empty_deck(
        self, service: DeckService, sample_deck: MagicMock
    ) -> None:
        """Test stats for an empty deck."""
        sample_deck.cards = []
        sample_deck.is_public = True

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_deck
        service.session.execute = AsyncMock(return_value=mock_result)

        result = await service.get_deck_stats(sample_deck.id, user=None)

        assert result is not None
        assert result.total_cards == 0
        assert result.average_hp is None
        assert result.type_breakdown.pokemon == 0

    @pytest.mark.asyncio
    async def test_get_deck_stats_with_cards(
        self, service: DeckService, sample_deck: MagicMock
    ) -> None:
        """Test stats for a deck with cards."""
        from src.models.card import Card

        sample_deck.cards = [
            {"card_id": "sv4-6", "quantity": 4},
            {"card_id": "sv4-1", "quantity": 2},
        ]
        sample_deck.is_public = True

        # Mock cards
        mock_pokemon = MagicMock(spec=Card)
        mock_pokemon.id = "sv4-6"
        mock_pokemon.supertype = "Pokemon"
        mock_pokemon.hp = 100
        mock_pokemon.attacks = [{"cost": ["Fire", "Fire"]}]

        mock_trainer = MagicMock(spec=Card)
        mock_trainer.id = "sv4-1"
        mock_trainer.supertype = "Trainer"
        mock_trainer.hp = None
        mock_trainer.attacks = None

        mock_deck_result = MagicMock()
        mock_deck_result.scalar_one_or_none.return_value = sample_deck
        mock_cards_result = MagicMock()
        mock_cards_result.scalars.return_value.all.return_value = [
            mock_pokemon,
            mock_trainer,
        ]

        service.session.execute = AsyncMock(
            side_effect=[mock_deck_result, mock_cards_result]
        )

        result = await service.get_deck_stats(sample_deck.id, user=None)

        assert result is not None
        assert result.total_cards == 6
        assert result.type_breakdown.pokemon == 4
        assert result.type_breakdown.trainer == 2
        assert result.average_hp == 100.0  # 4 Pokemon * 100 HP / 4

    @pytest.mark.asyncio
    async def test_get_deck_stats_not_found(self, service: DeckService) -> None:
        """Test stats for non-existent deck."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        service.session.execute = AsyncMock(return_value=mock_result)

        result = await service.get_deck_stats(uuid4(), user=None)

        assert result is None

    @pytest.mark.asyncio
    async def test_update_deck_success(
        self, service: DeckService, sample_user: MagicMock, sample_deck: MagicMock
    ) -> None:
        """Test updating a deck successfully."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_deck
        service.session.execute = AsyncMock(return_value=mock_result)
        service.session.commit = AsyncMock()
        service.session.refresh = AsyncMock()

        update_data = DeckUpdate(name="Updated Name")
        result = await service.update_deck(sample_deck.id, sample_user, update_data)

        assert result is not None
        assert sample_deck.name == "Updated Name"
        service.session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_deck_not_found(
        self, service: DeckService, sample_user: MagicMock
    ) -> None:
        """Test updating a non-existent deck returns None."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        service.session.execute = AsyncMock(return_value=mock_result)

        update_data = DeckUpdate(name="New Name")
        result = await service.update_deck(uuid4(), sample_user, update_data)

        assert result is None

    @pytest.mark.asyncio
    async def test_update_deck_not_owner(
        self, service: DeckService, sample_deck: MagicMock
    ) -> None:
        """Test updating a deck as non-owner returns None."""
        other_user = MagicMock(spec=User)
        other_user.id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_deck
        service.session.execute = AsyncMock(return_value=mock_result)

        update_data = DeckUpdate(name="New Name")
        result = await service.update_deck(sample_deck.id, other_user, update_data)

        assert result is None

    @pytest.mark.asyncio
    async def test_update_deck_validates_cards(
        self, service: DeckService, sample_user: MagicMock, sample_deck: MagicMock
    ) -> None:
        """Test updating deck cards validates card IDs."""
        from src.services.deck_service import CardValidationError

        # First call returns deck, second validates cards (empty = invalid)
        mock_deck_result = MagicMock()
        mock_deck_result.scalar_one_or_none.return_value = sample_deck
        mock_card_result = MagicMock()
        mock_card_result.all.return_value = []
        service.session.execute = AsyncMock(
            side_effect=[mock_deck_result, mock_card_result]
        )

        update_data = DeckUpdate(cards=[CardInDeck(card_id="nonexistent", quantity=4)])

        with pytest.raises(CardValidationError, match="Card IDs not found"):
            await service.update_deck(sample_deck.id, sample_user, update_data)

    @pytest.mark.asyncio
    async def test_delete_deck_success(
        self, service: DeckService, sample_user: MagicMock, sample_deck: MagicMock
    ) -> None:
        """Test deleting a deck successfully."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_deck
        service.session.execute = AsyncMock(return_value=mock_result)
        service.session.delete = AsyncMock()
        service.session.commit = AsyncMock()

        result = await service.delete_deck(sample_deck.id, sample_user)

        assert result is True
        service.session.delete.assert_called_once_with(sample_deck)
        service.session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_deck_not_found(
        self, service: DeckService, sample_user: MagicMock
    ) -> None:
        """Test deleting a non-existent deck returns False."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        service.session.execute = AsyncMock(return_value=mock_result)

        result = await service.delete_deck(uuid4(), sample_user)

        assert result is False

    @pytest.mark.asyncio
    async def test_delete_deck_not_owner(
        self, service: DeckService, sample_deck: MagicMock
    ) -> None:
        """Test deleting a deck as non-owner returns False."""
        other_user = MagicMock(spec=User)
        other_user.id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_deck
        service.session.execute = AsyncMock(return_value=mock_result)

        result = await service.delete_deck(sample_deck.id, other_user)

        assert result is False


class TestDeckExportService:
    """Tests for DeckExportService."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Create a mock async session."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> DeckExportService:
        """Create a DeckExportService with mock session."""
        return DeckExportService(mock_session)

    @pytest.fixture
    def sample_deck(self) -> MagicMock:
        """Create a sample deck mock."""
        deck = MagicMock(spec=Deck)
        deck.id = uuid4()
        deck.user_id = uuid4()
        deck.is_public = True
        deck.cards = []
        return deck

    @pytest.mark.asyncio
    async def test_export_ptcgo_empty_deck(
        self, service: DeckExportService, sample_deck: MagicMock
    ) -> None:
        """Test exporting an empty deck."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_deck
        service.session.execute = AsyncMock(return_value=mock_result)

        result = await service.export_ptcgo(sample_deck.id)

        assert result is not None
        assert "Total Cards - 0" in result
        assert "##Pokémon - 0" in result

    @pytest.mark.asyncio
    async def test_export_ptcgo_with_cards(
        self, service: DeckExportService, sample_deck: MagicMock
    ) -> None:
        """Test exporting a deck with cards."""
        sample_deck.cards = [
            {"card_id": "sv4-6", "quantity": 4},
            {"card_id": "sv4-189", "quantity": 2},
        ]

        # Mock cards
        mock_pokemon = MagicMock(spec=Card)
        mock_pokemon.id = "sv4-6"
        mock_pokemon.name = "Charizard ex"
        mock_pokemon.supertype = "Pokemon"
        mock_pokemon.set_id = "sv4"
        mock_pokemon.number = "6"

        mock_trainer = MagicMock(spec=Card)
        mock_trainer.id = "sv4-189"
        mock_trainer.name = "Professor's Research"
        mock_trainer.supertype = "Trainer"
        mock_trainer.set_id = "sv4"
        mock_trainer.number = "189"

        mock_deck_result = MagicMock()
        mock_deck_result.scalar_one_or_none.return_value = sample_deck
        mock_cards_result = MagicMock()
        mock_cards_result.scalars.return_value.all.return_value = [
            mock_pokemon,
            mock_trainer,
        ]

        service.session.execute = AsyncMock(
            side_effect=[mock_deck_result, mock_cards_result]
        )

        result = await service.export_ptcgo(sample_deck.id)

        assert result is not None
        assert "* 4 Charizard ex SV4 6" in result
        assert "* 2 Professor's Research SV4 189" in result
        assert "##Pokémon - 4" in result
        assert "##Trainer Cards - 2" in result
        assert "Total Cards - 6" in result

    @pytest.mark.asyncio
    async def test_export_ptcgo_not_found(self, service: DeckExportService) -> None:
        """Test export for non-existent deck returns None."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        service.session.execute = AsyncMock(return_value=mock_result)

        result = await service.export_ptcgo(uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_export_ptcgo_private_deck_no_auth(
        self, service: DeckExportService, sample_deck: MagicMock
    ) -> None:
        """Test export for private deck without auth returns None."""
        sample_deck.is_public = False

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_deck
        service.session.execute = AsyncMock(return_value=mock_result)

        result = await service.export_ptcgo(sample_deck.id, user=None)

        assert result is None


class TestDeckImportService:
    """Tests for DeckImportService."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Create a mock async session."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> DeckImportService:
        """Create a DeckImportService with mock session."""
        return DeckImportService(mock_session)

    @pytest.mark.asyncio
    async def test_import_ptcgo_format(self, service: DeckImportService) -> None:
        """Test importing a deck in PTCGO format."""
        deck_list = """****** Pokémon Trading Card Game Deck List ******

##Pokémon - 4
* 4 Charizard ex SV4 6

##Trainer Cards - 2
* 2 Professor's Research SV4 189

Total Cards - 6"""

        # Mock card lookup
        mock_charizard = MagicMock(spec=Card)
        mock_charizard.id = "sv4-6"
        mock_charizard.set_id = "sv4"
        mock_charizard.number = "6"

        mock_research = MagicMock(spec=Card)
        mock_research.id = "sv4-189"
        mock_research.set_id = "sv4"
        mock_research.number = "189"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            mock_charizard,
            mock_research,
        ]
        service.session.execute = AsyncMock(return_value=mock_result)

        result = await service.import_deck(deck_list)

        assert len(result.cards) == 2
        assert result.cards[0].card_id == "sv4-6"
        assert result.cards[0].quantity == 4
        assert result.cards[1].card_id == "sv4-189"
        assert result.cards[1].quantity == 2
        assert len(result.unmatched) == 0
        assert result.total_cards == 6

    @pytest.mark.asyncio
    async def test_import_pcl_format(self, service: DeckImportService) -> None:
        """Test importing a deck in Pokemon Card Live format."""
        deck_list = """Pokemon - 4
4 Charizard ex SV4 6

Trainer - 2
2 Professor's Research SV4 189

Total Cards - 6"""

        mock_charizard = MagicMock(spec=Card)
        mock_charizard.id = "sv4-6"
        mock_charizard.set_id = "sv4"
        mock_charizard.number = "6"

        mock_research = MagicMock(spec=Card)
        mock_research.id = "sv4-189"
        mock_research.set_id = "sv4"
        mock_research.number = "189"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            mock_charizard,
            mock_research,
        ]
        service.session.execute = AsyncMock(return_value=mock_result)

        result = await service.import_deck(deck_list)

        assert len(result.cards) == 2
        assert result.total_cards == 6

    @pytest.mark.asyncio
    async def test_import_with_unmatched_cards(
        self, service: DeckImportService
    ) -> None:
        """Test import with cards that don't exist in database."""
        deck_list = """* 4 Charizard ex SV4 6
* 2 Fake Card XYZ 999"""

        mock_charizard = MagicMock(spec=Card)
        mock_charizard.id = "sv4-6"
        mock_charizard.set_id = "sv4"
        mock_charizard.number = "6"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_charizard]
        service.session.execute = AsyncMock(return_value=mock_result)

        result = await service.import_deck(deck_list)

        assert len(result.cards) == 1
        assert result.cards[0].card_id == "sv4-6"
        assert len(result.unmatched) == 1
        assert result.unmatched[0].name == "Fake Card"
        assert result.unmatched[0].set_code == "XYZ"
        assert result.unmatched[0].number == "999"
        assert result.total_cards == 4

    @pytest.mark.asyncio
    async def test_import_empty_deck_list(self, service: DeckImportService) -> None:
        """Test importing an empty deck list."""
        result = await service.import_deck("")

        assert len(result.cards) == 0
        assert len(result.unmatched) == 0
        assert result.total_cards == 0

    @pytest.mark.asyncio
    async def test_import_duplicate_cards(self, service: DeckImportService) -> None:
        """Test importing a deck with duplicate card entries."""
        # Same card appears on multiple lines
        deck_list = """* 4 Charizard ex SV4 6
* 2 Charizard ex SV4 6"""

        mock_charizard = MagicMock(spec=Card)
        mock_charizard.id = "sv4-6"
        mock_charizard.set_id = "sv4"
        mock_charizard.number = "6"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_charizard]
        service.session.execute = AsyncMock(return_value=mock_result)

        result = await service.import_deck(deck_list)

        # Both entries should be matched (duplicates preserved, not merged)
        assert len(result.cards) == 2
        assert result.cards[0].card_id == "sv4-6"
        assert result.cards[0].quantity == 4
        assert result.cards[1].card_id == "sv4-6"
        assert result.cards[1].quantity == 2
        assert result.total_cards == 6

    @pytest.mark.asyncio
    async def test_import_card_with_letter_suffix(
        self, service: DeckImportService
    ) -> None:
        """Test importing cards with letter suffixes in card numbers."""
        deck_list = "* 1 Pikachu SWSH 25a"

        mock_card = MagicMock(spec=Card)
        mock_card.id = "swsh-25a"
        mock_card.set_id = "swsh"
        mock_card.number = "25a"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_card]
        service.session.execute = AsyncMock(return_value=mock_result)

        result = await service.import_deck(deck_list)

        assert len(result.cards) == 1
        assert result.cards[0].card_id == "swsh-25a"
        assert result.cards[0].quantity == 1

    @pytest.mark.asyncio
    async def test_import_all_unmatched(self, service: DeckImportService) -> None:
        """Test import when all cards fail to match."""
        deck_list = """* 4 Fake Card ABC 123
* 2 Another Fake XYZ 456"""

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        service.session.execute = AsyncMock(return_value=mock_result)

        result = await service.import_deck(deck_list)

        assert len(result.cards) == 0
        assert len(result.unmatched) == 2
        assert result.unmatched[0].name == "Fake Card"
        assert result.unmatched[1].name == "Another Fake"
        assert result.total_cards == 0

    @pytest.mark.asyncio
    async def test_import_case_insensitive_set_codes(
        self, service: DeckImportService
    ) -> None:
        """Test that set codes are matched case-insensitively."""
        deck_list = "* 4 Charizard ex sv4 6"  # lowercase set code

        mock_card = MagicMock(spec=Card)
        mock_card.id = "sv4-6"
        mock_card.set_id = "SV4"  # Database has uppercase
        mock_card.number = "6"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_card]
        service.session.execute = AsyncMock(return_value=mock_result)

        result = await service.import_deck(deck_list)

        assert len(result.cards) == 1
        assert result.cards[0].card_id == "sv4-6"

    @pytest.mark.asyncio
    async def test_import_with_malformed_lines(
        self, service: DeckImportService
    ) -> None:
        """Test that malformed lines are skipped without error."""
        deck_list = """Some random text
* 4 Charizard ex SV4 6
This line doesn't match
Pokemon - 4"""

        mock_card = MagicMock(spec=Card)
        mock_card.id = "sv4-6"
        mock_card.set_id = "sv4"
        mock_card.number = "6"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_card]
        service.session.execute = AsyncMock(return_value=mock_result)

        result = await service.import_deck(deck_list)

        # Only the valid line should be parsed
        assert len(result.cards) == 1
        assert len(result.unmatched) == 0


class TestDeckEndpoints:
    """Tests for deck API endpoints."""

    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        """Create a mock database session."""
        return AsyncMock()

    @pytest.fixture
    def mock_user(self) -> MagicMock:
        """Create a mock user."""
        user = MagicMock(spec=User)
        user.id = uuid4()
        user.username = "testuser"
        return user

    @pytest.fixture
    def client(self, mock_db: AsyncMock, mock_user: MagicMock) -> TestClient:
        """Create test client with mocked dependencies."""
        from src.db.database import get_db
        from src.dependencies.auth import get_current_user, get_current_user_optional

        async def override_get_db():
            yield mock_db

        async def override_get_current_user():
            return mock_user

        async def override_get_current_user_optional():
            return mock_user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_current_user_optional] = (
            override_get_current_user_optional
        )

        yield TestClient(app)

        app.dependency_overrides.clear()

    @pytest.fixture
    def unauthenticated_client(self, mock_db: AsyncMock) -> TestClient:
        """Create test client without authentication."""
        from src.db.database import get_db
        from src.dependencies.auth import get_current_user_optional

        async def override_get_db():
            yield mock_db

        async def override_get_current_user_optional():
            return None

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user_optional] = (
            override_get_current_user_optional
        )

        yield TestClient(app)

        app.dependency_overrides.clear()

    def test_create_deck_success(
        self, client: TestClient, mock_db: AsyncMock, mock_user: MagicMock
    ) -> None:
        """Test POST /api/v1/decks creates a deck."""
        from datetime import datetime

        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()

        # Mock refresh to set server-side defaults
        async def mock_refresh(obj, attrs=None):
            obj.created_at = datetime.now(UTC)
            obj.updated_at = datetime.now(UTC)

        mock_db.refresh = AsyncMock(side_effect=mock_refresh)

        response = client.post(
            "/api/v1/decks",
            json={
                "name": "New Deck",
                "description": "My first deck",
                "format": "standard",
                "is_public": False,
                "cards": [],
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Deck"
        assert data["description"] == "My first deck"
        assert data["format"] == "standard"
        assert data["is_public"] is False

    def test_create_deck_requires_name(self, client: TestClient) -> None:
        """Test POST /api/v1/decks requires name field."""
        response = client.post(
            "/api/v1/decks",
            json={"format": "standard"},
        )

        assert response.status_code == 422  # Validation error

    def test_create_deck_invalid_format(self, client: TestClient) -> None:
        """Test POST /api/v1/decks validates format enum."""
        response = client.post(
            "/api/v1/decks",
            json={"name": "Bad Deck", "format": "invalid_format"},
        )

        assert response.status_code == 422  # Validation error

    def test_import_deck_ptcgo_format(
        self, unauthenticated_client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test POST /api/v1/decks/import parses PTCGO format."""
        mock_charizard = MagicMock(spec=Card)
        mock_charizard.id = "sv4-6"
        mock_charizard.set_id = "sv4"
        mock_charizard.number = "6"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_charizard]
        mock_db.execute = AsyncMock(return_value=mock_result)

        response = unauthenticated_client.post(
            "/api/v1/decks/import",
            json={"deck_list": "* 4 Charizard ex SV4 6"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["cards"]) == 1
        assert data["cards"][0]["card_id"] == "sv4-6"
        assert data["cards"][0]["quantity"] == 4
        assert data["total_cards"] == 4

    def test_import_deck_with_unmatched(
        self, unauthenticated_client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test POST /api/v1/decks/import reports unmatched cards."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        response = unauthenticated_client.post(
            "/api/v1/decks/import",
            json={"deck_list": "* 4 Fake Card XYZ 999"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["cards"]) == 0
        assert len(data["unmatched"]) == 1
        assert data["unmatched"][0]["name"] == "Fake Card"
        assert data["unmatched"][0]["set_code"] == "XYZ"
        assert data["total_cards"] == 0

    def test_import_deck_empty_list(self, unauthenticated_client: TestClient) -> None:
        """Test POST /api/v1/decks/import validates non-empty input."""
        response = unauthenticated_client.post(
            "/api/v1/decks/import",
            json={"deck_list": ""},
        )

        # Empty string should fail validation (min_length=1)
        assert response.status_code == 422

    def test_list_decks_success(
        self, client: TestClient, mock_db: AsyncMock, mock_user: MagicMock
    ) -> None:
        """Test GET /api/v1/decks returns user's decks."""
        from datetime import datetime

        # Create mock deck
        mock_deck = MagicMock(spec=Deck)
        mock_deck.id = uuid4()
        mock_deck.user_id = mock_user.id
        mock_deck.name = "My Deck"
        mock_deck.format = "standard"
        mock_deck.archetype = None
        mock_deck.is_public = False
        mock_deck.cards = []
        mock_deck.created_at = datetime.now(UTC)
        mock_deck.updated_at = datetime.now(UTC)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_deck]
        mock_db.execute = AsyncMock(
            side_effect=[
                MagicMock(scalar=MagicMock(return_value=1)),  # count
                mock_result,  # decks
            ]
        )

        response = client.get("/api/v1/decks")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "My Deck"

    def test_list_decks_pagination(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test GET /api/v1/decks respects pagination params."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(
            side_effect=[
                MagicMock(scalar=MagicMock(return_value=0)),
                mock_result,
            ]
        )

        response = client.get("/api/v1/decks?page=2&limit=50")

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["limit"] == 50

    def test_list_public_decks_success(
        self, unauthenticated_client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test GET /api/v1/decks/public returns public decks."""
        from datetime import datetime

        deck_id = uuid4()
        mock_deck = MagicMock(spec=Deck)
        mock_deck.id = deck_id
        mock_deck.user_id = uuid4()
        mock_deck.name = "Public Deck"
        mock_deck.format = "standard"
        mock_deck.archetype = "Charizard"
        mock_deck.is_public = True
        mock_deck.cards = [{"card_id": "sv4-6", "quantity": 4}]
        mock_deck.created_at = datetime.now(UTC)
        mock_deck.updated_at = datetime.now(UTC)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_deck]
        mock_db.execute = AsyncMock(
            side_effect=[
                MagicMock(scalar=MagicMock(return_value=1)),  # count
                mock_result,  # decks
            ]
        )

        response = unauthenticated_client.get("/api/v1/decks/public")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "Public Deck"

    def test_list_public_decks_with_filters(
        self, unauthenticated_client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test GET /api/v1/decks/public with format filter."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(
            side_effect=[
                MagicMock(scalar=MagicMock(return_value=0)),
                mock_result,
            ]
        )

        response = unauthenticated_client.get(
            "/api/v1/decks/public?format=standard&sort=popular"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0

    def test_list_public_decks_with_archetype_filter(
        self, unauthenticated_client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test GET /api/v1/decks/public with archetype filter."""
        from datetime import datetime

        mock_deck = MagicMock(spec=Deck)
        mock_deck.id = uuid4()
        mock_deck.user_id = uuid4()
        mock_deck.name = "Charizard Deck"
        mock_deck.format = "standard"
        mock_deck.archetype = "Charizard"
        mock_deck.is_public = True
        mock_deck.cards = [{"card_id": "sv4-6", "quantity": 4}]
        mock_deck.created_at = datetime.now(UTC)
        mock_deck.updated_at = datetime.now(UTC)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_deck]
        mock_db.execute = AsyncMock(
            side_effect=[
                MagicMock(scalar=MagicMock(return_value=1)),
                mock_result,
            ]
        )

        response = unauthenticated_client.get(
            "/api/v1/decks/public?archetype=Charizard"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["archetype"] == "Charizard"

    def test_get_deck_public(
        self, unauthenticated_client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test GET /api/v1/decks/{id} returns public deck without auth."""
        from datetime import datetime

        deck_id = uuid4()
        mock_deck = MagicMock(spec=Deck)
        mock_deck.id = deck_id
        mock_deck.user_id = uuid4()
        mock_deck.name = "Public Deck"
        mock_deck.description = None
        mock_deck.format = "standard"
        mock_deck.archetype = None
        mock_deck.is_public = True
        mock_deck.share_code = None
        mock_deck.cards = []
        mock_deck.created_at = datetime.now(UTC)
        mock_deck.updated_at = datetime.now(UTC)
        mock_deck.user = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_deck
        mock_db.execute = AsyncMock(return_value=mock_result)

        response = unauthenticated_client.get(f"/api/v1/decks/{deck_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Public Deck"

    def test_get_deck_private_forbidden(
        self, unauthenticated_client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test GET /api/v1/decks/{id} returns 404 for private deck without auth."""
        from datetime import datetime

        deck_id = uuid4()
        mock_deck = MagicMock(spec=Deck)
        mock_deck.id = deck_id
        mock_deck.user_id = uuid4()
        mock_deck.is_public = False
        mock_deck.created_at = datetime.now(UTC)
        mock_deck.updated_at = datetime.now(UTC)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_deck
        mock_db.execute = AsyncMock(return_value=mock_result)

        response = unauthenticated_client.get(f"/api/v1/decks/{deck_id}")

        # Returns 404 (not 403) to avoid leaking existence of private decks
        assert response.status_code == 404

    def test_get_deck_not_found(self, client: TestClient, mock_db: AsyncMock) -> None:
        """Test GET /api/v1/decks/{id} returns 404 for non-existent deck."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        response = client.get(f"/api/v1/decks/{uuid4()}")

        assert response.status_code == 404

    def test_create_deck_invalid_cards_returns_400(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test POST /api/v1/decks returns 400 for invalid card IDs."""
        # Mock card validation - no cards exist
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        response = client.post(
            "/api/v1/decks",
            json={
                "name": "Bad Deck",
                "cards": [{"card_id": "nonexistent-card", "quantity": 4}],
                "format": "standard",
            },
        )

        assert response.status_code == 400
        assert "Card IDs not found" in response.json()["detail"]

    def test_get_deck_stats_success(
        self, client: TestClient, mock_db: AsyncMock, mock_user: MagicMock
    ) -> None:
        """Test GET /api/v1/decks/{id}/stats returns stats."""
        from src.models.card import Card

        deck_id = uuid4()
        mock_deck = MagicMock(spec=Deck)
        mock_deck.id = deck_id
        mock_deck.user_id = mock_user.id
        mock_deck.is_public = True
        mock_deck.cards = [{"card_id": "sv4-6", "quantity": 4}]

        mock_pokemon = MagicMock(spec=Card)
        mock_pokemon.id = "sv4-6"
        mock_pokemon.supertype = "Pokemon"
        mock_pokemon.hp = 120
        mock_pokemon.attacks = [{"cost": ["Fire"]}]

        mock_deck_result = MagicMock()
        mock_deck_result.scalar_one_or_none.return_value = mock_deck
        mock_cards_result = MagicMock()
        mock_cards_result.scalars.return_value.all.return_value = [mock_pokemon]

        mock_db.execute = AsyncMock(side_effect=[mock_deck_result, mock_cards_result])

        response = client.get(f"/api/v1/decks/{deck_id}/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total_cards"] == 4
        assert data["type_breakdown"]["pokemon"] == 4
        assert data["average_hp"] == 120.0

    def test_get_deck_stats_not_found(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test GET /api/v1/decks/{id}/stats returns 404 for non-existent deck."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        response = client.get(f"/api/v1/decks/{uuid4()}/stats")

        assert response.status_code == 404

    def test_export_deck_ptcgo_success(
        self, client: TestClient, mock_db: AsyncMock, mock_user: MagicMock
    ) -> None:
        """Test GET /api/v1/decks/{id}/export returns PTCGO format."""
        from src.models.card import Card

        deck_id = uuid4()
        mock_deck = MagicMock(spec=Deck)
        mock_deck.id = deck_id
        mock_deck.user_id = mock_user.id
        mock_deck.is_public = True
        mock_deck.cards = [{"card_id": "sv4-6", "quantity": 4}]

        mock_pokemon = MagicMock(spec=Card)
        mock_pokemon.id = "sv4-6"
        mock_pokemon.name = "Charizard ex"
        mock_pokemon.supertype = "Pokemon"
        mock_pokemon.set_id = "sv4"
        mock_pokemon.number = "6"

        mock_deck_result = MagicMock()
        mock_deck_result.scalar_one_or_none.return_value = mock_deck
        mock_cards_result = MagicMock()
        mock_cards_result.scalars.return_value.all.return_value = [mock_pokemon]

        mock_db.execute = AsyncMock(side_effect=[mock_deck_result, mock_cards_result])

        response = client.get(f"/api/v1/decks/{deck_id}/export?format=ptcgo")

        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]
        assert "* 4 Charizard ex SV4 6" in response.text
        assert "Total Cards - 4" in response.text

    def test_export_deck_not_found(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test GET /api/v1/decks/{id}/export returns 404 for non-existent deck."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        response = client.get(f"/api/v1/decks/{uuid4()}/export?format=ptcgo")

        assert response.status_code == 404

    def test_update_deck_success(
        self, client: TestClient, mock_db: AsyncMock, mock_user: MagicMock
    ) -> None:
        """Test PUT /api/v1/decks/{id} updates a deck."""
        from datetime import datetime

        deck_id = uuid4()
        mock_deck = MagicMock(spec=Deck)
        mock_deck.id = deck_id
        mock_deck.user_id = mock_user.id
        mock_deck.name = "Original Name"
        mock_deck.description = None
        mock_deck.format = "standard"
        mock_deck.archetype = None
        mock_deck.is_public = False
        mock_deck.share_code = None
        mock_deck.cards = []
        mock_deck.created_at = datetime.now(UTC)
        mock_deck.updated_at = datetime.now(UTC)
        mock_deck.user = mock_user

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_deck
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        response = client.put(
            f"/api/v1/decks/{deck_id}",
            json={"name": "Updated Name"},
        )

        assert response.status_code == 200
        assert mock_deck.name == "Updated Name"

    def test_update_deck_not_found(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test PUT /api/v1/decks/{id} returns 404 for non-existent deck."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        response = client.put(
            f"/api/v1/decks/{uuid4()}",
            json={"name": "Updated Name"},
        )

        assert response.status_code == 404

    def test_update_deck_not_owner(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test PUT /api/v1/decks/{id} returns 404 for non-owner."""
        from datetime import datetime

        deck_id = uuid4()
        mock_deck = MagicMock(spec=Deck)
        mock_deck.id = deck_id
        mock_deck.user_id = uuid4()  # Different user
        mock_deck.is_public = False
        mock_deck.created_at = datetime.now(UTC)
        mock_deck.updated_at = datetime.now(UTC)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_deck
        mock_db.execute = AsyncMock(return_value=mock_result)

        response = client.put(
            f"/api/v1/decks/{deck_id}",
            json={"name": "Updated Name"},
        )

        # Returns 404 to avoid leaking existence
        assert response.status_code == 404

    def test_update_deck_invalid_cards(
        self, client: TestClient, mock_db: AsyncMock, mock_user: MagicMock
    ) -> None:
        """Test PUT /api/v1/decks/{id} returns 400 for invalid card IDs."""
        from datetime import datetime

        deck_id = uuid4()
        mock_deck = MagicMock(spec=Deck)
        mock_deck.id = deck_id
        mock_deck.user_id = mock_user.id
        mock_deck.created_at = datetime.now(UTC)
        mock_deck.updated_at = datetime.now(UTC)

        mock_deck_result = MagicMock()
        mock_deck_result.scalar_one_or_none.return_value = mock_deck
        mock_card_result = MagicMock()
        mock_card_result.all.return_value = []
        mock_db.execute = AsyncMock(side_effect=[mock_deck_result, mock_card_result])

        response = client.put(
            f"/api/v1/decks/{deck_id}",
            json={"cards": [{"card_id": "nonexistent", "quantity": 4}]},
        )

        assert response.status_code == 400
        assert "Card IDs not found" in response.json()["detail"]

    def test_delete_deck_success(
        self, client: TestClient, mock_db: AsyncMock, mock_user: MagicMock
    ) -> None:
        """Test DELETE /api/v1/decks/{id} deletes a deck."""
        from datetime import datetime

        deck_id = uuid4()
        mock_deck = MagicMock(spec=Deck)
        mock_deck.id = deck_id
        mock_deck.user_id = mock_user.id
        mock_deck.created_at = datetime.now(UTC)
        mock_deck.updated_at = datetime.now(UTC)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_deck
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.delete = AsyncMock()
        mock_db.commit = AsyncMock()

        response = client.delete(f"/api/v1/decks/{deck_id}")

        assert response.status_code == 204
        mock_db.delete.assert_called_once()

    def test_delete_deck_not_found(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test DELETE /api/v1/decks/{id} returns 404 for non-existent deck."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        response = client.delete(f"/api/v1/decks/{uuid4()}")

        assert response.status_code == 404

    def test_delete_deck_not_owner(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test DELETE /api/v1/decks/{id} returns 404 for non-owner."""
        from datetime import datetime

        deck_id = uuid4()
        mock_deck = MagicMock(spec=Deck)
        mock_deck.id = deck_id
        mock_deck.user_id = uuid4()  # Different user
        mock_deck.created_at = datetime.now(UTC)
        mock_deck.updated_at = datetime.now(UTC)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_deck
        mock_db.execute = AsyncMock(return_value=mock_result)

        response = client.delete(f"/api/v1/decks/{deck_id}")

        # Returns 404 to avoid leaking existence
        assert response.status_code == 404


class TestDeckEndpointsAuth:
    """Tests for deck endpoint authentication requirements."""

    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        """Create a mock database session."""
        return AsyncMock()

    @pytest.fixture
    def no_auth_client(self, mock_db: AsyncMock) -> TestClient:
        """Create test client that does NOT override auth dependencies.

        This allows testing the actual 401 behavior when no auth is provided.
        """
        from src.db.database import get_db

        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        # Intentionally NOT overriding get_current_user or get_current_user_optional

        yield TestClient(app)

        app.dependency_overrides.clear()

    def test_create_deck_unauthenticated_returns_401(
        self, no_auth_client: TestClient
    ) -> None:
        """Test POST /api/v1/decks returns 401 without authentication."""
        response = no_auth_client.post(
            "/api/v1/decks",
            json={"name": "Test Deck", "format": "standard"},
        )

        assert response.status_code == 401
        assert "Authorization header required" in response.json()["detail"]

    def test_list_decks_unauthenticated_returns_401(
        self, no_auth_client: TestClient
    ) -> None:
        """Test GET /api/v1/decks returns 401 without authentication."""
        response = no_auth_client.get("/api/v1/decks")

        assert response.status_code == 401
        assert "Authorization header required" in response.json()["detail"]

    def test_get_deck_with_invalid_auth_returns_401(
        self, no_auth_client: TestClient
    ) -> None:
        """Test GET /api/v1/decks/{id} returns 401 with malformed auth header."""
        deck_id = uuid4()
        response = no_auth_client.get(
            f"/api/v1/decks/{deck_id}",
            headers={"Authorization": "Bearer invalid-not-a-uuid"},
        )

        assert response.status_code == 401
        assert "Invalid user ID" in response.json()["detail"]

    def test_update_deck_unauthenticated_returns_401(
        self, no_auth_client: TestClient
    ) -> None:
        """Test PUT /api/v1/decks/{id} returns 401 without authentication."""
        response = no_auth_client.put(
            f"/api/v1/decks/{uuid4()}",
            json={"name": "Updated Name"},
        )

        assert response.status_code == 401
        assert "Authorization header required" in response.json()["detail"]

    def test_delete_deck_unauthenticated_returns_401(
        self, no_auth_client: TestClient
    ) -> None:
        """Test DELETE /api/v1/decks/{id} returns 401 without authentication."""
        response = no_auth_client.delete(f"/api/v1/decks/{uuid4()}")

        assert response.status_code == 401
        assert "Authorization header required" in response.json()["detail"]
