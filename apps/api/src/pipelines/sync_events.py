"""Event synchronization pipeline.

Syncs upcoming Pokemon TCG events from RK9.gg and the official
Pokemon events site into the tournaments table with lifecycle
status tracking.
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import timedelta
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.clients.pokemon_events import (
    PokemonEvent,
    PokemonEventsClient,
    PokemonEventsError,
)
from src.clients.rk9 import RK9Client, RK9Error, RK9Event
from src.db.database import async_session_factory
from src.models.tournament import Tournament

logger = logging.getLogger(__name__)


@dataclass
class SyncEventsResult:
    """Result of an event sync operation."""

    events_fetched: int = 0
    events_created: int = 0
    events_updated: int = 0
    events_skipped: int = 0
    events_deduped: int = 0
    sources_merged: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return len(self.errors) == 0


def _rk9_event_to_tournament_data(event: RK9Event) -> dict:
    """Convert an RK9Event to tournament column data.

    Args:
        event: RK9Event from the scraper.

    Returns:
        Dict of column values for Tournament model.
    """
    return {
        "name": event.name,
        "date": event.date,
        "status": _normalize_status(event.status),
        "region": _infer_region_from_country(event.country),
        "country": event.country,
        "city": event.city,
        "venue_name": event.venue,
        "format": "standard",
        "best_of": 3,
        "registration_url": event.registration_url,
        "source": "rk9",
        "source_url": event.source_url,
        "event_source": "rk9",
    }


def _pokemon_event_to_tournament_data(
    event: PokemonEvent,
) -> dict:
    """Convert a PokemonEvent to tournament column data.

    Args:
        event: PokemonEvent from the scraper.

    Returns:
        Dict of column values for Tournament model.
    """
    return {
        "name": event.name,
        "date": event.date,
        "status": "announced",
        "region": event.region or "NA",
        "country": event.country,
        "city": event.city,
        "venue_name": event.venue,
        "format": "standard",
        "best_of": 3,
        "tier": event.tier,
        "registration_url": event.registration_url,
        "source": "pokemon.com",
        "source_url": event.source_url,
        "event_source": "pokemon.com",
    }


def _normalize_status(status: str) -> str:
    """Normalize event status to valid tournament status.

    Args:
        status: Raw status string from scraper.

    Returns:
        Valid tournament status string.
    """
    mapping = {
        "upcoming": "announced",
        "registration_open": "registration_open",
        "registration_closed": "registration_closed",
        "in_progress": "active",
        "completed": "completed",
    }
    return mapping.get(status, "announced")


def _infer_region_from_country(
    country: str | None,
) -> str:
    """Infer Pokemon TCG region from country code/name.

    Args:
        country: Country name or code.

    Returns:
        Region code (NA, EU, JP, LATAM, OCE).
    """
    if not country:
        return "NA"

    country_lower = country.lower().strip()

    na = {"us", "usa", "united states", "canada", "ca"}
    eu = {
        "uk",
        "gb",
        "united kingdom",
        "germany",
        "de",
        "france",
        "fr",
        "italy",
        "it",
        "spain",
        "es",
        "netherlands",
        "nl",
        "belgium",
        "be",
        "austria",
        "at",
        "switzerland",
        "ch",
        "poland",
        "pl",
        "sweden",
        "se",
        "norway",
        "no",
        "denmark",
        "dk",
        "finland",
        "fi",
        "portugal",
        "pt",
        "ireland",
        "ie",
    }
    latam = {
        "brazil",
        "br",
        "mexico",
        "mx",
        "argentina",
        "ar",
        "chile",
        "cl",
        "colombia",
        "co",
        "peru",
        "pe",
    }
    oce = {"australia", "au", "new zealand", "nz"}
    jp = {"japan", "jp"}

    if country_lower in na:
        return "NA"
    if country_lower in eu:
        return "EU"
    if country_lower in latam:
        return "LATAM"
    if country_lower in oce:
        return "OCE"
    if country_lower in jp:
        return "JP"
    return "NA"


# Valid status transitions (from -> allowed to)
_STATUS_TRANSITIONS: dict[str, set[str]] = {
    "announced": {
        "registration_open",
        "registration_closed",
        "active",
        "completed",
    },
    "registration_open": {
        "registration_closed",
        "active",
        "completed",
    },
    "registration_closed": {"active", "completed"},
    "active": {"completed"},
    "completed": set(),  # terminal state
}

_EVENT_NAME_STOPWORDS = {
    "pokemon",
    "play",
    "tcg",
    "tournament",
    "championship",
    "championships",
    "event",
    "open",
}

_TOKEN_ALIASES = {
    "regionals": "regional",
    "internationals": "international",
    "world": "worlds",
    "worldchampionship": "worlds",
    "naic": "northamerica",
    "euic": "europe",
    "laic": "latinamerica",
    "ocic": "oceania",
}


def _is_valid_transition(current: str, new: str) -> bool:
    """Check if a status transition is valid.

    Args:
        current: Current status.
        new: Proposed new status.

    Returns:
        True if the transition is allowed.
    """
    return new in _STATUS_TRANSITIONS.get(current, set())


def _normalize_text(value: str | None) -> str:
    """Normalize free text for robust matching."""
    if not value:
        return ""
    lowered = value.lower()
    lowered = lowered.replace("&", " and ")
    lowered = re.sub(r"[^a-z0-9\s]", " ", lowered)
    lowered = re.sub(r"\s+", " ", lowered).strip()
    return lowered


def _name_tokens(value: str | None) -> set[str]:
    """Tokenize event name while removing high-noise words."""
    normalized = _normalize_text(value)
    if not normalized:
        return set()

    tokens: set[str] = set()
    for token in normalized.split(" "):
        if not token:
            continue
        if re.fullmatch(r"20\d{2}", token):
            continue
        token = _TOKEN_ALIASES.get(token, token)
        if token in _EVENT_NAME_STOPWORDS:
            continue
        tokens.add(token)
    return tokens


def _name_similarity(left: str | None, right: str | None) -> float:
    """Compute simple Jaccard similarity over normalized tokens."""
    left_tokens = _name_tokens(left)
    right_tokens = _name_tokens(right)
    if not left_tokens or not right_tokens:
        return 0.0
    intersection = left_tokens.intersection(right_tokens)
    union = left_tokens.union(right_tokens)
    return len(intersection) / len(union)


def _merge_csv(
    existing: str | None, incoming: str | None, max_len: int = 100
) -> str | None:
    """Merge comma-separated source markers into a stable string."""
    tokens: list[str] = []
    for raw in (existing, incoming):
        if not raw:
            continue
        for token in raw.split(","):
            token = token.strip()
            if token and token not in tokens:
                tokens.append(token)

    if not tokens:
        return None

    merged = ",".join(tokens)
    if len(merged) <= max_len:
        return merged
    return "multi"


async def _find_canonical_event_match(
    session: AsyncSession,
    data: dict,
) -> Tournament | None:
    """Find likely existing event when source URLs differ across providers."""
    event_date = data.get("date")
    region = data.get("region")
    if event_date is None or region is None:
        return None

    stmt = (
        select(Tournament)
        .where(Tournament.region == region)
        .where(Tournament.date >= event_date - timedelta(days=2))
        .where(Tournament.date <= event_date + timedelta(days=2))
        .where(Tournament.best_of == data.get("best_of", 3))
        .where(Tournament.format == data.get("format", "standard"))
    )
    candidates = (await session.execute(stmt)).scalars().all()
    if not candidates:
        return None

    incoming_city = _normalize_text(data.get("city"))
    incoming_country = _normalize_text(data.get("country"))
    incoming_tier = data.get("tier")

    best_candidate: Tournament | None = None
    best_score = 0.0

    for candidate in candidates:
        score = 0.0

        similarity = _name_similarity(candidate.name, data.get("name"))
        score += similarity * 4

        candidate_city = _normalize_text(candidate.city)
        if incoming_city and candidate_city and incoming_city == candidate_city:
            score += 4

        candidate_country = _normalize_text(candidate.country)
        if (
            incoming_country
            and candidate_country
            and incoming_country == candidate_country
        ):
            score += 1

        if incoming_tier and candidate.tier and incoming_tier == candidate.tier:
            score += 2

        if score > best_score:
            best_score = score
            best_candidate = candidate

    return best_candidate if best_score >= 4.5 else None


async def _upsert_event(
    session: AsyncSession,
    data: dict,
    result: SyncEventsResult,
) -> None:
    """Upsert a single event into the tournaments table.

    Matches by source_url to avoid duplicates. Updates status
    and other fields if the event already exists.

    Args:
        session: Database session.
        data: Tournament column data dict.
        result: Result tracker to update counters.
    """
    source_url = data.get("source_url")
    if not source_url:
        logger.debug(
            "Skipping event with no source_url: %s",
            data.get("name", "<unknown>"),
        )
        result.events_skipped += 1
        return

    # Check for existing tournament by source_url
    stmt = select(Tournament).where(Tournament.source_url == source_url)
    existing = (await session.execute(stmt)).scalar_one_or_none()

    dedupe_match = False
    if not existing:
        existing = await _find_canonical_event_match(session, data)
        dedupe_match = existing is not None
        if dedupe_match:
            result.events_deduped += 1

    if existing:
        # Update fields that may have changed
        updated = False
        new_status = data.get("status", "announced")

        # Only transition status forward
        if new_status != existing.status:
            if _is_valid_transition(existing.status, new_status):
                existing.status = new_status
                updated = True
            else:
                logger.debug(
                    "Rejected status transition %s -> %s for %s",
                    existing.status,
                    new_status,
                    source_url,
                )

        # Update registration URL if newly available
        if data.get("registration_url") and not existing.registration_url:
            existing.registration_url = data["registration_url"]
            updated = True

        # Update location if newly available
        if data.get("city") and not existing.city:
            existing.city = data["city"]
            updated = True
        if data.get("venue_name") and not existing.venue_name:
            existing.venue_name = data["venue_name"]
            updated = True
        if data.get("country") and not existing.country:
            existing.country = data["country"]
            updated = True
        if data.get("tier") and not existing.tier:
            existing.tier = data["tier"]
            updated = True

        merged_source = _merge_csv(existing.source, data.get("source"))
        if merged_source and merged_source != existing.source:
            existing.source = merged_source
            updated = True
            result.sources_merged += 1

        merged_event_source = _merge_csv(
            existing.event_source,
            data.get("event_source"),
            max_len=20,
        )
        if merged_event_source and merged_event_source != existing.event_source:
            existing.event_source = merged_event_source
            updated = True
            result.sources_merged += 1

        if dedupe_match:
            logger.info(
                "Deduped cross-source event '%s' into existing tournament id=%s",
                data.get("name", "<unknown>"),
                existing.id,
            )

        if updated:
            result.events_updated += 1
        else:
            result.events_skipped += 1
    else:
        # Create new tournament
        tournament = Tournament(
            id=uuid4(),
            **data,
        )
        session.add(tournament)
        result.events_created += 1


async def sync_events(
    dry_run: bool = False,
) -> SyncEventsResult:
    """Sync upcoming events from all sources.

    Fetches events from RK9.gg and Pokemon events site,
    then upserts them into the tournaments table.

    Args:
        dry_run: If True, don't persist changes.

    Returns:
        SyncEventsResult with sync statistics.
    """
    result = SyncEventsResult()
    run_id = str(uuid4())
    logger.info("Starting event sync (run_id=%s, dry_run=%s)", run_id, dry_run)

    # Fetch from RK9
    rk9_events: list[RK9Event] = []
    try:
        async with RK9Client() as client:
            rk9_events = await client.fetch_upcoming_events()
        logger.info("Fetched %d events from RK9", len(rk9_events))
    except RK9Error as e:
        error_msg = f"RK9 fetch failed: {e}"
        logger.warning(error_msg)
        result.errors.append(error_msg)

    # Fetch from Pokemon Events
    pokemon_events: list[PokemonEvent] = []
    try:
        async with PokemonEventsClient() as client:
            pokemon_events = await client.fetch_all_events()
        logger.info(
            "Fetched %d events from Pokemon Events",
            len(pokemon_events),
        )
    except PokemonEventsError as e:
        error_msg = f"Pokemon Events fetch failed: {e}"
        logger.warning(error_msg)
        result.errors.append(error_msg)

    result.events_fetched = len(rk9_events) + len(pokemon_events)

    if dry_run:
        logger.info(
            "Dry run: would upsert %d events",
            result.events_fetched,
        )
        return result

    # Upsert into database
    async with async_session_factory() as session:
        # Process RK9 events
        for event in rk9_events:
            try:
                data = _rk9_event_to_tournament_data(event)
                await _upsert_event(session, data, result)
            except (SQLAlchemyError, ValueError, KeyError) as e:
                error_msg = f"Error upserting RK9 event '{event.name}': {e}"
                logger.warning(error_msg, exc_info=True)
                result.errors.append(error_msg)

        # Process Pokemon Events
        for event in pokemon_events:
            try:
                data = _pokemon_event_to_tournament_data(event)
                await _upsert_event(session, data, result)
            except (SQLAlchemyError, ValueError, KeyError) as e:
                error_msg = f"Error upserting Pokemon event '{event.name}': {e}"
                logger.warning(error_msg, exc_info=True)
                result.errors.append(error_msg)

        await session.commit()

    logger.info(
        "Event sync complete (run_id=%s): "
        "fetched=%d, created=%d, updated=%d, skipped=%d, deduped=%d, "
        "sources_merged=%d, errors=%d",
        run_id,
        result.events_fetched,
        result.events_created,
        result.events_updated,
        result.events_skipped,
        result.events_deduped,
        result.sources_merged,
        len(result.errors),
    )

    return result
