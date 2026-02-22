"""Tests for admin tournament creation endpoint."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.db.database import get_db
from src.dependencies.admin import require_admin
from src.main import app
from src.models.user import User


@pytest.fixture
def mock_db() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_admin() -> MagicMock:
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.email = "admin@trainerlab.gg"
    return user


@pytest.fixture
def client(mock_db: AsyncMock, mock_admin: MagicMock) -> TestClient:
    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[require_admin] = lambda: mock_admin
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def unauthed_client(mock_db: AsyncMock) -> TestClient:
    """Client without admin override — triggers 403."""

    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


URL = "/api/v1/admin/tournaments"


class TestCreateTournamentWithPlacements:
    """POST /api/v1/admin/tournaments with placements."""

    def test_creates_tournament_with_placements(
        self,
        client: TestClient,
        mock_db: AsyncMock,
    ) -> None:
        # No duplicate source_url
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        payload = {
            "name": "Test Cup 2026",
            "date": "2026-03-01",
            "region": "NA",
            "format": "standard",
            "best_of": 3,
            "participant_count": 32,
            "source_url": "https://example.com/test",
            "tier": "league_cup",
            "placements": [
                {
                    "placement": 1,
                    "player_name": "Ash K.",
                    "archetype": "Charizard ex",
                },
                {
                    "placement": 2,
                    "player_name": "Misty W.",
                    "archetype": "Lugia VSTAR",
                },
            ],
        }

        with patch("src.routers.admin.ArchetypeNormalizer") as mock_norm_cls:
            mock_normalizer = MagicMock()
            mock_normalizer.load_db_sprites = AsyncMock()
            mock_normalizer.resolve.return_value = (
                "Charizard ex",
                "Charizard ex",
                "text_label",
            )
            mock_norm_cls.return_value = mock_normalizer

            resp = client.post(URL, json=payload)

        assert resp.status_code == 200
        body = resp.json()
        assert body["name"] == "Test Cup 2026"
        assert body["region"] == "NA"
        assert body["placements_created"] == 2
        assert body["date"] == "2026-03-01"

        # Tournament + 2 placements added
        assert mock_db.add.call_count == 3
        mock_db.commit.assert_awaited_once()

    def test_creates_tournament_no_placements(
        self,
        client: TestClient,
        mock_db: AsyncMock,
    ) -> None:
        payload = {
            "name": "Empty Cup",
            "date": "2026-04-01",
            "region": "EU",
            "placements": [],
        }

        with patch("src.routers.admin.ArchetypeNormalizer") as mock_norm_cls:
            mock_normalizer = MagicMock()
            mock_normalizer.load_db_sprites = AsyncMock()
            mock_norm_cls.return_value = mock_normalizer

            resp = client.post(URL, json=payload)

        assert resp.status_code == 200
        body = resp.json()
        assert body["placements_created"] == 0
        assert body["archetypes_detected"] == 0
        # Only tournament added
        assert mock_db.add.call_count == 1


class TestDuplicateSourceUrl:
    """Duplicate source_url returns 409."""

    def test_duplicate_source_url_returns_409(
        self,
        client: TestClient,
        mock_db: AsyncMock,
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        payload = {
            "name": "Dup Cup",
            "date": "2026-05-01",
            "region": "JP",
            "source_url": "https://example.com/dup",
        }
        resp = client.post(URL, json=payload)
        assert resp.status_code == 409
        assert "source_url" in resp.json()["detail"]


class TestAdminAuthRequired:
    """Admin auth required — no admin user returns 403."""

    def test_no_admin_returns_403(
        self,
        unauthed_client: TestClient,
    ) -> None:
        payload = {
            "name": "No Auth Cup",
            "date": "2026-06-01",
            "region": "NA",
        }
        resp = unauthed_client.post(URL, json=payload)
        # Without valid auth, should be 401 or 403
        assert resp.status_code in (401, 403)


class TestArchetypeNormalization:
    """Archetype normalization runs on provided archetypes."""

    def test_normalizer_called_for_archetypes(
        self,
        client: TestClient,
        mock_db: AsyncMock,
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        payload = {
            "name": "Norm Cup",
            "date": "2026-07-01",
            "region": "NA",
            "source_url": "https://example.com/norm",
            "placements": [
                {
                    "placement": 1,
                    "player_name": "Brock",
                    "archetype": "Charizard ex",
                },
                {
                    "placement": 2,
                    "player_name": "Gary",
                },
            ],
        }

        with patch("src.routers.admin.ArchetypeNormalizer") as mock_norm_cls:
            mock_normalizer = MagicMock()
            mock_normalizer.load_db_sprites = AsyncMock()
            mock_normalizer.resolve.return_value = (
                "Charizard ex",
                "Charizard ex",
                "text_label",
            )
            mock_norm_cls.return_value = mock_normalizer

            resp = client.post(URL, json=payload)

        assert resp.status_code == 200
        body = resp.json()
        # Only the first placement had an archetype
        assert body["archetypes_detected"] == 1
        mock_normalizer.resolve.assert_called_once_with(
            sprite_urls=[],
            html_archetype="Charizard ex",
            decklist=None,
        )

    def test_normalizer_exception_keeps_original(
        self,
        client: TestClient,
        mock_db: AsyncMock,
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        payload = {
            "name": "Error Cup",
            "date": "2026-08-01",
            "region": "EU",
            "source_url": "https://example.com/err",
            "placements": [
                {
                    "placement": 1,
                    "archetype": "Bad Archetype",
                },
            ],
        }

        with patch("src.routers.admin.ArchetypeNormalizer") as mock_norm_cls:
            mock_normalizer = MagicMock()
            mock_normalizer.load_db_sprites = AsyncMock()
            mock_normalizer.resolve.side_effect = RuntimeError("boom")
            mock_norm_cls.return_value = mock_normalizer

            resp = client.post(URL, json=payload)

        assert resp.status_code == 200
        body = resp.json()
        assert body["placements_created"] == 1
        # Normalization failed, so 0 detected
        assert body["archetypes_detected"] == 0
