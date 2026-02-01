"""API routers."""

from src.routers.cards import router as cards_router
from src.routers.decks import router as decks_router
from src.routers.health import router as health_router
from src.routers.meta import router as meta_router
from src.routers.sets import router as sets_router
from src.routers.tournaments import router as tournaments_router
from src.routers.users import router as users_router

__all__ = [
    "cards_router",
    "decks_router",
    "health_router",
    "meta_router",
    "sets_router",
    "tournaments_router",
    "users_router",
]
