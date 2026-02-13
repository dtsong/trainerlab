from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from src.config import Settings, get_settings
from src.db.database import get_db
from src.main import app
from src.models.meta_snapshot import MetaSnapshot


class TestOpsTPCIReadiness:
    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def client(self, mock_db: AsyncMock) -> TestClient:
        async def override_get_db():
            yield mock_db

        async def override_get_settings() -> Settings:
            return Settings(readiness_alert_token="test-readiness-token")

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_settings] = override_get_settings
        yield TestClient(app)
        app.dependency_overrides.clear()

    def test_requires_auth_header(self, client: TestClient) -> None:
        response = client.get("/api/v1/ops/readiness/tpci")

        assert response.status_code == 401
        assert response.json()["detail"] == "Authorization header required"

    def test_rejects_invalid_token(self, client: TestClient) -> None:
        response = client.get(
            "/api/v1/ops/readiness/tpci",
            headers={"Authorization": "Bearer wrong-token"},
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid or expired token"

    def test_reports_thresholds_and_deadline(
        self, client: TestClient, mock_db: AsyncMock
    ) -> None:
        major_end = date(2026, 2, 9)  # Monday -> Tuesday deadline (2026-02-10)
        snapshot = MagicMock(spec=MetaSnapshot)
        snapshot.snapshot_date = date(2026, 2, 10)
        snapshot.sample_size = 12
        mock_db.scalar.side_effect = [major_end, snapshot]

        with pytest.MonkeyPatch.context() as mp:
            import src.routers.ops as ops_router

            class _DT(datetime):
                @classmethod
                def now(cls, tz=None):
                    return datetime(2026, 2, 10, tzinfo=UTC)

            mp.setattr(ops_router, "datetime", _DT)
            response = client.get(
                "/api/v1/ops/readiness/tpci",
                headers={"Authorization": "Bearer test-readiness-token"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pass"
        assert data["latest_major_end_date"] == "2026-02-09"
        assert data["deadline_date"] == "2026-02-10"
        assert data["snapshot_date"] == "2026-02-10"
        assert data["sample_size"] == 12
        assert data["meets_partial_threshold"] is True
        assert data["meets_fresh_threshold"] is False
        assert data["deadline_missed"] is False
