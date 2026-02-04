"""Tests for translations router."""

from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.db.database import get_db
from src.dependencies.auth import get_current_user
from src.main import app
from src.models.user import User


def _make_mock_user(email: str = "user@example.com") -> MagicMock:
    """Create a mock user with given email."""
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.email = email
    user.display_name = "Test User"
    user.avatar_url = None
    user.preferences = {}
    user.created_at = datetime.now(UTC)
    user.updated_at = datetime.now(UTC)
    return user


# ---------------------------------------------------------------------------
# Public endpoints
# ---------------------------------------------------------------------------


class TestGetJPAdoptionRates:
    """Tests for GET /api/v1/japan/adoption-rates."""

    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def client(self, mock_db: AsyncMock) -> TestClient:
        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        yield TestClient(app)
        app.dependency_overrides.clear()

    def test_returns_adoption_rates(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test that adoption rates are returned with default parameters."""
        mock_rate = MagicMock()
        mock_rate.id = uuid4()
        mock_rate.card_id = "sv7-001"
        mock_rate.card_name_jp = "リザードンex"
        mock_rate.card_name_en = "Charizard ex"
        mock_rate.inclusion_rate = 0.85
        mock_rate.avg_copies = 2.5
        mock_rate.archetype_context = "Charizard"
        mock_rate.period_start = date(2025, 1, 1)
        mock_rate.period_end = date(2025, 1, 31)
        mock_rate.source = "pokeca-data"

        # First execute call: query results
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_rate]
        # Second execute call: count
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_db.execute = AsyncMock(side_effect=[mock_result, mock_count_result])

        response = client.get("/api/v1/japan/adoption-rates")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["rates"]) == 1
        assert data["rates"][0]["card_id"] == "sv7-001"
        assert data["rates"][0]["inclusion_rate"] == 0.85

    def test_returns_empty_list_when_no_data(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test that an empty list is returned when no adoption rate data exists."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_db.execute = AsyncMock(side_effect=[mock_result, mock_count_result])

        response = client.get("/api/v1/japan/adoption-rates")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["rates"] == []

    def test_filters_by_archetype(self, client: TestClient, mock_db: AsyncMock) -> None:
        """Test that the archetype query parameter filters results."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_db.execute = AsyncMock(side_effect=[mock_result, mock_count_result])

        response = client.get("/api/v1/japan/adoption-rates?archetype=Lugia")

        assert response.status_code == 200
        # Two db.execute calls: query + count
        assert mock_db.execute.call_count == 2

    def test_accepts_days_parameter(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test that the days query parameter is accepted."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_db.execute = AsyncMock(side_effect=[mock_result, mock_count_result])

        response = client.get("/api/v1/japan/adoption-rates?days=7")
        assert response.status_code == 200

    def test_rejects_days_out_of_range(self, client: TestClient) -> None:
        """Test that days=0 or days=91 are rejected by validation."""
        response = client.get("/api/v1/japan/adoption-rates?days=0")
        assert response.status_code == 422

        response = client.get("/api/v1/japan/adoption-rates?days=91")
        assert response.status_code == 422

    def test_accepts_limit_parameter(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test that the limit query parameter is accepted."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_db.execute = AsyncMock(side_effect=[mock_result, mock_count_result])

        response = client.get("/api/v1/japan/adoption-rates?limit=10")
        assert response.status_code == 200

    def test_rejects_limit_out_of_range(self, client: TestClient) -> None:
        """Test that limit=0 or limit=101 are rejected by validation."""
        response = client.get("/api/v1/japan/adoption-rates?limit=0")
        assert response.status_code == 422

        response = client.get("/api/v1/japan/adoption-rates?limit=101")
        assert response.status_code == 422


class TestGetJPUpcomingCards:
    """Tests for GET /api/v1/japan/upcoming-cards."""

    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def client(self, mock_db: AsyncMock) -> TestClient:
        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        yield TestClient(app)
        app.dependency_overrides.clear()

    def test_returns_upcoming_cards(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test that upcoming cards are returned with default parameters."""
        mock_card = MagicMock()
        mock_card.id = uuid4()
        mock_card.jp_card_id = "sv8-055"
        mock_card.jp_set_id = "sv8"
        mock_card.name_jp = "テツノイサハex"
        mock_card.name_en = "Iron Leaves ex"
        mock_card.card_type = "Pokemon"
        mock_card.competitive_impact = 4
        mock_card.affected_archetypes = ["Raging Bolt", "Iron Thorns"]
        mock_card.notes = "Strong attacker"
        mock_card.expected_release_set = "Surging Sparks"
        mock_card.is_released = False

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_card]
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_db.execute = AsyncMock(side_effect=[mock_result, mock_count_result])

        response = client.get("/api/v1/japan/upcoming-cards")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["cards"]) == 1
        assert data["cards"][0]["jp_card_id"] == "sv8-055"
        assert data["cards"][0]["competitive_impact"] == 4
        assert data["cards"][0]["is_released"] is False

    def test_returns_empty_list_when_no_cards(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test that an empty list is returned when no upcoming cards exist."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_db.execute = AsyncMock(side_effect=[mock_result, mock_count_result])

        response = client.get("/api/v1/japan/upcoming-cards")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["cards"] == []

    def test_accepts_include_released_parameter(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test that include_released=true is accepted."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_db.execute = AsyncMock(side_effect=[mock_result, mock_count_result])

        response = client.get("/api/v1/japan/upcoming-cards?include_released=true")
        assert response.status_code == 200

    def test_accepts_min_impact_parameter(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test that min_impact query parameter is accepted."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_db.execute = AsyncMock(side_effect=[mock_result, mock_count_result])

        response = client.get("/api/v1/japan/upcoming-cards?min_impact=3")
        assert response.status_code == 200

    def test_rejects_min_impact_out_of_range(self, client: TestClient) -> None:
        """Test that min_impact=0 or min_impact=6 are rejected."""
        response = client.get("/api/v1/japan/upcoming-cards?min_impact=0")
        assert response.status_code == 422

        response = client.get("/api/v1/japan/upcoming-cards?min_impact=6")
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Admin endpoints
# ---------------------------------------------------------------------------


class TestGetAdminTranslations:
    """Tests for GET /api/v1/admin/translations."""

    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def admin_user(self) -> MagicMock:
        return _make_mock_user(email="admin@trainerlab.gg")

    @pytest.fixture
    def non_admin_user(self) -> MagicMock:
        return _make_mock_user(email="regular@example.com")

    @pytest.fixture
    def admin_client(self, mock_db: AsyncMock, admin_user: MagicMock) -> TestClient:
        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = lambda: admin_user
        yield TestClient(app)
        app.dependency_overrides.clear()

    @pytest.fixture
    def non_admin_client(
        self, mock_db: AsyncMock, non_admin_user: MagicMock
    ) -> TestClient:
        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = lambda: non_admin_user
        yield TestClient(app)
        app.dependency_overrides.clear()

    @patch(
        "src.routers.translations.settings",
        MagicMock(admin_emails="admin@trainerlab.gg"),
    )
    def test_returns_translations_for_admin(
        self, admin_client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test that admin can list translations."""
        mock_content = MagicMock()
        mock_content.id = uuid4()
        mock_content.source_id = "article-123"
        mock_content.source_url = "https://pokeca.example.com/article/1"
        mock_content.content_type = "article"
        mock_content.original_text = "テスト記事"
        mock_content.translated_text = "Test article"
        mock_content.status = "completed"
        mock_content.translated_at = datetime.now(UTC)
        mock_content.uncertainties = None
        mock_content.created_at = datetime.now(UTC)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_content]
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_db.execute = AsyncMock(side_effect=[mock_result, mock_count_result])

        response = admin_client.get("/api/v1/admin/translations")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["content"]) == 1
        assert data["content"][0]["source_id"] == "article-123"

    @patch(
        "src.routers.translations.settings",
        MagicMock(admin_emails="admin@trainerlab.gg"),
    )
    def test_returns_403_for_non_admin(self, non_admin_client: TestClient) -> None:
        """Test that non-admin users receive 403."""
        response = non_admin_client.get("/api/v1/admin/translations")
        assert response.status_code == 403
        assert "admin" in response.json()["detail"].lower()

    @patch(
        "src.routers.translations.settings",
        MagicMock(admin_emails="admin@trainerlab.gg"),
    )
    def test_filters_by_status(
        self, admin_client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test that status_filter query parameter filters results."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_db.execute = AsyncMock(side_effect=[mock_result, mock_count_result])

        response = admin_client.get("/api/v1/admin/translations?status_filter=pending")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["content"] == []

    @patch(
        "src.routers.translations.settings",
        MagicMock(admin_emails="admin@trainerlab.gg"),
    )
    def test_filters_by_content_type(
        self, admin_client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test that content_type query parameter filters results."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_db.execute = AsyncMock(side_effect=[mock_result, mock_count_result])

        response = admin_client.get("/api/v1/admin/translations?content_type=deck_list")

        assert response.status_code == 200


class TestSubmitTranslation:
    """Tests for POST /api/v1/admin/translations."""

    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def admin_user(self) -> MagicMock:
        return _make_mock_user(email="admin@trainerlab.gg")

    @pytest.fixture
    def non_admin_user(self) -> MagicMock:
        return _make_mock_user(email="regular@example.com")

    @pytest.fixture
    def admin_client(self, mock_db: AsyncMock, admin_user: MagicMock) -> TestClient:
        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = lambda: admin_user
        yield TestClient(app)
        app.dependency_overrides.clear()

    @pytest.fixture
    def non_admin_client(
        self, mock_db: AsyncMock, non_admin_user: MagicMock
    ) -> TestClient:
        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = lambda: non_admin_user
        yield TestClient(app)
        app.dependency_overrides.clear()

    @patch(
        "src.routers.translations.settings",
        MagicMock(admin_emails="admin@trainerlab.gg"),
    )
    def test_submits_new_translation(
        self, admin_client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test that admin can submit a new URL for translation."""
        # First execute: check existing (not found)
        mock_existing_result = MagicMock()
        mock_existing_result.scalar_one_or_none.return_value = None

        # After db.add + commit + refresh, the new_content object is created
        # We mock db.execute, db.commit, db.refresh
        mock_db.execute = AsyncMock(return_value=mock_existing_result)
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        response = admin_client.post(
            "/api/v1/admin/translations",
            json={
                "url": "https://pokeca.example.com/new-article",
                "content_type": "article",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["source_url"] == "https://pokeca.example.com/new-article"
        assert data["status"] == "pending"
        assert data["content_type"] == "article"

    @patch(
        "src.routers.translations.settings",
        MagicMock(admin_emails="admin@trainerlab.gg"),
    )
    def test_returns_existing_if_url_already_submitted(
        self, admin_client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test that submitting a duplicate URL returns the existing record."""
        existing = MagicMock()
        existing.id = uuid4()
        existing.source_id = "existing-123"
        existing.source_url = "https://pokeca.example.com/existing"
        existing.content_type = "article"
        existing.original_text = "既存の記事"
        existing.translated_text = "Existing article"
        existing.status = "completed"
        existing.translated_at = datetime.now(UTC)
        existing.uncertainties = None

        mock_existing_result = MagicMock()
        mock_existing_result.scalar_one_or_none.return_value = existing

        mock_db.execute = AsyncMock(return_value=mock_existing_result)

        response = admin_client.post(
            "/api/v1/admin/translations",
            json={"url": "https://pokeca.example.com/existing"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["source_id"] == "existing-123"
        assert data["status"] == "completed"
        # commit should not be called for duplicates
        mock_db.commit.assert_not_called()

    @patch(
        "src.routers.translations.settings",
        MagicMock(admin_emails="admin@trainerlab.gg"),
    )
    def test_returns_403_for_non_admin(self, non_admin_client: TestClient) -> None:
        """Test that non-admin users receive 403 on submit."""
        response = non_admin_client.post(
            "/api/v1/admin/translations",
            json={"url": "https://pokeca.example.com/article"},
        )
        assert response.status_code == 403

    @patch(
        "src.routers.translations.settings",
        MagicMock(admin_emails="admin@trainerlab.gg"),
    )
    def test_returns_500_on_database_error(
        self, admin_client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test that 500 is returned when a database error occurs."""
        from sqlalchemy.exc import SQLAlchemyError

        mock_db.execute = AsyncMock(side_effect=SQLAlchemyError("DB down"))
        mock_db.rollback = AsyncMock()

        response = admin_client.post(
            "/api/v1/admin/translations",
            json={"url": "https://pokeca.example.com/fail"},
        )

        assert response.status_code == 500
        assert "failed" in response.json()["detail"].lower()


class TestUpdateTranslation:
    """Tests for PATCH /api/v1/admin/translations/{id}."""

    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def admin_user(self) -> MagicMock:
        return _make_mock_user(email="admin@trainerlab.gg")

    @pytest.fixture
    def non_admin_user(self) -> MagicMock:
        return _make_mock_user(email="regular@example.com")

    @pytest.fixture
    def admin_client(self, mock_db: AsyncMock, admin_user: MagicMock) -> TestClient:
        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = lambda: admin_user
        yield TestClient(app)
        app.dependency_overrides.clear()

    @pytest.fixture
    def non_admin_client(
        self, mock_db: AsyncMock, non_admin_user: MagicMock
    ) -> TestClient:
        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = lambda: non_admin_user
        yield TestClient(app)
        app.dependency_overrides.clear()

    @patch(
        "src.routers.translations.settings",
        MagicMock(admin_emails="admin@trainerlab.gg"),
    )
    def test_updates_translation_text(
        self, admin_client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test that admin can update translation text."""
        translation_id = uuid4()
        content = MagicMock()
        content.id = translation_id
        content.source_id = "src-1"
        content.source_url = "https://pokeca.example.com/1"
        content.content_type = "article"
        content.original_text = "元のテキスト"
        content.translated_text = "Updated translation"
        content.status = "completed"
        content.translated_at = datetime.now(UTC)
        content.uncertainties = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = content
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        response = admin_client.patch(
            f"/api/v1/admin/translations/{translation_id}",
            json={"translated_text": "Updated translation"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["translated_text"] == "Updated translation"

    @patch(
        "src.routers.translations.settings",
        MagicMock(admin_emails="admin@trainerlab.gg"),
    )
    def test_updates_translation_status(
        self, admin_client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test that admin can update translation status."""
        translation_id = uuid4()
        content = MagicMock()
        content.id = translation_id
        content.source_id = "src-1"
        content.source_url = "https://pokeca.example.com/1"
        content.content_type = "article"
        content.original_text = "テスト"
        content.translated_text = None
        content.status = "failed"
        content.translated_at = None
        content.uncertainties = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = content
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        response = admin_client.patch(
            f"/api/v1/admin/translations/{translation_id}",
            json={"status": "failed"},
        )

        assert response.status_code == 200

    @patch(
        "src.routers.translations.settings",
        MagicMock(admin_emails="admin@trainerlab.gg"),
    )
    def test_returns_404_when_translation_not_found(
        self, admin_client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test that 404 is returned for a non-existent translation ID."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        fake_id = uuid4()
        response = admin_client.patch(
            f"/api/v1/admin/translations/{fake_id}",
            json={"status": "completed"},
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @patch(
        "src.routers.translations.settings",
        MagicMock(admin_emails="admin@trainerlab.gg"),
    )
    def test_returns_403_for_non_admin(self, non_admin_client: TestClient) -> None:
        """Test that non-admin users receive 403 on update."""
        fake_id = uuid4()
        response = non_admin_client.patch(
            f"/api/v1/admin/translations/{fake_id}",
            json={"status": "completed"},
        )
        assert response.status_code == 403


class TestGetGlossaryOverrides:
    """Tests for GET /api/v1/admin/translations/glossary."""

    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def admin_user(self) -> MagicMock:
        return _make_mock_user(email="admin@trainerlab.gg")

    @pytest.fixture
    def non_admin_user(self) -> MagicMock:
        return _make_mock_user(email="regular@example.com")

    @pytest.fixture
    def admin_client(self, mock_db: AsyncMock, admin_user: MagicMock) -> TestClient:
        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = lambda: admin_user
        yield TestClient(app)
        app.dependency_overrides.clear()

    @pytest.fixture
    def non_admin_client(
        self, mock_db: AsyncMock, non_admin_user: MagicMock
    ) -> TestClient:
        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = lambda: non_admin_user
        yield TestClient(app)
        app.dependency_overrides.clear()

    @patch(
        "src.routers.translations.settings",
        MagicMock(admin_emails="admin@trainerlab.gg"),
    )
    def test_returns_glossary_terms(
        self, admin_client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test that admin can list glossary term overrides."""
        mock_term = MagicMock()
        mock_term.id = uuid4()
        mock_term.term_jp = "ポケモンex"
        mock_term.term_en = "Pokemon ex"
        mock_term.context = "Card name suffix"
        mock_term.source = "admin"
        mock_term.is_active = True

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_term]
        mock_db.execute = AsyncMock(return_value=mock_result)

        response = admin_client.get("/api/v1/admin/translations/glossary")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["terms"][0]["term_jp"] == "ポケモンex"
        assert data["terms"][0]["is_active"] is True

    @patch(
        "src.routers.translations.settings",
        MagicMock(admin_emails="admin@trainerlab.gg"),
    )
    def test_returns_empty_glossary(
        self, admin_client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test that empty list is returned when no glossary terms exist."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        response = admin_client.get("/api/v1/admin/translations/glossary")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["terms"] == []

    @patch(
        "src.routers.translations.settings",
        MagicMock(admin_emails="admin@trainerlab.gg"),
    )
    def test_returns_403_for_non_admin(self, non_admin_client: TestClient) -> None:
        """Test that non-admin users receive 403."""
        response = non_admin_client.get("/api/v1/admin/translations/glossary")
        assert response.status_code == 403


class TestCreateGlossaryOverride:
    """Tests for POST /api/v1/admin/translations/glossary."""

    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def admin_user(self) -> MagicMock:
        return _make_mock_user(email="admin@trainerlab.gg")

    @pytest.fixture
    def non_admin_user(self) -> MagicMock:
        return _make_mock_user(email="regular@example.com")

    @pytest.fixture
    def admin_client(self, mock_db: AsyncMock, admin_user: MagicMock) -> TestClient:
        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = lambda: admin_user
        yield TestClient(app)
        app.dependency_overrides.clear()

    @pytest.fixture
    def non_admin_client(
        self, mock_db: AsyncMock, non_admin_user: MagicMock
    ) -> TestClient:
        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = lambda: non_admin_user
        yield TestClient(app)
        app.dependency_overrides.clear()

    @patch(
        "src.routers.translations.settings",
        MagicMock(admin_emails="admin@trainerlab.gg"),
    )
    def test_creates_new_glossary_term(
        self, admin_client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test that admin can create a new glossary term override."""
        # No existing term found
        mock_existing_result = MagicMock()
        mock_existing_result.scalar_one_or_none.return_value = None

        mock_db.execute = AsyncMock(return_value=mock_existing_result)
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        response = admin_client.post(
            "/api/v1/admin/translations/glossary",
            json={
                "term_jp": "対戦",
                "term_en": "battle",
                "context": "General gameplay",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["term_jp"] == "対戦"
        assert data["term_en"] == "battle"
        assert data["source"] == "admin"
        assert data["is_active"] is True

    @patch(
        "src.routers.translations.settings",
        MagicMock(admin_emails="admin@trainerlab.gg"),
    )
    def test_updates_existing_glossary_term(
        self, admin_client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test that submitting an existing JP term updates it instead."""
        existing = MagicMock()
        existing.id = uuid4()
        existing.term_jp = "対戦"
        existing.term_en = "match"
        existing.context = "Old context"
        existing.source = "admin"
        existing.is_active = False

        mock_existing_result = MagicMock()
        mock_existing_result.scalar_one_or_none.return_value = existing

        mock_db.execute = AsyncMock(return_value=mock_existing_result)
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        response = admin_client.post(
            "/api/v1/admin/translations/glossary",
            json={
                "term_jp": "対戦",
                "term_en": "battle",
                "context": "Updated context",
            },
        )

        assert response.status_code == 200
        # Verify the existing record was updated
        assert existing.term_en == "battle"
        assert existing.context == "Updated context"
        assert existing.is_active is True

    @patch(
        "src.routers.translations.settings",
        MagicMock(admin_emails="admin@trainerlab.gg"),
    )
    def test_returns_403_for_non_admin(self, non_admin_client: TestClient) -> None:
        """Test that non-admin users receive 403."""
        response = non_admin_client.post(
            "/api/v1/admin/translations/glossary",
            json={
                "term_jp": "対戦",
                "term_en": "battle",
            },
        )
        assert response.status_code == 403

    @patch(
        "src.routers.translations.settings",
        MagicMock(admin_emails="admin@trainerlab.gg"),
    )
    def test_returns_500_on_database_error(
        self, admin_client: TestClient, mock_db: AsyncMock
    ) -> None:
        """Test that 500 is returned when a database error occurs."""
        from sqlalchemy.exc import SQLAlchemyError

        mock_db.execute = AsyncMock(side_effect=SQLAlchemyError("DB error"))
        mock_db.rollback = AsyncMock()

        response = admin_client.post(
            "/api/v1/admin/translations/glossary",
            json={
                "term_jp": "対戦",
                "term_en": "battle",
            },
        )

        assert response.status_code == 500
        assert "failed" in response.json()["detail"].lower()
