"""Tests for Visual Card References enrichment (Issue #320).

Tests that KeyCardResponse and CardUsageSummary objects are enriched
with card_name and image_small via _batch_lookup_cards and
_enrich_key_cards helper functions in the meta router.
"""

from datetime import date
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.db.database import get_db
from src.main import app
from src.models.meta_snapshot import MetaSnapshot
from src.models.tournament import Tournament
from src.models.tournament_placement import TournamentPlacement
from src.schemas.meta import KeyCardResponse


class TestBatchLookupCards:
    """Unit tests for _batch_lookup_cards helper."""

    @pytest.mark.asyncio
    async def test_returns_empty_dict_for_empty_input(
        self,
    ) -> None:
        """Test empty card_ids returns empty dict."""
        from src.routers.meta import _batch_lookup_cards

        db = AsyncMock()
        result = await _batch_lookup_cards([], db)
        assert result == {}
        db.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_returns_card_info_dict(self) -> None:
        """Test returns dict of card_id -> (name, image)."""
        from src.routers.meta import _batch_lookup_cards

        db = AsyncMock()

        row1 = MagicMock()
        row1.id = "sv4-6"
        row1.name = "Pikachu"
        row1.japanese_name = None
        row1.image_small = "https://img.example.com/sv4-6.png"

        row2 = MagicMock()
        row2.id = "sv3-1"
        row2.name = "Charizard ex"
        row2.japanese_name = None
        row2.image_small = "https://img.example.com/sv3-1.png"

        mock_result = MagicMock()
        mock_result.all.return_value = [row1, row2]
        db.execute.return_value = mock_result

        result = await _batch_lookup_cards(["sv4-6", "sv3-1"], db)

        assert result["sv4-6"] == (
            "Pikachu",
            "https://img.example.com/sv4-6.png",
        )
        assert result["sv3-1"] == (
            "Charizard ex",
            "https://img.example.com/sv3-1.png",
        )

    @pytest.mark.asyncio
    async def test_falls_back_to_japanese_name(self) -> None:
        """Test uses japanese_name when name is None."""
        from src.routers.meta import _batch_lookup_cards

        db = AsyncMock()

        row = MagicMock()
        row.id = "jp-card-1"
        row.name = None
        row.japanese_name = "ピカチュウ"
        row.image_small = "https://img.example.com/jp1.png"

        mock_result = MagicMock()
        mock_result.all.return_value = [row]
        db.execute.return_value = mock_result

        result = await _batch_lookup_cards(["jp-card-1"], db)

        assert result["jp-card-1"] == (
            "ピカチュウ",
            "https://img.example.com/jp1.png",
        )

    @pytest.mark.asyncio
    async def test_returns_empty_on_db_error(self) -> None:
        """Test returns empty dict on SQLAlchemy error."""
        from sqlalchemy.exc import SQLAlchemyError

        from src.routers.meta import _batch_lookup_cards

        db = AsyncMock()
        db.execute.side_effect = SQLAlchemyError("fail")

        result = await _batch_lookup_cards(["sv4-6"], db)

        assert result == {}

    @pytest.mark.asyncio
    async def test_falls_back_to_card_id_mapping(self) -> None:
        """Test JP card not in cards table resolves via mapping."""
        from src.routers.meta import _batch_lookup_cards

        db = AsyncMock()

        # Step 1: Direct lookup returns empty
        mock_direct = MagicMock()
        mock_direct.all.return_value = []

        # Step 2: Mapping lookup returns a JP->EN mapping
        mapping_row = MagicMock()
        mapping_row.jp_card_id = "sv09-97"
        mapping_row.en_card_id = "JTG-097"
        mapping_row.card_name_en = "Hydrapple ex"
        mock_mapping = MagicMock()
        mock_mapping.all.return_value = [mapping_row]

        # Step 3: EN card lookup returns the card
        en_row = MagicMock()
        en_row.id = "JTG-097"
        en_row.name = "Hydrapple ex"
        en_row.japanese_name = None
        en_row.image_small = "https://img.example.com/JTG-097.png"
        mock_en = MagicMock()
        mock_en.all.return_value = [en_row]

        db.execute.side_effect = [mock_direct, mock_mapping, mock_en]

        result = await _batch_lookup_cards(["sv09-97"], db)

        assert result["sv09-97"] == (
            "Hydrapple ex",
            "https://img.example.com/JTG-097.png",
        )

    @pytest.mark.asyncio
    async def test_mapping_fallback_uses_card_name_when_en_card_missing(
        self,
    ) -> None:
        """Test mapping exists but EN card not in DB returns name only."""
        from src.routers.meta import _batch_lookup_cards

        db = AsyncMock()

        # Step 1: Direct lookup returns empty
        mock_direct = MagicMock()
        mock_direct.all.return_value = []

        # Step 2: Mapping exists
        mapping_row = MagicMock()
        mapping_row.jp_card_id = "sv09-50"
        mapping_row.en_card_id = "JTG-050"
        mapping_row.card_name_en = "Raichu ex"
        mock_mapping = MagicMock()
        mock_mapping.all.return_value = [mapping_row]

        # Step 3: EN card not found
        mock_en = MagicMock()
        mock_en.all.return_value = []

        db.execute.side_effect = [mock_direct, mock_mapping, mock_en]

        result = await _batch_lookup_cards(["sv09-50"], db)

        assert result["sv09-50"] == ("Raichu ex", None)

    @pytest.mark.asyncio
    async def test_no_mapping_query_when_all_cards_found(self) -> None:
        """Test no fallback query when all cards found directly."""
        from src.routers.meta import _batch_lookup_cards

        db = AsyncMock()

        row = MagicMock()
        row.id = "sv4-6"
        row.name = "Pikachu"
        row.japanese_name = None
        row.image_small = "https://img.example.com/sv4-6.png"

        mock_result = MagicMock()
        mock_result.all.return_value = [row]
        db.execute.return_value = mock_result

        result = await _batch_lookup_cards(["sv4-6"], db)

        assert result["sv4-6"] == (
            "Pikachu",
            "https://img.example.com/sv4-6.png",
        )
        # Only one query (direct lookup), no mapping fallback
        assert db.execute.call_count == 1

    @pytest.mark.asyncio
    async def test_mixed_direct_and_mapped_cards(self) -> None:
        """Test some cards found directly, others via mapping."""
        from src.routers.meta import _batch_lookup_cards

        db = AsyncMock()

        # Step 1: Direct lookup finds sv4-6 but not sv09-97
        en_row = MagicMock()
        en_row.id = "sv4-6"
        en_row.name = "Pikachu"
        en_row.japanese_name = None
        en_row.image_small = "https://img.example.com/sv4-6.png"
        mock_direct = MagicMock()
        mock_direct.all.return_value = [en_row]

        # Step 2: Mapping for sv09-97
        mapping_row = MagicMock()
        mapping_row.jp_card_id = "sv09-97"
        mapping_row.en_card_id = "JTG-097"
        mapping_row.card_name_en = "Hydrapple ex"
        mock_mapping = MagicMock()
        mock_mapping.all.return_value = [mapping_row]

        # Step 3: EN card found
        mapped_row = MagicMock()
        mapped_row.id = "JTG-097"
        mapped_row.name = "Hydrapple ex"
        mapped_row.japanese_name = None
        mapped_row.image_small = "https://img.example.com/JTG-097.png"
        mock_en = MagicMock()
        mock_en.all.return_value = [mapped_row]

        db.execute.side_effect = [mock_direct, mock_mapping, mock_en]

        result = await _batch_lookup_cards(["sv4-6", "sv09-97"], db)

        assert result["sv4-6"] == (
            "Pikachu",
            "https://img.example.com/sv4-6.png",
        )
        assert result["sv09-97"] == (
            "Hydrapple ex",
            "https://img.example.com/JTG-097.png",
        )


class TestEnrichKeyCards:
    """Unit tests for _enrich_key_cards helper."""

    @pytest.mark.asyncio
    async def test_enriches_key_cards_in_place(self) -> None:
        """Test key cards get card_name and image_small."""
        from src.routers.meta import _enrich_key_cards

        db = AsyncMock()

        row = MagicMock()
        row.id = "sv4-6"
        row.name = "Pikachu"
        row.japanese_name = None
        row.image_small = "https://img.example.com/sv4-6.png"

        mock_result = MagicMock()
        mock_result.all.return_value = [row]
        db.execute.return_value = mock_result

        key_cards = [
            KeyCardResponse(
                card_id="sv4-6",
                inclusion_rate=1.0,
                avg_copies=4.0,
            ),
        ]

        await _enrich_key_cards(key_cards, db)

        assert key_cards[0].card_name == "Pikachu"
        assert key_cards[0].image_small == ("https://img.example.com/sv4-6.png")

    @pytest.mark.asyncio
    async def test_leaves_none_for_unknown_cards(
        self,
    ) -> None:
        """Test card_name/image_small stay None for unknown IDs."""
        from src.routers.meta import _enrich_key_cards

        db = AsyncMock()

        mock_result = MagicMock()
        mock_result.all.return_value = []
        db.execute.return_value = mock_result

        key_cards = [
            KeyCardResponse(
                card_id="unknown-1",
                inclusion_rate=0.5,
                avg_copies=2.0,
            ),
        ]

        await _enrich_key_cards(key_cards, db)

        assert key_cards[0].card_name is None
        assert key_cards[0].image_small is None

    @pytest.mark.asyncio
    async def test_enriches_mixed_known_unknown(
        self,
    ) -> None:
        """Test enrichment with both known and unknown cards."""
        from src.routers.meta import _enrich_key_cards

        db = AsyncMock()

        row = MagicMock()
        row.id = "sv4-6"
        row.name = "Pikachu"
        row.japanese_name = None
        row.image_small = "https://img.example.com/sv4-6.png"

        mock_result = MagicMock()
        mock_result.all.return_value = [row]
        db.execute.return_value = mock_result

        key_cards = [
            KeyCardResponse(
                card_id="sv4-6",
                inclusion_rate=1.0,
                avg_copies=4.0,
            ),
            KeyCardResponse(
                card_id="unknown-1",
                inclusion_rate=0.3,
                avg_copies=1.0,
            ),
        ]

        await _enrich_key_cards(key_cards, db)

        # Known card enriched
        assert key_cards[0].card_name == "Pikachu"
        assert key_cards[0].image_small == ("https://img.example.com/sv4-6.png")
        # Unknown card stays None
        assert key_cards[1].card_name is None
        assert key_cards[1].image_small is None


class TestSnapshotToResponseCardInfo:
    """Tests that _snapshot_to_response correctly applies card_info."""

    def test_card_usage_enriched_with_card_info(
        self,
    ) -> None:
        """Test card_usage entries get card_name/image_small."""
        from src.routers.meta import _snapshot_to_response

        snapshot = MagicMock(spec=MetaSnapshot)
        snapshot.snapshot_date = date(2024, 1, 15)
        snapshot.region = None
        snapshot.format = "standard"
        snapshot.best_of = 3
        snapshot.archetype_shares = {"Test Deck": 0.1}
        snapshot.card_usage = {
            "sv4-6": {
                "inclusion_rate": 0.85,
                "avg_count": 3.5,
            },
        }
        snapshot.sample_size = 100
        snapshot.tournaments_included = []
        snapshot.diversity_index = None
        snapshot.tier_assignments = None
        snapshot.jp_signals = None
        snapshot.trends = None
        snapshot.era_label = None
        snapshot.tournament_type = "all"

        card_info = {
            "sv4-6": (
                "Pikachu",
                "https://img.example.com/sv4-6.png",
            ),
        }

        result = _snapshot_to_response(snapshot, card_info=card_info)

        assert len(result.card_usage) == 1
        assert result.card_usage[0].card_id == "sv4-6"
        assert result.card_usage[0].card_name == "Pikachu"
        assert result.card_usage[0].image_small == ("https://img.example.com/sv4-6.png")

    def test_card_usage_none_when_no_card_info(self) -> None:
        """Test card_usage has None fields when no card_info."""
        from src.routers.meta import _snapshot_to_response

        snapshot = MagicMock(spec=MetaSnapshot)
        snapshot.snapshot_date = date(2024, 1, 15)
        snapshot.region = None
        snapshot.format = "standard"
        snapshot.best_of = 3
        snapshot.archetype_shares = {}
        snapshot.card_usage = {
            "sv4-6": {
                "inclusion_rate": 0.85,
                "avg_count": 3.5,
            },
        }
        snapshot.sample_size = 100
        snapshot.tournaments_included = []
        snapshot.diversity_index = None
        snapshot.tier_assignments = None
        snapshot.jp_signals = None
        snapshot.trends = None
        snapshot.era_label = None
        snapshot.tournament_type = "all"

        result = _snapshot_to_response(snapshot)

        assert result.card_usage[0].card_name is None
        assert result.card_usage[0].image_small is None

    def test_card_usage_none_when_card_not_in_info(
        self,
    ) -> None:
        """Test card_usage None when card_id not in card_info."""
        from src.routers.meta import _snapshot_to_response

        snapshot = MagicMock(spec=MetaSnapshot)
        snapshot.snapshot_date = date(2024, 1, 15)
        snapshot.region = None
        snapshot.format = "standard"
        snapshot.best_of = 3
        snapshot.archetype_shares = {}
        snapshot.card_usage = {
            "unknown-card": {
                "inclusion_rate": 0.5,
                "avg_count": 2.0,
            },
        }
        snapshot.sample_size = 50
        snapshot.tournaments_included = []
        snapshot.diversity_index = None
        snapshot.tier_assignments = None
        snapshot.jp_signals = None
        snapshot.trends = None
        snapshot.era_label = None
        snapshot.tournament_type = "all"

        # Card info exists but does not contain unknown-card
        card_info = {
            "sv4-6": ("Pikachu", "https://img.example.com/sv4-6.png"),
        }

        result = _snapshot_to_response(snapshot, card_info=card_info)

        assert result.card_usage[0].card_id == "unknown-card"
        assert result.card_usage[0].card_name is None
        assert result.card_usage[0].image_small is None


class TestCurrentMetaCardEnrichment:
    """Tests that GET /meta/current enriches card_usage."""

    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        """Create mock database session."""
        return AsyncMock()

    @pytest.fixture
    def client(self, mock_db: AsyncMock) -> TestClient:
        """Create test client with mocked database."""

        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        yield TestClient(app)
        app.dependency_overrides.clear()

    def test_current_meta_card_usage_has_names(
        self,
        client: TestClient,
        mock_db: AsyncMock,
    ) -> None:
        """Test /meta/current card_usage has card_name."""
        snapshot = MagicMock(spec=MetaSnapshot)
        snapshot.snapshot_date = date(2024, 1, 15)
        snapshot.region = None
        snapshot.format = "standard"
        snapshot.best_of = 3
        snapshot.archetype_shares = {"Charizard ex": 0.15}
        snapshot.card_usage = {
            "sv4-6": {
                "inclusion_rate": 0.85,
                "avg_count": 3.5,
            },
        }
        snapshot.sample_size = 100
        snapshot.tournaments_included = []
        snapshot.diversity_index = None
        snapshot.tier_assignments = None
        snapshot.jp_signals = None
        snapshot.trends = None
        snapshot.era_label = None
        snapshot.tournament_type = "all"

        # Mock: snapshot query
        mock_snapshot = MagicMock()
        mock_snapshot.scalar_one_or_none.return_value = snapshot

        # Mock: display overrides query (empty)
        mock_overrides = MagicMock()
        mock_overrides.all.return_value = []

        # Mock: batch card lookup query
        card_row = MagicMock()
        card_row.id = "sv4-6"
        card_row.name = "Pikachu"
        card_row.japanese_name = None
        card_row.image_small = "https://img.example.com/sv4-6.png"
        mock_card_lookup = MagicMock()
        mock_card_lookup.all.return_value = [card_row]

        mock_db.execute.side_effect = [
            mock_snapshot,
            mock_overrides,
            mock_card_lookup,
        ]

        response = client.get("/api/v1/meta/current")

        assert response.status_code == 200
        data = response.json()
        assert len(data["card_usage"]) == 1
        assert data["card_usage"][0]["card_name"] == "Pikachu"
        assert data["card_usage"][0]["image_small"] == (
            "https://img.example.com/sv4-6.png"
        )


class TestArchetypeDetailKeyCardEnrichment:
    """Tests that GET /meta/archetypes/{name} enriches key_cards."""

    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        """Create mock database session."""
        return AsyncMock()

    @pytest.fixture
    def client(self, mock_db: AsyncMock) -> TestClient:
        """Create test client with mocked database."""

        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        yield TestClient(app)
        app.dependency_overrides.clear()

    def test_key_cards_enriched_with_names(
        self,
        client: TestClient,
        mock_db: AsyncMock,
    ) -> None:
        """Test archetype detail key_cards have card_name."""
        snapshot = MagicMock(spec=MetaSnapshot)
        snapshot.snapshot_date = date(2024, 1, 15)
        snapshot.archetype_shares = {"Charizard ex": 0.15}
        snapshot.sample_size = 100

        placement = MagicMock(spec=TournamentPlacement)
        placement.id = uuid4()
        placement.tournament_id = uuid4()
        placement.archetype = "Charizard ex"
        placement.placement = 1
        placement.player_name = "Player 1"
        placement.decklist = [
            {"card_id": "sv4-6", "quantity": 4},
            {"card_id": "sv3-1", "quantity": 3},
        ]

        tournament = MagicMock(spec=Tournament)
        tournament.id = placement.tournament_id
        tournament.name = "Test Tournament"

        # Mock: snapshot query
        mock_snapshot_result = MagicMock()
        mock_snapshot_result.scalars.return_value.all.return_value = [snapshot]

        # Mock: placement query
        mock_placement_result = MagicMock()
        mock_placement_result.scalars.return_value.all.return_value = [placement]

        # Mock: _enrich_key_cards -> _batch_lookup_cards
        card_row1 = MagicMock()
        card_row1.id = "sv4-6"
        card_row1.name = "Pikachu"
        card_row1.japanese_name = None
        card_row1.image_small = "https://img.example.com/sv4-6.png"
        card_row2 = MagicMock()
        card_row2.id = "sv3-1"
        card_row2.name = "Venusaur ex"
        card_row2.japanese_name = None
        card_row2.image_small = "https://img.example.com/sv3-1.png"
        mock_card_result = MagicMock()
        mock_card_result.all.return_value = [
            card_row1,
            card_row2,
        ]

        # Mock: tournament lookup
        mock_tournament_result = MagicMock()
        mock_tournament_result.scalars.return_value.all.return_value = [tournament]

        mock_db.execute.side_effect = [
            mock_snapshot_result,
            mock_placement_result,
            mock_card_result,
            mock_tournament_result,
        ]

        response = client.get("/api/v1/meta/archetypes/Charizard%20ex")

        assert response.status_code == 200
        data = response.json()

        key_cards = {kc["card_id"]: kc for kc in data["key_cards"]}
        assert key_cards["sv4-6"]["card_name"] == "Pikachu"
        assert key_cards["sv4-6"]["image_small"] == (
            "https://img.example.com/sv4-6.png"
        )
        assert key_cards["sv3-1"]["card_name"] == "Venusaur ex"
        assert key_cards["sv3-1"]["image_small"] == (
            "https://img.example.com/sv3-1.png"
        )

    def test_key_cards_none_for_unknown_cards(
        self,
        client: TestClient,
        mock_db: AsyncMock,
    ) -> None:
        """Test key_cards have None fields for unknown IDs."""
        snapshot = MagicMock(spec=MetaSnapshot)
        snapshot.snapshot_date = date(2024, 1, 15)
        snapshot.archetype_shares = {"Charizard ex": 0.15}
        snapshot.sample_size = 100

        placement = MagicMock(spec=TournamentPlacement)
        placement.id = uuid4()
        placement.tournament_id = uuid4()
        placement.archetype = "Charizard ex"
        placement.placement = 1
        placement.player_name = "Player 1"
        placement.decklist = [
            {"card_id": "unknown-card", "quantity": 3},
        ]

        tournament = MagicMock(spec=Tournament)
        tournament.id = placement.tournament_id
        tournament.name = "Test Tournament"

        # Mock: snapshot query
        mock_snapshot_result = MagicMock()
        mock_snapshot_result.scalars.return_value.all.return_value = [snapshot]

        # Mock: placement query
        mock_placement_result = MagicMock()
        mock_placement_result.scalars.return_value.all.return_value = [placement]

        # Mock: _enrich_key_cards -> _batch_lookup_cards
        # (card not found in direct lookup)
        mock_card_result = MagicMock()
        mock_card_result.all.return_value = []

        # Mock: card_id_mappings fallback (no mapping found)
        mock_mapping_result = MagicMock()
        mock_mapping_result.all.return_value = []

        # Mock: tournament lookup
        mock_tournament_result = MagicMock()
        mock_tournament_result.scalars.return_value.all.return_value = [tournament]

        mock_db.execute.side_effect = [
            mock_snapshot_result,
            mock_placement_result,
            mock_card_result,
            mock_mapping_result,
            mock_tournament_result,
        ]

        response = client.get("/api/v1/meta/archetypes/Charizard%20ex")

        assert response.status_code == 200
        data = response.json()

        assert len(data["key_cards"]) == 1
        kc = data["key_cards"][0]
        assert kc["card_id"] == "unknown-card"
        assert kc["card_name"] is None
        assert kc["image_small"] is None


class TestKeyCardResponseSchema:
    """Tests for KeyCardResponse schema with new fields."""

    def test_key_card_response_with_card_info(self) -> None:
        """Test KeyCardResponse with card_name and image_small."""
        kc = KeyCardResponse(
            card_id="sv4-6",
            card_name="Pikachu",
            image_small="https://img.example.com/sv4-6.png",
            inclusion_rate=0.95,
            avg_copies=3.5,
        )
        assert kc.card_name == "Pikachu"
        assert kc.image_small == ("https://img.example.com/sv4-6.png")

    def test_key_card_response_defaults_to_none(self) -> None:
        """Test KeyCardResponse defaults card_name/image to None."""
        kc = KeyCardResponse(
            card_id="sv4-6",
            inclusion_rate=0.95,
            avg_copies=3.5,
        )
        assert kc.card_name is None
        assert kc.image_small is None


class TestCardUsageSummarySchema:
    """Tests for CardUsageSummary schema with new fields."""

    def test_card_usage_summary_with_card_info(self) -> None:
        """Test CardUsageSummary with card_name/image_small."""
        from src.schemas.meta import CardUsageSummary

        usage = CardUsageSummary(
            card_id="sv4-6",
            card_name="Pikachu",
            image_small="https://img.example.com/sv4-6.png",
            inclusion_rate=0.85,
            avg_copies=3.5,
        )
        assert usage.card_name == "Pikachu"
        assert usage.image_small == ("https://img.example.com/sv4-6.png")

    def test_card_usage_summary_defaults_to_none(
        self,
    ) -> None:
        """Test CardUsageSummary defaults card_name/image."""
        from src.schemas.meta import CardUsageSummary

        usage = CardUsageSummary(
            card_id="sv4-6",
            inclusion_rate=0.85,
            avg_copies=3.5,
        )
        assert usage.card_name is None
        assert usage.image_small is None
