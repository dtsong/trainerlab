"""Tests for the compute_evolution pipeline."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.models.adaptation import Adaptation
from src.pipelines.compute_evolution import (
    ComputeEvolutionResult,
    compute_evolution_intelligence,
)

_UNSET = object()


def _make_execute_result(
    *, scalar_one_or_none=_UNSET, scalars_all=_UNSET, scalar=_UNSET, all=_UNSET
):
    """Create a mock result from session.execute()."""
    mock_result = MagicMock()
    if scalar_one_or_none is not _UNSET:
        mock_result.scalar_one_or_none.return_value = scalar_one_or_none
    if scalars_all is not _UNSET:
        mock_result.scalars.return_value.all.return_value = scalars_all
    if scalar is not _UNSET:
        mock_result.scalar.return_value = scalar
    if all is not _UNSET:
        mock_result.all.return_value = all
    return mock_result


class TestComputeEvolutionResult:
    """Tests for the result dataclass."""

    def test_success_when_no_errors(self) -> None:
        result = ComputeEvolutionResult()
        assert result.success is True

    def test_failure_when_errors(self) -> None:
        result = ComputeEvolutionResult(errors=["something broke"])
        assert result.success is False

    def test_default_counts_are_zero(self) -> None:
        result = ComputeEvolutionResult()
        assert result.adaptations_classified == 0
        assert result.contexts_generated == 0
        assert result.predictions_generated == 0
        assert result.articles_generated == 0


class TestComputeEvolutionIntelligence:
    """Tests for the main pipeline function."""

    @pytest.mark.asyncio
    async def test_dry_run_returns_result(self) -> None:
        """Should return a result without errors on dry run."""
        mock_session = AsyncMock()
        mock_claude = AsyncMock()

        # Mock all queries to return empty results
        mock_session.execute.return_value = _make_execute_result(scalars_all=[])

        with (
            patch("src.pipelines.compute_evolution.ClaudeClient") as mock_claude_cls,
            patch(
                "src.pipelines.compute_evolution.async_session_factory"
            ) as mock_session_factory,
        ):
            mock_claude_cls.return_value.__aenter__ = AsyncMock(
                return_value=mock_claude
            )
            mock_claude_cls.return_value.__aexit__ = AsyncMock()
            mock_session_factory.return_value.__aenter__ = AsyncMock(
                return_value=mock_session
            )
            mock_session_factory.return_value.__aexit__ = AsyncMock()

            result = await compute_evolution_intelligence(dry_run=True)

        assert isinstance(result, ComputeEvolutionResult)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_classifies_unclassified_adaptations(self) -> None:
        """Should classify adaptations that haven't been classified by Claude."""
        mock_session = AsyncMock()
        mock_claude = AsyncMock()

        adaptation = MagicMock(spec=Adaptation)
        adaptation.id = uuid4()
        adaptation.source = "diff"

        # First call: unclassified adaptations, rest: empty
        mock_session.execute.side_effect = [
            _make_execute_result(scalars_all=[adaptation]),  # adaptations
            _make_execute_result(scalars_all=[]),  # snapshots missing context
            _make_execute_result(scalars_all=[]),  # upcoming tournaments
            _make_execute_result(all=[]),  # archetypes with 3+ snapshots
        ]

        with (
            patch("src.pipelines.compute_evolution.ClaudeClient") as mock_claude_cls,
            patch(
                "src.pipelines.compute_evolution.async_session_factory"
            ) as mock_session_factory,
            patch(
                "src.pipelines.compute_evolution.AdaptationClassifier"
            ) as mock_classifier_cls,
            patch("src.pipelines.compute_evolution.PredictionEngine"),
            patch("src.pipelines.compute_evolution.EvolutionArticleGenerator"),
        ):
            mock_claude_cls.return_value.__aenter__ = AsyncMock(
                return_value=mock_claude
            )
            mock_claude_cls.return_value.__aexit__ = AsyncMock()
            mock_session_factory.return_value.__aenter__ = AsyncMock(
                return_value=mock_session
            )
            mock_session_factory.return_value.__aexit__ = AsyncMock()

            mock_classifier = AsyncMock()
            mock_classifier_cls.return_value = mock_classifier

            result = await compute_evolution_intelligence(dry_run=False)

        assert result.adaptations_classified == 1
        mock_classifier.classify.assert_called_once_with(adaptation)

    @pytest.mark.asyncio
    async def test_handles_errors_gracefully(self) -> None:
        """Should capture errors and continue processing."""
        with patch("src.pipelines.compute_evolution.ClaudeClient") as mock_claude_cls:
            mock_claude_cls.side_effect = Exception("Connection failed")

            result = await compute_evolution_intelligence(dry_run=False)

        assert result.success is False
        assert len(result.errors) == 1
        assert "Connection failed" in result.errors[0]
