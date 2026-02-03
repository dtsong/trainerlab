"""Tests for TCGdex API client."""

from datetime import date
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from src.clients.tcgdex import (
    TCGdexCard,
    TCGdexClient,
    TCGdexError,
    TCGdexSet,
    TCGdexSetSummary,
)


@pytest.fixture
def client() -> TCGdexClient:
    """Create TCGdex client for testing."""
    return TCGdexClient(base_url="https://api.tcgdex.net/v2")


class TestTCGdexSetSummary:
    """Tests for TCGdexSetSummary model."""

    def test_from_dict(self):
        """Test parsing set summary from API response."""
        data = {
            "id": "swsh1",
            "name": "Sword & Shield",
            "logo": "https://assets.tcgdex.net/en/swsh/swsh1/logo",
            "cardCount": {"total": 216, "official": 202},
        }
        summary = TCGdexSetSummary.from_dict(data)
        assert summary.id == "swsh1"
        assert summary.name == "Sword & Shield"
        assert summary.logo == "https://assets.tcgdex.net/en/swsh/swsh1/logo"
        assert summary.card_count_total == 216
        assert summary.card_count_official == 202

    def test_from_dict_missing_optional_fields(self):
        """Test parsing set summary with missing optional fields."""
        data = {
            "id": "swshp",
            "name": "Promos",
            "cardCount": {"total": 100, "official": 100},
        }
        summary = TCGdexSetSummary.from_dict(data)
        assert summary.id == "swshp"
        assert summary.logo is None


class TestTCGdexSet:
    """Tests for TCGdexSet model."""

    def test_from_dict(self):
        """Test parsing set from API response."""
        data = {
            "id": "swsh1",
            "name": "Sword & Shield",
            "releaseDate": "2020-02-07",
            "serie": {"id": "swsh", "name": "Sword & Shield"},
            "legal": {"standard": False, "expanded": True},
            "logo": "https://assets.tcgdex.net/en/swsh/swsh1/logo",
            "symbol": "https://assets.tcgdex.net/univ/swsh/swsh1/symbol",
            "cardCount": {"total": 216, "official": 202},
            "cards": [{"id": "swsh1-1", "localId": "1", "name": "Celebi V"}],
        }
        tcgdex_set = TCGdexSet.from_dict(data)
        assert tcgdex_set.id == "swsh1"
        assert tcgdex_set.name == "Sword & Shield"
        assert tcgdex_set.release_date == date(2020, 2, 7)
        assert tcgdex_set.series_id == "swsh"
        assert tcgdex_set.series_name == "Sword & Shield"
        assert tcgdex_set.legal_standard is False
        assert tcgdex_set.legal_expanded is True
        assert len(tcgdex_set.card_summaries) == 1

    def test_from_dict_missing_release_date(self):
        """Test parsing set with missing release date."""
        data = {
            "id": "swshp",
            "name": "Promos",
            "serie": {"id": "swsh", "name": "Sword & Shield"},
            "cardCount": {"total": 100, "official": 100},
            "cards": [],
        }
        tcgdex_set = TCGdexSet.from_dict(data)
        assert tcgdex_set.release_date is None


class TestTCGdexCard:
    """Tests for TCGdexCard model."""

    def test_from_dict_pokemon(self):
        """Test parsing Pokemon card from API response."""
        data = {
            "id": "swsh1-1",
            "localId": "1",
            "name": "Celebi V",
            "category": "Pokemon",
            "hp": 180,
            "types": ["Grass"],
            "stage": "Basic",
            "suffix": "V",
            "attacks": [
                {
                    "cost": ["Grass"],
                    "name": "Find a Friend",
                    "effect": "Search your deck for up to 2 Pokemon.",
                },
                {
                    "cost": ["Grass", "Colorless"],
                    "name": "Line Force",
                    "damage": "50+",
                    "effect": "Does 20 more damage for each Benched Pokemon.",
                },
            ],
            "weaknesses": [{"type": "Fire", "value": "×2"}],
            "retreat": 1,
            "rarity": "Holo Rare V",
            "regulationMark": "D",
            "image": "https://assets.tcgdex.net/en/swsh/swsh1/1",
            "set": {"id": "swsh1", "name": "Sword & Shield"},
            "legal": {"standard": False, "expanded": True},
        }
        card = TCGdexCard.from_dict(data)
        assert card.id == "swsh1-1"
        assert card.local_id == "1"
        assert card.name == "Celebi V"
        assert card.supertype == "Pokemon"
        assert card.hp == 180
        assert card.types == ["Grass"]
        assert card.stage == "Basic"
        assert len(card.attacks) == 2
        assert card.attacks[0]["name"] == "Find a Friend"
        assert card.weaknesses == [{"type": "Fire", "value": "×2"}]
        assert card.retreat_cost == 1
        assert card.rarity == "Holo Rare V"
        assert card.regulation_mark == "D"
        assert card.set_id == "swsh1"
        assert card.legal_standard is False
        assert card.legal_expanded is True

    def test_from_dict_trainer(self):
        """Test parsing Trainer card from API response."""
        data = {
            "id": "swsh1-100",
            "localId": "100",
            "name": "Professor's Research",
            "category": "Trainer",
            "trainerType": "Supporter",
            "effect": "Discard your hand and draw 7 cards.",
            "rarity": "Rare Holo",
            "image": "https://assets.tcgdex.net/en/swsh/swsh1/100",
            "set": {"id": "swsh1", "name": "Sword & Shield"},
            "legal": {"standard": True, "expanded": True},
        }
        card = TCGdexCard.from_dict(data)
        assert card.supertype == "Trainer"
        assert card.subtypes == ["Supporter"]
        assert card.hp is None
        assert card.types is None

    def test_from_dict_energy(self):
        """Test parsing Energy card from API response."""
        data = {
            "id": "swsh1-200",
            "localId": "200",
            "name": "Basic Grass Energy",
            "category": "Energy",
            "energyType": "Basic",
            "rarity": "Common",
            "image": "https://assets.tcgdex.net/en/swsh/swsh1/200",
            "set": {"id": "swsh1", "name": "Sword & Shield"},
            "legal": {"standard": True, "expanded": True},
        }
        card = TCGdexCard.from_dict(data)
        assert card.supertype == "Energy"
        assert card.subtypes == ["Basic"]


class TestTCGdexClient:
    """Tests for TCGdex client."""

    @pytest.mark.asyncio
    async def test_fetch_all_sets(self, client: TCGdexClient):
        """Test fetching all sets."""
        mock_response = [
            {
                "id": "swsh1",
                "name": "Sword & Shield",
                "cardCount": {"total": 216, "official": 202},
            },
            {
                "id": "swsh2",
                "name": "Rebel Clash",
                "cardCount": {"total": 200, "official": 192},
            },
        ]
        with patch.object(
            client, "_get", new_callable=AsyncMock, return_value=mock_response
        ):
            sets = await client.fetch_all_sets()
            assert len(sets) == 2
            assert sets[0].id == "swsh1"
            assert sets[1].id == "swsh2"

    @pytest.mark.asyncio
    async def test_fetch_set(self, client: TCGdexClient):
        """Test fetching a single set with card summaries."""
        mock_response = {
            "id": "swsh1",
            "name": "Sword & Shield",
            "releaseDate": "2020-02-07",
            "serie": {"id": "swsh", "name": "Sword & Shield"},
            "cardCount": {"total": 216, "official": 202},
            "cards": [
                {"id": "swsh1-1", "localId": "1", "name": "Celebi V"},
            ],
        }
        with patch.object(
            client, "_get", new_callable=AsyncMock, return_value=mock_response
        ):
            tcgdex_set = await client.fetch_set("swsh1")
            assert tcgdex_set.id == "swsh1"
            assert len(tcgdex_set.card_summaries) == 1

    @pytest.mark.asyncio
    async def test_fetch_card(self, client: TCGdexClient):
        """Test fetching a single card."""
        mock_response = {
            "id": "swsh1-1",
            "localId": "1",
            "name": "Celebi V",
            "category": "Pokemon",
            "hp": 180,
            "types": ["Grass"],
            "set": {"id": "swsh1", "name": "Sword & Shield"},
            "legal": {"standard": False, "expanded": True},
        }
        with patch.object(
            client, "_get", new_callable=AsyncMock, return_value=mock_response
        ):
            card = await client.fetch_card("swsh1-1")
            assert card.id == "swsh1-1"
            assert card.name == "Celebi V"

    @pytest.mark.asyncio
    async def test_fetch_cards_for_set(self, client: TCGdexClient):
        """Test fetching all cards for a set."""
        mock_set_response = {
            "id": "swsh1",
            "name": "Sword & Shield",
            "serie": {"id": "swsh", "name": "Sword & Shield"},
            "cardCount": {"total": 2, "official": 2},
            "cards": [
                {"id": "swsh1-1", "localId": "1", "name": "Celebi V"},
                {"id": "swsh1-2", "localId": "2", "name": "Charizard V"},
            ],
        }
        mock_card1 = {
            "id": "swsh1-1",
            "localId": "1",
            "name": "Celebi V",
            "category": "Pokemon",
            "set": {"id": "swsh1"},
            "legal": {},
        }
        mock_card2 = {
            "id": "swsh1-2",
            "localId": "2",
            "name": "Charizard V",
            "category": "Pokemon",
            "set": {"id": "swsh1"},
            "legal": {},
        }

        endpoint_responses = {
            "/en/sets/swsh1": mock_set_response,
            "/en/cards/swsh1-1": mock_card1,
            "/en/cards/swsh1-2": mock_card2,
        }

        async def mock_get(endpoint: str):
            return endpoint_responses.get(endpoint)

        with patch.object(client, "_get", side_effect=mock_get):
            cards = await client.fetch_cards_for_set("swsh1")
            assert len(cards) == 2
            assert cards[0].id == "swsh1-1"
            assert cards[1].id == "swsh1-2"

    @pytest.mark.asyncio
    async def test_retry_on_rate_limit(self, client: TCGdexClient):
        """Test retry behavior on rate limit."""
        # Override retry delay for faster tests
        client._retry_delay = 0.01
        call_count = 0

        async def mock_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            request = httpx.Request("GET", "http://test")
            if call_count == 1:
                raise httpx.HTTPStatusError(
                    "Rate limited",
                    request=request,
                    response=httpx.Response(429, request=request),
                )
            response = httpx.Response(200, json={"id": "swsh1"}, request=request)
            return response

        with patch.object(client._client, "get", side_effect=mock_request):
            result = await client._get("/en/sets/swsh1")
            assert result == {"id": "swsh1"}
            assert call_count == 2

    @pytest.mark.asyncio
    async def test_error_on_not_found(self, client: TCGdexClient):
        """Test error on 404 response."""

        async def mock_request(*args, **kwargs):
            raise httpx.HTTPStatusError(
                "Not found",
                request=httpx.Request("GET", "http://test"),
                response=httpx.Response(404),
            )

        with (
            patch.object(client._client, "get", side_effect=mock_request),
            pytest.raises(TCGdexError, match="Not found"),
        ):
            await client._get("/en/sets/invalid")

    @pytest.mark.asyncio
    async def test_fetch_card_encodes_special_characters(self, client: TCGdexClient):
        """Test that card IDs with special characters are URL-encoded."""
        mock_response = {
            "id": "exu-?",
            "localId": "?",
            "name": "Promo Card",
            "category": "Pokemon",
            "set": {"id": "exu"},
            "legal": {},
        }

        async def mock_get(endpoint: str):
            # Verify the endpoint has the encoded card_id
            assert endpoint == "/en/cards/exu-%3F"
            return mock_response

        with patch.object(client, "_get", side_effect=mock_get):
            card = await client.fetch_card("exu-?")
            assert card.id == "exu-?"
            assert card.name == "Promo Card"

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager."""
        async with TCGdexClient(base_url="https://api.tcgdex.net/v2") as client:
            assert client._client is not None
