"""Tests for the sync_events pipeline."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.clients.pokemon_events import PokemonEvent, PokemonEventsError
from src.clients.rk9 import RK9Error, RK9Event
from src.pipelines.sync_events import (
    SyncEventsResult,
    _infer_region_from_country,
    _is_valid_transition,
    _normalize_status,
    _pokemon_event_to_tournament_data,
    _rk9_event_to_tournament_data,
    _upsert_event,
    sync_events,
)

# ── Helper factories ────────────────────────────────────────────────


def _make_rk9_event(**overrides) -> RK9Event:
    defaults = {
        "name": "Charlotte Regional",
        "date": date(2026, 3, 15),
        "city": "Charlotte",
        "country": "US",
        "venue": "Charlotte Convention Center",
        "status": "upcoming",
        "source_url": "https://rk9.gg/event/charlotte-2026",
    }
    defaults.update(overrides)
    return RK9Event(**defaults)


def _make_pokemon_event(**overrides) -> PokemonEvent:
    defaults = {
        "name": "NAIC 2026",
        "date": date(2026, 6, 20),
        "city": "Columbus",
        "country": "US",
        "region": "NA",
        "venue": "Greater Columbus Convention Center",
        "source_url": "https://pokemon.com/events/naic-2026",
        "tier": "international",
    }
    defaults.update(overrides)
    return PokemonEvent(**defaults)


def _make_mock_tournament(
    source_url: str = "https://rk9.gg/event/charlotte-2026",
    status: str = "announced",
    registration_url: str | None = None,
    name: str = "Charlotte Regional",
    event_date: date = date(2026, 3, 15),
    region: str = "NA",
    format_name: str = "standard",
    best_of: int = 3,
    city: str | None = "Charlotte",
    venue_name: str | None = None,
    country: str | None = "US",
    source: str | None = "rk9",
    event_source: str | None = "rk9",
    tier: str | None = None,
) -> MagicMock:
    t = MagicMock()
    t.source_url = source_url
    t.status = status
    t.registration_url = registration_url
    t.name = name
    t.date = event_date
    t.region = region
    t.format = format_name
    t.best_of = best_of
    t.city = city
    t.venue_name = venue_name
    t.country = country
    t.source = source
    t.event_source = event_source
    t.tier = tier
    t.id = "t-1"
    return t


# ── Status transition tests ─────────────────────────────────────────


class TestStatusTransitions:
    """Test forward-only status transitions."""

    def test_announced_to_registration_open(self) -> None:
        assert _is_valid_transition("announced", "registration_open") is True

    def test_announced_to_active(self) -> None:
        assert _is_valid_transition("announced", "active") is True

    def test_announced_to_completed(self) -> None:
        assert _is_valid_transition("announced", "completed") is True

    def test_registration_open_to_active(self) -> None:
        assert _is_valid_transition("registration_open", "active") is True

    def test_registration_open_to_completed(self) -> None:
        assert _is_valid_transition("registration_open", "completed") is True

    def test_active_to_completed(self) -> None:
        assert _is_valid_transition("active", "completed") is True

    def test_reject_backward_completed_to_active(self) -> None:
        assert _is_valid_transition("completed", "active") is False

    def test_reject_backward_active_to_announced(self) -> None:
        assert _is_valid_transition("active", "announced") is False

    def test_reject_backward_registration_open_to_announced(self) -> None:
        assert _is_valid_transition("registration_open", "announced") is False

    def test_completed_is_terminal(self) -> None:
        for status in [
            "announced",
            "registration_open",
            "registration_closed",
            "active",
        ]:
            assert _is_valid_transition("completed", status) is False

    def test_same_status_not_valid(self) -> None:
        assert _is_valid_transition("announced", "announced") is False

    def test_unknown_status_not_valid(self) -> None:
        assert _is_valid_transition("unknown", "announced") is False


# ── Status normalization tests ───────────────────────────────────────


class TestNormalizeStatus:
    """Test status string normalization."""

    def test_upcoming_maps_to_announced(self) -> None:
        assert _normalize_status("upcoming") == "announced"

    def test_registration_open_passes_through(self) -> None:
        assert _normalize_status("registration_open") == "registration_open"

    def test_in_progress_maps_to_active(self) -> None:
        assert _normalize_status("in_progress") == "active"

    def test_completed_passes_through(self) -> None:
        assert _normalize_status("completed") == "completed"

    def test_unknown_defaults_to_announced(self) -> None:
        assert _normalize_status("some_random_status") == "announced"


# ── Region inference tests ───────────────────────────────────────────


class TestInferRegion:
    """Test country-to-region mapping."""

    @pytest.mark.parametrize(
        ("country", "expected"),
        [
            ("US", "NA"),
            ("usa", "NA"),
            ("United States", "NA"),
            ("Canada", "NA"),
            ("UK", "EU"),
            ("Germany", "EU"),
            ("France", "EU"),
            ("Brazil", "LATAM"),
            ("Mexico", "LATAM"),
            ("Australia", "OCE"),
            ("New Zealand", "OCE"),
            ("Japan", "JP"),
            ("jp", "JP"),
        ],
    )
    def test_known_countries(self, country: str, expected: str) -> None:
        assert _infer_region_from_country(country) == expected

    def test_none_defaults_to_na(self) -> None:
        assert _infer_region_from_country(None) == "NA"

    def test_unknown_country_defaults_to_na(self) -> None:
        assert _infer_region_from_country("Narnia") == "NA"

    def test_case_insensitive(self) -> None:
        assert _infer_region_from_country("GERMANY") == "EU"
        assert _infer_region_from_country("japan") == "JP"

    def test_whitespace_stripped(self) -> None:
        assert _infer_region_from_country("  US  ") == "NA"


# ── Data conversion tests ───────────────────────────────────────────


class TestRK9EventConversion:
    """Test RK9Event to tournament data conversion."""

    def test_basic_conversion(self) -> None:
        event = _make_rk9_event()
        data = _rk9_event_to_tournament_data(event)

        assert data["name"] == "Charlotte Regional"
        assert data["date"] == date(2026, 3, 15)
        assert data["status"] == "announced"  # "upcoming" normalized
        assert data["region"] == "NA"
        assert data["country"] == "US"
        assert data["city"] == "Charlotte"
        assert data["venue_name"] == "Charlotte Convention Center"
        assert data["format"] == "standard"
        assert data["best_of"] == 3
        assert data["source"] == "rk9"
        assert data["event_source"] == "rk9"

    def test_registration_open_status(self) -> None:
        event = _make_rk9_event(status="registration_open")
        data = _rk9_event_to_tournament_data(event)
        assert data["status"] == "registration_open"


class TestPokemonEventConversion:
    """Test PokemonEvent to tournament data conversion."""

    def test_basic_conversion(self) -> None:
        event = _make_pokemon_event()
        data = _pokemon_event_to_tournament_data(event)

        assert data["name"] == "NAIC 2026"
        assert data["status"] == "announced"
        assert data["region"] == "NA"
        assert data["tier"] == "international"
        assert data["source"] == "pokemon.com"
        assert data["event_source"] == "pokemon.com"

    def test_missing_region_defaults_to_na(self) -> None:
        event = _make_pokemon_event(region=None)
        data = _pokemon_event_to_tournament_data(event)
        assert data["region"] == "NA"


# ── Upsert logic tests ──────────────────────────────────────────────


class TestUpsertEvent:
    """Test event upsert logic (create vs. update)."""

    @pytest.mark.asyncio
    async def test_creates_new_tournament(self) -> None:
        """Should create a new tournament when source_url not found."""
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute.return_value = mock_result

        result = SyncEventsResult()
        data = _rk9_event_to_tournament_data(_make_rk9_event())

        await _upsert_event(session, data, result)

        assert result.events_created == 1
        assert result.events_updated == 0
        assert result.events_skipped == 0
        session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_updates_existing_with_status_forward(self) -> None:
        """Should update status when transitioning forward."""
        existing = _make_mock_tournament(status="announced")
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing
        session.execute.return_value = mock_result

        result = SyncEventsResult()
        data = _rk9_event_to_tournament_data(
            _make_rk9_event(status="registration_open")
        )

        await _upsert_event(session, data, result)

        assert result.events_updated == 1
        assert existing.status == "registration_open"

    @pytest.mark.asyncio
    async def test_rejects_backward_status_transition(self) -> None:
        """Should not update status backwards."""
        existing = _make_mock_tournament(
            status="active",
            venue_name="Convention Center",
            registration_url="https://rk9.gg/register",
            tier="regional",
        )
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing
        session.execute.return_value = mock_result

        result = SyncEventsResult()
        data = _rk9_event_to_tournament_data(_make_rk9_event())
        data["status"] = "announced"

        await _upsert_event(session, data, result)

        assert result.events_skipped == 1
        assert existing.status == "active"  # unchanged

    @pytest.mark.asyncio
    async def test_updates_registration_url_when_missing(self) -> None:
        """Should fill in registration_url if existing has none."""
        existing = _make_mock_tournament(registration_url=None)
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing
        session.execute.return_value = mock_result

        result = SyncEventsResult()
        data = _rk9_event_to_tournament_data(
            _make_rk9_event(registration_url="https://rk9.gg/register/charlotte")
        )

        await _upsert_event(session, data, result)

        assert result.events_updated == 1
        assert existing.registration_url == "https://rk9.gg/register/charlotte"

    @pytest.mark.asyncio
    async def test_skips_when_no_source_url(self) -> None:
        """Should skip events with no source_url."""
        session = AsyncMock()
        result = SyncEventsResult()

        await _upsert_event(session, {"name": "No URL"}, result)

        assert result.events_skipped == 1
        session.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_fills_venue_when_missing(self) -> None:
        """Should update venue_name if existing has none."""
        existing = _make_mock_tournament(venue_name=None)
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing
        session.execute.return_value = mock_result

        result = SyncEventsResult()
        data = _rk9_event_to_tournament_data(_make_rk9_event())

        await _upsert_event(session, data, result)

        assert result.events_updated == 1
        assert existing.venue_name == "Charlotte Convention Center"

    @pytest.mark.asyncio
    async def test_fills_tier_when_missing(self) -> None:
        """Should update tier if existing has none."""
        existing = _make_mock_tournament(tier=None)
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing
        session.execute.return_value = mock_result

        result = SyncEventsResult()
        data = _pokemon_event_to_tournament_data(_make_pokemon_event())

        await _upsert_event(session, data, result)

        assert result.events_updated == 1
        assert existing.tier == "international"

    @pytest.mark.asyncio
    async def test_dedupes_canonical_match_when_source_url_differs(self) -> None:
        """Should merge cross-source duplicates by canonical identity."""
        existing = _make_mock_tournament(
            source_url="https://rk9.gg/event/charlotte-2026",
            name="Charlotte Regional Championships",
            city="Charlotte",
            country="US",
            event_source="rk9",
            source="rk9",
            tier="regional",
        )
        session = AsyncMock()

        source_result = MagicMock()
        source_result.scalar_one_or_none.return_value = None
        canonical_result = MagicMock()
        canonical_result.scalars.return_value.all.return_value = [existing]
        session.execute = AsyncMock(side_effect=[source_result, canonical_result])

        result = SyncEventsResult()
        data = _pokemon_event_to_tournament_data(
            _make_pokemon_event(
                name="Charlotte Regional",
                city="Charlotte",
                source_url="https://pokemon.com/events/charlotte-regional-2026",
                tier="regional",
            )
        )

        await _upsert_event(session, data, result)

        assert result.events_created == 0
        assert result.events_deduped == 1
        assert result.events_updated == 1
        assert existing.source == "rk9,pokemon.com"
        assert existing.event_source == "rk9,pokemon.com"


# ── End-to-end pipeline tests ───────────────────────────────────────


class TestSyncEventsPipeline:
    """Test the full sync_events pipeline."""

    @pytest.mark.asyncio
    @patch("src.pipelines.sync_events.async_session_factory")
    @patch("src.pipelines.sync_events.PokemonEventsClient")
    @patch("src.pipelines.sync_events.RK9Client")
    async def test_dry_run_no_db_writes(
        self,
        mock_rk9_cls,
        mock_pokemon_cls,
        mock_session_factory,
    ) -> None:
        """Dry run should fetch events but not write to DB."""
        # Set up RK9 client mock
        mock_rk9 = AsyncMock()
        mock_rk9.fetch_upcoming_events.return_value = [_make_rk9_event()]
        mock_rk9.__aenter__ = AsyncMock(return_value=mock_rk9)
        mock_rk9.__aexit__ = AsyncMock(return_value=False)
        mock_rk9_cls.return_value = mock_rk9

        # Set up Pokemon Events client mock
        mock_pokemon = AsyncMock()
        mock_pokemon.fetch_all_events.return_value = [_make_pokemon_event()]
        mock_pokemon.__aenter__ = AsyncMock(return_value=mock_pokemon)
        mock_pokemon.__aexit__ = AsyncMock(return_value=False)
        mock_pokemon_cls.return_value = mock_pokemon

        result = await sync_events(dry_run=True)

        assert result.events_fetched == 2
        assert result.events_created == 0
        assert result.events_updated == 0
        mock_session_factory.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.pipelines.sync_events.async_session_factory")
    @patch("src.pipelines.sync_events.PokemonEventsClient")
    @patch("src.pipelines.sync_events.RK9Client")
    async def test_creates_events_from_both_sources(
        self,
        mock_rk9_cls,
        mock_pokemon_cls,
        mock_session_factory,
    ) -> None:
        """Should create events from both RK9 and Pokemon sources."""
        # RK9 client
        mock_rk9 = AsyncMock()
        mock_rk9.fetch_upcoming_events.return_value = [
            _make_rk9_event(),
            _make_rk9_event(
                name="Dallas Regional",
                source_url="https://rk9.gg/event/dallas-2026",
            ),
        ]
        mock_rk9.__aenter__ = AsyncMock(return_value=mock_rk9)
        mock_rk9.__aexit__ = AsyncMock(return_value=False)
        mock_rk9_cls.return_value = mock_rk9

        # Pokemon Events client
        mock_pokemon = AsyncMock()
        mock_pokemon.fetch_all_events.return_value = [_make_pokemon_event()]
        mock_pokemon.__aenter__ = AsyncMock(return_value=mock_pokemon)
        mock_pokemon.__aexit__ = AsyncMock(return_value=False)
        mock_pokemon_cls.return_value = mock_pokemon

        # DB session mock — no existing tournaments
        mock_session = AsyncMock()
        mock_exec_result = MagicMock()
        mock_exec_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_exec_result
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session_factory.return_value = mock_session

        result = await sync_events(dry_run=False)

        assert result.events_fetched == 3
        assert result.events_created == 3
        assert result.success is True

    @pytest.mark.asyncio
    @patch("src.pipelines.sync_events.PokemonEventsClient")
    @patch("src.pipelines.sync_events.RK9Client")
    async def test_rk9_error_continues_with_pokemon(
        self,
        mock_rk9_cls,
        mock_pokemon_cls,
    ) -> None:
        """Should continue fetching from Pokemon if RK9 fails."""
        # RK9 raises error
        mock_rk9 = AsyncMock()
        mock_rk9.__aenter__ = AsyncMock(side_effect=RK9Error("Connection timeout"))
        mock_rk9.__aexit__ = AsyncMock(return_value=False)
        mock_rk9_cls.return_value = mock_rk9

        # Pokemon Events succeeds
        mock_pokemon = AsyncMock()
        mock_pokemon.fetch_all_events.return_value = [_make_pokemon_event()]
        mock_pokemon.__aenter__ = AsyncMock(return_value=mock_pokemon)
        mock_pokemon.__aexit__ = AsyncMock(return_value=False)
        mock_pokemon_cls.return_value = mock_pokemon

        result = await sync_events(dry_run=True)

        assert len(result.errors) == 1
        assert "RK9" in result.errors[0]
        assert result.events_fetched == 1  # only Pokemon events

    @pytest.mark.asyncio
    @patch("src.pipelines.sync_events.PokemonEventsClient")
    @patch("src.pipelines.sync_events.RK9Client")
    async def test_pokemon_error_continues_with_rk9(
        self,
        mock_rk9_cls,
        mock_pokemon_cls,
    ) -> None:
        """Should continue with RK9 events if Pokemon fails."""
        # RK9 succeeds
        mock_rk9 = AsyncMock()
        mock_rk9.fetch_upcoming_events.return_value = [_make_rk9_event()]
        mock_rk9.__aenter__ = AsyncMock(return_value=mock_rk9)
        mock_rk9.__aexit__ = AsyncMock(return_value=False)
        mock_rk9_cls.return_value = mock_rk9

        # Pokemon Events raises error
        mock_pokemon = AsyncMock()
        mock_pokemon.__aenter__ = AsyncMock(
            side_effect=PokemonEventsError("Service unavailable")
        )
        mock_pokemon.__aexit__ = AsyncMock(return_value=False)
        mock_pokemon_cls.return_value = mock_pokemon

        result = await sync_events(dry_run=True)

        assert len(result.errors) == 1
        assert "Pokemon" in result.errors[0]
        assert result.events_fetched == 1  # only RK9 events

    @pytest.mark.asyncio
    @patch("src.pipelines.sync_events.PokemonEventsClient")
    @patch("src.pipelines.sync_events.RK9Client")
    async def test_both_sources_fail(
        self,
        mock_rk9_cls,
        mock_pokemon_cls,
    ) -> None:
        """Should report errors from both sources."""
        mock_rk9 = AsyncMock()
        mock_rk9.__aenter__ = AsyncMock(side_effect=RK9Error("Down"))
        mock_rk9.__aexit__ = AsyncMock(return_value=False)
        mock_rk9_cls.return_value = mock_rk9

        mock_pokemon = AsyncMock()
        mock_pokemon.__aenter__ = AsyncMock(side_effect=PokemonEventsError("Down"))
        mock_pokemon.__aexit__ = AsyncMock(return_value=False)
        mock_pokemon_cls.return_value = mock_pokemon

        result = await sync_events(dry_run=True)

        assert len(result.errors) == 2
        assert result.events_fetched == 0
        assert result.success is False


class TestSyncEventsResult:
    """Test the SyncEventsResult dataclass."""

    def test_success_when_no_errors(self) -> None:
        result = SyncEventsResult(events_fetched=5, events_created=5)
        assert result.success is True

    def test_failure_when_errors(self) -> None:
        result = SyncEventsResult(errors=["Something failed"])
        assert result.success is False

    def test_defaults(self) -> None:
        result = SyncEventsResult()
        assert result.events_fetched == 0
        assert result.events_created == 0
        assert result.events_updated == 0
        assert result.events_skipped == 0
        assert result.events_deduped == 0
        assert result.sources_merged == 0
        assert result.errors == []
        assert result.success is True
