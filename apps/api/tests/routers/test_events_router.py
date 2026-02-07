"""Tests for events router."""

from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError

from src.models.tournament import Tournament
from src.models.tournament_placement import TournamentPlacement
from src.routers.events import (
    get_event,
    get_event_calendar,
    list_events,
)


@pytest.fixture
def mock_session():
    return AsyncMock()


def _make_tournament(**overrides):
    """Create a mock Tournament with sensible defaults."""
    t = MagicMock(spec=Tournament)
    t.id = overrides.get("id", uuid4())
    t.name = overrides.get("name", "Test Regional")
    t.date = overrides.get("date", date.today() + timedelta(days=30))
    t.region = overrides.get("region", "NA")
    t.country = overrides.get("country", "US")
    t.format = overrides.get("format", "standard")
    t.best_of = overrides.get("best_of", 3)
    t.tier = overrides.get("tier", "major")
    t.status = overrides.get("status", "announced")
    t.city = overrides.get("city", "Orlando")
    t.venue_name = overrides.get("venue_name", "Convention Center")
    t.venue_address = overrides.get("venue_address", "123 Main St")
    t.registration_url = overrides.get("registration_url")
    t.registration_opens_at = overrides.get("registration_opens_at")
    t.registration_closes_at = overrides.get("registration_closes_at")
    t.participant_count = overrides.get("participant_count")
    t.event_source = overrides.get("event_source", "rk9")
    t.source_url = overrides.get("source_url")
    t.placements = overrides.get("placements", [])
    return t


class TestListEvents:
    """Tests for GET /api/v1/events."""

    @pytest.mark.asyncio
    async def test_returns_upcoming_events(self, mock_session):
        t1 = _make_tournament(name="Event A")
        t2 = _make_tournament(name="Event B")

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 2

        mock_rows = MagicMock()
        mock_rows.scalars.return_value.unique.return_value.all.return_value = [
            t1,
            t2,
        ]

        mock_session.execute = AsyncMock(side_effect=[mock_count_result, mock_rows])

        result = await list_events(
            db=mock_session,
            region=None,
            format=None,
            tier=None,
            status_filter=None,
            include_completed=False,
            page=1,
            limit=20,
        )

        assert result.total == 2
        assert len(result.items) == 2
        assert result.items[0].name == "Event A"

    @pytest.mark.asyncio
    async def test_filters_by_region(self, mock_session):
        t1 = _make_tournament(name="EU Regional", region="EU")

        mock_count = MagicMock()
        mock_count.scalar.return_value = 1

        mock_rows = MagicMock()
        mock_rows.scalars.return_value.unique.return_value.all.return_value = [t1]

        mock_session.execute = AsyncMock(side_effect=[mock_count, mock_rows])

        result = await list_events(
            db=mock_session,
            region="EU",
            format=None,
            tier=None,
            status_filter=None,
            include_completed=False,
            page=1,
            limit=20,
        )

        assert result.total == 1
        assert result.items[0].region == "EU"

    @pytest.mark.asyncio
    async def test_handles_db_error(self, mock_session):
        mock_session.execute = AsyncMock(side_effect=SQLAlchemyError("DB error"))

        with pytest.raises(HTTPException) as exc_info:
            await list_events(
                db=mock_session,
                region=None,
                format=None,
                tier=None,
                status_filter=None,
                include_completed=False,
                page=1,
                limit=20,
            )
        assert exc_info.value.status_code == 503

    @pytest.mark.asyncio
    async def test_empty_result(self, mock_session):
        mock_count = MagicMock()
        mock_count.scalar.return_value = 0

        mock_rows = MagicMock()
        mock_rows.scalars.return_value.unique.return_value.all.return_value = []

        mock_session.execute = AsyncMock(side_effect=[mock_count, mock_rows])

        result = await list_events(
            db=mock_session,
            region=None,
            format=None,
            tier=None,
            status_filter=None,
            include_completed=False,
            page=1,
            limit=20,
        )

        assert result.total == 0
        assert result.items == []
        assert result.has_next is False

    @pytest.mark.asyncio
    async def test_computes_days_until(self, mock_session):
        future_date = date.today() + timedelta(days=15)
        t = _make_tournament(date=future_date)

        mock_count = MagicMock()
        mock_count.scalar.return_value = 1

        mock_rows = MagicMock()
        mock_rows.scalars.return_value.unique.return_value.all.return_value = [t]

        mock_session.execute = AsyncMock(side_effect=[mock_count, mock_rows])

        result = await list_events(
            db=mock_session,
            region=None,
            format=None,
            tier=None,
            status_filter=None,
            include_completed=False,
            page=1,
            limit=20,
        )

        assert result.items[0].days_until == 15


class TestGetEvent:
    """Tests for GET /api/v1/events/{id}."""

    @pytest.mark.asyncio
    async def test_returns_event_detail(self, mock_session):
        t = _make_tournament()
        p1 = MagicMock(spec=TournamentPlacement)
        p1.placement = 1
        p1.player_name = "Alice"
        p1.archetype = "Charizard ex"
        p2 = MagicMock(spec=TournamentPlacement)
        p2.placement = 2
        p2.player_name = "Bob"
        p2.archetype = "Gardevoir ex"
        t.placements = [p2, p1]

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = t
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await get_event(t.id, mock_session)

        assert result.name == "Test Regional"
        assert len(result.top_placements) == 2
        assert result.top_placements[0].placement == 1
        assert len(result.meta_breakdown) == 2

    @pytest.mark.asyncio
    async def test_returns_404_for_missing_event(self, mock_session):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(HTTPException) as exc_info:
            await get_event(uuid4(), mock_session)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_handles_db_error(self, mock_session):
        mock_session.execute = AsyncMock(side_effect=SQLAlchemyError("DB error"))

        with pytest.raises(HTTPException) as exc_info:
            await get_event(uuid4(), mock_session)
        assert exc_info.value.status_code == 503


class TestGetEventCalendar:
    """Tests for GET /api/v1/events/{id}/calendar.ics."""

    @pytest.mark.asyncio
    async def test_returns_ics_content(self, mock_session):
        t = _make_tournament(
            name="NAIC 2026",
            date=date(2026, 6, 20),
            venue_name="Convention Center",
            city="Columbus",
            country="US",
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = t
        mock_session.execute = AsyncMock(return_value=mock_result)

        response = await get_event_calendar(t.id, mock_session)

        assert response.media_type == "text/calendar"
        body = response.body.decode()
        assert "BEGIN:VCALENDAR" in body
        assert "SUMMARY:NAIC 2026" in body
        assert "DTSTART;VALUE=DATE:20260620" in body
        assert "Convention Center" in body
        assert "Columbus" in body

    @pytest.mark.asyncio
    async def test_returns_404_for_missing_event(self, mock_session):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(HTTPException) as exc_info:
            await get_event_calendar(uuid4(), mock_session)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_ics_without_venue(self, mock_session):
        t = _make_tournament(venue_name=None, city=None, country=None)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = t
        mock_session.execute = AsyncMock(return_value=mock_result)

        response = await get_event_calendar(t.id, mock_session)
        body = response.body.decode()
        assert "LOCATION" not in body
