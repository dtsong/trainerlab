"""Tests for DeckExportService."""

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from src.models.card import Card
from src.models.deck import Deck
from src.models.user import User
from src.services.deck_export import DeckExportService


class TestDeckExportPTCGO:
    """Tests for exporting decks to PTCGO format."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Create a mock async session."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> DeckExportService:
        """Create a DeckExportService with mock session."""
        return DeckExportService(mock_session)

    @pytest.fixture
    def user_id(self) -> UUID:
        """Create a consistent user ID for tests."""
        return uuid4()

    @pytest.fixture
    def deck_id(self) -> UUID:
        """Create a consistent deck ID for tests."""
        return uuid4()

    @pytest.fixture
    def mock_user(self, user_id: UUID) -> MagicMock:
        """Create a mock user."""
        user = MagicMock(spec=User)
        user.id = user_id
        return user

    @pytest.fixture
    def mock_public_deck(self, deck_id: UUID, user_id: UUID) -> MagicMock:
        """Create a mock public deck with cards."""
        deck = MagicMock(spec=Deck)
        deck.id = deck_id
        deck.user_id = user_id
        deck.is_public = True
        deck.cards = [
            {"card_id": "sv4-6", "quantity": 4},
            {"card_id": "sv4-189", "quantity": 4},
            {"card_id": "sve-2", "quantity": 10},
        ]
        return deck

    @pytest.fixture
    def mock_private_deck(self, deck_id: UUID, user_id: UUID) -> MagicMock:
        """Create a mock private deck."""
        deck = MagicMock(spec=Deck)
        deck.id = deck_id
        deck.user_id = user_id
        deck.is_public = False
        deck.cards = [{"card_id": "sv4-6", "quantity": 4}]
        return deck

    @pytest.fixture
    def mock_pokemon_card(self) -> MagicMock:
        """Create a mock Pokemon card."""
        card = MagicMock(spec=Card)
        card.id = "sv4-6"
        card.name = "Charizard ex"
        card.set_id = "sv4"
        card.number = "6"
        card.local_id = "6"
        card.supertype = "Pokemon"
        return card

    @pytest.fixture
    def mock_trainer_card(self) -> MagicMock:
        """Create a mock Trainer card."""
        card = MagicMock(spec=Card)
        card.id = "sv4-189"
        card.name = "Professor's Research"
        card.set_id = "sv4"
        card.number = "189"
        card.local_id = "189"
        card.supertype = "Trainer"
        return card

    @pytest.fixture
    def mock_energy_card(self) -> MagicMock:
        """Create a mock Energy card."""
        card = MagicMock(spec=Card)
        card.id = "sve-2"
        card.name = "Fire Energy"
        card.set_id = "sve"
        card.number = "2"
        card.local_id = "2"
        card.supertype = "Energy"
        return card

    @pytest.mark.asyncio
    async def test_export_ptcgo_deck_not_found(
        self, service: DeckExportService, deck_id: UUID
    ) -> None:
        """Test exporting a deck that does not exist returns None."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        service.session.execute.return_value = mock_result

        result = await service.export_ptcgo(deck_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_export_ptcgo_public_deck_no_auth(
        self,
        service: DeckExportService,
        deck_id: UUID,
        mock_public_deck: MagicMock,
        mock_pokemon_card: MagicMock,
        mock_trainer_card: MagicMock,
        mock_energy_card: MagicMock,
    ) -> None:
        """Test exporting a public deck without authentication."""
        # First call: fetch deck, second call: fetch cards
        deck_result = MagicMock()
        deck_result.scalar_one_or_none.return_value = mock_public_deck
        card_result = MagicMock()
        card_result.scalars.return_value.all.return_value = [
            mock_pokemon_card,
            mock_trainer_card,
            mock_energy_card,
        ]
        service.session.execute.side_effect = [deck_result, card_result]

        result = await service.export_ptcgo(deck_id)

        assert result is not None
        assert "Pokémon Trading Card Game Deck List" in result
        assert "* 4 Charizard ex SV4 6" in result
        assert "* 4 Professor's Research SV4 189" in result
        assert "* 10 Fire Energy SVE 2" in result

    @pytest.mark.asyncio
    async def test_export_ptcgo_private_deck_owner_access(
        self,
        service: DeckExportService,
        deck_id: UUID,
        mock_private_deck: MagicMock,
        mock_user: MagicMock,
        mock_pokemon_card: MagicMock,
    ) -> None:
        """Test that deck owner can export their private deck."""
        deck_result = MagicMock()
        deck_result.scalar_one_or_none.return_value = mock_private_deck
        card_result = MagicMock()
        card_result.scalars.return_value.all.return_value = [mock_pokemon_card]
        service.session.execute.side_effect = [deck_result, card_result]

        result = await service.export_ptcgo(deck_id, user=mock_user)

        assert result is not None
        assert "* 4 Charizard ex SV4 6" in result

    @pytest.mark.asyncio
    async def test_export_ptcgo_private_deck_no_auth_denied(
        self,
        service: DeckExportService,
        deck_id: UUID,
        mock_private_deck: MagicMock,
    ) -> None:
        """Test that unauthenticated user cannot export private deck."""
        deck_result = MagicMock()
        deck_result.scalar_one_or_none.return_value = mock_private_deck
        service.session.execute.return_value = deck_result

        result = await service.export_ptcgo(deck_id, user=None)

        assert result is None

    @pytest.mark.asyncio
    async def test_export_ptcgo_private_deck_wrong_user_denied(
        self,
        service: DeckExportService,
        deck_id: UUID,
        mock_private_deck: MagicMock,
    ) -> None:
        """Test that another user cannot export someone else's private deck."""
        other_user = MagicMock(spec=User)
        other_user.id = uuid4()  # Different user ID

        deck_result = MagicMock()
        deck_result.scalar_one_or_none.return_value = mock_private_deck
        service.session.execute.return_value = deck_result

        result = await service.export_ptcgo(deck_id, user=other_user)

        assert result is None

    @pytest.mark.asyncio
    async def test_export_ptcgo_empty_deck(
        self,
        service: DeckExportService,
        deck_id: UUID,
        user_id: UUID,
    ) -> None:
        """Test exporting a deck with no cards."""
        empty_deck = MagicMock(spec=Deck)
        empty_deck.id = deck_id
        empty_deck.user_id = user_id
        empty_deck.is_public = True
        empty_deck.cards = []

        deck_result = MagicMock()
        deck_result.scalar_one_or_none.return_value = empty_deck
        service.session.execute.return_value = deck_result

        result = await service.export_ptcgo(deck_id)

        assert result is not None
        assert "##Pokémon - 0" in result
        assert "##Trainer Cards - 0" in result
        assert "##Energy - 0" in result
        assert "Total Cards - 0" in result

    @pytest.mark.asyncio
    async def test_export_ptcgo_empty_cards_none(
        self,
        service: DeckExportService,
        deck_id: UUID,
        user_id: UUID,
    ) -> None:
        """Test exporting a deck with cards set to None/falsy."""
        deck = MagicMock(spec=Deck)
        deck.id = deck_id
        deck.user_id = user_id
        deck.is_public = True
        deck.cards = None

        deck_result = MagicMock()
        deck_result.scalar_one_or_none.return_value = deck
        service.session.execute.return_value = deck_result

        result = await service.export_ptcgo(deck_id)

        assert result is not None
        assert "Total Cards - 0" in result

    @pytest.mark.asyncio
    async def test_export_ptcgo_card_grouping(
        self,
        service: DeckExportService,
        deck_id: UUID,
        mock_public_deck: MagicMock,
        mock_pokemon_card: MagicMock,
        mock_trainer_card: MagicMock,
        mock_energy_card: MagicMock,
    ) -> None:
        """Test that cards are grouped by supertype with correct counts."""
        deck_result = MagicMock()
        deck_result.scalar_one_or_none.return_value = mock_public_deck
        card_result = MagicMock()
        card_result.scalars.return_value.all.return_value = [
            mock_pokemon_card,
            mock_trainer_card,
            mock_energy_card,
        ]
        service.session.execute.side_effect = [deck_result, card_result]

        result = await service.export_ptcgo(deck_id)

        assert result is not None
        assert "##Pokémon - 4" in result
        assert "##Trainer Cards - 4" in result
        assert "##Energy - 10" in result
        assert "Total Cards - 18" in result

    @pytest.mark.asyncio
    async def test_export_ptcgo_total_calculation(
        self,
        service: DeckExportService,
        deck_id: UUID,
        mock_public_deck: MagicMock,
        mock_pokemon_card: MagicMock,
        mock_trainer_card: MagicMock,
        mock_energy_card: MagicMock,
    ) -> None:
        """Test that total card count is correct."""
        deck_result = MagicMock()
        deck_result.scalar_one_or_none.return_value = mock_public_deck
        card_result = MagicMock()
        card_result.scalars.return_value.all.return_value = [
            mock_pokemon_card,
            mock_trainer_card,
            mock_energy_card,
        ]
        service.session.execute.side_effect = [deck_result, card_result]

        result = await service.export_ptcgo(deck_id)

        assert result is not None
        # 4 Pokemon + 4 Trainer + 10 Energy = 18
        assert "Total Cards - 18" in result


class TestDeckExportPokemonCard:
    """Tests for exporting decks to Pokemon Card Live format."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Create a mock async session."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> DeckExportService:
        """Create a DeckExportService with mock session."""
        return DeckExportService(mock_session)

    @pytest.fixture
    def user_id(self) -> UUID:
        """Create a consistent user ID for tests."""
        return uuid4()

    @pytest.fixture
    def deck_id(self) -> UUID:
        """Create a consistent deck ID for tests."""
        return uuid4()

    @pytest.fixture
    def mock_user(self, user_id: UUID) -> MagicMock:
        """Create a mock user."""
        user = MagicMock(spec=User)
        user.id = user_id
        return user

    @pytest.fixture
    def mock_public_deck(self, deck_id: UUID, user_id: UUID) -> MagicMock:
        """Create a mock public deck with cards."""
        deck = MagicMock(spec=Deck)
        deck.id = deck_id
        deck.user_id = user_id
        deck.is_public = True
        deck.cards = [
            {"card_id": "sv4-6", "quantity": 4},
            {"card_id": "sv4-189", "quantity": 4},
            {"card_id": "sve-2", "quantity": 10},
        ]
        return deck

    @pytest.fixture
    def mock_private_deck(self, deck_id: UUID, user_id: UUID) -> MagicMock:
        """Create a mock private deck."""
        deck = MagicMock(spec=Deck)
        deck.id = deck_id
        deck.user_id = user_id
        deck.is_public = False
        deck.cards = [{"card_id": "sv4-6", "quantity": 4}]
        return deck

    @pytest.fixture
    def mock_pokemon_card(self) -> MagicMock:
        """Create a mock Pokemon card."""
        card = MagicMock(spec=Card)
        card.id = "sv4-6"
        card.name = "Charizard ex"
        card.set_id = "sv4"
        card.number = "6"
        card.local_id = "6"
        card.supertype = "Pokemon"
        return card

    @pytest.fixture
    def mock_trainer_card(self) -> MagicMock:
        """Create a mock Trainer card."""
        card = MagicMock(spec=Card)
        card.id = "sv4-189"
        card.name = "Professor's Research"
        card.set_id = "sv4"
        card.number = "189"
        card.local_id = "189"
        card.supertype = "Trainer"
        return card

    @pytest.fixture
    def mock_energy_card(self) -> MagicMock:
        """Create a mock Energy card."""
        card = MagicMock(spec=Card)
        card.id = "sve-2"
        card.name = "Fire Energy"
        card.set_id = "sve"
        card.number = "2"
        card.local_id = "2"
        card.supertype = "Energy"
        return card

    @pytest.mark.asyncio
    async def test_export_pokemoncard_deck_not_found(
        self, service: DeckExportService, deck_id: UUID
    ) -> None:
        """Test exporting a deck that does not exist returns None."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        service.session.execute.return_value = mock_result

        result = await service.export_pokemoncard(deck_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_export_pokemoncard_public_deck(
        self,
        service: DeckExportService,
        deck_id: UUID,
        mock_public_deck: MagicMock,
        mock_pokemon_card: MagicMock,
        mock_trainer_card: MagicMock,
        mock_energy_card: MagicMock,
    ) -> None:
        """Test exporting a public deck to Pokemon Card Live format."""
        deck_result = MagicMock()
        deck_result.scalar_one_or_none.return_value = mock_public_deck
        card_result = MagicMock()
        card_result.scalars.return_value.all.return_value = [
            mock_pokemon_card,
            mock_trainer_card,
            mock_energy_card,
        ]
        service.session.execute.side_effect = [deck_result, card_result]

        result = await service.export_pokemoncard(deck_id)

        assert result is not None
        # PCL format does NOT have the asterisk prefix
        assert "4 Charizard ex SV4 6" in result
        assert "4 Professor's Research SV4 189" in result
        assert "10 Fire Energy SVE 2" in result
        # PCL format uses different section headers
        assert "Pokemon - 4" in result
        assert "Trainer - 4" in result
        assert "Energy - 10" in result

    @pytest.mark.asyncio
    async def test_export_pokemoncard_private_deck_owner(
        self,
        service: DeckExportService,
        deck_id: UUID,
        mock_private_deck: MagicMock,
        mock_user: MagicMock,
        mock_pokemon_card: MagicMock,
    ) -> None:
        """Test that deck owner can export their private deck in PCL format."""
        deck_result = MagicMock()
        deck_result.scalar_one_or_none.return_value = mock_private_deck
        card_result = MagicMock()
        card_result.scalars.return_value.all.return_value = [mock_pokemon_card]
        service.session.execute.side_effect = [deck_result, card_result]

        result = await service.export_pokemoncard(deck_id, user=mock_user)

        assert result is not None
        assert "4 Charizard ex SV4 6" in result

    @pytest.mark.asyncio
    async def test_export_pokemoncard_private_deck_denied(
        self,
        service: DeckExportService,
        deck_id: UUID,
        mock_private_deck: MagicMock,
    ) -> None:
        """Test that unauthenticated user cannot export private deck."""
        deck_result = MagicMock()
        deck_result.scalar_one_or_none.return_value = mock_private_deck
        service.session.execute.return_value = deck_result

        result = await service.export_pokemoncard(deck_id, user=None)

        assert result is None

    @pytest.mark.asyncio
    async def test_export_pokemoncard_wrong_user_denied(
        self,
        service: DeckExportService,
        deck_id: UUID,
        mock_private_deck: MagicMock,
    ) -> None:
        """Test that another user cannot export someone else's private deck."""
        other_user = MagicMock(spec=User)
        other_user.id = uuid4()

        deck_result = MagicMock()
        deck_result.scalar_one_or_none.return_value = mock_private_deck
        service.session.execute.return_value = deck_result

        result = await service.export_pokemoncard(deck_id, user=other_user)

        assert result is None

    @pytest.mark.asyncio
    async def test_export_pokemoncard_empty_deck(
        self,
        service: DeckExportService,
        deck_id: UUID,
        user_id: UUID,
    ) -> None:
        """Test exporting a deck with no cards in PCL format."""
        empty_deck = MagicMock(spec=Deck)
        empty_deck.id = deck_id
        empty_deck.user_id = user_id
        empty_deck.is_public = True
        empty_deck.cards = []

        deck_result = MagicMock()
        deck_result.scalar_one_or_none.return_value = empty_deck
        service.session.execute.return_value = deck_result

        result = await service.export_pokemoncard(deck_id)

        assert result is not None
        assert "Pokemon - 0" in result
        assert "Trainer - 0" in result
        assert "Energy - 0" in result
        assert "Total Cards - 0" in result

    @pytest.mark.asyncio
    async def test_export_pokemoncard_total(
        self,
        service: DeckExportService,
        deck_id: UUID,
        mock_public_deck: MagicMock,
        mock_pokemon_card: MagicMock,
        mock_trainer_card: MagicMock,
        mock_energy_card: MagicMock,
    ) -> None:
        """Test total card count in PCL format export."""
        deck_result = MagicMock()
        deck_result.scalar_one_or_none.return_value = mock_public_deck
        card_result = MagicMock()
        card_result.scalars.return_value.all.return_value = [
            mock_pokemon_card,
            mock_trainer_card,
            mock_energy_card,
        ]
        service.session.execute.side_effect = [deck_result, card_result]

        result = await service.export_pokemoncard(deck_id)

        assert result is not None
        assert "Total Cards - 18" in result


class TestDeckExportFormatHelpers:
    """Tests for card line formatting and output building helpers."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Create a mock async session."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> DeckExportService:
        """Create a DeckExportService with mock session."""
        return DeckExportService(mock_session)

    def test_format_card_line_ptcgo(self, service: DeckExportService) -> None:
        """Test formatting a card line in PTCGO format."""
        card = MagicMock(spec=Card)
        card.name = "Charizard ex"
        card.set_id = "sv4"
        card.number = "6"
        card.local_id = "6"

        result = service._format_card_line(card, 4)

        assert result == "* 4 Charizard ex SV4 6"

    def test_format_card_line_ptcgo_set_id_uppercase(
        self, service: DeckExportService
    ) -> None:
        """Test that set_id is uppercased in PTCGO card lines."""
        card = MagicMock(spec=Card)
        card.name = "Fire Energy"
        card.set_id = "sve"
        card.number = "2"
        card.local_id = "2"

        result = service._format_card_line(card, 10)

        assert result == "* 10 Fire Energy SVE 2"

    def test_format_card_line_ptcgo_no_set_id(self, service: DeckExportService) -> None:
        """Test formatting when set_id is None uses 'UNK'."""
        card = MagicMock(spec=Card)
        card.name = "Unknown Card"
        card.set_id = None
        card.number = "1"
        card.local_id = "1"

        result = service._format_card_line(card, 1)

        assert result == "* 1 Unknown Card UNK 1"

    def test_format_card_line_ptcgo_no_number_uses_local_id(
        self, service: DeckExportService
    ) -> None:
        """Test formatting when number is None falls back to local_id."""
        card = MagicMock(spec=Card)
        card.name = "Pikachu"
        card.set_id = "sv4"
        card.number = None
        card.local_id = "42"

        result = service._format_card_line(card, 2)

        assert result == "* 2 Pikachu SV4 42"

    def test_format_card_line_ptcgo_no_number_no_local_id(
        self, service: DeckExportService
    ) -> None:
        """Test formatting when both number and local_id are None defaults to '1'."""
        card = MagicMock(spec=Card)
        card.name = "Mystery Card"
        card.set_id = "sv4"
        card.number = None
        card.local_id = None

        result = service._format_card_line(card, 3)

        assert result == "* 3 Mystery Card SV4 1"

    def test_format_pokemoncard_line(self, service: DeckExportService) -> None:
        """Test formatting a card line in Pokemon Card Live format."""
        card = MagicMock(spec=Card)
        card.name = "Charizard ex"
        card.set_id = "sv4"
        card.number = "6"
        card.local_id = "6"

        result = service._format_pokemoncard_line(card, 4)

        assert result == "4 Charizard ex SV4 6"

    def test_format_pokemoncard_line_no_set_id(
        self, service: DeckExportService
    ) -> None:
        """Test PCL format when set_id is None uses 'UNK'."""
        card = MagicMock(spec=Card)
        card.name = "Unknown Card"
        card.set_id = None
        card.number = "1"
        card.local_id = "1"

        result = service._format_pokemoncard_line(card, 1)

        assert result == "1 Unknown Card UNK 1"

    def test_build_ptcgo_empty(self, service: DeckExportService) -> None:
        """Test building an empty PTCGO output."""
        result = service._build_ptcgo_empty()

        assert "Pokémon Trading Card Game Deck List" in result
        assert "##Pokémon - 0" in result
        assert "##Trainer Cards - 0" in result
        assert "##Energy - 0" in result
        assert "Total Cards - 0" in result

    def test_build_pokemoncard_empty(self, service: DeckExportService) -> None:
        """Test building an empty Pokemon Card Live output."""
        result = service._build_pokemoncard_empty()

        assert "Pokemon - 0" in result
        assert "Trainer - 0" in result
        assert "Energy - 0" in result
        assert "Total Cards - 0" in result
        # PCL format should NOT have the PTCGO header
        assert "Pokémon Trading Card Game Deck List" not in result

    def test_build_ptcgo_output_structure(self, service: DeckExportService) -> None:
        """Test the full PTCGO output structure with all sections."""
        result = service._build_ptcgo_output(
            pokemon_lines=["* 4 Charizard ex SV4 6"],
            trainer_lines=["* 4 Professor's Research SV4 189"],
            energy_lines=["* 10 Fire Energy SVE 2"],
            pokemon_count=4,
            trainer_count=4,
            energy_count=10,
            total=18,
        )

        lines = result.split("\n")
        # Header
        assert lines[0] == "****** Pokémon Trading Card Game Deck List ******"
        assert lines[1] == ""
        # Pokemon section
        assert lines[2] == "##Pokémon - 4"
        assert lines[3] == "* 4 Charizard ex SV4 6"
        assert lines[4] == ""
        # Trainer section
        assert lines[5] == "##Trainer Cards - 4"
        assert lines[6] == "* 4 Professor's Research SV4 189"
        assert lines[7] == ""
        # Energy section
        assert lines[8] == "##Energy - 10"
        assert lines[9] == "* 10 Fire Energy SVE 2"
        assert lines[10] == ""
        # Total
        assert lines[11] == "Total Cards - 18"

    def test_build_pokemoncard_output_structure(
        self, service: DeckExportService
    ) -> None:
        """Test the full Pokemon Card Live output structure."""
        result = service._build_pokemoncard_output(
            pokemon_lines=["4 Charizard ex SV4 6"],
            trainer_lines=["4 Professor's Research SV4 189"],
            energy_lines=["10 Fire Energy SVE 2"],
            pokemon_count=4,
            trainer_count=4,
            energy_count=10,
            total=18,
        )

        lines = result.split("\n")
        # Pokemon section (no header banner)
        assert lines[0] == "Pokemon - 4"
        assert lines[1] == "4 Charizard ex SV4 6"
        assert lines[2] == ""
        # Trainer section
        assert lines[3] == "Trainer - 4"
        assert lines[4] == "4 Professor's Research SV4 189"
        assert lines[5] == ""
        # Energy section
        assert lines[6] == "Energy - 10"
        assert lines[7] == "10 Fire Energy SVE 2"
        assert lines[8] == ""
        # Total
        assert lines[9] == "Total Cards - 18"
