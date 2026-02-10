"""Tests for Pokemon Events client."""

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
