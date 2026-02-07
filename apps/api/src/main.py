"""FastAPI application entry point."""

import json
import logging
import sys
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from contextvars import ContextVar

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from src.config import get_settings
from src.routers import (
    api_keys_router,
    cards_router,
    decks_router,
    evolution_router,
    exports_router,
    format_router,
    health_router,
    japan_router,
    lab_notes_router,
    meta_router,
    pipeline_router,
    public_api_router,
    sets_router,
    tournaments_router,
    translations_router,
    users_router,
    waitlist_router,
    widgets_router,
)

settings = get_settings()

# Correlation ID for request tracing (async-safe via contextvars)
correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")


class JSONFormatter(logging.Formatter):
    """Structured JSON log formatter for production."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, object] = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": correlation_id_var.get(""),
        }
        if hasattr(record, "pipeline"):
            log_entry["pipeline"] = record.pipeline  # type: ignore[attr-defined]
        if hasattr(record, "run_id"):
            log_entry["run_id"] = record.run_id  # type: ignore[attr-defined]
        return json.dumps(log_entry)


# Configure logging: INFO in production, DEBUG in development.
# Cloud Run captures stdout as structured logs.
if settings.is_production:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    logging.root.handlers = [handler]
    logging.root.setLevel(logging.INFO)
else:
    logging.basicConfig(
        level=logging.DEBUG if settings.debug else logging.INFO,
        stream=sys.stdout,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
# Quiet noisy third-party loggers
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("hpack").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Rate limiter setup
limiter = Limiter(key_func=get_remote_address)


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """Generate/propagate X-Correlation-ID for request tracing."""

    async def dispatch(self, request: Request, call_next) -> Response:
        cid = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        correlation_id_var.set(cid)
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = cid
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        if not settings.is_development:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        return response


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Handle application startup and shutdown."""
    # Startup
    if settings.nextauth_secret:
        logger.info("NextAuth.js JWT authentication enabled")
    else:
        logger.warning(
            "NEXTAUTH_SECRET not configured - API endpoints requiring auth will fail"
        )
    yield
    # Shutdown


app = FastAPI(
    title="TrainerLab API",
    description="Competitive intelligence platform for Pokemon TCG",
    version="0.0.1",
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    lifespan=lifespan,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

# Correlation ID middleware (outermost — runs first)
app.add_middleware(CorrelationIDMiddleware)  # type: ignore[arg-type]

# Security headers middleware
app.add_middleware(SecurityHeadersMiddleware)  # type: ignore[arg-type]

# CORS middleware
app.add_middleware(
    CORSMiddleware,  # type: ignore[arg-type]
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Include routers
app.include_router(api_keys_router)
app.include_router(cards_router)
app.include_router(decks_router)
app.include_router(evolution_router)
app.include_router(exports_router)
app.include_router(format_router)
app.include_router(health_router)
app.include_router(japan_router)
app.include_router(lab_notes_router)
app.include_router(meta_router)
app.include_router(pipeline_router)
app.include_router(public_api_router)
app.include_router(sets_router)
app.include_router(tournaments_router)
app.include_router(translations_router)
app.include_router(users_router)
app.include_router(waitlist_router)
app.include_router(widgets_router)
