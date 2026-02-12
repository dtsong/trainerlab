from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.db.database import get_db
from src.dependencies.admin import require_admin
from src.main import app
from src.models.user import User


class TestAdminSubscribers:
    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        return AsyncMock()

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

    @pytest.fixture
    def mock_user(self) -> MagicMock:
        user = MagicMock(spec=User)
        user.id = uuid4()
        user.email = "user@example.com"
        user.display_name = "User"
        user.is_beta_tester = False
        user.is_creator = False
        user.is_subscriber = False
        user.created_at = datetime.now(UTC)
        user.updated_at = datetime.now(UTC)
        return user

    def test_grant_subscriber_access(
        self, client: TestClient, mock_db: AsyncMock, mock_user: MagicMock
    ) -> None:
        result = MagicMock()
        result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = result

        response = client.post(
            "/api/v1/admin/subscribers/grant",
            json={"email": "user@example.com"},
        )

        assert response.status_code == 200
        assert mock_user.is_subscriber is True
        mock_db.commit.assert_called_once()

        data = response.json()
        assert data["email"] == "user@example.com"
        assert data["is_subscriber"] is True

    def test_revoke_subscriber_access(
        self, client: TestClient, mock_db: AsyncMock, mock_user: MagicMock
    ) -> None:
        mock_user.is_subscriber = True
        result = MagicMock()
        result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = result

        response = client.post(
            "/api/v1/admin/subscribers/revoke",
            json={"email": "user@example.com"},
        )

        assert response.status_code == 200
        assert mock_user.is_subscriber is False
        mock_db.commit.assert_called_once()

        data = response.json()
        assert data["is_subscriber"] is False

    def test_list_subscribers(
        self, client: TestClient, mock_db: AsyncMock, mock_user: MagicMock
    ) -> None:
        mock_user.is_subscriber = True
        result = MagicMock()
        result.scalars.return_value.all.return_value = [mock_user]
        mock_db.execute.return_value = result

        response = client.get("/api/v1/admin/subscribers?active=true")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["email"] == "user@example.com"
        assert data[0]["is_subscriber"] is True
