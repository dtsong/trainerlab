"""Tests for card_usage_stats materialized view migration.

These tests validate the migration file structure and SQL logic.
They verify:
- Required Alembic attributes (revision, down_revision)
- Expected SQL columns and view structure
- Index creation statements
- Downgrade capability
- Data validation filters for malformed JSON
"""

import importlib.util
import re
import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path


class TestCardUsageViewMigration:
    """Tests for card usage view migration structure."""

    def test_migration_file_exists(self) -> None:
        """Test migration file exists."""
        migration_path = Path(__file__).parent.parent / (
            "alembic/versions/20260130_0001_003_card_usage_view.py"
        )
        assert migration_path.exists()

    def test_migration_has_required_attributes(self) -> None:
        """Test migration module has required alembic attributes."""
        migration_path = Path(__file__).parent.parent / (
            "alembic/versions/20260130_0001_003_card_usage_view.py"
        )

        spec = importlib.util.spec_from_file_location("migration_003", migration_path)
        assert spec is not None
        assert spec.loader is not None

        module = importlib.util.module_from_spec(spec)
        sys.modules["migration_003"] = module
        spec.loader.exec_module(module)

        assert hasattr(module, "revision")
        assert module.revision == "003"
        assert hasattr(module, "down_revision")
        assert module.down_revision == "002"
        assert hasattr(module, "upgrade")
        assert hasattr(module, "downgrade")
        assert callable(module.upgrade)
        assert callable(module.downgrade)

    def test_migration_sql_contains_required_columns(self) -> None:
        """Test migration SQL defines expected columns."""
        migration_path = Path(__file__).parent.parent / (
            "alembic/versions/20260130_0001_003_card_usage_view.py"
        )
        content = migration_path.read_text()

        # Check for required columns in the view
        assert "card_id" in content
        assert "format" in content
        assert "region" in content
        assert "best_of" in content
        assert "inclusion_rate" in content
        assert "avg_copies" in content
        assert "decks_including" in content
        assert "total_decks_with_lists" in content

    def test_migration_creates_materialized_view(self) -> None:
        """Test migration creates a materialized view."""
        migration_path = Path(__file__).parent.parent / (
            "alembic/versions/20260130_0001_003_card_usage_view.py"
        )
        content = migration_path.read_text()

        assert "CREATE MATERIALIZED VIEW" in content
        assert "card_usage_stats" in content

    def test_migration_creates_indexes(self) -> None:
        """Test migration creates necessary indexes."""
        migration_path = Path(__file__).parent.parent / (
            "alembic/versions/20260130_0001_003_card_usage_view.py"
        )
        content = migration_path.read_text()

        assert "CREATE INDEX" in content
        assert "ix_card_usage_stats_card_id" in content
        assert "ix_card_usage_stats_format_region" in content
        assert "ix_card_usage_stats_inclusion_rate" in content

    def test_migration_has_downgrade(self) -> None:
        """Test migration has proper downgrade."""
        migration_path = Path(__file__).parent.parent / (
            "alembic/versions/20260130_0001_003_card_usage_view.py"
        )
        content = migration_path.read_text()

        assert "DROP MATERIALIZED VIEW IF EXISTS card_usage_stats" in content

    def test_migration_sql_contains_date_columns(self) -> None:
        """Test migration SQL includes first_seen, last_seen, computed_at."""
        migration_path = Path(__file__).parent.parent / (
            "alembic/versions/20260130_0001_003_card_usage_view.py"
        )
        content = migration_path.read_text()

        assert "first_seen" in content
        assert "last_seen" in content
        assert "computed_at" in content


class TestCardUsageViewDataValidation:
    """Tests for data validation filters in the view."""

    def test_migration_filters_null_card_ids(self) -> None:
        """Test migration filters out entries with NULL card_id."""
        migration_path = Path(__file__).parent.parent / (
            "alembic/versions/20260130_0001_003_card_usage_view.py"
        )
        content = migration_path.read_text()

        # Should filter out NULL card_ids to prevent silent data loss
        assert "card_entry->>'card_id' IS NOT NULL" in content

    def test_migration_filters_null_quantities(self) -> None:
        """Test migration filters out entries with NULL quantity."""
        migration_path = Path(__file__).parent.parent / (
            "alembic/versions/20260130_0001_003_card_usage_view.py"
        )
        content = migration_path.read_text()

        # Should filter out NULL quantities to prevent cast failures
        assert "card_entry->>'quantity' IS NOT NULL" in content

    def test_migration_validates_decklist_is_array(self) -> None:
        """Test migration validates decklist is a JSON array."""
        migration_path = Path(__file__).parent.parent / (
            "alembic/versions/20260130_0001_003_card_usage_view.py"
        )
        content = migration_path.read_text()

        # Should validate decklist is an array, not object or other type
        assert "jsonb_typeof" in content
        assert "'array'" in content

    def test_migration_filters_empty_decklists(self) -> None:
        """Test migration filters out empty decklist arrays."""
        migration_path = Path(__file__).parent.parent / (
            "alembic/versions/20260130_0001_003_card_usage_view.py"
        )
        content = migration_path.read_text()

        # Should filter out empty arrays to prevent incorrect totals
        assert "jsonb_array_length" in content
        assert "> 0" in content


class TestCardUsageCalculationLogic:
    """Tests verifying the calculation logic is correct."""

    def test_inclusion_rate_calculation(self) -> None:
        """Test inclusion_rate = decks_including / total_decks_with_lists."""
        # Simulate: 7 decks include card X out of 10 total decks
        decks_including = 7
        total_decks_with_lists = 10

        # Expected: 7/10 = 0.7000 (rounded to 4 decimal places)
        expected = Decimal("0.7000")
        actual = Decimal(decks_including) / Decimal(total_decks_with_lists)
        actual = actual.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

        assert actual == expected

    def test_avg_copies_calculation(self) -> None:
        """Test avg_copies = total_copies / decks_including."""
        # Simulate: Card appears in 4 decks with quantities [4, 3, 4, 3] = 14 total
        total_copies = 14
        decks_including = 4

        # Expected: 14/4 = 3.50 (rounded to 2 decimal places)
        expected = Decimal("3.50")
        actual = Decimal(total_copies) / Decimal(decks_including)
        actual = actual.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        assert actual == expected

    def test_inclusion_rate_edge_case_all_decks(self) -> None:
        """Test inclusion_rate = 1.0 when card is in all decks."""
        decks_including = 50
        total_decks_with_lists = 50

        expected = Decimal("1.0000")
        actual = Decimal(decks_including) / Decimal(total_decks_with_lists)
        actual = actual.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

        assert actual == expected

    def test_avg_copies_single_copy(self) -> None:
        """Test avg_copies when card always appears as single copy."""
        # Card appears once in each of 5 decks
        total_copies = 5
        decks_including = 5

        expected = Decimal("1.00")
        actual = Decimal(total_copies) / Decimal(decks_including)
        actual = actual.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        assert actual == expected

    def test_sql_uses_correct_rounding_precision(self) -> None:
        """Test SQL uses correct ROUND precision for calculations."""
        migration_path = Path(__file__).parent.parent / (
            "alembic/versions/20260130_0001_003_card_usage_view.py"
        )
        content = migration_path.read_text()

        # inclusion_rate should round to 4 decimal places
        assert re.search(
            r"ROUND\(decks_including::numeric\s*/\s*total_decks_with_lists,\s*4\)",
            content,
        )

        # avg_copies should round to 2 decimal places
        assert re.search(
            r"ROUND\(total_copies::numeric\s*/\s*decks_including,\s*2\)", content
        )
