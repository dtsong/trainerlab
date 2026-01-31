"""Tests for tournament seed script."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


class TestLoadFixtures:
    """Tests for fixtures loading."""

    def test_fixtures_file_exists(self) -> None:
        """Fixtures file should exist."""
        fixtures_path = Path(__file__).parent.parent / "fixtures" / "tournaments.json"
        assert fixtures_path.exists(), f"Fixtures file not found: {fixtures_path}"

    def test_fixtures_valid_json(self) -> None:
        """Fixtures file should be valid JSON."""
        fixtures_path = Path(__file__).parent.parent / "fixtures" / "tournaments.json"
        with open(fixtures_path) as f:
            data = json.load(f)

        assert "tournaments" in data
        assert isinstance(data["tournaments"], list)
        assert len(data["tournaments"]) > 0

    def test_fixtures_have_required_fields(self) -> None:
        """Each tournament should have required fields."""
        fixtures_path = Path(__file__).parent.parent / "fixtures" / "tournaments.json"
        with open(fixtures_path) as f:
            data = json.load(f)

        required_fields = ["name", "date", "region", "format", "best_of", "placements"]

        for tournament in data["tournaments"]:
            for field in required_fields:
                assert field in tournament, (
                    f"Missing {field} in tournament {tournament.get('name')}"
                )

    def test_fixtures_have_multiple_regions(self) -> None:
        """Fixtures should include tournaments from multiple regions."""
        fixtures_path = Path(__file__).parent.parent / "fixtures" / "tournaments.json"
        with open(fixtures_path) as f:
            data = json.load(f)

        regions = {t["region"] for t in data["tournaments"]}
        assert len(regions) >= 3, f"Expected at least 3 regions, got {regions}"

    def test_fixtures_have_bo1_and_bo3(self) -> None:
        """Fixtures should include both BO1 and BO3 tournaments."""
        fixtures_path = Path(__file__).parent.parent / "fixtures" / "tournaments.json"
        with open(fixtures_path) as f:
            data = json.load(f)

        best_of_values = {t["best_of"] for t in data["tournaments"]}
        assert 1 in best_of_values, "No BO1 tournaments in fixtures"
        assert 3 in best_of_values, "No BO3 tournaments in fixtures"

    def test_fixtures_have_placements(self) -> None:
        """Each tournament should have placements."""
        fixtures_path = Path(__file__).parent.parent / "fixtures" / "tournaments.json"
        with open(fixtures_path) as f:
            data = json.load(f)

        for tournament in data["tournaments"]:
            assert len(tournament["placements"]) > 0, (
                f"No placements in tournament {tournament['name']}"
            )

    def test_placements_have_required_fields(self) -> None:
        """Each placement should have required fields."""
        fixtures_path = Path(__file__).parent.parent / "fixtures" / "tournaments.json"
        with open(fixtures_path) as f:
            data = json.load(f)

        for tournament in data["tournaments"]:
            for placement in tournament["placements"]:
                assert "placement" in placement
                assert "archetype" in placement
                assert isinstance(placement["placement"], int)
                assert placement["placement"] >= 1


class TestTournamentFixtureValidation:
    """Tests for fixture validation with Pydantic."""

    def test_fixtures_validate_with_pydantic(self) -> None:
        """All fixtures should validate with TournamentFixture model."""
        from src.fixtures.tournaments import TournamentFixture

        fixtures_path = Path(__file__).parent.parent / "fixtures" / "tournaments.json"
        with open(fixtures_path) as f:
            data = json.load(f)

        for item in data["tournaments"]:
            # Should not raise ValidationError
            fixture = TournamentFixture.model_validate(item)
            assert fixture.name == item["name"]

    def test_fixtures_normalize_archetypes(self) -> None:
        """Archetypes in fixtures should be recognizable."""
        from src.fixtures.tournaments import normalize_archetype

        fixtures_path = Path(__file__).parent.parent / "fixtures" / "tournaments.json"
        with open(fixtures_path) as f:
            data = json.load(f)

        archetypes = set()
        for tournament in data["tournaments"]:
            for placement in tournament["placements"]:
                archetypes.add(normalize_archetype(placement["archetype"]))

        # Should have multiple unique archetypes
        assert len(archetypes) >= 5, f"Expected at least 5 archetypes, got {archetypes}"
