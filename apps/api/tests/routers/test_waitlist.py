from contextlib import asynccontextmanager
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from src.main import app


def test_waitlist_accepts_note_and_is_privacy_safe(monkeypatch) -> None:
    mock_session = AsyncMock()

    @asynccontextmanager
    async def fake_factory():
        yield mock_session

    import src.routers.waitlist as waitlist_router

    monkeypatch.setattr(waitlist_router, "async_session_factory", fake_factory)

    client = TestClient(app)
    resp = client.post(
        "/api/v1/waitlist",
        json={
            "email": "Test@Example.com",
            "note": "please let me in",
            "intent": "both",
            "source": "closed_beta_page",
        },
    )

    assert resp.status_code == 201
    data = resp.json()
    assert data["success"] is True
    assert "on the list" in data["message"].lower()
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()
