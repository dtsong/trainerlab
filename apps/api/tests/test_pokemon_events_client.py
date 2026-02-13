"""Tests for Pokemon Events client."""

import json
from datetime import date
from unittest.mock import AsyncMock, patch

import pytest

from src.clients.pokemon_events import (
    PokemonEvent,
    PokemonEventsClient,
    PokemonEventsError,
)


@pytest.fixture
def pokemon_client():
    return PokemonEventsClient(timeout=5.0, max_retries=1, retry_delay=0.01)


class TestPokemonEventDataclass:
    """Tests for PokemonEvent dataclass."""

    def test_creates_event_with_defaults(self):
        event = PokemonEvent(
            name="Portland Regional",
            date=date(2026, 4, 10),
        )
        assert event.name == "Portland Regional"
        assert event.tier == "regional"
        assert event.region is None

    def test_creates_event_with_all_fields(self):
        event = PokemonEvent(
            name="Worlds 2026",
            date=date(2026, 8, 15),
            end_date=date(2026, 8, 17),
            city="Honolulu",
            country="US",
            region="NA",
            venue="Hawaii Convention Center",
            registration_url="https://pokemon.com/worlds",
            source_url="https://pokemon.com/worlds",
            tier="worlds",
        )
        assert event.city == "Honolulu"
        assert event.tier == "worlds"


class TestPokemonEventsClientInit:
    """Tests for PokemonEventsClient initialization."""

    def test_creates_client(self, pokemon_client):
        assert pokemon_client is not None

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        async with PokemonEventsClient(timeout=5.0, max_retries=1) as client:
            assert client is not None


class TestPokemonEventsClientParsing:
    """Tests for HTML parsing."""

    @pytest.mark.asyncio
    async def test_fetch_returns_empty_for_no_events(self, pokemon_client):
        html = "<html><body><div>No events</div></body></html>"

        with patch.object(
            pokemon_client,
            "_get",
            new_callable=AsyncMock,
        ) as mock_get:
            mock_get.return_value = html
            events = await pokemon_client.fetch_regional_championships()

        assert isinstance(events, list)
        assert len(events) == 0

    @pytest.mark.asyncio
    async def test_handles_error_returns_empty(self, pokemon_client):
        with patch.object(
            pokemon_client,
            "_get",
            new_callable=AsyncMock,
            side_effect=PokemonEventsError("Fetch error"),
        ):
            events = await pokemon_client.fetch_regional_championships()

        assert events == []


class TestPokemonEventsJsonIngestion:
    @pytest.mark.asyncio
    async def test_fetch_all_events_parses_official_majors_and_skips_online(
        self,
        pokemon_client,
    ):
        payload = {
            "items": [
                {
                    "eventName_s": "Seattle Pokemon Regional Championships 2026",
                    "type_s": "regional",
                    "region_s": "northamerica",
                    "startDateTime_dt": "2026-02-27T16:00:00.000Z",
                    "endDateTime_dt": "2026-03-01T22:00:00.000Z",
                    "eventLocation_s": "Seattle, WA",
                    "uRL_s": "/en-us/events/regionals/2026/seattle",
                },
                {
                    "eventName_s": "UCS Regional Leagues Week 3",
                    "type_s": "online",
                    "region_s": "virtual",
                    "startDateTime_dt": "2026-02-28T16:00:00.000Z",
                    "uRL_s": "/en-us/events/online/2026/ucs-regional-leagues-week-3",
                },
                {
                    "eventName_s": "2026 Pokemon Europe International Championships",
                    "type_s": "international",
                    "region_s": "europe",
                    "startDateTime_dt": "2026-02-13T16:00:00.000Z",
                    "endDateTime_dt": "2026-02-15T22:00:00.000Z",
                    "eventLocation_s": "London, UK",
                    "uRL_s": "/en-us/events/internationals/2026/london",
                },
            ]
        }

        with patch.object(
            pokemon_client,
            "_get",
            new_callable=AsyncMock,
        ) as mock_get:
            mock_get.return_value = json.dumps(payload)
            events = await pokemon_client.fetch_all_events()

        assert len(events) == 2
        assert all(event.tier in {"regional", "international"} for event in events)
        assert all("/events/online/" not in event.source_url for event in events)

    @pytest.mark.asyncio
    async def test_fetch_all_events_returns_empty_on_invalid_json(self, pokemon_client):
        with patch.object(
            pokemon_client,
            "_get",
            new_callable=AsyncMock,
            return_value="not-json",
        ):
            events = await pokemon_client.fetch_all_events()

        assert events == []
