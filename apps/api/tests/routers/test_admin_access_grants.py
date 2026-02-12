from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.db.database import get_db
from src.dependencies.admin import require_admin
from src.main import app
from src.models.user import User


class TestAdminAccessGrants:
    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        db = AsyncMock()
        # AsyncSession.add is sync in real life.
        # Use MagicMock to avoid coroutine warnings in tests.
        db.add = MagicMock()

        async def refresh_side_effect(obj):
            if getattr(obj, "id", None) is None:
                obj.id = uuid4()
            if getattr(obj, "created_at", None) is None:
                obj.created_at = datetime.now(UTC)
            obj.updated_at = datetime.now(UTC)

        db.refresh.side_effect = refresh_side_effect
        return db

    @pytest.fixture
    def mock_admin_user(self) -> MagicMock:
        user = MagicMock(spec=User)
        user.id = uuid4()
        user.email = "admin@trainerlab.io"
        return user

    @pytest.fixture
    def client(self, mock_db: AsyncMock, mock_admin_user: MagicMock) -> TestClient:
        async def override_get_db():
            yield mock_db

        async def override_require_admin():
            return mock_admin_user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[require_admin] = override_require_admin
        yield TestClient(app)
        app.dependency_overrides.clear()

    def test_grant_beta_creates_pending_invite_when_user_missing(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        # _get_user_by_email -> None
        result_user = MagicMock()
        result_user.scalar_one_or_none.return_value = None
        # _get_access_grant_by_email -> None
        result_grant = MagicMock()
        result_grant.scalar_one_or_none.return_value = None
        mock_db.execute.side_effect = [result_user, result_grant]

        resp = client.post(
            "/api/v1/admin/access-grants/beta/grant",
            json={"email": "friend@example.com", "note": "early tester"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "friend@example.com"
        assert data["is_beta_tester"] is True
        assert data["is_subscriber"] is False
        assert data["has_user"] is False
        assert data["note"] == "early tester"

    def test_grant_subscriber_applies_to_existing_user(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        user = MagicMock(spec=User)
        user.id = uuid4()
        user.email = "friend@example.com"
        user.is_subscriber = False

        result_user = MagicMock()
        result_user.scalar_one_or_none.return_value = user

        result_grant = MagicMock()
        result_grant.scalar_one_or_none.return_value = None

        mock_db.execute.side_effect = [result_user, result_grant]

        resp = client.post(
            "/api/v1/admin/access-grants/subscribers/grant",
            json={"email": "friend@example.com"},
        )

        assert resp.status_code == 200
        assert user.is_subscriber is True
        data = resp.json()
        assert data["email"] == "friend@example.com"
        assert data["is_subscriber"] is True
        assert data["has_user"] is True
