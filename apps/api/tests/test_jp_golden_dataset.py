"""Golden dataset tests for JP archetype pipeline.

End-to-end validation: HTML parsing → sprite extraction →
ArchetypeNormalizer resolution → correct archetype + detection method.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from src.clients.limitless import LimitlessClient
from src.services.archetype_normalizer import ArchetypeNormalizer

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "jp_tournaments"


def load_fixture(name: str) -> str:
    """Load an HTML fixture file."""
    return (FIXTURES_DIR / name).read_text()


def load_expected_results() -> dict:
    """Load expected results JSON."""
    return json.loads((FIXTURES_DIR / "expected_results.json").read_text())


EXPECTED = load_expected_results()
FIXTURE_FILES = list(EXPECTED.keys())


class TestJPGoldenDataset:
    """Golden dataset: HTML → sprite extraction → normalizer."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("fixture_file", FIXTURE_FILES)
    async def test_sprite_extraction_accuracy(
        self,
        fixture_file: str,
    ) -> None:
        """Sprite URLs are correctly extracted from fixture HTML."""
        html = load_fixture(fixture_file)
        expected = EXPECTED[fixture_file]

        async with LimitlessClient() as client:
            with patch.object(
                client,
                "_get_official",
                new_callable=AsyncMock,
            ) as mock_get:
                mock_get.return_value = html
                url = "https://play.limitlesstcg.com/tournaments/jp/test"
                placements = await client.fetch_jp_city_league_placements(url)

        assert len(placements) == len(expected)

        for placement, exp in zip(placements, expected, strict=True):
            assert placement.placement == exp["placement"], (
                f"Placement {exp['placement']}: wrong rank {placement.placement}"
            )
            assert len(placement.sprite_urls) == exp["sprite_count"], (
                f"Placement {exp['placement']}: "
                f"expected {exp['sprite_count']} sprites, "
                f"got {len(placement.sprite_urls)}"
            )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("fixture_file", FIXTURE_FILES)
    async def test_archetype_resolution(
        self,
        fixture_file: str,
    ) -> None:
        """Sprite URLs resolve to correct archetype via normalizer."""
        html = load_fixture(fixture_file)
        expected = EXPECTED[fixture_file]
        normalizer = ArchetypeNormalizer()

        async with LimitlessClient() as client:
            with patch.object(
                client,
                "_get_official",
                new_callable=AsyncMock,
            ) as mock_get:
                mock_get.return_value = html
                url = "https://play.limitlesstcg.com/tournaments/jp/test"
                placements = await client.fetch_jp_city_league_placements(url)

        for placement, exp in zip(placements, expected, strict=True):
            archetype, _raw, _method = normalizer.resolve(
                placement.sprite_urls,
                placement.archetype,
            )
            assert archetype == exp["archetype"], (
                f"Placement {exp['placement']}: "
                f"expected '{exp['archetype']}', "
                f"got '{archetype}'"
            )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("fixture_file", FIXTURE_FILES)
    async def test_detection_method_tracking(
        self,
        fixture_file: str,
    ) -> None:
        """Detection method matches expected provenance."""
        html = load_fixture(fixture_file)
        expected = EXPECTED[fixture_file]
        normalizer = ArchetypeNormalizer()

        async with LimitlessClient() as client:
            with patch.object(
                client,
                "_get_official",
                new_callable=AsyncMock,
            ) as mock_get:
                mock_get.return_value = html
                url = "https://play.limitlesstcg.com/tournaments/jp/test"
                placements = await client.fetch_jp_city_league_placements(url)

        for placement, exp in zip(placements, expected, strict=True):
            _archetype, _raw, method = normalizer.resolve(
                placement.sprite_urls,
                placement.archetype,
            )
            assert method == exp["detection_method"], (
                f"Placement {exp['placement']}: "
                f"expected method '{exp['detection_method']}', "
                f"got '{method}'"
            )


class TestCinderaceRegression:
    """Cinderace sprites must NOT produce 'Rogue'."""

    def test_cinderace_sprite_not_rogue(self) -> None:
        """Single cinderace sprite → 'Cinderace ex', not 'Rogue'."""
        normalizer = ArchetypeNormalizer()
        archetype, _raw, method = normalizer.resolve(
            [
                "https://r2.limitlesstcg.net/pokemon/gen9/cinderace.png",
            ],
            "Unknown",
        )
        assert archetype == "Cinderace ex"
        assert method == "sprite_lookup"
        assert archetype != "Rogue"

    def test_cinderace_with_partner(self) -> None:
        """Cinderace + Moltres → auto_derive, not 'Rogue'."""
        normalizer = ArchetypeNormalizer()
        archetype, _raw, method = normalizer.resolve(
            [
                "https://r2.limitlesstcg.net/pokemon/gen9/cinderace.png",
                "https://r2.limitlesstcg.net/pokemon/gen9/moltres.png",
            ],
            "Unknown",
        )
        assert archetype == "Cinderace Moltres"
        assert method == "auto_derive"
        assert archetype != "Rogue"

    def test_cinderace_in_golden_dataset(self) -> None:
        """Cinderace placements in Tokyo fixture are correct."""
        html = load_fixture("city_league_tokyo_2025.html")
        normalizer = ArchetypeNormalizer()
        client = LimitlessClient()

        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "lxml")
        table = soup.select_one("table.striped")
        assert table is not None
        rows = table.select("tbody tr")

        # Placement 5: single Cinderace
        p5 = client._parse_jp_placement_row(rows[4])
        assert p5 is not None
        arch, _raw, method = normalizer.resolve(p5.sprite_urls, p5.archetype)
        assert arch == "Cinderace ex"
        assert method == "sprite_lookup"

        # Placement 6: Cinderace + Moltres
        p6 = client._parse_jp_placement_row(rows[5])
        assert p6 is not None
        arch, _raw, method = normalizer.resolve(p6.sprite_urls, p6.archetype)
        assert arch == "Cinderace Moltres"
        assert method == "auto_derive"
