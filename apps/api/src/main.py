"""FastAPI application entry point."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import get_settings
from src.core.firebase import init_firebase
from src.routers import (
    cards_router,
    decks_router,
    health_router,
    meta_router,
    pipeline_router,
    sets_router,
    tournaments_router,
    users_router,
)

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Handle application startup and shutdown."""
    # Startup
    firebase_app = init_firebase()
    if firebase_app:
        logger.info("Firebase authentication enabled")
    else:
        logger.warning(
            "Firebase authentication disabled - API endpoints requiring auth will fail"
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

# CORS middleware
app.add_middleware(
    CORSMiddleware,  # type: ignore[arg-type]
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(cards_router)
app.include_router(decks_router)
app.include_router(health_router)
app.include_router(meta_router)
app.include_router(pipeline_router)
app.include_router(sets_router)
app.include_router(tournaments_router)
app.include_router(users_router)
