"""Tests for placeholder card service."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.card_id_mapping import CardIdMapping
from src.models.placeholder_card import PlaceholderCard
from src.services.placeholder_service import (
    PlaceholderGenerationResult,
    PlaceholderService,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_session() -> AsyncMock:
    """Create a mock database session."""
    session = AsyncMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def service(mock_session: AsyncMock) -> PlaceholderService:
    """Create PlaceholderService for testing."""
    return PlaceholderService(mock_session)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_scalar_result(value):
    """Build a MagicMock that behaves like an SA result with scalar_one_or_none."""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = value
    mock_result.scalar_one.return_value = value
    return mock_result


def _make_placeholder(**overrides) -> MagicMock:
    """Create a MagicMock placeholder card with sensible defaults."""
    defaults = {
        "id": uuid4(),
        "jp_card_id": "SV10-15",
        "en_card_id": "POR-042",
        "name_jp": "テスト",
        "name_en": "Test Card",
        "supertype": "Pokemon",
        "subtypes": None,
        "hp": 120,
        "types": ["Fire"],
        "attacks": None,
        "set_code": "POR",
        "official_set_code": "ME03",
        "is_unreleased": True,
        "is_released": False,
        "released_at": None,
        "source": "manual",
        "source_url": None,
        "source_account": None,
    }
    defaults.update(overrides)
    mock = MagicMock(spec=PlaceholderCard)
    for key, val in defaults.items():
        setattr(mock, key, val)
    return mock


def _make_mapping(**overrides) -> MagicMock:
    """Create a MagicMock card ID mapping with sensible defaults."""
    defaults = {
        "id": uuid4(),
        "jp_card_id": "SV10-15",
        "en_card_id": "POR-042",
        "card_name_en": "Test Card",
        "jp_set_id": "SV10",
        "en_set_id": "POR",
        "is_synthetic": True,
        "placeholder_card_id": uuid4(),
    }
    defaults.update(overrides)
    mock = MagicMock(spec=CardIdMapping)
    for key, val in defaults.items():
        setattr(mock, key, val)
    return mock


# ===========================================================================
# PlaceholderGenerationResult
# ===========================================================================


class TestPlaceholderGenerationResult:
    """Tests for PlaceholderGenerationResult dataclass."""

    def test_initial_state(self):
        """Test initial state with zero counters and no errors."""
        result = PlaceholderGenerationResult()
        assert result.placeholders_created == 0
        assert result.mappings_created == 0
        assert result.errors == []

    def test_success_when_no_errors(self):
        """Test success property returns True when there are no errors."""
        result = PlaceholderGenerationResult(placeholders_created=3, mappings_created=3)
        assert result.success is True

    def test_not_success_when_errors(self):
        """Test success property returns False when there are errors."""
        result = PlaceholderGenerationResult(errors=["something went wrong"])
        assert result.success is False


# ===========================================================================
# generate_placeholder_id
# ===========================================================================


class TestGeneratePlaceholderId:
    """Tests for generate_placeholder_id."""

    def test_format_starts_with_set_code(self, service: PlaceholderService):
        """Test generated ID starts with the placeholder set code."""
        pid = service.generate_placeholder_id()
        assert pid.startswith("POR-")

    def test_format_has_three_digit_suffix(self, service: PlaceholderService):
        """Test generated ID has a zero-padded 3-digit suffix."""
        pid = service.generate_placeholder_id()
        suffix = pid.split("-")[1]
        assert len(suffix) == 3
        assert suffix.isdigit()

    def test_suffix_in_valid_range(self, service: PlaceholderService):
        """Test suffix number is between 001 and 999."""
        for _ in range(50):
            pid = service.generate_placeholder_id()
            num = int(pid.split("-")[1])
            assert 1 <= num <= 999

    @patch("src.services.placeholder_service.random.randint", return_value=7)
    def test_deterministic_with_mocked_random(
        self, mock_randint, service: PlaceholderService
    ):
        """Test deterministic output when random is mocked."""
        assert service.generate_placeholder_id() == "POR-007"


# ===========================================================================
# create_placeholder
# ===========================================================================


class TestCreatePlaceholder:
    """Tests for create_placeholder."""

    @pytest.mark.asyncio
    async def test_creates_placeholder_card(
        self, service: PlaceholderService, mock_session: AsyncMock
    ):
        """Test creating a placeholder card stores it via session."""
        mock_session.execute.return_value = _make_scalar_result(None)

        await service.create_placeholder(
            jp_card_id="SV10-15",
            name_jp="テストカード",
            name_en="Test Card",
            supertype="Pokemon",
        )

        mock_session.add.assert_called_once()
        mock_session.commit.assert_awaited_once()
        added = mock_session.add.call_args[0][0]
        assert isinstance(added, PlaceholderCard)
        assert added.jp_card_id == "SV10-15"
        assert added.name_en == "Test Card"
        assert added.supertype == "Pokemon"
        assert added.is_unreleased is True
        assert added.is_released is False
        assert added.set_code == "POR"

    @pytest.mark.asyncio
    async def test_retries_id_on_collision(
        self, service: PlaceholderService, mock_session: AsyncMock
    ):
        """Test that a new ID is generated when the first one collides."""
        existing_placeholder = _make_placeholder()
        # First call returns existing (collision), the rest don't matter
        # because the code only retries once
        mock_session.execute.return_value = _make_scalar_result(existing_placeholder)

        # The service will generate two IDs -- the first collides, the second is used
        with patch.object(
            service, "generate_placeholder_id", side_effect=["POR-001", "POR-002"]
        ):
            await service.create_placeholder(
                jp_card_id="SV10-15",
                name_jp="テスト",
                name_en="Test",
                supertype="Pokemon",
            )

        added = mock_session.add.call_args[0][0]
        assert added.en_card_id == "POR-002"

    @pytest.mark.asyncio
    async def test_passes_optional_kwargs(
        self, service: PlaceholderService, mock_session: AsyncMock
    ):
        """Test that optional keyword arguments are passed through."""
        mock_session.execute.return_value = _make_scalar_result(None)

        await service.create_placeholder(
            jp_card_id="SV10-20",
            name_jp="テスト",
            name_en="Test",
            supertype="Pokemon",
            subtypes=["Stage 1"],
            hp=130,
            types=["Water"],
            attacks=[{"name": "Splash", "cost": ["Water"], "damage": "30"}],
            source="limitless",
            source_url="https://example.com",
            source_account="@test",
        )

        added = mock_session.add.call_args[0][0]
        assert added.subtypes == ["Stage 1"]
        assert added.hp == 130
        assert added.types == ["Water"]
        assert added.attacks == [{"name": "Splash", "cost": ["Water"], "damage": "30"}]
        assert added.source == "limitless"
        assert added.source_url == "https://example.com"
        assert added.source_account == "@test"

    @pytest.mark.asyncio
    async def test_default_source_is_manual(
        self, service: PlaceholderService, mock_session: AsyncMock
    ):
        """Test default source is 'manual'."""
        mock_session.execute.return_value = _make_scalar_result(None)

        await service.create_placeholder(
            jp_card_id="SV10-30",
            name_jp="テスト",
            name_en="Test",
            supertype="Trainer",
        )

        added = mock_session.add.call_args[0][0]
        assert added.source == "manual"


# ===========================================================================
# create_synthetic_mapping
# ===========================================================================


class TestCreateSyntheticMapping:
    """Tests for create_synthetic_mapping."""

    @pytest.mark.asyncio
    async def test_creates_mapping(
        self, service: PlaceholderService, mock_session: AsyncMock
    ):
        """Test creating a new synthetic mapping."""
        mock_session.execute.return_value = _make_scalar_result(None)

        placeholder = _make_placeholder(
            id=uuid4(), en_card_id="POR-100", name_en="Test Pokemon"
        )

        await service.create_synthetic_mapping("SV10-15", placeholder)

        mock_session.add.assert_called_once()
        mock_session.commit.assert_awaited_once()
        added = mock_session.add.call_args[0][0]
        assert isinstance(added, CardIdMapping)
        assert added.jp_card_id == "SV10-15"
        assert added.en_card_id == "POR-100"
        assert added.card_name_en == "Test Pokemon"
        assert added.is_synthetic is True
        assert added.placeholder_card_id == placeholder.id

    @pytest.mark.asyncio
    async def test_extracts_jp_set_id(
        self, service: PlaceholderService, mock_session: AsyncMock
    ):
        """Test JP set ID is extracted from card ID."""
        mock_session.execute.return_value = _make_scalar_result(None)

        placeholder = _make_placeholder(en_card_id="POR-200")
        await service.create_synthetic_mapping("SV10-15", placeholder)

        added = mock_session.add.call_args[0][0]
        assert added.jp_set_id == "SV10"

    @pytest.mark.asyncio
    async def test_jp_set_id_none_when_no_dash(
        self, service: PlaceholderService, mock_session: AsyncMock
    ):
        """Test JP set ID is None when card ID has no dash."""
        mock_session.execute.return_value = _make_scalar_result(None)

        placeholder = _make_placeholder(en_card_id="POR-300")
        await service.create_synthetic_mapping("NODASH", placeholder)

        added = mock_session.add.call_args[0][0]
        assert added.jp_set_id is None

    @pytest.mark.asyncio
    async def test_returns_existing_when_mapping_exists(
        self, service: PlaceholderService, mock_session: AsyncMock
    ):
        """Test returns existing mapping without creating a new one."""
        existing_mapping = _make_mapping()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_mapping
        mock_result.scalar_one.return_value = existing_mapping
        mock_session.execute.return_value = mock_result

        placeholder = _make_placeholder()
        result = await service.create_synthetic_mapping("SV10-15", placeholder)

        mock_session.add.assert_not_called()
        assert result == existing_mapping


# ===========================================================================
# generate_for_unreleased_cards
# ===========================================================================


class TestGenerateForUnreleasedCards:
    """Tests for generate_for_unreleased_cards."""

    @pytest.mark.asyncio
    async def test_creates_placeholders_for_new_cards(
        self, service: PlaceholderService, mock_session: AsyncMock
    ):
        """Test creating placeholders for multiple new cards."""
        # All execute calls return None (no existing records)
        mock_session.execute.return_value = _make_scalar_result(None)

        cards = [
            {
                "card_id": "SV10-01",
                "name_jp": "カード1",
                "name_en": "Card One",
                "card_type": "Pokemon",
            },
            {
                "card_id": "SV10-02",
                "name_jp": "カード2",
                "name_en": "Card Two",
                "card_type": "Trainer",
            },
        ]

        result = await service.generate_for_unreleased_cards(cards)

        assert result.placeholders_created == 2
        assert result.mappings_created == 2
        assert result.success is True

    @pytest.mark.asyncio
    async def test_skips_cards_without_card_id(
        self, service: PlaceholderService, mock_session: AsyncMock
    ):
        """Test that cards without a card_id are skipped."""
        mock_session.execute.return_value = _make_scalar_result(None)

        cards = [
            {"name_jp": "No ID Card", "name_en": "No ID"},
            {"card_id": None, "name_jp": "Null ID", "name_en": "Null"},
        ]

        result = await service.generate_for_unreleased_cards(cards)

        assert result.placeholders_created == 0
        assert result.mappings_created == 0

    @pytest.mark.asyncio
    async def test_skips_existing_placeholders(
        self, service: PlaceholderService, mock_session: AsyncMock
    ):
        """Test that existing placeholders are skipped."""
        existing = _make_placeholder()

        # First execute (check for existing placeholder) returns existing,
        # but we need separate calls for the loop: the first check inside
        # generate_for_unreleased_cards is for existing placeholder
        mock_session.execute.return_value = _make_scalar_result(existing)

        cards = [{"card_id": "SV10-01", "name_en": "Existing"}]

        result = await service.generate_for_unreleased_cards(cards)

        assert result.placeholders_created == 0

    @pytest.mark.asyncio
    async def test_uses_default_values_for_missing_fields(
        self, service: PlaceholderService, mock_session: AsyncMock
    ):
        """Test default values when optional fields are missing."""
        mock_session.execute.return_value = _make_scalar_result(None)

        cards = [{"card_id": "SV10-99"}]

        result = await service.generate_for_unreleased_cards(cards)

        assert result.placeholders_created == 1
        # Verify the create_placeholder call used defaults
        # The add call args contain the PlaceholderCard object
        # There are multiple add calls (placeholder + mapping), check the first
        first_add = mock_session.add.call_args_list[0][0][0]
        assert first_add.name_jp == "Unknown"
        assert first_add.name_en == "Card SV10-99"
        assert first_add.supertype == "Pokemon"

    @pytest.mark.asyncio
    async def test_handles_errors_gracefully(
        self, service: PlaceholderService, mock_session: AsyncMock
    ):
        """Test that errors are captured without stopping the batch."""
        # First card succeeds, second card fails
        call_count = 0

        async def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            # The first 3 calls are for the first card (check existing, check
            # ID collision in create_placeholder, check existing mapping)
            if call_count <= 3:
                return _make_scalar_result(None)
            # Fourth call is for the second card -- blow up
            raise RuntimeError("DB connection lost")

        mock_session.execute.side_effect = side_effect

        cards = [
            {"card_id": "SV10-01", "name_en": "Good Card"},
            {"card_id": "SV10-02", "name_en": "Bad Card"},
        ]

        result = await service.generate_for_unreleased_cards(cards, source="limitless")

        assert result.placeholders_created == 1
        assert len(result.errors) == 1
        assert "SV10-02" in result.errors[0]

    @pytest.mark.asyncio
    async def test_uses_provided_source(
        self, service: PlaceholderService, mock_session: AsyncMock
    ):
        """Test the source parameter is passed through."""
        mock_session.execute.return_value = _make_scalar_result(None)

        cards = [{"card_id": "SV10-01", "name_en": "Test"}]
        await service.generate_for_unreleased_cards(cards, source="llm_x")

        # The placeholder that was added should have the source
        first_add = mock_session.add.call_args_list[0][0][0]
        assert first_add.source == "llm_x"

    @pytest.mark.asyncio
    async def test_empty_list_returns_zero_counts(
        self, service: PlaceholderService, mock_session: AsyncMock
    ):
        """Test empty input list returns zeroed result."""
        result = await service.generate_for_unreleased_cards([])
        assert result.placeholders_created == 0
        assert result.mappings_created == 0
        assert result.success is True


# ===========================================================================
# get_mapping_with_fallback
# ===========================================================================


class TestGetMappingWithFallback:
    """Tests for get_mapping_with_fallback."""

    @pytest.mark.asyncio
    async def test_returns_official_mapping(
        self, service: PlaceholderService, mock_session: AsyncMock
    ):
        """Test returns official (non-synthetic) mapping."""
        mapping = _make_mapping(
            en_card_id="SCR-28", is_synthetic=False, placeholder_card_id=None
        )
        mock_session.execute.return_value = _make_scalar_result(mapping)

        en_card_id, placeholder = await service.get_mapping_with_fallback("SV10-15")

        assert en_card_id == "SCR-28"
        assert placeholder is None

    @pytest.mark.asyncio
    async def test_returns_synthetic_mapping_with_placeholder(
        self, service: PlaceholderService, mock_session: AsyncMock
    ):
        """Test returns synthetic mapping and associated placeholder."""
        placeholder_id = uuid4()
        mapping = _make_mapping(
            en_card_id="POR-042",
            is_synthetic=True,
            placeholder_card_id=placeholder_id,
        )
        placeholder = _make_placeholder(id=placeholder_id)

        # First execute: find mapping; Second execute: find placeholder
        mock_session.execute.side_effect = [
            _make_scalar_result(mapping),
            _make_scalar_result(placeholder),
        ]

        en_card_id, ph = await service.get_mapping_with_fallback("SV10-15")

        assert en_card_id == "POR-042"
        assert ph == placeholder

    @pytest.mark.asyncio
    async def test_creates_placeholder_on_the_fly_when_no_mapping(
        self, service: PlaceholderService, mock_session: AsyncMock
    ):
        """Test creates a new placeholder when no mapping exists."""
        # All queries return None (no existing mapping, no ID collision,
        # no existing mapping for synthetic mapping creation)
        mock_session.execute.return_value = _make_scalar_result(None)

        en_card_id, placeholder = await service.get_mapping_with_fallback("SV10-99")

        # Should have created both a placeholder and a mapping
        assert en_card_id is not None
        assert en_card_id.startswith("POR-")
        # placeholder is the PlaceholderCard object that was added
        assert placeholder is not None
        assert isinstance(placeholder, PlaceholderCard)
        assert placeholder.name_en == "Unknown Card (SV10-99)"
        assert placeholder.source == "auto"


# ===========================================================================
# enrich_decklist
# ===========================================================================


class TestEnrichDecklist:
    """Tests for enrich_decklist."""

    @pytest.mark.asyncio
    async def test_enriches_placeholder_entries(
        self, service: PlaceholderService, mock_session: AsyncMock
    ):
        """Test enrichment adds metadata for placeholder cards."""
        placeholder = _make_placeholder(
            en_card_id="POR-042",
            name_en="Charizard ex",
            name_jp="リザードンex",
            supertype="Pokemon",
            types=["Fire"],
            set_code="POR",
        )
        mock_session.execute.return_value = _make_scalar_result(placeholder)

        decklist = [{"card_id": "POR-042", "quantity": 2}]
        enriched = await service.enrich_decklist(decklist)

        assert len(enriched) == 1
        entry = enriched[0]
        assert entry["is_placeholder"] is True
        assert entry["name"] == "Charizard ex"
        assert entry["name_jp"] == "リザードンex"
        assert entry["supertype"] == "Pokemon"
        assert entry["types"] == ["Fire"]
        assert entry["set_code"] == "POR"
        assert entry["quantity"] == 2

    @pytest.mark.asyncio
    async def test_non_placeholder_entries(
        self, service: PlaceholderService, mock_session: AsyncMock
    ):
        """Test non-placeholder cards are marked correctly."""
        mock_session.execute.return_value = _make_scalar_result(None)

        decklist = [{"card_id": "swsh1-1", "quantity": 4}]
        enriched = await service.enrich_decklist(decklist)

        assert len(enriched) == 1
        assert enriched[0]["is_placeholder"] is False
        assert "name" not in enriched[0]

    @pytest.mark.asyncio
    async def test_skips_entries_without_card_id(
        self, service: PlaceholderService, mock_session: AsyncMock
    ):
        """Test entries without a card_id are skipped entirely."""
        decklist = [{"quantity": 1}, {"card_id": None, "quantity": 2}]
        enriched = await service.enrich_decklist(decklist)

        assert len(enriched) == 0

    @pytest.mark.asyncio
    async def test_empty_decklist(
        self, service: PlaceholderService, mock_session: AsyncMock
    ):
        """Test empty decklist returns empty list."""
        enriched = await service.enrich_decklist([])
        assert enriched == []

    @pytest.mark.asyncio
    async def test_mixed_decklist(
        self, service: PlaceholderService, mock_session: AsyncMock
    ):
        """Test decklist with both placeholder and official cards."""
        placeholder = _make_placeholder(en_card_id="POR-042", name_en="New Card")

        # First execute finds placeholder, second does not
        mock_session.execute.side_effect = [
            _make_scalar_result(placeholder),
            _make_scalar_result(None),
        ]

        decklist = [
            {"card_id": "POR-042", "quantity": 2},
            {"card_id": "swsh1-1", "quantity": 4},
        ]
        enriched = await service.enrich_decklist(decklist)

        assert len(enriched) == 2
        assert enriched[0]["is_placeholder"] is True
        assert enriched[1]["is_placeholder"] is False


# ===========================================================================
# mark_as_released
# ===========================================================================


class TestMarkAsReleased:
    """Tests for mark_as_released."""

    @pytest.mark.asyncio
    async def test_marks_placeholder_as_released(
        self, service: PlaceholderService, mock_session: AsyncMock
    ):
        """Test marking a placeholder as released updates its status."""
        placeholder = _make_placeholder(
            is_unreleased=True, is_released=False, released_at=None
        )
        mapping = _make_mapping(is_synthetic=True, placeholder_card_id=placeholder.id)

        mock_session.execute.side_effect = [
            _make_scalar_result(placeholder),
            _make_scalar_result(mapping),
        ]

        await service.mark_as_released("SV10-15", "SCR-28")

        assert placeholder.is_unreleased is False
        assert placeholder.is_released is True
        assert placeholder.released_at is not None
        assert mapping.en_card_id == "SCR-28"
        assert mapping.is_synthetic is False
        assert mapping.placeholder_card_id is None
        mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_uses_provided_released_at(
        self, service: PlaceholderService, mock_session: AsyncMock
    ):
        """Test using an explicit released_at datetime."""
        placeholder = _make_placeholder()
        mapping = _make_mapping()

        mock_session.execute.side_effect = [
            _make_scalar_result(placeholder),
            _make_scalar_result(mapping),
        ]

        release_dt = datetime(2025, 3, 15, tzinfo=UTC)
        await service.mark_as_released("SV10-15", "SCR-28", released_at=release_dt)

        assert placeholder.released_at == release_dt

    @pytest.mark.asyncio
    async def test_no_op_when_placeholder_not_found(
        self, service: PlaceholderService, mock_session: AsyncMock
    ):
        """Test no-op when the placeholder does not exist."""
        mock_session.execute.return_value = _make_scalar_result(None)

        await service.mark_as_released("SV10-999", "SCR-99")

        mock_session.commit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_handles_no_synthetic_mapping(
        self, service: PlaceholderService, mock_session: AsyncMock
    ):
        """Test marking as released when no synthetic mapping exists."""
        placeholder = _make_placeholder()

        mock_session.execute.side_effect = [
            _make_scalar_result(placeholder),
            _make_scalar_result(None),  # No mapping
        ]

        await service.mark_as_released("SV10-15", "SCR-28")

        # Placeholder should still be updated
        assert placeholder.is_unreleased is False
        assert placeholder.is_released is True
        mock_session.commit.assert_awaited_once()
