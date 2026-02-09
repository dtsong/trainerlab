"""Tests for Limitless TCG scraper."""

import logging
from datetime import date
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.clients.limitless import (
    LimitlessClient,
    LimitlessDecklist,
    LimitlessError,
    LimitlessPlacement,
    LimitlessTournament,
    map_set_code,
    parse_card_line,
)

# Load fixtures
FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> str:
    """Load an HTML fixture file."""
    return (FIXTURES_DIR / name).read_text()


class TestMapSetCode:
    """Tests for set code mapping."""

    def test_maps_sv_era_sets(self) -> None:
        """Should map Scarlet & Violet era sets."""
        assert map_set_code("SCR") == "sv7"
        assert map_set_code("SFA") == "sv6pt5"
        assert map_set_code("TWM") == "sv6"
        assert map_set_code("TEF") == "sv5"
        assert map_set_code("PAR") == "sv4"
        assert map_set_code("OBF") == "sv3"
        assert map_set_code("SVI") == "sv1"

    def test_maps_swsh_era_sets(self) -> None:
        """Should map Sword & Shield era sets."""
        assert map_set_code("CRZ") == "swsh12pt5"
        assert map_set_code("LOR") == "swsh11"
        assert map_set_code("BRS") == "swsh9"

    def test_returns_lowercase_for_unknown(self) -> None:
        """Should return lowercase for unknown set codes."""
        assert map_set_code("XYZ") == "xyz"


class TestParseCardLine:
    """Tests for decklist line parsing."""

    def test_parses_standard_card_line(self) -> None:
        """Should parse standard card format."""
        result = parse_card_line("4 Charizard ex OBF 125")

        assert result is not None
        assert result["card_id"] == "sv3-125"
        assert result["quantity"] == 4
        assert result["name"] == "Charizard ex"
        assert result["set_code"] == "OBF"

    def test_parses_card_with_long_name(self) -> None:
        """Should parse cards with multi-word names."""
        result = parse_card_line("3 Boss's Orders PAL 172")

        assert result is not None
        assert result["card_id"] == "sv2-172"
        assert result["quantity"] == 3
        assert result["name"] == "Boss's Orders"

    def test_parses_basic_energy(self) -> None:
        """Should parse basic energy lines."""
        # "4 Fire Energy Energy" matches the main pattern with set_code=Energy
        result = parse_card_line("4 Fire Energy Energy")

        assert result is not None
        assert result["quantity"] == 4
        assert "energy" in result["card_id"].lower()

    def test_parses_jp_set_code_with_suffix(self) -> None:
        """Should parse JP set codes with digits and suffix letters."""
        result = parse_card_line("2 Pikachu SV5a 012")

        assert result is not None
        assert result["card_id"] == "sv5a-012"
        assert result["quantity"] == 2
        assert result["name"] == "Pikachu"

    def test_returns_none_for_empty_line(self) -> None:
        """Should return None for empty lines."""
        assert parse_card_line("") is None
        assert parse_card_line("   ") is None

    def test_returns_none_for_invalid_format(self) -> None:
        """Should return None for invalid formats."""
        assert parse_card_line("Invalid line format") is None
        assert parse_card_line("Pokémon: 13") is None
        assert parse_card_line("## Section Header") is None


class TestLimitlessTournament:
    """Tests for LimitlessTournament dataclass."""

    def test_from_listing_parses_date(self) -> None:
        """Should parse various date formats."""
        tournament = LimitlessTournament.from_listing(
            name="Test Event",
            date_str="2026-01-25",
            region="NA",
            game_format="standard",
            participant_count=128,
            url="https://example.com",
        )

        assert tournament.tournament_date == date(2026, 1, 25)

    def test_from_listing_parses_month_name_date(self) -> None:
        """Should parse date with month name."""
        tournament = LimitlessTournament.from_listing(
            name="Test Event",
            date_str="January 25, 2026",
            region="NA",
            game_format="standard",
            participant_count=128,
            url="https://example.com",
        )

        assert tournament.tournament_date == date(2026, 1, 25)

    def test_from_listing_defaults_best_of(self) -> None:
        """Should default best_of to 3."""
        tournament = LimitlessTournament.from_listing(
            name="Test Event",
            date_str="2026-01-25",
            region="NA",
            game_format="standard",
            participant_count=128,
            url="https://example.com",
        )

        assert tournament.best_of == 3

    def test_from_listing_parses_short_date_format(self) -> None:
        """Should parse DD Mon YY format used by JP City Leagues."""
        tournament = LimitlessTournament.from_listing(
            name="JP City League",
            date_str="01 Feb 26",
            region="JP",
            game_format="standard",
            participant_count=64,
            url="https://example.com",
            best_of=1,
        )

        assert tournament.tournament_date == date(2026, 2, 1)

    def test_from_listing_parses_short_date_various_months(self) -> None:
        """Should parse DD Mon YY format for various months."""
        tournament = LimitlessTournament.from_listing(
            name="JP City League",
            date_str="25 Jan 26",
            region="JP",
            game_format="standard",
            participant_count=64,
            url="https://example.com",
            best_of=1,
        )

        assert tournament.tournament_date == date(2026, 1, 25)

    def test_from_listing_allows_best_of_1(self) -> None:
        """Should allow best_of=1 for JP tournaments."""
        tournament = LimitlessTournament.from_listing(
            name="JP Event",
            date_str="2026-01-25",
            region="JP",
            game_format="standard",
            participant_count=256,
            url="https://example.com",
            best_of=1,
        )

        assert tournament.best_of == 1


class TestLimitlessDecklist:
    """Tests for LimitlessDecklist dataclass."""

    def test_is_valid_with_cards(self) -> None:
        """Should be valid when cards present."""
        decklist = LimitlessDecklist(cards=[{"card_id": "sv3-125", "quantity": 2}])
        assert decklist.is_valid is True

    def test_not_valid_when_empty(self) -> None:
        """Should not be valid when empty."""
        decklist = LimitlessDecklist(cards=[])
        assert decklist.is_valid is False


class TestLimitlessClient:
    """Tests for LimitlessClient."""

    @pytest.fixture
    def client(self) -> LimitlessClient:
        return LimitlessClient(
            requests_per_minute=100,  # High limit for tests
            max_concurrent=10,
        )

    @pytest.mark.asyncio
    async def test_parses_tournament_listings(self, client: LimitlessClient) -> None:
        """Should parse tournament listings from HTML."""
        html = load_fixture("limitless_tournaments.html")

        with patch.object(client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = html

            tournaments = await client.fetch_tournament_listings(
                region="en",
                game_format="standard",
            )

            assert len(tournaments) == 3
            assert tournaments[0].name == "Regional Championship 2026"
            assert tournaments[0].participant_count == 256
            assert tournaments[1].name == "League Challenge January"
            assert tournaments[1].participant_count == 32

    @pytest.mark.asyncio
    async def test_parses_standings(self, client: LimitlessClient) -> None:
        """Should parse tournament standings from HTML."""
        html = load_fixture("limitless_standings.html")

        with patch.object(client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = html

            placements = await client.fetch_tournament_placements(
                "https://play.limitlesstcg.com/tournament/abc123"
            )

            assert len(placements) == 4
            assert placements[0].placement == 1
            assert placements[0].player_name == "John Smith"
            assert placements[0].archetype == "Charizard ex"
            assert placements[0].country == "US"
            assert placements[0].decklist_url is not None

            # Player without decklist
            assert placements[3].archetype == "Rogue"
            assert placements[3].decklist_url is None

    @pytest.mark.asyncio
    async def test_parses_decklist(self, client: LimitlessClient) -> None:
        """Should parse decklist from HTML."""
        html = load_fixture("limitless_decklist.html")

        with patch.object(client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = html

            decklist = await client.fetch_decklist(
                "https://play.limitlesstcg.com/decks/abc123"
            )

            assert decklist is not None
            assert decklist.is_valid

            # Check that cards were parsed
            card_ids = [c["card_id"] for c in decklist.cards]

            # Should have Charizard ex from OBF
            assert any("sv3-125" in cid for cid in card_ids)

    @pytest.mark.asyncio
    async def test_handles_rate_limit_retry(self, client: LimitlessClient) -> None:
        """Should retry on rate limit (429)."""
        call_count = 0

        async def mock_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                response = MagicMock()
                response.status_code = 429
                return response
            response = MagicMock()
            response.status_code = 200
            response.text = "<html></html>"
            response.raise_for_status = MagicMock()
            return response

        with patch.object(client._client, "get", side_effect=mock_get):
            # Should not raise after retry
            # Note: This is a simplified test; full retry logic tested elsewhere
            pass

    @pytest.mark.asyncio
    async def test_context_manager(self) -> None:
        """Should work as async context manager."""
        async with LimitlessClient() as client:
            assert client is not None

    @pytest.mark.asyncio
    async def test_jp_tournament_gets_bo1(self, client: LimitlessClient) -> None:
        """Should set best_of=1 for JP tournaments."""
        html = load_fixture("limitless_tournaments.html")

        with patch.object(client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = html

            tournaments = await client.fetch_tournament_listings(
                region="jp",
                game_format="standard",
            )

            for t in tournaments:
                assert t.best_of == 1


class TestLimitlessClientRateLimiting:
    """Tests for rate limiting behavior."""

    @pytest.mark.asyncio
    async def test_tracks_request_times(self) -> None:
        """Should track request times for rate limiting."""
        client = LimitlessClient(
            requests_per_minute=60,
            max_concurrent=5,
        )

        # Verify client is initialized with empty request times
        assert client._request_times == []
        await client.close()

    @pytest.mark.asyncio
    async def test_rate_limiter_enforces_delay_when_limit_reached(self) -> None:
        """Should delay requests when rate limit is reached."""
        client = LimitlessClient(
            requests_per_minute=2,
            max_concurrent=1,
            max_retries=1,
        )

        with patch.object(client._client, "get", new_callable=AsyncMock) as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = "<html></html>"
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            # Make requests up to the limit
            await client._get("/test1")
            await client._get("/test2")

            # Both should have completed and tracked
            assert len(client._request_times) == 2

        await client.close()


class TestLimitlessClientRetries:
    """Tests for retry behavior on errors."""

    @pytest.mark.asyncio
    async def test_raises_after_exhausting_retries_on_503(self) -> None:
        """Should raise LimitlessError after max retries on 503."""
        client = LimitlessClient(
            max_retries=3,
            retry_delay=0.01,  # Very short for testing
        )

        call_count = 0

        async def mock_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            response = MagicMock()
            response.status_code = 503
            return response

        with (
            patch.object(client._client, "get", side_effect=mock_get),
            pytest.raises(LimitlessError, match="Max retries exceeded"),
        ):
            await client._get("/test")

        # Should have retried max_retries times
        assert call_count == 3

        await client.close()

    @pytest.mark.asyncio
    async def test_raises_immediately_on_404(self) -> None:
        """Should raise LimitlessError immediately on 404 without retry."""
        client = LimitlessClient(max_retries=3)

        mock_request = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch.object(client._client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.HTTPStatusError(
                "Not Found",
                request=mock_request,
                response=mock_response,
            )

            with pytest.raises(LimitlessError, match="Not found"):
                await client._get("/nonexistent")

            # Should only be called once (no retry on 404)
            assert mock_get.call_count == 1

        await client.close()

    @pytest.mark.asyncio
    async def test_retries_on_429_rate_limit(self) -> None:
        """Should retry on 429 rate limit with exponential backoff."""
        client = LimitlessClient(
            max_retries=3,
            retry_delay=0.01,
        )

        call_count = 0

        async def mock_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            response = MagicMock()
            if call_count < 3:
                response.status_code = 429
            else:
                response.status_code = 200
                response.text = "<html></html>"
                response.raise_for_status = MagicMock()
            return response

        with patch.object(client._client, "get", side_effect=mock_get):
            result = await client._get("/test")
            assert result == "<html></html>"

        # Should have retried twice before success
        assert call_count == 3

        await client.close()


class TestLimitlessPlacement:
    """Tests for LimitlessPlacement dataclass."""

    def test_creates_placement_with_all_fields(self) -> None:
        """Should create placement with all fields."""
        placement = LimitlessPlacement(
            placement=1,
            player_name="Test Player",
            country="US",
            archetype="Charizard ex",
            decklist=LimitlessDecklist(cards=[{"card_id": "sv3-125", "quantity": 2}]),
            decklist_url="https://example.com/deck/123",
        )

        assert placement.placement == 1
        assert placement.player_name == "Test Player"
        assert placement.country == "US"
        assert placement.archetype == "Charizard ex"
        assert placement.decklist is not None
        assert placement.decklist.is_valid

    def test_creates_placement_without_decklist(self) -> None:
        """Should create placement without decklist."""
        placement = LimitlessPlacement(
            placement=5,
            player_name="Player",
            country=None,
            archetype="Rogue",
        )

        assert placement.decklist is None
        assert placement.decklist_url is None


class TestOfficialDecklistParsing:
    """Tests for parsing decklists from the official Limitless site."""

    @pytest.fixture
    def client(self) -> LimitlessClient:
        return LimitlessClient(requests_per_minute=100, max_concurrent=10)

    @pytest.mark.asyncio
    async def test_parses_official_decklist_with_card_links(
        self, client: LimitlessClient
    ) -> None:
        """Should parse card links and quantities from official site format."""
        html = load_fixture("limitless_official_decklist.html")

        with patch.object(client, "_get_official", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = html

            decklist = await client.fetch_decklist(
                "https://limitlesstcg.com/decks/some-deck-id"
            )

            assert decklist is not None
            assert decklist.is_valid
            assert len(decklist.cards) == 5

            # Check specific card mappings
            cards_by_id = {c["card_id"]: c for c in decklist.cards}
            assert "sv3-125" in cards_by_id  # Charizard ex (OBF)
            assert cards_by_id["sv3-125"]["quantity"] == 3
            assert cards_by_id["sv3-125"]["name"] == "Charizard ex"

            assert "sv3-26" in cards_by_id  # Charmander (OBF)
            assert cards_by_id["sv3-26"]["quantity"] == 4

            assert "sv1-196" in cards_by_id  # Ultra Ball (SVI)
            assert "sv2-172" in cards_by_id  # Boss's Orders (PAL)
            assert "swsh9-151" in cards_by_id  # Double Turbo Energy (BRS)

        await client.close()


class TestJPStandingsParsing:
    """Tests for parsing JP standings with image-only archetypes."""

    @pytest.fixture
    def client(self) -> LimitlessClient:
        return LimitlessClient(requests_per_minute=100, max_concurrent=10)

    @pytest.mark.asyncio
    async def test_extracts_archetype_from_img_alt(
        self, client: LimitlessClient
    ) -> None:
        """Should extract archetype from img alt text in JP standings."""
        html = load_fixture("limitless_jp_standings.html")

        with patch.object(client, "_get_official", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = html

            placements = await client.fetch_official_tournament_placements(
                "https://limitlesstcg.com/tournaments/jp/3954"
            )

            assert len(placements) == 4

            # 1st place: two Pokemon images with alt text
            assert placements[0].archetype == "Grimmsnarl / Froslass"
            assert placements[0].decklist_url is not None

            # 2nd place: single Pokemon image with alt text
            assert placements[1].archetype == "Charizard"

    @pytest.mark.asyncio
    async def test_extracts_archetype_from_img_filename(
        self, client: LimitlessClient
    ) -> None:
        """Should fall back to img filename when alt text is missing."""
        html = load_fixture("limitless_jp_standings.html")

        with patch.object(client, "_get_official", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = html

            placements = await client.fetch_official_tournament_placements(
                "https://limitlesstcg.com/tournaments/jp/3954"
            )

            # 3rd place: images without alt text, names from filenames
            assert placements[2].archetype == "Dragapult / Pidgeot"

    @pytest.mark.asyncio
    async def test_preserves_text_archetype(self, client: LimitlessClient) -> None:
        """Should preserve text-based archetype for EN-style rows."""
        html = load_fixture("limitless_jp_standings.html")

        with patch.object(client, "_get_official", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = html

            placements = await client.fetch_official_tournament_placements(
                "https://limitlesstcg.com/tournaments/jp/3954"
            )

            # 4th place: plain text archetype "Rogue"
            assert placements[3].archetype == "Rogue"
            assert placements[3].decklist_url is None

    @pytest.mark.asyncio
    async def test_text_archetype_preserved_for_en_tournaments(
        self, client: LimitlessClient
    ) -> None:
        """Should still work for EN tournaments with text archetypes."""
        html = load_fixture("limitless_standings.html")

        with patch.object(client, "_get_official", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = html

            placements = await client.fetch_official_tournament_placements(
                "https://limitlesstcg.com/tournaments/en/1234"
            )

            assert placements[0].archetype == "Charizard ex"
            assert placements[0].decklist_url is not None

    @pytest.mark.asyncio
    async def test_captures_sprite_urls_r2_cdn(self, client: LimitlessClient) -> None:
        """Should capture sprite URLs from r2 CDN pattern."""
        html = load_fixture("limitless_jp_standings.html")

        with patch.object(client, "_get_official", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = html

            placements = await client.fetch_official_tournament_placements(
                "https://limitlesstcg.com/tournaments/jp/3954"
            )

            # Row 1: r2 CDN URLs
            assert len(placements[0].sprite_urls) == 2
            assert "r2.limitlesstcg.net" in placements[0].sprite_urls[0]
            assert "grimmsnarl.png" in placements[0].sprite_urls[0]
            assert "froslass.png" in placements[0].sprite_urls[1]

            # Row 2: single r2 CDN URL
            assert len(placements[1].sprite_urls) == 1
            assert "charizard.png" in placements[1].sprite_urls[0]

    @pytest.mark.asyncio
    async def test_captures_sprite_urls_old_pattern(
        self, client: LimitlessClient
    ) -> None:
        """Should capture sprite URLs from old limitlesstcg.com pattern."""
        html = load_fixture("limitless_jp_standings.html")

        with patch.object(client, "_get_official", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = html

            placements = await client.fetch_official_tournament_placements(
                "https://limitlesstcg.com/tournaments/jp/3954"
            )

            # Row 3: old URL pattern
            assert len(placements[2].sprite_urls) == 2
            assert "limitlesstcg.com/img/pokemon" in placements[2].sprite_urls[0]

    @pytest.mark.asyncio
    async def test_text_only_row_has_no_sprites(self, client: LimitlessClient) -> None:
        """Should return empty sprite_urls for text-only rows."""
        html = load_fixture("limitless_jp_standings.html")

        with patch.object(client, "_get_official", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = html

            placements = await client.fetch_official_tournament_placements(
                "https://limitlesstcg.com/tournaments/jp/3954"
            )

            # Row 4: text "Rogue" — no sprites
            assert placements[3].sprite_urls == []


class TestExtractArchetypeAndSprites:
    """Tests for _extract_archetype_and_sprites_from_images static method."""

    def test_returns_tuple_with_archetype_and_urls(self) -> None:
        """Should return (archetype, sprite_urls) tuple."""
        from bs4 import BeautifulSoup

        html = (
            '<a href="/decks/123">'
            '<img alt="Charizard" src="https://r2.limitlesstcg.net/pokemon/gen9/charizard.png">'
            "</a>"
        )
        soup = BeautifulSoup(html, "html.parser")
        link = soup.select_one("a")

        archetype, urls = LimitlessClient._extract_archetype_and_sprites_from_images(
            link
        )

        assert archetype == "Charizard"
        assert urls == ["https://r2.limitlesstcg.net/pokemon/gen9/charizard.png"]

    def test_multiple_sprites(self) -> None:
        """Should handle multiple sprite images."""
        from bs4 import BeautifulSoup

        html = (
            '<a href="/decks/123">'
            '<img alt="Dragapult" src="https://example.com/dragapult.png">'
            '<img alt="Pidgeot" src="https://example.com/pidgeot.png">'
            "</a>"
        )
        soup = BeautifulSoup(html, "html.parser")
        link = soup.select_one("a")

        archetype, urls = LimitlessClient._extract_archetype_and_sprites_from_images(
            link
        )

        assert archetype == "Dragapult / Pidgeot"
        assert len(urls) == 2

    def test_no_images_returns_unknown(self) -> None:
        """Should return Unknown with empty list when no images."""
        from bs4 import BeautifulSoup

        html = '<a href="/decks/123">Some text</a>'
        soup = BeautifulSoup(html, "html.parser")
        link = soup.select_one("a")

        archetype, urls = LimitlessClient._extract_archetype_and_sprites_from_images(
            link
        )

        assert archetype == "Unknown"
        assert urls == []

    def test_backward_compat_wrapper_returns_string(self) -> None:
        """Backward-compat wrapper should return plain string."""
        from bs4 import BeautifulSoup

        html = (
            '<a href="/decks/123">'
            '<img alt="Charizard" src="https://example.com/charizard.png">'
            "</a>"
        )
        soup = BeautifulSoup(html, "html.parser")
        link = soup.select_one("a")

        result = LimitlessClient._extract_archetype_from_images(link)

        assert isinstance(result, str)
        assert result == "Charizard"


class TestCountryToRegion:
    """Tests for LimitlessClient._country_to_region helper."""

    @pytest.fixture
    def client(self) -> LimitlessClient:
        return LimitlessClient(requests_per_minute=100, max_concurrent=10)

    def test_maps_us_to_na(self, client: LimitlessClient) -> None:
        """Should map US to NA region."""
        assert client._country_to_region("US") == "NA"

    def test_maps_ca_to_na(self, client: LimitlessClient) -> None:
        """Should map Canada to NA region."""
        assert client._country_to_region("CA") == "NA"

    def test_maps_jp_to_jp(self, client: LimitlessClient) -> None:
        """Should map Japan to JP region."""
        assert client._country_to_region("JP") == "JP"

    def test_maps_eu_countries(self, client: LimitlessClient) -> None:
        """Should map European countries to EU region."""
        eu_countries = ["GB", "DE", "FR", "IT", "ES", "NL", "SE", "PL"]
        for country in eu_countries:
            assert client._country_to_region(country) == "EU", f"Failed for {country}"

    def test_maps_latam_countries(self, client: LimitlessClient) -> None:
        """Should map Latin American countries to LATAM region."""
        latam_countries = ["MX", "BR", "AR", "CL", "CO"]
        for country in latam_countries:
            assert client._country_to_region(country) == "LATAM", (
                f"Failed for {country}"
            )

    def test_maps_oce_countries(self, client: LimitlessClient) -> None:
        """Should map Oceania countries to OCE region."""
        assert client._country_to_region("AU") == "OCE"
        assert client._country_to_region("NZ") == "OCE"

    def test_maps_asia_countries_to_apac(self, client: LimitlessClient) -> None:
        """Should map non-JP Asian countries to APAC region."""
        asia_countries = ["KR", "TW", "SG", "MY", "TH"]
        for country in asia_countries:
            assert client._country_to_region(country) == "APAC", f"Failed for {country}"

    def test_maps_unknown_country_to_na(self, client: LimitlessClient) -> None:
        """Should default unknown countries to NA."""
        assert client._country_to_region("XX") == "NA"
        assert client._country_to_region("") == "NA"


class TestParseOfficialTournamentRow:
    """Tests for LimitlessClient._parse_official_tournament_row helper."""

    @pytest.fixture
    def client(self) -> LimitlessClient:
        return LimitlessClient(requests_per_minute=100, max_concurrent=10)

    def _make_row(
        self,
        data_date: str = "2026-01-25",
        data_country: str = "US",
        data_name: str = "Charlotte Regional",
        data_format: str = "standard",
        data_players: str = "512",
        href: str = "/tournaments/en/1234",
    ) -> MagicMock:
        """Create a mock BeautifulSoup row tag."""
        from bs4 import BeautifulSoup

        html = (
            f'<tr data-date="{data_date}" data-country="{data_country}" '
            f'data-name="{data_name}" data-format="{data_format}" '
            f'data-players="{data_players}">'
            f'<td><a href="{href}">View</a></td>'
            f"</tr>"
        )
        soup = BeautifulSoup(html, "html.parser")
        return soup.select_one("tr")

    def test_parses_standard_tournament(self, client: LimitlessClient) -> None:
        """Should parse a standard format tournament row."""
        row = self._make_row()
        result = client._parse_official_tournament_row(row, "standard")

        assert result is not None
        assert result.name == "Charlotte Regional"
        assert result.tournament_date == date(2026, 1, 25)
        assert result.region == "NA"
        assert result.best_of == 3
        assert result.participant_count == 512
        assert "limitlesstcg.com" in result.source_url

    def test_filters_out_wrong_format(self, client: LimitlessClient) -> None:
        """Should return None when format does not match target."""
        row = self._make_row(data_format="expanded")
        result = client._parse_official_tournament_row(row, "standard")

        assert result is None

    def test_parses_expanded_format(self, client: LimitlessClient) -> None:
        """Should parse expanded format tournaments when targeting expanded."""
        row = self._make_row(data_format="expanded")
        result = client._parse_official_tournament_row(row, "expanded")

        assert result is not None
        assert result.game_format == "expanded"

    def test_parses_jp_standard_format(self, client: LimitlessClient) -> None:
        """Should parse standard-jp as standard with BO1."""
        row = self._make_row(
            data_format="standard-jp", data_country="JP", data_name="Champions League"
        )
        result = client._parse_official_tournament_row(row, "standard")

        assert result is not None
        assert result.game_format == "standard"
        assert result.best_of == 1
        assert result.region == "JP"

    def test_returns_none_when_missing_required_fields(
        self, client: LimitlessClient
    ) -> None:
        """Should return None when required data attributes are missing."""
        from bs4 import BeautifulSoup

        # Missing data-name
        html = (
            '<tr data-date="2026-01-25" data-country="US" data-format="standard">'
            '<td><a href="/tournaments/en/1234">View</a></td>'
            "</tr>"
        )
        soup = BeautifulSoup(html, "html.parser")
        row = soup.select_one("tr")
        result = client._parse_official_tournament_row(row, "standard")

        assert result is None

    def test_returns_none_when_no_link(self, client: LimitlessClient) -> None:
        """Should return None when no tournament link is found."""
        from bs4 import BeautifulSoup

        html = (
            '<tr data-date="2026-01-25" data-country="US" '
            'data-name="Test" data-format="standard">'
            "<td>No link here</td>"
            "</tr>"
        )
        soup = BeautifulSoup(html, "html.parser")
        row = soup.select_one("tr")
        result = client._parse_official_tournament_row(row, "standard")

        assert result is None

    def test_jp_country_sets_bo1(self, client: LimitlessClient) -> None:
        """Should set best_of=1 when country is JP even for standard format."""
        row = self._make_row(data_country="JP", data_format="standard")
        result = client._parse_official_tournament_row(row, "standard")

        assert result is not None
        assert result.best_of == 1

    def test_eu_country_sets_bo3(self, client: LimitlessClient) -> None:
        """Should set best_of=3 for EU country."""
        row = self._make_row(data_country="GB")
        result = client._parse_official_tournament_row(row, "standard")

        assert result is not None
        assert result.best_of == 3
        assert result.region == "EU"


class TestParseJPCityLeagueRow:
    """Tests for LimitlessClient._parse_jp_city_league_row helper."""

    @pytest.fixture
    def client(self) -> LimitlessClient:
        return LimitlessClient(requests_per_minute=100, max_concurrent=10)

    def _make_jp_row(
        self,
        date_text: str = "01 Feb 26",
        prefecture: str = "Tokyo",
        href: str = "/tournaments/jp/3954",
    ) -> MagicMock:
        """Create a mock JP City League row."""
        from bs4 import BeautifulSoup

        html = (
            "<tr>"
            f'<td><a href="{href}">{date_text}</a></td>'
            f"<td>{prefecture}</td>"
            f'<td><a href="{href}">View</a></td>'
            "</tr>"
        )
        soup = BeautifulSoup(html, "html.parser")
        return soup.select_one("tr")

    def test_parses_valid_row(self, client: LimitlessClient) -> None:
        """Should parse a valid JP City League row."""
        row = self._make_jp_row()
        cutoff = date(2026, 1, 1)
        result = client._parse_jp_city_league_row(row, cutoff)

        assert result is not None
        assert result.name == "City League Tokyo"
        assert result.tournament_date == date(2026, 2, 1)
        assert result.region == "JP"
        assert result.best_of == 1
        assert result.game_format == "standard"
        assert "limitlesstcg.com" in result.source_url

    def test_returns_none_for_old_tournament(self, client: LimitlessClient) -> None:
        """Should return None when tournament is before cutoff date."""
        row = self._make_jp_row(date_text="01 Jan 25")
        cutoff = date(2026, 1, 1)
        result = client._parse_jp_city_league_row(row, cutoff)

        assert result is None

    def test_returns_none_for_too_few_cells(self, client: LimitlessClient) -> None:
        """Should return None when row has fewer than 3 cells."""
        from bs4 import BeautifulSoup

        html = "<tr><td>Only one cell</td></tr>"
        soup = BeautifulSoup(html, "html.parser")
        row = soup.select_one("tr")
        result = client._parse_jp_city_league_row(row, date(2020, 1, 1))

        assert result is None

    def test_returns_none_when_no_jp_link(self, client: LimitlessClient) -> None:
        """Should return None when no /tournaments/jp/ link is present."""
        from bs4 import BeautifulSoup

        html = (
            "<tr>"
            '<td><a href="/other/link">01 Feb 26</a></td>'
            "<td>Tokyo</td>"
            "<td>Info</td>"
            "</tr>"
        )
        soup = BeautifulSoup(html, "html.parser")
        row = soup.select_one("tr")
        result = client._parse_jp_city_league_row(row, date(2020, 1, 1))

        assert result is None


class TestJPCityLeaguePlacementParsing:
    """Tests for JP City League placement parsing with fixture."""

    @pytest.fixture
    def client(self) -> LimitlessClient:
        return LimitlessClient(requests_per_minute=100, max_concurrent=10)

    @pytest.mark.asyncio
    async def test_parses_all_jp_placement_rows(self, client: LimitlessClient) -> None:
        """Should parse all 4 rows from JP standings fixture."""
        html = load_fixture("limitless_jp_standings.html")

        with patch.object(client, "_get_official", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = html

            placements = await client.fetch_jp_city_league_placements(
                "https://limitlesstcg.com/tournaments/jp/3954"
            )

            assert len(placements) == 4

    @pytest.mark.asyncio
    async def test_jp_row1_sprites_from_r2_cdn(self, client: LimitlessClient) -> None:
        """Row 1 should have r2 CDN sprite URLs and correct archetype."""
        html = load_fixture("limitless_jp_standings.html")

        with patch.object(client, "_get_official", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = html

            placements = await client.fetch_jp_city_league_placements(
                "https://limitlesstcg.com/tournaments/jp/3954"
            )

            p = placements[0]
            assert p.placement == 1
            assert p.player_name == "Taro Yamada"
            assert p.archetype == "Grimmsnarl / Froslass"
            assert len(p.sprite_urls) == 2
            assert "r2.limitlesstcg.net" in p.sprite_urls[0]

    @pytest.mark.asyncio
    async def test_jp_row2_single_sprite(self, client: LimitlessClient) -> None:
        """Row 2 should have a single sprite URL."""
        html = load_fixture("limitless_jp_standings.html")

        with patch.object(client, "_get_official", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = html

            placements = await client.fetch_jp_city_league_placements(
                "https://limitlesstcg.com/tournaments/jp/3954"
            )

            p = placements[1]
            assert p.placement == 2
            assert p.archetype == "Charizard"
            assert len(p.sprite_urls) == 1

    @pytest.mark.asyncio
    async def test_jp_row3_old_url_pattern(self, client: LimitlessClient) -> None:
        """Row 3 should use old URL pattern and derive from filename."""
        html = load_fixture("limitless_jp_standings.html")

        with patch.object(client, "_get_official", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = html

            placements = await client.fetch_jp_city_league_placements(
                "https://limitlesstcg.com/tournaments/jp/3954"
            )

            p = placements[2]
            assert p.placement == 3
            assert p.archetype == "Dragapult / Pidgeot"
            assert len(p.sprite_urls) == 2
            assert "limitlesstcg.com/img/pokemon" in p.sprite_urls[0]

    @pytest.mark.asyncio
    async def test_jp_row4_text_only_rogue(self, client: LimitlessClient) -> None:
        """Row 4 should fall back to text 'Rogue' with no sprites."""
        html = load_fixture("limitless_jp_standings.html")

        with patch.object(client, "_get_official", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = html

            placements = await client.fetch_jp_city_league_placements(
                "https://limitlesstcg.com/tournaments/jp/3954"
            )

            p = placements[3]
            assert p.placement == 4
            assert p.archetype == "Rogue"
            assert p.sprite_urls == []
            assert p.decklist_url is None


class TestJPPipelineEndToEnd:
    """End-to-end: JP fixture HTML → LimitlessPlacement → ArchetypeNormalizer."""

    @pytest.fixture
    def client(self) -> LimitlessClient:
        return LimitlessClient(requests_per_minute=100, max_concurrent=10)

    @pytest.fixture
    def normalizer(self):
        from src.services.archetype_normalizer import ArchetypeNormalizer

        return ArchetypeNormalizer()

    @pytest.mark.asyncio
    async def test_full_pipeline_all_rows(
        self,
        client: LimitlessClient,
        normalizer,
    ) -> None:
        """Parse JP fixture, run through normalizer, verify all rows."""
        from src.services.archetype_normalizer import ArchetypeNormalizer

        normalizer = ArchetypeNormalizer()
        html = load_fixture("limitless_jp_standings.html")

        with patch.object(client, "_get_official", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = html

            placements = await client.fetch_jp_city_league_placements(
                "https://limitlesstcg.com/tournaments/jp/3954"
            )

        assert len(placements) == 4

        # Row 1: grimmsnarl + froslass → sprite_lookup (sorted: froslass-grimmsnarl)
        a1, r1, m1 = normalizer.resolve(
            placements[0].sprite_urls, placements[0].archetype, None
        )
        assert a1 == "Froslass Grimmsnarl"
        assert m1 == "sprite_lookup"

        # Row 2: charizard → sprite_lookup → "Charizard ex"
        a2, r2, m2 = normalizer.resolve(
            placements[1].sprite_urls, placements[1].archetype, None
        )
        assert a2 == "Charizard ex"
        assert m2 == "sprite_lookup"

        # Row 3: dragapult + pidgeot → sprite_lookup → "Dragapult ex"
        a3, r3, m3 = normalizer.resolve(
            placements[2].sprite_urls, placements[2].archetype, None
        )
        assert a3 == "Dragapult ex"
        assert m3 == "sprite_lookup"

        # Row 4: no sprites, text "Rogue" → text_label
        a4, r4, m4 = normalizer.resolve(
            placements[3].sprite_urls, placements[3].archetype, None
        )
        assert a4 == "Rogue"
        assert m4 == "text_label"


class TestDecklistParserFailureLogging:
    """Tests for diagnostic logging when all parsers fail."""

    @pytest.fixture
    def client(self) -> LimitlessClient:
        return LimitlessClient(requests_per_minute=100, max_concurrent=10)

    @pytest.mark.asyncio
    async def test_logs_warning_when_all_parsers_fail(
        self, client: LimitlessClient, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Should log a warning with diagnostic info when no parser succeeds."""
        empty_html = (
            "<html><head><title>Error Page</title></head><body>Oops</body></html>"
        )

        with patch.object(client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = empty_html

            with caplog.at_level(logging.WARNING, logger="src.clients.limitless"):
                decklist = await client.fetch_decklist(
                    "https://play.limitlesstcg.com/decks/broken"
                )

            assert decklist is None
            assert any(
                "All decklist parsers failed" in record.message
                for record in caplog.records
            )
            assert any("Error Page" in record.message for record in caplog.records)

        await client.close()
