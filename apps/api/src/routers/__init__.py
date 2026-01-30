"""API routers."""

from src.routers.cards import router as cards_router
from src.routers.decks import router as decks_router
from src.routers.health import router as health_router
from src.routers.sets import router as sets_router

__all__ = ["cards_router", "decks_router", "health_router", "sets_router"]
