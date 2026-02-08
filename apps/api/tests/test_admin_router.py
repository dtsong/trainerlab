"""Tests for admin router endpoints (placeholder card + archetype sprite)."""

import json
from datetime import UTC, datetime
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.db.database import get_db
from src.models.archetype_sprite import ArchetypeSprite
from src.models.placeholder_card import PlaceholderCard
from src.routers.admin import router


def _make_placeholder(**overrides) -> MagicMock:
    """Create a mock PlaceholderCard with sensible defaults."""
    now = datetime.now(UTC)
    mock = MagicMock(spec=PlaceholderCard)
    defaults = {
        "id": uuid4(),
        "jp_card_id": "SV10-015",
        "en_card_id": "POR-042",
        "name_jp": "\u30d4\u30ab\u30c1\u30e5\u30a6ex",
        "name_en": "Pikachu ex",
        "supertype": "Pokemon",
        "subtypes": ["Basic"],
        "hp": 200,
        "types": ["Lightning"],
        "attacks": [
            {
                "name": "Thunderbolt",
                "cost": ["Lightning", "Lightning"],
                "damage": "120",
                "text": "",
            }
        ],
        "set_code": "POR",
        "official_set_code": "ME03",
        "is_unreleased": True,
        "is_released": False,
        "released_at": None,
        "source": "manual",
        "source_url": None,
        "source_account": None,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(overrides)
    for key, value in defaults.items():
        setattr(mock, key, value)
    return mock


@pytest.fixture
def mock_db() -> AsyncMock:
    """Create a mock async database session."""
    session = AsyncMock()
    return session


@pytest.fixture
def app(mock_db: AsyncMock) -> FastAPI:
    """Create a test FastAPI app with the admin router."""
    test_app = FastAPI()
    test_app.include_router(router)

    async def override_get_db():
        yield mock_db

    test_app.dependency_overrides[get_db] = override_get_db
    return test_app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def error_client(app: FastAPI) -> TestClient:
    """Client that does not raise server exceptions."""
    return TestClient(app, raise_server_exceptions=False)


class TestCreatePlaceholderCard:
    """Tests for POST /api/v1/admin/placeholder-cards."""

    def test_create_placeholder_card_success(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Should create a placeholder card and return it."""
        placeholder = _make_placeholder()

        # Mock the duplicate check: no existing card found
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with patch("src.routers.admin.PlaceholderService") as mock_service_cls:
            mock_service = MagicMock()
            mock_service.create_placeholder = AsyncMock(return_value=placeholder)
            mock_service.create_synthetic_mapping = AsyncMock()
            mock_service_cls.return_value = mock_service

            response = client.post(
                "/api/v1/admin/placeholder-cards",
                json={
                    "jp_card_id": "SV10-015",
                    "name_jp": "\u30d4\u30ab\u30c1\u30e5\u30a6ex",
                    "name_en": "Pikachu ex",
                    "supertype": "Pokemon",
                    "subtypes": ["Basic"],
                    "hp": 200,
                    "types": ["Lightning"],
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["jp_card_id"] == "SV10-015"
        assert data["name_en"] == "Pikachu ex"
        assert data["supertype"] == "Pokemon"
        mock_service.create_placeholder.assert_called_once()
        mock_service.create_synthetic_mapping.assert_called_once()

    def test_create_placeholder_card_duplicate(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Should return 400 if placeholder already exists for jp_card_id."""
        existing = _make_placeholder()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing
        mock_db.execute.return_value = mock_result

        response = client.post(
            "/api/v1/admin/placeholder-cards",
            json={
                "jp_card_id": "SV10-015",
                "name_jp": "\u30d4\u30ab\u30c1\u30e5\u30a6ex",
                "name_en": "Pikachu ex",
                "supertype": "Pokemon",
            },
        )

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_create_placeholder_card_missing_required_fields(
        self, client: TestClient
    ) -> None:
        """Should return 422 when required fields are missing."""
        response = client.post(
            "/api/v1/admin/placeholder-cards",
            json={"jp_card_id": "SV10-015"},
        )

        assert response.status_code == 422

    def test_create_placeholder_card_with_optional_fields(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Should accept optional fields like attacks, source_url, source_account."""
        placeholder = _make_placeholder(
            source="llm_x",
            source_url="https://x.com/post/123",
            source_account="@pokejp",
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with patch("src.routers.admin.PlaceholderService") as mock_service_cls:
            mock_service = MagicMock()
            mock_service.create_placeholder = AsyncMock(return_value=placeholder)
            mock_service.create_synthetic_mapping = AsyncMock()
            mock_service_cls.return_value = mock_service

            response = client.post(
                "/api/v1/admin/placeholder-cards",
                json={
                    "jp_card_id": "SV10-020",
                    "name_jp": "\u30ea\u30b6\u30fc\u30c9\u30f3ex",
                    "name_en": "Charizard ex",
                    "supertype": "Pokemon",
                    "attacks": [
                        {
                            "name": "Fire Blast",
                            "cost": ["Fire", "Fire"],
                            "damage": "200",
                        }
                    ],
                    "source": "llm_x",
                    "source_url": "https://x.com/post/123",
                    "source_account": "@pokejp",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["source"] == "llm_x"
        assert data["source_url"] == "https://x.com/post/123"


class TestBatchCreatePlaceholderCards:
    """Tests for POST /api/v1/admin/placeholder-cards/batch."""

    def test_batch_create_success(self, client: TestClient, mock_db: AsyncMock) -> None:
        """Should batch create placeholder cards from JSON file."""
        p1 = _make_placeholder(jp_card_id="SV10-001", name_en="Card A")
        p2 = _make_placeholder(jp_card_id="SV10-002", name_en="Card B")

        # All execute calls return "not found" for duplicate checks
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with patch("src.routers.admin.PlaceholderService") as mock_service_cls:
            mock_service = MagicMock()
            mock_service.create_placeholder = AsyncMock(side_effect=[p1, p2])
            mock_service.create_synthetic_mapping = AsyncMock()
            mock_service_cls.return_value = mock_service

            file_content = json.dumps(
                {
                    "cards": [
                        {
                            "jp_card_id": "SV10-001",
                            "name_jp": "Card A JP",
                            "name_en": "Card A",
                            "supertype": "Pokemon",
                        },
                        {
                            "jp_card_id": "SV10-002",
                            "name_jp": "Card B JP",
                            "name_en": "Card B",
                            "supertype": "Trainer",
                        },
                    ]
                }
            )

            response = client.post(
                "/api/v1/admin/placeholder-cards/batch",
                files={
                    "file": (
                        "cards.json",
                        BytesIO(file_content.encode()),
                        "application/json",
                    )
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name_en"] == "Card A"
        assert data[1]["name_en"] == "Card B"

    def test_batch_create_invalid_format(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Should return 400 if uploaded JSON is missing 'cards' key."""
        file_content = json.dumps({"items": []})

        response = client.post(
            "/api/v1/admin/placeholder-cards/batch",
            files={
                "file": (
                    "cards.json",
                    BytesIO(file_content.encode()),
                    "application/json",
                )
            },
        )

        assert response.status_code == 400
        assert "missing 'cards' key" in response.json()["detail"]

    def test_batch_create_skips_duplicates(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Should skip cards that already exist as placeholders."""
        existing = _make_placeholder(jp_card_id="SV10-001")
        new_placeholder = _make_placeholder(jp_card_id="SV10-002", name_en="Card B")

        # First call returns existing, second returns None (not found)
        mock_existing_result = MagicMock()
        mock_existing_result.scalar_one_or_none.return_value = existing
        mock_new_result = MagicMock()
        mock_new_result.scalar_one_or_none.return_value = None
        mock_db.execute.side_effect = [mock_existing_result, mock_new_result]

        with patch("src.routers.admin.PlaceholderService") as mock_service_cls:
            mock_service = MagicMock()
            mock_service.create_placeholder = AsyncMock(return_value=new_placeholder)
            mock_service.create_synthetic_mapping = AsyncMock()
            mock_service_cls.return_value = mock_service

            file_content = json.dumps(
                {
                    "cards": [
                        {
                            "jp_card_id": "SV10-001",
                            "name_jp": "Card A JP",
                            "name_en": "Card A",
                            "supertype": "Pokemon",
                        },
                        {
                            "jp_card_id": "SV10-002",
                            "name_jp": "Card B JP",
                            "name_en": "Card B",
                            "supertype": "Trainer",
                        },
                    ]
                }
            )

            response = client.post(
                "/api/v1/admin/placeholder-cards/batch",
                files={
                    "file": (
                        "cards.json",
                        BytesIO(file_content.encode()),
                        "application/json",
                    )
                },
            )

        assert response.status_code == 200
        data = response.json()
        # Only the new card should be in the response
        assert len(data) == 1
        assert data[0]["name_en"] == "Card B"

    def test_batch_create_handles_errors_gracefully(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Should continue processing after individual card errors."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with patch("src.routers.admin.PlaceholderService") as mock_service_cls:
            mock_service = MagicMock()
            # First card fails, second succeeds
            good_placeholder = _make_placeholder(
                jp_card_id="SV10-002", name_en="Card B"
            )
            mock_service.create_placeholder = AsyncMock(
                side_effect=[RuntimeError("DB error"), good_placeholder]
            )
            mock_service.create_synthetic_mapping = AsyncMock()
            mock_service_cls.return_value = mock_service

            file_content = json.dumps(
                {
                    "cards": [
                        {
                            "jp_card_id": "SV10-001",
                            "name_jp": "Card A JP",
                            "name_en": "Card A",
                            "supertype": "Pokemon",
                        },
                        {
                            "jp_card_id": "SV10-002",
                            "name_jp": "Card B JP",
                            "name_en": "Card B",
                            "supertype": "Trainer",
                        },
                    ]
                }
            )

            response = client.post(
                "/api/v1/admin/placeholder-cards/batch",
                files={
                    "file": (
                        "cards.json",
                        BytesIO(file_content.encode()),
                        "application/json",
                    )
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name_en"] == "Card B"


class TestListPlaceholderCards:
    """Tests for GET /api/v1/admin/placeholder-cards."""

    def test_list_placeholder_cards_success(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Should return paginated list of placeholder cards."""
        p1 = _make_placeholder(jp_card_id="SV10-001", name_en="Card A")
        p2 = _make_placeholder(jp_card_id="SV10-002", name_en="Card B")

        # Mock for count query and paginated query
        mock_count_result = MagicMock()
        mock_count_result.scalars.return_value.all.return_value = [p1.id, p2.id]

        mock_items_result = MagicMock()
        mock_items_result.scalars.return_value.all.return_value = [p1, p2]

        mock_db.execute.side_effect = [mock_count_result, mock_items_result]

        response = client.get("/api/v1/admin/placeholder-cards")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2
        assert data["limit"] == 100
        assert data["offset"] == 0

    def test_list_placeholder_cards_with_filters(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Should accept filtering query parameters."""
        p1 = _make_placeholder(is_unreleased=True, source="manual")

        mock_count_result = MagicMock()
        mock_count_result.scalars.return_value.all.return_value = [p1.id]

        mock_items_result = MagicMock()
        mock_items_result.scalars.return_value.all.return_value = [p1]

        mock_db.execute.side_effect = [mock_count_result, mock_items_result]

        response = client.get(
            "/api/v1/admin/placeholder-cards",
            params={
                "is_unreleased": True,
                "source": "manual",
                "limit": 50,
                "offset": 10,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["limit"] == 50
        assert data["offset"] == 10

    def test_list_placeholder_cards_empty(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Should return empty list when no placeholders exist."""
        mock_count_result = MagicMock()
        mock_count_result.scalars.return_value.all.return_value = []

        mock_items_result = MagicMock()
        mock_items_result.scalars.return_value.all.return_value = []

        mock_db.execute.side_effect = [mock_count_result, mock_items_result]

        response = client.get("/api/v1/admin/placeholder-cards")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []


class TestGetPlaceholderCard:
    """Tests for GET /api/v1/admin/placeholder-cards/{placeholder_id}."""

    def test_get_placeholder_card_success(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Should return a single placeholder card by ID."""
        placeholder = _make_placeholder()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = placeholder
        mock_db.execute.return_value = mock_result

        response = client.get(f"/api/v1/admin/placeholder-cards/{placeholder.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(placeholder.id)
        assert data["name_en"] == "Pikachu ex"

    def test_get_placeholder_card_not_found(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Should return 404 when placeholder card does not exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        fake_id = uuid4()
        response = client.get(f"/api/v1/admin/placeholder-cards/{fake_id}")

        assert response.status_code == 404
        assert response.json()["detail"] == "Placeholder card not found"

    def test_get_placeholder_card_invalid_uuid(self, client: TestClient) -> None:
        """Should return 422 for invalid UUID format."""
        response = client.get("/api/v1/admin/placeholder-cards/not-a-uuid")

        assert response.status_code == 422


class TestUpdatePlaceholderCard:
    """Tests for PATCH /api/v1/admin/placeholder-cards/{placeholder_id}."""

    def test_update_placeholder_card_success(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Should update and return the placeholder card."""
        placeholder = _make_placeholder()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = placeholder
        mock_db.execute.return_value = mock_result

        response = client.patch(
            f"/api/v1/admin/placeholder-cards/{placeholder.id}",
            json={"name_en": "Pikachu ex V2", "hp": 210},
        )

        assert response.status_code == 200
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(placeholder)

    def test_update_placeholder_card_not_found(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Should return 404 when placeholder card does not exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        fake_id = uuid4()
        response = client.patch(
            f"/api/v1/admin/placeholder-cards/{fake_id}",
            json={"name_en": "Updated Name"},
        )

        assert response.status_code == 404

    def test_update_placeholder_card_partial(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Should only update provided fields (partial update)."""
        placeholder = _make_placeholder()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = placeholder
        mock_db.execute.return_value = mock_result

        response = client.patch(
            f"/api/v1/admin/placeholder-cards/{placeholder.id}",
            json={"is_unreleased": False},
        )

        assert response.status_code == 200
        # Verify setattr was called on the placeholder (via mock)
        mock_db.commit.assert_called_once()


class TestFetchTranslations:
    """Tests for POST /api/v1/admin/translations/fetch."""

    def test_fetch_translations_dry_run(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Should return dry run response without making changes."""
        response = client.post(
            "/api/v1/admin/translations/fetch",
            json={
                "accounts": ["@pokebeach", "@pokejp_translations"],
                "since_date": "2026-01-01",
                "dry_run": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["dry_run"] is True
        assert data["accounts_checked"] == ["@pokebeach", "@pokejp_translations"]
        assert data["posts_fetched"] == 0
        assert data["translations_parsed"] == 0
        assert data["placeholders_created"] == 0

    def test_fetch_translations_not_implemented(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Should return stub response (not yet implemented)."""
        response = client.post(
            "/api/v1/admin/translations/fetch",
            json={
                "accounts": ["@pokebeach"],
                "since_date": "2026-01-01",
                "dry_run": False,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["dry_run"] is False
        assert data["message"] == "LLM translation fetcher not yet implemented"

    def test_fetch_translations_missing_required_fields(
        self, client: TestClient
    ) -> None:
        """Should return 422 when required fields are missing."""
        response = client.post(
            "/api/v1/admin/translations/fetch",
            json={},
        )

        assert response.status_code == 422


class TestMarkPlaceholderReleased:
    """Tests for POST /api/v1/admin/placeholder-cards/{placeholder_id}/mark-released."""

    def test_mark_released_success(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Should mark a placeholder card as released."""
        placeholder = _make_placeholder()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = placeholder
        mock_db.execute.return_value = mock_result

        with patch("src.routers.admin.PlaceholderService") as mock_service_cls:
            mock_service = MagicMock()
            mock_service.mark_as_released = AsyncMock()
            mock_service_cls.return_value = mock_service

            response = client.post(
                f"/api/v1/admin/placeholder-cards/{placeholder.id}/mark-released",
                params={"official_card_id": "sv10-015"},
            )

        assert response.status_code == 200
        mock_service.mark_as_released.assert_called_once_with(
            jp_card_id=placeholder.jp_card_id,
            en_card_id="sv10-015",
        )

    def test_mark_released_not_found(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Should return 404 when placeholder does not exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        fake_id = uuid4()
        response = client.post(
            f"/api/v1/admin/placeholder-cards/{fake_id}/mark-released",
            params={"official_card_id": "sv10-015"},
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Placeholder card not found"

    def test_mark_released_missing_official_card_id(self, client: TestClient) -> None:
        """Should return 422 when official_card_id query param is missing."""
        fake_id = uuid4()
        response = client.post(
            f"/api/v1/admin/placeholder-cards/{fake_id}/mark-released",
        )

        assert response.status_code == 422


# --- Archetype Sprite endpoint tests ---


def _make_sprite(**overrides) -> MagicMock:
    """Create a mock ArchetypeSprite with sensible defaults."""
    mock = MagicMock(spec=ArchetypeSprite)
    defaults = {
        "id": uuid4(),
        "sprite_key": "charizard",
        "archetype_name": "Charizard ex",
        "display_name": None,
        "sprite_urls": [],
        "pokemon_names": ["charizard"],
    }
    defaults.update(overrides)
    for key, value in defaults.items():
        setattr(mock, key, value)
    return mock


class TestListArchetypeSprites:
    """Tests for GET /api/v1/admin/archetype-sprites."""

    def test_list_sprites_success(self, client: TestClient, mock_db: AsyncMock) -> None:
        """Should return list of all archetype sprite mappings."""
        s1 = _make_sprite(sprite_key="charizard")
        s2 = _make_sprite(
            sprite_key="dragapult-pidgeot",
            archetype_name="Dragapult ex",
        )

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [s1, s2]
        mock_db.execute.return_value = mock_result

        response = client.get("/api/v1/admin/archetype-sprites")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2
        assert data["items"][0]["sprite_key"] == "charizard"
        assert data["items"][1]["archetype_name"] == "Dragapult ex"

    def test_list_sprites_empty(self, client: TestClient, mock_db: AsyncMock) -> None:
        """Should return empty list when no sprites exist."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        response = client.get("/api/v1/admin/archetype-sprites")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []


class TestCreateArchetypeSprite:
    """Tests for POST /api/v1/admin/archetype-sprites."""

    def test_create_sprite_success(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Should create a new sprite mapping."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        # db.refresh is a no-op; the real ArchetypeSprite object
        # created in the endpoint already has all attrs set.
        mock_db.refresh = AsyncMock(side_effect=lambda x: None)

        response = client.post(
            "/api/v1/admin/archetype-sprites",
            json={
                "sprite_key": "new-mon",
                "archetype_name": "New Mon ex",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["sprite_key"] == "new-mon"
        assert data["archetype_name"] == "New Mon ex"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_create_sprite_duplicate(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Should return 400 if sprite key already exists."""
        existing = _make_sprite(sprite_key="charizard")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing
        mock_db.execute.return_value = mock_result

        response = client.post(
            "/api/v1/admin/archetype-sprites",
            json={
                "sprite_key": "charizard",
                "archetype_name": "Charizard ex",
            },
        )

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_create_sprite_missing_fields(self, client: TestClient) -> None:
        """Should return 422 when required fields are missing."""
        response = client.post(
            "/api/v1/admin/archetype-sprites",
            json={"sprite_key": "charizard"},
        )

        assert response.status_code == 422


class TestUpdateArchetypeSprite:
    """Tests for PATCH /api/v1/admin/archetype-sprites/{sprite_key}."""

    def test_update_sprite_success(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Should update the archetype name for a sprite key."""
        sprite = _make_sprite(sprite_key="charizard")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sprite
        mock_db.execute.return_value = mock_result

        response = client.patch(
            "/api/v1/admin/archetype-sprites/charizard",
            json={
                "archetype_name": "Charizard ex Updated",
            },
        )

        assert response.status_code == 200
        assert sprite.archetype_name == "Charizard ex Updated"
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(sprite)

    def test_update_sprite_not_found(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Should return 404 when sprite key does not exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        response = client.patch(
            "/api/v1/admin/archetype-sprites/nonexistent",
            json={
                "archetype_name": "Something",
            },
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestDeleteArchetypeSprite:
    """Tests for DELETE /api/v1/admin/archetype-sprites/{sprite_key}."""

    def test_delete_sprite_success(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Should delete a sprite mapping and return confirmation."""
        sprite = _make_sprite(sprite_key="charizard")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sprite
        mock_db.execute.return_value = mock_result

        response = client.delete("/api/v1/admin/archetype-sprites/charizard")

        assert response.status_code == 200
        assert response.json() == {"deleted": "charizard"}
        mock_db.delete.assert_called_once_with(sprite)
        mock_db.commit.assert_called_once()

    def test_delete_sprite_not_found(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Should return 404 when sprite key does not exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        response = client.delete("/api/v1/admin/archetype-sprites/nonexistent")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestSeedArchetypeSprites:
    """Tests for POST /api/v1/admin/archetype-sprites/seed."""

    def test_seed_sprites_success(self, client: TestClient, mock_db: AsyncMock) -> None:
        """Should seed sprites and return inserted count."""
        with patch("src.routers.admin.ArchetypeNormalizer") as mock_norm_cls:
            mock_norm_cls.seed_db_sprites = AsyncMock(return_value=42)

            response = client.post("/api/v1/admin/archetype-sprites/seed")

        assert response.status_code == 200
        assert response.json() == {"inserted": 42}
        mock_norm_cls.seed_db_sprites.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_seed_sprites_zero_inserted(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Should return 0 when all entries already exist."""
        with patch("src.routers.admin.ArchetypeNormalizer") as mock_norm_cls:
            mock_norm_cls.seed_db_sprites = AsyncMock(return_value=0)

            response = client.post("/api/v1/admin/archetype-sprites/seed")

        assert response.status_code == 200
        assert response.json() == {"inserted": 0}
