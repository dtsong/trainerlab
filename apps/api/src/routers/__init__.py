"""API routers."""

from src.routers.admin import router as admin_router
from src.routers.api_keys import router as api_keys_router
from src.routers.cards import router as cards_router
from src.routers.decks import router as decks_router
from src.routers.events import router as events_router
from src.routers.evolution import router as evolution_router
from src.routers.exports import router as exports_router
from src.routers.format import router as format_router
from src.routers.health import router as health_router
from src.routers.japan import router as japan_router
from src.routers.lab_notes import router as lab_notes_router
from src.routers.meta import router as meta_router
from src.routers.pipeline import router as pipeline_router
from src.routers.public_api import router as public_api_router
from src.routers.sets import router as sets_router
from src.routers.tournaments import router as tournaments_router
from src.routers.translations import router as translations_router
from src.routers.trips import router as trips_router
from src.routers.users import router as users_router
from src.routers.waitlist import router as waitlist_router
from src.routers.widgets import router as widgets_router

__all__ = [
    "admin_router",
    "api_keys_router",
    "cards_router",
    "decks_router",
    "events_router",
    "evolution_router",
    "exports_router",
    "format_router",
    "health_router",
    "japan_router",
    "lab_notes_router",
    "meta_router",
    "pipeline_router",
    "public_api_router",
    "sets_router",
    "tournaments_router",
    "trips_router",
    "translations_router",
    "users_router",
    "waitlist_router",
    "widgets_router",
]
