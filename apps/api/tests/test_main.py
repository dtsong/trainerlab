"""Tests for FastAPI application entry point."""

import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app


class TestAppConfiguration:
    """Tests for FastAPI app configuration."""

    def test_app_title(self) -> None:
        """Test that the app title is set correctly."""
        assert app.title == "TrainerLab API"

    def test_app_description(self) -> None:
        """Test that the app description is set correctly."""
        assert app.description == "Competitive intelligence platform for Pokemon TCG"

    def test_app_version(self) -> None:
        """Test that the app version is set correctly."""
        assert app.version == "0.0.1"


class TestRouterRegistration:
    """Tests for router registration on the app."""

    @pytest.fixture
    def all_route_paths(self) -> set[str]:
        """Collect all registered route paths."""
        return {route.path for route in app.routes}

    def test_health_router_registered(self, all_route_paths: set[str]) -> None:
        """Test that the health router is mounted."""
        assert "/api/v1/health" in all_route_paths

    def test_cards_router_registered(self, all_route_paths: set[str]) -> None:
        """Test that the cards router is mounted."""
        assert any("/api/v1/cards" in path for path in all_route_paths)

    def test_decks_router_registered(self, all_route_paths: set[str]) -> None:
        """Test that the decks router is mounted."""
        assert any("/api/v1/decks" in path for path in all_route_paths)

    def test_users_router_registered(self, all_route_paths: set[str]) -> None:
        """Test that the users router is mounted."""
        assert any("/api/v1/users" in path for path in all_route_paths)

    def test_tournaments_router_registered(self, all_route_paths: set[str]) -> None:
        """Test that the tournaments router is mounted."""
        assert any("/api/v1/tournaments" in path for path in all_route_paths)

    def test_meta_router_registered(self, all_route_paths: set[str]) -> None:
        """Test that the meta router is mounted."""
        assert any("/api/v1/meta" in path for path in all_route_paths)

    def test_sets_router_registered(self, all_route_paths: set[str]) -> None:
        """Test that the sets router is mounted."""
        assert any("/api/v1/sets" in path for path in all_route_paths)

    def test_waitlist_router_registered(self, all_route_paths: set[str]) -> None:
        """Test that the waitlist router is mounted."""
        assert any("/api/v1/waitlist" in path for path in all_route_paths)

    def test_pipeline_router_registered(self, all_route_paths: set[str]) -> None:
        """Test that the pipeline router is mounted."""
        assert any("/api/v1/pipeline" in path for path in all_route_paths)

    def test_widgets_router_registered(self, all_route_paths: set[str]) -> None:
        """Test that the widgets router is mounted."""
        assert any("/api/v1/widgets" in path for path in all_route_paths)


class TestHealthEndpoint:
    """Tests for the health check endpoint via TestClient."""

    @pytest.mark.asyncio
    async def test_health_check_returns_ok(self) -> None:
        """Test that /api/v1/health returns status ok."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "0.0.1"

    @pytest.mark.asyncio
    async def test_health_check_has_security_headers(self) -> None:
        """Test that the health response includes security headers."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/api/v1/health")

        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["X-XSS-Protection"] == "1; mode=block"


class TestSecurityHeadersMiddleware:
    """Tests for the SecurityHeadersMiddleware."""

    @pytest.mark.asyncio
    async def test_nosniff_header_present(self) -> None:
        """Test X-Content-Type-Options header is set."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/api/v1/health")

        assert response.headers["X-Content-Type-Options"] == "nosniff"

    @pytest.mark.asyncio
    async def test_frame_options_deny(self) -> None:
        """Test X-Frame-Options header is set to DENY."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/api/v1/health")

        assert response.headers["X-Frame-Options"] == "DENY"

    @pytest.mark.asyncio
    async def test_xss_protection_header(self) -> None:
        """Test X-XSS-Protection header is set."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/api/v1/health")

        assert response.headers["X-XSS-Protection"] == "1; mode=block"


class TestCORSMiddleware:
    """Tests for CORS middleware configuration."""

    def test_cors_middleware_is_registered(self) -> None:
        """Test that CORSMiddleware is registered on the app."""
        # CORSMiddleware is registered via app.add_middleware
        # Check that it's in the middleware stack
        has_cors = any("CORSMiddleware" in str(m) for m in app.user_middleware)
        assert has_cors, "CORSMiddleware should be registered"

    @pytest.mark.asyncio
    async def test_cors_preflight_request(self) -> None:
        """Test that CORS preflight requests are handled."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.options(
                "/api/v1/health",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "GET",
                    "Access-Control-Request-Headers": "Authorization",
                },
            )

        # CORS should respond to preflight
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
