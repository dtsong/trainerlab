"""Tests for JP intelligence pipeline."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.pipelines.compute_jp_intelligence import (
    ComputeJPIntelligenceResult,
    _impact_rating,
    _slugify,
    compute_card_innovations,
    compute_jp_intelligence,
    compute_new_archetypes,
)


class TestSlugify:
    """Tests for _slugify helper."""

    def test_simple_name(self) -> None:
        assert _slugify("Charizard ex") == "charizard-ex"

    def test_multiple_spaces(self) -> None:
        assert _slugify("Raging Bolt ex") == "raging-bolt-ex"

    def test_special_characters(self) -> None:
        assert _slugify("Chien-Pao ex") == "chien-pao-ex"

    def test_strips_whitespace(self) -> None:
        assert _slugify("  Charizard ex  ") == "charizard-ex"


class TestImpactRating:
    """Tests for _impact_rating helper."""

    def test_rating_5(self) -> None:
        assert _impact_rating(0.35) == 5

    def test_rating_4(self) -> None:
        assert _impact_rating(0.25) == 4

    def test_rating_3(self) -> None:
        assert _impact_rating(0.15) == 3

    def test_rating_2(self) -> None:
        assert _impact_rating(0.08) == 2

    def test_rating_1(self) -> None:
        assert _impact_rating(0.03) == 1

    def test_boundary_30(self) -> None:
        assert _impact_rating(0.30) == 4  # Not > 0.30

    def test_boundary_above_30(self) -> None:
        assert _impact_rating(0.31) == 5


class TestComputeNewArchetypes:
    """Tests for compute_new_archetypes."""

    @pytest.mark.asyncio
    async def test_identifies_jp_only_archetype(self) -> None:
        """Archetype in JP >1% and not in global should be identified."""
        session = AsyncMock()

        jp_snapshot = MagicMock()
        jp_snapshot.archetype_shares = {
            "Grimmsnarl ex": 0.05,  # 5% in JP
            "Charizard ex": 0.20,  # Also in global
        }
        jp_snapshot.trends = {
            "Grimmsnarl ex": {"direction": "rising"},
        }

        global_snapshot = MagicMock()
        global_snapshot.archetype_shares = {
            "Charizard ex": 0.20,  # Exists globally
            # Grimmsnarl not present globally
        }

        # First call: JP snapshot, second: Global snapshot
        jp_result = MagicMock()
        jp_result.scalar_one_or_none.return_value = jp_snapshot

        global_result = MagicMock()
        global_result.scalar_one_or_none.return_value = global_snapshot

        # Third call: existing archetypes (for removal check)
        existing_result = MagicMock()
        existing_result.all.return_value = []

        session.execute.side_effect = [
            jp_result,
            global_result,
            # pg_insert for Grimmsnarl
            MagicMock(),
            # select for removal check
            existing_result,
        ]

        found, removed = await compute_new_archetypes(session, dry_run=False)

        # Should find Grimmsnarl (JP-only) but not Charizard (global)
        assert found == 1
        assert removed == 0

    @pytest.mark.asyncio
    async def test_skips_when_no_jp_snapshot(self) -> None:
        """Should return 0,0 when no JP snapshot exists."""
        session = AsyncMock()

        jp_result = MagicMock()
        jp_result.scalar_one_or_none.return_value = None

        global_result = MagicMock()
        global_result.scalar_one_or_none.return_value = MagicMock()

        session.execute.side_effect = [jp_result, global_result]

        found, removed = await compute_new_archetypes(session, dry_run=False)
        assert found == 0
        assert removed == 0

    @pytest.mark.asyncio
    async def test_dry_run_does_not_write(self) -> None:
        """Dry run should not execute insert statements."""
        session = AsyncMock()

        jp_snapshot = MagicMock()
        jp_snapshot.archetype_shares = {"Grimmsnarl ex": 0.05}
        jp_snapshot.trends = {}

        global_snapshot = MagicMock()
        global_snapshot.archetype_shares = {}

        jp_result = MagicMock()
        jp_result.scalar_one_or_none.return_value = jp_snapshot

        global_result = MagicMock()
        global_result.scalar_one_or_none.return_value = global_snapshot

        session.execute.side_effect = [jp_result, global_result]

        found, removed = await compute_new_archetypes(session, dry_run=True)

        assert found == 1
        # Only 2 execute calls (the two snapshot queries)
        assert session.execute.call_count == 2


class TestComputeCardInnovations:
    """Tests for compute_card_innovations."""

    @pytest.mark.asyncio
    async def test_creates_innovation_from_adoption_rate(self) -> None:
        """Should create innovation for card with high inclusion rate."""
        session = AsyncMock()

        # Mock max period_end
        period_result = MagicMock()
        period_result.scalar_one_or_none.return_value = date(2026, 2, 1)

        # Mock adoption rates
        rate = MagicMock()
        rate.card_id = "sv9-001"
        rate.card_name_en = "TestCard"
        rate.card_name_jp = "テストカード"
        rate.inclusion_rate = 0.15
        rate.archetype_context = "Grimmsnarl ex"
        rate.sample_size = 200

        rates_result = MagicMock()
        rates_result.scalars.return_value.all.return_value = [rate]

        # Mock card lookup — no card found by EN name
        no_card = MagicMock()
        no_card.scalar_one_or_none.return_value = None

        # Mock for removal check: current_card_ids query
        current_ids = MagicMock()
        current_ids.all.return_value = [("sv9-001",)]

        current_names = MagicMock()
        current_names.all.return_value = [("TestCard",)]

        existing_innovations = MagicMock()
        existing_innovations.all.return_value = []

        session.execute.side_effect = [
            period_result,
            rates_result,
            no_card,  # Card lookup by card_name_en
            no_card,  # Card lookup by card_name_jp
            MagicMock(),  # pg_insert
            current_ids,  # removal: current card_ids
            current_names,  # removal: current names
            existing_innovations,  # removal: existing
        ]

        found, removed = await compute_card_innovations(session, dry_run=False)

        assert found == 1
        assert removed == 0

    @pytest.mark.asyncio
    async def test_skips_when_no_adoption_data(self) -> None:
        """Should return 0,0 when no adoption rate data exists."""
        session = AsyncMock()

        period_result = MagicMock()
        period_result.scalar_one_or_none.return_value = None

        session.execute.side_effect = [period_result]

        found, removed = await compute_card_innovations(session, dry_run=False)
        assert found == 0
        assert removed == 0

    @pytest.mark.asyncio
    async def test_dry_run_does_not_write(self) -> None:
        """Dry run should not execute insert/delete statements."""
        session = AsyncMock()

        period_result = MagicMock()
        period_result.scalar_one_or_none.return_value = date(2026, 2, 1)

        rate = MagicMock()
        rate.card_id = "sv9-001"
        rate.card_name_en = "TestCard"
        rate.card_name_jp = None
        rate.inclusion_rate = 0.15
        rate.archetype_context = None
        rate.sample_size = 100

        rates_result = MagicMock()
        rates_result.scalars.return_value.all.return_value = [rate]

        # Card lookup returns no match
        no_card = MagicMock()
        no_card.scalar_one_or_none.return_value = None

        session.execute.side_effect = [
            period_result,
            rates_result,
            no_card,  # Card lookup by card_name_en
        ]

        found, removed = await compute_card_innovations(session, dry_run=True)

        assert found == 1
        # 3 calls: period query + rates query + card lookup
        assert session.execute.call_count == 3
        # No flush should be called in dry_run
        session.flush.assert_not_called()


class TestComputeJPIntelligence:
    """Tests for the orchestrator function."""

    @pytest.mark.asyncio
    async def test_orchestrates_both_functions(self) -> None:
        """Should run both new archetypes and card innovations."""
        with (
            patch(
                "src.pipelines.compute_jp_intelligence.async_session_factory"
            ) as mock_factory,
            patch(
                "src.pipelines.compute_jp_intelligence.compute_new_archetypes",
                return_value=(3, 1),
            ),
            patch(
                "src.pipelines.compute_jp_intelligence.compute_card_innovations",
                return_value=(5, 2),
            ),
        ):
            mock_session = AsyncMock()
            mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await compute_jp_intelligence(dry_run=False)

            assert result.new_archetypes_found == 3
            assert result.new_archetypes_removed == 1
            assert result.innovations_found == 5
            assert result.innovations_removed == 2
            assert result.success is True

    @pytest.mark.asyncio
    async def test_handles_archetype_error_gracefully(self) -> None:
        """Should continue if new archetypes fails."""
        with (
            patch(
                "src.pipelines.compute_jp_intelligence.async_session_factory"
            ) as mock_factory,
            patch(
                "src.pipelines.compute_jp_intelligence.compute_new_archetypes",
                side_effect=Exception("DB error"),
            ),
            patch(
                "src.pipelines.compute_jp_intelligence.compute_card_innovations",
                return_value=(2, 0),
            ),
        ):
            mock_session = AsyncMock()
            mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await compute_jp_intelligence(dry_run=False)

            assert result.new_archetypes_found == 0
            assert result.innovations_found == 2
            assert len(result.errors) == 1
            assert result.success is False

    @pytest.mark.asyncio
    async def test_dry_run_does_not_commit(self) -> None:
        """Dry run should not call session.commit()."""
        with (
            patch(
                "src.pipelines.compute_jp_intelligence.async_session_factory"
            ) as mock_factory,
            patch(
                "src.pipelines.compute_jp_intelligence.compute_new_archetypes",
                return_value=(0, 0),
            ),
            patch(
                "src.pipelines.compute_jp_intelligence.compute_card_innovations",
                return_value=(0, 0),
            ),
        ):
            mock_session = AsyncMock()
            mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

            await compute_jp_intelligence(dry_run=True)

            mock_session.commit.assert_not_called()


class TestComputeJPIntelligenceResult:
    """Tests for the result dataclass."""

    def test_success_when_no_errors(self) -> None:
        result = ComputeJPIntelligenceResult()
        assert result.success is True

    def test_not_success_with_errors(self) -> None:
        result = ComputeJPIntelligenceResult(errors=["something failed"])
        assert result.success is False
