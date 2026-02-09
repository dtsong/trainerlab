"""Tests for data quality: archetype names, tier classification, and normalization.

These tests encode data quality expectations discovered from production data analysis.
Each test targets a specific issue found in the live dataset.
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from bs4 import BeautifulSoup

from src.clients.limitless import LimitlessClient
from src.data.signature_cards import normalize_archetype
from src.models import TournamentPlacement
from src.services.meta_service import MetaService

# ---------------------------------------------------------------------------
# Issue 1: Empty archetype names must never reach the database
# ---------------------------------------------------------------------------


class TestGrassrootsParserEmptyArchetype:
    """Grassroots parser must fall back to 'Unknown' when link text is empty."""

    def _make_client(self) -> LimitlessClient:
        """Create a LimitlessClient for unit-testing parsers."""
        client = LimitlessClient.__new__(LimitlessClient)
        client.BASE_URL = "https://play.limitlesstcg.com"
        client.OFFICIAL_BASE_URL = "https://limitlesstcg.com"
        return client

    def test_empty_link_text_falls_back_to_unknown(self) -> None:
        """When archetype link exists but has no text, archetype should be 'Unknown'."""
        html = """
        <tr>
            <td>1</td>
            <td><a href="/player/p1">Alice</a></td>
            <td><a href="/decks/d1"></a></td>
        </tr>
        """
        row = BeautifulSoup(html, "lxml").select_one("tr")
        client = self._make_client()
        placement = client._parse_placement_row(row)

        assert placement is not None
        assert placement.archetype != "", "Empty archetype must not propagate"
        assert placement.archetype == "Unknown"

    def test_whitespace_only_link_text_falls_back_to_unknown(self) -> None:
        """When archetype link text is whitespace-only, should fall back."""
        html = """
        <tr>
            <td>1</td>
            <td><a href="/player/p1">Alice</a></td>
            <td><a href="/decks/d1">   </a></td>
        </tr>
        """
        row = BeautifulSoup(html, "lxml").select_one("tr")
        client = self._make_client()
        placement = client._parse_placement_row(row)

        assert placement is not None
        assert placement.archetype != ""
        assert placement.archetype == "Unknown"


class TestOfficialParserEmptyArchetype:
    """Official parser must never produce empty archetype strings."""

    def _make_client(self) -> LimitlessClient:
        client = LimitlessClient.__new__(LimitlessClient)
        client.BASE_URL = "https://play.limitlesstcg.com"
        client.OFFICIAL_BASE_URL = "https://limitlesstcg.com"
        return client

    def test_deck_link_with_no_text_and_no_images(self) -> None:
        """Deck link with no text and no images should produce 'Unknown'."""
        html = """
        <tr>
            <td>1</td>
            <td><a href="/player/jp001">Taro</a></td>
            <td><a href="/decks/d1"></a></td>
        </tr>
        """
        row = BeautifulSoup(html, "lxml").select_one("tr")
        client = self._make_client()
        placement = client._parse_official_placement_row(row)

        assert placement is not None
        assert placement.archetype != ""
        assert placement.archetype == "Unknown"

    def test_deck_link_with_images_missing_alt_and_src(self) -> None:
        """Images without alt/filename should produce 'Unknown'."""
        html = """
        <tr>
            <td>1</td>
            <td><a href="/player/jp001">Taro</a></td>
            <td>
                <a href="/decks/d1">
                    <img alt="" src="https://example.com/images/blob/12345">
                    <img src="https://example.com/images/blob/67890">
                </a>
            </td>
        </tr>
        """
        row = BeautifulSoup(html, "lxml").select_one("tr")
        client = self._make_client()
        placement = client._parse_official_placement_row(row)

        assert placement is not None
        assert placement.archetype != ""
        assert placement.archetype == "Unknown"


class TestExtractArchetypeFromImages:
    """Image-based archetype extraction edge cases."""

    def test_empty_alt_text_falls_back_to_filename(self) -> None:
        """Empty alt attribute should try filename extraction."""
        html = '<a href="/decks/d1"><img alt="" src="/img/pokemon/charizard.png"></a>'
        tag = BeautifulSoup(html, "lxml").select_one("a")
        result = LimitlessClient._extract_archetype_from_images(tag)

        assert result == "Charizard"

    def test_no_images_returns_unknown(self) -> None:
        """Link with no images should return 'Unknown'."""
        html = '<a href="/decks/d1">   </a>'
        tag = BeautifulSoup(html, "lxml").select_one("a")
        result = LimitlessClient._extract_archetype_from_images(tag)

        assert result == "Unknown"

    def test_unextractable_src_returns_unknown(self) -> None:
        """Image with non-standard src pattern should return 'Unknown'."""
        html = '<a href="/decks/d1"><img alt="" src="data:image/png;base64,abc"></a>'
        tag = BeautifulSoup(html, "lxml").select_one("a")
        result = LimitlessClient._extract_archetype_from_images(tag)

        assert result == "Unknown"


# ---------------------------------------------------------------------------
# Issue 2: Meta computation must not propagate empty archetype names
# ---------------------------------------------------------------------------


class TestMetaArchetypeSharesDataQuality:
    """Meta snapshot computation must filter out empty/blank archetype names."""

    @pytest.fixture
    def service(self) -> MetaService:
        return MetaService(AsyncMock())

    def test_empty_archetype_excluded_from_shares(self, service: MetaService) -> None:
        """Placements with empty archetype string must not appear in shares."""
        t1, t2, t3 = uuid4(), uuid4(), uuid4()
        placements = []
        for archetype, tid in [
            ("Charizard ex", t1),
            ("Charizard ex", t2),
            ("Charizard ex", t3),
            ("", t1),
            ("", t2),
            ("Lugia VSTAR", t1),
            ("Lugia VSTAR", t2),
            ("Lugia VSTAR", t3),
        ]:
            p = MagicMock(spec=TournamentPlacement)
            p.archetype = archetype
            p.tournament_id = tid
            placements.append(p)

        shares = service._compute_archetype_shares(placements)

        assert "" not in shares, "Empty archetype must not appear in meta shares"
        assert "Charizard ex" in shares
        assert "Lugia VSTAR" in shares

    def test_whitespace_archetype_excluded_from_shares(
        self, service: MetaService
    ) -> None:
        """Placements with whitespace-only archetype must be excluded."""
        t1, t2, t3 = uuid4(), uuid4(), uuid4()
        placements = []
        for tid in [t1, t2, t3]:
            p = MagicMock(spec=TournamentPlacement)
            p.archetype = "Dragapult ex"
            p.tournament_id = tid
            placements.append(p)
        p = MagicMock(spec=TournamentPlacement)
        p.archetype = "   "
        p.tournament_id = t1
        placements.append(p)

        shares = service._compute_archetype_shares(placements)

        assert "" not in shares
        assert "   " not in shares

    def test_shares_sum_to_one_after_filtering(self, service: MetaService) -> None:
        """Shares should still sum to ~1.0 after filtering empty archetypes."""
        t1, t2, t3 = uuid4(), uuid4(), uuid4()
        placements = []
        # A in 3 tournaments, B in 3 tournaments, empty in 1
        for tid in [t1, t2, t3]:
            p = MagicMock(spec=TournamentPlacement)
            p.archetype = "A"
            p.tournament_id = tid
            placements.append(p)
        for tid in [t1, t2, t3]:
            p = MagicMock(spec=TournamentPlacement)
            p.archetype = "B"
            p.tournament_id = tid
            placements.append(p)
        p = MagicMock(spec=TournamentPlacement)
        p.archetype = ""
        p.tournament_id = t1
        placements.append(p)

        shares = service._compute_archetype_shares(placements)

        # After filtering empty, only A (3) and B (3) remain
        total = sum(shares.values())
        assert abs(total - 1.0) < 0.01, f"Shares sum to {total}, expected ~1.0"


# ---------------------------------------------------------------------------
# Issue 3: Archetype normalization must be case-insensitive
# ---------------------------------------------------------------------------


class TestArchetypeNormalizationCasing:
    """normalize_archetype should handle common case variations."""

    def test_lowercase_alias_matches(self) -> None:
        """Lowercase version of known alias should normalize correctly."""
        # "Dragapult" is in ARCHETYPE_ALIASES → "Dragapult ex"
        assert normalize_archetype("dragapult") == "Dragapult ex"

    def test_mixed_case_alias_matches(self) -> None:
        """Mixed case version of known alias should normalize correctly."""
        assert normalize_archetype("DRAGAPULT") == "Dragapult ex"

    def test_unknown_archetype_preserved(self) -> None:
        """Unknown archetype names should be returned as-is."""
        assert normalize_archetype("Some Random Deck") == "Some Random Deck"

    def test_empty_string_returns_unknown(self) -> None:
        """Empty string should normalize to 'Unknown', not stay empty."""
        result = normalize_archetype("")
        assert result != "", "Empty string must not pass through normalization"
        assert result == "Unknown"

    def test_whitespace_only_returns_unknown(self) -> None:
        """Whitespace-only should normalize to 'Unknown'."""
        result = normalize_archetype("   ")
        assert result != "   "
        assert result == "Unknown"


# ---------------------------------------------------------------------------
# Issue 4: Tournament tier should be classified from tournament metadata
# ---------------------------------------------------------------------------


class TestTournamentTierClassification:
    """Tournament tier should be derived from participant count or name patterns."""

    def test_large_tournament_gets_major_tier(self) -> None:
        """Tournaments with 256+ participants should be classified as 'major'."""
        from src.services.tournament_scrape import TournamentScrapeService

        # We test that the tier classification function produces correct tiers
        assert (
            TournamentScrapeService.classify_tier(
                participant_count=512, name="Regional Championship"
            )
            == "major"
        )

    def test_medium_tournament_gets_premier_tier(self) -> None:
        """Tournaments with 64-255 participants should be 'premier'."""
        from src.services.tournament_scrape import TournamentScrapeService

        assert (
            TournamentScrapeService.classify_tier(
                participant_count=128, name="League Challenge"
            )
            == "premier"
        )

    def test_small_tournament_gets_league_tier(self) -> None:
        """Tournaments with <64 participants should be 'league'."""
        from src.services.tournament_scrape import TournamentScrapeService

        assert (
            TournamentScrapeService.classify_tier(
                participant_count=32, name="Weekly Tournament"
            )
            == "league"
        )

    def test_zero_participant_count_uses_name_pattern(self) -> None:
        """When participant count is 0 (JP), tier should be inferred from name."""
        from src.services.tournament_scrape import TournamentScrapeService

        result = TournamentScrapeService.classify_tier(
            participant_count=0, name="City League Tokyo"
        )
        assert result is not None, (
            "JP tournaments with 0 participants still need a tier"
        )


# ---------------------------------------------------------------------------
# Issue 5: validate_placement() fail-open quality checks
# ---------------------------------------------------------------------------


class TestValidatePlacement:
    """Tests for src.services.data_quality.validate_placement()."""

    def _make_placement(
        self,
        archetype: str = "Charizard ex",
        raw_archetype_sprites: list[str] | None = None,
        archetype_confidence: float | None = None,
        archetype_detection_method: str | None = None,
    ) -> MagicMock:
        p = MagicMock()
        p.archetype = archetype
        p.raw_archetype_sprites = raw_archetype_sprites
        p.archetype_confidence = archetype_confidence
        p.archetype_detection_method = archetype_detection_method
        return p

    def test_clean_placement_returns_no_warnings(self) -> None:
        from src.services.data_quality import validate_placement

        p = self._make_placement(
            archetype="Charizard ex",
            archetype_confidence=0.9,
            archetype_detection_method="sprite_lookup",
        )
        assert validate_placement(p) == []

    def test_sprites_present_but_unknown(self) -> None:
        from src.services.data_quality import validate_placement

        p = self._make_placement(
            archetype="Unknown",
            raw_archetype_sprites=["charizard", "pidgeot"],
        )
        warnings = validate_placement(p)
        assert len(warnings) == 1
        assert "sprites_present_but_unknown" in warnings[0]

    def test_low_confidence(self) -> None:
        from src.services.data_quality import validate_placement

        p = self._make_placement(archetype_confidence=0.3)
        warnings = validate_placement(p)
        assert len(warnings) == 1
        assert "low_confidence" in warnings[0]
        assert "0.3" in warnings[0]

    def test_text_label_with_sprites(self) -> None:
        from src.services.data_quality import validate_placement

        p = self._make_placement(
            archetype_detection_method="text_label",
            raw_archetype_sprites=["gardevoir"],
        )
        warnings = validate_placement(p)
        assert len(warnings) == 1
        assert "text_label_with_sprites" in warnings[0]

    def test_multiple_warnings_combined(self) -> None:
        from src.services.data_quality import validate_placement

        p = self._make_placement(
            archetype="Unknown",
            raw_archetype_sprites=["charizard"],
            archetype_confidence=0.2,
            archetype_detection_method="text_label",
        )
        warnings = validate_placement(p)
        assert len(warnings) == 3
        types = {w.split(":")[0] for w in warnings}
        assert types == {
            "sprites_present_but_unknown",
            "low_confidence",
            "text_label_with_sprites",
        }

    def test_confidence_exactly_half_no_warning(self) -> None:
        from src.services.data_quality import validate_placement

        p = self._make_placement(archetype_confidence=0.5)
        assert validate_placement(p) == []

    def test_confidence_just_below_half_warns(self) -> None:
        from src.services.data_quality import validate_placement

        p = self._make_placement(archetype_confidence=0.49)
        warnings = validate_placement(p)
        assert len(warnings) == 1
        assert "low_confidence" in warnings[0]

    def test_none_confidence_no_warning(self) -> None:
        from src.services.data_quality import validate_placement

        p = self._make_placement(archetype_confidence=None)
        assert validate_placement(p) == []

    def test_unknown_without_sprites_no_warning(self) -> None:
        from src.services.data_quality import validate_placement

        p = self._make_placement(archetype="Unknown", raw_archetype_sprites=None)
        assert validate_placement(p) == []

    def test_text_label_without_sprites_no_warning(self) -> None:
        from src.services.data_quality import validate_placement

        p = self._make_placement(
            archetype_detection_method="text_label",
            raw_archetype_sprites=None,
        )
        assert validate_placement(p) == []

    def test_fail_open_on_none_input(self) -> None:
        from src.services.data_quality import validate_placement

        assert validate_placement(None) == []

    def test_fail_open_on_non_object_input(self) -> None:
        from src.services.data_quality import validate_placement

        assert validate_placement(42) == []

    def test_fail_open_on_string_input(self) -> None:
        from src.services.data_quality import validate_placement

        assert validate_placement("not a placement") == []

    def test_empty_sprites_list_no_warning(self) -> None:
        from src.services.data_quality import validate_placement

        p = self._make_placement(archetype="Unknown", raw_archetype_sprites=[])
        assert validate_placement(p) == []

    def test_sprite_lookup_method_no_warning(self) -> None:
        from src.services.data_quality import validate_placement

        p = self._make_placement(
            archetype="Charizard ex",
            raw_archetype_sprites=["charizard"],
            archetype_confidence=0.95,
            archetype_detection_method="sprite_lookup",
        )
        assert validate_placement(p) == []

    def test_negative_confidence_warns(self) -> None:
        from src.services.data_quality import validate_placement

        p = self._make_placement(archetype_confidence=-0.1)
        warnings = validate_placement(p)
        assert len(warnings) == 1
        assert "low_confidence" in warnings[0]
