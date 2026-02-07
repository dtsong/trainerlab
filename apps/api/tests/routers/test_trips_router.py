"""Tests for trips router."""

from datetime import UTC, date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.models.tournament import Tournament
from src.models.trip import Trip, TripEvent
from src.models.user import User
from src.routers.trips import (
    add_event_to_trip,
    create_trip,
    delete_trip,
    get_shared_trip,
    get_trip,
    list_trips,
    remove_event_from_trip,
    share_trip,
    update_trip,
)
from src.schemas.trip import TripCreate, TripEventAdd, TripUpdate


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.fixture
def mock_user():
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.email = "test@example.com"
    user.is_beta_tester = True
    return user


@pytest.fixture
def mock_free_user():
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.email = "free@example.com"
    user.is_beta_tester = False
    return user


def _make_tournament(**overrides):
    t = MagicMock(spec=Tournament)
    t.id = overrides.get("id", uuid4())
    t.name = overrides.get("name", "Test Regional")
    t.date = overrides.get("date", date.today() + timedelta(days=30))
    t.region = overrides.get("region", "NA")
    t.country = overrides.get("country", "US")
    t.status = overrides.get("status", "announced")
    t.city = overrides.get("city", "Orlando")
    return t


def _make_trip(user_id, **overrides):
    trip = MagicMock(spec=Trip)
    trip.id = overrides.get("id", uuid4())
    trip.user_id = user_id
    trip.name = overrides.get("name", "My Trip")
    trip.status = overrides.get("status", "planning")
    trip.visibility = overrides.get("visibility", "private")
    trip.notes = overrides.get("notes")
    trip.share_token = overrides.get("share_token")
    trip.created_at = overrides.get("created_at", datetime.now(UTC))
    trip.updated_at = overrides.get("updated_at", datetime.now(UTC))
    trip.trip_events = overrides.get("trip_events", [])
    return trip


def _make_trip_event(trip_id, tournament):
    te = MagicMock(spec=TripEvent)
    te.id = uuid4()
    te.trip_id = trip_id
    te.tournament_id = tournament.id
    te.tournament = tournament
    te.role = "competitor"
    te.notes = None
    te.created_at = datetime.now(UTC)
    return te


class TestCreateTrip:
    """Tests for POST /api/v1/trips."""

    @pytest.mark.asyncio
    async def test_creates_trip_successfully(self, mock_session, mock_user):
        body = TripCreate(name="NAIC Trip")

        # Mock: after commit + refresh, re-fetch returns trip
        created_trip = _make_trip(mock_user.id, name="NAIC Trip")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = created_trip
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await create_trip(body, mock_user, mock_session)

        assert result.name == "NAIC Trip"
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_enforces_trip_limit_for_free_users(
        self, mock_session, mock_free_user
    ):
        body = TripCreate(name="Trip 6")

        mock_count = MagicMock()
        mock_count.scalar.return_value = 5
        mock_session.execute = AsyncMock(return_value=mock_count)

        with pytest.raises(HTTPException) as exc_info:
            await create_trip(body, mock_free_user, mock_session)
        assert exc_info.value.status_code == 403
        assert "limited to 5" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_beta_users_bypass_trip_limit(self, mock_session, mock_user):
        body = TripCreate(name="Trip 10")

        created_trip = _make_trip(mock_user.id, name="Trip 10")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = created_trip
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await create_trip(body, mock_user, mock_session)
        assert result.name == "Trip 10"


class TestListTrips:
    """Tests for GET /api/v1/trips."""

    @pytest.mark.asyncio
    async def test_returns_user_trips(self, mock_session, mock_user):
        t1 = _make_trip(mock_user.id, name="Trip 1")
        t2 = _make_trip(mock_user.id, name="Trip 2")

        mock_result = MagicMock()
        mock_result.scalars.return_value.unique.return_value.all.return_value = [
            t1,
            t2,
        ]
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await list_trips(mock_user, mock_session)

        assert len(result) == 2
        assert result[0].name == "Trip 1"

    @pytest.mark.asyncio
    async def test_handles_db_error(self, mock_session, mock_user):
        mock_session.execute = AsyncMock(side_effect=SQLAlchemyError("DB error"))

        with pytest.raises(HTTPException) as exc_info:
            await list_trips(mock_user, mock_session)
        assert exc_info.value.status_code == 503

    @pytest.mark.asyncio
    async def test_computes_next_event_date(self, mock_session, mock_user):
        future = date.today() + timedelta(days=10)
        tournament = _make_tournament(date=future)
        trip = _make_trip(mock_user.id, name="Trip With Event")
        te = _make_trip_event(trip.id, tournament)
        trip.trip_events = [te]

        mock_result = MagicMock()
        mock_result.scalars.return_value.unique.return_value.all.return_value = [trip]
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await list_trips(mock_user, mock_session)
        assert result[0].next_event_date == future
        assert result[0].event_count == 1


class TestGetTrip:
    """Tests for GET /api/v1/trips/{id}."""

    @pytest.mark.asyncio
    async def test_returns_trip_detail(self, mock_session, mock_user):
        trip = _make_trip(mock_user.id)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = trip
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await get_trip(trip.id, mock_user, mock_session)
        assert result.name == "My Trip"

    @pytest.mark.asyncio
    async def test_returns_404_for_missing_trip(self, mock_session, mock_user):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(HTTPException) as exc_info:
            await get_trip(uuid4(), mock_user, mock_session)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_returns_404_for_other_users_trip(self, mock_session, mock_user):
        other_user_id = uuid4()
        trip = _make_trip(other_user_id)

        # Query filters by user_id, so it won't find the trip
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(HTTPException) as exc_info:
            await get_trip(trip.id, mock_user, mock_session)
        assert exc_info.value.status_code == 404


class TestUpdateTrip:
    """Tests for PUT /api/v1/trips/{id}."""

    @pytest.mark.asyncio
    async def test_updates_trip_name(self, mock_session, mock_user):
        trip = _make_trip(mock_user.id, name="Old Name")
        body = TripUpdate(name="New Name")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = trip
        mock_session.execute = AsyncMock(return_value=mock_result)

        await update_trip(trip.id, body, mock_user, mock_session)
        assert trip.name == "New Name"

    @pytest.mark.asyncio
    async def test_updates_trip_status(self, mock_session, mock_user):
        trip = _make_trip(mock_user.id)
        body = TripUpdate(status="upcoming")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = trip
        mock_session.execute = AsyncMock(return_value=mock_result)

        await update_trip(trip.id, body, mock_user, mock_session)
        assert trip.status == "upcoming"


class TestDeleteTrip:
    """Tests for DELETE /api/v1/trips/{id}."""

    @pytest.mark.asyncio
    async def test_deletes_trip(self, mock_session, mock_user):
        trip = _make_trip(mock_user.id)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = trip
        mock_session.execute = AsyncMock(return_value=mock_result)

        await delete_trip(trip.id, mock_user, mock_session)
        mock_session.delete.assert_called_once_with(trip)
        mock_session.commit.assert_called()


class TestAddEventToTrip:
    """Tests for POST /api/v1/trips/{id}/events."""

    @pytest.mark.asyncio
    async def test_adds_event_to_trip(self, mock_session, mock_user):
        tournament = _make_tournament()
        trip = _make_trip(mock_user.id)
        body = TripEventAdd(tournament_id=str(tournament.id))

        # First call: _get_trip_or_404
        # Second call: find tournament
        # Third call: _get_trip_or_404 for return
        mock_trip_result = MagicMock()
        mock_trip_result.scalar_one_or_none.return_value = trip

        mock_tournament_result = MagicMock()
        mock_tournament_result.scalar_one_or_none.return_value = tournament

        mock_session.execute = AsyncMock(
            side_effect=[
                mock_trip_result,
                mock_tournament_result,
                mock_trip_result,
            ]
        )

        await add_event_to_trip(trip.id, body, mock_user, mock_session)
        mock_session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_404_for_missing_tournament(self, mock_session, mock_user):
        trip = _make_trip(mock_user.id)
        body = TripEventAdd(tournament_id=str(uuid4()))

        mock_trip_result = MagicMock()
        mock_trip_result.scalar_one_or_none.return_value = trip

        mock_tournament_result = MagicMock()
        mock_tournament_result.scalar_one_or_none.return_value = None

        mock_session.execute = AsyncMock(
            side_effect=[
                mock_trip_result,
                mock_tournament_result,
            ]
        )

        with pytest.raises(HTTPException) as exc_info:
            await add_event_to_trip(trip.id, body, mock_user, mock_session)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_returns_409_for_duplicate_event(self, mock_session, mock_user):
        tournament = _make_tournament()
        trip = _make_trip(mock_user.id)
        body = TripEventAdd(tournament_id=str(tournament.id))

        mock_trip_result = MagicMock()
        mock_trip_result.scalar_one_or_none.return_value = trip

        mock_tournament_result = MagicMock()
        mock_tournament_result.scalar_one_or_none.return_value = tournament

        mock_session.execute = AsyncMock(
            side_effect=[
                mock_trip_result,
                mock_tournament_result,
            ]
        )
        mock_session.commit = AsyncMock(side_effect=IntegrityError("dup", None, None))

        with pytest.raises(HTTPException) as exc_info:
            await add_event_to_trip(trip.id, body, mock_user, mock_session)
        assert exc_info.value.status_code == 409


class TestRemoveEventFromTrip:
    """Tests for DELETE /api/v1/trips/{id}/events/{event_id}."""

    @pytest.mark.asyncio
    async def test_removes_event(self, mock_session, mock_user):
        trip = _make_trip(mock_user.id)
        tournament = _make_tournament()
        te = _make_trip_event(trip.id, tournament)

        mock_trip_result = MagicMock()
        mock_trip_result.scalar_one_or_none.return_value = trip

        mock_te_result = MagicMock()
        mock_te_result.scalar_one_or_none.return_value = te

        mock_session.execute = AsyncMock(side_effect=[mock_trip_result, mock_te_result])

        await remove_event_from_trip(trip.id, te.id, mock_user, mock_session)
        mock_session.delete.assert_called_once_with(te)

    @pytest.mark.asyncio
    async def test_returns_404_for_missing_trip_event(self, mock_session, mock_user):
        trip = _make_trip(mock_user.id)

        mock_trip_result = MagicMock()
        mock_trip_result.scalar_one_or_none.return_value = trip

        mock_te_result = MagicMock()
        mock_te_result.scalar_one_or_none.return_value = None

        mock_session.execute = AsyncMock(side_effect=[mock_trip_result, mock_te_result])

        with pytest.raises(HTTPException) as exc_info:
            await remove_event_from_trip(trip.id, uuid4(), mock_user, mock_session)
        assert exc_info.value.status_code == 404


class TestShareTrip:
    """Tests for POST /api/v1/trips/{id}/share."""

    @pytest.mark.asyncio
    async def test_generates_share_token(self, mock_session, mock_user):
        trip = _make_trip(mock_user.id, share_token=None, visibility="private")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = trip
        mock_session.execute = AsyncMock(return_value=mock_result)

        await share_trip(trip.id, mock_user, mock_session)
        assert trip.visibility == "shared"
        assert trip.share_token is not None


class TestGetSharedTrip:
    """Tests for GET /api/v1/trips/shared/{token}."""

    @pytest.mark.asyncio
    async def test_returns_shared_trip(self, mock_session):
        trip = _make_trip(
            uuid4(),
            share_token="test-token",
            visibility="shared",
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = trip
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await get_shared_trip("test-token", mock_session)
        assert result.name == "My Trip"

    @pytest.mark.asyncio
    async def test_returns_404_for_invalid_token(self, mock_session):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(HTTPException) as exc_info:
            await get_shared_trip("bad-token", mock_session)
        assert exc_info.value.status_code == 404
