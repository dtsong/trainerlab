"""Tests for format and rotation router endpoints."""

from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from src.db.database import get_db
from src.dependencies.beta import require_beta
from src.main import app
from src.models import FormatConfig, RotationImpact


@pytest.fixture
def mock_format_config() -> FormatConfig:
    """Create a mock current format config."""
    return FormatConfig(
        id=uuid4(),
        name="svi-tef",
        display_name="Scarlet & Violet - Temporal Forces",
        legal_sets=["sv1", "sv2", "sv3", "sv4", "sv5"],
        start_date=date.today() - timedelta(days=30),
        end_date=None,
        is_current=True,
        is_upcoming=False,
        rotation_details=None,
    )


@pytest.fixture
def mock_upcoming_format() -> FormatConfig:
    """Create a mock upcoming format config."""
    return FormatConfig(
        id=uuid4(),
        name="svi-por",
        display_name="Scarlet & Violet - Paldean Fates",
        legal_sets=["sv3", "sv4", "sv5", "sv6"],
        start_date=date.today() + timedelta(days=30),
        end_date=None,
        is_current=False,
        is_upcoming=True,
        rotation_details={
            "rotating_out_sets": ["sv1", "sv2"],
            "new_set": "sv6",
        },
    )


@pytest.fixture
def mock_rotation_impact() -> RotationImpact:
    """Create a mock rotation impact."""
    return RotationImpact(
        id=uuid4(),
        format_transition="svi-tef-to-svi-por",
        archetype_id="charizard-ex",
        archetype_name="Charizard ex",
        survival_rating="adapts",
        rotating_cards=[
            {
                "card_name": "Arven",
                "card_id": "sv1-166",
                "count": 4,
                "role": "supporter",
                "replacement": "Iono",
            }
        ],
        analysis="Charizard ex loses some consistency cards but remains viable.",
        jp_evidence="Strong performance in JP post-rotation meta.",
        jp_survival_share=0.15,
    )


class TestGetCurrentFormat:
    """Tests for GET /api/v1/format/current."""

    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def client(self, mock_db: AsyncMock) -> TestClient:
        async def override_get_db():
            yield mock_db

        async def override_require_beta():
            return None

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[require_beta] = override_require_beta
        yield TestClient(app)
        app.dependency_overrides.clear()

    def test_returns_current_format(
        self,
        client: TestClient,
        mock_db: AsyncMock,
        mock_format_config: FormatConfig,
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_format_config
        mock_db.execute.return_value = mock_result

        response = client.get("/api/v1/format/current")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "svi-tef"
        assert data["is_current"] is True

    def test_returns_404_when_no_current_format(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        response = client.get("/api/v1/format/current")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_returns_503_on_database_error(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        mock_db.execute.side_effect = SQLAlchemyError("DB error")

        response = client.get("/api/v1/format/current")

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE


class TestGetUpcomingFormat:
    """Tests for GET /api/v1/format/upcoming."""

    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def client(self, mock_db: AsyncMock) -> TestClient:
        async def override_get_db():
            yield mock_db

        async def override_require_beta():
            return None

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[require_beta] = override_require_beta
        yield TestClient(app)
        app.dependency_overrides.clear()

    def test_returns_upcoming_format_with_countdown(
        self,
        client: TestClient,
        mock_db: AsyncMock,
        mock_upcoming_format: FormatConfig,
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_upcoming_format
        mock_db.execute.return_value = mock_result

        response = client.get("/api/v1/format/upcoming")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["format"]["name"] == "svi-por"
        assert data["days_until_rotation"] >= 0
        assert "rotation_date" in data

    def test_returns_404_when_no_upcoming_format(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        response = client.get("/api/v1/format/upcoming")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_returns_500_when_no_start_date(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        format_no_date = FormatConfig(
            id=uuid4(),
            name="svi-por",
            display_name="Scarlet & Violet",
            legal_sets=["sv1"],
            start_date=None,
            is_current=False,
            is_upcoming=True,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = format_no_date
        mock_db.execute.return_value = mock_result

        response = client.get("/api/v1/format/upcoming")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


class TestGetRotationImpact:
    """Tests for GET /api/v1/rotation/impact."""

    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def client(self, mock_db: AsyncMock) -> TestClient:
        async def override_get_db():
            yield mock_db

        async def override_require_beta():
            return None

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[require_beta] = override_require_beta
        yield TestClient(app)
        app.dependency_overrides.clear()

    def test_returns_rotation_impacts(
        self,
        client: TestClient,
        mock_db: AsyncMock,
        mock_rotation_impact: RotationImpact,
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_rotation_impact]
        mock_db.execute.return_value = mock_result

        response = client.get(
            "/api/v1/rotation/impact",
            params={"transition": "svi-tef-to-svi-por"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["format_transition"] == "svi-tef-to-svi-por"
        assert data["total_archetypes"] == 1
        assert len(data["impacts"]) == 1

    def test_returns_empty_list_when_no_impacts(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        response = client.get(
            "/api/v1/rotation/impact",
            params={"transition": "unknown-transition"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_archetypes"] == 0
        assert data["impacts"] == []

    def test_returns_503_on_database_error(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        mock_db.execute.side_effect = SQLAlchemyError("DB error")

        response = client.get(
            "/api/v1/rotation/impact",
            params={"transition": "svi-tef-to-svi-por"},
        )

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE


class TestGetArchetypeRotationImpact:
    """Tests for GET /api/v1/rotation/impact/{archetype_id}."""

    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def client(self, mock_db: AsyncMock) -> TestClient:
        async def override_get_db():
            yield mock_db

        async def override_require_beta():
            return None

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[require_beta] = override_require_beta
        yield TestClient(app)
        app.dependency_overrides.clear()

    def test_returns_archetype_impact(
        self,
        client: TestClient,
        mock_db: AsyncMock,
        mock_rotation_impact: RotationImpact,
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_rotation_impact
        mock_db.execute.return_value = mock_result

        response = client.get(
            "/api/v1/rotation/impact/charizard-ex",
            params={"transition": "svi-tef-to-svi-por"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["archetype_id"] == "charizard-ex"
        assert data["survival_rating"] == "adapts"

    def test_returns_404_when_not_found(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        response = client.get(
            "/api/v1/rotation/impact/nonexistent",
            params={"transition": "svi-tef-to-svi-por"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_derives_transition_when_not_provided(
        self,
        client: TestClient,
        mock_db: AsyncMock,
        mock_format_config: FormatConfig,
        mock_upcoming_format: FormatConfig,
        mock_rotation_impact: RotationImpact,
    ) -> None:
        upcoming_result = MagicMock()
        upcoming_result.scalar_one_or_none.return_value = mock_upcoming_format

        current_result = MagicMock()
        current_result.scalar_one_or_none.return_value = mock_format_config

        impact_result = MagicMock()
        impact_result.scalar_one_or_none.return_value = mock_rotation_impact

        mock_db.execute.side_effect = [
            upcoming_result,
            current_result,
            impact_result,
        ]

        response = client.get("/api/v1/rotation/impact/charizard-ex")

        assert response.status_code == status.HTTP_200_OK

    def test_returns_404_when_no_upcoming_format_for_auto_transition(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        response = client.get("/api/v1/rotation/impact/charizard-ex")

        assert response.status_code == status.HTTP_404_NOT_FOUND
