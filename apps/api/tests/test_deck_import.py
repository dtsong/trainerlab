"""Tests for DeckImportService."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.models.card import Card
from src.schemas import DeckImportResponse
from src.services.deck_import import DeckImportService, ParsedCard


class TestDeckImportParsePTCGO:
    """Tests for parsing PTCGO deck list format."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Create a mock async session."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> DeckImportService:
        """Create a DeckImportService with mock session."""
        return DeckImportService(mock_session)

    def test_parse_single_ptcgo_line(self, service: DeckImportService) -> None:
        """Test parsing a single PTCGO format line."""
        deck_list = "* 4 Charizard ex SV4 6"
        result = service._parse_deck_list(deck_list)

        assert len(result) == 1
        assert result[0].quantity == 4
        assert result[0].name == "Charizard ex"
        assert result[0].set_code == "sv4"
        assert result[0].number == "6"

    def test_parse_multiple_ptcgo_lines(self, service: DeckImportService) -> None:
        """Test parsing multiple PTCGO format lines."""
        deck_list = """* 4 Charizard ex SV4 6
* 3 Pidgey OBF 162
* 2 Pidgeot ex OBF 164"""
        result = service._parse_deck_list(deck_list)

        assert len(result) == 3
        assert result[0].name == "Charizard ex"
        assert result[1].name == "Pidgey"
        assert result[2].name == "Pidgeot ex"

    def test_parse_ptcgo_with_section_headers(self, service: DeckImportService) -> None:
        """Test that section headers (***) are skipped."""
        deck_list = """****** Pokemon Trading Card Game Deck List ******

##Pokemon - 2
* 4 Charizard ex SV4 6
* 3 Pidgey OBF 162

##Trainer Cards - 1
* 4 Professor's Research SV4 189

Total Cards - 60"""
        result = service._parse_deck_list(deck_list)

        assert len(result) == 3

    def test_parse_ptcgo_skips_empty_lines(self, service: DeckImportService) -> None:
        """Test that empty lines are skipped."""
        deck_list = """* 4 Charizard ex SV4 6

* 3 Pidgey OBF 162"""
        result = service._parse_deck_list(deck_list)

        assert len(result) == 2

    def test_parse_ptcgo_skips_total_line(self, service: DeckImportService) -> None:
        """Test that 'Total Cards' lines are skipped."""
        deck_list = """* 4 Charizard ex SV4 6
Total Cards - 60"""
        result = service._parse_deck_list(deck_list)

        assert len(result) == 1

    def test_parse_ptcgo_skips_hash_comments(self, service: DeckImportService) -> None:
        """Test that lines starting with # are skipped."""
        deck_list = """##Pokemon - 2
* 4 Charizard ex SV4 6"""
        result = service._parse_deck_list(deck_list)

        assert len(result) == 1

    def test_parse_ptcgo_card_number_with_letter(
        self, service: DeckImportService
    ) -> None:
        """Test parsing a card number with a trailing letter (e.g., 6a)."""
        deck_list = "* 2 Illustration Rare SV4 6a"
        result = service._parse_deck_list(deck_list)

        assert len(result) == 1
        assert result[0].number == "6a"

    def test_parse_ptcgo_set_code_lowercased(self, service: DeckImportService) -> None:
        """Test that set codes are lowercased during parsing."""
        deck_list = "* 4 Charizard ex SV4 6"
        result = service._parse_deck_list(deck_list)

        assert result[0].set_code == "sv4"


class TestDeckImportParsePCL:
    """Tests for parsing Pokemon Card Live (PCL) format."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Create a mock async session."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> DeckImportService:
        """Create a DeckImportService with mock session."""
        return DeckImportService(mock_session)

    def test_parse_single_pcl_line(self, service: DeckImportService) -> None:
        """Test parsing a single PCL format line."""
        deck_list = "4 Charizard ex SV4 6"
        result = service._parse_deck_list(deck_list)

        assert len(result) == 1
        assert result[0].quantity == 4
        assert result[0].name == "Charizard ex"
        assert result[0].set_code == "sv4"
        assert result[0].number == "6"

    def test_parse_multiple_pcl_lines(self, service: DeckImportService) -> None:
        """Test parsing multiple PCL format lines."""
        deck_list = """4 Charizard ex SV4 6
3 Pidgey OBF 162
2 Pidgeot ex OBF 164"""
        result = service._parse_deck_list(deck_list)

        assert len(result) == 3

    def test_parse_pcl_with_section_labels(self, service: DeckImportService) -> None:
        """Test PCL format with section labels (no * prefix)."""
        deck_list = """Pokemon - 2
4 Charizard ex SV4 6
3 Pidgey OBF 162

Trainer - 1
4 Professor's Research SV4 189

Total Cards - 60"""
        result = service._parse_deck_list(deck_list)

        # "Pokemon - 2" and "Trainer - 1" don't match the pattern (no card number)
        # and are skipped via the warning logger
        assert len(result) == 3


class TestDeckImportParseEdgeCases:
    """Tests for edge cases in deck list parsing."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Create a mock async session."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> DeckImportService:
        """Create a DeckImportService with mock session."""
        return DeckImportService(mock_session)

    def test_parse_empty_string(self, service: DeckImportService) -> None:
        """Test parsing an empty string returns no cards."""
        result = service._parse_deck_list("")

        assert result == []

    def test_parse_whitespace_only(self, service: DeckImportService) -> None:
        """Test parsing whitespace-only string returns no cards."""
        result = service._parse_deck_list("   \n  \n   ")

        assert result == []

    def test_parse_unrecognized_format(self, service: DeckImportService) -> None:
        """Test that lines not matching any format are skipped."""
        deck_list = """This is not a valid deck list
Random text here"""
        result = service._parse_deck_list(deck_list)

        assert result == []

    def test_parse_preserves_original_line(self, service: DeckImportService) -> None:
        """Test that the original line is preserved in ParsedCard."""
        deck_list = "* 4 Charizard ex SV4 6"
        result = service._parse_deck_list(deck_list)

        assert result[0].line == "* 4 Charizard ex SV4 6"


class TestDeckImportCardMatching:
    """Tests for card matching against the database."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Create a mock async session."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> DeckImportService:
        """Create a DeckImportService with mock session."""
        return DeckImportService(mock_session)

    @pytest.fixture
    def mock_card(self) -> MagicMock:
        """Create a mock card from the database."""
        card = MagicMock(spec=Card)
        card.id = "sv4-6"
        card.set_id = "sv4"
        card.number = "6"
        card.name = "Charizard ex"
        return card

    @pytest.mark.asyncio
    async def test_match_cards_all_found(
        self, service: DeckImportService, mock_card: MagicMock
    ) -> None:
        """Test matching when all cards are found in the database."""
        parsed = [
            ParsedCard(
                line="* 4 Charizard ex SV4 6",
                name="Charizard ex",
                set_code="sv4",
                number="6",
                quantity=4,
            )
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_card]
        service.session.execute.return_value = mock_result

        matched, unmatched = await service._match_cards(parsed)

        assert len(matched) == 1
        assert matched[0].card_id == "sv4-6"
        assert matched[0].quantity == 4
        assert len(unmatched) == 0

    @pytest.mark.asyncio
    async def test_match_cards_none_found(self, service: DeckImportService) -> None:
        """Test matching when no cards are found in the database."""
        parsed = [
            ParsedCard(
                line="* 4 Fakemon SV4 999",
                name="Fakemon",
                set_code="sv4",
                number="999",
                quantity=4,
            )
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        service.session.execute.return_value = mock_result

        matched, unmatched = await service._match_cards(parsed)

        assert len(matched) == 0
        assert len(unmatched) == 1
        assert unmatched[0].name == "Fakemon"
        assert unmatched[0].set_code == "SV4"  # uppercased in output
        assert unmatched[0].number == "999"
        assert unmatched[0].quantity == 4

    @pytest.mark.asyncio
    async def test_match_cards_partial_match(
        self, service: DeckImportService, mock_card: MagicMock
    ) -> None:
        """Test matching when some cards are found and some are not."""
        parsed = [
            ParsedCard(
                line="* 4 Charizard ex SV4 6",
                name="Charizard ex",
                set_code="sv4",
                number="6",
                quantity=4,
            ),
            ParsedCard(
                line="* 2 Fakemon SV4 999",
                name="Fakemon",
                set_code="sv4",
                number="999",
                quantity=2,
            ),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_card]
        service.session.execute.return_value = mock_result

        matched, unmatched = await service._match_cards(parsed)

        assert len(matched) == 1
        assert len(unmatched) == 1
        assert matched[0].card_id == "sv4-6"
        assert unmatched[0].name == "Fakemon"

    @pytest.mark.asyncio
    async def test_match_cards_empty_list(self, service: DeckImportService) -> None:
        """Test matching with an empty parsed cards list."""
        matched, unmatched = await service._match_cards([])

        assert matched == []
        assert unmatched == []

    @pytest.mark.asyncio
    async def test_match_cards_database_error_propagates(
        self, service: DeckImportService
    ) -> None:
        """Test that database errors propagate."""
        parsed = [
            ParsedCard(
                line="* 4 Charizard ex SV4 6",
                name="Charizard ex",
                set_code="sv4",
                number="6",
                quantity=4,
            )
        ]

        service.session.execute.side_effect = Exception("DB connection lost")

        with pytest.raises(Exception, match="DB connection lost"):
            await service._match_cards(parsed)


class TestDeckImportFullFlow:
    """Tests for the full import_deck flow."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Create a mock async session."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> DeckImportService:
        """Create a DeckImportService with mock session."""
        return DeckImportService(mock_session)

    @pytest.fixture
    def mock_card(self) -> MagicMock:
        """Create a mock card from the database."""
        card = MagicMock(spec=Card)
        card.id = "sv4-6"
        card.set_id = "sv4"
        card.number = "6"
        card.name = "Charizard ex"
        return card

    @pytest.mark.asyncio
    async def test_import_deck_empty_input(self, service: DeckImportService) -> None:
        """Test importing an empty deck list."""
        result = await service.import_deck("")

        assert isinstance(result, DeckImportResponse)
        assert result.cards == []
        assert result.unmatched == []
        assert result.total_cards == 0

    @pytest.mark.asyncio
    async def test_import_deck_no_parseable_lines(
        self, service: DeckImportService
    ) -> None:
        """Test importing a deck list with no parseable lines."""
        result = await service.import_deck(
            "This is not a valid deck list\nNeither is this"
        )

        assert result.cards == []
        assert result.unmatched == []
        assert result.total_cards == 0

    @pytest.mark.asyncio
    async def test_import_deck_ptcgo_format(
        self, service: DeckImportService, mock_card: MagicMock
    ) -> None:
        """Test importing a full PTCGO-format deck list."""
        deck_list = """****** Pokemon Trading Card Game Deck List ******

##Pokemon - 4
* 4 Charizard ex SV4 6

Total Cards - 4"""

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_card]
        service.session.execute.return_value = mock_result

        result = await service.import_deck(deck_list)

        assert isinstance(result, DeckImportResponse)
        assert len(result.cards) == 1
        assert result.cards[0].card_id == "sv4-6"
        assert result.cards[0].quantity == 4
        assert result.total_cards == 4

    @pytest.mark.asyncio
    async def test_import_deck_total_cards_calculation(
        self, service: DeckImportService
    ) -> None:
        """Test that total_cards sums only matched card quantities."""
        card1 = MagicMock(spec=Card)
        card1.id = "sv4-6"
        card1.set_id = "sv4"
        card1.number = "6"
        card1.name = "Charizard ex"

        card2 = MagicMock(spec=Card)
        card2.id = "obf-162"
        card2.set_id = "obf"
        card2.number = "162"
        card2.name = "Pidgey"

        deck_list = """* 4 Charizard ex SV4 6
* 3 Pidgey OBF 162
* 2 Fakemon FAK 999"""

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [card1, card2]
        service.session.execute.return_value = mock_result

        result = await service.import_deck(deck_list)

        # 4 + 3 = 7 matched. Fakemon is unmatched, so total = 7
        assert result.total_cards == 7
        assert len(result.cards) == 2
        assert len(result.unmatched) == 1
