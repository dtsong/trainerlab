"""Tests for card_usage_stats materialized view migration."""

import importlib.util
import sys
from pathlib import Path


class TestCardUsageViewMigration:
    """Tests for card usage view migration."""

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
