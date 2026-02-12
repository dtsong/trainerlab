from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from src.db.database import get_db
from src.dependencies.admin import require_admin
from src.main import app
from src.models.meta_snapshot import MetaSnapshot
from src.models.user import User


class TestAdminTPCIReadiness:
    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def client(self, mock_db: AsyncMock) -> TestClient:
        async def override_get_db():
            yield mock_db

        async def override_require_admin():
            u = MagicMock(spec=User)
            u.email = "admin@trainerlab.io"
            return u

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[require_admin] = override_require_admin
        yield TestClient(app)
        app.dependency_overrides.clear()

    def test_returns_fail_when_no_major_context_and_low_sample(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        mock_db.scalar.side_effect = [None, None]
        res = client.get("/api/v1/admin/readiness/tpci")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "fail"
        assert data["latest_major_end_date"] is None

    def test_passes_before_deadline_with_partial_sample(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        major_end = date(2026, 2, 9)  # Monday -> deadline Tuesday 2026-02-10
        snapshot = MagicMock(spec=MetaSnapshot)
        snapshot.snapshot_date = date(2026, 2, 10)
        snapshot.sample_size = 8

        mock_db.scalar.side_effect = [major_end, snapshot]

        with pytest.MonkeyPatch.context() as mp:
            import src.routers.admin as admin_router

            class _DT(datetime):
                @classmethod
                def now(cls, tz=None):
                    return datetime(2026, 2, 10, tzinfo=UTC)

            mp.setattr(admin_router, "datetime", _DT)
            res = client.get("/api/v1/admin/readiness/tpci")

        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "pass"
        assert data["meets_partial_threshold"] is True
        assert data["meets_fresh_threshold"] is False

    def test_fails_after_deadline_without_fresh_sample(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        major_end = date(2026, 2, 9)
        snapshot = MagicMock(spec=MetaSnapshot)
        snapshot.snapshot_date = date(2026, 2, 10)
        snapshot.sample_size = 12
        mock_db.scalar.side_effect = [major_end, snapshot]

        with pytest.MonkeyPatch.context() as mp:
            import src.routers.admin as admin_router

            class _DT(datetime):
                @classmethod
                def now(cls, tz=None):
                    return datetime(2026, 2, 11, tzinfo=UTC)

            mp.setattr(admin_router, "datetime", _DT)
            res = client.get("/api/v1/admin/readiness/tpci")

        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "fail"
        assert data["deadline_missed"] is True
