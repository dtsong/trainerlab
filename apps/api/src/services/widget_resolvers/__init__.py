"""Widget resolver registry with Protocol-based resolvers."""

from typing import Any, Protocol

from sqlalchemy.ext.asyncio import AsyncSession


class WidgetResolver(Protocol):
    """Protocol for widget data resolvers."""

    async def resolve(
        self, session: AsyncSession, config: dict[str, Any]
    ) -> dict[str, Any]:
        """Resolve widget data from config.

        Args:
            session: Database session
            config: Widget configuration

        Returns:
            Resolved data for widget rendering
        """
        ...


_RESOLVERS: dict[str, type[WidgetResolver]] = {}


def register_resolver(widget_type: str):
    """Decorator to register a widget resolver.

    Args:
        widget_type: The widget type string (e.g., "meta_snapshot")

    Returns:
        Decorator function
    """

    def decorator(cls: type[WidgetResolver]) -> type[WidgetResolver]:
        _RESOLVERS[widget_type] = cls
        return cls

    return decorator


def get_resolver(widget_type: str) -> type[WidgetResolver] | None:
    """Get a resolver class by widget type.

    Args:
        widget_type: The widget type string

    Returns:
        Resolver class or None if not found
    """
    return _RESOLVERS.get(widget_type)


def get_all_widget_types() -> list[str]:
    """Get all registered widget types.

    Returns:
        List of registered widget type strings
    """
    return list(_RESOLVERS.keys())


# Import all resolvers to trigger registration
# ruff: noqa: E402
from src.services.widget_resolvers.archetype_card import ArchetypeCardResolver
from src.services.widget_resolvers.deck_cost import DeckCostResolver
from src.services.widget_resolvers.evolution_timeline import EvolutionTimelineResolver
from src.services.widget_resolvers.jp_comparison import JPComparisonResolver
from src.services.widget_resolvers.meta_pie import MetaPieResolver
from src.services.widget_resolvers.meta_snapshot import MetaSnapshotResolver
from src.services.widget_resolvers.meta_trend import MetaTrendResolver
from src.services.widget_resolvers.prediction import PredictionResolver
from src.services.widget_resolvers.tournament_result import TournamentResultResolver

__all__ = [
    "WidgetResolver",
    "register_resolver",
    "get_resolver",
    "get_all_widget_types",
    "ArchetypeCardResolver",
    "DeckCostResolver",
    "EvolutionTimelineResolver",
    "JPComparisonResolver",
    "MetaPieResolver",
    "MetaSnapshotResolver",
    "MetaTrendResolver",
    "PredictionResolver",
    "TournamentResultResolver",
]
